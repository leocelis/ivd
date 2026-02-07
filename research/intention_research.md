# Intention: Philosophical and Formal Research

**Research Date:** February 3, 2026  
**Last Updated:** February 3, 2026 (expanded)  
**Scope:** What intention is—academic philosophy, action theory, formal logic, cognitive science, psychology, law, and relevance to IVD and AI  
**Sources:** Anscombe, Aristotle, Brentano, Bratman, Davidson, Searle, Gilbert; Stanford Encyclopedia of Philosophy (Intention, Intentionality, Shared Agency, Brentano); BDI and intention logic (Rao & Georgeff, Cohen & Levesque, STIT/Belnap); Theory of Planned Behavior (Ajzen), implementation intentions (Gollwitzer); mens rea (Model Penal Code); Philosophical Glossary of AI (2025); latest advances on generating artificial intent (Emergent Mind, SWI/arXiv, Frontiers agentic AI, BDI ontology, ReCAP, LKIRF, etc.)  
**Category:** Foundational concept for IVD (intent artifacts, creativity, alignment)  
**Status:** Research synthesis for IVD framework

---

## Executive Summary

**Intention** in the philosophical and formal literature is a **motivational mental state** formed when an agent **plans and decides how to act**, embodying **commitment** to bring about a certain outcome. It is not the same as **intentionality** (the “aboutness” of mental states) or mere desire. Key properties include: **commitment** (settling on a course of action), **reconsideration-blocking** (resistance to reopening the decision), **practical reasoning** (formation from beliefs and desires), and **unity** across three guises—intention for the future, intention with which one acts, and intentional action.

For IVD, this research supports: (1) **intent artifacts** as the written, verifiable trace of *human* intention (commitment to what the system should do); (2) **creativity** as intention plus derived constraints; (3) **why world models (e.g. Project Genie) do not have intention**—they predict, they do not commit; (4) **why AGI**, if conceived as goal-directed and creative, would need to be intention-driven; (5) **why “predicting next intent”** is not equivalent to *having* intention (prediction ≠ commitment).

---

## 1. Terminology: Intention vs Intentionality

**Intentionality** (philosophy of mind) and **intention** (philosophy of action) must be distinguished.

| Term | Meaning | Source |
|------|---------|--------|
| **Intentionality** | The power of minds and mental states to be *about*, represent, or stand for things, properties, and states of affairs. A pervasive feature of many mental states (beliefs, hopes, intentions, etc.). From Latin *tendere* (directedness). | Stanford Encyclopedia of Philosophy, “Intentionality”; Brentano |
| **Intention** | A specific state of mind that plays a distinctive role in the *etiology of action*: planning, deciding, and committing to bring about an outcome. Not all mental states with intentionality are intentions. | Stanford Encyclopedia of Philosophy, “Intention”; Anscombe; Bratman |

In IVD, we use **intent** in the action-theoretic sense: the commitment to what the system (or artifact) should do or be—i.e. **intention** as understood in philosophy of action, not “intentionality” as aboutness.

### 1.1 Brentano and the Origin of Intentionality

**Franz Brentano** (*Psychology from an Empirical Standpoint*, 1874) introduced intentionality into modern philosophy and made it the **mark of the mental**: the defining feature that distinguishes mental phenomena from physical phenomena.

**Thesis:** Intentionality is “characteristic exclusively of mental phenomena. No physical phenomenon manifests anything like it.” Mental phenomena are inherently *directed toward* or *about* an object (which may not exist—e.g. thinking of a unicorn). Physical phenomena lack this directedness.

**Influence:** The idea shaped phenomenology (Husserl), analytic philosophy of mind, and the distinction between “intentionality” (aboutness) and “intention” (aiming to act). Contemporary philosophers often reject the claim that *all* mental states are intentional (e.g. Searle: undirected anxiety need not be “about” anything), but the concept of intentionality as representational directedness remains central.

**Source:** Stanford Encyclopedia of Philosophy, “Franz Brentano”; Tim Crane, “Intentionality as the Mark of the Mental,” Royal Institute of Philosophy Supplements (Cambridge).

---

## 2. Three Guises of Intention (Anscombe and the Tradition)

Elizabeth Anscombe’s *Intention* (1957) establishes that “intention” appears in three related forms; a proper account must explain their unity.

1. **Intention for the future** — e.g. “I intend to complete this entry by the end of the month.”
2. **Intention with which one acts** — e.g. “I am typing with the intention of writing an introductory sentence.”
3. **Intentional action** — e.g. “I am typing these words intentionally.”

Anscombe: it is implausible that the word is equivocal across these cases; the task of the philosophy of intention is to uncover the **unity** of these three forms.

**Anscombe’s central claim:** An action is **intentional** if the question “Why?” (in the sense that asks for reasons or purposes) has application to it. The agent can answer with reasons—“to do Y” or “because I want to do Y”—and knows their intentional action **without observation**.

