# IVD Judgment — Runnable Showcase

> **TL;DR** — A 5-second demo that proves IVD Judgment changes what
> the next AI agent run actually generates, using nothing but
> corrections you would have made anyway. No model fine-tuning. No
> vector store. No retrieval magic. Just disciplined capture,
> codification, and pattern promotion — applied to a problem every
> developer using AI coding agents (Cursor, Claude Code, Cline,
> Copilot…) lives through every week.

---

## What this demo answers

> "What does IVD Judgment actually DO for me?"

Your AI coding agent does not know your project's conventions.
It cannot — those conventions live ONLY in your repo, not in any LLM's
training data.  So it reaches for framework defaults every run.  You
correct it.  Next chat the corrections are gone and the agent ships the
default again.

**IVD Judgment closes that loop.**  This showcase makes the loop visible
in concrete, file-on-disk terms, using a story that maps onto every
front-end codebase that has ever standardized its own testing helpers:

1. **Three real-world incidents are captured** — the agent ignored
   this project's React testing conventions in three different test
   files in three weeks: `vi.fn()` instead of MSW, bare `render()`
   instead of `renderWithProviders()`, `userEvent.click()` instead of
   `userEvent.setup()` + `await user.click()`.
2. **They get codified** — same root cause, same recommended fix.
3. **The Judgment engine clusters them into a single Pattern.**
4. **The agent's next system message gets the Pattern injected.**
5. **The agent generates a completely different test file** on the same
   request — adopting all three project conventions it had been
   ignoring.

You can see all five steps in the four files this demo writes.

### Why this scenario is the canonical Judgment demo

This is the textbook IVD use case:

- **The convention CANNOT come from the model's training data.**
  Your `renderWithProviders` helper, your `src/test/mocks/server.ts`
  setup, the discipline of `userEvent.setup()` once per test — none of
  those exist on Stack Overflow.  A static system-prompt nudge does
  not solve this; the model needs to inherit the lesson from YOUR
  repo.
- **It's the highest-frequency surface for AI coding agents.**
  Agents write a lot of tests.  A convention violation in tests
  ships unnoticed (the test passes!) but corrupts every future
  generation.
- **The before/after diff is impossible to dismiss.**  The strings
  `renderWithProviders` and `server.use(http.get(...))` literally do
  not appear in the model's parametric memory of this project.  When
  they appear in the AFTER response, they came from one place: the
  Pattern Judgment promoted from your past corrections.

---

## Run it

From the IVD repo root:

```bash
# Offline (no API key — uses outputs literally captured from gpt-4o-mini)
python examples/judgment_demo/run_demo.py

# Live LLM (calls gpt-4o-mini at temperature=0, ~$0.001 / run)
OPENAI_API_KEY=sk-... python examples/judgment_demo/run_demo.py
```

It runs in ~5 seconds.  The terminal prints a colored, narrated walk
through Step 0 → Step 8 of the workflow.

---

## Screencast (≈30 s)

<!--
  TODO(maintainer): drop a 30-second screencast here.

  Recording recipe (any of these works):

    # Option A — asciinema (renders as text-selectable inline player on GitHub
    # via https://asciinema.org embed, or as a static GIF via agg):
    asciinema rec -c 'python examples/judgment_demo/run_demo.py' \
      examples/judgment_demo/judgment_demo.cast
    agg --theme monokai --speed 1.5 \
      examples/judgment_demo/judgment_demo.cast \
      examples/judgment_demo/judgment_demo.gif

    # Option B — terminalizer (pure GIF, no external player):
    terminalizer record judgment_demo \
      --command 'python examples/judgment_demo/run_demo.py'
    terminalizer render judgment_demo \
      -o examples/judgment_demo/judgment_demo.gif

    # Option C — vhs (declarative .tape file → GIF; reproducible):
    #   see https://github.com/charmbracelet/vhs

  Then replace this comment with:
    ![IVD Judgment showcase](judgment_demo.gif)

  Keep the GIF under 2 MB (use --speed 1.5 and ~80 cols) so the README
  loads fast on GitHub.
-->

> _Screencast placeholder._ Run the command above locally for the live
> 5-second walkthrough; a recorded GIF will land here once captured.

---

## What you'll see in the terminal

