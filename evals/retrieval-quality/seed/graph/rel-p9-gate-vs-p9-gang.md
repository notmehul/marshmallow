---
id: rel-p9-gate-vs-p9-gang
insight: P9-GATE and P9-GANG diverged under Pier-9 Gate Retrofit vs Pier-9 Gangway Replacement with separate SAE 100R2AT hydraulic hose on the gangway side.
type: relationship
subjects: [p9-gate-retrofit, p9-gang-replacement]
source_ids: [2026-04-24-pier9-dual-scope-intro, 2026-05-08-gangway-hose-spec]
related_nodes: [p9-gate-retrofit, p9-gang-replacement, decision-hose-spec-r2at, victor-dunn]
labels: [disambiguation, pier-9-pair]
updated: 2026-05-08
---

# P9-GATE vs P9-GANG

## Current Model

**P9-GATE** and **P9-GANG** are near-duplicate Pier 9 codenames that share berth, staging, and hydraulic vocabulary but must be retrieved separately. Victor Dunn's April dual-scope intro split the whiteboard into **Pier-9 Gate Retrofit** (four fare lanes, gate automation, night lighting circuit upgrades) and **Pier-9 Gangway Replacement** (hydraulic gangway module, load test hooks, hose spec TBD) while both scopes still sat under the Kelwick Marine **single-contractor plan** on paper. By May 8 the scopes had diverged further: Victor locked **P9-GANG** **hydraulic hose** to **SAE 100R2AT** (400 bar working, gangway lift circuit) per **p9-gang spec**, while gate-side **P9-GATE** remained **SAE 100R1AT** on Turnstile fare lane actuators — procurement must not consolidate to one hose SKU; Bridgeway Hoist fabricator required written sign-off before May 21 delivery.

## Evidence

- `2026-04-24-pier9-dual-scope-intro` - Victor Dunn splits whiteboard into two columns still under Kelwick Marine **single-contractor plan**; **Pier-9 Gate Retrofit**: four fare lanes, gate automation, night lighting circuit upgrades; **Pier-9 Gangway Replacement**: hydraulic gangway module, load test hooks, hose spec TBD; **P9-GATE** and **P9-GANG** codenames live in **terminal readiness playbook** tracker.
- `2026-05-08-gangway-hose-spec` - **Hydraulic hose** assembly per **p9-gang spec**: **SAE 100R2AT** (400 bar working, gangway lift circuit); gate side P9-GATE remains **SAE 100R1AT** on Turnstile fare lane actuators; procurement warned not to consolidate to one hose SKU; near-miss on Kelwick bundle quote mixing specs; Bridgeway Hoist fabricator asked for written sign-off before May 21 delivery.

## Use In Work

- Disambiguate Pier 9 retrieval by codename, vendor (Turnstile Dynamics vs Bridgeway Hoist), or component (gate lane vs gangway width/hose) — not by generic "pier 9 retrofit" language alone.
- Never reuse P9-GATE R1AT hose spec on P9-GANG lift circuits; cite Victor Dunn's R2AT sign-off for gangway procurement.

## Limits

Kelwick Marine is inactive after the 2026-05-06 single-contractor supersession — do not treat it as the active vendor. Gate delivery slipped to 2026-05-28 while gangway delivery held 2026-05-21; do not conflate those dates.

## Connections

- [[p9-gate-retrofit]] - Pier 9 gate automation project using Turnstile Dynamics and R1AT actuators.
- [[p9-gang-replacement]] - Pier 9 gangway project using Bridgeway Hoist and R2AT hydraulic hose.
- [[decision-hose-spec-r2at]] - Decision locking SAE 100R2AT as the P9-GANG hose spec.
- [[victor-dunn]] - Pier Infrastructure Program Manager who introduced and enforced the scope split.