**Acting under a description:** Actions are intentional only under certain descriptions. Famous example: a man moving his arm may be intentionally “pumping water” but not intentionally “contracting these muscles” or “tapping out this rhythm.” The agent supplies the relevant descriptions through their understanding of what they are doing.

### 2.1 Practical Reasoning and the Practical Syllogism

**Aristotle** (e.g. *Nicomachean Ethics*, *Movement of Animals*) discusses a form of reasoning whose “conclusion” is an **action** rather than a proposition—the **practical syllogism**. Roughly: a general principle (major premise), a particular instance (minor premise), and the conclusion *is* the agent’s doing the action. Example: “All men should take exercise” + “I am a man” → taking exercise. The conclusion is not a further belief but the action itself.

**Anscombe** revived the practical syllogism for twentieth-century action theory. In *Intention* she calls practical reasoning “one of Aristotle’s best discoveries.” She distinguishes the *idle* practical syllogism (which suggests but does not constitute action) from the practical syllogism *proper* (which issues in action). This helps clarify how intention can exist without yet resulting in action—and how, when it does, the same kind of intention is present (Davidson’s “pure intending” and intention-in-acting are unified by the role of practical reasoning).

**Relevance to IVD:** Intent artifacts can be seen as the **written conclusion** or **specification** of practical reasoning: we have reasoned about what the system should do (beliefs + goals → intention), and the artifact is the stable, checkable expression of that conclusion. Verification (tests, constraints) then plays the role of checking that the “conclusion” (the implemented system) matches the reasoned intention.

**Sources:** Aristotle, *Nicomachean Ethics*, *Movement of Animals*; Anscombe, *Intention* (1957); Stanford Encyclopedia “Intention”; Wikipedia “Practical syllogism”; “Pure Intentions: Davidson’s Debt to Anscombe.”

---

## 3. Intention as Commitment and Plan (Bratman)

Michael Bratman’s **planning theory of intention** treats intentions as elements of **partial plans of action** that play fundamental roles in practical reasoning.

**Key theses:**

- **Intention is not merely predominant desire.** When I decide to do something and so intend to do it, I am **committed** to doing it. Desires can conflict and do not settle when or how I will act; intention **settles** the question (for now).
- **Plans** organize activity over time and enable **social coordination**. Intentions support the organization of our activities and constrain the amount of further deliberation we need—making rational behavior feasible for **resource-bounded** agents.
- **Commitment** has two main roles: (1) **temporal persistence**—the intention tends to persist until the action is done or reconsidered; (2) **hierarchical planning**—subsidiary plans are made in light of committed plans.
- Intentions **block reconsideration** to some degree: having decided, the agent does not reopen the question at every moment, which helps with **temptation** and **long-term plans**.

**Relevance to IVD:** Intent artifacts can be read as the **external, verifiable trace** of such commitment: “we are committed to the system’s doing X and satisfying constraints C.” The artifact is the durable, shareable form of intention-for-the-future and intention-with-which-we-act (in the design process).

**Sources:**  
- Michael E. Bratman, *Intention, Plans, and Practical Reason* (1987/1999).  
- Michael E. Bratman, *Faces of Intention: Selected Essays on Intention and Agency* (1999).  
- Stanford Encyclopedia of Philosophy, “Intention.”

---

## 4. Pure Intending (Davidson)

Donald Davidson initially analyzed “intention with which” in terms of **primary reasons** (beliefs + pro-attitudes) and treated “intention” as a way of redescribing action. He later recognized **prospective intention** (intention for the future) and **pure intending**—cases where an agent intends to do something but has taken **no steps** yet (e.g. “I intend to write the book review” while the book is still unopened).

**Implication:** Pure intending cannot be reduced to intentional action. Once we acknowledge it, we also allow that “intention of exactly the same kind is present when the intended action eventuates.” So intention is a **state** that can exist independently of current action and that is also present when we are acting intentionally.

**Unity:** Much subsequent work treats **intention as a mental state** and explains intentional action and intention-with-which in terms of it, rather than the reverse.

**Sources:**  
- Donald Davidson, “Actions, Reasons and Causes” (1963).  
- Donald Davidson, “Intending” (1978).  
- Stanford Encyclopedia of Philosophy, “Intention.”  
- “Pure Intentions: Davidson’s Debt to Anscombe” (hist-analytic.com).

---

## 5. Intentionality as Aboutness (Searle)

John Searle’s work on **intentionality** (in the philosophy-of-mind sense) concerns the capacity of mental states to be **about** or **represent** objects and states of affairs. This is distinct from **intention** (aiming to do something) but related: intentions are one kind of intentional mental state.

