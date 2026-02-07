# Coordinator Agent Design Patterns: Intent vs Action Detection

**Research Date:** January 24, 2026  
**Status:** Active Research Document  
**Purpose:** Establish evidence-based patterns for coordinator agents to distinguish conversational intent from action requests

---

## Executive Summary

Coordinator agents face a critical challenge: **distinguishing between conversational context (what is being discussed) and action requests (what should be executed)**. This research synthesizes industry best practices, IVD principles, and ADA's operational learnings to establish clear design patterns.

**Key Finding:** Most coordinator failures stem from conflating chat history (context for understanding user intent) with system state (requiring tool calls to verify). The solution requires explicit architectural separation at the prompt level.

---

## 1. The Core Problem: Intent vs Action Ambiguity

### 1.1 Definition of Terms

| Term | Definition | Example |
|------|------------|---------|
| **Conversational Intent** | What topic the user is discussing; provides context for understanding | "I'm interested in the image from article 22777" |
| **Action Request** | An explicit or implicit command to perform an operation | "Show me the image from article 22777" |
| **Chat History** | Past conversation turns; indicates what was DISCUSSED | Summary: "User asked about images yesterday" |
| **System State** | Current data/status; requires tool calls to verify | Database check: Does image exist? What's its URL? |

### 1.2 The Failure Pattern

**Scenario:**
1. User asks: "Show me image 1 for article 22777"
2. Chat history contains: "User previously discussed article 22777 images. File paths: images/generated/xyz.png"
3. Coordinator sees file path in history → returns it directly
4. **Tool is never called** → No verification of current state

**Root Cause:** The coordinator treated chat history as system state rather than conversational context.

---

## 2. Industry Patterns for Action Detection

### 2.1 Verb-Based Action Taxonomy

**Source:** OpenAI Function Calling Documentation, Anthropic Agent Patterns

Action requests typically use specific verb categories:

| Category | Verbs | Examples |
|----------|-------|----------|
| **Creation** | generate, create, build, make, produce | "Generate an image" |
| **Execution** | run, start, execute, launch, deploy | "Run the analysis" |
| **Retrieval** | get, fetch, retrieve, show, display, find | "Show me the data" |
| **Modification** | update, change, edit, modify, delete | "Update the article" |
| **Validation** | check, verify, test, validate, confirm | "Check if it exists" |

### 2.2 The Imperative Mood Test

**Pattern:** Action requests use imperative mood (commands), while conversational intent uses indicative/interrogative mood.

```
✅ ACTION: "Show me the image" (imperative)
❌ CONVERSATION: "I'd like to know about the image" (indicative)
❌ CONVERSATION: "What images are available?" (interrogative, but actually an ACTION!)
```

**Limitation:** Indirect speech acts can be actions disguised as questions.

### 2.3 OpenAI's "Tool-First" Architecture

**Source:** OpenAI Agents Documentation (2026)

**Principle:** "To know current system state → CALL A TOOL"

OpenAI's guidance for agent systems:
- **Memory is for understanding intent** (what the user wants)
- **Tools are for retrieving facts** (what currently exists)
- Never assume data from conversation history
- Always use tools to verify current state

---

## 3. Multi-Agent Orchestration Patterns

### 3.1 Specialized Agents with Orchestrator

**Source:** Microsoft Magentic-One, LangGraph Documentation

**Architecture:**
```
User Request
    ↓
Orchestrator (Coordinator)
    ↓
├─→ WebSurfer Agent
├─→ Database Agent  
├─→ File Agent
└─→ Code Agent
```

**Key Pattern:** The orchestrator never executes work itself; it only routes to specialist agents.

**Rule:** If the orchestrator can answer without calling a tool, it probably shouldn't answer at all.

### 3.2 Routing Decision Tree

**Source:** LangChain Agent Executor, ADA Operational Learnings

```
User Request
    ↓
Does request contain action verb? ───NO──→ Clarify or decline
    ↓ YES
Is request self-contained? ───NO──→ Ask ONE clarifying question
    ↓ YES
Which agent owns this capability? ──→ Route to agent
    ↓
Execute tool call
    ↓
Return result verbatim
```

**Anti-Pattern:** Routing based on keyword matching instead of semantic understanding.

---

## 4. Chat History Injection: Best Practices

