# Marshmallow Onboarding

Use this flow after `/marshmallow:start`.

## 1. Explain The Promise

Say:

> Give me a few things that feel like you. I will find the recurring patterns,
> make them available to Claude Code from the first prompt, and tune the skills
> where those patterns matter.

## 2. Ask For Calibration Depth

Ask:

> How deep should we go?
>
> 1. Quick start: give me 3-7 things and I will get you to one useful tuned skill quickly. Recommended.
> 2. Guided calibration: share a broader pack and I will map patterns across several skills.

Recommend quick start unless the user asks for a deeper pass. Keep the rest of
the flow structurally identical in both modes.

## 3. Gather One Taste Pack

Ask for any useful mix of:

- local files or folders
- pasted excerpts
- screenshots and images
- PDFs
- public URLs

Buckets:

1. Things you made: prior products, code, writing, design files, specs, or finished work.
2. Things you like: interfaces, articles, screenshots, repositories, products, or references.
3. Things you reject: outputs, screenshots, patterns, or tools that illustrate what the user does not want.

Treat the buckets as examples, not required filing work. Prefer 3-7 sources for
quick start. Do not ask for an archive migration.

## 4. Stage Evidence In The Inbox

Everything lands under `~/.marshmallow/inbox/` first. Queue one compact
candidate per useful source:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/queue-candidate.py" \
  --kind source \
  --title "<short title>" \
  --source-pointer "<pointer>" \
  --content "<compact reason this may matter and selected evidence>"
```

For pasted reusable insight without an external source, use `--kind insight`.
Do not copy originals or raw session logs into the inbox. Preserve a pointer and
selected evidence.

## 5. Promote Deliberately

Read staged candidates, then use `rg` or `grep` to search existing source cards
and graph nodes before writing durable memory. Promote only what will improve
future work:

- source cards under `~/.marshmallow/sources/` when provenance matters
- reusable alignment insights under `~/.marshmallow/graph/`
- compact projections rendered from those source-backed insights

Use [source-card-template](source-card-template.md) and
[graph-node-template](graph-node-template.md). Create a small set of high-signal
nodes only.

Every node needs source support. Labels are optional and corpus-shaped. Reuse a
label when it helps retrieval, introduce one when the user's work needs it, and
do not force a starter taxonomy. If evidence is weak, contradictory, or
context-dependent, name the tension in the node or ask the user.

## 6. Reveal Patterns And Recommend Skills

Render `GRAPH.md`, scan skills, then surface 3-5 emerging patterns in plain
language. Recommend only judgment-sensitive skills where those patterns can
improve real work. Ask which skills the user wants to edit.

Mention that the full source-backed graph is available at
`~/.marshmallow/GRAPH.md` whenever the user wants to inspect it.

Do not require graph approval before tuning. If the user corrects a pattern,
revise the graph before compiling overlays. If a real tension changes the
overlay, ask one focused question.

## 7. Propose Persistent Alignment

Render compact projections, then preview the user-level Claude Code adapter:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/install-adapter.py"
```

Explain that the adapter adds one replaceable import block to
`~/.claude/CLAUDE.md`. Future sessions use that imported router to search
`~/.marshmallow/projections/` for the smallest relevant personal context.
Neither the full graph nor the raw inbox is loaded into every prompt.

Keep this diff for the rewrite gate. If the user is also tuning skills, include
the adapter and named skill files in one explicit approval request. If the user
wants only the adapter, ask for approval before applying:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/install-adapter.py" --approve
```

## 8. Propose Skill Updates

Recommend only skills where several competent outputs are possible and personal judgment changes the result. Good targets include design, writing, product, architecture, brainstorming, and review workflows.

Avoid deterministic targets such as extraction, migration, linting, security checklists, or tax workflows unless the user explicitly asks.

For each chosen target:

1. draft a pending overlay under `~/.marshmallow/inbox/` using [overlay-template](overlay-template.md)
2. run the dry-run apply command
3. summarize the proposed changes
4. show the diff
5. ask for explicit approval

Apply the pending adapter first when it was included in the same approved list.

## 9. Keep Learning Explicit

After onboarding, respond to:

- “learn from these sources”
- “remember this correction”
- `/marshmallow:learn`
- “show my graph”
- “retune my skills”
- “roll back `<skill>`”

Align persistently through compact projections. Learn selectively. Do not
ingest ordinary sessions, copy raw session logs into the graph, or retune skills
in the background.
