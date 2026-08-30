---
id: pier-9
insight: Pier 9 night lighting upgrade stays on P9-GATE not P9-GANG and Marcus Holt's contractor shift ban blocks back-to-back shifts on the same pier 9 berth.
type: entity
subjects: [pier-9, p9-gate, p9-gang]
source_ids: [2026-05-12-pier9-lighting-scope, 2026-05-21-gangway-arrival-day]
related_nodes: [p9-gate-retrofit, p9-gang-replacement, rule-back-to-back-shift-ban, decision-lighting-tied-to-gate]
labels: [pier, contractor-staging]
updated: 2026-05-21
---

# Pier 9

## Current Model

**Pier 9** hosts parallel P9-GATE and P9-GANG workstreams sharing berth 9B staging vocabulary. The **night lighting upgrade** budget and commissioning window stay on **P9-GATE** only — **pier 9 lighting** panels on the gate approach feed Turnstile lane sensors while the gangway apron keeps existing sodium fixtures through Bridgeway install. Marcus Holt enforces a **contractor shift ban** on berth 9B: no **back-to-back shifts** with Turnstile gate crew on the same **pier 9 berth** after gangway delivery landed 2026-05-21. Gangway gets east apron until 1400 then clears for night lighting pull on the gate side.

## Evidence

- `2026-05-12-pier9-lighting-scope` - Key decision: **night lighting upgrade** budget and commissioning stay on **P9-GATE** only, not gangway work; **pier 9 lighting** panels on gate approach feed Turnstile lane sensors; gangway apron stays on existing sodium fixtures through Bridgeway install.
- `2026-05-21-gangway-arrival-day` - Berth 9B schedule gangway AM only with **contractor shift ban** in effect — no **back-to-back shifts** with Turnstile gate crew on the same **pier 9 berth**; gangway gets east apron until 1400 then clears for night lighting pull on gate side.

## Use In Work

- Tag Pier 9 night lighting line items and commissioning under P9-GATE in the Q2 playbook — do not duplicate on P9-GANG cost codes.
- Stagger Turnstile gate crew and Bridgeway gangway crew on berth 9B per Marcus Holt's shift ban; never schedule back-to-back contractor shifts on the same Pier 9 berth.

## Limits

Pier 9 berth rules here cover lighting scope binding and contractor shift sequencing — not fare gate lane counts (four lanes on P9-GATE) or hydraulic hose specs (SAE 100R2AT on P9-GANG). Cal Donner's 2026-06-03 floodlight maintenance mode for gate commissioning is a separate night-ops action.

## Connections

- [[p9-gate-retrofit]] - Gate project that owns Pier 9 night lighting upgrade scope.
- [[p9-gang-replacement]] - Gangway project sharing Pier 9 berth but excluded from lighting budget.
- [[rule-back-to-back-shift-ban]] - Standing rule banning back-to-back gate and gangway shifts on the same berth.
- [[decision-lighting-tied-to-gate]] - Decision binding night lighting upgrade to P9-GATE only.
