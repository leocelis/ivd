# IVD: Host-Derived Tenant Keys: Tech Spec

**Status:** PROPOSED (2026-11-15). Not built.
**Scope:** the hosted MCP server (`mcp_server/`). Stdio and local use do not change.

## 1. Problem

Today the hosted server accepts any key listed in `IVD_API_KEYS` and knows nothing about who the
caller is (`mcp_server/auth.py`). That fits one person using Claude Code or Cursor. It does not fit
a **host app**: a product that serves many of its own customers (tenants) and wants each of them to
use IVD through it.

Two things are missing for a host:

1. A key per tenant that the host does not have to register with the server one by one.
2. A wall. Most IVD tools take `project_root` or `workspace_root`: paths on the server's own disk.
   On a shared server those paths are shared by every caller.

## 2. Goal

A host app can give each of its tenants IVD's content-only checks, with one secret shared between
the host and the server, no provisioning step, and no tenant able to reach the server's disk.

Existing keys keep working exactly as today.

## 3. Design

### 3.1 The key

```
key = "ivd_" + tenant + "_" + base64url_nopad( HMAC-SHA256(SECRET, "ivd:" + VERSION + ":" + tenant) )
```

- `tenant` matches `^[a-z0-9][a-z0-9-]{0,55}$`. Lowercase only, so two ids can never differ by case.
- The MAC is always 43 characters. The server reads the tenant as the text between the prefix and
  the last 44 characters. Base64url can contain `_`, so the tenant is never found by splitting on `_`.
- The host derives the key on each call and never stores it. The server never stores it either.
- The signed text starts with the product name, so a key made for one server is not valid on
  another even if an operator reuses a secret. Use a different secret per server anyway.

Test vector (each project that implements this scheme carries its own, with the same secret and
tenant, so copies cannot drift):

| Secret | Version | Tenant | Key |
|---|---|---|---|
| `test-secret-do-not-use` | `v1` | `acme` | `ivd_acme_lapHGNV1gUE0w05P_i0KVkw8RF5Y5R_9-vngns5EZ50` |

### 3.2 Server settings

| Variable | Meaning | Default |
|---|---|---|
| `IVD_TENANT_KEY_SECRET` | The shared secret. Not set → the feature is off and nothing changes | not set |
| `IVD_TENANT_KEY_VERSIONS` | Comma-separated versions the server accepts | `v1` |
| `IVD_REVOKED_TENANTS` | Comma-separated tenants whose keys are refused | empty |

### 3.3 Verification (I1)

In `validate_api_key`, a bearer key that is not in `IVD_API_KEYS` is accepted when all hold:

1. `IVD_TENANT_KEY_SECRET` is set.
2. The key has the `ivd_` prefix and a tenant that matches the rule.
3. Its MAC equals the MAC computed for that tenant with one of the accepted versions, compared in
   constant time.
4. The tenant is not revoked.

The request then runs **as that tenant**, and the tenant is written to the auth log in place of the
key id. Rotation: add a new version, move the host to it, drop the old one.

The tenant is read from **each message's own request**, not from a value set when the MCP
session was opened. With stateful Streamable HTTP the server task for a session starts inside the
request that created it, so a per-request variable set there stays the first caller's. A session is
also bound to the identity that opened it: a message whose key resolves to a different identity
(another tenant, or an operator key) is refused. Without that, one MCP session reused for two
tenants would run both as the first.
The legacy SSE transport has the same shape and gets the same rule.

### 3.4 What a tenant key may call (I2)

| Allowed | Refused |
|---|---|
| `ivd_validate(artifact_yaml)`, `ivd_review_intent(artifact_yaml)`, `canon_check(text)` | Every other tool |

A tenant key that sends `project_root` or `workspace_root` on an allowed tool is refused.
`ivd_validate` has an optional `project_root` that is resolved on the server's disk, so the
argument itself is refused, not ignored.

**Refusing the argument is not enough.** Without it `ivd_validate` falls back to the server's own
framework folder and checks there whether each test path named in the YAML exists
(`tools/validate.py`). For a tenant that is wrong twice: its own test files are never on the server,
so every constraint would be reported as unverified; and a path in the YAML would tell the tenant
whether a file exists on the server. So for a tenant key the disk checks do not run at all: the
result says `test_paths_checked: false`, and no path from the YAML is ever opened or joined to a
server folder. `tools/list` for a tenant key returns only the three
allowed tools.

`ivd_search` is not offered: it is the one tool that makes a paid embedding call.

## 4. What does not change

- Keys in `IVD_API_KEYS`: same tools, same behaviour.
- Stdio transport: no auth, as today.
- No database is added. Verification is a computation, so there is nothing to provision or sync.

## 5. Tests

- The test vector verifies.
- A tampered MAC, an unknown version, a revoked tenant, a tenant that breaks the rule and a key with
  no secret configured are each refused with 401.
- A MAC that contains `_` still yields the right tenant.
- A tenant key calling a tool outside the allowlist is refused; calling `ivd_validate` with
  `project_root` is refused; without it, it validates.
- For a tenant key, an artifact naming a test path, relative or absolute, opens no file on the
  server and gets the same answer whether or not that path exists there.
- An MCP session opened with one key and continued with another is refused.
- `tools/list` for a tenant key shows three tools.
- A key from `IVD_API_KEYS` behaves as before.

## 6. Files

`mcp_server/auth.py` (verification), `mcp_server/server.py` (the tenant from each message's request,
the session binding), `mcp_server/registry.py` and the tool dispatch (allowlist and argument
refusal), `mcp_server/tools/validate.py` (no disk checks for a tenant), `mcp_server/logger.py` (tenant in the auth log), `SECURITY.md`, a new
`docs/integrations/HOST_APP.md` (how a host derives keys and which tools its tenants get), tests.

## 7. Open, named

- The server logs a truncated preview of tool arguments, and keeps an event store for resumable
  streams. That neither can show one tenant another tenant's content is not yet checked. It is
  checked in the build, before this is called done.
- When the operator sets `COMPLYEDGE_API_KEY`, every call's arguments and result are sent to
  ComplyEdge for screening, and a block replaces the tool's answer. That applies to tenant calls
  too; a host should know its tenants' text goes there.
- Judgment tools write to the server's disk and stay out of tenant reach. A per-tenant judgment
  store is a separate design.