**Chinese Room Argument (1980):** Computers manipulate symbols syntactically but need not have genuine understanding or **meaning** (semantics). This is used to argue that implementing a program does not by itself suffice for having intentional states in the full sense.

**Relevance:** When we ask whether an AI system “has intentions,” we are asking whether it has states that function like human intentions (commitment, guidance of action, etc.), not only whether it produces goal-like behavior. Syntax vs semantics and “simulation vs genuine” remain live in discussions of machine intention.

**Sources:**  
- John R. Searle, *Intentionality: An Essay in the Philosophy of Mind* (1983).  
- Stanford Encyclopedia of Philosophy, “Chinese Room Argument,” “Intentionality.”

---

## 6. Formal and Mathematical Treatments: BDI

The **Belief–Desire–Intention (BDI)** model formalizes intention for rational agents, drawing explicitly on Bratman’s philosophy.

**Rao & Georgeff (1991):** BDI architecture gives intentions **equal status** with beliefs and desires. Intentions are formalized in a **branching-time possible-worlds** framework (e.g. BDICTL: BDI + CTL*). Key formal properties:

- **Commitment:** Intentions are distinguished from desires by commitment—producing temporal persistence and hierarchical planning.
- **Multi-modal logic:** Modalities for belief, desire, and intention; temporal logic for “will eventually,” “until,” etc.

**Cohen & Levesque (1990):** One of the most influential formalizations of intention in AI. Following Bratman, they identify **seven properties** a reasonable theory of intention must satisfy: intentions pose problems agents must solve; they serve as filters for adopting compatible intentions; agents believe their intentions are possible; etc. They define **intention as choice with commitment**: agents maintain commitment to goals under appropriate circumstances rather than abandoning them arbitrarily. The framework uses a two-tiered approach: first a logic of rational agency with sorted modal operators, then derived constructs forming a partial theory of rational action. It has become a standard reference for BDI logics and has been extended by Rao & Georgeff and others.

**STIT logic (“Seeing To It That”):** Developed by Nuel Belnap and colleagues (late 1980s onward). STIT provides a **modal logic of agency**: an agent “sees to it that” a proposition holds—i.e. brings it about. The logic uses branching-time models plus agent choice: an agent can ensure a formula is true regardless of other agents’ choices. Variants include the Chellas stit operator and the deliberative stit operator. STIT grounds agency on **control** and **attempt**; it has been used to formalize obligation, influence, commitment, and responsibility. It relates to Coalition Logic and multiagent systems. So intention and “bringing it about” are formalized in a way that separates what the agent controls from what merely happens.

**Relevance to IVD:** BDI and STIT show that intention can be **represented** and **reasoned about** in a formal system. IVD’s intent artifacts are a different kind of formalization—not modal logic over agent states, but **declarative constraints and success criteria** that express what the designer intends the system to do. Both share the idea that intention has structure that can be made explicit and checked. The “choice with commitment” (Cohen & Levesque) and “seeing to it that” (STIT) align with IVD’s emphasis on commitment and verifiable outcomes.

**Sources:**  
- Anand S. Rao & Michael P. Georgeff, “Modeling Rational Agents within a BDI-Architecture” (1991).  
- Philip R. Cohen & Hector J. Levesque, “Intention is Choice with Commitment,” *Artificial Intelligence* 42 (1990).  
- Nuel Belnap et al., STIT logic (multiple papers); “Stit and the language of agency,” *Synthese*; “A Computationally Grounded Logic of ‘Seeing-to-it-that’” (IJCAI 2022).  
- Wikipedia, “Belief–desire–intention software model.”  
- Decision Procedures for BDI Logics (Rao, 1998).  
- BDI Logics (Utrecht thesis, dspace.library.uu.nl).

---

## 7. Cognitive Science and Psychology of Intention

**Theory of Planned Behavior (Ajzen):** In social psychology, **behavioral intention** is the immediate antecedent of behavior. Intentions are determined by attitude toward the behavior, subjective norms, and perceived behavioral control. Intention is thus the **motivational factor** that captures how much effort people are willing to exert to perform the behavior. This aligns with the philosophical picture: intention as the settled motivational state that precedes and guides action.

**Implementation intentions (Gollwitzer):** **Goal intentions** (“I intend to achieve X”) are often insufficient for action. **Implementation intentions** are if–then plans: “If situation X occurs, then I will perform response Y.” They specify *when*, *where*, and *how* to act. Meta-analyses show a medium-to-large effect (d ≈ 0.61–0.65) on goal attainment; difficult goals are completed roughly three times more often when paired with implementation intentions. They work by **delegating action control to situational cues** (heightened accessibility of the cue, automated link between situation and response). So intention in psychology has a **hierarchical** structure: higher-level goal intention + lower-level implementation intention (when/where/how).

