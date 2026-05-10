# Legal Notices and Disclaimers

> **Version:** 1.0 · **Effective:** May 10, 2026
>
> This document applies to the IVD framework (ivdframework.dev), the hosted MCP server
> at `mcp.ivdframework.dev`, the open-source repository at github.com/leocelis/ivd,
> and any self-hosted deployment of the same codebase.
>
> This document is **not legal advice**. It describes how IVD is designed, what it does
> and does not do, and what responsibilities remain with the user. If you are deploying
> IVD in a regulated context, consult qualified legal counsel.

---

## 1. What IVD Is — and Is Not

IVD (Intent-Verified Development) is a **developer framework and MCP server** that
helps software teams write structured intent artifacts and run AI-assisted verification
workflows against those artifacts. It is:

- A workflow tool for making AI development intent explicit and verifiable
- A collection of 28 MCP tools accessible to AI coding agents
- An open-source project (MIT License) with an optional hosted server component

IVD is **not**:

- A certified AI system under Regulation (EU) 2024/1689 (EU AI Act) or any other
  regulatory scheme
- A legal compliance product or conformity assessment tool
- A guarantee that AI outputs are accurate, hallucination-free, or legally sufficient
- A substitute for human review, professional judgment, or legal counsel

**Classification note (EU AI Act):** IVD does not provide LLM inference — it
orchestrates calls to third-party LLMs. It is not listed in Annex III of Regulation
(EU) 2024/1689. Under current guidance, IVD is most likely classified as a
non-high-risk general-purpose software tool. However, **if you use IVD to build a
system that falls under Annex III** (employment screening, credit scoring, medical
diagnosis, critical infrastructure management, etc.), your system — not IVD — bears
the obligations under Articles 6, 9, 13, and 14 of the AI Act, and you are the
deployer responsible for compliance.

Official text: <https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ:L_202401689>

---

## 2. Inherent AI Limitations

IVD mitigates known LLM failure modes but cannot eliminate them. The following
limitations are **architectural properties of all current large language models**, not
defects specific to IVD:

### 2.1 Read-Acknowledge-Violate Pattern

An AI agent can recite all constraints from an intent artifact and confirm understanding
— then violate those same constraints in the implementation. This occurs because LLM
attention is finite and degrades over long contexts. IVD's segmented implementation
workflow (IVD Rule 1) reduces this risk by forcing attention resets between segments,
but compliance cannot be mechanically guaranteed.

**Research basis:** Issues #26848, #6120, #32290, and #742 in the anthropics/claude-code
GitHub repository document this pattern empirically across multiple model families.

### 2.2 Position Bias

Constraints listed earlier in an intent artifact are weighted less heavily than those
listed later when conflicts arise between them. This is a documented LLM architectural
property.

**Research basis:** NIST AI 600-1 (Confabulation risk, GV-6.1); IFScale 2025
(constraint compliance degrades to 68% accuracy at high constraint density).

### 2.3 Context Window Saturation

In long coding sessions, early intent artifacts may be displaced from the model's active
context window, causing the agent to operate without the constraints it was given. IVD's
`ivd_load_context` tool addresses this; users who skip this step in long sessions do so
at their own risk.

### 2.4 Hallucination in AI-Generated Artifacts

When an AI agent uses `ivd_scaffold` to generate an intent artifact, the generated
constraints may be plausible but factually incorrect, overly broad, or structurally
valid while missing the actual system intent. The mandatory human review step (IVD Step
3) is the designed mitigation. **Skipping human review eliminates the primary safety
gate.**

NIST AI 600-1 identifies confabulation as one of 13 primary generative AI risks and
recommends human-in-the-loop processes for consequential outputs. IVD's design
implements this recommendation; users who bypass it accept the residual risk.

**Source:** <https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf>  
**Source:** <https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence>

---

## 3. Marketing Claims — Scope and Limits

IVD's marketing references "eliminating hallucinations" and "turning complex
implementations into single-turn completions." These claims are **scoped to specific,
tested conditions**:

- The Canon layer's 4/4 verification beat detection and 72% R-failure improvement
  figures are based on n=9 internal test scenarios. These are illustrative results,
  not statistically guaranteed performance across all models, contexts, or task types.
- The "single-turn completion" claim applies to well-constrained intent artifacts with
  near-zero entropy constraints. High-entropy or under-specified artifacts will not
  produce this outcome.
