---
id: decision-hp-golive-target
insight: HarborPass 2.0 go-live 2026-06-02 remains the published june 2 go-live target for HP-MIGRATE after rollback token clearance.
type: decision
subjects: [harborpass-2-0, hp-migrate, fatima-okonkwo]
source_ids: [2026-05-26-rollback-token-gate, 2026-06-02-harborpass-golive]
related_nodes: [harborpass-2-0, hp-migrate, decision-rollback-token-gate, rel-fatima-harborpass]
labels: [migration, ticketing]
updated: 2026-06-02
---

# HarborPass Go-Live Target Decision

## Current Model

**HarborPass 2.0** production cutover targeted **go-live 2026-06-02**, the published **june 2 go-live** date Jessamine Lee could cite externally once Fatima Okonkwo cleared the rollback token hold. Migration completed at 05:47 on June 2 with HarborPass 2.0 live across Pier 3 and Pier 5 first. Pier 7 retained legacy barcode readers on a separate sunset track through 2026-06-12.

## Evidence

- `2026-05-26-rollback-token-gate` - Fatima Okonkwo reaffirms targeting **HarborPass 2.0** **go-live 2026-06-02** as the published **june 2 go-live** date Jessamine can cite externally once rollback token test clears; hard gate on HarborPass migration remains until staging test passes clean.
- `2026-06-02-harborpass-golive` - HarborPass migration completes at **go-live 05:47** on the **june 2 migration** track; **HarborPass 2.0** is live with **june 2 go-live** milestone checked in Q2 playbook; Jessamine posts all-clear to Pier 3 and Pier 5 boards.

## Use In Work

- Treat **2026-06-02** as the authoritative HarborPass 2.0 go-live date for outage notices, playbook milestones, and post-cutover reader configuration.
- Confirm rollback token test completion before citing the go-live target in external passenger communications.

## Limits

Go-live target covers production cutover timing only — Pier 7 **legacy barcode** readers remain on the old stack until **june 12 sunset**. Actual cutover logged at 05:47, not midnight.

## Connections

- [[harborpass-2-0]] - Fare system whose go-live date this decision tracks.
- [[hp-migrate]] - Migration project codename for the HarborPass 2.0 cutover.
- [[decision-rollback-token-gate]] - Prerequisite gate Fatima imposed before migration could proceed.
- [[rel-fatima-harborpass]] - Relationship linking Fatima Okonkwo to HarborPass administration.
