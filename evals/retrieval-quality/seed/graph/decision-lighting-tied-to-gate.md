---
id: decision-lighting-tied-to-gate
insight: Victor Dunn tied the pier 9 lighting night lighting upgrade to p9-gate only, not P9-GANG gangway apron fixtures.
type: decision
subjects: [pier-9, p9-gate, victor-dunn]
source_ids: [2026-05-12-pier9-lighting-scope]
related_nodes: [pier-9-night-lighting, p9-gate-retrofit, p9-gang-replacement, cal-donner]
labels: [night-lighting, pier-9]
updated: 2026-05-12
---

# Lighting Tied To Gate Decision

## Current Model

Victor Dunn bound the Pier 9 **night lighting upgrade** budget and commissioning window to **P9-GATE** only at the 2026-05-12 scope meeting. **Pier 9 lighting** panels on the gate approach feed Turnstile lane sensors and sit under gate retrofit cost codes in playbook section 9.2. The gangway apron keeps existing sodium fixtures through Bridgeway Hoist install — no duplicate line items on P9-GANG. Cal Donner requested a circuit map before touching floodlight breakers; Victor committed to upload by EOD.

## Evidence

- `2026-05-12-pier9-lighting-scope` - Key decision: the **night lighting upgrade** budget and commissioning window stay on **P9-GATE** only — not gangway work; **pier 9 lighting** panels on the gate approach feed Turnstile lane sensors while the gangway apron stays on existing sodium fixtures through Bridgeway install; Juno notes playbook section 9.2 already tags lighting under gate retrofit.

## Use In Work

- Tag all Pier 9 night lighting budget lines, breaker work, and commissioning windows under P9-GATE — never duplicate on P9-GANG cost codes.
- When retrieving "pier 9 lighting" artifacts, filter by codename P9-GATE or Turnstile Dynamics vendor context to avoid conflating with gangway scope.

## Limits

This binding covers budget and commissioning scope only — not Cal Donner's later 2026-06-03 floodlight maintenance mode for gate commissioning or gangway apron sodium fixtures through Bridgeway install.

## Connections

- [[pier-9-night-lighting]] - Entity node describing the Pier 9 night lighting scope.
- [[p9-gate-retrofit]] - Gate project that owns the night lighting upgrade.
- [[p9-gang-replacement]] - Adjacent Pier 9 workstream explicitly excluded from lighting scope.
- [[cal-donner]] - Night harbormaster who requested the circuit map before breaker work.
