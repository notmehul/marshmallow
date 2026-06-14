# Source-Backed Recall Beta Plan

**Status:** Beta implementation plan  
**Date:** 2026-06-14  

## Product Direction

Marshmallow should ship as a plugin-led context runtime, not as a memory
platform, automation tool, or dashboard.

The beta promise:

```text
Marshmallow gives agents source-backed recall for the people, projects,
decisions, and working rules that matter now.
```

Connected agents and external systems may take downstream actions. Marshmallow
only supplies the right context; it does not queue, post, update, or automate.

## Core Model

```text
sources -> typed graph nodes -> indexes/recall packets -> runtime adapter -> agent
```

Use the current plain-file workspace:

- `sources/` stores evidence pointers.
- `graph/` stores durable records.
- `indexes/` stores compact navigation pages.
- `projections/` stores task-shaped recall packets.
- `overlays/` remains optional for skill tuning.

No new database, daemon, background capture, dashboard, MCP surface, or entity
folders are part of this beta.

## Typed Graph Nodes

Reuse graph nodes with existing optional fields:

```yaml
type: entity
subjects: [mehul]
status: active
updated: 2026-06-14
```

Beta node types:

- `entity`: a person, company, project, audience, agent, or workflow.
- `decision`: what was chosen, why, tradeoffs, and when to revisit.
- `relationship`: the useful dynamic between two or more entities.
- `preference`: a reusable working rule, taste, format, or standard.

Only promote information that changes future behavior. Interesting but unused
details stay in `inbox/` or `sources/`.

## Recall Packets

`projections/` should be described publicly as recall packets: short,
task-shaped files an agent can load before work.

A good recall packet answers:

- What task is this for?
- Which entity, decision, relationship, or preference nodes matter?
- What rules, open loops, and source trails should the agent preserve?

The agent harness synthesizes and acts. Marshmallow points to the files.

## Minimal CLI

Add:

```bash
scripts/marshmallow.py recall "<query>" [--json] [--limit N]
```

The command is read-only. It searches only `indexes/`, `projections/`, and
`graph/`. It never searches `sources/` or `inbox/` by default. It returns
matching paths, ids, kinds, titles/insights/tasks, types, subjects, scores, and
snippets.

The CLI does not generate, edit, or synthesize recall packets.

## Beta Demo

Add one fictional operator/founder workspace that proves the new loop:

```text
Prepare an investor update and explain why we are not raising this month.
```

The demo should include:

- one founder entity
- one investor entity
- one company/project entity
- one decision node
- one relationship node
- one index
- one recall packet

The walkthrough should lead with `doctor` and `recall`, then mention skill
overlays as optional downstream tuning.

## Public Copy

Update public docs to lead with source-backed recall and context runtime. Keep
the trust model unchanged:

- local files
- explicit learning
- source-backed records
- preview before mutation
- rollback
- no silent capture

Skill overlays remain useful, but they are no longer the only activation path.

## Acceptance Criteria

- `recall` finds matching index, recall-packet, and graph records.
- `recall` supports plain text and JSON output.
- `recall` respects `--limit`.
- `recall` returns an empty result successfully when nothing matches.
- `recall` does not search `sources/` or `inbox/`.
- `entity`, `decision`, and `relationship` nodes without `skills` do not get
  the old skill-specific warning.
- Existing validation, adapter, overlay, and rollback behavior still passes.