- IVD's effectiveness depends entirely on the quality of the intent artifact. A
  structurally valid artifact with vague constraints (`write well`, `be appropriate`)
  will not prevent hallucinations — it will pass validation while providing no actual
  constraint.

The FTC has stated that unsubstantiated efficacy claims about AI capabilities are
actionable as deceptive practices under 15 U.S.C. § 45 (Section 5 of the FTC Act).
IVD does not guarantee the marketing outcomes for use cases, models, or constraint
qualities outside the tested conditions described above.

**Source:** <https://www.ftc.gov/business-guidance/blog/2023/02/keep-your-ai-claims-check>  
**Source:** <https://www.ftc.gov/news-events/news/press-releases/2024/09/ftc-announces-crackdown-deceptive-ai-claims-schemes>

---

## 4. Hosted Server — Data Transmission and Privacy

When you use the hosted IVD MCP server at `mcp.ivdframework.dev`:

### 4.1 What is transmitted

**Every tool call** sends the arguments you provide — including `yaml_content`,
`project_root`, `artifact_path`, and any other parameters — to the hosted server over
HTTPS. This content is processed to execute the tool and is not intentionally retained
beyond the session.

### 4.2 Where it is processed

The hosted server runs on **DigitalOcean App Platform (US East region)**. Search queries
made via `ivd_search` are processed using the **OpenAI Embeddings API** (text-embedding-3-small
model). These are US-based infrastructure providers.

**If you are in the European Union**, transmitting personal data through tool arguments
constitutes an international data transfer from the EU to the United States under
GDPR Chapter V (Articles 44–46, Regulation (EU) 2016/679).

**Source:** <https://www.edpb.europa.eu/sme-data-protection-guide/international-data-transfers_en>

### 4.3 Sub-processors

| Sub-processor | Role | DPA |
|---------------|------|-----|
| DigitalOcean, Inc. | Infrastructure hosting | <https://www.digitalocean.com/legal/data-processing-agreement> |
| OpenAI, L.L.C. | Embedding generation (`ivd_search`) | <https://openai.com/policies/data-processing-addendum/> |

### 4.4 What you must not transmit

Do not transmit the following through hosted server tool arguments:

- **Personal data** (names, emails, government IDs, IP addresses, behavioral data
  attributable to individuals) — doing so without a lawful basis and appropriate
  safeguards violates GDPR Article 6 if you are an EU controller
- **Sensitive personal data** (health, biometric, political, religious, or sexual
  orientation data) — prohibited basis processing under GDPR Article 9
- **Trade secrets or confidential business information** — the hosted server is a
  shared infrastructure; treat it as untrusted for confidential content
- **API keys, credentials, or secrets** — never include these in intent artifact
  content, correction text, or any tool argument

### 4.5 Self-hosted alternative

If data isolation is required, clone the repository and run the server locally. In a
self-hosted deployment, no data leaves your environment. The `OPENAI_API_KEY` you
configure is used only by your own instance of the server and is not accessible to IVD
as a project.