**Intention–behavior gap:** There is a well-documented gap between intending and doing. Implementation intentions help close it by making the transition from intention to action less dependent on momentary willpower. For IVD, this suggests that **writing down** intent (the artifact) and **attaching verification** (tests, constraints) functions like an implementation intention: “If we change this module, then we run these checks.” The artifact makes the commitment concrete and situation-specific.

**Action planning and effects:** Cognitive science treats action planning as operating through **anticipated effects** of intended goals. Agents learn movement–effect contingencies and run internal simulations to select actions likely to produce desired effects. Planning is largely off-line (preceding execution), though it can overlap with execution for simple actions. This supports the idea that intention involves a **representation of a goal state** and a **commitment** to bringing it about—consistent with Bratman and with BDI’s “intention as choice with commitment.”

**Sources:**  
- Icek Ajzen, “From Intentions to Actions: A Theory of Planned Behavior,” in *Action-Control* (Springer).  
- Peter M. Gollwitzer, “Implementation Intentions and Effective Goal Pursuit,” *Journal of Personality and Social Psychology*; “Implementation Intentions and Goal Achievement: A Meta-analysis” (Advances in Experimental Social Psychology).  
- Frontiers in Human Neuroscience, “Promoting the translation of intentions into action by implementation intentions” (2015).  
- Cognitive Science Society proceedings on action planning and effect anticipation.

---

## 8. Shared and Collective Intention

**Phenomenon:** Sometimes individuals act **together**—joint action, shared activity, collective intention. What distinguishes “we did it together” from a mere aggregation of individual acts? The answer is standardly given in terms of **intention**: shared or collective intention.

**Bratman’s account:** Shared intention is not a single group mind but **interlocking personal intentions**. Each participant has intentions that are **interdependent** with the others’ intentions (e.g. I intend that we J in part because I expect you to intend that we J, and similarly for you). So shared agency is **reducible** to a structure of individual intentions that mesh. Plans are shared when they are compatible and subplans are coordinated; no primitive “we-intention” is required.

**Searle’s we-intention:** In the collective case, each participant’s intention “I am running to the shelter” **derives from** an intention that adverts to the others—e.g. “We are running to the shelter.” This “we-intention” is what distinguishes collective action from a mere sum of individual actions. (Not all theorists accept irreducible we-intentions.)

**Gilbert’s joint commitment:** Margaret Gilbert argues that shared intention involves being **jointly committed to intend as a body** to do something—a normative, mutually obligating structure that is more demanding than Bratman’s interlocking personal intentions.

**Relevance to IVD:** **Team intent** (e.g. a team committing to what a system should do) can be understood via shared intention: the intent artifact is the **public, stable expression** of what “we” intend. It allows multiple people to have interlocking intentions (each intends that the system satisfy the artifact, in part because others do too). The artifact is the shared plan. So the philosophy of shared agency supports IVD’s use of a **single, verifiable intent artifact** as the focus of collective commitment.

**Sources:**  
- Stanford Encyclopedia of Philosophy, “Shared Agency” (2010/2017).  
- Michael Bratman, “Shared Intention,” *Ethics*; *Shared Agency: A Planning Theory of Acting Together* (2014).  
- John Searle, “Collective Intentions and Actions” (1990).  
- Margaret Gilbert, joint commitment accounts (multiple works).

---

## 9. Intention in Law: Mens Rea

**Mens rea** (“guilty mind”) is the mental element required for criminal liability in most legal systems. It is one of two fundamental elements of crime, alongside *actus reus* (the wrongful act). The law distinguishes levels of culpability based on the defendant’s **mental state** with respect to the conduct or result.

**Model Penal Code (MPC) hierarchy (widely adopted in the U.S.):**

1. **Purposely** — The defendant’s **goal** was to cause the criminal conduct or result.  
2. **Knowingly** — The defendant was practically certain the conduct would cause the result.  
3. **Recklessly** — Conscious disregard of a substantial and unjustified risk.  
4. **Negligently** — Unaware of the risk but should have been aware.

Purpose corresponds most closely to **intention** in the philosophical sense: the agent’s aim or goal. Knowing, reckless, and negligent states are weaker or different. Higher mental states can substitute for lower ones in prosecution; blameworthiness and sentencing track the hierarchy.

**Relevance:** The law treats **intention** (purpose) as a distinct and especially culpable mental state. This reinforces that intention is not just “what happened” but **what the agent meant to bring about**—commitment to an outcome. For AI and responsibility, the question of whether a system “intended” an outcome (in a sense that could ground mens rea) remains contested and connects to the Philosophical Glossary of AI’s discussion of moral responsibility.

**Sources:**  
- Stanford Encyclopedia (and legal encyclopedias) on philosophy of criminal law.  
- Cornell Law School, Wex: “mens rea,” “intent,” “criminal intent.”  
- Model Penal Code (§2.02); Wikipedia “Mens rea.”

---

