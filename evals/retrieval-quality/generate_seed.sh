#!/usr/bin/env bash
# Regenerate the retrieval-quality seed corpus by driving `cursor-agent -p`
# through the design's staged prompts (docs/plans/2026-07-08-retrieval-quality-eval-design.md).
#
# This is a ONE-TIME generation pipeline with a human in the loop, not CI
# automation. Each stage writes raw model output under seed/stage-out/ first;
# the operator (or the agent driving this script) then splits/repairs the
# staged output into its final location, so every creative artifact stays
# inspectable and every deterministic fix is visible in the diff.
#
# Usage:
#   ./generate_seed.sh bible            # stage 1: universe bible
#   ./generate_seed.sh raw <a> <b>      # stage 2: raw artifacts, ledger rows a..b
#   ./generate_seed.sh sources <a> <b>  # stage 3a: source cards for raw rows a..b
#   ./generate_seed.sh roster           # stage 3b: deterministic node roster (JSON)
#   ./generate_seed.sh nodes <a> <b>    # stage 3c: graph nodes, roster rows a..b (1-based)
#   ./generate_seed.sh navigation       # stage 3d: indexes/home.md + two projections
#   ./generate_seed.sh queries          # stage 4: queries + labels (JSONL)
#   ./generate_seed.sh verify           # adversarial pass: refute every label
#   ./generate_seed.sh split <file>     # split a stage-out file on FILE markers
#
# Human-in-the-loop steps (deliberate, documented in seed/README-generation.md):
#   - review the bible before running later stages;
#   - run `split` on each stage-out file, then repair frontmatter/formatting
#     deterministically (never the creative content);
#   - if an output contradicts the bible, re-run that stage with a corrective
#     note appended via EXTRA_NOTE=...;
#   - re-run `verify` until it reports no confirmed discrepancies.
#
# cursor-agent must run from the repo root (workspace trust); prompts tell it
# to READ inputs from paths instead of inlining them, and to answer on stdout
# with `=== FILE: <relative-path> ===` markers so no stage writes the repo.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EVAL_DIR="$REPO_ROOT/evals/retrieval-quality"
SEED="$EVAL_DIR/seed"
OUT="$SEED/stage-out"
BIBLE="$SEED/bible.md"
EXTRA_NOTE="${EXTRA_NOTE:-}"

mkdir -p "$OUT" "$SEED/raw" "$SEED/sources" "$SEED/graph" "$SEED/indexes" "$SEED/projections"

# All creative prose comes from cursor-agent so the vocabulary distribution is
# not the reviewing agent's own. --mode ask keeps every stage read-only.
# Every call is timeout-wrapped (a hung oversized call once stalled the whole
# pipeline); on timeout, retry once, then split the batch in half.
AGENT_TIMEOUT="${AGENT_TIMEOUT:-240}"
run_agent() { # $1 = output file; prompt on stdin
  local out_file="$1"
  local prompt
  prompt="$(cat)"
  if [ -n "$EXTRA_NOTE" ]; then
    prompt="$prompt

CORRECTIVE NOTE FROM THE OPERATOR (obey this over anything above it conflicts with):
$EXTRA_NOTE"
  fi
  cd "$REPO_ROOT"
  timeout "$AGENT_TIMEOUT" cursor-agent -p --output-format text --mode ask "$prompt" | tee "$out_file"
}

# Vocabulary that must NOT appear in the generated universe: names and core
# domain words from evals/retrieval-quality/fixture/ and examples/, so eval
# vocabulary cannot leak into example-workspace tests.
RESERVED='Copperbeam, Trellis, Verdella, Kestrel, Bramblewood, Sanne, Okafor,
Tomas, Riel, Ines, Marek, Loomline, Meera, Mani, Rowan, Naya, greenhouse,
grower, agritech, humidity sensor. Also avoid the whole startup-fundraising /
investor-relations domain and the greenhouse/agriculture domain entirely.'