Self-hosting instructions: [`deploy/`](deploy/) directory and
[`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## 5. Judgment Phase — Special Data Handling Warning

The Judgment phase tools (`ivd_judgment_capture`, `ivd_judgment_distill_pattern`,
`ivd_judgment_inject_context`, and related tools) capture corrections made to AI outputs
and accumulate them in a `.judgment/` directory as structured YAML files.

**This creates a persistent record of individual corrections.** Before using these tools,
understand the following:

- **PII risk:** Correction text often naturally includes names, code comments that
  reference individuals, ticket numbers linked to personnel, or other identifying
  information. Do not include PII in correction descriptions. The tool does not
  automatically sanitize these entries.

- **Employment law risk:** Judgment ledger entries that accumulate corrections
  attributed to a specific person may constitute profiling under GDPR Article 22
  if used in employment or performance assessment decisions. Individuals have the
  right to object (GDPR Article 21) and to request human review of any
  significant automated decision (GDPR Article 22(3)).

- **Retention:** There is no automatic expiry on `.judgment/` entries. If the ledger
  is committed to version control, entries are permanent in the git history. Apply
  your organization's data retention policy to this directory.

**Source:** <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/guidance-on-ai-and-data-protection/how-do-we-ensure-fairness-in-ai/>  
**Source:** <https://edpb.europa.eu/sites/default/files/files/file1/edpb_guidelines_201904_dataprotection_by_design_and_by_default_v2.0_en.pdf>

---

## 6. Your Responsibilities as a Deployer

When you use IVD to build AI-powered systems, you are the **deployer** of those systems.
The obligations that apply to your system are yours, not IVD's.

### 6.1 EU AI Act (Regulation (EU) 2024/1689)

Under Article 25 of the AI Act, deployers of high-risk AI systems bear specific
obligations regardless of the tool they used to build the system. If you are building
a system covered by Annex III using IVD:

- You must implement Article 9 risk management for your system
- You must provide Article 13 transparency documentation that accurately reflects your
  *current* system (stale IVD intent artifacts do not satisfy this obligation)
- You must implement Article 14 human oversight — IVD's Step 3 review supports this,
  but skipping it eliminates compliance

**Source:** <https://artificialintelligenceact.eu/article/14/>

### 6.2 Colorado AI Act (SB 24-205)

Effective June 30, 2026, Colorado Revised Statute § 6-1-1701 et seq. (SB 24-205)
requires developers and deployers of high-risk AI systems used in **consequential
decisions** (employment, housing, financial services, insurance, education, healthcare,
legal) to:

- Conduct algorithmic discrimination impact assessments
- Notify affected consumers before consequential decisions
- Provide the right to appeal and request human review

If you deploy an IVD-assisted system that makes consequential decisions affecting
Colorado residents, these obligations apply to you.

**Source:** <https://leg.colorado.gov/bills/SB24-205>

### 6.3 GDPR (if applicable to your users)

If your AI system processes personal data of EU residents, GDPR applies to you as a
controller. IVD intent artifacts used to document your system may support GDPR
Article 25 (data protection by design) and Article 13 (transparency) compliance — but
only if those artifacts are accurate, current, and substantive. Structural compliance
(artifacts exist) without substantive compliance (artifacts accurately constrain the
system) does not satisfy the regulation.

**Source:** <https://eur-lex.europa.eu/eli/reg/2016/679/oj>

### 6.4 CCPA/CPRA (if applicable)

If your business meets California Consumer Privacy Act thresholds (Cal. Civ. Code
§§ 1798.100–1798.199.100: annual gross revenue > $25M, or data of ≥ 100,000
California consumers/households, or ≥ 50% revenue from selling personal information),
CCPA/CPRA applies to your processing of California residents' data. IVD provides
no CCPA compliance coverage.

**Source:** <https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&lawCode=CIV&part=4&title=1.81.5.>

---

## 7. Known Architectural Limitation — Hosted Server and Local Filesystems

The hosted MCP server at `mcp.ivdframework.dev` **cannot access your local
filesystem**. Path-based tools (`ivd_assess_coverage`, `ivd_list_features`,
`ivd_validate` with a file path, `ivd_search` over a local project) will not find
your files when called against a local path — they operate against the server's own
filesystem only.

This is not a bug; it is a consequence of the remote service architecture. If you
need these tools to operate against your local project files, use a self-hosted
deployment.

This limitation is a material fact for any organization evaluating IVD for compliance
documentation purposes under EU AI Act Article 13 or FTC Section 5.

---

## 8. No Warranty

THE IVD FRAMEWORK, HOSTED SERVER, AND ALL ASSOCIATED TOOLS ARE PROVIDED "AS IS,"
WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, ACCURACY OF AI-GENERATED
OUTPUTS, REGULATORY COMPLIANCE, OR NON-INFRINGEMENT.

USE OF IVD DOES NOT GUARANTEE THAT YOUR AI SYSTEM WILL COMPLY WITH ANY LAW, REGULATION,
OR STANDARD, INCLUDING BUT NOT LIMITED TO THE EU AI ACT, GDPR, CCPA/CPRA, NIST AI RMF,
OR THE COLORADO AI ACT.

---

## 9. Limitation of Liability

TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT SHALL THE IVD PROJECT,
ITS CONTRIBUTORS, OR ITS MAINTAINERS BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL,
CONSEQUENTIAL, OR PUNITIVE DAMAGES (INCLUDING BUT NOT LIMITED TO LOSS OF DATA, LOSS OF
PROFITS, REGULATORY FINES OR PENALTIES, OR BUSINESS INTERRUPTION) ARISING OUT OF OR
IN CONNECTION WITH YOUR USE OF IVD, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.

NOTHING IN THIS SECTION LIMITS LIABILITY FOR FRAUD, GROSS NEGLIGENCE, OR INTENTIONAL
MISCONDUCT.

---

## 10. Security Vulnerabilities

To report a security vulnerability in IVD (including the hosted server), follow the
responsible disclosure process in [`SECURITY.md`](SECURITY.md). Do not open a public
GitHub issue for security vulnerabilities.

---

## 11. Changes to This Document

Material changes to this document will be noted in `DECISIONS.md` with an FDR entry.
The effective date at the top of this file reflects the last revision. This document
does not have automatic email notification — check the repository for the current
version before relying on it.

---

## 12. Reference Index

All legal sources cited in this document, with official URLs and verification dates:

| Source | Official URL | Verified |
|--------|-------------|---------|
| EU AI Act (Regulation 2024/1689) — full text | <https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ:L_202401689> | 2026-05-10 |
| EU AI Act — interactive article explorer | <https://artificialintelligenceact.eu/the-act/> | 2026-05-10 |
| EU AI Act Article 9 (risk management) | <https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-9> | 2026-05-10 |
| EU AI Act Article 13 (transparency) | <https://www.aiact-info.eu/regulation/aiact/article/13/> | 2026-05-10 |
| EU AI Act Article 14 (human oversight) | <https://artificialintelligenceact.eu/article/14/> | 2026-05-10 |
| EU AI Act Article 25 (deployer responsibilities) | <https://artificialintelligenceact.eu/article/25/> | 2026-05-10 |
| EU AI Act Article 50 (transparency obligations) | <https://www.euaiact.com/article/50> | 2026-05-10 |
| GDPR — full text (EUR-Lex) | <https://eur-lex.europa.eu/eli/reg/2016/679/oj> | 2026-05-10 |
| GDPR Article 22 — automated decision-making (ICO) | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/automated-decision-making-and-profiling/> | 2026-05-10 |
| GDPR Article 25 — data protection by design (EDPB) | <https://edpb.europa.eu/sites/default/files/files/file1/edpb_guidelines_201904_dataprotection_by_design_and_by_default_v2.0_en.pdf> | 2026-05-10 |
| GDPR Chapter V — international transfers (EDPB) | <https://www.edpb.europa.eu/sme-data-protection-guide/international-data-transfers_en> | 2026-05-10 |
| Standard Contractual Clauses (European Commission) | <https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/standard-contractual-clauses-scc_en> | 2026-05-10 |
| ICO AI and data protection guidance | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/> | 2026-05-10 |
| ICO fairness in AI guidance | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/guidance-on-ai-and-data-protection/how-do-we-ensure-fairness-in-ai/> | 2026-05-10 |
| NIS2 Directive (EUR-Lex) | <http://data.europa.eu/eli/dir/2022/2555/2022-12-27> | 2026-05-10 |
| Cyber Resilience Act summary (EC) | <https://digital-strategy.ec.europa.eu/en/policies/cyber-resilience-act> | 2026-05-10 |
| NIST AI RMF 1.0 (PDF) | <https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf> | 2026-05-10 |
| NIST AI 600-1 GenAI Profile | <https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence> | 2026-05-10 |
| FTC Act § 45 (15 U.S.C.) | <https://www.law.cornell.edu/uscode/text/15/45> | 2026-05-10 |
| FTC AI guidance page | <https://www.ftc.gov/business-guidance/artificial-intelligence> | 2026-05-10 |
| FTC — "Keep Your AI Claims in Check" (Feb 2023) | <https://www.ftc.gov/business-guidance/blog/2023/02/keep-your-ai-claims-check> | 2026-05-10 |
| FTC — AI privacy/confidentiality (Jan 2024) | <https://www.ftc.gov/policy/advocacy-research/tech-at-ftc/2024/01/ai-companies-uphold-your-privacy-confidentiality-commitments> | 2026-05-10 |
| FTC Operation AI Comply (Sept 2024) | <https://www.ftc.gov/news-events/news/press-releases/2024/09/ftc-announces-crackdown-deceptive-ai-claims-schemes> | 2026-05-10 |
| CCPA/CPRA statute | <https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&lawCode=CIV&part=4&title=1.81.5.> | 2026-05-10 |
| Colorado SB 24-205 (AI Act) | <https://leg.colorado.gov/bills/SB24-205> | 2026-05-10 |
| OpenAI Data Processing Addendum | <https://openai.com/policies/data-processing-addendum/> | 2026-05-10 |
| DigitalOcean Data Processing Agreement | <https://www.digitalocean.com/legal/data-processing-agreement> | 2026-05-10 |

---

*This document is not legal advice. Consult qualified legal counsel before making
compliance decisions based on this text.*
