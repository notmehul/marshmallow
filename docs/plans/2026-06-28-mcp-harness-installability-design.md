# MCP Harness Installability Design

## Goal

Make the existing dependency-free stdio MCP server straightforward to register
in the agent harnesses Marshmallow users already run, without adding a broad
integration layer or another installer that mutates vendor configuration.

## Design

- Keep `scripts/mcp_server.py` as the single MCP entry point.
- Negotiate the latest stable MCP revision while retaining compatibility with
  the previously shipped revision.
- Document each harness's native MCP registration command or config shape.
- Keep Claude plugin auto-registration unchanged.
- Serialize user-authored scaffold metadata as safe, single-line frontmatter.
- Correct first-start documentation: the server creates the workspace skeleton;
  later writes are limited to explicit `remember` calls into the untrusted inbox.

## Verification

- Unit tests cover protocol negotiation and scaffold metadata injection.
- The full test suite, Python compilation, example doctor run, diff checks, and
  strict Claude plugin validation must pass before merge.
