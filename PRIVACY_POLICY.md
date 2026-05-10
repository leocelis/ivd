# Privacy Policy

> **Version:** 1.0 · **Effective:** May 10, 2026
>
> This Privacy Policy applies to the IVD website (`ivdframework.dev`), the hosted MCP
> server (`mcp.ivdframework.dev`), and all associated services (collectively, the
> "Service"). It does not apply to self-hosted deployments of the IVD codebase on your
> own infrastructure — in those deployments, you control all data.
>
> This Policy is provided in compliance with **GDPR Article 13** (information to be
> provided at the time personal data is collected) and **FTC Act Section 5** (privacy
> and confidentiality commitments).

**Data Controller:**  
Leo Celis  
[leo@leocelis.com](mailto:leo@leocelis.com)  
ivdframework.dev

*IVD has not appointed a Data Protection Officer (DPO). The controller contact above
handles all data protection inquiries.*

---

## 1. What Data We Collect and Why

### 1.1 Hosted server — tool call arguments

**What:** Every call to a tool on the hosted MCP server transmits the arguments you
provide. This includes `yaml_content`, `project_root`, `artifact_path`, correction
text, `query` strings, and any other parameters in the tool call.

**Why:** To execute the requested tool and return a result to your MCP client.

**Legal basis (GDPR Art. 6):** Legitimate interests (Art. 6(1)(f)) — processing is
necessary to provide the service you requested. For users in a contractual relationship
with IVD, performance of a contract (Art. 6(1)(b)).

**Retention:** Tool argument content is not retained in IVD's own application storage
beyond the active processing session. However, **provider-level operational logs** may
retain records of requests for up to 30 days as part of normal infrastructure operations
(see Sub-processors, Section 4). IVD does not use tool argument content for model
training, analytics, or any purpose other than executing the requested tool.

**Warning:** IVD's hosted server is not designed for personal data. **Do not transmit
personal data** (names, emails, IDs, or any information relating to an identified or
identifiable natural person) through tool arguments. See Section 7 (Your
Responsibilities).

---

### 1.2 API key issuance (GitHub Discussions)

**What:** When you request an API key via a GitHub Discussion, GitHub collects your
GitHub username and the content of your request. IVD receives: your GitHub username
and any contact information you provide.

**Why:** To issue and manage your API key.

**Legal basis (GDPR Art. 6):** Performance of a contract / pre-contractual steps
(Art. 6(1)(b)).

**Retention:** IVD retains API key records for the duration of your active use plus
a reasonable period for security auditing (typically 90 days after key revocation or
last use).

**Note:** GitHub's own privacy policy governs GitHub's handling of your data in
Discussions: <https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement>

---

### 1.3 Website analytics

**What:** Basic server access logs (IP address, browser/client identifier, requested
URL, timestamp). IVD does not deploy third-party analytics scripts (no Google Analytics,
no tracking pixels).

**Why:** Operational monitoring and security.

**Legal basis (GDPR Art. 6):** Legitimate interests (Art. 6(1)(f)) — monitoring
service health and detecting abuse.

**Retention:** Access logs are retained for up to 30 days.

---

### 1.4 Security incident records

**What:** If you report a security vulnerability or a suspected data breach, IVD
retains records of that communication and the response.

**Why:** To resolve the incident and meet legal obligations (GDPR Art. 33; applicable
breach notification laws).

**Legal basis (GDPR Art. 6):** Compliance with a legal obligation (Art. 6(1)(c)).

**Retention:** Incident records are retained for 3 years.

---

## 2. What We Do Not Do

IVD does **not**:

