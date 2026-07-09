---
id: rule-change-order-routing
insight: Route P9-GATE change orders through Glenn Wexler under the change order cap of $18400 without VP sign-off on p9-gate WBS spend.
type: preference
subjects: [glenn-wexler, p9-gate-retrofit]
source_ids: [2026-05-04-procurement-week-open, 2026-06-08-q2-closeout-preview]
related_nodes: [glenn-wexler, decision-change-order-cap, p9-gate-retrofit, decision-reject-gangway-contingency]
labels: [procurement, change-orders]
updated: 2026-06-08
---

# Change Order Routing Rule

## Current Model

Glenn Wexler capped **P9-GATE** change orders at **$18400** without VP sign-off during procurement week open on 2026-05-04. The standing **change order cap** routes anything above Glenn's desk, with Elena Vasquez looped if fleet-adjacent. Juno must keep Turnstile Dynamics mobilization on the gate PO — not the gangway track — and Glenn warned against burying gangway contingency inside gate change orders. At Q2 closeout preview Glenn reaffirmed the **p9-gate** ceiling held after the Turnstile delivery slip; night lighting Victor tied to gate side counts if it sits on the P9-GATE WBS.

## Evidence

- `2026-05-04-procurement-week-open` - Glenn Wexler sets **change order cap** for **p9-gate** at **$18400** without VP sign-off; anything above routes to his desk plus Elena Vasquez if fleet-adjacent; Glenn confirms cap covers night lighting on P9-GATE WBS and warns against burying gangway contingency in gate change orders; Juno confirms Turnstile mobilization stays on gate PO.
- `2026-06-08-q2-closeout-preview` - Glenn reaffirms original **change order cap** on **p9-gate** remains **$18400** without VP sign-off and reports the project stayed inside that ceiling after Turnstile gate delivery landed May 28; duplicate gangway contingency denial archived for audit.

## Use In Work

- Route all P9-GATE change orders through Glenn Wexler and hold them under **$18400** unless VP sign-off is obtained — escalate fleet-adjacent items to Elena Vasquez alongside Glenn.
- Keep P9-GANG gangway contingency and Bridgeway spend on separate cost codes; never fold gangway envelopes into gate change orders under this cap.

## Limits

This routing rule governs P9-GATE WBS change orders only — P9-GANG has a separate PO track and Glenn's rejected **$62000 contingency** gangway envelope follows different approval logic. Mobilization discounts on Bridgeway Hoist are logged under P9-GANG, not this cap.

## Connections

- [[glenn-wexler]] - Procurement Finance Controller who set the cap and owns the routing desk.
- [[decision-change-order-cap]] - Decision node recording Glenn's $18400 ceiling establishment and reaffirmation.
- [[p9-gate-retrofit]] - Gate project whose change orders must follow this routing path.
- [[decision-reject-gangway-contingency]] - Related rejection showing gangway contingency must not route through the gate cap.
