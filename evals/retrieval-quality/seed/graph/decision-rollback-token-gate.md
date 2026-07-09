---
id: decision-rollback-token-gate
insight: Fatima okonkwo blocks harborpass migration until rollback token test completes clean in staging before the HarborPass 2.0 cutover.
type: decision
subjects: [fatima-okonkwo, hp-migrate, harborpass-2-0]
source_ids: [2026-05-26-rollback-token-gate]
related_nodes: [fatima-okonkwo, harborpass-2-0, decision-hp-golive-target, hp-migrate]
labels: [migration, access-systems]
updated: 2026-05-26
---

# Rollback Token Gate Decision

## Current Model

**Fatima Okonkwo** placed a hard gate on **HarborPass migration** until the **rollback token test** completes clean in staging — non-negotiable from her side on HP-MIGRATE. Pier 3 and Pier 5 reader failover failed on the second attempt due to stale cache when the hold was issued. Jessamine Lee was told to hold the passenger notice draft until Fatima green-lights; outage copy could stay in draft but boards must not publish early. The **june 2 go-live** target remained published pending clearance.

## Evidence

- `2026-05-26-rollback-token-gate` - **Fatima okonkwo** places hard gate on **HarborPass migration** until **rollback token test** completes clean in staging; Pier 3 and Pier 5 reader failover FAIL on second attempt with stale cache; Jessamine told to hold passenger notice draft until green-light while **HarborPass 2.0** **go-live 2026-06-02** target stays published.

## Use In Work

- Do not schedule production HarborPass cutover or publish outage notices until Fatima Okonkwo confirms rollback token test pass in staging.
- Resolve Pier 3 and Pier 5 reader failover stale-cache failures before requesting migration window clearance.

## Limits

This gate covers rollback token test completion only — it does not govern Pier 7 legacy barcode reader sunset on 2026-06-12 or P9-GATE contractor badge batches.

## Connections

- [[fatima-okonkwo]] - Access Systems admin who imposed the rollback token hard gate.
- [[harborpass-2-0]] - Fare system whose migration this gate blocks until test clearance.
- [[decision-hp-golive-target]] - Go-live target that remained published while this gate was active.
- [[hp-migrate]] - Migration project codename governed by Fatima's rollback token requirement.
