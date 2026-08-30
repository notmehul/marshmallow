---
id: pier-3
insight: Pier 3 float switch failure on 2026-04-22 triggered pier 3 berth closure until Hana Suzuki finished float switch replacement and marked pier 3 complete on 2026-04-28.
type: entity
subjects: [pier-3]
source_ids: [2026-04-21-pier3-berth-hold, 2026-04-22-float-switch-panic, 2026-04-28-pier3-switch-complete]
related_nodes: [hana-suzuki, rel-hana-pier-3, decision-float-switch-replacement, decision-pier3-berth-closure]
labels: [pier, berth-ops]
updated: 2026-04-28
---

# Pier 3

## Current Model

**Pier 3** berths 3A and 3B entered partial closure after a **float switch failure** confirmed on **2026-04-22** when the 3A pump cycled twice in ten minutes then flatlined. Hana Suzuki had pre-announced the **pier 3 berth closure** event starting 2026-04-22 06:00, treating it as a float-switch scenario until dive proved otherwise. **Hana Suzuki** completed the **float switch replacement** with dive lead sign-off on 2026-04-27 19:30; berths cleared for normal ops effective **2026-04-28** 06:00 with **pier 3 complete** logged in the maintenance portal and Q2 playbook pier status set to green.

## Evidence

- `2026-04-21-pier3-berth-hold` - Hana emails berths 3A and 3B out of service starting **2026-04-22** 06:00 for a **float switch failure** scenario; night crew told to treat it as a **pier 3 berth closure** event, not wait-and-see.
- `2026-04-22-float-switch-panic` - Live Slack thread confirms **float switch failure** — 3A pump cycled twice in 10 min then flatlined; partial closure list executing with Marcus rebuilding the **2026-04-22** sailing grid.
- `2026-04-28-pier3-switch-complete` - **Float switch replacement** signed off by dive lead 2026-04-27 19:30; berth 3A/3B cleared effective **2026-04-28** 06:00 with Hana marking **pier 3 complete** in the maintenance portal; Marcus slid May 1 commuter turns back to 3A.

## Use In Work

- Treat Pier 3 berths 3A/3B as fully operational after 2026-04-28 unless a new float-switch alarm triggers — the April closure is closed out.
- Hold passenger-facing posts during future Pier 3 float-switch events until dive scope is confirmed, per the April 21–22 playbook pattern.

## Limits

Pier 3 closure in April was float-switch driven, not related to P7-RAMP, P9-GATE, or HarborPass migration. Dive inspection overtime on 2026-04-23 was authorized separately and is not part of this node's berth-status facts.

## Connections

- [[hana-suzuki]] - Pier 3 Site Superintendent who ordered closure and completed switch replacement.
- [[rel-hana-pier-3]] - Relationship node linking Hana Suzuki to Pier 3 operations.
- [[decision-float-switch-replacement]] - Decision record for the completed switch replacement work.
- [[decision-pier3-berth-closure]] - Decision record for the partial berth closure triggered by float switch failure.
