---
id: retention-proof-plan
insight: Use the retention proof plan as the operational hub until its revisit condition is met.
type: plan
applies_to: [retention, operating-plan]
source_ids: [source-example]
related_nodes: [company-context, founder-context, retention-decision]
managed: true
status: active
labels: [plan]
updated: YYYY-MM-DD
---

# Retention Proof Plan

Write the plan in whatever form fits the work. Marshmallow does not require
milestones, sequencing, branching, checklists, or prescribed headings.

The frontmatter makes this node discoverable as an active operational hub. Keep
`insight`, `applies_to`, and `related_nodes` specific enough to identify its
scope; recall deliberately does not activate a plan from incidental words in
its free-form body. After the first managed transaction, Marshmallow adds
`revision_source_id` and a full UTC `updated` timestamp. Do not author that
lineage field by hand; `maintain` creates the immutable receipt and sets it.
