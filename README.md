<!-- Hero art: drop assets/marshy-hero.png here once committed. See assets/README.md. -->
<div align="center">

# 🐱 Marshmallow

### Make your AI agents less generic.

**Local-first personalization for AI coding agents.** Your taste, your rules,
your context — captured into the skills your agent already uses as plain files,
nothing hidden.

[![tests](https://github.com/notmehul/marshmallow/actions/workflows/test.yml/badge.svg)](https://github.com/notmehul/marshmallow/actions/workflows/test.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![works with: Claude Code · Codex · Cursor](https://img.shields.io/badge/works%20with-Claude%20Code%20·%20Codex%20·%20Cursor-blue.svg)](#supported-harnesses)

</div>

---

## Your agent keeps forgetting

Taste. Rules. Context. Constraints. Every new session, a competent stranger
shows up — knows the language, knows nothing about *you*. You re-explain the same
preferences, paste the same references, correct the same defaults.

Marshmallow gives your agent a small, inspectable memory of what makes your work
*yours*, and feeds only the relevant piece into each task.

> Meet **Marshy** — the mascot. Cute on the outside, boringly robust underneath.
> We took the Go gopher approach: a friendly face on a system you can trust with
> your `CLAUDE.md`.

## How it works

```text
sources  ->  graph nodes  ->  runtime adapter  ->  skill overlays  ->  better output
 your        small,            one import in        your skills,         answers that
 notes,      source-backed     CLAUDE.md /          tuned to your        sound like you,
 docs,       insights          AGENTS.md            judgment             not everyone
 likes…
```

- **Sources become context.** Point Marshmallow at things you made, liked,
  rejected, or corrected. It distills them into small graph nodes — each one
  backed by a real source you can trace.
- **Context stays small.** A runtime adapter tells your agent to load only the
  handful of nodes relevant to the task, not your whole history.
- **Skills get tuned, not replaced.** Marshmallow adds a reviewable overlay to
  the skills you already use. The base skill keeps its procedure; the overlay
  carries your judgment.
- **Models synthesize, Python is deterministic.** The model does the
  understanding. Python handles file mutation, previews, backups, and byte-exact
  rollback — the parts that must be predictable.

## No silent memory tricks

Marshmallow is **local-first** and **honest** by design:

- 🔒 **Local-first.** Marshmallow writes plain files under `~/.marshmallow/` and
  does not upload, sync, or run a background service.
- ❌ **No log hoarding.** No background capture, no silent learning. Marshmallow
  remembers only what you explicitly ask it to.
- ↩️ **Rollback.** Every change is previewed before it's applied, backed up
  byte-for-byte, and reversible.

## Quickstart

### 1. Install the plugin (Claude Code)

```text
/plugin marketplace add notmehul/marshmallow
/plugin install marshmallow
```

> Prefer the CLI? `claude plugin marketplace add notmehul/marshmallow && claude plugin install marshmallow`

### 2. Let Marshy interview you

```text
/marshmallow:start
```

Marshy asks for a few things that feel like *you* — files you made, references
you love, a default you keep correcting — and runs a short calibration:

1. Pick a depth (quick start is one taste pack → one tuned skill).
2. Share a loose bundle: local files, pasted text, screenshots, PDFs, URLs.
3. Marshy reveals the patterns it found, in plain language.
4. You approve a persistent adapter and the first skill tune. Nothing is written
   without your explicit yes.

That's the whole loop. Later, teach it more with `/marshmallow:learn` and retune
skills with `/marshmallow:tune`.

### Codex & Cursor

Marshmallow's graph and overlays are plain files, so other harnesses can use them
too. Install the adapter into `AGENTS.md` instead of `CLAUDE.md`:

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