FORMAT_RULES='Formatting rules for every file you emit:
- Output each file between markers, exactly:
  === FILE: <relative path> ===
  <file content>
  === END FILE ===
- No prose outside the markers. No code fences around the markers.'

case "${1:-}" in

bible)
  run_agent "$OUT/bible.out" <<PROMPT
You are generating the universe bible for a retrieval-quality evaluation
dataset. It must be fresh fiction. Never use any of these reserved names or
domains: $RESERVED

Invent ONE fictional operator (the person whose working memory this is) and
their working context over exactly eight weeks: 2026-04-20 through 2026-06-12.
Pick a concrete, specific operational domain (physical-world operations with
vendors, sites, schedules, and customers work well). Requirements:

1. PEOPLE: 10 to 14 named people with roles and relationships to the operator.
   At least TWO people must share the same first name but have different last
   names, roles, and projects, so retrieval must disambiguate them.
2. PROJECTS: 4 to 6 named projects. At least TWO projects must have heavily
   overlapping vocabulary (shared jargon, similar component names, adjacent
   codenames) so they act as near-duplicates for lexical retrieval.
3. TIMELINE: week-by-week summary of what happened across the eight weeks.
4. PLANS: three standing plans owned by the operator: one currently ACTIVE,
   one INACTIVE (superseded mid-timeline, say why), and one that the operator
   MANUALLY EDITED after it was written so it has drifted from its source
   notes (say what drifted).
5. PLANTED FACTS: enumerate exactly 48 ground-truth facts with IDs F01..F48.
   Each fact entry must give:
   - claim: one precise sentence (a decision, a number, an owner, a date, a
     rule, a relationship);
   - anchors: 2 to 4 short lexical anchor phrases that raw artifacts and graph
     notes will literally contain when stating this fact. For any multi-word
     coined term include BOTH the hyphenated and the spaced spelling as two
     separate anchors (e.g. "cold-chain audit" and "cold chain audit").
     Anchors must be distinctive (not generic words), lowercase.
   - where: which week(s) and which people/projects it involves.
   Spread facts across all projects and weeks. Make several facts live ONLY in
   the near-duplicate project pair so confusion is possible.
6. CONTRADICTION: pick one fact (name its ID) that an early artifact states
   WRONG (give the wrong value and the week it appears); a later artifact
   corrects it (give the week). Ground truth is the corrected value.
7. ARTIFACT LEDGER: a numbered table of exactly 40 raw artifacts, rows R01 to
   R40, dated across the eight weeks (workdays only). Each row: date
   (YYYY-MM-DD), kind (meeting-notes | chat-log | email | session-fragment),
   slug (lowercase-hyphen-case, no date in it), people present, fact IDs this
   artifact must plant (every fact F01..F48 must be planted by at least one
   row; the contradiction's wrong statement and its correction get their own
   rows), and one line of what else happens in it (drift, small talk, other
   threads).

Write it as one well-structured markdown document. Output ONLY the document
between these exact markers:
=== FILE: seed/bible.md ===
...content...
=== END FILE ===
PROMPT
  ;;

raw)
  ROWS="rows R${2:?row start} to R${3:?row end}"
  run_agent "$OUT/raw-$2-$3.out" <<PROMPT
Read the universe bible at evals/retrieval-quality/seed/bible.md, especially
the ARTIFACT LEDGER and the PLANTED FACTS list. Also list the files already in
evals/retrieval-quality/seed/raw/ to stay consistent with anything generated
so far (do not repeat their exact phrasings).

Write the raw artifacts for ledger $ROWS, one file per row, named
seed/raw/<date>-<slug>.md (date from the ledger row).

Rules:
- Each artifact is realistic working material of its ledger kind: meeting
  notes with attendees and bullets, chat logs with timestamps and handles,
  emails with From/To/Subject, session fragments as terse work logs.
