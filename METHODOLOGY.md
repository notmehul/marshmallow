# Methodology

Marshmallow is intentionally small, but the shape is not accidental.

This document explains the product reasoning behind the first public plugin: the
problem we chose, the systems we studied, the ideas we borrowed, the complexity
we deferred, and the tests that should decide what gets built next.

The public research pass was refreshed on June 2, 2026. Product descriptions
below summarize the linked public documentation and repositories. They are not
claims that Marshmallow has independently benchmarked every system.

## The Problem We Chose

The broad problem is the correction tax around AI agents. Users repeatedly
explain the same judgment, preferences, constraints, and quality bars because
each new session starts too far away from how they actually work.

Marshmallow starts with a concrete promise:

> Give agent harnesses the smallest relevant personal context from the first
> prompt, then learn selectively from corrections and sources the user
> deliberately chooses to preserve.

A frontend skill may reliably produce responsive layouts while repeatedly
choosing an aesthetic you dislike. A planning skill may keep expanding scope
when you value a sharp wedge. An architecture skill may introduce services
before a local file has failed.

Repeated prompting is a weak fix. The same correction tax returns in the next
session even when no specialized skill is active.

The runtime model is:

```text
user-level harness adapter
+ smallest relevant personal projection
+ optional source-backed skill overlay
+ current task
= better first attempt
```

One local graph can improve ordinary harness use and feed many judgment-
sensitive skills over time.

## The Research Questions

We used five questions to keep the research grounded:

1. What personal context materially changes an agent's output?
2. What belongs in durable memory, and what should remain a source pointer?
3. How should a rich graph affect work without bloating every prompt?
4. What should be deterministic filesystem logic, and what should remain host-agent judgment?
5. What is the smallest persistent alignment layer that can be trusted, tested, and rolled back?

The answer is not a universal second-brain platform. For v1, it is an
inspectable compiler from inbox candidates to source-backed insights and compact
tagged projections, plus reviewable skill overlays where they add leverage.

## Research Map

We studied several adjacent product families. Many are solving real problems.
The goal was to borrow their strongest ideas without inheriting their full
operating surface.

### Memory APIs And Context Infrastructure

These systems focus on application memory, retrieval, evolving facts, and
production-scale context delivery.

