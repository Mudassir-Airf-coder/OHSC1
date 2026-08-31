# Loop Engineering — My Notes

**Core idea:** Prompting = you press "go" every step. Looping = you build a system once, and it presses "go" itself, forever, while you sleep.

**My goal in this:** the two things a loop can NEVER do for me — deciding what I actually want (**intent**) and owning the result when it ships (**accountability**). Everything else in the middle, the loop can do.

---

## Part 1 — The Shift

### 1. From Prompting to Looping

- Prompting: I start each turn, I read the output, I decide what's next. Stops the moment I stop typing.
- Looping: a schedule/event starts each turn, a **separate checker** grades it, keeps running while I sleep.
- **Real example:** Instead of me manually asking Claude every morning "check yesterday's GitHub issues," a loop does it at 9am on its own and posts a summary to Slack — even if my laptop is closed.

### 2. What a Loop Is Made Of (6 parts)

1. **Heartbeat** — what starts it (schedule/event)
2. **Worktree** — isolated folder so parallel agents don't collide
3. **Skill** — project knowledge written once (`SKILL.md`)
4. **Subagents** — maker–checker split (one writes, another grades)
5. **Connector (MCP)** — lets loop _act_ (open a PR, post to Slack), not just talk
6. **Spine** — memory that survives between runs (`progress.md` + rules file). **No spine, no loop** — without it, the loop repeats step 1 forever.

- **Real example:** A nightly "fix flaky tests" loop needs its own worktree (so it doesn't collide with my manual work), a skill describing test conventions, a checker agent to grade the fix, GitHub access to open a PR, and a `progress.md` so tomorrow's run knows what was already tried.

### 3. Two Ways to Build a Loop

- Claude Code = many parts built-in (`/loop`, `/goal`, Routines).
- OpenCode = you assemble parts yourself (shell scripts, cron, GitHub Actions).
- Same 6-part shape either way — that shape is the transferable skill, not the exact commands.

---

## Part 2 — The Heartbeat (what starts a loop)

### 4. In-session Loops

- Repeats on a timer _while your session/terminal is open_. Closes when you close the terminal.
- Like a kitchen timer — only rings while you're in the kitchen.
- **Real example:** `/loop 5m check if the deployment finished` — watches a live deploy while you grab coffee, but dies if you close the laptop.

### 5. Conditional Loop (Run-Until-Done)

- Stops when a **testable condition** is true, not on a timer. A separate checker decides "done" — never the worker itself.
- Needs 3 stops always: a **success condition**, a **limit** (max tries/cost), a **no-progress check** (catches it repeating the same failed move).
- **Real example:** `/goal All tests in test/auth pass and lint is clean` — Claude keeps fixing code until a test runner (not Claude itself) proves it's done.

### 6. Unattended Schedules (Routines)

- Runs on a clock, whether or not you're at the computer — the heartbeat that makes loop engineering actually matter.
- A Routine needs 4 answers: **prompt** (what to do), **repos** (where it can act), **connectors** (what it can reach), **trigger** (schedule / API call / GitHub event).
- Safety default: pushes only to `claude/` branches — never straight to `main`.
- **Real example:** Every weekday 8:30am, a Routine reads overnight GitHub issues, labels them, and posts a Slack summary — no human needed to start it.

### 7. Event-Driven Loops

- Reacts the instant something happens (PR opened, message received) — like a doorbell, silent until pressed.
- **Real example:** "The Doorbell" project — open a PR with a bug, and within a minute an unattended review appears, even with your laptop shut, because it runs on GitHub's rented servers, not yours.

---

## Part 3 — The Body (what the loop does each beat)

### 8. Isolation (Worktrees)

- Separate working folder/branch per agent so parallel agents don't overwrite each other's files.
- **Real example:** Two agents fixing "feature A" and "feature B" at the same time — each gets its own git worktree so their edits never collide.

### 9. Knowledge (Skills)

- Project habits written once in `SKILL.md`, loaded only when the task matches — keeps the loop prompt short.
- **Real example:** Instead of repeating "we use pnpm not npm, squash commits, run linter first" every single run, it's written once in a skill and read automatically.

### 10. Action (Connectors / MCP)

- Lets the loop actually _do_ things (open PR, post Slack, query DB) — not just describe what should happen.
- Rule: fewer, focused tools beat many overlapping ones; writes must be safe to repeat (no duplicate customers on retry); errors must say what to do next.
- **Real example:** A connector error "403 Forbidden" wastes a beat. "Permission denied: request the `repo` scope" lets the next beat self-heal.

### 11. Maker-Checker (Subagents)

- The agent that writes the work must NOT be the agent that approves it — a model checking its own work approves too easily.
- **Real example:** One subagent drafts a bug fix; a separate subagent (sometimes a cheaper model) reviews the diff against the spec and replies PASS/FAIL.

---

## Part 4 — The Spine (memory between runs)

### 12. State That Survives Between Runs

- The model forgets everything between runs — the _repo_ does not.
- Two layers: **rules file** (`CLAUDE.md`/`AGENTS.md`) = durable lessons read every run; **progress file** (`progress.md`) = what was tried, what passed, what's still open.
- Habit: every run reads the spine first, updates it last.
- **Real example (the intern's diary):** front of the diary = lessons ("don't use that pattern, this team squashes commits") read every morning; back of the diary = yesterday's checkpoint, so today doesn't restart from zero.

---

## Part 6 — Keeping Human Control

### 13. Token Cost Is the Real Limit

- Frequency drives cost more than the command used. Running every 5 min instead of once an hour can be >100x the beats for no extra value.
- Fixes: cap every loop, match model strength to job difficulty, keep rules file short, run less often.
- **Real example:** Same triage loop at 5 daily beats ≈ $20/month. The same loop firing every 5 minutes ≈ $1,800/month — same work, 100x the cost.

### 14. Checking the Work Is Still Your Job

- Maker-checker makes "done" _mean something_ — but it's still a claim, not a proof. Read the diffs before they count.
- **Real example:** A loop opens 5 PRs overnight, all "checker-approved." I still skim each diff at 9am before merging — trusting green checkmarks blindly is how quality erodes.

### 15. Don't Stop Understanding Your Own Project

- Building the loop can be _engagement_ (used with care) or _avoidance_ (used to stop thinking) — same action, opposite result.
- **Real example:** Two engineers build the identical overnight loop. One reads every PR and gets faster. The other stops reading, trusts green checks, and six months later can't explain how their own codebase works.

---

## What's Next

After Loop Engineering comes **Harness Engineering** (what happens _inside_ one beat — permissions, checks, error handling) and then **Graph Engineering** (shared memory when many loops work together).
## Related Notes

- [[Harness Engineering]]
- [[Graph Engineering]]
- [[Loop Engineering by Humna]]
- [[The Story of PixelDesk From Prompting to a Graph of Loops|PixelDesk Story]]