- Every fact ID assigned to the row must be planted: state the fact naturally
  and include at least one of its lexical anchor phrases VERBATIM. Do not
  label facts or mention fact IDs in the artifact text.
- Natural messiness: occasional typos, nicknames and first-name-only
  references, topic drift, unrelated small threads, inconsistent formatting.
  People who share a first name are sometimes referred to by first name only.
- If the ledger marks a row as the WRONG statement of the contradiction fact,
  state the wrong value confidently. If it is the correction row, correct it
  explicitly ("turns out...", "correction:").
- Stay strictly consistent with the bible: names, dates, numbers, ownership.
- 15 to 40 lines per artifact.
- Never use the reserved names/domains: $RESERVED

$FORMAT_RULES
PROMPT
  ;;

sources)
  ROWS="rows R${2:?row start} to R${3:?row end}"
  run_agent "$OUT/sources-$2-$3.out" <<PROMPT
Read the bible at evals/retrieval-quality/seed/bible.md (ARTIFACT LEDGER +
PLANTED FACTS), then read the raw artifacts in evals/retrieval-quality/seed/raw/
for ledger $ROWS (files are named <date>-<slug>.md).

For each of those raw artifacts emit one Marshmallow source card,
seed/sources/<same-stem-as-raw-file>.md, in exactly this shape:

---
id: <file stem, lowercase hyphen-case>
pointer: raw/<raw file name>
captured: <artifact date>T00:00:00Z
summary: <one specific sentence: what this artifact is and why it matters>
labels: [seed]
---

# <Title Case Name>

## Useful Excerpts

- <verbatim or near-verbatim quote of each planted fact line from the
  artifact, keeping its lexical anchor phrases exactly>
- <2 to 5 bullets total; include the most decision-relevant lines>

Rules: excerpts must keep anchor phrases verbatim; summary must be specific,
not generic; do not invent content that is not in the artifact.

$FORMAT_RULES
PROMPT
  ;;

# The roster (node ids, types, fact assignments, backing sources) is DERIVED
# DETERMINISTICALLY from the bible's own tables: every person/project/vendor/
# site gets an entity node, every planted fact a decision/preference node,
# plus relationship and plan nodes. IDs are slugs of cursor-agent-authored
# names; fact->source mapping comes from the bible's artifact ledger. The
# creative prose (insights, bodies) still comes from cursor-agent in the
# `nodes` stage. This replaced a single-call LLM "manifest" stage that hung on
# prompt size.
roster)
  python3 - "$SEED" <<'PY'
import json, re, sys
from pathlib import Path

seed = Path(sys.argv[1])
bible = (seed / "bible.md").read_text(encoding="utf-8")

facts = {}
for m in re.finditer(r"\| \*\*(F\d+)\*\* \| (.+?) \| (.+?) \|", bible):
    fid, claim, anchors = m.groups()
    facts[fid] = {
        "claim": re.sub(r"\*\*", "", claim).strip(),
        "anchors": re.findall(r"`([^`]+)`", anchors),
    }

# fact id -> source card ids (from the artifact ledger rows that plant it)
fact_sources: dict[str, list[str]] = {f: [] for f in facts}
for m in re.finditer(
    r"\| \*\*(R\d+)\*\* \| (\d{4}-\d{2}-\d{2}) \| [-\w]+ \| ([-\w]+) \| .+? \| (.+?) \|", bible
):
    _, date, slug, fids = m.groups()
    for fid in re.findall(r"F\d+", fids):
        fact_sources[fid].append(f"{date}-{slug}")