| System | What we studied | What it taught us | Why it is not the v1 shape |
| --- | --- | --- | --- |
| [Honcho](https://github.com/plastic-labs/honcho) | Peers, sessions, messages, background reasoning, and evolving peer representations | Memory becomes more useful when raw history compiles into a compact representation that can be queried cheaply | Marshmallow borrows representation thinking, but keeps the graph local and source-traced instead of introducing a server or opaque background inference |
| [PAMbase](https://docs.pambase.io/) | One user-owned memory shared across apps, natural-language briefs, separate read/write permissions, and app-specific personas | Personal context should have one canonical home. Harnesses should consume the same memory through small pointers instead of inventing parallel profiles | Cross-app accounts, permission scopes, and hosted shared memory are later product layers. V1 proves the local single-user contract first |
| [Mem0](https://github.com/mem0ai/mem0) and [OpenMemory](https://github.com/mem0ai/mem0/tree/main/openmemory) | User, session, and agent memory scopes; local and managed paths; retrieval over accumulated memories | Long-term memory is a real developer primitive, and portability matters | A general memory API is broader than the first user-visible proof. OpenMemory is also being sunset in favor of Mem0's self-hosted server |
| [Graphiti](https://github.com/getzep/graphiti) / [Zep](https://www.getzep.com/) | Temporal context graphs with entities, facts, validity windows, provenance episodes, and hybrid retrieval | Evolving truth and provenance matter. Old information should be superseded deliberately, not silently erased | Temporal graph infrastructure is powerful but unnecessary before a small Markdown graph proves value |
| [Supermemory](https://github.com/supermemoryai/supermemory) | Memory extraction, static and dynamic profiles, connectors, hybrid search, contradiction handling, and forgetting | Runtime context should be compact and useful immediately; profiles and documents solve different problems | Connectors, hosted sync, extraction infrastructure, and automatic profile maintenance are deferred until the explicit loop earns them |
| [Cognee](https://github.com/topoteretes/cognee) | Knowledge-engine framing, graph and vector retrieval, ingestion, and MCP access | Shared context can become infrastructure for many agents and applications | Marshmallow starts before the control plane: local files, human correction, and no MCP server |

The useful synthesis is simple:

```text
raw material
-> compiled representation
-> small runtime projection
```

Marshmallow applies that pattern to personal builder judgment rather than
shipping a general memory backend.

### Local Brains, Markdown Graphs, And Agent Knowledge Systems

These systems helped clarify the value of inspectable local knowledge and the
risk of building too much machinery too early.

| System | What we studied | What we borrowed | What we deferred |
| --- | --- | --- | --- |
| [Ars Contexta](https://github.com/agenticnotetaking/arscontexta) | Conversational setup, Markdown knowledge graphs, progressive disclosure, reduction, reflection, reweaving, verification, and system rethinking | Graphs should guide attention. New learning should update older synthesis. Important pages should pass a cold-read test | Its generated knowledge-system factory, broad command catalog, hooks, mandatory schemas, and automation surface |
| [GBrain](https://github.com/garrytan/gbrain) | Markdown brains, inbox capture, graph plus search, citations, retrieval evaluation, and schema packs that can be detected from the user's actual filesystem | Preserve source authority, stage captures before curation, evaluate likely queries, and let structure evolve from the corpus | Database engines, MCP breadth, resolver tables, job queues, large schema packs, and a wide skill catalog |
| [Hermes Agent memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory/) and its [`llm-wiki`](https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/research/research-llm-wiki) skill | Bounded curated `MEMORY.md` and `USER.md`, on-demand session search, a broad harness-level skill library, and an agent-operated local Markdown wiki | Keep prompt-facing memory compact, keep raw history out of always-loaded context, and let the harness own execution breadth | Becoming a session-history store, universal skill marketplace, renderer, integration layer, or task runner |
| [`coding_agent_session_search`](https://github.com/Dicklesworthstone/coding_agent_session_search) | Local indexing across coding-agent histories, bounded cited handoffs, archive-first recovery, source authority, and rebuildable derived assets | Preserve originals, make derived views disposable, and expose reviewable context instead of pretending the index is canonical truth | Session-history indexing is useful adjacent infrastructure, not Marshmallow's first product loop |
| [3Notch](https://3notch.dev/) | Portable packets containing files, briefs, intent, deterministic manifests, previews, and a local trail | Local-first handoff artifacts should be inspectable and previewable. Files should remain authoritative | Packet transport and MCP are neighboring workflows. Marshmallow v1 focuses on compiling personal judgment into skill overlays |

The strongest lesson was restraint: a local knowledge substrate can remain
useful without becoming a large application.

### Personal Context And Portable Projections

These references sharpened the distinction between storing information and
delivering the right compressed context to an agent.

| System | What we studied | What it taught us |
| --- | --- | --- |
| [Fintella Context Capsule](https://fintella.io/) | A compressed behavioral portrait derived from user activity, with inspectable evidence and user control over what reaches an AI | A useful personal layer is a projection, not a raw data dump. Context should change the answer while remaining reviewable |
| [PAMbase user memory](https://docs.pambase.io/concepts/identity) | One durable user memory with a deliberately thin profile, while each app brings its own persona | Marshmallow should keep one canonical local context layer and let harness-specific adapters remain thin |
| [Claude Code auto memory](https://code.claude.com/docs/en/memory) | Local Markdown memory, a concise `MEMORY.md` entrypoint, topic files loaded on demand, and correction-driven learning | A small always-available index plus progressive disclosure is enough to begin. Plain files improve auditability |
| [Agent Skills specification](https://agentskills.io/specification) | Portable `SKILL.md` folders, progressive disclosure, scripts, references, assets, and metadata-based discovery | Skills are a practical execution surface for compact personal projections. Marshmallow should emit compatible files rather than invent a closed format |
| [Claude Code skills](https://code.claude.com/docs/en/slash-commands) and [plugins](https://code.claude.com/docs/en/plugins) | User, project, and plugin skill locations; namespaced plugin skills; marketplace distribution | Claude Code is the first polished adapter because it already has the right skill-loading and plugin-distribution primitives |

### Adjacent Multi-Agent Operating Systems

[SuperAda](https://superada.ai/) is adjacent rather than directly comparable.
It presents a crew-style operating system that routes intent across specialized
agents and machines while maintaining system state across research, builds,
memory, and workflow operations.

The relevant lesson is long-term: as agent environments proliferate, shared
personal context becomes more valuable. The v1 plugin deliberately stops before
crew orchestration. It builds the portable alignment substrate first.

### Landscape Index

[`awesome-second-brain`](https://github.com/aristoapp/awesome-second-brain) was
useful as a current map of the category. Its lifecycle framing is particularly
helpful:

```text
collect -> organize -> evolve -> use -> govern
```

Marshmallow's first public plugin covers a narrow, testable slice of that
lifecycle:

```text
collect intentional sources
-> stage inbox candidates
-> promote a small source-backed graph
-> surface recognizable patterns conversationally
-> use it through approved skill overlays
-> govern changes through diffs, backups, and rollback
```

It does not claim to solve the entire second-brain lifecycle yet.

## Research Foundations

The product research also sits on a few durable technical ideas:

| Reference | Relevant idea | Marshmallow translation |
| --- | --- | --- |
| [Karpathy's LLM Wiki](https://gist.githubusercontent.com/karpathy/442a6bf555914893e9891c11519de94f/raw/ac46de1ad27f92b28ac95459c782c07f6b8c964a/llm-wiki.md) | Maintain a compiled wiki between raw sources and repeated queries | Compile before query. Do not re-read the entire source library for every task |
| [Retrieval-Augmented Generation](https://arxiv.org/abs/2005.11401) | Explicit non-parametric memory improves updating and provenance | Keep source-backed external memory instead of relying on model parameters or vibes |
| [Lost in the Middle](https://arxiv.org/abs/2307.03172) | Relevant context can become harder to use when buried in long prompts | Keep runtime overlays short and put the highest-signal instructions first |
| [MemGPT](https://arxiv.org/abs/2310.08560) | Memory needs tiers because not everything belongs in active context | Separate sources, graph nodes, generated graph views, and runtime overlays |
| [Reflexion](https://arxiv.org/abs/2303.11366) | Verbal feedback can improve later attempts when it persists | Preserve corrections, accepted outputs, and rejected outputs when they change future work |

These references point in the same direction: better memory is not maximal
prompt stuffing. It is selective, inspectable context compilation.

## The Product Synthesis

The first version follows thirteen decisions.

### 1. Start With Judgment-Sensitive Skills

Personalization matters most where multiple outputs can be correct and taste or
judgment determines which one is useful. Frontend direction, product planning,
architecture defaults, and writing are strong early targets.

Deterministic skills such as PDF extraction, security checklists, and strict
validation should generally remain untouched.

### 2. Ask For Made, Liked, And Rejected Sources

The three source prompts are intentionally concrete:

```text
things you made
things you like
things you reject
```

Self-authored profiles often flatten a person into slogans. Artifacts and
reactions reveal the actual quality bar. Rejections are especially useful
because they surface defaults the agent should stop repeating.

They are onboarding prompts, not permanent memory categories.

### 3. Stage Everything In The Inbox

Every source or compact insight lands under `~/.marshmallow/inbox/` before it
can change durable memory.

The host agent searches existing sources and graph nodes, reasons over the new
material, and promotes only what should improve future work. This creates a
clear boundary between incoming evidence and compiled context.

### 4. Preserve Pointers, Not Copies

Marshmallow stores a source card with the original pointer and selected excerpts
or visual description. It does not silently copy the original.

That keeps provenance clear, reduces duplication, and leaves private sources
where the user already controls them.

### 5. Let The Shape Evolve

The graph contract is deliberately small:

```text
id
insight
source_ids
applies_to
related_nodes
skills
optional labels
```

Each node needs source support. Labels are optional and corpus-shaped. Reuse
them when they improve retrieval, introduce them when the user's work needs a
new handle, and do not force a starter ontology. Weak or conflicting evidence
becomes an explicit tension or a conversational question.

### 6. Keep The Graph Rich During Learning And Small During Execution

The graph helps compile and inspect personal context. It is not the default
runtime prompt.

```text
graph during learning
projection during execution
```

Routine overlays should use only 3-7 relevant nodes. This preserves the value
of connected context without making every skill verbose or brittle.

### 7. Install One Persistent Harness Adapter

After showing a diff and receiving approval, Marshmallow adds one replaceable
import block to the user-level `~/.claude/CLAUDE.md`:

```md
<!-- marshmallow:adapter:start -->
@/Users/you/.marshmallow/runtime.md
<!-- marshmallow:adapter:end -->
```

The imported router tells Claude Code when to search compact generated
projections. It does not load the full graph, raw sources, or inbox into every
prompt.

### 8. Learn Selectively

Alignment is persistent. Learning is selective.

`/marshmallow:learn` queues explicitly approved compact insights and source
pointers as inbox candidates. Ordinary sessions are not silently ingested. Raw
session logs do not become graph nodes or runtime projections. Candidate
material remains outside runtime projections until it is deliberately promoted
into source-backed graph nodes. The adapter may ask once whether a clearly
reusable correction should be saved.

### 9. Patch Skills With Reviewable Overlay Pointers

Marshmallow preserves the useful base skill, stores an approved overlay under
`~/.marshmallow/overlays/`, and inserts one replaceable pointer block:

```md
<!-- marshmallow:alignment:start -->
## Marshmallow Alignment

Before using this skill, read `/Users/you/.marshmallow/overlays/frontend-design.md`
and apply it as the personal alignment layer.
<!-- marshmallow:alignment:end -->
```

This is intentionally less magical than generating opaque bespoke prompts. The
user can inspect the delta, understand why it exists, and keep upstream skill
content outside the block intact. The canonical instruction exists once under
`~/.marshmallow/`.

### 10. Make Every Durable Rewrite Explicit And Reversible

The deterministic scripts are conservative:

- dry-run diff first
- explicit approval before write
- timestamped backup before mutation
- atomic rewrite
- one idempotent marker block
- validation after rewrite
- exact rollback
- no silent plugin-cache edits

Trust is part of the product, not a cleanup task.

### 11. Keep V1 Markdown-Native And Standard-Library-Only

Markdown is enough to prove the loop. Python's standard library is enough for
deterministic filesystem work.

Files plus `rg` or `grep` are the retrieval layer for v1. Coding agents already
understand them, users can inspect them, and no MCP service is required.

The host agent remains responsible for interpretation: reading sources,
understanding images and PDFs, compiling graph nodes, proposing overlays, and
running the review conversation.

### 12. Ship One Claude Code Adapter Without Closing The Format

Claude Code is the first polished adapter because it has a mature user-level
instruction surface, local skills, and a distributable plugin model. Generated
aligned copies follow the open Agent Skills format so later Codex, Hermes, and
other harness adapters do not require a graph redesign.

### 13. Optimize For The First Aligned Result

The graph is a learning and compilation substrate. It should remain
inspectable, but it should not become mandatory setup work.

The first-run flow therefore asks how much detail the user wants, gathers one
loose taste pack, surfaces a few recognizable patterns, previews the persistent
adapter, and recommends useful skills. It does not require a separate graph-
approval reply before tuning.

The hard gate remains where trust matters most: before any filesystem rewrite.
See [`UX.md`](UX.md) for the interaction contract.

## Why We Deferred The Bigger System

We explicitly deferred:

- databases and graph databases
- embeddings and vector search
- MCP retrieval servers
- hosted accounts and sync
- team permissions
- dashboards
- OAuth connector layers
- ambient session ingestion and scheduled maintenance
- silent writes and automatic retuning

These are not permanently rejected. They need evidence.

The trigger for adding infrastructure is repeated pain in the smallest useful
loop: retrieval misses, slow graph inspection, unsafe manual steps, real
cross-machine demand, or team workflows that cannot be handled through local
files.

## Validation Method

The repository tests deterministic behavior:

- workspace bootstrap is idempotent
- graph validation rejects unsafe labels, missing sources, and broken links
- graph rendering is deterministic
- compact runtime projections are generated from safe graph tags
- projection rendering blocks common prompt-injection and credential-exfiltration patterns
- the Claude adapter is previewable, idempotent, removable, and backed up
- inbox candidates remain outside runtime projections until promotion
- oversized inline candidates are rejected so raw dumps stay out of the graph path
- skill scanning excludes plugin caches and deterministic skills
- overlay writes reject non-`SKILL.md` targets
- dry runs do not mutate skills
- approved rewrites create backups and exactly one pointer block
- approved skill overlays have one canonical copy under `~/.marshmallow/overlays/`
- generated overlays are checked for blocked runtime guidance before apply
- repeated tuning replaces the marker block
- rollback restores exact original bytes
- repeated tunes can be rolled back one layer at a time
- read-only targets return a documented choice flow
- aligned copies follow the Agent Skills format
- a starter user-level skill can be previewed, created, and rolled back when no
  existing skill is a good target

Before a public launch, the product test is more important than the unit suite:

1. Run five builder tasks in fresh sessions with base and tuned skills.
2. Cover product planning, architecture review, frontend direction, writing, and one mixed builder workflow.
3. Blind-review the outputs.
4. Launch only if tuned outputs win at least four of five comparisons without correctness regressions.
5. Confirm that users can explain why each tuned skill changed.
6. Confirm that onboarding reaches the first approved update without manual file editing.
7. Confirm that rollback remains reliable.
8. Confirm that quick start does not require a graph-approval reply.

## Working Rule

Every future feature should answer:

```text
Does this help an agent retrieve or apply the right personal context
for a real task without making the system harder to trust or maintain?
```

If not, defer it.
