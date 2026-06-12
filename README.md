<div align="center">

<img src="assets/marshy-hero.png" alt="Marshmallow: sources to runtime context to skill overlays, with Marshy the mascot" width="900">

# Marshmallow

### Make your agent skills less generic.

**Open-source alignment for AI agent skills.** Marshmallow turns the things you
explicitly provide — docs, examples, corrections, preferences, and project rules
— into plain-file context and overlays that tune the skills your agents already
use.

[![tests](https://github.com/notmehul/marshmallow/actions/workflows/test.yml/badge.svg)](https://github.com/notmehul/marshmallow/actions/workflows/test.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![works with: Claude Code · Codex · Cursor](https://img.shields.io/badge/works%20with-Claude%20Code%20·%20Codex%20·%20Cursor-blue.svg)](#supported-harnesses)

</div>

---

## Why this exists

Agent skills are powerful, but they are generic by default.

A design skill knows how to produce a layout. A code review skill knows how to
look for risk. A writing skill knows how to shape a draft.

What they do not know is *your* version of good: the defaults you keep rejecting,
the taste you are trying to preserve, the project rules that matter here, and the
corrections you have already made three times.

Marshmallow makes those skill-level corrections reusable without turning them
into a black box.

It keeps a small, source-backed graph of the things you explicitly ask it to
learn, then uses that graph to tune runtime context and skill overlays.

> **Marshy** is the mascot. Marshmallow is the system.
> Cute face, boringly inspectable files underneath.

## The idea

```text
sources -> graph nodes -> runtime.md -> adapter -> skill overlays -> aligned skills
```

- **Sources** are things you chose: files, notes, examples, rejected outputs,
  corrections, screenshots, PDFs, or URLs.
- **Graph nodes** are compact rules with provenance: what the source teaches,
  where it applies, and which skills it should affect.
- **`runtime.md`** tells the agent how to search the graph and load only what
  matters now.
- **Adapters** connect that runtime file to `CLAUDE.md` or `AGENTS.md`.
- **Skill overlays** tune existing agent skills without replacing their base
  procedure. The skill still knows its craft; the overlay carries your judgment.

The goal is not to make a giant memory layer. The goal is to make useful skills
behave less like generic imports and more like tools shaped by your standards.

## Trust model

Marshmallow is deliberately boring where trust matters.

- **Local-first.** It writes plain files under `~/.marshmallow/`.
- **Explicit learning.** No background capture. No silent session ingestion.
- **Source-backed guidance.** Graph nodes point back to real sources or approved
  corrections.
- **Preview before mutation.** Adapter installs and skill rewrites show you what
  will change.
- **Rollback.** Applied mutations create byte-exact backups and rollback records.

No hosted profile. No dashboard. No database. No memory daemon.

## Quickstart

### Claude Code

```text
/plugin marketplace add notmehul/marshmallow
/plugin install marshmallow
```

> Prefer the CLI? `claude plugin marketplace add notmehul/marshmallow && claude plugin install marshmallow`

Then start the calibration:

```text
/marshmallow:start
```

Marshy asks for a small taste pack: things you made, liked, rejected, or
corrected. Marshmallow turns that bundle into the first source-backed graph,
previews the runtime adapter, and proposes the first useful skill overlay.

Nothing durable is written without your explicit approval.

Later, teach it more with `/marshmallow:learn` and retune skills with
`/marshmallow:tune`.

### Codex & Cursor

Marshmallow's graph and overlays are plain files. Codex and Cursor can read the
same context through an `AGENTS.md` adapter:

```bash
scripts/marshmallow.py adapter apply --harness codex   # ~/.codex/AGENTS.md
scripts/marshmallow.py adapter apply --harness cursor  # ./AGENTS.md
```

## What it creates

`~/.marshmallow/` is the source of truth — plain files, no database:

```text
runtime.md    # short instructions imported by CLAUDE.md / AGENTS.md
inbox/        # unsynthesized candidate material (untrusted until promoted)
sources/      # source cards with pointers and provenance
graph/        # source-backed graph nodes (the durable substrate)
overlays/     # approved skill alignment overlays
backups/      # exact backup bytes plus record.json for rollback
```

## Skills

- **`/marshmallow:start`** — onboard the workspace, build the first graph,
  install the runtime adapter, create the first tune.
- **`/marshmallow:learn`** — ingest explicit sources or corrections.
- **`/marshmallow:tune`** — retune skills with overlays, create aligned copies or
  starter skills, and roll overlays back.

## CLI

The skills call one public CLI. You can run it directly too:

```bash
scripts/marshmallow.py init
scripts/marshmallow.py doctor
scripts/marshmallow.py scan-skills
scripts/marshmallow.py adapter preview   [--harness claude|codex|cursor]
scripts/marshmallow.py adapter apply     [--harness claude|codex|cursor]
scripts/marshmallow.py adapter remove [--approve]
scripts/marshmallow.py overlay preview  --skill <SKILL.md> --overlay <overlay.md>
scripts/marshmallow.py overlay apply    --skill <SKILL.md> --overlay <overlay.md>
scripts/marshmallow.py overlay rollback --skill <SKILL.md> [--approve]
scripts/marshmallow.py starter preview  --overlay <overlay.md>
scripts/marshmallow.py starter apply    --overlay <overlay.md>
```

Preview before mutation. Adapter installs and skill rewrites require explicit
approval. Rollback metadata lives beside each backup in `backups/`.

## Graph shape

Graph node minimum schema:

```yaml
id: prefer-clear-hierarchy
insight: Prefer clear hierarchy over decorative complexity.
source_ids: [source-example]
applies_to: [design]
related_nodes: []
skills: [frontend-design]
labels: [visual-taste]
```

Graph nodes should stay compact and behavior-changing. Use the body to explain
the rule, evidence, skills affected, limits, and any real `[[wikilink]]`
connections. `doctor --json` may report quality warnings for generic or thin
nodes; warnings do not break existing workspaces.

Source card minimum schema:

```yaml
id: source-example
pointer: /absolute/path/or/url
captured: 2026-06-01T00:00:00Z
summary: Optional reason this source matters.
labels: [product]
```

Every graph node must have at least one `source_ids` entry. User corrections are
saved as source cards, so corrections stay source-backed too.

## Supported harnesses

| Harness | Adapter target | Style |
| --- | --- | --- |
| Claude Code | `~/.claude/CLAUDE.md` | native `@import` |
| Codex | `~/.codex/AGENTS.md` | pointer block |
| Cursor | `./AGENTS.md` | pointer block |

The full onboarding skills are built for Claude Code today. Codex and Cursor read
the same graph through the `AGENTS.md` adapter; deeper native flows for them are
on the roadmap.

## Try the demo

The bundled demo workspace is reproducible and touches nothing real:

```bash
scripts/marshmallow.py doctor --workspace examples/builder-graph
```

See [DEMO.md](DEMO.md) for the full walkthrough.

## Checks

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q scripts tests
claude plugin validate . --strict
```

Requires **Python 3.11+** (uses `datetime.UTC` and modern typing).

## Learn more

- [ARCHITECTURE.md](ARCHITECTURE.md) — the runtime loop and design boundaries
- [METHODOLOGY.md](METHODOLOGY.md) — what we borrowed, what we deliberately didn't
- [docs/trust-and-rollback.md](docs/trust-and-rollback.md) — the trust model
- [UX.md](UX.md) — what good onboarding should feel like
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to help

## Contributing

Marshmallow is built for builders — try it, remix it, make it yours. Issues and
PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE).
