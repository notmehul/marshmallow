---
id: pier-9-night-lighting
insight: The pier 9 lighting night lighting upgrade budget and commissioning stay on p9-gate only, not P9-GANG gangway apron fixtures.
type: entity
subjects: [pier-9, p9-gate]
source_ids: [2026-05-12-pier9-lighting-scope]
related_nodes: [decision-lighting-tied-to-gate, p9-gate-retrofit, cal-donner, pier-9]
labels: [night-lighting, pier-9]
updated: 2026-05-12
---

# Pier 9 Night Lighting

## Current Model

The **night lighting upgrade** at Pier 9 is explicitly bound to **P9-GATE**, not P9-GANG. **Pier 9 lighting** panels on the gate approach feed Turnstile lane sensors and sit under gate retrofit cost codes in playbook section 9.2. The gangway apron keeps existing sodium fixtures through Bridgeway Hoist install — no duplicate line items on P9-GANG. Cal Donner requested a circuit map before touching floodlight breakers; Victor Dunn committed to upload by EOD for commissioning prep.

## Evidence

- `2026-05-12-pier9-lighting-scope` - Key decision: the **night lighting upgrade** budget and commissioning window stay on **P9-GATE** only — not gangway work; **pier 9 lighting** panels on the gate approach feed Turnstile lane sensors while the gangway apron stays on existing sodium fixtures through Bridgeway install.

## Use In Work

- Tag all Pier 9 night lighting budget lines, breaker work, and commissioning windows under P9-GATE in the Q2 playbook — never duplicate on P9-GANG cost codes.
- When retrieving "pier 9 lighting" artifacts, filter by codename P9-GATE or Turnstile Dynamics vendor context to avoid conflating with gangway load-test or hydraulic scope.

## Limits

Pier 9 night lighting here covers budget binding and gate-approach panel scope — not Cal Donner's later 2026-06-03 floodlight maintenance mode for gate commissioning or gangway apron sodium fixtures through Bridgeway install.

## Connections

- [[decision-lighting-tied-to-gate]] - Formal decision record binding night lighting to P9-GATE.
- [[p9-gate-retrofit]] - Gate project that owns the night lighting upgrade scope.
- [[cal-donner]] - Night harbormaster who requested the circuit map before breaker work.
- [[pier-9]] - Pier entity hosting both gate and gangway lighting zones.
