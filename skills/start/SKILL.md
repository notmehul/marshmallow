---
name: start
description: Build or update a source-backed personal alignment layer, install the persistent Claude Code adapter with approval, inspect builder taste and judgment, tune skills with reviewable overlays, show the graph, or roll back an approved tune. Use when the user runs /marshmallow:start or asks Marshmallow to personalize Claude Code, show their graph, retune skills, or roll back a tuned skill.
license: MIT
compatibility: Designed for Claude Code with Python 3.10+ available locally.
---

# Marshmallow

Give Marshmallow the things the user makes, likes, and rejects. Build an
inspectable personal graph, compile compact runtime projections, install the
persistent Claude Code adapter with approval, then tune selected agent skills
where personal judgment changes useful defaults.

Keep the system simple:

- use plain Markdown files under `~/.marshmallow/`
- preserve source pointers and selected excerpts, not copied originals
- use files plus `rg` or `grep` as the retrieval layer
- use the host's existing tools to inspect local files, images, PDFs, pasted text, and user-provided URLs
- never rewrite a user skill without showing a summary and diff, then receiving explicit approval
- never load the full graph into tuned skills

Read [onboarding](../../references/onboarding.md) for the detailed flow. Use the templates in `../../references/` when creating source cards, graph nodes, and overlays.

## Start Or Learn

1. Run:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py"
   ```

2. For a first run, ask how much detail the user wants:
   - Quick start: use a small taste pack and get to one useful tuned skill quickly.
   - Guided calibration: use a broader source pack and consider several skills.

   Recommend quick start unless the user asks for a deeper pass. Do not turn
   this into a wizard.

3. Ask for one loose taste pack. Explain that useful sources include things
   they made, things they like, and things they reject, but do not require the
   user to sort every source into buckets before sharing it.

4. Accept paths, folders, pasted text, images, PDFs, or user-provided URLs. For local paths, check them first:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py" --check-source "<pointer>"
   ```

5. Stage every useful input under `~/.marshmallow/inbox/` before it changes
   durable memory. Preserve pointers instead of copying raw files:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/queue-candidate.py" \
     --kind source \
     --title "<short title>" \
     --source-pointer "<pointer>" \
     --content "<compact reason this may matter and selected evidence>"
   ```

   For pasted reusable insight without an external source, queue `--kind
   insight`. If a URL cannot be accessed, ask the user to paste an excerpt or
   export the file. Do not silently skip it.

6. Run a deliberate synthesis pass. Search existing `sources/` and `graph/`
   with `rg` or `grep`, then promote only durable source cards and reusable
   insights. Do not copy raw session logs into the graph. Use optional labels
   only when they improve retrieval; let them emerge from the user's corpus
   instead of forcing a fixed category list.

7. Run:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render-graph.py"
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate-workspace.py"
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scan-skills.py" --project "$PWD"
   ```

8. Show 3-5 emerging patterns in plain language, mention that the full graph is
   available in `~/.marshmallow/GRAPH.md`, and recommend judgment-sensitive
   skills where the patterns can improve real work. Ask which skills the user
   wants to edit.

   If no useful writable skills are found, do not stall. Treat the persistent
   adapter as the first activation. Offer to preview a small user-level starter
   skill called `marshmallow-aligned-builder`, backed by the same canonical
   overlay and rollback path.

9. Preview the persistent Claude Code adapter:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/install-adapter.py"
   ```

   Explain that it adds one replaceable import block to `~/.claude/CLAUDE.md`
   so future Claude Code sessions can search the generated compact projections.
   Keep the diff for the rewrite gate. If the user is also tuning skills,
   include the adapter and named skill files in one explicit approval request.
   If the user wants only the adapter, ask for approval before applying it:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/install-adapter.py" --approve
   ```

Do not require graph approval before tuning. The graph is the inspectable
learning substrate, not the product checkpoint. If the user corrects a pattern,
update the graph before compiling overlays. If a real tension affects a
recommended skill, ask one focused question instead of making a silent choice.

## Tune Skills

After the user chooses one or more skills:

1. Draft one pending overlay per chosen skill under `~/.marshmallow/inbox/`.
   Use 3-7 graph nodes. Preserve correct procedure; change only defaults,
   quality bars, anti-patterns, and decision rules. The apply script promotes
   the approved overlay into `~/.marshmallow/overlays/` and inserts only a
   pointer into the skill.

2. Preview the diff:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/apply-overlay.py" "<skill-path>" "<overlay-path>"
   ```

3. Explain the proposed changes briefly. Show the diff. Ask the user whether
   to apply the pending adapter update, if any, and the named skill updates. A
   single explicit approval may cover the adapter and several clearly listed
   writable skills.

4. Apply only after explicit approval. Install the pending adapter first when
   it was included in the approved list:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/install-adapter.py" --approve
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/apply-overlay.py" "<skill-path>" "<overlay-path>" --approve
   ```

If a target is read-only, pause and offer three choices:

1. Create a personal aligned copy under `~/.claude/skills/<name>-aligned/`.
2. Provide a writable skill path.
3. Skip the skill.

Create an aligned copy only after the user chooses it:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/apply-overlay.py" "<skill-path>" "<overlay-path>" \
  --aligned-copy "$HOME/.claude/skills/<name>-aligned/SKILL.md" --approve
```

If the user has no useful existing skill and approves the starter-skill path,
preview first:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/create-starter-skill.py" "<overlay-path>"
```

Apply only after explicit approval:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/create-starter-skill.py" "<overlay-path>" --approve
```

The generated skill must live under `~/.claude/skills/`, point to
`~/.marshmallow/overlays/`, and remain rollbackable through
`rollback-overlay.py`.

## Diagnose

Run the local doctor when installation state is unclear:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"
```

## Show The Graph

Re-render, validate, then read `~/.marshmallow/GRAPH.md`. Explain which nodes feed which skills. Do not dump the entire graph unless asked.

## Roll Back

Preview first:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/rollback-overlay.py" "<skill-path>"
```

Apply only after explicit approval:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/rollback-overlay.py" "<skill-path>" --approve
```

Remove the persistent Claude adapter with a preview first:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/install-adapter.py" --remove
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/install-adapter.py" --remove --approve
```

## Boundary

Marshmallow is a persistent personal alignment layer, not a general memory
platform. Align ordinary Claude Code sessions through compact runtime
projections. Learn selectively through `/marshmallow:learn`. Do not add
databases, embeddings, daemons, background agents, dashboards, OAuth flows, or
silent ingestion.
