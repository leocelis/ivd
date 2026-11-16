# Security Policy

## Supported Versions

The latest release on the `main` branch is supported with security updates.

| Version | Supported |
|---------|-----------|
| Latest  | Yes       |

## Reporting a Vulnerability

**Do not open a public issue for security vulnerabilities.**

To report a vulnerability, use one of these methods:

1. **GitHub Security Advisories** (preferred) — navigate to the [Security](https://github.com/leocelis/ivd/security) tab and click **Report a vulnerability**.
2. **Email** — send details to [leo@leocelis.com](mailto:leo@leocelis.com).

Please include:

- Description of the vulnerability
- Steps to reproduce
- Affected versions
- Potential impact

## Response

- Reports are acknowledged within **3 business days**.
- A fix or mitigation plan is communicated within **14 days**.
- Public disclosure is coordinated after a fix is available.

## Hosted server: tenant keys

The hosted MCP server can serve a **host app**: a product whose own customers
(tenants) use IVD through it. The host and the server share one secret
(`IVD_TENANT_KEY_SECRET`) and the host derives a key per tenant; nothing is
stored or provisioned on the server. How a host derives keys:
[docs/integrations/HOST_APP.md](docs/integrations/HOST_APP.md).

What the server guarantees for a tenant key:

- **Content-only tools.** A tenant key can list and call only `ivd_validate`,
  `ivd_review_intent` and `canon_check`. Every other tool is refused.
- **No server disk.** `project_root` and `workspace_root` are refused, not
  ignored. `ivd_validate` runs no disk check for a tenant: no path named in the
  YAML is opened or joined to a server folder, and the result says
  `test_paths_checked: false`.
- **One identity per session.** The tenant is read from each message's own
  request. An MCP session (Streamable HTTP or legacy SSE) is bound to the
  identity that opened it; a message with a key for another tenant, or an
  operator key, is refused as if the session did not exist.
- **Resumable streams stay with their owner.** Stored stream events are kept
  per identity, so a `Last-Event-ID` cannot replay another caller's events.
- **No made-up keys.** While tenant keys are on, a bearer key that is neither
  in `IVD_API_KEYS` nor a valid tenant key gets 401, even when `IVD_API_KEYS`
  is empty.
- **Logs name the tenant, never the key.** Auth and tool-call logs record
  `tenant:<id>`. Tool-call logs keep a truncated, redacted preview of the
  arguments on the operator's side; no tool returns logs to any caller.

Operator duties: use a different secret per server; rotate by adding a version
to `IVD_TENANT_KEY_VERSIONS`, moving the host to it, then dropping the old
one; revoke a tenant with `IVD_REVOKED_TENANTS`. `MCP_AUTH_DISABLED=true`
turns all of this off and must never be set on a shared server. When the
operator sets `COMPLYEDGE_API_KEY`, every call's arguments and result
(tenant calls included) are sent to ComplyEdge for screening; a host should
tell its tenants.

## Scope

This policy covers the IVD framework code, MCP server, and published recipes/templates. Third-party dependencies are managed via Dependabot and updated promptly when advisories are published.

Thank you for helping keep IVD secure.
