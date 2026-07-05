# ComplyEdge TrustLint — IVD integration

IVD uses [ComplyEdge](https://complyedge.io) TrustLint on LLM-facing artifacts: offline EU AI Act screening in CI, optional runtime checks, and a public trust surface.

**Tenant slug:** `ivd`

---

## What runs where

| Layer | Mechanism | API key in repo? | Blocks merge? |
|-------|-----------|------------------|---------------|
| **Offline gate** | `trustlint check` via `./scripts/compliance/check.sh` | No | Yes (CI `compliance` job) |
| **Runtime enforcement** | `POST /v1/check` via `./scripts/compliance/runtime_check.sh` | No (BYOK env only) | No (opt-in local / scheduled) |
| **Public proof** | Live seal + trust JSON | No | N/A |

```
ivd_scaffold → ivd_validate → trustlint check (offline) → CI green
                    ↓ optional BYOK
              runtime_check.sh → /v1/check → audit trail → badge + trust page
```

---

## Public surfaces

| Surface | URL |
|---------|-----|
| Enforcement seal (SVG) | https://api.complyedge.io/v1/public/badge/ivd.svg |
| Trust JSON | https://api.complyedge.io/v1/public/trust/ivd |
| Trust page | https://trust.complyedge.io/ivd |
| Origin site (badge host) | https://ivdframework.dev |
| Overview on site | https://ivdframework.dev/#complyedge |

The seal reflects **live runtime audit data** (checks in 24h / 7d). It is not a static marketing badge.

---

## LLM-facing scan scope

Recipes, templates, all `*_intent.yaml`, and root `ivd_system_intent.yaml` — see `.trustlint.yaml` for exact globs.

**Agent workflow:** `ivd_scaffold` → `ivd_validate` → `./scripts/compliance/check.sh` → declare done. Recipe: `ivd_load_recipe compliance-trustlint`.

---

## Operator setup (BYOK)

1. Provision a ComplyEdge tenant with slug `ivd` and store the API key in env only — `COMPLYEDGE_API_KEY` (GitHub Actions secret for optional runtime job, never in git).
2. Enable public trust:

```bash
curl -s -X PATCH https://api.complyedge.io/v1/tenant/trust \
  -H "Authorization: Bearer $COMPLYEDGE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"trust_public_enabled": true, "public_slug": "ivd", "display_name": "IVD Framework", "website_url": "https://ivdframework.dev"}'
```

3. Seed runtime checks (feeds live seal):

```bash
export COMPLYEDGE_API_KEY=ce_...
./scripts/compliance/runtime_check.sh
```

---

## CI

| Job | Path | Secret required |
|-----|------|-----------------|
| `compliance` | `./scripts/compliance/check.sh` | None |
| `compliance-runtime` (optional) | `./scripts/compliance/runtime_check.sh` | `COMPLYEDGE_API_KEY` |

Offline gate is the auditable merge blocker. Runtime is opt-in proof for live trust metrics.

---

## Local validation

```bash
pip install 'trustlint>=2.0.1'
./scripts/compliance/check.sh
pytest mcp_server/tests/unit/test_compliance_trustlint.py -q
export COMPLYEDGE_API_KEY=ce_...
./scripts/compliance/runtime_check.sh
```

---

## References

- Recipe: `recipes/compliance-trustlint.yaml`
- Agent rule: `<BEGIN-COMPLYEDGE v1.0>` in `.cursorrules`
- CE embed guide: https://complyedge.io/docs/trust-badge.html
- CE OSS adoption guide: `complyedge-platform/docs/development/oss-trustlint-adoption-guide.md`
- Horizon variant: [leocelis/horizon](https://github.com/leocelis/horizon) → `docs/integrations/COMPLYEDGE.md`
