# Data Processing Agreement

> **Version:** 1.0 · **Template effective:** May 10, 2026
>
> This Data Processing Agreement ("DPA") is entered into between Leo Celis ("IVD",
> "Processor") and the organization identified in the signature block below ("Customer",
> "Controller"). It supplements the IVD Terms of Service and governs IVD's processing
> of personal data on the Controller's behalf, as required by GDPR Article 28.
>
> **How to execute:** Email [leo@leocelis.com](mailto:leo@leocelis.com) with subject
> "DPA Request" and your organization details. IVD will return a countersigned copy.
> Until a signed DPA is in place, **do not transmit personal data through the hosted
> server.**

---

## Parties

**Controller (Customer):**
- Organization name: _______________________________________________
- Address: _______________________________________________
- Contact: _______________________________________________
- Email: _______________________________________________

**Processor (IVD):**
- Leo Celis, operating ivdframework.dev / mcp.ivdframework.dev
- Email: [leo@leocelis.com](mailto:leo@leocelis.com)

---

## 1. Subject Matter and Duration

**1.1 Subject matter:** IVD processes personal data on behalf of the Controller solely
to provide the hosted MCP server service at `mcp.ivdframework.dev`, as described in
the Terms of Service and this DPA.

**1.2 Duration:** This DPA is effective from the date of last signature below and
continues for as long as IVD processes personal data on behalf of the Controller, or
until the underlying Terms of Service are terminated, whichever comes first.

**1.3 Nature of processing:** Transmission, temporary in-memory processing, and
return of results. No persistent storage of personal data in IVD's own application
layer beyond the active session.

---

## 2. Categories of Personal Data and Data Subjects

The categories of personal data and data subjects processed under this DPA depend
entirely on what the Controller transmits through hosted server tool arguments.

**IVD processes only the data the Controller chooses to transmit.** IVD's hosted
server is not designed for personal data processing. The Controller acknowledges this
and accepts that the Controller is responsible for minimizing personal data in tool
arguments consistent with GDPR Article 5(1)(c) (data minimization).

**Anticipated categories** (Controller to complete):

| Category | Examples | Included? |
|----------|---------|-----------|
| Identifiers | Names, emails, usernames | ☐ Yes / ☐ No |
| Professional data | Job titles, employer | ☐ Yes / ☐ No |
| Technical data | Code, system architecture details | ☐ Yes / ☐ No |
| Behavioral data | Correction patterns, usage notes | ☐ Yes / ☐ No |
| Other (specify) | _____________________________ | ☐ Yes / ☐ No |

**Anticipated data subjects** (Controller to complete):
☐ Employees  ☐ Contractors  ☐ End users  ☐ Other: ___________________

---

## 3. Purpose and Legal Basis

**3.1 Purpose:** IVD processes personal data solely for the purpose of executing the
MCP tool calls requested by the Controller's AI agents and returning results to them.
IVD will not process personal data for any other purpose without the Controller's prior
written instruction.

**3.2 Documented instructions:** The Controller's instructions to IVD are contained
in: (a) the Terms of Service, (b) this DPA, and (c) the parameters of each tool call
made through the hosted server. IVD will notify the Controller if it believes any
instruction infringes applicable data protection law (GDPR Art. 28(3)(h)).

**3.3 Legal basis:** The Controller is responsible for ensuring a lawful legal basis
under GDPR Article 6 for all personal data it directs IVD to process.

---

## 4. Processor Obligations

IVD, as Processor, agrees to:

**4.1 Process only on instructions:** Process personal data only in accordance with
the Controller's documented instructions, except where required by applicable law. In
such cases, IVD will notify the Controller before processing unless prohibited by law.

**4.2 Confidentiality:** Ensure that all personnel authorized to process personal
data are bound by confidentiality obligations.

**4.3 Security:** Implement appropriate technical and organizational security measures
per GDPR Article 32 and Section 8 of the Privacy Policy, including:
- HTTPS/TLS encryption for all data in transit
- API key authentication with per-user access controls
- DigitalOcean-managed Redis with TLS for session state

**4.4 Sub-processor management:** Engage sub-processors only as listed in Section 5
of this DPA, and require each sub-processor to meet equivalent data protection
obligations.

**4.5 Data subject rights:** Assist the Controller in fulfilling data subject rights
requests (GDPR Arts. 15–22) to the extent technically feasible, given that IVD does
not retain tool argument content beyond the active session.

**4.6 Security assistance:** Assist the Controller in meeting obligations under GDPR
Articles 32–36 (security, breach notification, DPIA). In the event of a personal data
breach, IVD will notify the Controller without undue delay and not later than 48 hours
after becoming aware, to allow the Controller to meet its 72-hour notification
obligation under GDPR Article 33.