```
━━━ Step 1: Week 1: src/features/checkout/__tests__/PaymentForm.test.tsx ━━━
  Agent wrote a Vitest test for <PaymentForm /> that called `vi.fn()`
  to stub the submitPayment API call, called bare `render(<PaymentForm />)`
  without our providers, and used `userEvent.click(submitButton)`
  without setup…

━━━ Step 2: Week 2: src/features/dashboard/__tests__/MetricsCard.test.tsx ━━━
  MetricsCard.test.tsx flaked 3x in CI this week — agent used jest.fn()
  to mock fetchMetrics() and bare render().  No AuthContext was
  provided, so the component early-returned the loading state…

━━━ Step 3: Week 3: src/features/settings/__tests__/ProfileSettings.test.tsx ━━━
  Agent ignored test-utils.tsx AGAIN.  7 separate vi.fn() mocks
  instead of MSW handlers.  Bare render().  Mix of fireEvent and
  userEvent without setup().  Wall of act() warnings in CI…

━━━ Step 4: BEFORE the pattern is promoted ━━━
  patterns in context  0   ← agent has no consolidated guidance

━━━ Step 5: you run `ivd_judgment_detect_patterns` ━━━
  patterns promoted    1
  member_count         3 incidents (3-week window)
  weighted_confidence  1.0 (max — all expert depth)

━━━ Step 6: AFTER the pattern is promoted ━━━
  patterns in context  1   ← consolidated guidance available
  injection_hash       b56f19153c8f3540…   ← provably changed
```

---

## What you'll find on disk

| File                              | What it is                                                        |
| --------------------------------- | ----------------------------------------------------------------- |
| `output/before.md`                | The system message the agent saw the FIRST time (no Judgment)     |
| `output/after.md`                 | The system message the agent sees NOW (3 incidents → 1 Pattern)   |
| `output/diff.md`                  | A clean diff that highlights exactly what Judgment added          |
| `output/llm_responses.md`         | Side-by-side agent responses on the same request, before vs after |
| `output/your_project/.judgment/`  | The actual on-disk Judgment store — inspect everything            |

---

## What Judgment added to the agent's system message

This block was absent from the agent's instructions before Judgment
compounded.  It is now hard-attached to every code-generation request
in this project:

```
## LESSONS LEARNED IN THIS PROJECT (from past corrections)

### Pattern 1: code__agent-ignores-project-test-conventions-…
- Confidence: 1.0 (from 3 incidents, freshness: fresh)
- Root cause we keep hitting:
  agent_ignores_project_test_conventions: AI agent writes React tests
  using framework defaults (raw jest.fn() mocks, bare render(),
  inline userEvent.click) instead of this project's standardized
  testing primitives (MSW handlers, renderWithProviders helper,
  userEvent.setup).  These conventions live ONLY in this repo —
  the model has no parametric knowledge of them and reaches for
  its training-data defaults every run.
- Required fix (apply unconditionally):
  Every React component test in this project MUST follow these
  three conventions without exception:
    1. MOCKING: never use `jest.fn()` to mock API calls.  Use the
       MSW server defined in `src/test/mocks/server.ts`.  Override
       per test with `server.use(http.get('/api/...', () => HttpResponse.json(...)))`.
    2. RENDERING: never call bare `render(<Foo />)` from
       @testing-library/react.  Always import and use
       `renderWithProviders` from `src/test/test-utils.tsx`…
    3. USER INTERACTION: never call `userEvent.click(...)` directly.
       First create a user instance with `const user = userEvent.setup()`…
```

That block came from your own corrections.  It is local to this
project.  It compounds with every additional incident.  It self-decays
through the half-life policy.

---

## The behavioral diff (real LLM, captured verbatim)

`output/llm_responses.md` shows the same coding request answered TWICE
by `gpt-4o-mini` at `temperature=0`.  The two responses below are
**literal captures from the live API**.  Repeat the experiment yourself
and you will see the same shape every time.

**Request:** _"Write a Vitest test file for the `<UserMenu />` React
component.  Verify that the user's name 'Ada Lovelace' is visible
after mount, the avatar img has the right src, and clicking 'Sign out'
calls POST `/api/logout` exactly once.  Output ONLY a single TypeScript
code block — no commentary."_

**Agent response — BEFORE Judgment** (no consolidated guidance, model
reaches for framework defaults from its training data):

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import UserMenu from '../components/UserMenu';

global.fetch = vi.fn();   // ← anti-pattern #1: API mocked via vi.fn()

describe('<UserMenu />', () => {
  it('renders user name and avatar after mount', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        name: 'Ada Lovelace',
        avatarUrl: 'https://cdn.example.com/ada.png',
      }),
    });

    render(<UserMenu />);   // ← anti-pattern #2: bare render(), no providers

    expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument();
  });

  it('triggers logout on sign out button click', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    (fetch as jest.Mock).mockResolvedValueOnce({ ok: true });

    render(<UserMenu />);

    const signOutButton = await screen.findByRole('button', { name: /sign out/i });
    userEvent.click(signOutButton);   // ← anti-pattern #3: no userEvent.setup()

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/logout', { method: 'POST' });
    });
  });
});
```

**Agent response — AFTER Judgment** (same model, same temperature,
same request — only the system message changed):

```typescript
import { renderWithProviders } from 'src/test/test-utils';   // ← convention #2 adopted
import { UserMenu } from 'src/components/UserMenu';
import { server } from 'src/test/mocks/server';              // ← convention #1 adopted
import { rest } from 'msw';
import userEvent from '@testing-library/user-event';
import { screen } from '@testing-library/react';

