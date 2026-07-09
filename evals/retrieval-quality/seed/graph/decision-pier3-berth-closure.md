---
id: decision-pier3-berth-closure
insight: Pier 3 float switch failure on 2026-04-22 triggered partial pier 3 berth closure of berths 3A and 3B starting that morning.
type: decision
subjects: [hana-suzuki, pier-3]
source_ids: [2026-04-21-pier3-berth-hold, 2026-04-22-float-switch-panic]
related_nodes: [pier-3, hana-suzuki, decision-dive-overtime, decision-float-switch-replacement]
labels: [berth-closure, float-switch]
updated: 2026-04-22
---

# Pier 3 Berth Closure Decision

## Current Model

A Pier 3 **float switch failure** on **2026-04-22** triggered partial **pier 3 berth closure** of berths 3A and 3B starting 06:00 that day. Hana Suzuki had emailed the closure list on 2026-04-21 after alarm readings; live execution on the 22nd confirmed the pump cycled twice in ten minutes then flatlined. Night crew treated the event as a formal closure, not a wait-and-see hold. Jessamine Lee held passenger tweets pending dive scope confirmation while Marcus Holt rebuilt the sailing grid for 2026-04-22.

## Evidence

- `2026-04-21-pier3-berth-hold` - Hana Suzuki emails berths 3A and 3B out of service starting **2026-04-22** 06:00 in a **float switch failure** scenario until dive proves otherwise; night crew instructed to treat it as a **pier 3 berth closure** event; Juno asked to hold Jessamine on passenger posts until dive scope confirmed.
- `2026-04-22-float-switch-panic` - Slack thread documents live execution of partial closure after confirmed **float switch failure** with pump flatline on **2026-04-22**; Cal Donner offers overnight pier 3 berth closure watch; Marcus rebuilding sailings grid for **2026-04-22**.

## Use In Work

- When float switch alarms recur at Pier 3, execute the partial closure list immediately and hold passenger notices until dive scope is confirmed.
- Rebuild berth assignments and sailing grids against 3A/3B outage windows rather than assuming normal Pier 3 capacity during the closure.

## Limits

Closure covered berths 3A and 3B only through the April diagnostic window — Hana completed float switch replacement and cleared berths on 2026-04-28. Pier 9 contractor staging and HarborPass cutover schedules are unrelated.

## Connections

- [[pier-3]] - Pier where berths 3A and 3B were taken out of service.
- [[hana-suzuki]] - Site superintendent who ordered and executed the partial closure.
- [[decision-dive-overtime]] - Dive crew overtime authorized the next day to diagnose the float switch failure.
- [[decision-float-switch-replacement]] - Replacement work that resolved the failure and lifted the closure.
