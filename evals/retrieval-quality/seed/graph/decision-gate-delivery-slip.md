---
id: decision-gate-delivery-slip
insight: Turnstile Dynamics gate delivery slip pushes fare gate panels to 2026-05-28 with may 28 delivery confirmed after the prior May 21 window slipped.
type: decision
subjects: [p9-gate, turnstile-dynamics, pier-9]
source_ids: [2026-05-22-gate-delivery-slip]
related_nodes: [p9-gate-retrofit, turnstile-dynamics, decision-critical-path-p9-gate, rel-p9-gate-vs-p9-gang]
labels: [delivery, pier-9]
updated: 2026-05-22
---

# Gate Delivery Slip Decision

## Current Model

Turnstile Dynamics issued an official **gate delivery slip** moving P9-GATE fare gate panels and lane controllers from the penciled May 21 window to **2026-05-28**. Alicia Varga tied the slip to fabrication backlog, not berth conflict — Bridgeway Hoist was already on site when gates slipped. **May 28 delivery** does not reverse Juno Castillo's **critical path** call on P9-GATE from 2026-05-13; it only updates the date in the Q2 Terminal Readiness Playbook.

## Evidence

- `2026-05-22-gate-delivery-slip` - Derek Blunt documents the official **gate delivery slip**: fare gate panels and lane controllers ship for **2026-05-28**, not the May 21 window penciled before gangway landed; **may 28 delivery** tied to fab backlog per Alicia Varga; Juno asked to fold the slip into the Q2 playbook critical-path section without changing the P9-GATE critical-path call.

## Use In Work

- Schedule Turnstile gate crew windows, badge access, and commissioning around **2026-05-28** — not May 21.
- When comparing Pier 9 delivery dates, disambiguate gate slip (May 28) from gangway hold (May 21) using vendor name or codename.

## Limits

This slip covers Turnstile Dynamics gate hardware only — Bridgeway Hoist **gangway delivery** remains firm on 2026-05-21. Fab backlog caused the slip; berth conflict with gangway work was explicitly ruled out.

## Connections

- [[p9-gate-retrofit]] - Pier 9 gate project whose delivery date this slip updates.
- [[turnstile-dynamics]] - P9-GATE vendor that issued the May 28 delivery slip.
- [[decision-critical-path-p9-gate]] - Critical-path declaration that stands despite the date slip.
- [[rel-p9-gate-vs-p9-gang]] - Near-duplicate pair where gate and gangway delivery dates diverged.
