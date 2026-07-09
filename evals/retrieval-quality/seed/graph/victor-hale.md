---
id: victor-hale
insight: Victor Hale blocks SG-REFIT hull penetration until spare thrust bearing delivery is staged port-side per his engineering sign-off.
type: entity
subjects: [victor-hale, sg-refit, mv-seaglass]
source_ids: [2026-04-29-seaglass-crane-prelim]
related_nodes: [sg-refit, mv-seaglass, rel-victor-hale-sg-refit, rule-thrust-bearing-before-hull]
labels: [chief-engineer, seaglass-refit]
updated: 2026-04-29
---

# Victor Hale

## Current Model

Victor Hale is Chief Engineer on MV Seaglass and schedules crane and berth time around his SG-REFIT refit sequence with Juno. He requires spare **thrust bearing** delivery and staging before any **hull penetration** on SG-REFIT — **victor hale** will not authorize cutting until the bearing crate is port-side. His preliminary crane quote (forwarded by Marcus Holt) cited a May 12 booking that was later corrected to 2026-05-19 once drydock opened.

## Evidence

- `2026-04-29-seaglass-crane-prelim` - Marcus Holt's forward of **victor hale**'s preliminary quote blocks **hull penetration** until spare **thrust bearing** lands on the dock, with Victor stating he will not authorize hull penetration until the bearing crate is staged port-side; seaglass crane lift slot was preliminarily listed as 2026-05-12 pending pier crane availability survey.

## Use In Work

- Confirm thrust bearing is staged port-side and Victor Hale has signed off before scheduling SG-REFIT hull penetration or cutting work.
- Coordinate crane booking and heavy-lift windows with Victor Hale rather than relying on early forwarded quotes that may conflate survey dates with berth bookings.

## Limits

Victor Hale does not manage Pier 9 infrastructure (Victor Dunn) or set P9-GATE change-order caps. The May 12 crane booking in the preliminary email was wrong; ground-truth crane on berth is 2026-05-19 per drydock morning sync.

## Connections

- [[sg-refit]] - Engine-room refit where Victor Hale gates hull penetration on thrust bearing delivery.
- [[mv-seaglass]] - Vessel Victor Hale engineers during the refit sequence.
- [[rel-victor-hale-sg-refit]] - Relationship node linking Victor Hale to SG-REFIT engineering ownership.
- [[rule-thrust-bearing-before-hull]] - Standing rule encoding Victor's thrust-bearing-before-penetration requirement.
