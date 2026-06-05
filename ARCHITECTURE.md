# Architecture

Marshmallow is deliberately small. Claude Code does the interpretation. Python scripts handle deterministic filesystem work.

```text
user sources + explicitly approved insights
-> ~/.marshmallow/inbox/*.md
-> host-agent search, reading, and synthesis
-> ~/.marshmallow/sources/*.md
-> ~/.marshmallow/graph/*.md
-> ~/.marshmallow/GRAPH.md
-> ~/.marshmallow/projections/*.md
-> ~/.marshmallow/runtime.md
-> ~/.claude/CLAUDE.md import block
-> better context during ordinary Claude Code sessions
```

Judgment-sensitive skills remain an additional downstream surface:

```text
relevant graph nodes
-> reviewable pending overlay
-> approved ~/.marshmallow/overlays/*.md
-> approved SKILL.md pointer block
```

## Boundaries

- `skills/start/SKILL.md` owns the guided conversation and approval gates.
- `skills/learn/SKILL.md` owns inbox-first selective learning after onboarding.
- `scripts/` owns workspace initialization, skill discovery, validation, rendering, safe apply, and rollback.
- `~/.marshmallow/` owns durable personal graph data outside plugin caches.
- `~/.claude/CLAUDE.md` owns one replaceable import block after explicit approval.
- Existing Claude skills remain authoritative outside one replaceable
  Marshmallow pointer block.

The graph stays inspectable, but it is not a mandatory approval screen. The
first-run experience surfaces recognizable patterns and relevant skills, then
reserves explicit approval for filesystem rewrites. See [`UX.md`](UX.md).

## Why Markdown And Grep

The graph is a learning and compilation substrate, not a runtime database. Markdown keeps provenance inspectable and lets future harnesses reuse the same files without adopting a service.

During normal work, the imported router tells Claude Code to search compact
tagged projections with `rg` or `grep`. It never loads the whole graph by
default:

```text
global adapter + smallest relevant projection + task = aligned run
```

Tuned skills receive an additional compact approved overlay:

```text
base skill + personal projection + task = aligned run
```

## Learning Boundary

Alignment is persistent. Learning is selective.

Ordinary sessions are not silently captured. Every source or compact insight
lands under `~/.marshmallow/inbox/` first. Inbox files remain untrusted
candidates until the host agent searches existing memory, reasons over the
candidate, promotes source cards where provenance matters, extracts only
reusable insight into graph nodes, and re-renders projections. Raw session logs
do not become graph nodes or runtime projections. The runtime adapter may ask
once whether a clearly reusable correction should be preserved; it does not
silently save it.

## Evolving Shape

Graph nodes have a small stable contract: ID, insight, source pointers, runtime
tags, links, and optional labels. There is no fixed memory taxonomy. Labels
emerge when they improve retrieval and evolve with the user's work.

## Pointer Rule

`~/.marshmallow/` is canonical. The Claude adapter imports `runtime.md`. Tuned
skills contain a pointer to an approved overlay under `overlays/`. Future
harness adapters should point to the same canonical files instead of copying
instructions into harness-specific stores.

Projection rendering rejects common prompt-injection and credential-
exfiltration patterns before runtime files are rewritten.

## Deferred

Do not add a database, vector search, graph server, daemon, MCP service,
dashboard, account system, sync layer, OAuth flow, or silent session ingestion
until real usage proves the need.
