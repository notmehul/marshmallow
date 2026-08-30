---
id: turnstile-dynamics
insight: Turnstile Dynamics is the p9-gate vendor and gate vendor whose gate delivery slip moved to 2026-05-28 may 28 delivery from the prior May 21 window.
type: entity
subjects: [p9-gate, pier-9]
source_ids: [2026-04-27-vendor-split-announcement, 2026-05-22-gate-delivery-slip]
related_nodes: [p9-gate-retrofit, rel-derek-turnstile-dynamics, decision-gate-delivery-slip, derek-blunt]
labels: [vendor, gate-retrofit]
updated: 2026-05-22
---

# Turnstile Dynamics

## Current Model

**Turnstile Dynamics** is the **P9-GATE** **gate vendor** — assigned gate automation, fare lane hardware, and commissioning support after Derek Blunt's vendor split announcement. As the **p9-gate vendor** of record, Turnstile owns fare gate panels and lane controllers for Pier 9 gate retrofit work. An official **gate delivery slip** moved shipment from the May 21 penciled window to **2026-05-28**; Alicia Varga at Turnstile cited fab backlog, not berth conflict, since Bridgeway Hoist was already on site. The **may 28 delivery** does not change Juno's P9-GATE critical-path declaration from 2026-05-13 — only the date.

## Evidence

- `2026-04-27-vendor-split-announcement` - Derek Blunt assigns **P9-GATE → Turnstile Dynamics** for gate automation, fare lane hardware, and commissioning support; Turnstile is the **p9-gate vendor** going forward with Kelwick staying on old paperwork until Victor Dunn supersedes it.
- `2026-05-22-gate-delivery-slip` - Derek documents official **gate delivery slip**: fare gate panels and lane controllers ship for **2026-05-28**, not the May 21 window penciled before gangway landed; **May 28 delivery** tied to fab backlog per Alicia Varga, not berth conflict.

## Use In Work

- Route P9-GATE gate automation quotes, badge windows, and commissioning schedules through Turnstile Dynamics — not Kelwick Marine or Bridgeway Hoist.
- Plan Pier 9 gate crew staging around the 2026-05-28 delivery date while keeping gangway work on the separate May 21 Bridgeway calendar.

## Limits

Turnstile Dynamics does not own P9-GANG gangway fabrication, hydraulic hose specs (SAE 100R2AT), or Bridgeway mobilization discounts. Gate slip was fab-driven; gangway delivery remained firm on 2026-05-21 per Derek's 2026-05-14 hold email.

## Connections

- [[p9-gate-retrofit]] - Pier 9 gate project Turnstile Dynamics executes as assigned vendor.
- [[rel-derek-turnstile-dynamics]] - Relationship node for Derek Blunt's liaison role with the gate vendor.
- [[decision-gate-delivery-slip]] - Decision record documenting the May 28 delivery date change.
- [[derek-blunt]] - Vendor liaison who announced the split and reported the delivery slip.
