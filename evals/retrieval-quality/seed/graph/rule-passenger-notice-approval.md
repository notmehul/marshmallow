---
id: rule-passenger-notice-approval
insight: Jessamine Lee's passenger notice covers the HarborPass outage from june 1 22:00 through 2026-06-02 06:00 — Juno and Fatima must approve before external posting.
type: preference
subjects: [jessamine-lee, harborpass-2-0, hp-migrate]
source_ids: [2026-06-01-harborpass-outage-notice-draft]
related_nodes: [jessamine-lee, decision-outage-notice-window, harborpass-2-0, rel-jessamine-passenger-comms]
labels: [passenger-comms, approval]
updated: 2026-06-01
---

# Passenger Notice Approval Rule

## Current Model

Jessamine Lee drafted the **passenger notice** for the **HarborPass outage** ahead of HarborPass 2.0 cutover. The notice window runs from **june 1 22:00** local through **2026-06-02 06:00** — a six-hour blackout across all staffed fare piers. Juno Castillo and Fatima Okonkwo must approve before Jessamine posts the web alert with HarborPass 2.0 branding. Jessamine noted that any cutover slip past 06:00 requires a revised **passenger notice** pinged on Slack.

## Evidence

- `2026-06-01-harborpass-outage-notice-draft` - Jessamine Lee draft sets **HarborPass outage** beginning **june 1 22:00** local ending **2026-06-02 06:00** (six-hour window) across staffed fare piers; web alert carries HarborPass 2.0 branding; P.S. requires revised **passenger notice** if cutover slips past 06:00 — pending Juno and Fatima approval before posting.

## Use In Work

- Route all HarborPass migration passenger-facing disruption copy through Jessamine Lee and hold external posting until Juno Castillo signs off — treat her draft as the template for the approved notice window.
- Trigger a revised passenger notice workflow immediately if cutover extends past 06:00 on June 2 rather than silently extending the original window.

## Limits

This rule covers the drafted outage notice approval workflow and its six-hour window — not the actual go-live completion at 05:47 on June 2, rollback token test gating, or Pier 7 legacy barcode reader sunset on 2026-06-12.

## Connections

- [[jessamine-lee]] - Passenger communications lead who drafted the outage notice pending Juno approval.
- [[decision-outage-notice-window]] - Decision node recording the same HarborPass outage window dates.
- [[harborpass-2-0]] - HarborPass 2.0 fare system whose cutover the notice covers.
- [[rel-jessamine-passenger-comms]] - Relationship linking Jessamine to passenger notices Juno approves before publication.
