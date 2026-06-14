# Contributing to Marshmallow

Thanks for helping make AI agents less generic. Marshmallow is small on purpose —
the goal is a foundation people can read, trust, fork, and extend.

## Principles

Before proposing a change, skim [METHODOLOGY.md](METHODOLOGY.md) and the
**Deliberate Non-Goals** in [ARCHITECTURE.md](ARCHITECTURE.md). Contributions are
much easier to accept when they respect the boundaries:

- Models synthesize; deterministic Python handles file mutation, previews, and
  rollback.
- Personalization stays source-backed and inspectable.
- Learning is explicit — no background capture, no silent learning.
- No databases, daemons, cron jobs, dashboards, or broad MCP layers.

## Development setup

You only need Python 3.9+ and (optionally) the Claude Code CLI.

```bash
git clone https://github.com/notmehul/marshmallow.git
cd marshmallow
python3 -m unittest discover -s tests -v
```

## Before you open a PR

All of these must pass — they run in CI:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q scripts tests
scripts/marshmallow.py doctor --workspace examples/operator-recall --json
claude plugin validate . --strict   # if you have the Claude Code CLI
```

Then make sure the working tree is clean (`git diff --exit-code`); CI fails if the
demo run leaves changes behind.

## Guidelines

- **Add tests for new behavior.** Deterministic file operations especially need
  coverage — see `tests/test_workspace.py`.
- **Keep the surface small.** One CLI (`scripts/marshmallow.py`), focused library
  modules. Prefer extending an existing module over adding a new one.
- **Match the existing style.** Read the surrounding code first.
- **Update docs in the same PR** when you change a contract, command, or schema.
- **Mutations stay reversible.** Anything that writes to a user file follows the
  preview → approve → backup → rollback shape.

## Reporting bugs and ideas

Open an issue using the templates in `.github/ISSUE_TEMPLATE/`. For security
concerns, please avoid filing a public issue with reproduction details until
maintainers have had a chance to respond.