E, D, P, R, PL = "entity", "decision", "preference", "relationship", "plan"
# (id, type, facts, extra_sources, status)
SPEC = [
    ("juno-castillo", E, ["F01"]), ("elena-vasquez", E, ["F11"]),
    ("elena-crane", E, ["F18"]), ("marcus-holt", E, ["F20"]),
    ("priya-nandakumar", E, ["F14"]), ("derek-blunt", E, ["F31"]),
    ("fatima-okonkwo", E, ["F29"]), ("glenn-wexler", E, ["F21"]),
    ("hana-suzuki", E, ["F10"]), ("victor-hale", E, ["F12"]),
    ("victor-dunn", E, ["F07"]), ("cal-donner", E, ["F28"]),
    ("jessamine-lee", E, ["F26"]),
    ("p9-gate-retrofit", E, ["F02", "F23"]), ("p9-gang-replacement", E, ["F03", "F22"]),
    ("sg-refit", E, ["F11", "F36"]), ("hp-migrate", E, ["F08", "F45"]),
    ("ssb-drill", E, ["F15", "F33"]), ("p7-ramp", E, ["F18", "F19"]),
    ("harborline-regional-ferry", E, [], ["2026-04-20-q2-kickoff-terminal"]),
    ("kelwick-marine", E, ["F06"]), ("turnstile-dynamics", E, ["F04", "F24"]),
    ("bridgeway-hoist", E, ["F05", "F25"]), ("surfside-condos", E, ["F40"]),
    ("pier-3", E, ["F09", "F35"]), ("pier-5", E, ["F20"]),
    ("pier-7", E, ["F38", "F47"]), ("pier-9", E, ["F32", "F34"]),
    ("mv-seaglass", E, ["F48"]), ("harborpass-2-0", E, ["F08", "F38"]),
    ("berth-9b-staging", E, [], ["2026-04-24-pier9-dual-scope-intro", "2026-05-07-pier9-staging-intrusion"]),
    ("pier-9-night-lighting", E, ["F32"]), ("drydock-berth-4", E, ["F13"]),
    ("simulation-weekends", E, ["F15"]),
    ("plan-q2-terminal-readiness", PL, ["F01"], None, "active"),
    ("plan-pier9-single-contractor", PL, ["F06", "F07"], None, "inactive"),
    ("plan-storm-surge-coverage-matrix", PL, ["F16", "F17"], None, "drifted"),
    ("decision-vendor-split", D, ["F04", "F05"]),
    ("decision-supersede-single-contractor", D, ["F07"]),
    ("decision-crane-booking-corrected", D, ["F13"]),
    ("decision-drydock-window", D, ["F11"]),
    ("decision-gate-delivery-slip", D, ["F24"]),
    ("decision-gangway-delivery-hold", D, ["F25"]),
    ("decision-change-order-cap", D, ["F21"]),
    ("decision-reject-gangway-contingency", D, ["F37"]),
    ("decision-critical-path-p9-gate", D, ["F41"]),
    ("decision-friday-harbor-diversion", D, ["F20"]),
    ("decision-hp-golive-target", D, ["F08"]),
    ("decision-rollback-token-gate", D, ["F27"]),
    ("decision-legacy-reader-sunset", D, ["F38"]),
    ("decision-outage-notice-window", D, ["F26"]),
    ("decision-lighting-tied-to-gate", D, ["F32"]),
    ("decision-hose-spec-r2at", D, ["F42"]),
    ("decision-gate-lane-count", D, ["F23"]),
    ("decision-grating-spec-6061", D, ["F18"]),
    ("decision-fuel-purge-adoption", D, ["F30"]),
    ("decision-mobilization-discount", D, ["F31"]),
    ("decision-badge-batch-p9-gate", D, ["F29"]),
    ("decision-sea-trial-date", D, ["F36"]),
    ("decision-revenue-return", D, ["F48"]),
    ("decision-ramp-handover", D, ["F47"]),
    ("decision-float-switch-replacement", D, ["F35"]),
    ("decision-dive-overtime", D, ["F10"]),
    ("decision-pier3-berth-closure", D, ["F09"]),
    ("decision-gangway-mockup-inspection", D, ["F39", "F22"]),
    ("decision-drill-weekends", D, ["F15"]),
    ("decision-after-action-review", D, ["F46"]),
    ("decision-highwater-codename", D, ["F33"]),
    ("decision-floodlight-maintenance", D, ["F44"]),
    ("decision-golive-completion", D, ["F45"]),
    ("decision-matrix-manual-edit", D, ["F16"]),
    ("rule-life-vest-checks", P, ["F14"]),
    ("rule-commuter-rush-cutoff", P, ["F19"]),
    ("rule-back-to-back-shift-ban", P, ["F34"]),
    ("rule-load-test-certificate", P, ["F43"]),
    ("rule-thrust-bearing-before-hull", P, ["F12"]),
    ("rule-coverage-source-notes", P, ["F17"]),
    ("rule-quiet-hours-p7", P, ["F40"]),
    ("rule-contractor-staging-access", P, ["F28"]),
    ("rule-passenger-notice-approval", P, ["F26"]),
    ("rule-change-order-routing", P, ["F21"]),
    ("rule-badge-deactivation-closeout", P, [], ["2026-06-08-q2-closeout-preview"]),
    ("rule-codename-disambiguation", P, [], ["2026-04-20-q2-kickoff-terminal", "2026-04-24-pier9-dual-scope-intro"]),
    ("rel-juno-elena-vasquez", R, [], ["2026-05-18-drydock-window-opens"]),
    ("rel-juno-victor-dunn", R, [], ["2026-04-20-q2-kickoff-terminal", "2026-05-13-critical-path-declaration"]),
    ("rel-juno-marcus-holt", R, [], ["2026-05-15-friday-harbor-diversion"]),
    ("rel-derek-turnstile-dynamics", R, [], ["2026-04-27-vendor-split-announcement", "2026-05-22-gate-delivery-slip"]),
    ("rel-derek-bridgeway-hoist", R, [], ["2026-05-05-bridgeway-discount-confirm", "2026-05-14-gangway-delivery-hold"]),
    ("rel-elena-crane-p7-ramp", R, [], ["2026-04-30-p7-grating-spec", "2026-06-10-pier7-ramp-handover"]),
    ("rel-victor-hale-sg-refit", R, [], ["2026-04-29-seaglass-crane-prelim", "2026-06-05-seaglass-sea-trial"]),
    ("rel-fatima-harborpass", R, [], ["2026-05-26-rollback-token-gate", "2026-06-02-harborpass-golive"]),
    ("rel-priya-ssb-drill", R, [], ["2026-05-25-highwater-drill-prep", "2026-06-11-highwater-after-action"]),
    ("rel-hana-pier-3", R, [], ["2026-04-21-pier3-berth-hold", "2026-04-28-pier3-switch-complete"]),
    ("rel-cal-night-operations", R, [], ["2026-05-07-pier9-staging-intrusion", "2026-06-03-pier9-floodlight-maintenance"]),
    ("rel-jessamine-passenger-comms", R, [], ["2026-06-01-harborpass-outage-notice-draft"]),
    ("rel-glenn-procurement", R, [], ["2026-05-04-procurement-week-open", "2026-06-08-q2-closeout-preview"]),
    ("rel-elena-vasquez-vs-crane", R, [], ["2026-05-18-drydock-window-opens", "2026-05-27-surfside-noise-escalation"]),
    ("rel-victor-hale-vs-dunn", R, [], ["2026-04-29-seaglass-crane-prelim", "2026-05-20-gangway-mockup-inspection"]),
    ("rel-p9-gate-vs-p9-gang", R, [], ["2026-04-24-pier9-dual-scope-intro", "2026-05-08-gangway-hose-spec"]),
    ("rel-juno-priya-drill-alignment", R, [], ["2026-05-29-coverage-matrix-drift"]),
]

