# Architecture

Marshmallow is a local file-based personalization layer. It is not a database,
memory daemon, graph server, or compiler.

## Runtime Loop

```text
sources/ -> graph/ -> runtime.md -> CLAUDE.md/AGENTS.md adapter -> skill overlays
```

The graph is the durable personalization substrate. The runtime adapter is a
small marker block that imports or points at `~/.marshmallow/runtime.md`:

- **Claude Code** uses a native `@import` in `~/.claude/CLAUDE.md`.
- **Codex and Cursor** use a short pointer block in `AGENTS.md` (Codex reads
  `~/.codex/AGENTS.md`; Cursor reads the project `./AGENTS.md`), since `AGENTS.md`
  has no import directive.

The runtime file tells the agent to search `~/.marshmallow/graph/` with `rg` or
`grep` and load only the smallest relevant graph nodes for the current task.

## Plugin Command Boundary

Claude Code skills call the single executable CLI at
`${CLAUDE_PLUGIN_ROOT}/scripts/marshmallow.py`. The skill frontmatter allowlists
that exact Bash prefix, plus `rg` and the file tools needed to stage user
approved material.

Do not route plugin skills through `python3 ${CLAUDE_PLUGIN_ROOT}/...` or broad
`Bash(python3:*)` permissions. Direct executable calls keep the harness
permission surface narrow and avoid auto-mode treating the workflow as arbitrary
third-party Python.

## Workspace

`~/.marshmallow/` contains plain files:

- `runtime.md`: concise routing guidance
- `inbox/`: unsynthesized candidates
- `sources/`: source cards with pointers
- `graph/`: source-backed personalization nodes
- `overlays/`: approved skill overlay files
- `backups/`: exact backup bytes plus `record.json`

There is no central state file. Tools discover state from the filesystem.

## Graph

Every graph node must include:

- `id`
- `insight`
- non-empty `source_ids`

Optional fields are `applies_to`, `related_nodes`, `skills`, and `labels`.
Labels are retrieval hints, not a fixed taxonomy.

Source cards must include `id`, `pointer`, and `captured`. A user correction can
become a source card named `user-correction-YYYYMMDD...`, which keeps future
guidance source-backed without pretending the correction came from an external
document.

## Skills

Base skills stay intact. Marshmallow inserts one marker block that points to an
overlay file in `~/.marshmallow/overlays/`. The overlay carries the personal
alignment layer; the base skill keeps its domain procedure.

Skills contain a pointer, not the whole graph. This keeps runtime context small
and makes rollback simple.

## Trust And Rollback

Mutating commands follow a preview/apply shape. Adapter changes and skill
rewrites require explicit approval. Each applied mutation writes a backup and a
`record.json` beside that backup. Rollback restores exact bytes from the backup
and restores or removes the overlay store according to the record.

Plugin-cache skills are not edited in place.

## Deliberate Non-Goals

Marshmallow avoids:

- generated projections
- mandatory graph render files
- background capture
- hidden learning or hallucination-backed guidance
- cron jobs
- dashboards
- databases and temporal graph infrastructure
- broad MCP/tool integration layers
