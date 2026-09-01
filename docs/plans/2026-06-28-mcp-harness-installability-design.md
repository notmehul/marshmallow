# MCP Harness Installability Design

## Goal

Ship native Claude Code and Codex plugins around one dependency-free stdio MCP
server. Keep clone-based configuration as a reversible fallback and label
Cursor support experimental until Marshmallow adopts its native plugin format.

## Design

- Keep `scripts/mcp_server.py` as the single MCP entry point.
- Negotiate the latest stable MCP revision while retaining compatibility with
  the previously shipped revision.
- Keep `.claude-plugin/plugin.json` as Claude Code's native manifest and MCP
  registration.
- Add `.codex-plugin/plugin.json` with inline MCP configuration and the
  repository Codex marketplace entry.
- Keep canonical procedures under `skills/` and document portable plugin-root
  resolution inside each procedure.
- Add `scripts/mcp_installer.py` with preview/apply/remove for Cursor
  (`~/.cursor/mcp.json`) and Codex (`~/.codex/config.toml`), copying runtime
  scripts to `~/.local/share/marshmallow/scripts/` on apply.
- Extend `setup --harness codex|cursor` to preview/apply MCP alongside the
  adapter, still requiring `--apply` before mutation.
- Keep Cursor's adapter and manual MCP installer, but make no native plugin
  claim.
- Pass the selected workspace and runtime paths into fallback MCP config and
  refuse to overwrite an existing server with the same name.
- Serialize user-authored scaffold metadata as safe, single-line frontmatter.
- Correct first-start documentation: the server creates the workspace skeleton;
  later writes are limited to explicit `remember` calls into the untrusted inbox.

## Verification

- Unit tests cover protocol negotiation, native manifest consistency, portable
  skills, and MCP installer preview/apply/remove for Cursor and Codex.
- The full test suite, Python compilation, example doctor run, diff checks, and
  Claude and Codex plugin validation must pass before merge.
