# UX

Marshmallow should feel like a short calibration conversation, not a memory
system migration.

## Product Promise

Give Marshmallow a few things that reveal taste, judgment, and working style.
It turns them into source-backed graph nodes, makes those nodes available to
Claude through a short runtime adapter, and tunes selected skills with
reviewable overlays.

## First-Run Budget

| Step | User burden |
| --- | --- |
| Choose depth | 1 reply |
| Share taste pack | 1 loose bundle |
| Mandatory graph approval | 0 user replies |
| Adapter apply | explicit approval |
| Skill rewrite | explicit approval |

The persistent adapter plus first successful aligned result is the activation.
The graph is inspectable, but it is not a mandatory checkpoint before tuning.

## Good Onboarding

- Ask for a small taste pack, not a taxonomy.
- Use "made, liked, rejected, corrected" as examples.
- Surface 3-5 patterns in ordinary language.
- Recommend only skills where personal judgment changes the output.
- Offer a starter skill when no useful existing skill is writable.

## Runtime Feel

Ordinary work should not feel like opening a second app. Claude searches
`~/.marshmallow/graph/`, loads the smallest relevant graph nodes, and uses them
only when they materially change the task.

## Trust Cues

- Preview before mutation.
- Backups are visible under `~/.marshmallow/backups/`.
- Rollback restores exact bytes.
- Learning is explicit.
- Plugin-cache files are not edited in place.
