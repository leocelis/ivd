# Preface: Why This Book Exists

I watched a senior engineer spend three hours correcting an AI agent that could have built the entire feature in ten minutes. The prompts were clear. The model was capable. The output kept missing the point. Turn after turn, the engineer refined, clarified, and corrected.

That scene plays out thousands of times a day, across every team that builds with AI. The AI agent writes fast, writes confidently, and writes wrong—because it fills in the gaps in your request with plausible guesses. You correct. It rewrites. You correct again. The cycle has a name in this book: the **many turns problem**. And when the AI's guesses are baked into code before anyone catches them, that's **hallucination**—not a rare failure, but the default mode of working with AI today.

The cost is staggering. Industry research estimates that software failures—projects that deliver the wrong thing, overrun, or collapse—drain tens of billions of dollars annually in the United States alone, with global waste reaching into the hundreds of billions.[^1] Most of that waste traces back to the same root: **misalignment** between what someone intended and what got built. AI agents didn't create that gap. They made it run at machine speed.

If you are a developer, a tech lead, or anyone who builds software with AI agents—Cursor, Copilot, Claude, GPT, or whatever ships next—you have felt this. The exhaustion of correcting. The doubt that anyone (human or AI) understands what you actually meant. The growing suspicion that there has to be a better way.

There is. This book is about that better way.

[^1]: Standish Group, IEEE Spectrum, and industry analyses of software project failure rates. See Appendix F for full references.

---

## My Journey

[PLACEHOLDER: Leo's personal story — the following structure is recommended based on the intent. Replace the bracketed sections with your authentic experience.]

<!-- The preface journey should cover:
  1. A concrete moment or project where the many-turns problem hit you hardest
  2. What you tried that didn't work (traditional artifacts, better prompts, etc.)
  3. The insight: intent as the primary artifact — how you arrived at it
  4. The first time it worked: what changed
  5. The decision to build a framework and write this book
  
  Voice: First person ("I"), personal and direct.
  Pattern: McConnell (research + practice), Clean Code (brief and personal),
  Pragmatic Programmer (explaining motivation).
  Constraint: no_solution_depth — you can name IVD and the insight, but do NOT
  explain principles, artifact structure, or the verification workflow here.
  Chapter 1 is where teaching begins.
-->

[PLACEHOLDER: "I first hit this wall when..." — describe the concrete project or moment where the many-turns problem cost you the most. What were you building? What kept going wrong?]

[PLACEHOLDER: "I tried everything the industry recommended..." — briefly mention the artifacts and approaches you tried before IVD. Prompts, docs, better context. Why they fell short.]

[PLACEHOLDER: "The turning point was..." — describe the insight that led to IVD. When did you realize that intent—structured, verifiable, written by the AI—was the missing piece? Keep this to the *what*, not the *how*. Chapter 1 teaches the how.]

[PLACEHOLDER: "The first time it worked..." — describe what changed. Fewer turns. Fewer hallucinations. The AI checking its own work instead of you checking it. One concrete before/after.]

That experience became a framework. I tested it across [PLACEHOLDER: number] real projects—classification agents, data pipelines, API integrations, multi-agent systems—and measured the results. Not opinions. Data. Every claim in this book is backed by experiments you can reproduce. The framework is called **Intent-Verified Development**, and this book teaches it from first principles to production adoption.

---

## What You Will Learn, Build, and Validate

This is not a book of opinions. It is a book of evidence.

**Part I: The Paradigm Shift** gives you the problem and the framework. You will understand why traditional artifacts fail with AI agents, what IVD is, and how its eight principles work together to eliminate many turns and catch hallucinations at the source.

**Part II: Practice** puts you in the driver's seat. Six real projects—from a classification agent to a full-stack feature—built with IVD and compared to the usual prompt-and-correct approach so you see the difference. You will write intent, build with AI, and measure the results.

**Part III: Validation** proves every claim. Context efficiency, alignment accuracy, knowledge durability, recipe effectiveness—all measured, all reproducible. If you are skeptical, this is the part that will convince you.

**Part IV: Adoption** takes IVD from your desk to your team. Getting started, scaling across an organization, advanced patterns, and the ecosystem.

By the end, you will not hope your AI gets it right. You will *know*.

---

## How This Book Is Different

Most books about AI-assisted development tell you what to think. This one shows you what to measure.

Every claim in this book has been tested with real projects and real data. The code examples are production-ready. The templates and recipes are yours to use. The validation experiments are reproducible—you can run them yourself and verify the results.

This is not a book about prompting. It is a book about **alignment**: making sure the AI understands what you intend, verifies it before it builds, and proves it after. The difference between hoping and knowing.

---

## Who Should Read This Book

This book is for **developers and engineers** who build with AI agents and are tired of many turns and hallucinations. It is for **tech leads and engineering managers** who need their teams to ship faster and with fewer corrections. It is for **indie developers and startup founders** who rely on AI to build fast and can't afford the rework. It is for **computer science educators** teaching the next generation how to build with AI. And it is for anyone who believes that working with AI should feel like collaboration, not correction.

You need a working knowledge of software development. You don't need a PhD, a specific language, or prior experience with IVD. Part I starts from first principles. Part II provides hands-on projects. If you can read code and write a prompt, you can use this book.

## Who This Book Is *Not* For

If you are not building software—or not building with AI—this book will not serve you. IVD is a framework for the AI Agents era; if AI agents are not part of your workflow, the problem this book solves is not yours. Similarly, if you are looking for a prompt engineering guide or a tutorial on a specific AI model, look elsewhere. This book is about the layer above the model: the **intent** that tells the AI what to build and how to verify it.

---

**From "hope it works" to "prove it works."** That is the shift this book teaches. Turn the page.
