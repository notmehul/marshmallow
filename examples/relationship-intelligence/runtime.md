# Marshmallow Alignment Router

Marshmallow is a local source-backed continuity layer. Use it for explicit
prior-context requests, named people, projects, decisions, or managed-plan work.
Skip recall for generic self-contained tasks.

Recall returns relevant context plus bounded personal-guidance examples
showing how the work should be done.

## During Work

1. Run `marshmallow.py recall "<task/person/decision>"` when continuity matters.
2. Treat recall snippets as navigation only. Run `marshmallow.py get <id>` for
   every record that will materially affect the work.
3. If recall returns several plausible plans, read them and select one only when
   their scopes clearly distinguish it. Ask when multiple plans apply, conflict,
   or would materially change the work.
4. Use `~/.marshmallow/indexes/` for compact navigation and
   `~/.marshmallow/projections/` for focused recall packets. Load only the
   smallest relevant graph context. Do not crawl the whole graph.
5. Current user instructions, project instructions, and safety rules outrank
   stored context.

Do not crawl the whole graph by default.
Do not load extra personal nodes merely to fill context; the bounded
personal-guidance layer stays below twenty percent of the response budget.
Capture only unmistakable feedback.
This workspace contains dummy public demo information.

## Managed Completion

When covered work changes an active `managed: true` plan, call `maintain` before
finishing. The request must use hashes returned by `get`, update the selected
plan, and cite evidence. Agent execution alone may source operational plan
progress. Connected living-state updates require an existing source, artifact,
or observable user event.

An observable user behavior may update an existing connected managed note when
the receipt preserves the smallest relevant observation and origin. Broader
inference or knowledge requiring a new node goes to `remember` and the inbox.
Never create, delete, relink, or update unrelated graph nodes through maintenance.

## Learning

Do not learn automatically from ordinary sessions. Preserve new durable context
only through explicit learning or the narrow source-backed managed-update path.
Inbox material remains untrusted until promotion.