roster = []
for row in SPEC:
    node_id, node_type, fact_ids = row[0], row[1], row[2]
    extra = row[3] if len(row) > 3 and row[3] else []
    status = row[4] if len(row) > 4 else ""
    source_ids: list[str] = list(extra)
    for fid in fact_ids:
        for sid in fact_sources.get(fid, []):
            if sid not in source_ids:
                source_ids.append(sid)
    entry = {
        "id": node_id,
        "type": node_type,
        "facts": [
            {"id": fid, "claim": facts[fid]["claim"], "anchors": facts[fid]["anchors"]}
            for fid in fact_ids
        ],
        "source_ids": source_ids[:3],
    }
    if status:
        entry["status"] = status
    roster.append(entry)

covered = {f["id"] for entry in roster for f in entry["facts"]}
missing = sorted(set(facts) - covered)
if missing:
    sys.exit(f"facts not covered by any roster node: {missing}")
existing = {p.stem for p in (seed / "sources").glob("*.md")}
bad = sorted({s for entry in roster for s in entry["source_ids"]} - existing)
if bad:
    sys.exit(f"roster references missing source cards: {bad}")
out = seed / "stage-out" / "roster.json"
out.write_text(json.dumps(roster, indent=1), encoding="utf-8")
print(f"wrote {out} ({len(roster)} nodes, all {len(facts)} facts covered)")
PY
  ;;