it('renders user name and avatar after mount', async () => {
  server.use(
    rest.get('/api/me', (req, res, ctx) =>
      res(ctx.json({
        name: 'Ada Lovelace',
        avatarUrl: 'https://cdn.example.com/ada.png',
      })),
    ),
  );

  renderWithProviders(<UserMenu />);   // ← project helper, used correctly

  expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument();
});

it('triggers logout on sign out button click', async () => {
  const logoutHandler = jest.fn();   // ← jest.fn() as a SPY (legitimate)

  server.use(
    rest.get('/api/me', (req, res, ctx) =>
      res(ctx.json({
        name: 'Ada Lovelace',
        avatarUrl: 'https://cdn.example.com/ada.png',
      })),
    ),
    rest.post('/api/logout', (req, res, ctx) => {
      logoutHandler();
      return res(ctx.status(200));
    }),
  );

  renderWithProviders(<UserMenu />);

  const user = userEvent.setup();        // ← convention #3 adopted
  const signOutButton = await screen.findByRole('button', { name: /sign out/i });
  await user.click(signOutButton);

  expect(logoutHandler).toHaveBeenCalledTimes(1);
});
```

The verdict line the demo prints (representative; n=3 trials with real
`gpt-4o-mini`):

> **JUDGMENT WORKED.**  The BEFORE agent reached for 3/3 framework
> defaults — raw `vi.fn()` / `jest.fn()` API mocks, bare `render()` (no
> providers), `userEvent.click` without `setup()`.  The AFTER agent —
> same model, same temperature, same request — adopted **3/3 of THIS
> PROJECT'S testing conventions:** MSW handler (`server.use` + `http.*`),
> `renderWithProviders` helper, `userEvent.setup()` before
> interactions.  These conventions live only in the repo
> (`renderWithProviders`, `server.use`) and could not have come from
> the model's training data.  The agent inherited them purely from
> your 3 past corrections being compounded into a single Pattern and
> injected at run time.

### What this proves

Three string presences in the AFTER response that **literally cannot
have come from the model's parametric memory**:

| String                    | Where it lives                                | Verdict signal              |
| ------------------------- | --------------------------------------------- | --------------------------- |
| `renderWithProviders(`    | `src/test/test-utils.tsx` (project-local)     | Convention #2 (rendering)   |
| `server.use(rest.get(...))` | `src/test/mocks/server.ts` (project-local)  | Convention #1 (mocking)     |
| `userEvent.setup()`       | Project linter rule + this Pattern            | Convention #3 (interaction) |

Same agent.  Same model.  Same temperature.  Same request.  The only
difference is the system message — and the system message changed
because you did the work of capturing your own corrections through the
Judgment phase.

That difference compounds across every future test the agent writes
in this project.  It does not require you to remember the lesson next
Monday.  It does not vanish when the chat session ends.  It does not
need to be re-explained to a new contractor.  It is built into the
project.

---

## Reproducibility

The demo is wrapped by a regression test that pins every claim made
above:

```bash
pytest mcp_server/tests/integration/test_judgment_demo.py -v
```

Twenty-one assertions cover:

- The full pipeline (init → capture × 3 → codify × 3 → detect → inject)
- The presence of `LESSONS LEARNED`, `renderWithProviders`,
  `server.use`, `userEvent.setup()`, and the canonical fix string in
  `after.md`
- Their absence in `before.md` (the agent had no parametric or
  contextual knowledge of these project-local helpers on day one)
- The `injection_hash` provably changing (auditable proof of context
  delta)
- The canned LLM outputs containing the framework-default
  anti-patterns (BEFORE) and the three project conventions (AFTER)
- The script main writing all four output files end-to-end

If any of those break, the demo no longer demonstrates the loop —
and the test fails loudly so the regression is caught before a user
sees it.

---

## Where to go next

- The Judgment phase canonical spec: [`ivd/judgment_layer.md`](../../judgment_layer.md)
- The 10 Judgment MCP tools: [`ivd/cheatsheet.md`](../../cheatsheet.md) §Part 2.5
- The full IVD framework: [`ivd/framework.md`](../../framework.md) §Principle 9
- Principle 9 — "Judgment Compounds": [`ivd/cookbook.md`](../../cookbook.md)
- Run the full integration test suite:
  `bash mcp_server/devops/test.sh --integration`
