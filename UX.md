# UX

Marshmallow should feel like a short context calibration, not a memory-system
migration.

## Product Promise

Give Marshmallow a few things that reveal people, projects, decisions, formats,
corrections, judgment, and working style. It turns them into source-backed graph
nodes, makes those nodes available through a short runtime adapter, and gives
agents compact recall before work. Skill overlays are optional.

## First-Run Budget

| Step | User burden |
| --- | --- |
| Choose depth | 1 reply |
| Share context pack | 1 loose bundle |
| Mandatory graph approval | 0 user replies |
| Adapter apply | explicit approval |
| Skill rewrite, if used | explicit approval |

The persistent adapter plus first useful recall result is the activation. The
graph is inspectable, but it is not a mandatory checkpoint before doing useful
work.

## Good Onboarding

- Ask for a small context pack, not a taxonomy.
- Use "person, project, decision, format, rejected output, correction" as examples.
- Ask what to learn before inferring from vague or low-signal folders.
- Promote 3-7 compact behavior-changing nodes, not exhaustive coverage.
- Surface 3-5 patterns in ordinary language.
- Create a recall packet when a meeting, handoff, workflow, or agent task needs
  reusable context.
- Recommend only skills where personal judgment changes the output.
- Offer a starter skill when no useful existing skill is writable.

## Runtime Feel

Ordinary work should not feel like opening a second app. The agent runs
`recall`, checks `~/.marshmallow/indexes/`, loads the smallest relevant graph
nodes or recall packets, and uses them only when they materially change the
task.

## Trust Cues

- Preview before mutation.
- Backups are visible under `~/.marshmallow/backups/`.
- Rollback restores exact bytes.
- Learning is explicit.
- Plugin-cache files are not edited in place.
