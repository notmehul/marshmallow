---
id: rule-back-to-back-shift-ban
insight: Marcus Holt's contractor shift ban prohibits back-to-back shifts between Turnstile gate crew and Bridgeway gangway crew on the same Pier 9 berth.
type: preference
subjects: [marcus-holt, p9-gate-retrofit, p9-gang-replacement]
source_ids: [2026-05-21-gangway-arrival-day]
related_nodes: [marcus-holt, rel-p9-gate-vs-p9-gang, p9-gang-replacement, p9-gate-retrofit]
labels: [contractor-access, pier-9]
updated: 2026-05-21
---

# Back To Back Shift Ban Rule

## Current Model

Marcus Holt enforces a **contractor shift ban** on **Pier 9 berth** 9B: no **back-to-back shifts** between Turnstile Dynamics gate crew and Bridgeway Hoist gangway crew on the same berth day. On **2026-05-21** gangway delivery day, berth 9B was gangway AM only — gate crew could not follow gangway on the same **pier 9 berth** without a gap. If Juno's P9-GATE critical path note conflicts, gate work waits; gangway gets east apron until 1400 then clears for night lighting pull on the gate side.

## Evidence

- `2026-05-21-gangway-arrival-day` - Bridgeway truck rolling for **gangway delivery** on **2026-05-21** at east apron staging; berth 9B schedule gangway AM only with **contractor shift ban** in effect — no **back-to-back shifts** with Turnstile gate crew on the same **pier 9 berth**; critical path note gives gate priority if conflict arises.

## Use In Work

- Sequence P9-GATE and P9-GANG contractor windows on berth 9B with a hard gap — never book Turnstile gate crew immediately after Bridgeway gangway crew (or vice versa) on the same calendar day.
- Check Marcus Holt's berth schedule before assigning Victor Dunn's Pier 9 staging maps to contractor badge batches.

## Limits

This ban covers same-berth shift sequencing on Pier 9 only — not Pier 7 commuter rush cutoffs, gangway load test certificate requirements, or P9-GATE night lighting scope. Kelwick Marine single-contractor plan is superseded and no longer governs shift booking.

## Connections

- [[marcus-holt]] - Master Scheduler who issued and enforces the contractor shift ban.
- [[rel-p9-gate-vs-p9-gang]] - Near-duplicate pair whose overlapping berth access this ban disambiguates.
- [[p9-gang-replacement]] - Gangway replacement workstream subject to the ban on gangway delivery days.
- [[p9-gate-retrofit]] - Gate retrofit workstream that cannot follow gangway crew back-to-back on berth 9B.