### 4.1 The Separation Principle

**Pattern:** Chat history must be framed as context, not as instructions or data.

**IVD Alignment:** From `MULTI_AGENT_KNOWLEDGE_SHARING_RESEARCH.md`:
> **Clear Instructions at the Beginning**: Place instructions at the beginning of prompts and use separators (`###`) to distinguish instructions from context.

**Template:**
```
### CORE INSTRUCTIONS
[System rules, capabilities, constraints]

### CONVERSATIONAL CONTEXT (FOR UNDERSTANDING USER INTENT ONLY)
**CRITICAL:** This is what was DISCUSSED, not what IS.
[Chat history summary and recent turns]

### CURRENT REQUEST
[User's current message]
```

### 4.2 Explicit Use-Case Labeling

**Pattern:** Tell the LLM exactly what chat history is FOR.

```markdown
Use chat history ONLY for:
- Understanding what topic the user is discussing
- Remembering user preferences mentioned earlier  
- Following conversation flow

Do NOT use chat history for:
- Determining what you can or cannot do (use your tools list)
- Deciding if data exists or doesn't exist (call the tool to check)
- Assuming previous failures still apply (systems get fixed)
```

### 4.3 The "Stale Data" Frame

**Pattern:** Explicitly mark historical data as potentially outdated.

```
Chat history may contain outdated information:
- File paths may have changed
- Data may have been updated
- Errors may have been fixed
- Tools may have been added

Always call tools to get current state.
```

---

## 5. ADA-Specific Learnings

### 5.1 The Chat History Poisoning Pattern

**Observed Failure (Jan 2026):**
```
User: "Show me the image for article 22777"
Chat Summary: "User asked about article 22777. File path: images/generated/xyz.png"
Coordinator: [Returns path from summary without calling tool]
```

**Root Cause:** Chat summary was too detailed and included data that should only come from tool calls.

**Lesson:** Chat summaries should capture topics/intent, not data/facts.

### 5.2 The Redundant Warning Anti-Pattern

**Observed Anti-Pattern:**
- 5+ sections in prompt all saying "don't trust chat history"
- Violations of DRY principle
- Creates confusion through repetition

**Better Pattern:** Single clear principle at the top, then specific rules in appropriate sections.

### 5.3 The False Negative Problem

**Pattern:** Coordinator refuses to call tool because chat history says it failed before.

```
Chat: "Assistant said: I don't have access to images"
User: "Show me the image"  [Tool WAS ADDED after that conversation]
Coordinator: "As I mentioned, I don't have access..."  [WRONG]
```

**Solution:** Treat chat history as conversational context, not capability limitations.

---

## 6. Proposed ADA Coordinator Architecture

### 6.1 Core Principle

```
TOOLS ARE TRUTH, HISTORY IS CONTEXT

Your tools list defines what you CAN do.
Chat history tells you what was DISCUSSED.

To know current system state → CALL A TOOL
To know what user wants → READ THEIR REQUEST + CHAT HISTORY FOR CONTEXT
```

### 6.2 Action Detection Rules

**Rule 1: Verb Test**
If the user message contains an action verb (generate, create, show, get, fetch, run, execute, update, delete, check), it is likely an action request.

**Rule 2: Current State Test**  
If the answer requires knowing current system state (does X exist? what is the URL for Y?), it requires a tool call.

**Rule 3: Data Retrieval Test**
If the user asks for specific data (ID, URL, file, image, record), call the appropriate retrieval tool.

**Rule 4: The "Verify" Override**
Even if chat history contains the answer, if the request is about current state, call the tool to verify.

### 6.3 Chat History Injection Pattern

```python
# Frame chat history explicitly
context_block = "### CONVERSATIONAL CONTEXT (FOR UNDERSTANDING USER INTENT ONLY)\n\n"
context_block += "**CRITICAL:** The information below is what was DISCUSSED, not what IS.\n"
context_block += "- To understand what the user wants → read this context\n"
context_block += "- To get current system state → call the appropriate tool\n"
context_block += "- NEVER answer data/retrieval requests from this context - always call tools\n\n"

if summary:
    context_block += f"**Previous Discussion Topics:**\n{summary}\n\n"
if history_str:
    context_block += f"**Recent Conversation:**\n{history_str}\n"
```

