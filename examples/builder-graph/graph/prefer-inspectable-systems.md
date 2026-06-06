---
id: prefer-inspectable-systems
insight: Prefer inspectable local primitives before adding infrastructure.
applies_to: [architecture, product]
source_ids: [made-local-first-tool]
related_nodes: [ask-before-platform]
skills: [architecture-review]
labels: [architecture-default]
---

# Prefer Inspectable Systems

## Rule

Start with inspectable local primitives before adding infrastructure.

## Evidence

- `made-local-first-tool` - prior work explicitly starts from files and earned complexity.

## Use In Skills

- `architecture-review` - prefer reversible file-backed or local designs until
  real usage proves heavier infrastructure is needed.

## Limits

Do not use local primitives when the brief already requires collaboration,
sync, permissions, or scale beyond local files.

## Connections

- [[ask-before-platform]] - this node supplies the default that platform features
  must earn.
