---
id: harborpass-2-0
insight: HarborPass 2.0 targets go-live 2026-06-02 june 2 go-live while legacy barcode pier 7 readers sunset on june 12 sunset at Pier 7 only.
type: entity
subjects: [harborpass, hp-migrate]
source_ids: [2026-05-26-rollback-token-gate, 2026-06-02-harborpass-golive, 2026-06-04-legacy-reader-sunset]
related_nodes: [hp-migrate, pier-7, fatima-okonkwo, decision-legacy-reader-sunset]
labels: [ticketing, fare-system]
updated: 2026-06-04
---

# HarborPass 2.0

## Current Model

**HarborPass 2.0** is HarborLine's next-generation fare and access system migrated under HP-MIGRATE. Fatima Okonkwo reaffirmed the published **go-live 2026-06-02** target — the **june 2 go-live** date Jessamine Lee could cite externally once rollback token tests cleared. Production cutover completed at 05:47 on June 2 with HarborPass 2.0 live on Piers 3, 5, and 9. **Legacy barcode** scanners remain at Pier 7 only until **june 12 sunset**; **Pier 7 readers** are the sole remaining legacy install site while booth staff carry fallback cards.

## Evidence

- `2026-05-26-rollback-token-gate` - Fatima hard-gates **HarborPass migration** on rollback token test while still targeting **HarborPass 2.0** **go-live 2026-06-02** as the published **june 2 go-live** date Jessamine can cite externally once the hold clears.
- `2026-06-02-harborpass-golive` - HarborOps war-room records HarborPass 2.0 live at go-live 05:47 on june 2 migration track; Jessamine posts all-clear to Pier 3 and Pier 5 boards; Pier 7 gets legacy barcode note with sunset still Jun 12.
- `2026-06-04-legacy-reader-sunset` - Fatima confirms **legacy barcode** scanners at Pier 7 stay on old stack until **june 12 sunset**; **Pier 7 readers** are the only remaining legacy install site with P3/P5/P9 already on 2.0 rails.

## Use In Work

- Treat 2026-06-02 as the HarborPass 2.0 go-live target and actual production cutover date when aligning berth operations and passenger outage notices.
- Keep Pier 7 legacy barcode readers active through 2026-06-12 — do not rip readers early because production cutover finished June 2.

## Limits

HarborPass 2.0 go-live required rollback token test clearance in staging — the published target date alone did not authorize cutover. Legacy reader sunset at Pier 7 is decoupled from the June 2 migration completion time.

## Connections

- [[hp-migrate]] - Migration project administering the HarborPass 2.0 cutover.
- [[pier-7]] - Sole pier retaining legacy barcode readers until June 12 sunset.
- [[fatima-okonkwo]] - Access Systems admin who gated migration and set reader sunset.
- [[decision-legacy-reader-sunset]] - Decision record for Pier 7 legacy reader decommission timing.
