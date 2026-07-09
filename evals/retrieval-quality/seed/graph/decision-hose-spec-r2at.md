---
id: decision-hose-spec-r2at
insight: P9-GANG p9-gang spec locks hydraulic hose to sae 100r2at, not P9-GATE's SAE 100R1AT fare lane actuators.
type: decision
subjects: [p9-gang, victor-dunn]
source_ids: [2026-05-08-gangway-hose-spec]
related_nodes: [p9-gang-replacement, p9-gate-retrofit, rel-p9-gate-vs-p9-gang, bridgeway-hoist]
labels: [hydraulics, pier-9]
updated: 2026-05-08
---

# Hose Spec R2AT Decision

## Current Model

Victor Dunn locked the **P9-GANG** **hydraulic hose** assembly to **SAE 100R2AT** (400 bar working, gangway lift circuit) per the written **p9-gang spec**. P9-GATE remains on **SAE 100R1AT** for Turnstile fare lane actuators — a different pressure class. Procurement must not consolidate to one hose SKU for convenience; a near-miss on a Kelwick bundle quote that mixed specs prompted the explicit split. Bridgeway Hoist fabricator requested written sign-off before May 21 delivery.

## Evidence

- `2026-05-08-gangway-hose-spec` - **Hydraulic hose** assembly per **p9-gang spec**: **SAE 100R2AT** (400 bar working, gangway lift circuit); gate side P9-GATE remains **SAE 100R1AT** on Turnstile fare lane actuators; Victor Dunn warns against consolidating to one hose SKU and notes a near-miss on a Kelwick bundle quote that mixed specs.

## Use In Work

- Order and inspect P9-GANG hydraulic assemblies against SAE 100R2AT only — reject R1AT gate-side stock for gangway lift circuits.
- When retrieving "hydraulic hose" or "pier 9 retrofit" artifacts, disambiguate by codename P9-GANG vs P9-GATE before citing a spec.

## Limits

Hose spec decision covers P9-GANG lift circuit assemblies only — not gangway mock-up width (2.4 m), load test certificate requirements, or Bridgeway delivery date (2026-05-21).

## Connections

- [[p9-gang-replacement]] - Gangway project whose hydraulic hose spec this decision locks.
- [[p9-gate-retrofit]] - Gate project retaining the separate SAE 100R1AT actuator spec.
- [[rel-p9-gate-vs-p9-gang]] - Disambiguation relationship for near-duplicate Pier 9 codenames.
- [[bridgeway-hoist]] - Gangway vendor whose fabricator required written sign-off on the R2AT spec.
