# Literate Programming via Dev Agent: A Practical Cookbook

**Purpose:** Apply Literate Programming principles to feature/module development using AI agent prompting  
**Audience:** Developers working with AI assistants to build or refactor business logic  
**Version:** 2.1  
**Last Updated:** January 24, 2026  
**Status:** Integrated with Intent-Verified Development v1.2

---

## 🚨 Important Note

This cookbook represents **LP-inspired documentation practices**—not pure Literate Programming in Knuth's sense. We borrow LP principles (document WHY, preserve reasoning) but use familiar tools and AI-assisted synchronization.

**For the evolved paradigm,** see: [`framework.md`](../framework.md) - Takes LP principles further with executable, verifiable understanding.

**NEW in IVD v1.2:** [`ivd_system_intent.yaml`](../ivd_system_intent.yaml) - Master intent defining all rules for extending the IVD framework itself.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Core Principles](#core-principles)
3. [The Complete Workflow](#the-complete-workflow)
4. [Example: Lead Qualification Module](#example-lead-qualification-module)
5. [Prompt Templates Library](#prompt-templates-library)
6. [Quality Checklist](#quality-checklist)
7. [Common Pitfalls](#common-pitfalls)
8. [Real-World Case Studies](#real-world-case-studies)
9. [Evolution to Intent-Verified Development](#evolution-to-intent-verified-development)
10. [IVD v1.2 Updates](#ivd-v12-updates)
11. [Cursor Rules Integration](#cursor-rules-integration)

---

## Introduction

### What is This Cookbook?

This cookbook shows how to use **AI agent prompting** to apply **Literate Programming (LP) principles** when developing or refactoring features/modules. The goal: preserve the WHY behind decisions, not just the WHAT of implementation.

### Honest Positioning

**This is NOT pure Literate Programming.** Knuth's LP requires:
- Single source with prose and code interleaved
- Special tools (WEB, CWEB) to tangle/weave
- Code written in human-logical order (not compiler order)

**This cookbook teaches:**
- LP **principles** applied with standard tools
- Rich documentation alongside code (not unified)
- AI agents as synchronization mechanism
- Pragmatic approach that teams actually adopt

**Think of it as:** "Comprehensive Documentation via AI Agents, Inspired by LP Principles"

### Why LP + AI Agents?

**Traditional development:**
- Code explains WHAT (10-15% knowledge capture)
- WHY is lost to team turnover, memory fade, time pressure
- Future maintainers inherit unexplained decisions

**LP + AI agents:**
- Agent enforces documentation discipline humans skip
- WHY is captured systematically (60-80% knowledge capture)
- Business logic becomes self-explanatory
- 20-30% faster onboarding for new developers

### When to Use This Cookbook

Apply these patterns when:
- Building new features with complex business logic
- Refactoring existing modules that lack explanation
- Investigating production incidents (preserve learnings)
- Onboarding to unfamiliar codebases
- Documenting threshold/validation decisions

### When NOT to Use This Cookbook

**Don't apply LP to:**
- Simple utility functions with obvious logic
- Self-explanatory operations
- Standard patterns everyone knows
- Temporary/prototype code
- Rapidly changing features (documentation becomes stale burden)

**The maintenance burden reality:**
Maintaining both code and narrative is **extra work**. LP is an investment that pays off for:
- Critical business logic
- Complex decision points
- Long-lived systems
- High-turnover teams

**But NOT for:**
- Trivial code
- Throwaway prototypes
- Frequently changing features

**The discipline:** Apply LP where knowledge preservation matters. Skip it where maintenance burden exceeds benefit.

---

## Core Principles

### 0. Human Understanding First, Machine Execution Second

**The foundational insight of Literate Programming:**

Programs should be written for **human beings** to read and understand, not primarily for machines to execute. The goal is not just to instruct computers, but to **communicate with other programmers and your future self**.

**What this means:**
- Code structure follows **human logic**, not compiler order
- Explanation is **primary**, implementation is byproduct
- Documentation grows **during development**, not after
- The program **IS** the documentation; documentation **IS** the program

**In AI-driven development:**
As AI writes more code, human understanding becomes the scarce, valuable skill. LP provides the paradigm for preserving that understanding.

### 1. Document WHY, Not WHAT

**Bad (traditional):**
```python
# Check if score is above threshold
if score >= 0.70:
    return True
```

**Good (literate):**
```python
# Qualify lead at 0.70 threshold based on 2025-12 A/B test
# showing this balances precision (85%) vs recall (70%).
# Alternative 0.80 threshold rejected: too few qualified leads.
# See playground/lead_analysis_2025-12.ipynb for validation.
if score >= 0.70:
    return True
```

### 2. Preserve Decision Context

Capture:
- **Rationale:** Why this approach?
- **Alternatives:** What else was considered?
- **Trade-offs:** What did we gain/lose?
- **Evidence:** What data supports this?
- **Incidents:** What failures shaped this?

### 3. Synchronize Code and Documentation

When code changes, documentation MUST update. Use agents to enforce this discipline.

### 4. Explain to Discover Bugs

The act of explaining logic reveals flaws. Use agent documentation prompts as a debugging technique.

### 5. Understanding Becomes More Valuable Than Writing (AI Era)

As AI generates more code, the human skill of **writing code** diminishes in importance. The skill of **understanding code** increases dramatically.

**The paradigm shift:**
- Old model: Developer value = ability to write code
- New model: Developer value = ability to understand, validate, and explain code

**Your LP contribution in AI-driven development:**
- **Comprehension:** Understand what AI generated and why it works
- **Validation:** Verify correctness against requirements
- **Explanation:** Document rationale for future maintainers
- **Integration:** Ensure code fits existing architecture
- **Judgment:** Decide when AI output is acceptable

### 6. Favor Lightweight Over Heavy Tooling

**Critical principle:** Use simple, familiar documentation tools that your team will actually adopt. Avoid specialized LP systems (WEB, CWEB, noweb) that create friction.

**Lightweight approach:**
- Markdown files with code references
- Computational notebooks for experiments (Jupyter, not custom systems)
- Standard code comments for critical logic
- Documentation generators the team already knows

**Why lightweight wins:**
- Lower barrier to entry
- Better adoption (no friction = consistent use)
- Easier maintenance
- Team velocity maintained

**The balance:**
- Literate **thinking**: YES (document why, not just what)
- Literate **tooling**: NO (unless team already uses it)
- Literate **principles**: YES (preserve reasoning)
- Literate **purity**: NO (pragmatism over orthodoxy)

### 7. Computational Notebooks for Experiments

Use notebooks (Jupyter, Quarto) to document research processes, not just results.

**What to document in notebooks:**
- Hypothesis and motivation (why this experiment?)
- Data preparation steps with rationale
- Alternative approaches tested
- Results with interpretation
- Decision made based on findings

**The pattern:**
```
playground/
  ├── lead_scoring_validation_2025-12.ipynb
  ├── routing_confidence_threshold_2026-01.ipynb
  └── data_quality_thresholds_2025-11.ipynb
```

Link from production code to these notebooks when documenting decisions.

### 8. Prompt Structure = Documentation Structure

**The insight:** Writing effective prompts uses the same skills as writing good documentation.

**Both require:**
1. High-level goal explanation (what are we trying to achieve?)
2. Context and constraints (what matters, what to avoid?)
3. Step-by-step logic (how should this work?)
4. Expected outcomes (what does success look like?)
5. Edge cases and examples (what about unusual situations?)

**Why this matters for LP via agents:**
- Developers who document well **prompt well**
- Practice explaining to humans transfers to explaining to AI
- The discipline of articulating logic clearly is the same skill

**Practical implication:**
When you struggle to write effective prompts for LP tasks, practice explaining code to humans first. The skill transfers directly.

---

## The Complete Workflow

### Overview

```
Phase 1: Discovery & Assessment
    ↓
Phase 2: Rationale Extraction
    ↓
Phase 3: Implementation with LP
    ↓
Phase 4: Synchronization Check
    ↓
Phase 5: Validation Review
```

### Phase 1: Discovery & Assessment

**Goal:** Understand current state, identify missing WHY documentation

**Agent Prompt Pattern:**
```
"Analyze the [FEATURE/MODULE] for Literate Programming gaps:

1. INVENTORY:
   - List all business rules, thresholds, validations
   - Identify decision points (if/else, switches, routing)
   - Map dependencies between components

2. ASSESS DOCUMENTATION:
   - Which decisions have WHY explanation?
   - Which lack rationale/alternatives/trade-offs?
   - Where are thresholds undocumented?
   - Which edge cases have no explanation?

3. KNOWLEDGE GAPS:
   - What would new developer struggle to understand?
   - What decisions would be hard to modify safely?
   - What incidents/requirements aren't captured?

Report as structured list with:
- File/line numbers
- Decision description
- Current documentation status
- Missing elements (rationale/alternatives/trade-offs/evidence)"
```

**Deliverable:** Gap analysis document identifying where LP is needed

---

### Phase 2: Rationale Extraction

**Goal:** Extract or infer the WHY behind existing decisions

**Agent Prompt Pattern:**
```
"For [SPECIFIC DECISION/THRESHOLD] in [MODULE]:

RESEARCH:
1. Search codebase for related:
   - Experiments (playground/, notebooks)
   - Tests that validate this decision
   - Comments/docs that explain rationale
   - Git history/commits introducing this
   - Related ADRs or design docs

2. Search external sources:
   - Industry best practices for [domain]
   - Academic research on [technique]
   - Framework documentation for [tool]

DOCUMENT FINDINGS:
1. RATIONALE (from evidence):
   - What problem does this solve?
   - Why this approach was chosen?

2. ALTERNATIVES (infer if not documented):
   - What other approaches were possible?
   - Why might they have been rejected?

3. TRADE-OFFS:
   - Benefits of this approach
   - Costs/limitations accepted

4. VALIDATION (if found):
   - Link to experiments/tests
   - Performance data, error rates
   - A/B test results

Format as draft documentation for my review."
```

**Deliverable:** Rationale documentation (to be validated by human)

**Critical:** Human must validate inferred rationale. Agent guesses must be confirmed.

---

### Phase 3: Implementation with LP

**Goal:** Build/refactor feature with LP documentation baked in

**Agent Prompt Pattern:**
```
"Implement [FEATURE/MODULE] following Literate Programming principles:

REQUIREMENTS:
[Detailed feature requirements here]

LP DOCUMENTATION STANDARDS:
1. INLINE COMMENTS:
   - Decision points: Explain WHY, not WHAT
   - Thresholds: Document rationale + validation source
   - Edge cases: Explain why handled this way
   - Complex logic: Add explanatory prose above

2. MODULE DOCSTRING:
   - High-level purpose
   - Key decisions and rationale
   - Links to related docs (ADRs, experiments)
   - Trade-offs accepted

3. FUNCTION DOCSTRINGS:
   - Purpose and context
   - Parameter constraints (why these types/ranges?)
   - Return value meaning
   - Edge cases and error handling rationale

4. COMPANION DOCUMENTATION:
   - Create [MODULE]_DESIGN.md with:
     * Architecture rationale
     * Alternative approaches considered
     * Trade-offs analysis
     * Validation evidence
     * Related ADRs/experiments
   
   - For AI agents/models, consider Model Card format:
     * Model details (version, type, architecture)
     * Intended use (what can/cannot do)
     * Performance metrics (accuracy, error rates)
     * Limitations and warnings
     * Training data and validation
     * Ethical considerations

VALIDATION LINKS:
- Reference experiments: playground/[name]
- Reference ADRs: docs/architecture/ADR-XXX.md
- Reference incidents: "incident #123"

DELIVERABLES:
1. Implementation with LP-style comments
2. Module design document
3. List of related docs (for synchronization check)"
```

**Deliverable:** Implemented feature with rich explanatory documentation

---

### Phase 4: Synchronization Check

**Goal:** Ensure code and documentation are aligned

**Agent Prompt Pattern:**
```
"Perform synchronization check for [MODULE]:

1. CODE ↔ INLINE COMMENTS:
   - Do comments accurately describe code behavior?
   - Are thresholds in comments same as in code?
   - Do edge case comments match implementation?

2. CODE ↔ MODULE DOCS:
   - Does design doc reflect actual architecture?
   - Are listed trade-offs still accurate?
   - Do ADR references match implementation?

3. CROSS-DOCUMENT CONSISTENCY:
   - Do related ADRs need updates?
   - Do architecture docs reflect this module?
   - Are experiment notebooks still valid?
   - Do testing docs cover this logic?

4. FIND DRIFT:
   - Comments that contradict code
   - Docs describing old implementation
   - Dead references (removed experiments/ADRs)
   - Outdated performance claims

REPORT:
For each drift issue:
- Location (file:line or doc name)
- Type of drift (comment/doc mismatch)
- Current code behavior
- What doc/comment claims
- Suggested fix

Provide update checklist: files/sections needing revision."
```

**Deliverable:** Synchronization report + update checklist

---

### Phase 5: Validation Review

**Goal:** Verify LP quality before merging

**Agent Prompt Pattern:**
```
"Self-review [MODULE] against LP quality standards:

1. EXPLAINING REVEALS BUGS:
   - Re-read all explanatory comments
   - Do they expose edge cases you missed?
   - Do documented trade-offs reveal problems?
   - Does rationale suggest better approaches?

2. KNOWLEDGE PRESERVATION:
   - New developer test: Can they understand WHY?
   - Modification test: Can they safely change logic?
   - Incident test: Would future failures be preventable?

3. DOCUMENTATION QUALITY:
   - Is WHY captured, not just WHAT?
   - Are alternatives/trade-offs documented?
   - Is validation evidence linked?
   - Are incident learnings preserved?

4. COMPLETENESS:
   - All decision points explained?
   - All thresholds documented?
   - All edge cases rationalized?
   - All assumptions stated?

SCORE (1-5 scale):
- Decision rationale: [score + explanation]
- Alternative consideration: [score + explanation]
- Trade-off documentation: [score + explanation]
- Validation evidence: [score + explanation]
- Overall LP quality: [score + explanation]

GAPS IDENTIFIED:
[List remaining gaps with recommendations]

READY FOR HUMAN REVIEW: [Yes/No + reasoning]"
```

**Deliverable:** Self-assessment report for human validation

---

## Example: Lead Qualification Module

### Context

**Module:** `agent/lead_qualifier/`  
**Purpose:** Score and qualify leads based on data quality and market fit  
**Business Logic:** Thresholds, validation rules, scoring algorithms  
**Why LP Matters:** Thresholds are critical; wrong values waste sales time

---

### Phase 1: Discovery Prompt (Real Example)

```markdown
"Analyze agent/lead_qualifier/ for Literate Programming gaps:

MODULE CONTEXT:
This module qualifies leads for sales team. It scores leads on:
- Data completeness (contact info, company details)
- Market fit (industry, company size, location)
- Engagement signals (web visits, content downloads)

Leads above threshold go to sales. Bad thresholds = wasted time or missed opportunities.

YOUR TASK:
1. INVENTORY DECISIONS:
   - Scoring thresholds (where are they, what values?)
   - Validation rules (what's checked, why?)
   - Data quality gates (what defines "good data"?)
   - Edge case handling (nulls, missing fields, outliers)

2. DOCUMENTATION GAPS:
   For each decision:
   - ✅ if WHY is documented (rationale/alternatives/trade-offs)
   - ❌ if missing explanation
   - ⚠️ if partial (some context but incomplete)

3. RISK ASSESSMENT:
   - Which undocumented decisions are most critical?
   - Which would be hardest for new developer to understand?
   - Which have changed recently (git history)?

REPORT FORMAT:
## Critical Decisions Lacking Documentation

### 1. Lead Score Threshold (0.70)
- **Location:** `scoring.py:45`
- **Status:** ❌ No rationale
- **Risk:** High - directly impacts sales pipeline
- **Questions:**
  - Why 0.70 not 0.60 or 0.80?
  - What testing validated this?
  - What error rate is acceptable?

[Continue for all decisions...]

## Summary
- Total decisions: [count]
- Documented: [count] ✅
- Partially documented: [count] ⚠️
- Undocumented: [count] ❌
- High-risk gaps: [count]"
```

---

### Phase 2: Rationale Extraction (Real Example)

**Agent discovers: Threshold set to 0.70 with no documentation**

```markdown
"Research the 0.70 lead score threshold in scoring.py:

SEARCH TASKS:
1. Local codebase:
   - Search playground/ for lead scoring experiments
   - Search tests/ for threshold validation tests
   - Search git history for commit introducing 0.70
   - Search docs/ for related ADRs or decisions

2. If experiments found:
   - Summarize methodology
   - Extract key findings (precision/recall)
   - Link to validation data

3. If not found:
   - Search external sources for lead scoring best practices
   - Recommend validation experiment design

DOCUMENT:
## Lead Score Threshold: 0.70 Rationale

### Evidence Found
[If found in codebase:]
- Source: playground/lead_analysis_2025-12.ipynb
- Test period: Dec 2025, 500 leads
- Results:
  * 0.60 threshold: 75% precision, 85% recall
  * 0.70 threshold: 85% precision, 70% recall
  * 0.80 threshold: 92% precision, 50% recall
- Decision: 0.70 chosen to balance quality vs volume

[If NOT found:]
- No local validation experiments found
- External research suggests 0.65-0.75 range common
- **RECOMMENDATION:** Create validation experiment

### Inferred Rationale (NEEDS VALIDATION)
- Likely balances lead quality vs pipeline volume
- Higher = better quality but fewer leads
- Lower = more leads but more sales time wasted
- **Must validate with stakeholder**

### Alternatives
- 0.60: More leads, lower quality (rejected likely due to sales feedback)
- 0.80: Higher quality, too few leads (rejected likely due to pipeline goals)

### Trade-offs at 0.70
- Gain: 85% precision (quality leads)
- Loss: 30% of potential leads filtered out
- Acceptable if: Sales can't handle more volume

### Validation Gaps
❌ No documented experiment
❌ No A/B test results
❌ No sales team feedback captured
⚠️ Threshold may be based on guess, not data

RECOMMENDATION:
Create playground/lead_scoring_validation.ipynb to:
1. Test thresholds: 0.60, 0.65, 0.70, 0.75, 0.80
2. Measure: precision, recall, sales conversion rate
3. Interview: sales team on lead quality
4. Document: chosen threshold with evidence"
```

**Human Action Required:**
1. Validate inferred rationale with stakeholder
2. Create validation experiment if missing
3. Approve documentation for implementation

---

### Phase 3: Implementation Prompt (Real Example)

```markdown
"Refactor agent/lead_qualifier/scoring.py with LP documentation:

CONTEXT:
- Current code has 0.70 threshold with no explanation
- Validation experiment completed: playground/lead_analysis_2025-12.ipynb
- Findings: 0.70 balances 85% precision vs 70% recall
- Stakeholder: VP Sales approved 0.70 based on team capacity

LP REQUIREMENTS:
1. Add comprehensive docstring to qualify_lead():
   - Purpose and business context
   - Threshold rationale with evidence link
   - Trade-offs accepted
   - Alternative thresholds considered

2. Add inline comment before threshold check:
   - Why 0.70 specifically
   - Link to validation experiment
   - What happens if changed

3. Add edge case explanations:
   - How nulls/missing data handled
   - Why certain validation rules exist
   - Incident learnings (if any)

4. Create scoring_DESIGN.md:
   - Architecture overview
   - Scoring algorithm rationale
   - Threshold selection process
   - Validation methodology
   - Future improvement notes

CODE TO REFACTOR:
```python
def qualify_lead(score: float, data_quality: float) -> bool:
    \"\"\"Qualify lead based on score and data quality.\"\"\"
    if score >= 0.70 and data_quality >= 0.80:
        return True
    return False
```

EXPECTED OUTPUT:
Full LP-style implementation with:
- Rich docstrings capturing WHY
- Inline comments at decision points
- Links to validation evidence
- Companion design document
- List of docs to update for synchronization"
```

**Agent Output (Abbreviated):**

```python
def qualify_lead(score: float, data_quality: float) -> bool:
    """
    Qualify lead for sales team based on predictive score and data quality.
    
    BUSINESS CONTEXT:
    Sales team can handle ~50 qualified leads/day. This function gates the
    pipeline to ensure only high-probability leads reach sales, preventing
    wasted effort on low-quality prospects.
    
    THRESHOLD RATIONALE:
    Score threshold (0.70) chosen based on 2025-12 validation experiment:
    - Tested: 0.60, 0.70, 0.80 on 500-lead sample
    - Results: 0.70 achieves 85% precision, 70% recall
    - Trade-off: Filters 30% of leads to maintain quality
    - Validation: playground/lead_analysis_2025-12.ipynb
    - Approval: VP Sales (2025-12-15) based on team capacity
    
    ALTERNATIVES CONSIDERED:
    - 0.60: Higher recall (85%) but precision dropped to 75%
      Rejected: Sales feedback indicated too many poor leads
    - 0.80: Higher precision (92%) but recall dropped to 50%
      Rejected: Insufficient pipeline volume for revenue goals
    
    DATA QUALITY GATE (0.80):
    Requires complete contact information (name, email, phone).
    Based on incident #456: High-score leads with missing contact info
    created sales frustration and reduced follow-up rates.
    
    VALIDATION EVIDENCE:
    - Experiment: playground/lead_analysis_2025-12.ipynb
    - A/B Test: 30-day live test (Jan 2026) confirmed lab results
    - Sales feedback: 90% satisfaction with lead quality post-change
    
    Args:
        score: Predictive score (0.0-1.0) from lead_scoring model
        data_quality: Data completeness score (0.0-1.0)
    
    Returns:
        True if lead meets qualification thresholds, False otherwise
    
    See Also:
        - Design doc: docs/agents/lead_qualifier/scoring_DESIGN.md
        - ADR: docs/architecture/ADR-089-lead-qualification-thresholds.md
    """
    
    # Apply score threshold validated in Dec 2025 experiment
    # This balance was approved by sales leadership after live testing
    # showed 85% precision with acceptable pipeline volume (35 leads/day)
    if score >= 0.70 and data_quality >= 0.80:
        return True
    
    # Log near-miss leads for periodic review
    # Incident #456: We were missing qualified leads due to data issues
    # This logging helps identify when thresholds need adjustment
    if score >= 0.70 and data_quality < 0.80:
        log_data_quality_issue(score, data_quality)
    
    # Log high-quality data leads that scored just below threshold
    # Helps identify model improvements needed
    if score >= 0.65 and score < 0.70 and data_quality >= 0.80:
        log_near_miss_lead(score, data_quality)
    
    return False
```

**Companion Document:** `docs/agents/lead_qualifier/scoring_DESIGN.md` (created by agent)

---

### Phase 4: Synchronization Check (Real Example)

```markdown
"Verify synchronization for agent/lead_qualifier/ refactor:

SCOPE:
- Code: agent/lead_qualifier/scoring.py (just refactored)
- Docs: Potential references in architecture, ADRs, tests

CHECK 1: Code ↔ Comments
✅ Threshold comment matches code (0.70)
✅ Data quality comment matches code (0.80)
✅ Experiment reference is valid file
✅ Incident #456 reference is real

CHECK 2: Code ↔ Module Docs
⚠️ Agent README mentions "basic scoring" but doesn't explain thresholds
  → Update: docs/agents/lead_qualifier/README.md
✅ Design doc (newly created) matches implementation

CHECK 3: Cross-Document References
⚠️ ADR-089 doesn't exist yet (code references it)
  → Create: docs/architecture/ADR-089-lead-qualification-thresholds.md
✅ Experiment notebook exists: playground/lead_analysis_2025-12.ipynb
✅ Incident #456 documented in incidents log

CHECK 4: Related Documentation
⚠️ Testing guide doesn't cover threshold validation
  → Update: docs/development/TESTING_GUIDE.md
    Add section on validating business logic thresholds
❌ Architecture overview doesn't mention lead qualification
  → Update: docs/architecture/AGENT_ARCHITECTURE.md
    Add lead qualifier to agent catalog with threshold note

SYNCHRONIZATION CHECKLIST:
[ ] Update docs/agents/lead_qualifier/README.md (add threshold explanation)
[ ] Create docs/architecture/ADR-089-lead-qualification-thresholds.md
[ ] Update docs/development/TESTING_GUIDE.md (add threshold testing section)
[ ] Update docs/architecture/AGENT_ARCHITECTURE.md (add agent to catalog)
[ ] Verify playground/lead_analysis_2025-12.ipynb still runs
[ ] Add scoring.py tests referencing thresholds

ESTIMATED EFFORT: 2 hours"
```

**Human Action:** Review checklist, approve updates

---

### Phase 5: Validation Review (Real Example)

```markdown
"Self-review lead qualifier refactor for LP quality:

1. EXPLAINING REVEALS BUGS TEST:
Re-reading docstring, I notice:
⚠️ We log near-misses (0.65-0.70) but don't have process to review them
   → RECOMMENDATION: Add weekly review process for near-miss leads
✅ Incident #456 handling is clear and justified
✅ Trade-offs are explicit (quality vs volume)

2. KNOWLEDGE PRESERVATION TEST:
✅ New developer can understand WHY 0.70 was chosen
✅ Future changes are safe (evidence-based threshold adjustment process)
✅ Incident prevents recurrence (data quality gate explained)

3. DOCUMENTATION QUALITY:
✅ WHY captured: Threshold rationale fully explained
✅ Alternatives documented: 0.60 and 0.80 with rejection reasons
✅ Trade-offs stated: 30% lead reduction accepted for quality
✅ Evidence linked: Experiment, A/B test, sales feedback
✅ Incident preserved: #456 shaped data quality requirement

4. COMPLETENESS CHECK:
✅ Decision points explained: Both thresholds (0.70, 0.80)
✅ Edge cases rationalized: Near-miss logging, data quality issues
✅ Assumptions stated: Sales capacity, quality preferences
⚠️ Validation schedule missing: When to re-evaluate thresholds?
   → RECOMMENDATION: Add to design doc: "Review thresholds quarterly"

LP QUALITY SCORES (1-5):
- Decision rationale: 5/5 (comprehensive with evidence)
- Alternative consideration: 5/5 (clear comparison of options)
- Trade-off documentation: 5/5 (explicit gains/losses)
- Validation evidence: 5/5 (experiment + A/B test + feedback)
- Overall LP quality: 5/5

REMAINING GAPS:
1. Missing review cadence for threshold validation
2. Near-miss lead review process not defined
3. Model improvement feedback loop not documented

RECOMMENDATIONS:
1. Add to design doc: "Threshold Review Process"
2. Create ops runbook: "Weekly Near-Miss Lead Review"
3. Link to ML team: "Lead scoring model feedback pipeline"

READY FOR HUMAN REVIEW: YES
- Core LP documentation complete
- Minor process improvements identified
- No blocking issues"
```

**Human Decision:** Approve with minor follow-ups

---

## Prompt Templates Library

### Template 1: Initial Discovery

```markdown
"Analyze [MODULE_PATH] for Literate Programming gaps:

MODULE CONTEXT:
[Business purpose, critical decisions, why LP matters]

YOUR TASK:
1. INVENTORY DECISIONS:
   - [Type of decisions in this module]
   - [Key thresholds/rules]
   - [Validation logic]

2. DOCUMENTATION GAPS:
   For each decision:
   - ✅ if WHY is documented
   - ❌ if missing
   - ⚠️ if partial

3. RISK ASSESSMENT:
   - Critical undocumented decisions
   - Hardest for new developers
   - Recent changes (git history)

REPORT: Structured list with file:line, status, risk level"
```

---

### Template 2: Rationale Research

```markdown
"Research [SPECIFIC_DECISION] in [MODULE]:

SEARCH TASKS:
1. Local codebase:
   - Experiments (playground/, notebooks)
   - Tests validating this decision
   - Git history (commits introducing it)
   - Related ADRs/design docs

2. External sources (if local not found):
   - Industry best practices
   - Academic research
   - Framework documentation

DOCUMENT:
## [DECISION] Rationale

### Evidence Found
[Summarize local findings OR external research]

### Inferred Rationale (NEEDS VALIDATION)
[Best guess based on context - mark as unvalidated]

### Alternatives
[What else was/could be considered]

### Trade-offs
[Benefits vs costs]

### Validation Gaps
[Missing experiments, tests, approvals]

RECOMMENDATION:
[Experiment design if validation missing]"
```

---

### Template 3: LP Implementation

```markdown
"Implement/refactor [FEATURE] with Literate Programming:

REQUIREMENTS:
[Feature specifications]

LP DOCUMENTATION STANDARDS:
1. INLINE COMMENTS:
   - Decision points: WHY not WHAT
   - Thresholds: rationale + validation source
   - Edge cases: explain handling
   - Complex logic: explanatory prose

2. DOCSTRINGS:
   - Module: purpose, key decisions, links
   - Function: context, constraints, edge cases
   - Include: rationale, alternatives, trade-offs

3. COMPANION DOCS:
   - [MODULE]_DESIGN.md with:
     * Architecture rationale
     * Alternatives considered
     * Trade-offs analysis
     * Validation evidence

VALIDATION LINKS:
- Reference experiments, ADRs, incidents

DELIVERABLES:
1. Implementation with LP comments
2. Design document
3. Synchronization checklist"
```

---

### Template 4: Synchronization Check

```markdown
"Verify synchronization for [MODULE]:

CHECK 1: Code ↔ Comments
- Do comments match code behavior?
- Are values (thresholds, configs) consistent?
- Are references (experiments, ADRs) valid?

CHECK 2: Code ↔ Docs
- Does design doc reflect implementation?
- Are trade-offs still accurate?
- Do ADRs match current state?

CHECK 3: Cross-Document References
- Related ADRs need updates?
- Architecture docs current?
- Experiment notebooks valid?
- Testing docs cover this?

CHECK 4: Find Drift
- Comments contradicting code
- Docs describing old implementation
- Dead references
- Outdated claims

REPORT:
- Drift issues (location, type, fix)
- Update checklist (files needing revision)
- Estimated effort"
```

---

### Template 5: Validation Review

```markdown
"Self-review [MODULE] for LP quality:

1. EXPLAINING REVEALS BUGS:
   - Re-read explanations
   - Do they expose missed edge cases?
   - Do trade-offs reveal problems?

2. KNOWLEDGE PRESERVATION:
   - New developer can understand WHY?
   - Safe to modify logic?
   - Future incidents preventable?

3. DOCUMENTATION QUALITY:
   - WHY captured (not just WHAT)?
   - Alternatives documented?
   - Evidence linked?
   - Incidents preserved?

4. COMPLETENESS:
   - All decision points explained?
   - All thresholds documented?
   - All edge cases rationalized?
   - All assumptions stated?

SCORE (1-5):
- Decision rationale: [score + explanation]
- Alternative consideration: [score + explanation]
- Trade-off documentation: [score + explanation]
- Validation evidence: [score + explanation]
- Overall: [score + explanation]

GAPS: [List with recommendations]

READY FOR REVIEW: [Yes/No + reasoning]"
```

---

### Template 6: Model Card for Agent/Model

```markdown
"Create Model Card documentation for [AGENT/MODEL]:

AGENT CONTEXT:
[What this agent does, domain, purpose]

MODEL CARD SECTIONS:

1. MODEL DETAILS:
   - Name and version
   - Type (classifier, generator, router, etc.)
   - Architecture (if applicable)
   - Training/configuration date
   - Owner/maintainer

2. INTENDED USE:
   - Primary use cases (what it's for)
   - Target users
   - Out-of-scope uses (what NOT to use for)
   - Success criteria

3. PERFORMANCE:
   - Accuracy/precision/recall metrics
   - Error rates (false positives/negatives)
   - Validation methodology
   - Test dataset characteristics
   - Link to evaluation notebooks

4. LIMITATIONS:
   - Known failure modes
   - Edge cases handled poorly
   - Input constraints
   - Performance boundaries
   - When to use alternatives

5. TRADE-OFFS:
   - What was optimized (speed vs accuracy?)
   - What was sacrificed
   - Why this balance
   - Stakeholder approval

6. TRAINING/VALIDATION:
   - Data sources used
   - Validation experiments
   - A/B test results
   - Feedback integration process

7. ETHICAL CONSIDERATIONS:
   - Bias risks
   - Fairness implications
   - Privacy considerations
   - Monitoring requirements

OUTPUT FORMAT:
[AGENT]_MODEL_CARD.md with clear sections
Link from agent code to this documentation"
```

---

## Quality Checklist

Use this checklist to verify LP quality before merging:

### Decision Documentation
- [ ] Every significant decision has WHY explanation
- [ ] Alternatives considered are documented
- [ ] Trade-offs are explicit (what gained, what lost)
- [ ] Evidence/validation is linked (experiments, tests, feedback)

### Threshold Documentation
- [ ] Every threshold has rationale (why this value)
- [ ] Validation source is linked (experiment, test, analysis)
- [ ] Impact of changes is documented (what if higher/lower)
- [ ] Review schedule is defined (when to re-evaluate)

### Edge Case Documentation
- [ ] Edge cases are identified
- [ ] Handling approach is explained (why handle this way)
- [ ] Consequences of not handling are stated

### Incident Preservation
- [ ] Incident learnings are captured
- [ ] Root causes are documented
- [ ] Prevention measures are explained
- [ ] Incident references are linked

### Synchronization
- [ ] Code matches inline comments
- [ ] Module docs reflect implementation
- [ ] Related ADRs are updated
- [ ] Architecture docs are current
- [ ] Test docs cover this logic

### Completeness
- [ ] New developer can understand WHY
- [ ] Logic can be safely modified
- [ ] Knowledge survives team turnover
- [ ] Future similar work has clear pattern

### LP Principles Applied
- [ ] Human understanding prioritized (not just machine execution)
- [ ] Appropriate scope (feature/module, not single file)
- [ ] Lightweight tools used (avoiding specialized LP systems)
- [ ] Computational notebooks for experiments (if applicable)
- [ ] Maintenance burden acceptable (not over-documenting trivial code)

---

## Common Pitfalls

### Pitfall 1: Inferring Rationale Without Validation

**Problem:**
```
Agent: "This threshold was likely chosen because..."
Developer: [Assumes correct, doesn't validate]
Result: Incorrect rationale preserved as truth
```

**Solution:**
- Mark all inferred rationale as "NEEDS VALIDATION"
- Require human confirmation before documenting
- Search for actual evidence before inferring

---

### Pitfall 2: Over-Documenting Trivial Logic

**Problem:**
```python
# This function adds two numbers together by using the + operator
# which performs mathematical addition on the operands provided
def add(a, b):
    return a + b
```

**Solution:**
- Apply LP to **decision points**, not trivial operations
- Focus on **business logic**, not language syntax
- Document **complexity**, not simplicity

---

### Pitfall 3: Documentation Drift After Changes

**Problem:**
```
Day 1: Code matches comments perfectly
Day 30: Threshold changed, comments not updated
Day 60: Comments describe old logic completely
```

**Solution:**
- Make synchronization part of PR checklist
- Use agent to verify alignment before merge
- Include "update documentation" in definition of done

---

### Pitfall 4: Missing Validation Evidence

**Problem:**
```
"Threshold is 0.70" [No link to validation]
Later: "Why 0.70?" [No one remembers]
```

**Solution:**
- Require evidence links in documentation
- Create experiments before choosing values
- If evidence missing, document that explicitly

---

### Pitfall 5: LP on Wrong Scope

**Problem:**
- Applying LP to single file instead of feature/module
- Missing cross-file decision connections
- Documenting implementation but not architecture

**Solution:**
- Apply LP at **feature/module level**
- Create **module design docs** for architecture
- Document **cross-cutting decisions** (affecting multiple files)

---

### Pitfall 6: Agent Oversimplification in Long Conversations

**Problem:**
When LP conversations get too long, agents exhibit dangerous behavior: **oversimplifying incorrectly**.

**What happens:**
- Context fills with back-and-forth
- Agent loses track of constraints
- Solutions become simpler but less correct
- Requirements get silently dropped
- Edge cases ignored

**Warning signs:**
- Agent suggests solutions that are "too clean"
- Previous constraints suddenly ignored
- Implementation skips validation steps discussed earlier
- Solution doesn't match problem complexity

**Solution:**
- **Use Hand-Off for long conversations** (~20 exchanges)
- Write progress to ticket with all constraints preserved
- Start fresh conversation: "Read ticket #123 hand-off, continue"
- Request research before implementation on complex tasks
- Regular review of outputs (don't wait until end)

**Prevention:**
Provide detailed, clear instructions. Validate incrementally. Use fresh context when needed.

---

## Real-World Case Studies

### Case Study 1: Data Validation Module Refactor

**Context:**
- Module: `ada_libs/validation/`
- Problem: Multiple validation rules with unclear origins
- LP Goal: Document why each rule exists

**Process:**
1. **Discovery:** 23 validation rules, 18 undocumented
2. **Research:** Found 5 rules from incidents, 8 from requirements, 5 unknown
3. **Implementation:** Added incident references, requirement links, inferred rationale for unknowns
4. **Synchronization:** Updated testing guide, architecture docs
5. **Result:** 30% reduction in "why does this validation exist?" questions

**Key Learnings:**
- Git history revealed incident origins for many rules
- Slack search found requirement discussions
- Marking "origin unknown" better than inventing rationale

---

### Case Study 2: Agent Routing Logic Documentation

**Context:**
- Module: `agent/coordinator/routing.py`
- Problem: Complex routing decisions undocumented
- LP Goal: Explain domain classification and agent selection

**Process:**
1. **Discovery:** 12 routing decision points, 2 partially documented
2. **Research:** Found semantic classification experiment in playground
3. **Implementation:** Added rationale for confidence thresholds, fallback logic
4. **Synchronization:** Created ADR for routing architecture
5. **Result:** New developer onboarded in 3 days (previously 7 days)

**Key Learnings:**
- Explaining routing revealed edge case (ties in confidence scores)
- Documentation exposed missing test cases
- ADR helped explain "why not rule-based routing"

---

### Case Study 3: Lead Scoring Threshold Investigation

**Context:**
- Module: `agent/lead_qualifier/scoring.py`
- Problem: Production incident - too many low-quality leads
- LP Goal: Document threshold selection for future tuning

**Process:**
1. **Discovery:** Threshold set arbitrarily (no validation)
2. **Research:** Created validation experiment with historical data
3. **Implementation:** Tuned threshold based on precision/recall trade-off
4. **Synchronization:** Updated testing guide with threshold validation pattern
5. **Result:** 40% reduction in low-quality leads, process for future tuning

**Key Learnings:**
- LP forced creation of missing validation experiment
- Documented process enables threshold tuning without guesswork
- Sales feedback critical for trade-off decisions

---

### Case Study 4: Computational Notebook for Threshold Research

**Context:**
- Task: Determine optimal confidence threshold for agent routing
- Problem: No data-driven process, thresholds set arbitrarily
- LP Goal: Create reproducible research process

**Process:**
1. **Created Jupyter notebook:** `playground/routing_confidence_2026-01.ipynb`
2. **Documented hypothesis:** "Higher confidence threshold reduces routing errors but increases fallback rate"
3. **Tested thresholds:** 0.60, 0.70, 0.75, 0.80, 0.85, 0.90
4. **Recorded results:** Error rate, fallback rate, user satisfaction for each
5. **Documented decision:** Chose 0.75 based on best error/fallback balance
6. **Linked from code:** Routing logic references notebook for rationale

**Results:**
- 25% reduction in routing errors
- Reproducible process for future threshold adjustments
- New developers understand WHY threshold was chosen
- Experiment rerun with new data validates original choice

**Key Learnings:**
- Notebooks preserve **research process**, not just results
- Linking code to experiments creates traceable decisions
- Reproducible research enables confident tuning
- Future similar work follows established pattern

---

## Appendix: LP Principles Quick Reference

| Principle | Description | When to Apply |
|-----------|-------------|---------------|
| **Document WHY** | Explain reasoning, not mechanics | Every decision point |
| **Capture Alternatives** | What else was considered? | Non-trivial choices |
| **State Trade-offs** | What gained, what lost? | All design decisions |
| **Link Evidence** | Experiments, tests, feedback | Thresholds, validations |
| **Preserve Incidents** | What failures shaped this? | Bug fixes, edge cases |
| **Synchronize** | Keep code and docs aligned | Every code change |
| **Explain to Debug** | Documentation reveals bugs | Complex logic |

---

---

## Evolution to Intent-Verified Development

### Beyond LP-Inspired Documentation

This cookbook teaches **pragmatic documentation practices**. But there's an evolution beyond this:

**Intent-Verified Development (IVD)** takes LP principles further:
- Intent is primary (not code or docs)
- Understanding is executable (not just readable)
- Verification is continuous (not manual)
- AI is understanding partner (not just synchronizer)

**See:** [`../framework.md`](../framework.md) - Complete IVD specification with all principles and patterns

### When to Use Each Approach

| Approach | Use When |
|----------|----------|
| **This Cookbook (LP-inspired)** | Improving existing codebase documentation |
| | Team needs better knowledge preservation |
| | Retrofitting understanding to legacy code |
| **Intent-Verified Development** | Starting new critical modules |
| | Need continuous verification of understanding |
| | Want understanding that survives rewrites |
| | Building systems with regulatory requirements |

### Migration Path

```
Current State (traditional)
    ↓
Apply this cookbook (LP-inspired docs)
    ↓
Evolve to IVD (intent artifacts + verification)
```

Don't try to jump straight to IVD. Use this cookbook first, learn what knowledge preservation means, then evolve.

---

## IVD v1.2 Updates

**NEW in January 24, 2026:** The Intent-Verified Development framework has evolved significantly.

### Master Framework Intent

**`ivd_system_intent.yaml`** (1,130 lines) - The canonical reference for extending IVD itself.

**Contains:**
- **7 Core Principles** (immutable) with sub-principles and validation
- **Extension Rules** for adding levels, sections, recipes, documentation
- **4-Level Validation Framework** for all IVD additions
- **6-Step Canonization Process** from proposal to canonical
- **6 Immutable Constraints** that must always hold true

**When to read it:**
- Understanding IVD principles deeply
- Proposing changes to IVD framework
- Explaining how IVD works
- Understanding what makes something IVD-canonical

### Workflow-Level Intents

**NEW:** IVD now supports **4 intent levels** (was 3):

1. **System-Level**: Entire product/platform scope
2. **Workflow-Level** (NEW): Multi-step processes spanning multiple modules/functions
3. **Module-Level**: Single feature or component
4. **Task-Level**: Individual function or method

**Workflow-level intents** solve a key gap: documenting end-to-end processes with:
- Step-by-step sequence across files
- File/function mapping for each step
- Data flow between steps
- Error handling per step
- Performance targets
- Orchestration strategy
- Monitoring metrics

**Example:** `templates/examples/workflow-lead-qualification-example.yaml` (892 lines)

**Benefits:**
- **80-90% reduction** in AI agent context needed for workflow understanding
- Single source of truth for multi-step processes
- Clear dependencies between steps
- Verifiable performance targets

### Updated Structure

The IVD framework now lives in a clean, portable structure:

```
ivd/
├── ivd_system_intent.yaml    # Master intent (rules for extending IVD)
├── README.md                    # Quick start
├── framework.md                 # Complete specification
├── cookbook.md                  # Practical guide
├── cheatsheet.md                # Quick reference
├── recipes/                     # Reusable patterns
│   ├── agent-classifier.yaml
│   ├── workflow-orchestration.yaml
│   ├── infra-background-job.yaml
│   └── doc-meeting-insights.yaml
└── templates/                   # Blank templates + examples
    ├── intent.yaml
    └── examples/
        ├── workflow-lead-qualification-example.yaml
        └── task-level-intent-example.yaml
```

**Copy the entire `ivd/` folder** to any project for instant IVD adoption.

---

## Cursor Rules Integration

**How AI agents now use IVD:**

### Context, Not Bureaucracy

The master intent (`ivd_system_intent.yaml`) provides **context** for AI thinking:
- **Read for understanding** when user asks about IVD
- **Reference as canonical** when explaining IVD principles
- **Use principles to guide** approach (verifiable, evidence-based)
- **Don't force artifacts** for every small change

### When to Create Intent Artifacts

**ALWAYS create for:**
- New AI agents or major agent modifications
- New modules/systems with business logic
- Features with constraints to verify
- Multi-step workflows across files/functions
- Significant architectural decisions

**SKIP for:**
- Small bug fixes or typo corrections
- Simple refactors without logic changes
- UI-only changes without business logic
- Configuration updates
- Minor utility functions

### AI Agent Workflow

**Scenario 1: User asks about IVD**
1. ✅ Read `ivd_system_intent.yaml` for context
2. ✅ Explain principles from canonical source
3. ✅ Reference master intent as authority

**Scenario 2: User wants to extend IVD**
1. ✅ Read `ivd_system_intent.yaml` first
2. ✅ Explain 8 principles, validation levels, process
3. ✅ Guide through 6-step canonization process
4. ✅ Apply strict validation criteria

**Scenario 3: User implements small change**
1. ❌ Do NOT force intent artifact creation
2. ✅ Use IVD thinking (verifiable, evidence-based)
3. ✅ Skip artifact if minor bug fix/refactor
4. ✅ Focus on getting work done

**Scenario 4: User implements major feature**
1. ✅ Check for existing recipe first
2. ✅ Create intent artifact (significant change)
3. ✅ Use IVD principles for structure
4. ✅ Ensure constraints are verifiable

### Key Philosophy

**IVD is context, not bureaucracy:**
- Master intent guides AI thinking
- Principles inform approach
- Not every task needs full YAML
- Flexibility with principles
- Strict only for framework evolution

---

## Further Reading

### IVD Framework (v1.2)

**Master Intent (Read for Context):**
- **`../ivd_system_intent.yaml`** ⭐ CANONICAL
  - Rules for extending IVD framework
  - 8 principles with validation
  - 4-level validation framework
  - 6-step canonization process

**Core Documentation:**
- **`../README.md`** - Quick start guide
- **`../framework.md`** - Complete IVD specification
- **`../cookbook.md`** - Practical implementation guide
- **`../cheatsheet.md`** - Quick reference

**Templates & Examples:**
- **`../templates/intent.yaml`** - Blank template
- **`../templates/examples/workflow-lead-qualification-example.yaml`** - Complete workflow example (892 lines)
- **`../templates/examples/task-level-intent-example.yaml`** - Task-level example

**Recipes (Reusable Patterns):**
- **`../recipes/agent-classifier.yaml`** - AI agent classification patterns
- **`../recipes/workflow-orchestration.yaml`** - Multi-step process patterns
- **`../recipes/infra-background-job.yaml`** - Background job patterns
- **`../recipes/doc-meeting-insights.yaml`** - Document processing patterns

### Core References (Legacy Paths Removed)

**AI-Driven Development:**
- **`EINs/ein003_ai_os/training/AI_DRIVEN_DEVELOPMENT_GUIDE.md`**
  - Document Intent, Not Just Implementation (line 338+)
  - Intent Artifacts Accelerate Onboarding (line 443+)
  - Understanding > Writing in AI Era (line 2066+)
  - Review Reasoning, Not Just Implementation (line 4193+)

**Literate Programming Research:**
- **`research/lp_research.md`** - Knuth's Literate Programming theory
  - Knuth's original vision
  - Why pure LP failed to get adopted
  - Modern applications (Jupyter notebooks)
  - Connection to AI-driven development

### Related Documentation
- `docs/development/DOCUMENTATION_GUIDELINES.md` - Documentation standards
- `docs/development/ARCHITECTURE_GUIDELINES.md` - Architecture patterns
- `docs/development/TESTING_GUIDE.md` - Testing and validation

### The Evolution Path

**1984: Knuth's Literate Programming**
- Write programs as literature
- Single source, tangle/weave
- **Problem:** Tooling friction killed adoption

**2020s: Pragmatic LP (This Cookbook)**
- Apply LP principles with standard tools
- AI agents synchronize code and docs
- **Problem:** Still separate artifacts that can drift

**2026: Intent-Verified Development (Evolution)**
- **v1.0 (Jan 23)**: Initial framework with 8 principles
- **v1.1 (Jan 23)**: Added recipes + task-level intents
- **v1.2 (Jan 24)**: Added workflow-level intents + master framework intent
- Intent is primary artifact
- Continuous verification prevents drift
- Understanding is executable and durable
- **Solution:** System enforces alignment

---

**Version History:**
- 2.1 (2026-01-24): Updated for IVD v1.2
  - Added IVD v1.2 updates section
  - Added Cursor Rules integration section
  - Fixed all broken references to new ivd/ structure
  - Added master framework intent documentation
  - Added workflow-level intents explanation
  - Updated Further Reading with correct paths
- 2.0 (2026-01-23): Repositioned as LP-inspired, introduced IVD evolution
  - Added honest positioning (not pure LP)
  - Created Intent-Verified Development framework
  - Added evolution path section
  - Updated all references to reflect paradigm evolution
- 1.1 (2026-01-23): Enhanced with additional LP principles
- 1.0 (2026-01-23): Initial cookbook creation
