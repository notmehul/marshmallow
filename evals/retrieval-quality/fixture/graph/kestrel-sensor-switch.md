---
id: kestrel-sensor-switch
insight: Copperbeam switched humidity sensors to Kestrel Micro after the Bramblewood units drifted about four percent per month.
type: decision
source_ids: [kestrel-vendor-eval]
related_nodes: [tomas-riel]
labels: [hardware]
updated: 2026-05-20
---

# Kestrel Sensor Switch

## Current Model

Copperbeam switched its humidity sensor vendor to Kestrel Micro. The
Bramblewood units drifted about four percent per month in the greenhouse
environment, while Kestrel Micro samples held calibration through the six-week
soak test.

## Evidence

- `kestrel-vendor-eval` - Bramblewood humidity units drifted about four percent
  per month; Kestrel Micro samples held calibration through the six-week soak
  test.

## Use In Work

- Quote Kestrel Micro parts in any new bill of materials or support answer.

## Limits

Only humidity sensing changed vendors; temperature sensing stays as is.

## Connections

- [[tomas-riel]] - owns the recalibration pass the switch requires.
