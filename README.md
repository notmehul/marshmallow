# Marshmallow

Marshmallow is a small local personalization layer for Claude Code.

The loop is intentionally plain:

```text
context sources -> source-backed graph nodes -> Claude runtime adapter -> skill overlays -> explicit learning updates
```

Models do the synthesis work. Python handles the parts that should be
deterministic: creating files, previewing diffs, installing/removing the runtime
adapter, applying overlays, and rolling back exact bytes from backups.

## What It Creates

`~/.marshmallow/` is the source of truth:

```text
runtime.md    # short instructions imported by ~/.claude/CLAUDE.md
inbox/        # unsynthesized candidate material
sources/      # source cards with pointers/provenance
graph/        # source-backed graph nodes
overlays/     # approved skill alignment overlays
backups/      # backup files plus record.json metadata
```

There is no required `workspace.json`, generated `GRAPH.md`, or generated
`projections/` directory.

## CLI

Use one public command:

```bash
python3 scripts/marshmallow.py init
python3 scripts/marshmallow.py doctor
python3 scripts/marshmallow.py scan-skills
python3 scripts/marshmallow.py adapter preview
python3 scripts/marshmallow.py adapter apply
python3 scripts/marshmallow.py adapter remove
python3 scripts/marshmallow.py adapter remove --approve
python3 scripts/marshmallow.py overlay preview --skill /path/to/SKILL.md --overlay /path/to/overlay.md
python3 scripts/marshmallow.py overlay apply --skill /path/to/SKILL.md --overlay /path/to/overlay.md
python3 scripts/marshmallow.py overlay rollback --skill /path/to/SKILL.md
python3 scripts/marshmallow.py overlay rollback --skill /path/to/SKILL.md --approve
python3 scripts/marshmallow.py starter preview --overlay /path/to/overlay.md
python3 scripts/marshmallow.py starter apply --overlay /path/to/overlay.md
```

Preview before mutation. Adapter installs and skill rewrites require explicit
user approval. Rollback metadata lives beside each backup in `backups/`.

## Skills

- `/marshmallow:start` onboards the workspace, first graph, adapter, and first tune.
- `/marshmallow:learn` ingests explicit sources or corrections.
- `/marshmallow:tune` retunes skills, creates aligned copies, creates starter skills, and rolls back overlays.

## Graph Shape

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

Source card minimum schema:

```yaml
id: source-example
pointer: /absolute/path/or/url
captured: 2026-06-01T00:00:00Z
summary: Optional reason this source matters.
labels: [product]
```

Every graph node must have at least one `source_ids` entry. User corrections are saved
as source cards, so corrections remain source-backed too.

## Demo

The bundled demo is reproducible:

```bash
python3 scripts/marshmallow.py doctor --workspace examples/builder-graph
python3 scripts/marshmallow.py overlay preview \
  --workspace examples/builder-graph \
  --skill /path/to/frontend-design/SKILL.md \
  --overlay examples/builder-graph/overlays/frontend-design.md
```

See [DEMO.md](DEMO.md), [ARCHITECTURE.md](ARCHITECTURE.md), and
[docs/trust-and-rollback.md](docs/trust-and-rollback.md).

## Checks

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q scripts tests
claude plugin validate . --strict
```
