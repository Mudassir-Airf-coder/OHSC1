"""Generate three isolated OHSC Graphify test vaults (Phase 6).

These vaults are TEMPORARY validation fixtures. They are created outside the
real Obsidian vault and deleted after validation (Phase 14).

Each note is a realistic Markdown file with wikilinks and semantic content so
Graphify can discover both explicit (wikilink) and semantic relationships.
"""
from pathlib import Path

ROOT = Path(r"D:\HOSC\validation")

# ----------------------------------------------------------------------------
# BASIC VAULT (~10 notes): single hub (OHSC) + related concepts
# ----------------------------------------------------------------------------
basic = {
    "OHSC.md": "# OHSC\n\nOHSC (Hermes Obsidian System Control) is the control plane that "
               "orchestrates [[Agent]]s to operate an Obsidian vault. It routes natural-language "
               "requests to the correct agent, including the [[Graphify Agent]] for knowledge-graph work.\n",
    "Agent.md": "# Agent\n\nAn Agent is an autonomous unit in [[OHSC]] that performs a focused task. "
                "Agents communicate through a shared message bus and are coordinated by the planner.\n",
    "Graphify Agent.md": "# Graphify Agent\n\nThe [[Graphify Agent]] builds and queries a knowledge graph "
                         "of the vault using [[Graphify]] and the Graphify Brain backend. It answers "
                         "relationship and shortest-path questions.\n",
    "Graphify.md": "# Graphify\n\n[[Graphify]] turns a folder of notes into a queryable knowledge graph. "
                   "It extracts [[Node]]s and [[Relationship]]s and clusters them into communities.\n",
    "Node.md": "# Node\n\nA [[Node]] is a concept or note in the knowledge graph produced by [[Graphify]]. "
               "Nodes are linked by [[Relationship]]s.\n",
    "Relationship.md": "# Relationship\n\nA [[Relationship]] connects two [[Node]]s in the graph built by "
                       "[[Graphify]]. Relationships can be explicit (wikilinks) or semantic.\n",
    "MCP.md": "# MCP\n\n[[MCP]] (Model Context Protocol) lets the [[Graphify Agent]] expose graph "
              "capabilities such as query and shortest-path to external tools.\n",
    "Knowledge Graph.md": "# Knowledge Graph\n\nA [[Knowledge Graph]] represents notes as [[Node]]s and "
                          "their connections as [[Relationship]]s. [[OHSC]] uses it for reasoning.\n",
    "Harness Engineering.md": "# Harness Engineering\n\n[[Harness Engineering]] builds the test harness that "
                              "validates [[Agent]] behaviour inside [[OHSC]].\n",
    "Loop Engineering.md": "# Loop Engineering\n\n[[Loop Engineering]] designs the control loops that let an "
                           "[[Agent]] iterate toward a goal under [[OHSC]].\n",
}

# ----------------------------------------------------------------------------
# INTERMEDIATE VAULT (~18 notes): two hubs, cross-topic, orphan candidate
# ----------------------------------------------------------------------------
inter = {
    "OHSC.md": "# OHSC\n\n[[OHSC]] is the control plane for Obsidian automation. It hosts the "
               "[[Planner]], the [[Graphify Agent]], and the [[Search Agent]]. It relies on "
               "[[MCP]] for tool integration and on [[OpenCode]] as the model execution layer.\n",
    "Planner.md": "# Planner\n\nThe [[Planner]] classifies natural-language requests and routes them to the "
                  "right [[Agent]] (e.g. [[Graphify Agent]] vs [[Search Agent]]). It uses intent rules.\n",
    "Graphify Agent.md": "# Graphify Agent\n\nThe [[Graphify Agent]] drives [[Graphify]] through the "
                         "[[Graphify Brain]] to build a [[Knowledge Graph]] from the vault.\n",
    "Search Agent.md": "# Search Agent\n\nThe [[Search Agent]] answers keyword and semantic search queries. "
                       "It must NOT handle graph questions; those go to the [[Graphify Agent]].\n",
    "Graphify.md": "# Graphify\n\n[[Graphify]] extracts [[Node]]s and [[Relationship]]s and detects "
                   "[[Community]]s and [[Hub Node]]s in a vault.\n",
    "Graphify Brain.md": "# Graphify Brain\n\nThe [[Graphify Brain]] is the LLM layer behind [[Graphify]]. "
                         "It uses [[OpenCode]] to run the [[HY3]] model for semantic extraction.\n",
    "OpenCode.md": "# OpenCode\n\n[[OpenCode]] is the LLM execution layer. [[OHSC]] calls it through the "
                   "[[Graphify Brain]] to run [[HY3]].\n",
    "HY3.md": "# HY3\n\n[[HY3]] is the model served by [[OpenCode]] for semantic graph extraction inside "
              "the [[Graphify Brain]].\n",
    "Knowledge Graph.md": "# Knowledge Graph\n\nA [[Knowledge Graph]] links [[Node]]s via [[Relationship]]s "
                          "and groups them into [[Community]]s.\n",
    "Node.md": "# Node\n\nA [[Node]] is a vertex in the [[Knowledge Graph]] from [[Graphify]].\n",
    "Relationship.md": "# Relationship\n\nA [[Relationship]] connects [[Node]]s in the [[Knowledge Graph]].\n",
    "Community.md": "# Community\n\nA [[Community]] is a densely-connected group of [[Node]]s detected by "
                    "[[Graphify]].\n",
    "Hub Node.md": "# Hub Node\n\nA [[Hub Node]] has a high degree of [[Relationship]]s and connects multiple "
                   "[[Community]]s.\n",
    "MCP.md": "# MCP\n\n[[MCP]] exposes [[Graphify Agent]] capabilities (query, shortest-path) to tools.\n",
    "Orphan Note.md": "# Orphan Note\n\nThis note is about [[Gardening]] and has no links to the rest of the "
                      "system. It is an orphan candidate for Graphify to detect.\n",
    "Gardening.md": "# Gardening\n\n[[Gardening]] is the practice of tending plants. This note is unrelated "
                    "to [[OHSC]] and should appear as an isolated concept.\n",
    "Reviewer.md": "# Reviewer\n\nThe [[Reviewer]] inspects [[OHSC]] architecture, security, and test results "
                  "before a release is approved.\n",
    "Caching.md": "# Caching\n\n[[Caching]] lets [[Graphify]] reuse an existing [[Knowledge Graph]] when the "
                  "vault is unchanged, saving [[OpenCode]] calls.\n",
}

