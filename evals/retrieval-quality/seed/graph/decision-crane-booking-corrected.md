---
id: decision-crane-booking-corrected
insight: SG-REFIT seaglass crane crane booking 2026-05-19 is confirmed ground truth as may 19 crane after drydock morning sync corrected the preliminary date.
type: decision
subjects: [sg-refit, mv-seaglass]
source_ids: [2026-04-29-seaglass-crane-prelim, 2026-05-19-drydock-morning-sync]
related_nodes: [drydock-berth-4, sg-refit, victor-hale, elena-vasquez]
labels: [drydock, crane]
updated: 2026-05-19
---

# Crane Booking Corrected Decision

## Current Model

The authoritative **crane booking 2026-05-19** for SG-REFIT was confirmed at drydock morning sync once drydock opened. Victor Hale stated the **seaglass crane** is on berth with **may 19 crane** matching the vendor hold letter — correcting the week-2 preliminary email that cited May 12 after Marcus Holt conflated the booking with an earlier pier crane availability survey. Marcus Holt was directed to update the master grid and retract the May 12 crane note in the sailing impact doc.

## Evidence

- `2026-04-29-seaglass-crane-prelim` - Marcus Holt forwarded Victor Hale's preliminary quote citing **seaglass crane** **crane booking 2026-05-12** at berth 4 heavy-lift zone; May 12 assumed a pier crane availability survey moved from May 5.
- `2026-05-19-drydock-morning-sync` - Victor Hale confirmed **seaglass crane** on berth with **crane booking 2026-05-19**, not May 12; **may 19 crane** is on the vendor hold letter; Marcus directed to retract May 12 note in sailing impact doc.

## Use In Work

- Treat 2026-05-19 as ground truth for SG-REFIT crane scheduling, sailing impact docs, and berth 4 heavy-lift windows.
- Downgrade the May 12 date in `2026-04-29-seaglass-crane-prelim` unless the question explicitly asks what the early preliminary email stated.

## Limits

This correction covers crane booking date only — not thrust-bearing staging gates, fuel-line purge sequence adoption, or sea trial scheduling (2026-06-05). An earlier note in the week-2 preliminary email incorrectly listed crane booking 2026-05-12.

## Connections

- [[drydock-berth-4]] - Heavy-lift berth where the corrected May 19 crane booking applies.
- [[sg-refit]] - Fleet refit project whose crane window this decision corrects.
- [[victor-hale]] - Chief Engineer who confirmed crane on berth at morning sync.
- [[elena-vasquez]] - Fleet Maintenance Director present at drydock opening when correction was recorded.
