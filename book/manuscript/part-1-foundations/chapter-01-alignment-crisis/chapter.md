# Chapter 1: The Alignment Crisis

You ask for X. You get something that looks like X. It isn't. You clarify. You get something else. Again, not quite. The cycle repeats—turn after turn, correction after correction—until the deadline forces a compromise or the project fails.

That pattern is as old as software. But we are no longer in the age of human developers. We are in the **AI Agents era**. The AI builds. The AI writes. The AI fills in the gaps. And when it fills in the gaps wrong, you correct, and it tries again.

This chapter is about that pattern, why it is so expensive, and why the way we work with AI today makes it almost inevitable. By the end, we will have named the problem—and asked the question that changes everything.

---

## 1.1 The Expensive Pattern: "Build X" → "Here's X" → "No, I meant..."

The pattern is simple. You prompt an **AI agent**: *Build X.* The AI returns: *Here's X.* You look at it and say: *No, I meant…* So it goes: prompt, deliver, correct. Prompt, deliver, correct.

Each round—each **turn**—costs time, attention, and **trust**. The AI can produce a full module or a full doc in seconds. The loop can spin dozens of times in a single session.

The cost of each turn is low in wall-clock time; the *total* cost—wrong assumptions, baked into more and more outputs, context overload, and the growing doubt that the AI Agent really understands what "X" really means—compounds fast!

This is the **many turns problem**.

Consider this example. You tell your AI agent: "Add export to CSV." The AI ships a CSV export. You try it: "I meant only these columns, and with this date format, and only for admins." The AI hadn't been told any of that (?)

**Your prompt was incomplete**; the code was a plausible interpretation.

The gap between "add export to CSV" and what you actually needed was never written down in a form the AI could verify against.

So the first delivery was, in a real sense, a **hallucination**—the AI filled in the blanks with something plausible but wrong.

The loop continues. Turn after turn.

The old pattern existed between humans too: PM writes a ticket, developer ships the wrong thing, correction ensues. But that was slow enough that we learned to "live with" it. Now, with AI agents that can write entire features in seconds, the same pattern runs at *machine speed*.

The expense is not only in the extra turns. It is in the hidden work: the mental load of keeping "*what I really meant*" in your head, the fatigue of correcting again and again, and the erosion of trust when "Here's X" keeps missing. 

**We have been building at the speed of misunderstanding.**

That sentence will come back. For now, hold it: the core problem is that we treat the *prompt* as informal and let the AI guess.

The AI fills the gaps. When the guess is wrong, we correct. We almost never write down the request in a way that can be **checked**—and that the AI can verify against before it builds.

---

## 1.2 Why Traditional Artifacts Fail: PRDs, User Stories, and Prompts

In theory, writing things down fixes the gap. In practice, it doesn't—because none of the traditional artifacts are **verifiable by the AI**.

By **verifiable**, we mean this: the AI can run a deterministic check—execute tests, validate structured constraints—that returns pass or fail, without having to interpret prose.

The artifact provides a contract to verify against. A PRD is not that. It is prose. The AI reads it, interprets it, and guesses what matches. That is not verification; that is inference. And **inference** is where **hallucination lives**.

Consider what we have tried before:
- **PRDs (Product Requirements Documents):** Prose documents written by humans for humans. The AI cannot verify whether its code matches a PRD. It can only read the PRD and guess.
- **User stories:** "As a user, I want to export to CSV so that I can analyze data offline." Still prose. Still unverifiable. The AI reads it and fills in the blanks.
- **Prompts:** The state of the art for AI agents. "Add export to CSV for admins, with these columns, in ISO date format." Better—but still informal. Still no structure the AI can check against. Still leads to many turns when the prompt was incomplete.

The problem is the same in each case: *none of these artifacts can be verified by the AI*. The AI reads them, interprets them, and produces code that is a plausible guess. When the guess is wrong, you correct. The loop continues.

**Why do these artifacts fail with AI?** Because they were designed for **humans** to read and interpret. They assume a human developer will ask clarifying questions, will remember context from last week's meeting, will know the unwritten rules of the codebase.

An AI agent has none of that. It has only what you give it. If what you give it is prose—PRD, user story, or prompt—it will infer. Inference is guesswork. **Guesswork is hallucination.** The AI fills in the gaps with something plausible but wrong.

You have seen this. The `API` that doesn't match the spec. The feature that ignores edge cases mentioned in the ticket. The AI output that looks right until you run the tests.

We learn to work around it: we add more context, we correct, we iterate. It's wasteful, but it's normal. It is the default mode of working with AI agents today. **The gap between "what I wanted" and "what the AI built" is where misalignment lives.**

---

## 1.3 The AI Amplification Effect: Many Turns, Many Hallucinations

**AI agents** can produce fast, plausible, and wrong output. They don't need to be "bad" at coding. They just need to fill in the gaps in your request with something reasonable—reasonable given the training data and the few lines of context in the prompt.