## 10. Key Properties of Intention (Synthesis)

From the foregoing (philosophy, formal logic, psychology, law), intention can be summarized as having at least the following properties:

| Property | Description | Implication for IVD / AI |
|----------|-------------|---------------------------|
| **Commitment** | Intention settles on a course of action; it is not merely a strong desire. Carrying out the action can figure in further planning. | Intent artifacts express commitment: “we are committed to these constraints and goals.” |
| **Reconsideration-blocking** | Intention raises the bar for reopening the question of what to do; it supports perseverance. | Design decisions in intent are stable until explicitly revised. |
| **Formation by reasoning** | Intentions are paradigmatically formed by practical reasoning (beliefs + desires → intention). | Intent can be written after deliberation and then used to guide implementation. |
| **Object of intention** | Intention is directed at *doing* something (or bringing about a state of affairs by doing). | Intent artifacts are directed at what the *system* should do or be. |
| **Unity** | Intention for the future, intention with which one acts, and intentional action are unified (either one explains the others or they are modes of the same phenomenon). | Same “intent” can govern both future work (plans) and current design decisions (intention with which we act). |

---

## 11. Intention and AI (2025–2026)

The **Philosophical Glossary of AI** (AIGlossary.co.uk, 2025) defines intention for AI contexts and raises whether AI systems have or could have intentions.

**Definition (Glossary):** “An intention is a motivational mental state, formed when an agent plans and decides how to act, which captures the way they commit to bring about a certain outcome.”

**Questions raised:**

- When an AI system produces outputs with effects in the world, were those effects **intended**? Do AI systems act on the basis of intentions at all?
- **Commitment vs motivation:** Intentions embody commitment, not just motivation. It is unclear whether AI systems form genuine commitments or only simulate goal-directed behavior.
- **Reconsideration-blocking:** Humans use intentions to resist reopening decisions. AI systems may not have the same kind of motivational conflict or need for this function.
- **Moral responsibility:** Whether AI outputs reflect “genuine” intentions affects ascriptions of responsibility.
- **Terminological care:** “Intentionality” in philosophy often means aboutness/representation; in some AI writing it is tied to intention or to agency more broadly.

**Relevance:** For IVD and for the “Project Genie / creativity / AGI” thread: systems that only **predict** (e.g. next frame) do not **commit**; they have no state that plays the commitment role. So they do not have intention in this sense. An AGI that sets goals, plans, and commits would be intention-driven; a world model alone is not.

**Source:** “Intention,” The Philosophical Glossary of AI (2025). https://aiglossary.co.uk/2025/06/24/intention/

---

## 12. Latest Advances on Generating Artificial Intent

This section surveys **recent research (2023–2026) on how to generate, represent, or operationalize intent in artificial systems**—i.e. advances in "artificial intent" as a technical capability, without assuming that such systems thereby "have" intention in the full philosophical sense (§11). The focus is on trusted academic and industry sources: conference and journal papers, arxiv preprints, and structured surveys.

### 12.1 Intent-driven reasoning (synthesis)

**Intent-driven reasoning** is a computational framework in which an agent **explicitly infers, represents, or acts upon high-level intent** (goals, purposes, motivations) to guide reasoning, planning, or action selection. Unlike purely reactive systems, intent-driven models anchor reasoning to inferred or specified intentions, enabling robustness, interpretability, and adaptivity (Emergent Mind, "Intent-Driven Reasoning," updated Jan 2026).

**Core properties:**

- **Bidirectionality:** Intent may be **inferred** from context (intent recognition) or used **generatively** to plan or explain actions (intent realization).
- **Intent-guided inference:** Reasoning—planning, prediction, classification—is **conditioned on** explicit intent rather than only on raw data.
- **Explicit intent representation:** Intents are structured variables or embeddings (tuples, tokens, vectors, logical specifications) that drive downstream computation.

**Formalisms in use:** Optimization (intent as constraint or objective), semantic ontologies and mappings (user expression → structured intent), graph-theoretic structures (intent graphs, scene graphs), logical specifications (e.g. past-time LTL for goals), token or embedding-based representations in neural architectures. Applications span recommendation, autonomous driving, dialogue, content safety, adaptive systems, and NLP (Emergent Mind; multiple cited papers 2022–2025).

**Source:** Emergent Mind, "Intent-Driven Reasoning in AI Systems" (2026). https://www.emergentmind.com/topics/intent-driven-reasoning

### 12.2 Speaking with Intent (SWI) in LLMs

**Speaking with Intent (SWI)** (Yin et al., arXiv:2503.21544, 2025) has the LLM **explicitly generate an intent statement** before producing the final answer. The intent "encapsulates the model's underlying intention and provides high-level planning to guide subsequent analysis and action," emulating deliberate, purposeful human thinking.

