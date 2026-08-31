# Graph Engineering — My Notes

**Core idea:** "The agent forgets, the graph does not." One loop with a `progress.md` file is fine. The moment I have _many_ loops or _many_ parallel agents, a plain text file can't be shared, queried, or trusted — so I need memory built as typed, connected records (nodes + edges) instead.

**Where this sits:** Loop Engineering = one agent that runs without me. Harness Engineering = walls around that one agent. Graph Engineering = shared memory + wiring once there's more than one loop.

---

## Part 1 — The Memory Problem

### 1. The Agent Forgets, the Graph Does Not

- A spine (`progress.md`) works for ONE loop. It breaks the moment: a second loop can't trust prose, 20 parallel agents can't share it, you can't query it, and it cites no sources.
- **Real example:** Agent #7 finds a timezone bug in `utils/dates.ts`. An hour later, Agent #14 finds the _same bug again_ — nothing connected them because each started with an empty context.

### 2. What a Graph Is: Nodes, Edges, Direction

- **Node** = a thing (entity, claim, commit, source). **Edge** = a labeled, _directed_ arrow between two nodes. Direction carries meaning.
- A **DAG** (directed acyclic graph) = arrows never loop back. Git history is one, already.
- **Real example:** `(Vendor X) —supplied→ (Component Z)` can be mechanically _traversed_ by code — chained onward to whatever else touches Component Z. A plain sentence in a log can't be chained like that.

### 3. Two Graphs, Never Collapsed