If your intent was "export these five columns in ISO dates for admins only," and you said "add CSV export," the model has no way to know. It will give you *a* CSV export. You get back 500 lines. You scroll, you see wrong columns, wrong permissions, wrong format.

You correct. It rewrites. Again. Again. Each iteration takes seconds. The *throughput* of misunderstanding goes up. So does the volume of wrong-but-plausible code that you must read, judge, and correct.

This is the core pain point of the **AI Agents era**: **many turns and hallucinations**.

- **Many turns:** The back-and-forth correction cycle. Each turn costs context, attention, and time. The AI rewrites; you re-review; errors propagate.
- **Hallucinations:** The AI "fills the gaps" with plausible but incorrect assumptions. It doesn't know what you meant, so it guesses. The guess becomes code. The code is wrong.

The cost of each turn is small. The compounding cost—wrong structure propagated, your mental model of "what we're building" constantly revised—is large. If you are working with AI agents today, you have felt this. It is exhausting.

It's the same pattern as 1.1: no shared, **verifiable statement of intent** that the AI can check against. The AI can't read your mind. It can only use what you give it. If what you give it is a short prompt and some existing code, it will infer. Inference is guesswork. Guesswork is hallucination. The more we rely on AI agents to build, the more we run that guesswork at scale.

**Alignment, not hope.** The alternative to hoping the AI guessed right is to have something that can be checked: a statement of intent that the AI can verify against before and after it builds. We are not there yet. Today, we build at the speed of misunderstanding, and AI makes that speed very high.

The cost of this pattern is not small. Industry research consistently shows that the majority of **critical project knowledge**—what the system should do, why design decisions were made—never makes it into a durable, machine-checkable form. Studies of software architecture and documentation find that 70–90% of mismatches between documentation and actual systems stem from documentation that failed to keep up with reality.[^1] This knowledge lives in meetings, in tickets that scatter, in the heads of people who leave.

The financial cost is measured in the tens of billions and beyond: the United States alone writes off over $260 billion annually on software development failures, with roughly $500 billion lost globally to projects that fail, overrun, or deliver the wrong thing.[^2] The AI prompt that fills in the wrong blanks, the feature that ignores unstated constraints, the turn after turn of correction—these aren't edge cases. They are the default. And the cost compounds.

[^1]: IEEE research on architectural knowledge loss in industrial projects (Rigby et al., ICSE; McGill studies on turnover-induced knowledge loss). See Appendix F for full references.

[^2]: Software industry failure costs: Standish Group 2024 (70%+ project failure/challenge rate); U.S. development failure costs and global waste (IEEE Spectrum, industry analyses). See Appendix F.

---

## 1.4 The Core Question: What If Intent Was Verifiable?

We have been building at the speed of misunderstanding. We have prompted AI agents and watched them fill the gaps with plausible hallucinations. We have corrected, turn after turn, exhausting ourselves and the context window. We have used PRDs, user stories, and prompts—and none of them are verifiable by the AI. The AI reads, guesses, and builds. When it builds wrong, we correct. The loop continues.

So: **what if intent was verifiable?**

What if, instead of handing the AI prose to interpret, we had something the AI could *check against*—before it builds, and after? Not a prompt to guess from. Not a PRD to infer from. Something that turns "what I meant" into a form the AI can verify: pass or fail, no guessing required.

What would change? Would the loop shrink? Would the hallucinations get caught before they ship? Would "Build X" → "Here's X" → "No, I meant…" finally break?

This chapter named the problem: the artifacts we use today—PRDs, user stories, prompts—are not verifiable by the AI, and the AI fills every gap with a plausible guess. The next chapter explores what happens when intent becomes verifiable—and who should write it.

---

## Key Points

- **Traditional artifacts fail with AI agents.** PRDs, user stories, and prompts are prose—unverifiable by the AI. The AI reads, guesses, and fills the gaps. Guesswork is hallucination.

- **The AI Agents era has a core pain point: many turns and hallucinations.** The "Prompt → Here's X → No, I meant…" loop runs at machine speed. Each turn costs context and attention. Each hallucination compounds. This is the default mode of working with AI today.

- **The scale is enormous: 70–90% knowledge loss, hundreds of billions in annual waste.** Research shows 70–90% of documentation-code mismatches stem from documentation failures; critical knowledge lives in meetings and heads, not durable artifacts. The financial cost: $260+ billion annually in the U.S. alone, $500 billion globally. The AI prompt that fills in wrong blanks, the feature that ignores unstated constraints—these are the default, not edge cases.

- **The hinge: what if intent was verifiable? What if the AI wrote the intent?** What if the AI could verify its output against a statement of intent—before it ships? What if the guesswork could be replaced with checking? The next chapter explores what happens when intent becomes verifiable—and who should write it.