**Mechanism:** Intent functions as a "meta-thought and planning" step: the model articulates what it intends to do or convey, then generates the answer conditioned on that intent. This leverages the autoregressive and attention structure of LLMs to give **structured direction** to later tokens.

**Results:** Improvements on text summarization (accuracy, conciseness, factual correctness, fewer hallucinations), multi-task question answering, and mathematical reasoning (comparable to Chain-of-Thought and Plan-and-Solve). Human evaluation indicates that SWI-generated intents are coherent, effective, and interpretable.

**Significance:** SWI is a **generative** approach to artificial intent: the model *produces* an explicit intent representation (text) that then guides its own downstream generation. It does not claim that the LLM "has" intention in the philosophical sense; it shows that **generating intent-like structure** can improve reasoning and generation quality. Code: https://github.com/YuweiYin/SWI

**Source:** Yuwei Yin, EunJeong Hwang, Giuseppe Carenini, "SWI: Speaking with Intent in Large Language Models," arXiv:2503.21544 (2025).

### 12.3 Intention recognition and goal generation (LLMs and knowledge)

**Intention recognition** is the inverse of generation: inferring intent from behavior or context. Recent work combines LLMs with **knowledge graphs** (e.g. LKIRF for service robots) to build offline and online reasoning graphs, improving prediction accuracy and interpretability (Nature Scientific Reports, 2024). **Goal generation** for agents is addressed by recursive planning frameworks (e.g. ReCAP: recursive context-aware reasoning and planning for long-horizon tasks) and by training pipelines that synthesize diverse tasks and difficulty curves (e.g. AgentGen) to improve LLM planning. **Goal-conditioned** value functions and RL are used to guide multi-turn reasoning for negotiation, persuasion, and tool use while remaining scalable to API-based models.

**Bridging LLMs and human intentions:** Survey work (e.g. "Bridging the Gap Between LLMs and Human Intentions," arXiv:2502.09101) frames progress and challenges in **instruction understanding**, **intention reasoning**, and **reliable generation**—treating "intention" as a target for both recognition and alignment in LLM systems.

**Sources:** Nature Scientific Reports (2024), LKIRF; ReCAP (arXiv:2510.23822); AgentGen; "Bridging the Gap Between LLMs and Human Intentions" (arXiv:2502.09101).

### 12.4 BDI and formal models of machine intention

**BDI (Belief–Desire–Intention)** remains a reference architecture for rational agency. Recent work continues to use BDI as an **ontology for modelling mental reality and agency** (e.g. arXiv:2511.17162), capturing beliefs, desires, intentions, and their dynamics as a bridge between declarative and procedural intelligence. **Modern agentic systems** combine classical BDI-style notions (goals, plans, intentions) with **foundation models** (e.g. neural networks) for flexibility—suggesting that "artificial intent" can be implemented as a **structured layer** (goals, plans, commitment) on top of learned policies or generators.

**Formal definition of intention in ML:** Some work **operationalizes intention using structural causal models (SCMs)**, grounding it in philosophy and applying it to RL agents and language models: intention is formalized so that it can be **inferred** from agent behavior and related to actual causality and instrumental goals. This provides a **testable, formal** notion of "machine intention" for analysis and verification (referenced in Emergent Mind and ML/arXiv literature).

**Sources:** BDI ontology (arXiv:2511.17162); Emergent Mind "Intent-Driven Reasoning"; structural causal models and intention (ML/arxiv).

### 12.5 Synthetic teleology and agentic AI

**Synthetic teleology** (or **synthetic purposiveness**) refers to the **engineered capacity** of artificial systems to **generate and regulate their own goals** through ongoing self-evaluation (Frontiers in Artificial Intelligence, 2025). Agentic AI is characterized as a shift from fixed task execution to systems that maintain **recursive loops** of perception, evaluation, goal-updating, and action—enabling purposive activity across temporal and organizational scales.

**Contrast:** Traditional AI optimizes externally specified objectives; agentic systems can **represent, evaluate, and revise** their own goals. Reliability is sought through **architectural decomposition** (e.g. goal managers, planners, memory, safety monitors). Researchers are developing **measurable indicators** of agentic purposiveness (e.g. teleological coherence, adaptive recovery, reflective efficiency) and operationalizing goal-directedness (e.g. near-optimal behavior for multiple sparse reward functions).

**Relation to "generating artificial intent":** Here intent/goal is not only **represented** but **generated and updated** by the system itself. That is the "synthetic" part: the system produces and maintains its own goal structure. Whether this amounts to **having** intention in the philosophical sense (commitment, reconsideration-blocking) is still debated (§11); technically, it is an advance in **autonomous goal generation and regulation**.

**Sources:** "From the logic of coordination to goal-directed reasoning: the agentic turn in artificial intelligence," Frontiers in Artificial Intelligence (2025); "Agentic AI Needs a Systems Theory" (arXiv:2503.00237); teleology and self-organization (Springer, PhilPapers).

