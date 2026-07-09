---
id: rule-codename-disambiguation
insight: Use P9-GATE and P9-GANG codenames in the terminal readiness playbook tracker to separate pier-9 gate retrofit fare-lane work from pier-9 gangway replacement hydraulic scope.
type: preference
subjects: [p9-gate-retrofit, p9-gang-replacement, juno-castillo]
source_ids: [2026-04-20-q2-kickoff-terminal, 2026-04-24-pier9-dual-scope-intro]
related_nodes: [p9-gate-retrofit, p9-gang-replacement, rel-p9-gate-vs-p9-gang, plan-q2-terminal-readiness]
labels: [codenames, pier-9]
updated: 2026-04-24
---

# Codename Disambiguation Rule

## Current Model

HarborLine's Pier 9 workstreams require explicit codenames because **Pier-9 Gate Retrofit** and **Pier-9 Gangway Replacement** share berth, staging, and hydraulic vocabulary. **P9-GATE** tracks fare lanes, gate automation, and night lighting circuit upgrades; **P9-GANG** tracks hydraulic gangway modules, load test hooks, and hose specs. Juno reminded the team at the dual-scope intro that **P9-GATE** and **P9-GANG** codenames are live in the **terminal readiness playbook** tracker — retrieval must use codename, vendor name, or component (gate lane vs gangway width) rather than generic "pier 9 retrofit" language. Both scopes still rolled up under Kelwick Marine on paper at kickoff but were clearly diverging by week 1.

## Evidence

- `2026-04-20-q2-kickoff-terminal` - Juno activates **Q2 Terminal Readiness Playbook**; **Pier-9 Gate Retrofit** tracks as **P9-GATE** (fare lanes, Turnstile-adjacent scope TBD) and **Pier-9 Gangway Replacement** as **P9-GANG** (hydraulic gangway, staging overlap with gate side); both still under Kelwick Marine **Pier 9 Single-Contractor Plan** until procurement splits vendors.
- `2026-04-24-pier9-dual-scope-intro` - Victor Dunn splits whiteboard into gate retrofit column (four fare lanes preliminary, gate automation, night lighting) and gangway replacement column (hydraulic gangway module, load test hooks, hose spec TBD); Juno confirms **P9-GATE** and **P9-GANG** codenames live in **terminal readiness playbook** tracker despite single Kelwick contractor on paper.

## Use In Work

- Always specify **P9-GATE** or **P9-GANG** (or vendor Turnstile Dynamics vs Bridgeway Hoist) when retrieving Pier 9 artifacts — never rely on "pier 9 retrofit" or "berth closure" alone.
- Log new Pier 9 scope items in the terminal readiness playbook under the correct codename before assigning badges, change orders, or berth windows.

## Limits

This rule disambiguates Pier 9 infrastructure codenames only — not SSB-DRILL's "Highwater" radio call sign, Elena Vasquez vs Elena Crane, or Victor Hale vs Victor Dunn. After 2026-05-06 vendor split, Kelwick Marine paperwork is superseded even though kickoff sources still name it.

## Connections

- [[p9-gate-retrofit]] - Gate automation workstream identified by P9-GATE codename.
- [[p9-gang-replacement]] - Gangway replacement workstream identified by P9-GANG codename.
- [[rel-p9-gate-vs-p9-gang]] - Relationship node capturing near-duplicate overlap between the two Pier 9 scopes.
- [[plan-q2-terminal-readiness]] - Playbook tracker where both codenames are logged and maintained.