**Key Changes:**
1. Use `### ` section headers (ADA standard)
2. Label it "FOR UNDERSTANDING USER INTENT ONLY" (explicit purpose)
3. Lead with "DISCUSSED vs IS" distinction (core principle)
4. Provide explicit use cases (when to use, when not to use)
5. Rename "Summary" to "Previous Discussion Topics" (emphasizes topics, not facts)

### 6.4 Prompt Structure

```markdown
### CORE PRINCIPLE: TOOLS ARE TRUTH, HISTORY IS CONTEXT
[One clear statement of the principle]

### TOOL CALLING
[When to call tools - action verbs, current state queries]

### AGENT SELECTION  
[How to choose which specialist agent to route to]

### EXECUTION
[Sequential vs parallel, retry logic]

### OUTPUT
[How to return tool responses]

### CONVERSATIONAL CONTEXT (FOR UNDERSTANDING USER INTENT ONLY)
[Chat history injected here with explicit framing]

### CURRENT REQUEST
[User's message]
```

**Key Principle:** Separate instructions (what the agent should do) from context (conversation history) using clear section headers.

---

## 7. Verification Checklist

For any coordinator agent implementation, verify:

- [ ] Core principle stated at top (tools = truth, history = context)
- [ ] Action detection rules include verb taxonomy  
- [ ] Chat history is explicitly framed as "for understanding intent"
- [ ] Chat history section comes AFTER instructions, not mixed in
- [ ] Tool call requirements are explicit (when current state is needed)
- [ ] No redundant warnings about chat history (DRY principle)
- [ ] Clear separation: instructions vs context vs current request
- [ ] Chat summaries capture topics/intent, not data/facts

---

## 8. Testing Scenarios

### 8.1 Test Case: Action with Context

```
Chat History: "User discussing images for article 22777"
User Request: "Show me image 1 for that article"
Expected: Call get_article_image_tool(22777, 1, "simple")
Anti-Pattern: Return info from chat history
```

### 8.2 Test Case: Repeated Request After Failure

```
Chat History: "Tool call failed: image not found"
User Request: "Show me that image again"  [Image was since generated]
Expected: Call tool again (may have been fixed)
Anti-Pattern: "As I mentioned, the image wasn't found"
```

### 8.3 Test Case: Conversational vs Action

```
User: "I'm curious about the images"  → Conversational (clarify or wait)
User: "Show me the images"            → Action (call tool)
User: "What images are available?"    → Action disguised as question (call tool)
```

---

## 9. Implementation Recommendations

### 9.1 For ADA Coordinator

**Immediate Changes:**
1. Simplify coordinator prompt to single core principle at top
2. Reframe chat history injection with explicit purpose
3. Add action verb detection rules to TOOL CALLING section
4. Remove redundant "don't trust history" warnings from multiple sections

**Architecture Changes:**
1. Chat summaries should capture topics, not data
2. Consider separate "facts DB" vs "conversation history" stores
3. Tool responses should always override chat history memory

### 9.2 For Future Multi-Agent Systems

1. **Orchestrator Pattern:** Coordinator never executes, only routes
2. **Capability Registry:** Maintain dynamic list of what tools can do (vs trusting history)
3. **Action Intent Classifier:** Consider a dedicated pre-processing step that tags requests as "action" vs "conversation"
4. **Audit Trail:** Log when coordinator skips tool calls (for debugging "history poisoning")

---

## 10. References

1. OpenAI Agents Documentation (2026) - Tool-first architecture
2. Anthropic Claude Patterns - Constitutional AI and context management
3. Microsoft Magentic-One - Multi-agent orchestration
4. LangChain Agent Executor - Routing and action detection
5. ADA IVD Framework - `MULTI_AGENT_KNOWLEDGE_SHARING_RESEARCH.md`
6. ADA Operational Learnings - Chat history poisoning incident (Jan 2026)

---

## Changelog

| Date | Change | Reason |
|------|--------|--------|
| 2026-01-24 | Initial research document created | Coordinator failing to call tools due to chat history |
| 2026-01-24 | Added verb taxonomy and action detection rules | Evidence from OpenAI/Anthropic patterns |
| 2026-01-24 | Documented chat history injection pattern | ADA-specific learnings from production failure |
