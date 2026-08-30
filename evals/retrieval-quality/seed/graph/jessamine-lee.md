---
id: jessamine-lee
insight: Jessamine Lee's passenger notice covers the HarborPass outage from june 1 22:00 through 2026-06-02 06:00 pending Juno and Fatima approval.
type: entity
subjects: [jessamine-lee, harborpass]
source_ids: [2026-06-01-harborpass-outage-notice-draft]
related_nodes: [rel-jessamine-passenger-comms, hp-migrate, harborpass-2-0, decision-outage-notice-window]
labels: [passenger-comms, outage-notice]
updated: 2026-06-01
---

# Jessamine Lee

## Current Model

Jessamine Lee owns passenger communications for HarborLine and publishes disruption notices Juno approves. Her draft **passenger notice** for the **HarborPass outage** sets a six-hour cutover window: **june 1 22:00** local through **2026-06-02 06:00**, covering all staffed fare piers with terminal boards, SMS, and a web alert carrying **HarborPass 2.0** branding. Jessamine held publication pending Juno and Fatima Okonkwo green-light after the rollback token gate cleared. She noted that if cutover slips past 06:00 she will need a revised notice.

## Evidence

- `2026-06-01-harborpass-outage-notice-draft` - Jessamine Lee draft email sets the **HarborPass outage** window from **june 1 22:00** through **2026-06-02 06:00** (six hours) across all staffed fare piers, with web alert FAQ under **HarborPass 2.0** branding and a note to revise the **passenger notice** if cutover slips past 06:00.

## Use In Work

- Route HarborPass migration outage copy and terminal-board alerts through Jessamine Lee's passenger notice draft rather than ad hoc pier-level tweets.
- Hold external publication until Juno approves and Fatima clears the rollback token gate, even if outage copy is drafted.

## Limits

Jessamine Lee does not administer HarborPass systems or run rollback token tests (Fatima Okonkwo). The notice covers the planned outage window only; actual go-live completed at 05:47 on June 2.

## Connections

- [[rel-jessamine-passenger-comms]] - Relationship node linking Jessamine to passenger-facing communications duties.
- [[hp-migrate]] - HarborPass 2.0 migration project the outage notice supports.
- [[harborpass-2-0]] - Fare system branding cited in the outage web alert.
- [[decision-outage-notice-window]] - Decision record for the Jun 1–2 six-hour outage window.
