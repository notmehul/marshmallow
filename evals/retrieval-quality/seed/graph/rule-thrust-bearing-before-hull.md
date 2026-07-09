---
id: rule-thrust-bearing-before-hull
insight: Victor Hale blocks SG-REFIT hull penetration until spare thrust bearing delivery is staged port-side — no cutting until the bearing crate is on the dock.
type: preference
subjects: [victor-hale, sg-refit]
source_ids: [2026-04-29-seaglass-crane-prelim]
related_nodes: [victor-hale, sg-refit, rel-victor-hale-sg-refit, mv-seaglass]
labels: [refit-sequence, engineering]
updated: 2026-04-29
---

# Thrust Bearing Before Hull Rule

## Current Model

**Victor Hale** will not authorize **hull penetration** on **SG-REFIT** until the spare **thrust bearing** is delivered and staged port-side on the dock. Marcus Holt's 2026-04-29 forward of Victor Hale's preliminary crane quote cites a crane booking of 2026-05-12 (later corrected to 2026-05-19 once drydock opened), but the thrust-bearing gate predates drydock and remains in force: no cutting until the bearing crate is physically on the dock. Elena Vasquez co-signs SG-REFIT milestones with this sequence constraint.

## Evidence

- `2026-04-29-seaglass-crane-prelim` - **Seaglass crane** lift slot cited as **crane booking 2026-05-12** (berth 4 heavy-lift zone); **hull penetration** work blocked until spare **thrust bearing** lands — Victor Hale says no cutting until it's on the dock; bearing crate must be staged port-side before authorization.

## Use In Work

- Verify thrust bearing crate is staged port-side before scheduling any SG-REFIT hull penetration or drydock cutting work — treat Victor Hale's hold as a hard gate regardless of crane booking date.
- Coordinate crane lift timing with bearing delivery lead time when updating the Q2 playbook berth schedule around MV Seaglass.

## Limits

This rule governs thrust bearing staging before hull cuts only — not fuel-line purge sequence adoption (Elena Vasquez's sequence won), sea trial date (2026-06-05), or revenue return (2026-06-12). The preliminary email's May 12 crane booking was wrong; ground truth is 2026-05-19 per drydock morning sync.

## Connections

- [[victor-hale]] - Chief Engineer, MV Seaglass who issued the hull penetration hold.
- [[sg-refit]] - MV Seaglass Engine-Room Refit project subject to the bearing-before-cut sequence.
- [[rel-victor-hale-sg-refit]] - Relationship linking Victor Hale to SG-REFIT engineering milestones.
- [[mv-seaglass]] - Vessel whose hull penetration Victor Hale gates on bearing delivery.
