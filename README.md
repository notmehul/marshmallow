# Marshmallow

No-bullshit AI personalization for Claude Code.

Marshmallow turns the things you make, like, and reject into a local skill graph
and knowledge graph. Claude Code can then use your taste, judgment, and working
style from the first prompt instead of relearning them through repeated
corrections.

```text
your work + references + rejections
-> guarded inbox
-> source-backed graph
-> compact runtime projections
-> Claude Code adapter
-> better first attempts
```

No database. No account. No daemon. No silent memory. Just inspectable Markdown,
`rg`/`grep`, reviewable diffs, backups, and rollback.

## Why

Generic agents keep making the same wrong calls:

- adding infrastructure before a local file has failed
- making interfaces busier than you like
- sanding away your writing voice
- expanding a focused wedge into a platform
- forgetting decisions you already explained three sessions ago

Marshmallow compiles those recurring signals into small, task-shaped context
files. Ordinary Claude Code sessions get a persistent adapter. Judgment-sensitive
skills can also get personal overlays that patch their defaults without copying
giant prompts into every skill.

## Install

After the public repository is live:

```text
/plugin marketplace add <github-owner>/marshmallow-plugin
/plugin install marshmallow@marshmallow
/reload-plugins
```

For local development:

```bash
claude --plugin-dir /absolute/path/to/marshmallow-plugin
```

Then run:

```text
/marshmallow:start
```

## Quick Start

Marshmallow asks how deep you want to go:

1. Quick start: 3-7 sources and one useful aligned result.
2. Guided calibration: a broader pass across several skills.

Send a loose taste pack:

- things you made
- things you like
- things you reject

Paths, folders, pasted text, screenshots, PDFs, and URLs all work. You do not
need to organize them perfectly.

Marshmallow stages the material, extracts reusable insights, renders compact
projections, previews a `~/.claude/CLAUDE.md` adapter, and asks before changing
anything durable.

If you have no existing skills, activation still works: the adapter routes
ordinary Claude Code sessions into your projections. Marshmallow can also
preview a starter skill called `marshmallow-aligned-builder`.

## What It Writes

`~/.marshmallow/` is the source of truth. Durable personal data lives outside
the plugin cache:

```text
~/.marshmallow/
  inbox/          # untrusted candidates
  sources/        # source cards and pointers
  graph/          # source-backed insights
  projections/    # compact runtime context
  overlays/       # approved skill overlays
  backups/        # rollback material
  runtime.md      # Claude Code router
  GRAPH.md        # inspectable graph view
```

After approval, Claude Code gets one replaceable import block:

```md
<!-- marshmallow:adapter:start -->
@/Users/you/.marshmallow/runtime.md
<!-- marshmallow:adapter:end -->
```

Tuned skills get one pointer to an approved overlay under `~/.marshmallow/`.
They do not receive copied graph dumps.

## Trust Model

- Dry-run diffs before adapter or skill rewrites.
- Explicit approval before every durable write.
- Timestamped backups and byte-for-byte rollback.
- Inbox material stays out of runtime until promoted.
- Raw session logs are not silently ingested.
- Generated projections and overlays block common prompt-injection patterns.
- Plugin caches are never edited.

Run a local health check:

```bash
python3 scripts/doctor.py --workspace examples/builder-graph
```

See [docs/trust-and-rollback.md](docs/trust-and-rollback.md) for rollback and
uninstall commands.

## Example

The example graph turns taste and builder judgment into runtime guidance:

- prefer inspectable local primitives before adding infrastructure
- avoid decorative glass cards without hierarchy
- prefer calm helper-like interfaces over control panels

Open [examples/builder-graph/GRAPH.md](examples/builder-graph/GRAPH.md) or run:

```bash
python3 scripts/render-graph.py --workspace examples/builder-graph
```

## Learn More

- [docs/usage.md](docs/usage.md): onboarding, learning, and no-skills fallback.
- [ARCHITECTURE.md](ARCHITECTURE.md): file layout and ownership boundaries.
- [UX.md](UX.md): first-run interaction contract.
- [METHODOLOGY.md](METHODOLOGY.md): research trail and validation method.
- [DEMO.md](DEMO.md): one-minute launch walkthrough.

## Development

Requires Python 3.10+ and the standard library only.

```bash
python3 -m unittest discover -s tests -v
claude plugin validate . --strict
python3 scripts/validate-workspace.py --workspace examples/builder-graph
python3 scripts/render-graph.py --workspace examples/builder-graph
```

## License

MIT