nodes)
  A="${2:?roster row start (1-based)}"; B="${3:?roster row end}"
  BATCH_SPEC="$(python3 - "$SEED" "$A" "$B" <<'PY'
import json, sys
from pathlib import Path
seed = Path(sys.argv[1]); a, b = int(sys.argv[2]), int(sys.argv[3])
roster = json.loads((seed / "stage-out" / "roster.json").read_text(encoding="utf-8"))
batch = roster[a - 1 : b]
print("ALL NODE IDS (the only ids allowed in related_nodes):")
print(", ".join(entry["id"] for entry in roster))
print()
print("NODES TO WRITE IN THIS BATCH:")
print(json.dumps(batch, indent=1))
PY
)"
  run_agent "$OUT/nodes-$A-$B.out" <<PROMPT
Read the bible at evals/retrieval-quality/seed/bible.md. You are writing graph
nodes for a Marshmallow workspace derived from it. Below is the batch spec:
for each node you get its fixed id, type, backing source card ids (files in
evals/retrieval-quality/seed/sources/ - read the ones you need for exact
wording), and the planted facts it must state (claim + anchor phrases).

$BATCH_SPEC

Write one file per node in this batch, seed/graph/<id>.md, exactly this shape:

---
id: <the fixed id from the batch spec>
insight: <ONE LINE, one sentence, under 300 chars, stating the node's core
  claim; it MUST literally contain at least one lexical anchor phrase of every
  fact listed for this node; never wrap it onto a second line>
type: <the type from the batch spec>
subjects: [<lowercase-hyphen-case person/project slugs, optional>]
source_ids: [<exactly the source_ids from the batch spec>]
related_nodes: [<0-4 ids chosen ONLY from the ALL NODE IDS list above>]
labels: [<1-2 lowercase-hyphen-case topical labels>]
updated: <a plausible YYYY-MM-DD inside the eight weeks>
---

# <Title Case Name>

## Current Model

<2-5 sentences. Must restate every assigned fact, keeping at least one anchor
phrase per fact verbatim. For multi-word coined terms, use the hyphenated
spelling here and the spaced spelling somewhere else in the node (or vice
versa) so both variants appear in the file.>

## Evidence

