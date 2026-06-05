# One-Minute Demo

## Setup

Install the plugin, then run:

```text
/marshmallow:start
```

## Walkthrough

1. Choose quick start.

2. Add three sources:
   - a product spec you made
   - an interface screenshot you like
   - a dashboard screenshot you reject

3. Let Marshmallow surface the patterns it sees:

   ```text
   Prefer a calm helper-like interface over a control panel.
   Avoid decorative glass cards and gradients without hierarchy.
   Prefer inspectable local primitives before adding infrastructure.
   ```

4. Review and approve the one-block `~/.claude/CLAUDE.md` adapter diff.

5. Let Marshmallow recommend the frontend-design skill.

6. Choose frontend-design and review the proposed diff:

   ```diff
   + Prefer calm hierarchy and conversational warmth over dashboard density.
   + Avoid decorative glass cards, excessive rounding, and gradients without hierarchy.
   ```

7. Approve the tune.

8. Show that the tuned skill contains one pointer to
   `~/.marshmallow/overlays/frontend-design.md`, not a copied prompt.

9. Start a fresh Claude Code session and run the same UI task before and after
   alignment.

10. Open `~/.marshmallow/projections/design.md` and `~/.marshmallow/GRAPH.md` to
   show that the alignment comes from an
   inspectable reusable graph.

11. Run `/marshmallow:learn` with one correction. Show the inbox candidate
    before its reusable insight is promoted.

12. Roll back the skill to prove the update is reversible.

## Launch Message

> Drop in the things you love. Marshmallow turns them into a personal alignment
> layer so your agents start closer to how you actually work.