**4.7 Deletion / return:** Upon termination of the DPA or on the Controller's request:
confirm deletion of any personal data that may have been retained in operational logs.
Given that tool argument content is not retained in IVD's application layer, the
primary deletion obligation concerns provider-level logs, which are subject to each
sub-processor's data handling practices.

**4.8 Audit rights:** Make available, on written request with reasonable notice, the
information necessary to demonstrate compliance with this DPA. IVD may satisfy audit
requests by providing relevant certifications, security documentation, or responses to
a standard questionnaire in lieu of on-site audits.

---

## 5. Sub-processors

IVD uses the following sub-processors under this DPA. All sub-processors are bound by
data protection obligations equivalent to those in this DPA.

| Sub-processor | Location | Role | DPA |
|---------------|----------|------|-----|
| DigitalOcean, Inc. | United States | App hosting, managed Redis, infrastructure | <https://www.digitalocean.com/legal/data-processing-agreement> |
| OpenAI, L.L.C. | United States | Embedding generation for `ivd_search` only | <https://openai.com/policies/data-processing-addendum/> |

**Changes to sub-processors:** IVD will give the Controller at least **14 days' prior
written notice** of any intended change to sub-processors (addition or replacement).
The Controller may object to a new sub-processor by notifying IVD in writing within
14 days. If the parties cannot resolve the objection, either party may terminate this
DPA with immediate effect without penalty.

---

## 6. International Data Transfers

**6.1 US processing:** Both DigitalOcean and OpenAI are US-based. Transfers from the
EEA to the United States are covered by the EU-US Standard Contractual Clauses (SCCs)
in the form approved by the European Commission Decision of June 4, 2021, which are
incorporated into this DPA by reference.

**Controller-to-Processor SCCs:** The Module 2 (Controller to Processor) SCCs apply
to transfers of personal data by the Controller to IVD. The optional clauses are
adopted as follows:
- Clause 7 (Docking clause): Not adopted
- Clause 11 (Redress): Option 1 (not adopted)
- Clause 17 (Governing law): Ireland
- Clause 18 (Choice of forum): Irish courts

**IVD-to-Sub-processor SCCs:** IVD represents that its agreements with DigitalOcean
and OpenAI include Module 3 (Processor to Processor) SCCs or equivalent safeguards.

**6.2 Transfer impact assessment:** The Controller acknowledges that US law (including
FISA §702 and EO 12333) may authorize access to data processed in the United States by
US-based providers. The Controller is responsible for conducting a Transfer Impact
Assessment (TIA) for its own risk profile before relying on SCCs alone.

Standard Contractual Clauses:
<https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/standard-contractual-clauses-scc_en>

---

## 7. Controller Obligations

The Controller warrants and agrees to:

1. Have a lawful legal basis under GDPR Article 6 for all personal data it directs
   IVD to process under this DPA
2. Comply with GDPR Article 5 data minimization — only transmit personal data that is
   necessary for the specific tool call purpose
3. Not transmit special categories of personal data (GDPR Article 9) without explicit
   prior agreement with IVD and additional safeguards in place
4. Provide timely, accurate documented instructions to IVD
5. Notify IVD promptly of any data subject requests that require IVD's assistance
6. Ensure that IVD's use of sub-processors (Section 5) is covered by the Controller's
   own legal basis and privacy notices

---

## 8. Liability

**8.1** As between the parties, liability under this DPA is subject to the limitations
in the Terms of Service, Section 9.

**8.2** GDPR Article 82 governs liability to data subjects. Where a data subject
seeks compensation from IVD as Processor, IVD may be exempt from liability if it
proves that it is not in any way responsible for the event giving rise to the damage
(GDPR Art. 82(3)).

**8.3** The Controller indemnifies IVD against all claims, costs, and fines arising
from the Controller's failure to comply with its obligations as Data Controller under
GDPR, including but not limited to: failing to have a lawful basis for processing,
transmitting special categories of data without authorization, or failing to conduct
a required DPIA.

---

## 9. Governing Law

This DPA is governed by the laws of the **State of Florida, United States**, except
that the SCCs in Section 6 are governed by the law of the EU member state specified
in SCC Clause 17.

---

## 10. Termination and Survival

This DPA terminates automatically upon termination of the Terms of Service. Sections
4.7 (deletion), 6 (international transfers), 7 (controller obligations), 8 (liability),
and any obligations that arose during the DPA term survive termination.

---

## Signatures

By signing below, the parties agree to be bound by this DPA as of the date of last
signature.

**Controller (Customer):**

Name: _______________________________________________

Title: _______________________________________________

Organization: _______________________________________________

Date: _______________________________________________

Signature: _______________________________________________

---

**Processor (IVD):**

Name: Leo Celis

Title: Owner / Controller

Date: _______________________________________________

Signature: _______________________________________________

---

*To request a countersigned copy of this DPA, email [leo@leocelis.com](mailto:leo@leocelis.com)
with subject "DPA Request" and your organization details.*