- **Commit DAG** = remembers the _work_ (what was tried). Facts by construction — it happened, Git guarantees it.
- **Knowledge graph** = remembers the _facts_ (what's known). Claims with evidence — might be wrong, needs a source and confidence.
- **Real example:** "I refactored the parser (commit 9fc2), and confirmed the vendor's API rejects pre-1970 dates" — the refactor lives in the commit DAG; the API behavior is a _claim_ for the knowledge graph, with the error response as its source.

---

## Part 2 — The DAG of Work

### 4. Autoresearch: The Ratchet Writes History Into Git

- Karpathy's pattern: one editable file, everything else frozen; propose one change, commit, measure, keep if better or `git reset` if worse.
- Two memories: the **Git branch** keeps only what was _retained_ (verified); a `results.tsv` log keeps _every_ attempt including crashes (untracked by git, on purpose).
- **Real example:** ~700 experiments run in two days, ~20 kept — the git branch shows only the winning chain; the tsv file shows the honest full story of every failed attempt too.

### 5. AgentHub: Traverse, Don't Merge to Main

- For swarms: don't reset failed experiments away — keep them as durable, queryable nodes. "GitHub is for humans. AgentHub is for agents."
- Commands read like graph queries: `children` (what was tried on top of this?), `leaves` (unexplored frontier), `lineage` (full ancestry of a result).
- **Real example:** Agent A's batch-size-64 experiment crashes from memory limits. Instead of vanishing, it's posted with its lineage — every future agent that queries it inherits the warning without re-running the crash.

---

## Part 3 — The Graph of Facts

### 6. Extraction: The Schema Is the Training Data

- Define entity/relation types as a schema (e.g. Pydantic classes), constrain a cheap model's output to that shape — no trained NLP pipeline needed anymore.
- **Real example:** Feed a README to a cheap model with a JSON schema for `{entities, relations}` — it returns structured triples instead of a paragraph you'd have to re-read every time.

### 7. Resolution: Same Thing, Many Names

- Same real-world thing can appear as different **surface forms** ("Edwin Aldrin," "Buzz Aldrin," "Col. Aldrin"). Merging them wrong (a **false merge**) is the catastrophic failure — always keep the merge reversible, with rationale + confidence + all original aliases kept.
- **Real example:** Two entities both named "M. Khan" but with different job descriptions (flight surgeon vs press officer) — must stay _separate_ people, not merged just because the name matches.

### 8. Provenance: Every Edge Keeps Its Receipt

- 4 invariants: every claim has a source (or is marked inference); every artifact has an authoring run; every evaluation names its rubric; superseded claims stay addressable (never deleted, just replaced).
- **Real example:** "Vendor X supplied Component Z" without a source is a rumor. With `source: contract.pdf, confidence: 0.94, run: agent_run_183` it's an auditable claim.

---

## Part 4 — Working From the Graph

### 9. The Subgraph, Not the Whole Graph

- Never dump 50,000 edges into one prompt. Resolve → expand 1-2 hops → include conflicts (don't hide disagreement) → serialize within a token budget → attach stable edge IDs so verdicts can cite them.
- **Real example:** For "the vendor incident" task, an agent gets ~20 relevant triples with IDs — not the entire company knowledge graph — and a synthesizer can combine findings from 20 workers who never each saw all the source documents.

### 10. The Grounded Checker: "Triple Not Found" Beats "Seems Off"

- An ungrounded reviewer says "this seems weak" (a mood — maker has to guess what to fix). A grounded reviewer checks the graph mechanically: does the supporting edge actually exist? If not, it names the exact missing evidence.
- **Real example:** Claim: "Vendor X supplied the component in Incident Y." Grounded checker: `{"decision": "revise", "required_evidence": ["a source-backed 'involved_in' relation to incident_y"]}` — a work order, not a vibe.

---

## Part 5 — The Graph of Loops (Governance)

### 11. The Wiring: Who Feeds Whom, Who Checks Whom

- Zoom out: each **loop** becomes one node. The graph is the wiring between loops — who routes to whom, who checks whom, where the human gate sits.
- **Real example:** Routine A drafts → a human decides → the decision fires Routine B. That's a 3-node governance graph, built without even knowing the name.

### 12. Perez's Four Failures of a Single Loop

- **Gaming** (Goodhart's law: number moves, real outcome doesn't) → fix: a watching loop on a counter-metric.
- **Blindness upward** (loop can't question its own target) → fix: a slower loop owns the target.
- **Conflict** (loops fight each other) → fix: an arbitration node/human gate.
- **Measurement decay** (checking one report against another report, not reality) → fix: independent audit loops.
- **Real example:** A support bot optimized "tickets closed per day." The number climbed — because it was marking abandoned problems as "solved" and pushing customers away. The metric won; the real goal lost.

### 13. Anchors and Frozen Nodes

- A graph where every loop only reads other loops' reports is **circular** — internally consistent, verified against nothing.
- **Anchors** = measurements no loop can argue with (tests that actually ran, money that actually arrived). **Frozen nodes** = rules the optimizing loops can never touch (e.g. `check.py`).
- **Real example:** Follow 10 random claims to their root. If they all trace back to another model's report instead of a real test/document/API, the "graph" is just consensus theater.

---

## Part 6 & 7 — Building It, and Staying Grounded

### 14. Choosing a Level

- 6 questions before building anything: Can success be verified? Are steps stable? Are subtasks independent? Must alternative lineages stay alive? Must facts survive the run? Can I afford the cost?
- A graph is the **8th rung** on a 9-step ladder (zero-shot → loop → chain → router → parallel workers → orchestrator → DAG → knowledge graph → dynamic workflow). Most work stops much earlier.
- **Real example:** Anthropic's own multi-agent research system used ~15x the tokens of a single chat reply — parallel breadth buys real coverage, but it has to earn that cost.

### 15. When NOT to Build a Graph

- Skip it when: tasks are independent, answers come from one document at a time, relations are simple (a plain table already answers every query), or nobody needs provenance.
- **Real example:** A team wants a knowledge graph "because agents." Their real answers (independent tasks, no shared state needed) point to plain parallel workers instead — building the graph anyway just adds extraction bugs for questions nobody asked.

### 16. What the Graph Cannot Do

- It cannot make the checker's PASS automatically trustworthy (the checker is still a model — can be measured, not blindly believed).
- It cannot decide what's worth remembering, which sources count as evidence, or what "better" means — that's still a human judgment call, always.
- **Real example:** The graph moves memory outside the context window — real progress. But someone still has to decide the ontology (what counts as an entity) and the source policy (what counts as trustworthy evidence). No amount of wiring does that job for you.

---

## The Big Picture

**Loop** → what to do and when. **Harness** → what's allowed and how it's proven. **Graph** → how it's all remembered once more than one loop/agent is involved. Three layers, one growing system.
## Related Notes

- [[Loop Engineering]]
- [[Harness Engineering]]
- [[Graph Engineering by Humna]]
- [[The Story of PixelDesk From Prompting to a Graph of Loops|PixelDesk Story]]