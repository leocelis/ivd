# Host apps: tenant keys for the hosted IVD MCP server

A **host app** is a product that serves many of its own customers (tenants) and
wants each of them to use IVD through it. Instead of registering a key per
tenant, the host and the server share one secret, and the host derives each
tenant's key on demand. The server recomputes the key to check it: there is no
provisioning step and nothing to sync.

## What a tenant gets

A tenant key can list and call three content-only tools:

| Tool | Input |
|---|---|
| `ivd_validate` | `artifact_yaml`, optional `artifact_type` |
| `ivd_review_intent` | `artifact_yaml` |
| `canon_check` | `text` or `document` |

- Every other tool is refused, and `tools/list` shows only these three.
- `project_root` and `workspace_root` are refused on every call. They name
  paths on the server's disk, which every caller of a shared server shares.
- `ivd_validate` runs no disk check for a tenant. A test path named in the YAML
  is never opened, and the result carries `test_paths_checked: false`. The
  tenant's own test files are not on the server, so run them on your side.
- `ivd_search` (a paid embedding call) and the Judgment tools (they write to
  the server's disk) are not offered.

## Deriving a key

```
key = "ivd_" + tenant + "_" + base64url_nopad( HMAC-SHA256(SECRET, "ivd:" + VERSION + ":" + tenant) )
```

- `tenant` must match `^[a-z0-9][a-z0-9-]{0,55}$` (lowercase only).
- `VERSION` is one of the versions the server accepts (default `v1`).
- The MAC is always 43 characters. The server reads the tenant as the text
  between `ivd_` and the last 44 characters. Do not split the key on `_`:
  base64url can contain `_`.
- Derive the key per call; do not store it.

Python:

```python
import base64, hashlib, hmac

def ivd_tenant_key(secret: str, tenant: str, version: str = "v1") -> str:
    mac = hmac.new(secret.encode(), f"ivd:{version}:{tenant}".encode(), hashlib.sha256).digest()
    return f"ivd_{tenant}_" + base64.urlsafe_b64encode(mac).rstrip(b"=").decode()
```

Test vector, to check your implementation:

| Secret | Version | Tenant | Key |
|---|---|---|---|
| `test-secret-do-not-use` | `v1` | `acme` | `ivd_acme_lapHGNV1gUE0w05P_i0KVkw8RF5Y5R_9-vngns5EZ50` |

Send it as `Authorization: Bearer <key>` on every request (Streamable HTTP at
`/mcp`, or legacy SSE at `/sse` + `/messages`).

## Sessions

Open one MCP session per tenant. A session is bound to the key that opened it:
a message on that session with another tenant's key, or an operator key, is
answered as if the session did not exist (404). Reusing one session for two
tenants does not work, by design.

## Server settings (operator)

| Variable | Meaning | Default |
|---|---|---|
| `IVD_TENANT_KEY_SECRET` | Shared secret. Not set: tenant keys are off and nothing changes | not set |
| `IVD_TENANT_KEY_VERSIONS` | Comma-separated versions accepted | `v1` |
| `IVD_REVOKED_TENANTS` | Comma-separated tenants whose keys are refused | empty |

- Keys in `IVD_API_KEYS` keep the full tool set, as before.
- While the secret is set, a key that is neither an operator key nor a valid
  tenant key gets 401, even if `IVD_API_KEYS` is empty.
- Rotation: add the new version (`v1,v2`), move the host to `v2`, then drop `v1`.
- The signed text starts with `ivd:`, so a key made for another product that
  uses the same scheme is not valid here even with the same secret. Use a
  different secret per server anyway.
- Logs record `tenant:<id>`, never the key.
- If the operator sets `COMPLYEDGE_API_KEY`, every call's arguments and result,
  tenant calls included, are sent to ComplyEdge for screening, and a block
  replaces the tool's answer. Tell your tenants their text goes there.
