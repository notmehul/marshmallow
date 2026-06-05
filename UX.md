# User Experience

Marshmallow should feel like a power tool for personal alignment, not a setup
wizard for a knowledge system.

The user-facing promise is simple:

> Give Marshmallow a few things that feel like you. It gives Claude Code the
> right personal context from the first prompt and tunes skills where your
> judgment should change their defaults.

The graph remains inspectable, but it is a means to better work. The first-run
experience should optimize for the first useful aligned skill.

## Product Goals

The onboarding flow serves two goals:

1. Ship a packaged value proposition: align a Claude Code setup to the user's
   actual taste and judgment.
2. Stay beautifully simple in a category full of systems that ask users to
   manage infrastructure before receiving value.

The user should leave the first run thinking:

```text
It understood how I like to work.
It knew where that should change my setup.
It showed me the exact change before touching anything.
The same graph can improve more skills later.
```

## Aha Ladder

The flow should deliver four moments in order:

1. Recognition: the surfaced patterns feel specific and true.
2. Utility: those patterns become available in ordinary Claude Code sessions.
3. Trust: the adapter and skill updates are compact, inspectable, and reversible.
4. Expansion: explicit corrections and sources improve future projections.

Do not lead with graph administration. Let the user feel recognition before
explaining the machinery.

## Calibration Depth

Start by asking the user how much detail they want.

### Quick Start

Recommend this by default.

Use 3-7 sources, surface 3-5 patterns, and aim to tune one high-leverage skill.
This is the Product Hunt path and the fastest route to the aha moment.

### Guided Calibration

Use this when the user wants a deeper pass.

Accept a broader source pack, surface more patterns, and recommend several
skills. Keep the same interaction shape. A deeper pass is more thorough, not a
different product with more ceremony.

## First-Run Flow

```text
/marshmallow:start
-> choose quick start or guided calibration
-> share one loose taste pack
-> Marshmallow stages inbox candidates
-> Marshmallow searches existing memory and promotes reusable insight
-> Marshmallow renders compact runtime projections
-> Marshmallow surfaces emerging patterns and relevant skills
-> Marshmallow previews the persistent Claude Code adapter
-> user chooses skills to edit
-> Marshmallow shows compact adapter and overlay diffs
-> user explicitly approves named rewrites
-> Marshmallow applies backups and updates
```

The opening prompt should be light:

```text
How deep should we go?

1. Quick start: give me 3-7 things and I will get you to one useful tuned
   skill quickly. Recommended.
2. Guided calibration: share a broader pack and I will map patterns across
   several skills.
```

Then ask:

```text
Send me a few things that feel like you: things you made, things you like, or
things you reject. Paths, URLs, screenshots, PDFs, and pasted text all work.
You do not need to organize them perfectly.

If you already know which skill you want to improve, mention it. Otherwise, I
will recommend a few.
```

## Pattern Reveal

The first reveal is not a graph approval screen.

Show 3-5 plain-language patterns, followed by useful skill candidates:

```text
Here is what I see emerging:

1. Prefer calm hierarchy over dashboard density.
2. Reach for inspectable local systems before adding infrastructure.
3. Avoid decorative polish that does not clarify the product.

These patterns could sharpen:
- frontend-design
- product-builder
- architecture-review

Which skills should I edit first?

Your full graph is available at ~/.marshmallow/GRAPH.md whenever you want to
inspect the source trail.
```

If the user corrects a pattern, revise it. Do not require an approval reply
when the patterns already feel useful.

## Rewrite Gate

Durable adapter and skill changes remain explicit.

For the persistent Claude adapter:

1. show the proposed `~/.claude/CLAUDE.md` import block
2. explain that it routes Claude Code into compact generated projections
3. show the dry-run diff
4. ask whether to apply the adapter update
5. back up and rewrite only after explicit approval

For each chosen skill:

1. draft one compact pending overlay from 3-7 relevant nodes
2. show the proposed behavioral delta
3. show the dry-run diff
4. ask whether to apply the named skill update
5. after explicit approval, store the canonical overlay under
   `~/.marshmallow/overlays/` and add one pointer block to the skill

A single user reply may approve the clearly listed adapter and skill updates.
Do not silently edit read-only targets or plugin caches.

## Interaction Budget

The quick-start path should target:

| Moment | Budget |
| --- | ---: |
| Calibration choice | 1 user reply |
| Taste-pack intake | 1 user reply |
| Skill selection after pattern reveal | 1 user reply |
| Explicit adapter and skill rewrite approval | 1 user reply |
| Mandatory graph approval | 0 user replies |

The default path should reach recognition after the taste pack and a tuned
skill after four user replies. Fewer is welcome when the user includes a depth
choice, taste pack, or target skill in the same message.

## Ask Only When It Changes The Result

Ask an extra question only when:

- a source cannot be accessed and needs an excerpt or export
- evidence conflicts in a way that changes a proposed skill overlay
- a target is read-only and the user must choose an aligned copy, writable
  path, or skip
- the requested skill is deterministic and personalization may weaken
  correctness

Do not ask the user to manage graph internals.

## After Activation

After applying the persistent adapter and first tune, keep the expansion path
short:

```text
Installed your Claude Code alignment adapter and updated frontend-design.
The originals are backed up and rollback is available.

Use /marshmallow:learn when a correction, decision, or reference should improve
future sessions. Your graph can also improve:
- product-builder
- architecture-review

Tune another skill, inspect the graph, or stop here.
```

The persistent adapter plus first successful aligned result is the activation
event. Everything after that should feel optional.

## No Existing Skills

If the user has no writable judgment-sensitive skills, do not stall the
onboarding. Treat the persistent adapter as the first activation, then offer one
explicit choice:

```text
I did not find a good existing skill to tune.

We can stop after the persistent adapter, or I can preview a small user-level
starter skill called marshmallow-aligned-builder that uses your approved
Marshmallow overlay for product, design, architecture, writing, and planning
work.
```

Create the starter skill only after showing the diff and receiving explicit
approval. It should live under `~/.claude/skills/`, point to a canonical overlay
under `~/.marshmallow/overlays/`, and roll back by deleting the generated skill.

## Acceptance Test

Before launch, run the quick-start path in a clean home and verify:

- the user sees the value proposition before graph terminology
- the first pattern reveal is specific enough to feel recognizable
- there is no mandatory graph-approval reply
- the user-level Claude adapter is installed only after a visible diff and approval
- ordinary sessions search compact projections instead of loading the full graph
- `/marshmallow:learn` stages only explicitly requested learning evidence in the inbox
- raw session logs never become graph nodes or runtime projections
- tuned skills point to canonical overlays instead of copying alignment instructions
- the first tuned skill is reached without manual file editing
- every filesystem rewrite still receives explicit approval
- rollback restores the prior bytes
- the user can explain why the tuned skill changed
- a user with no existing skills can still activate the adapter and optionally
  create the starter skill without manual file editing