- Use tool argument content to train AI models (ours or third parties')
- Sell, rent, or share your data with third parties for marketing purposes
- Build behavioral profiles from your usage
- Use automated decision-making or profiling that produces legal or similarly significant
  effects concerning you (GDPR Art. 22)
- Share personal data with government authorities except where legally required

---

## 3. International Data Transfers

The hosted server runs on **DigitalOcean App Platform (US East region)**. If you are
located in the European Economic Area (EEA), United Kingdom, or Switzerland, any data
transmitted through tool calls constitutes a transfer of data to the United States under
GDPR Chapter V.

**Current transfer mechanism:** IVD does not currently have Standard Contractual Clauses
(SCCs) in place with its users. This is a known compliance gap. **EU/EEA controllers
must not transmit personal data through the hosted server until SCCs or equivalent
safeguards are established.** Use the self-hosted path for any processing involving
personal data of EEA residents.

If you require a Data Processing Agreement and SCCs for your organization, contact
[leo@leocelis.com](mailto:leo@leocelis.com).

EU-US Data Privacy Framework reference:
<https://www.dataprivacyframework.gov/>

EDPB international transfers guidance:
<https://www.edpb.europa.eu/sme-data-protection-guide/international-data-transfers_en>

---

## 4. Sub-processors

IVD uses the following sub-processors to operate the hosted server. Each sub-processor
handles data only as necessary to perform their specific function.

| Sub-processor | Location | Role | Privacy/DPA |
|---------------|----------|------|------------|
| DigitalOcean, Inc. | United States | App hosting, Redis session management, infrastructure logs | [Privacy Policy](https://www.digitalocean.com/legal/privacy-policy) · [DPA](https://www.digitalocean.com/legal/data-processing-agreement) |
| OpenAI, L.L.C. | United States | Embedding generation for `ivd_search` (query text sent to embeddings API) | [Privacy Policy](https://openai.com/policies/privacy-policy/) · [DPA](https://openai.com/policies/data-processing-addendum/) |

IVD will update this table when sub-processors change. Material changes will be noted
in `DECISIONS.md`.

**OpenAI data handling note:** IVD uses the OpenAI API via the standard API endpoint.
Per OpenAI's API data usage policy (as of this Policy's effective date), API inputs are
not used to train OpenAI's models by default. Verify the current policy at
<https://openai.com/policies/api-data-usage-policies> before transmitting sensitive
content through `ivd_search`.

---

## 5. Your Rights (EEA, UK, and Swiss Residents)

Under GDPR and applicable national law, you have the following rights regarding personal
data IVD holds about you:

| Right | What it means |
|-------|---------------|
| **Access** (Art. 15) | Request a copy of the personal data IVD holds about you |
| **Rectification** (Art. 16) | Request correction of inaccurate personal data |
| **Erasure** (Art. 17) | Request deletion of your personal data ("right to be forgotten") |
| **Restriction** (Art. 18) | Request that IVD restrict processing of your data |
| **Portability** (Art. 20) | Receive your data in a machine-readable format |
| **Object** (Art. 21) | Object to processing based on legitimate interests |
| **Withdraw consent** (Art. 7(3)) | Where processing is based on consent, withdraw at any time |

**To exercise any right:** Email [leo@leocelis.com](mailto:leo@leocelis.com) with the
subject "GDPR Data Request." IVD will respond within 30 days (extendable to 60 days for
complex requests with notice).

**Right to lodge a complaint:** You have the right to lodge a complaint with your
national supervisory authority. Find your authority at:
<https://www.edpb.europa.eu/about-edpb/about-edpb/members_en>

For UK residents, the supervisory authority is the Information Commissioner's Office
(ICO): <https://ico.org.uk/make-a-complaint/>

---

## 6. California Residents (CCPA/CPRA)

California Civil Code §§ 1798.100–1798.199.100 grants California residents additional
rights. IVD does not currently meet CCPA applicability thresholds (< $25M annual
revenue; < 100,000 California consumers), but provides the following disclosures
voluntarily and in anticipation of future applicability:

**Categories of personal information collected:** identifiers (GitHub username, email
address if provided); internet/electronic activity (API key usage logs, server access
logs).

**Purpose:** Service provision, security monitoring.

**Do Not Sell or Share:** IVD does not sell or share personal information as defined
under CCPA/CPRA.

**Retention:** As specified in Section 1 above.

To exercise CCPA rights, email [leo@leocelis.com](mailto:leo@leocelis.com).

---

## 7. Your Responsibilities

You are the data controller for any personal data you choose to transmit through IVD
tools. IVD acts as a processor of that data. **The decision to transmit personal data
through the hosted server is yours; the legal obligation to ensure you have a lawful
basis for that transmission is also yours.**

IVD explicitly instructs you not to transmit the following through hosted server tool
arguments:
- Personal data (any information relating to an identified or identifiable natural person)
- Sensitive personal data (health, biometric, genetic, political, religious, racial, or
  sexual orientation data)
- Any data subject to sector-specific regulation (health records under HIPAA, financial
  data under PCI-DSS, etc.)

If you transmit personal data in violation of this instruction, you bear sole
responsibility for the GDPR compliance of that transfer.

---

## 8. Security

IVD implements the following security measures for the hosted server:

- HTTPS/TLS for all data in transit
- API key authentication for all hosted server access
- DigitalOcean-managed Redis with TLS for session storage
- Access logging with anomaly monitoring

IVD does not guarantee that these measures will prevent all unauthorized access or data
breaches. In the event of a personal data breach affecting data you transmitted through
the hosted server, IVD will notify you within 72 hours of becoming aware of it to assist
you in meeting your own breach notification obligations under GDPR Article 33.

---

## 9. Children

The Service is not directed at children under 18. IVD does not knowingly collect personal
data from anyone under 18. If you believe a minor has provided personal data through the
Service, contact [leo@leocelis.com](mailto:leo@leocelis.com) for immediate deletion.

---

## 10. Changes to This Policy

IVD may update this Privacy Policy by publishing a revised version with an updated
effective date. Material changes — particularly those affecting your rights or the
categories of data collected — will be noted in `DECISIONS.md` with an FDR entry.

For hosted-server users who are EU controllers, material changes to the processing
purposes, legal basis, or sub-processor list constitute a change to the processor
obligations under GDPR Art. 28(3). IVD will provide at least 14 days' advance notice
of such changes through the repository.

---

## 11. Contact

For all privacy inquiries, data subject requests, security incidents, or questions about
this Policy:

**Email:** [leo@leocelis.com](mailto:leo@leocelis.com)  
**Subject line:** Privacy Inquiry / GDPR Request / Security Incident  

IVD aims to respond to all inquiries within 5 business days and to fulfill data subject
requests within 30 days.

---

## 12. Legal Basis Summary (GDPR Article 13(1)(c))

| Processing activity | Legal basis | GDPR article |
|--------------------|-------------|--------------|
| Tool call execution (hosted server) | Legitimate interests / Contract performance | Art. 6(1)(f) / Art. 6(1)(b) |
| API key issuance and management | Contract performance | Art. 6(1)(b) |
| Website access logs | Legitimate interests | Art. 6(1)(f) |
| Security incident records | Legal obligation | Art. 6(1)(c) |
| Responding to data subject requests | Legal obligation | Art. 6(1)(c) |

---

*This Privacy Policy is not legal advice. If you are implementing a GDPR compliance
program, consult qualified legal counsel.*
