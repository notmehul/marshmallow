---
id: harborline-regional-ferry
insight: HarborLine Regional Ferry operates multi-pier commuter and tourist ferry terminal readiness across four active piers and six vessels in Q2 2026.
type: entity
subjects: [harborline-regional-ferry]
source_ids: [2026-04-20-q2-kickoff-terminal]
related_nodes: [juno-castillo, plan-q2-terminal-readiness, pier-9, pier-7]
labels: [operator, ferry]
updated: 2026-04-20
---

# HarborLine Regional Ferry

## Current Model

HarborLine Regional Ferry is the multi-pier passenger ferry operator running commuter and tourist routes across four active piers and six vessels during the Q2 2026 evaluation window. Week-1 kickoff under Juno Castillo activated the Q2 Terminal Readiness Playbook to coordinate berth scheduling, vessel refit windows, contractor access, safety drills, and fare-system cutovers. Spring surge construction spans Pier 9 gate and gangway retrofits, MV Seaglass refit, HarborPass 2.0 migration, storm surge barrier drills, and Pier 7 accessibility ramp installation.

## Evidence

- `2026-04-20-q2-kickoff-terminal` - Week-1 kickoff meeting for HarborLine terminal operations: Juno Castillo activates the Q2 Terminal Readiness Playbook, introduces P9-GATE and P9-GANG Pier 9 workstreams under Victor Dunn's single-contractor plan, and frames spring surge readiness across active piers and fleet sailings.

## Use In Work

- Frame all Q2 terminal readiness, cross-pier scheduling, and passenger-disruption coordination as HarborLine Regional Ferry operations governed by Juno's Q2 playbook.
- Treat pier-specific projects (P9-GATE, P9-GANG, P7-RAMP, SG-REFIT, HP-MIGRATE, SSB-DRILL) as workstreams within this operator context rather than standalone entities.

## Limits

This node captures the operator entity only — it does not hold planted fact anchors for specific dates, vendors, or technical specs. Retrieve project-level nodes for codenames, delivery slips, and approval decisions.

## Connections

- [[juno-castillo]] - Senior Terminal Operations Manager who runs day-to-day readiness for HarborLine.
- [[plan-q2-terminal-readiness]] - Active cross-pier playbook governing the Q2 evaluation window.
- [[pier-9]] - Primary construction pier for parallel gate and gangway retrofits.
- [[pier-7]] - Pier hosting accessibility ramp install and legacy HarborPass reader sunset.
