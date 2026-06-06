---
id: ask-before-platform
insight: Ask whether a platform feature has earned its complexity before adding it.
applies_to: [architecture, product]
source_ids: [made-local-first-tool]
related_nodes: [prefer-inspectable-systems]
skills: [architecture-review, product-spec]
labels: [complexity-boundary]
---

# Ask Before Platform

## Rule

Ask what repeated pain earned a platform feature before adding databases,
background workers, dashboards, or broad integration surfaces.

## Evidence

- `made-local-first-tool` - prior work treats infrastructure as earned complexity.

## Use In Skills

- `architecture-review` - challenge platform surfaces before local primitives
  have failed.
- `product-spec` - keep early specs focused on reversible user value.

## Limits

Do not block infrastructure that is already required by the user's product,
security, compliance, or integration constraints.

## Connections

- [[prefer-inspectable-systems]] - this is the architectural default behind the
  ask-before-platform rule.