# ----------------------------------------------------------------------------
# ADVANCED VAULT (~34 notes): multiple domains, cross-domain, provenance
# ----------------------------------------------------------------------------
adv_core = {
    "OHSC.md": "# OHSC\n\n[[OHSC]] orchestrates [[Agent]]s to control an Obsidian vault. It routes via the "
               "[[Planner]] to the [[Graphify Agent]], [[Search Agent]], and [[Reviewer]]. It depends on "
               "[[MCP]] and [[OpenCode]].\n",
    "Planner.md": "# Planner\n\nThe [[Planner]] maps intent to agent. Graph requests go to the "
                  "[[Graphify Agent]]; search goes to the [[Search Agent]].\n",
    "Agent.md": "# Agent\n\nAn [[Agent]] is an autonomous worker in [[OHSC]]. Examples: [[Graphify Agent]], "
                "[[Search Agent]], [[Reviewer]].\n",
    "Graphify Agent.md": "# Graphify Agent\n\nThe [[Graphify Agent]] builds a [[Knowledge Graph]] via "
                         "[[Graphify]] and the [[Graphify Brain]].\n",
    "Search Agent.md": "# Search Agent\n\nThe [[Search Agent]] handles retrieval; graph questions are routed "
                       "to the [[Graphify Agent]].\n",
    "Reviewer.md": "# Reviewer\n\nThe [[Reviewer]] audits architecture, security, and tests before approval.\n",
    "Graphify.md": "# Graphify\n\n[[Graphify]] turns notes into a [[Knowledge Graph]] of [[Node]]s and "
                   "[[Relationship]]s, with [[Community]] and [[Hub Node]] detection.\n",
    "Graphify Brain.md": "# Graphify Brain\n\nThe [[Graphify Brain]] is the LLM layer using [[OpenCode]] and "
                         "[[HY3]] for semantic extraction.\n",
    "OpenCode.md": "# OpenCode\n\n[[OpenCode]] executes [[HY3]] for [[OHSC]] via the [[Graphify Brain]].\n",
    "HY3.md": "# HY3\n\n[[HY3]] is the model run by [[OpenCode]] inside the [[Graphify Brain]].\n",
    "MCP.md": "# MCP\n\n[[MCP]] exposes [[Graphify Agent]] graph tools (query, shortest-path, communities).\n",
    "Knowledge Graph.md": "# Knowledge Graph\n\nA [[Knowledge Graph]] represents the vault as [[Node]]s and "
                          "[[Relationship]]s grouped into [[Community]]s.\n",
    "Node.md": "# Node\n\nA [[Node]] is a vertex (note/concept) in the [[Knowledge Graph]].\n",
    "Relationship.md": "# Relationship\n\nA [[Relationship]] links two [[Node]]s; can be explicit or semantic.\n",
    "Community.md": "# Community\n\nA [[Community]] is a dense subgroup of [[Node]]s in the [[Knowledge Graph]].\n",
    "Hub Node.md": "# Hub Node\n\nA [[Hub Node]] connects multiple [[Community]]s via many [[Relationship]]s.\n",
    "Caching.md": "# Caching\n\n[[Caching]] reuses the [[Knowledge Graph]] when the vault is unchanged.\n",
    "Vault Safety.md": "# Vault Safety\n\n[[Vault Safety]] guarantees [[OHSC]] never writes into the real "
                       "Obsidian vault; all artifacts live under the workspace.\n",
    "Path Engineering.md": "# Path Engineering\n\n[[Path Engineering]] computes the shortest conceptual "
                           "[[Relationship]] path between two [[Node]]s using [[Graphify]].\n",
    "Semantic Extraction.md": "# Semantic Extraction\n\n[[Semantic Extraction]] infers [[Relationship]]s that "
                              "are not explicit wikilinks, powered by [[HY3]] in the [[Graphify Brain]].\n",
    "Provenance.md": "# Provenance\n\n[[Provenance]] records which [[Agent]] and model produced each "
                     "[[Relationship]] in the [[Knowledge Graph]].\n",
    "Intent Routing.md": "# Intent Routing\n\n[[Intent Routing]] is the [[Planner]]'s job of sending graph "
                         "asks to the [[Graphify Agent]].\n",
    "Failure Handling.md": "# Failure Handling\n\n[[Failure Handling]] returns structured errors (status, "
                           "error_type, retryable) when [[OpenCode]] or [[Graphify]] fail.\n",
    "Performance.md": "# Performance\n\n[[Performance]] tracks [[OpenCode]] latency and [[Caching]] hit rate "
                     "for the [[Graphify Brain]].\n",
    "Diagnostics.md": "# Diagnostics\n\n[[Diagnostics]] compares backends (e.g. [[OpenCode]] vs alternatives) "
                      "without exposing credentials.\n",
    "Configuration.md": "# Configuration\n\n[[Configuration]] selects the backend ([[OpenCode]]) and model "
                        "([[HY3]]) via environment variables for the [[Graphify Brain]].\n",
    "Security.md": "# Security\n\n[[Security]] ensures the [[OpenCode]] credential is never logged, printed, "
                  "or committed by [[OHSC]].\n",
    "Testing.md": "# Testing\n\n[[Testing]] validates the [[Graphify Agent]] end-to-end across basic, "
                  "intermediate, and advanced vaults.\n",
    "Documentation.md": "# Documentation\n\n[[Documentation]] records the [[Graphify Brain]] architecture and "
                        "the [[OpenCode]] + [[HY3]] production setup.\n",
    "Loop Engineering.md": "# Loop Engineering\n\n[[Loop Engineering]] builds control loops for [[Agent]] "
                           "iteration under [[OHSC]].\n",
    "Harness Engineering.md": "# Harness Engineering\n\n[[Harness Engineering]] builds validation harnesses "
                              "for [[Agent]]s in [[OHSC]].\n",
    "Graph Engineering.md": "# Graph Engineering\n\n[[Graph Engineering]] designs the [[Knowledge Graph]] "
                            "schema ([[Node]], [[Relationship]], [[Community]]).\n",
    "Schema.md": "# Schema\n\nThe graph [[Schema]] defines [[Node]] and [[Relationship]] types used by "
                 "[[Graphify]].\n",
    "Embedding.md": "# Embedding\n\n[[Embedding]]s power semantic similarity used in [[Semantic Extraction]].\n",
    "Query Engine.md": "# Query Engine\n\nThe [[Query Engine]] answers questions over the [[Knowledge Graph]] "
                      "via the [[Graphify Agent]].\n",
    "Shortest Path.md": "# Shortest Path\n\n[[Shortest Path]] finds the minimal [[Relationship]] chain "
                        "between [[Node]]s (see [[Path Engineering]]).\n",
    "Orphan Detection.md": "# Orphan Detection\n\n[[Orphan Detection]] finds [[Node]]s with no "
                           "[[Relationship]]s in the [[Knowledge Graph]].\n",
    "Hub Detection.md": "# Hub Detection\n\n[[Hub Detection]] ranks [[Node]]s by degree to surface "
                        "[[Hub Node]]s.\n",
    "Community Detection.md": "# Community Detection\n\n[[Community Detection]] groups [[Node]]s into "
                              "[[Community]]s with [[Graphify]].\n",
    "Cross Domain.md": "# Cross Domain\n\n[[Cross Domain]] links bridge separate topic areas in the "
                      "[[Knowledge Graph]], e.g. [[Security]] and [[Performance]].\n",
    "Gardening.md": "# Gardening\n\n[[Gardening]] is an unrelated hobby topic kept as an orphan to test "
                   "[[Orphan Detection]].\n",
}
adv = dict(adv_core)

def write_vault(name: str, notes: dict):
    base = ROOT / name
    (base / ".obsidian").mkdir(parents=True, exist_ok=True)
    for fn, body in notes.items():
        (base / fn).write_text(body, encoding="utf-8")
    print(f"{name}: {len(notes)} notes -> {base}")

write_vault("basic_vault", basic)
write_vault("intermediate_vault", inter)
write_vault("advanced_vault", adv)
print("DONE")