### 12.6 Summary: generating artificial intent today

| Approach | What is "generated" | Role of intent | Typical use |
|----------|---------------------|----------------|-------------|
| **SWI (LLM)** | Explicit intent *text* before answer | Meta-thought; conditions next tokens | Summarization, QA, math; interpretability |
| **Intent-driven reasoning** | Intent as structured variable (embedding, graph, logic) | Conditions inference/planning/action | Recommendation, driving, dialogue, safety, adaptive systems |
| **BDI + foundation models** | Goals/plans/intentions as ontology layer | Commitment-like persistence; hierarchy | Agent architectures; hybrid symbolic–neural |
| **Synthetic teleology** | Goals generated and updated by system | Self-evaluation; recursive goal regulation | Agentic AI; long-horizon purposive behavior |
| **Intention recognition** | Intent *inferred* from context/behavior | Inverted: observation → intent | Robotics, dialogue, safety (e.g. user intent) |

**Limitations (from the literature):** Formal verification and ontological consistency of inferred/specified intents; need for human-in-the-loop and interactive intent updating; generalization of intent representations across domains; handling ambiguous or underspecified natural input; scalability of intent mapping in large, dynamic systems (Emergent Mind, "Intent-Driven Reasoning," §6).

**Relevance to IVD:** These advances show that **artificial intent** can be **generated** (SWI), **represented** (graphs, logic, embeddings), **inferred** (recognition), and **self-updated** (synthetic teleology)—without resolving whether the system thereby has intention in the philosophical sense. IVD's "AI writes the intent" fits into this landscape: the AI **produces** a structured intent artifact (e.g. YAML) that then **conditions** implementation and verification. That is a form of **generated artificial intent** in the sense of this section; the **commitment** to that intent remains with the human who reviews and approves it (§13.1–13.5 below).

---

## 13. Implications for IVD

### 13.1 Intent artifacts as traces of intention

- Intent artifacts are **written, verifiable expressions** of what the designer (or team) **intends** the system to do—commitment to goals, constraints, and success criteria.
- They correspond to **intention for the future** (what we intend the system to be) and support **intention with which we act** (we implement and verify in light of this intent).
- They are **not** the same as “intentionality” (aboutness); they are the action-theoretic notion of intention, made explicit and checkable.

### 13.2 Creativity as intention + derived constraints

- Under the lens adopted in our prior analysis: **creativity** = intention (what the creator wants to achieve) + **derived constraints** (rules, form, structure that realize that intention).
- **Rules are derived from intention;** they are the form intention takes in the artifact. So intent artifacts that state constraints are the right level of abstraction: they encode the commitments (intentions) from which implementation and verification are derived.

### 13.3 Why world models (e.g. Project Genie) lack intention

- World models predict next frames (or states) given context and actions. They do not **commit** to an outcome; they do not have a state that **blocks reconsideration** or that was **formed by practical reasoning** in the agent.
- So they **cannot have intention** in the philosophical sense. They can be **used** by an intention-driven agent (e.g. AGI) that commits to goals and uses the model as a tool.

### 13.4 Why “predicting next intent” ≠ having intention

- A model that predicts “next intention” from context would output a **representation of a likely intention**, not an agent’s **commitment**. Prediction does not entail commitment or ownership.
- Having intention requires a **subject** that means something and stands behind it. A predictor has no such stance; it only produces plausible continuations.

### 13.5 AGI and intention

- If AGI is conceived as **goal-directed**, **planning**, and **creative**, then it must be **intention-driven**: it must have states that play the role of commitment, plan, and guidance of action. Otherwise it remains a reactive or predictive system, not an author or designer in the sense we care about for games and art.

---

## 14. References and Further Reading

### Philosophy (primary and secondary)