- \`<source-id>\` - <the specific detail from that source that backs this
  node; be concrete, quote numbers and names; at least 90 characters of real
  content across the section>

## Use In Work

- <one or two bullets: what an agent should do differently because of this>

## Limits

<one or two sentences: where this does not apply or what is uncertain>

## Connections

- [[<related-node-id>]] - <why it relates> (one line per related node; EVERY
  id in related_nodes must appear as an [[id]] link here; omit the whole
  section only if related_nodes is empty)

Extra rules:
- For plan nodes (type: plan) copy the "status" value from the batch spec into
  the frontmatter after "type:", and add "skills: [planning]". Their bodies
  must read like standing plans (steps, owners, checkpoints). The drifted one
  must note it was manually edited after its sources and how it now differs;
  the inactive one must name what superseded it.
- The contradiction fact's node states the CORRECTED value and its Limits
  section mentions that an earlier note had it wrong.
- Never use the reserved names/domains: $RESERVED

$FORMAT_RULES
PROMPT
  ;;

queries)
  run_agent "$OUT/queries.out" <<PROMPT
Read the bible at evals/retrieval-quality/seed/bible.md (PLANTED FACTS), the
node roster at evals/retrieval-quality/seed/stage-out/roster.json (it maps
node ids to the facts they state), and skim a few graph nodes in
evals/retrieval-quality/seed/graph/ to see how facts are phrased there.

Write the eval query set: one JSON object per line (JSONL), 40 direct queries
then 10 negative queries.

DIRECT query line:
{"id": "q<NN>-<short-slug>", "text": "<natural question the operator would
ask>", "paraphrase": "<same intent, deliberately sharing as FEW content words
with the graph node text as possible - use synonyms, drop the coined terms>",
"type": "direct", "facts": [{"claim": "<the planted fact claim>", "aliases":
["<anchor>", ...]}], "marshmallow": {"expected_node_ids": ["<node id>", ...]}}

Rules for direct queries:
- Walk the planted facts: cover at least 38 distinct fact IDs across the 40
  queries; a query may carry 1 or 2 facts.
- aliases: copy the fact's lexical anchor phrases from the bible, lowercase.
  Include BOTH punctuation variants of any multi-word coined term ("cold-chain"
  AND "cold chain"). Every alias must be a phrase that actually appears in the
  graph nodes that state the fact.
- expected_node_ids: the roster node ids that state the fact (1-3 ids).
- Several queries must target the near-duplicate project pair and the
  shared-first-name people, phrased so the wrong twin is a plausible hit.
- "facts" must never be empty for direct queries.

NEGATIVE query line (no facts field, or "facts": []):
{"id": "q<NN>-<slug>", "text": "...", "paraphrase": "...", "type": "negative",
"facts": []}
- 5 ZERO-RESULT probes: plausible operator questions whose EVERY content word
  is absent from the whole universe (avoid filler words like "the", "what",
  "is", "for", "how" entirely - write them telegraphic, e.g. "Quarterly
  payroll ledger reconciliation cadence?"). Topics never planted anywhere.
- 5 LEXICAL-JUNK traps: reuse real entity/project names from the universe but
  ask something that was never planted or discussed, so retrieval returns
  confident junk (e.g. asking about a person's salary, a project's patent
  filing - topics with zero coverage).

Output ONLY:
=== FILE: evals/retrieval-quality/queries.jsonl ===
<50 JSONL lines>
=== END FILE ===
PROMPT
  ;;

navigation)
  run_agent "$OUT/navigation.out" <<PROMPT
Read the bible at evals/retrieval-quality/seed/bible.md and the node roster at
evals/retrieval-quality/seed/stage-out/roster.json (all graph node ids).

Write three navigation files for this Marshmallow workspace.

1. seed/indexes/home.md - the home index:
---
id: home
title: <short universe-appropriate title>
graph_ids: [<15-20 of the most load-bearing node ids: the operator, the six
  projects, the three plan- nodes, the twin-disambiguation relationship nodes,
  and the highest-stakes decisions>]
labels: [home]
updated: 2026-06-12
---

# <Title>

## Start Here

- [[<node-id>]] - <one specific line on why to load it> (one bullet per id in
  graph_ids, same order)

## Notes

<2-3 lines: when to use this index.>

2 and 3. Two projections (recall packets), seed/projections/<id>.md each:
---
id: <lowercase-hyphen-case id>
title: <title>
task: <one sentence: the concrete recurring task this packet prepares an agent for>
graph_ids: [<4-6 node ids from the roster>]
labels: [recall-packet]
updated: 2026-06-12
---

# <Title>

## Use For

<one or two lines>

## Load First

- [[<node-id>]] - <why> (one per graph_id, same order)

## Working Context

<3-5 lines of operator-voice guidance for the task, consistent with the bible>

Pick the two projection tasks yourself: the two briefs this operator would
most plausibly reuse (e.g. a weekly cross-project status ritual, a
commissioning/closeout conversation). Never use the reserved names/domains:
$RESERVED

$FORMAT_RULES
PROMPT
  ;;

verify)
  run_agent "$OUT/verify-$(date +%Y%m%d-%H%M%S).out" <<PROMPT
You are an adversarial label auditor. Your job is to REFUTE labels, not to
confirm them. Read every raw artifact in evals/retrieval-quality/seed/raw/
and every line of evals/retrieval-quality/queries.jsonl (also consult
evals/retrieval-quality/seed/bible.md only to understand intent - the raw
artifacts are the evidence that counts).

For EVERY query, attack the label:
1. DIRECT queries: is each fact's claim actually answerable from the raw
   artifacts alone? Quote the artifact line(s) that answer it, or declare
   UNSUPPORTED. Is any claim contradicted by a LATER artifact (the corrected
   value wins)?
2. ALIASES: for each fact, do the aliases actually appear verbatim (after
   lowercasing) in the raw artifacts and read as anchors for THIS fact? Flag
   aliases that are too generic (would match unrelated artifacts), missing
   punctuation variants, or absent from the material.
3. EXPECTED NODES: do the expected_node_ids (files in
   evals/retrieval-quality/seed/graph/) actually contain every alias needed
   to score the fact? Flag nodes that miss the anchor phrases.
4. NEGATIVES: is any negative query accidentally answerable from the raw
   artifacts? For zero-result probes, list ANY content word of the query that
   appears anywhere in seed/graph/, seed/indexes/, or seed/projections/.

Output a markdown report: one section per query WITH a problem (skip clean
ones, but end with a one-line count of clean queries), each problem tagged
[UNSUPPORTED] [BAD-ALIAS] [MISSING-VARIANT] [NODE-MISSING-ANCHOR]
[NEGATIVE-ANSWERABLE] [NEGATIVE-TOKEN-HIT] [CONTRADICTION] plus the evidence
quote. Finish with "## Verdict" - either "CLEAN" or the list of query ids
needing fixes.

Output ONLY:
=== FILE: seed/verify-report.md ===
...report...
=== END FILE ===
PROMPT
  ;;

split)
  python3 - "$EVAL_DIR" "${2:?stage-out file to split}" <<'PY'
import re, sys
from pathlib import Path

eval_dir = Path(sys.argv[1])
text = Path(sys.argv[2]).read_text(encoding="utf-8")
blocks = re.findall(r"^=== FILE: (.+?) ===\n(.*?)\n?=== END FILE ===", text, re.M | re.S)
if not blocks:
    # Single-file stages (bible) end without an END marker sometimes; accept
    # one FILE marker followed by everything to EOF.
    single = re.search(r"^=== FILE: (.+?) ===\n(.*)$", text, re.M | re.S)
    blocks = [single.groups()] if single else []
if not blocks:
    sys.exit("no FILE markers found")
for rel, content in blocks:
    rel = rel.strip()
    if rel.startswith("evals/retrieval-quality/"):
        rel = rel[len("evals/retrieval-quality/"):]
    dest = (eval_dir / rel).resolve()
    if eval_dir.resolve() not in dest.parents:
        sys.exit(f"refusing to write outside the eval dir: {rel}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content.rstrip() + "\n", encoding="utf-8")
    print(f"wrote {dest}")
PY
  ;;

*)
  grep -E '^#( |$)' "$0" | sed 's/^# \{0,1\}//'
  exit 1
  ;;
esac
