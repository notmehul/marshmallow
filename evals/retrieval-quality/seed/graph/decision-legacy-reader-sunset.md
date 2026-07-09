---
id: decision-legacy-reader-sunset
insight: HarborPass 2.0 keeps legacy barcode pier 7 readers active until june 12 sunset as the sole remaining legacy install site.
type: decision
subjects: [harborpass-2-0, pier-7, fatima-okonkwo]
source_ids: [2026-06-04-legacy-reader-sunset]
related_nodes: [harborpass-2-0, pier-7, fatima-okonkwo, elena-crane]
labels: [migration, pier-7]
updated: 2026-06-04
---

# Legacy Reader Sunset Decision

## Current Model

HarborPass 2.0 retains **legacy barcode** scanners at Pier 7 on the old HarborPass stack until **june 12 sunset** — do not decommission early. **Pier 7 readers** are the only remaining legacy install site; Pier 3, Pier 5, and Pier 9 already run on 2.0 rails after the June 2 cutover. Elena Crane was directed to print legacy barcode fallback cards for booth staff. Fatima Okonkwo will publish the **june 12 sunset** date on the HP-MIGRATE internal wiki.

## Evidence

- `2026-06-04-legacy-reader-sunset` - Fatima Okonkwo confirms **legacy barcode** scanners at Pier 7 stay on old HarborPass stack until **june 12 sunset** with no early decommission; **pier 7 readers** are the only remaining legacy install site while P3, P5, and P9 already on 2.0 rails; Elena Crane to print fallback cards for booth staff.

## Use In Work

- Keep Pier 7 legacy barcode readers operational and staffed with fallback cards through **2026-06-12** — do not rip readers early after HarborPass 2.0 go-live.
- When configuring reader failover, treat Pier 7 as the sole legacy exception until the published sunset date.

## Limits

Sunset applies to Pier 7 legacy barcode hardware only — it does not extend HarborPass outage windows, rollback token requirements, or P7-RAMP ramp handover on 2026-06-10.

## Connections

- [[harborpass-2-0]] - New fare system whose rollout left Pier 7 on legacy readers temporarily.
- [[pier-7]] - Sole pier retaining legacy barcode install until sunset.
- [[fatima-okonkwo]] - HarborPass admin who set and will publish the sunset date.
- [[elena-crane]] - Pier 7 passenger services manager preparing booth fallback cards.