- Anscombe, G.E.M. *Intention* (1957). Ithaca: Cornell University Press.
- Aristotle. *Nicomachean Ethics*; *Movement of Animals* (practical syllogism).
- Brentano, Franz. *Psychology from an Empirical Standpoint* (1874). Intentionality as mark of the mental.
- Bratman, Michael E. *Intention, Plans, and Practical Reason* (1987). Cambridge, MA: Harvard University Press; reprint Stanford: CSLI, 1999.
- Bratman, Michael E. *Faces of Intention: Selected Essays on Intention and Agency* (1999). Cambridge University Press.
- Bratman, Michael E. *Shared Agency: A Planning Theory of Acting Together* (2014). Oxford University Press.
- Davidson, Donald. “Actions, Reasons and Causes” (1963). In *Essays on Actions and Events*. Oxford: Clarendon.
- Davidson, Donald. “Intending” (1978). In *Essays on Actions and Events*. Oxford: Clarendon.
- Gilbert, Margaret. Joint commitment and collective intention (multiple works).
- Searle, John R. *Intentionality: An Essay in the Philosophy of Mind* (1983). Cambridge University Press.
- Searle, John. “Collective Intentions and Actions” (1990).
- Stanford Encyclopedia of Philosophy. “Intention” (2009; rev. 2022). https://plato.stanford.edu/entries/intention/
- Stanford Encyclopedia of Philosophy. “Intentionality” (2003; rev. 2023). https://plato.stanford.edu/entries/intentionality/
- Stanford Encyclopedia of Philosophy. “Shared Agency” (2010; rev. 2017). https://plato.stanford.edu/entries/shared-agency/
- Stanford Encyclopedia of Philosophy. “Franz Brentano.” https://plato.stanford.edu/entries/brentano/
- Stanford Encyclopedia of Philosophy. “Chinese Room Argument.” https://plato.stanford.edu/entries/chinese-room/
- Crane, Tim. “Intentionality as the Mark of the Mental,” Royal Institute of Philosophy Supplements (Cambridge).

### Formal and computational

- Rao, Anand S., & Georgeff, Michael P. “Modeling Rational Agents within a BDI-Architecture.” KR 1991.
- Rao, Anand S. “Decision Procedures for BDI Logics.” 1998.
- Cohen, Philip R., & Levesque, Hector J. “Intention is Choice with Commitment.” *Artificial Intelligence* 42 (1990). 213–261.
- Belnap, Nuel, et al. STIT logic (“Seeing to it that”). Multiple papers; *Synthese*; “Stit and the language of agency.”
- “A Computationally Grounded Logic of ‘Seeing-to-it-that’.” IJCAI 2022.
- Wooldridge, Michael. LORA (Logic of Rational Agents). Multiple papers.
- Belief–desire–intention software model. Wikipedia (with references to Rao & Georgeff, Cohen & Levesque).

### Cognitive science and psychology

- Ajzen, Icek. “From Intentions to Actions: A Theory of Planned Behavior.” In Kuhl & Beckmann (eds.), *Action-Control: From Cognition to Behavior*. Springer.
- Gollwitzer, Peter M. “Implementation Intentions and Effective Goal Pursuit.” *Journal of Personality and Social Psychology*.
- Gollwitzer, P. M., & Sheeran, P. “Implementation Intentions and Goal Achievement: A Meta-analysis of Effects and Processes.” *Advances in Experimental Social Psychology* (2006).
- Frontiers in Human Neuroscience. “Promoting the translation of intentions into action by implementation intentions: behavioral effects and physiological correlates” (2015).

### Law

- Model Penal Code (§2.02). Mens rea hierarchy (purposely, knowingly, recklessly, negligently).
- Cornell Law School, LII/Wex. “Mens rea,” “intent,” “criminal intent.”
- Wikipedia. “Mens rea.”

### AI and intention (recent)

- "Intention." The Philosophical Glossary of AI (2025). https://aiglossary.co.uk/2025/06/24/intention/

### Latest advances on generating artificial intent (2023–2026)

- Emergent Mind. "Intent-Driven Reasoning in AI Systems" (updated Jan 2026). https://www.emergentmind.com/topics/intent-driven-reasoning
- Yin, Yuwei, EunJeong Hwang, Giuseppe Carenini. "SWI: Speaking with Intent in Large Language Models." arXiv:2503.21544 (2025). https://arxiv.org/abs/2503.21544 Code: https://github.com/YuweiYin/SWI
- "Bridging the Gap Between LLMs and Human Intentions: Progresses and Challenges in Instruction Understanding, Intention Reasoning, and Reliable Generation." arXiv:2502.09101 (2025).
- Nature Scientific Reports. "Enhancing intention prediction and interpretability in service robots with LLM and KG" (2024). LKIRF framework.
- ReCAP: "Recursive Context-Aware Reasoning and Planning for Large Language Model Agents." arXiv:2510.23822.
- BDI ontology: "The Belief-Desire-Intention Ontology for modelling mental reality and agency." arXiv:2511.17162.
- "From the logic of coordination to goal-directed reasoning: the agentic turn in artificial intelligence." Frontiers in Artificial Intelligence (2025). Synthetic teleology; agentic AI.
- "Agentic AI Needs a Systems Theory." arXiv:2503.00237.
- IntentionReasoner, IntentDial, IGR-SR, MINDREAD, DRAMA-X, IDSS (cited in Emergent Mind intent-driven reasoning survey).

---

## Document Info

**Governed by:** IVD framework (e.g. `ivd_system_intent.yaml`)  
**Placement:** `ivd/research/intention_research.md`  
**Use:** Foundational concept for intent artifacts, creativity, and limits of prediction-only AI (e.g. world models). Supports IVD positioning of “intent as primary” and “AI writes intent” under human authorship and commitment.
