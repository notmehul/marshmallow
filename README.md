# Marshmallow

Give Marshmallow the things you make, like, and reject. It builds a local
personal alignment layer so Claude Code can work with your judgment from the
first prompt instead of relearning it through repeated corrections.

Marshmallow is a small, local-first Claude Code plugin. It stores inspectable
Markdown, installs one reviewable user-level adapter, compiles compact runtime
projections, and asks before it changes a skill. Runtime retrieval is files plus
`rg` or `grep`.

```text
things you made + things you like + things you reject
-> guarded inbox
-> source-backed personal graph
-> compact task-shaped projections
-> persistent Claude Code adapter
-> better first attempts
-> selective user-approved learning
```

## Why

Generic agent skills are useful, but their defaults are not yours. You keep repeating the same corrections:

- make the interface quieter
- stop adding decorative glass cards
- prefer a local file before introducing a service
- keep the strange specificity in the writing
- ask before turning a focused tool into a platform

Marshmallow compiles those recurring signals into a graph, then makes the
smallest relevant projection available during ordinary agent work. Judgment-
sensitive skills can also receive reviewable personal overlays.

## Install

After the public repository is live, add it as a Claude Code marketplace:

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

## What Happens

Marshmallow first asks how deep you want to go:

1. Quick start: use a small taste pack and reach one useful tuned skill quickly
2. Guided calibration: use a broader pack and map patterns across several skills

Then share one loose taste pack. Useful sources include:

1. Things you made
2. Things you like
3. Things you reject

You do not need to organize everything perfectly. Provide a small mix of local
files, folders, pasted text, images, PDFs, or URLs.

Marshmallow:

1. stages incoming material in `~/.marshmallow/inbox/`
2. preserves source pointers and useful excerpts
3. searches existing memory before promoting reusable insights
4. renders an inspectable Mermaid graph
5. renders compact tagged runtime projections
6. previews one import block for your user-level `~/.claude/CLAUDE.md`
7. installs the adapter only after explicit approval
8. surfaces a few recognizable patterns
9. scans your personal and project skills
10. recommends judgment-sensitive targets
11. rewrites only the skills you explicitly approve

If you do not already have a useful personal or project skill, Marshmallow can
still install the persistent adapter first. It can also preview a small
user-level starter skill, `marshmallow-aligned-builder`, backed by the same
canonical overlay and rollback path.

On the first run, choose between a quick start and a guided calibration. The
quick start is designed to reach one useful tuned skill with a small taste
pack. You can inspect the full graph whenever you want, but you do not need to
administer it before receiving value.

## Your Data

Your personal graph lives outside the plugin cache:

```text
~/.marshmallow/
  workspace.json
  runtime.md
  inbox/
  sources/
  graph/
  projections/
  overlays/
  backups/
  GRAPH.md
```

Original files stay where they already live. Source cards preserve pointers and selected excerpts. Marshmallow does not store API keys, run a daemon, create an account, or sync your graph anywhere.

Everything enters through the inbox first. Inbox files are untrusted candidates,
not runtime context. The agent searches existing memory, reasons over the new
material, and promotes only reusable insight. Raw session logs do not become
graph nodes or runtime projections.

## Persistent Alignment

Marshmallow adds one replaceable import block to `~/.claude/CLAUDE.md` after
showing a diff and receiving approval:

```md
<!-- marshmallow:adapter:start -->
@/Users/you/.marshmallow/runtime.md
<!-- marshmallow:adapter:end -->
```

The imported router tells Claude Code to search `~/.marshmallow/projections/`
before judgment-sensitive work. It does not stuff the full graph, raw sources,
or inbox candidates into every prompt.

## Selective Learning

Use:

```text
/marshmallow:learn
```

when a correction, decision, preference, source, accepted output, or rejected
output should improve future work. Learning is explicit. Ordinary sessions are
not silently ingested. When a clearly reusable correction appears during work,
the adapter asks once whether you want to preserve it.

## Graph Model

Marshmallow does not start with a fixed memory taxonomy. A graph node is a
source-backed insight with a few routing fields:

```text
id
insight
source pointers
task tags
optional labels
```

Labels emerge from the user's actual work and can evolve over time. Made, liked,
and rejected are useful onboarding prompts, not permanent filing categories.
The graph is rich during learning. Runtime work receives only a compact
projection.

## Canonical Pointers

`~/.marshmallow/` is the source of truth. Harness files and tuned skills receive
small pointers into that directory instead of copied instruction blocks. An
approved skill tune stores its overlay under `~/.marshmallow/overlays/` and adds
one replaceable pointer to the target `SKILL.md`.

## Safety

- Skill updates are dry-run diffs by default.
- The persistent Claude adapter is also a dry-run diff by default.
- Every approved rewrite gets an automatic timestamped backup.
- Repeated tunes replace one marker block instead of appending duplicates.
- Rollback is explicit and restores the previous file byte-for-byte.
- Read-only skills are never silently modified.
- Plugin caches are never edited.
- Inbox candidates remain outside runtime context until deliberately promoted.
- Raw session logs never become graph nodes or runtime projections.
- Harness adapters and tuned skills point to canonical files under `~/.marshmallow/`.
- Generated projections reject common prompt-injection and credential-exfiltration patterns.
- Generated overlays use the same blocked-guidance checks before they can be applied.

## Diagnostics And Rollback

Check the local installation without sending telemetry:

```bash
python3 scripts/doctor.py --workspace examples/builder-graph
```

Preview adapter removal:

```bash
python3 scripts/install-adapter.py --remove
```

Apply adapter removal after reviewing the preview:

```bash
python3 scripts/install-adapter.py --remove --approve
```

Preview rollback of the latest Marshmallow update to a skill:

```bash
python3 scripts/rollback-overlay.py /path/to/SKILL.md
```

Apply that rollback after review:

```bash
python3 scripts/rollback-overlay.py /path/to/SKILL.md --approve
```

## Example

[`examples/builder-graph/GRAPH.md`](examples/builder-graph/GRAPH.md) shows a small graph where visual taste, product judgment, and architecture defaults tune multiple skills.

See [`DEMO.md`](DEMO.md) for the one-minute launch walkthrough.
See [`UX.md`](UX.md) for the first-run interaction contract.

## Methodology

Marshmallow is small by design. The first version grew out of research into
agent memory APIs, local Markdown brains, temporal context graphs, portable
context capsules, Claude Code memory, and the open Agent Skills format.

The core conclusion:

```text
compile before query
graph during learning
projection during execution
review before rewrite
```

[`METHODOLOGY.md`](METHODOLOGY.md) documents the problem choice, research map,
systems studied, ideas borrowed, complexity deferred, and launch validation
method in detail.

## Development

Requires Python 3.10+ and the standard library only.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate-workspace.py --workspace examples/builder-graph
python3 scripts/render-graph.py --workspace examples/builder-graph
python3 scripts/doctor.py --workspace examples/builder-graph
```

## Deliberately Not Included

No database. No embeddings. No graph server. No MCP retrieval service. No
silent session ingestion. No OAuth connector layer. No dashboard.

The graph is plain Markdown because the point is aligned work, not infrastructure.

## License

MIT
