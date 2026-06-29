from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from marshmallow_workspace import MarshmallowError, atomic_write, ensure_workspace  # noqa: E402
from mcp_installer import (  # noqa: E402
    MCP_SERVER_NAME,
    cursor_server_entry,
    install_codex_mcp_section,
    install_runtime,
    mcp_status,
    remove_codex_mcp_section,
    remove_cursor_entry,
    update_mcp,
)


class McpInstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name) / "home"
        self.home.mkdir()
        self.workspace = self.home / ".marshmallow"
        ensure_workspace(self.workspace)
        self.runtime_dir = self.home / ".local/share/marshmallow/scripts"
        self.cursor_config = self.home / ".cursor/mcp.json"
        self.codex_config = self.home / ".codex/config.toml"
        self._env = os.environ.copy()
        os.environ["HOME"] = str(self.home)
        os.environ["MARSHMALLOW_MCP_RUNTIME_DIR"] = str(self.runtime_dir)
        os.environ["MARSHMALLOW_CURSOR_MCP"] = str(self.cursor_config)
        os.environ["MARSHMALLOW_CODEX_CONFIG"] = str(self.codex_config)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)
        self.temp.cleanup()

    def test_install_runtime_copies_executable_scripts(self) -> None:
        install_runtime(SCRIPTS, self.runtime_dir)
        server = self.runtime_dir / "mcp_server.py"
        self.assertTrue(server.is_file())
        self.assertTrue(server.stat().st_mode & stat.S_IXUSR)

    def test_cursor_preview_does_not_write_config(self) -> None:
        code, message = update_mcp(
            self.workspace,
            "cursor",
            approve=False,
            remove=False,
            runtime_dir=self.runtime_dir,
            source_dir=SCRIPTS,
        )

        self.assertEqual(0, code)
        self.assertFalse(self.cursor_config.exists())
        self.assertFalse((self.runtime_dir / "mcp_server.py").exists())
        self.assertIn(MCP_SERVER_NAME, message)

    def test_cursor_apply_writes_user_wide_config(self) -> None:
        code, message = update_mcp(
            self.workspace,
            "cursor",
            approve=True,
            remove=False,
            runtime_dir=self.runtime_dir,
            source_dir=SCRIPTS,
        )

        self.assertEqual(0, code)
        payload = json.loads(self.cursor_config.read_text())
        entry = payload["mcpServers"][MCP_SERVER_NAME]
        self.assertEqual(cursor_server_entry(self.runtime_dir, self.workspace), entry)
        self.assertIn("applied", message)

    def test_cursor_apply_uses_custom_runtime_and_workspace_paths(self) -> None:
        update_mcp(
            self.workspace,
            "cursor",
            approve=True,
            remove=False,
            runtime_dir=self.runtime_dir,
            source_dir=SCRIPTS,
        )

        entry = json.loads(self.cursor_config.read_text())["mcpServers"][MCP_SERVER_NAME]
        self.assertEqual(str((self.runtime_dir / "mcp_server.py").resolve()), entry["command"])
        self.assertEqual(str(self.workspace.resolve()), entry["env"]["MARSHMALLOW_HOME"])

    def test_cursor_apply_refuses_to_replace_an_unmanaged_entry(self) -> None:
        self.cursor_config.parent.mkdir(parents=True)
        atomic_write(
            self.cursor_config,
            json.dumps({"mcpServers": {MCP_SERVER_NAME: {"command": "/custom/server"}}}) + "\n",
        )

        with self.assertRaisesRegex(MarshmallowError, "different MCP server"):
            update_mcp(
                self.workspace,
                "cursor",
                approve=True,
                remove=False,
                runtime_dir=self.runtime_dir,
                source_dir=SCRIPTS,
            )

    def test_codex_apply_appends_mcp_section(self) -> None:
        self.codex_config.parent.mkdir(parents=True)
        atomic_write(self.codex_config, 'model = "gpt-5"\n')
        code, _message = update_mcp(
            self.workspace,
            "codex",
            approve=True,
            remove=False,
            runtime_dir=self.runtime_dir,
            source_dir=SCRIPTS,
        )

        self.assertEqual(0, code)
        text = self.codex_config.read_text()
        self.assertIn("[mcp_servers.marshmallow]", text)
        self.assertIn("[mcp_servers.marshmallow.env]", text)
        self.assertIn(str(self.runtime_dir / "mcp_server.py"), text)
        self.assertIn(str(self.workspace), text)
        self.assertIn('model = "gpt-5"', text)

    def test_codex_remove_deletes_only_marshmallow_section(self) -> None:
        server = str(self.runtime_dir / "mcp_server.py")
        original = (
            f'model = "gpt-5"\n\n[mcp_servers.marshmallow]\ncommand = "{server}"\n\n'
            f'[mcp_servers.marshmallow.env]\nMARSHMALLOW_HOME = "{self.workspace}"\n\n'
            '[mcp_servers.other]\ncommand = "echo"\n'
        )
        atomic_write(self.codex_config, original)
        cleaned = remove_codex_mcp_section(original)
        self.assertNotIn("[mcp_servers.marshmallow]", cleaned)
        self.assertNotIn("[mcp_servers.marshmallow.env]", cleaned)
        self.assertIn('model = "gpt-5"', cleaned)
        self.assertIn("[mcp_servers.other]", cleaned)

    def test_cursor_remove_drops_server_entry(self) -> None:
        payload = {
            "mcpServers": {
                MCP_SERVER_NAME: cursor_server_entry(),
                "other": {"command": "echo"},
            }
        }
        updated = remove_cursor_entry(payload)
        self.assertNotIn(MCP_SERVER_NAME, updated["mcpServers"])
        self.assertIn("other", updated["mcpServers"])

    def test_cursor_remove_does_not_create_a_missing_config(self) -> None:
        code, message = update_mcp(
            self.workspace,
            "cursor",
            approve=True,
            remove=True,
            runtime_dir=self.runtime_dir,
            source_dir=SCRIPTS,
        )

        self.assertEqual(0, code)
        self.assertFalse(self.cursor_config.exists())
        self.assertIn("unchanged", message)

    def test_mcp_status_reports_installed_cursor_config(self) -> None:
        self.cursor_config.parent.mkdir(parents=True)
        atomic_write(
            self.cursor_config,
            json.dumps({"mcpServers": {MCP_SERVER_NAME: cursor_server_entry()}}, indent=2) + "\n",
        )
        install_runtime(SCRIPTS, self.runtime_dir)
        status = mcp_status("cursor", runtime_dir=self.runtime_dir)
        self.assertEqual("installed", status["status"])
        self.assertEqual("ready", status["runtime"])

    def test_codex_section_helpers_are_idempotent(self) -> None:
        server = self.runtime_dir / "mcp_server.py"
        server.parent.mkdir(parents=True)
        server.touch()
        first = install_codex_mcp_section("", server, self.workspace)
        second = install_codex_mcp_section(first, server, self.workspace)
        self.assertEqual(first.count("[mcp_servers.marshmallow]"), 1)
        self.assertEqual(first.count("[mcp_servers.marshmallow.env]"), 1)
        self.assertEqual(second.count("[mcp_servers.marshmallow]"), 1)

    def test_codex_apply_refuses_to_replace_an_existing_entry(self) -> None:
        self.codex_config.parent.mkdir(parents=True)
        atomic_write(
            self.codex_config,
            '[mcp_servers.marshmallow]\ncommand = "/custom/server"\n',
        )

        with self.assertRaisesRegex(MarshmallowError, "different MCP server"):
            update_mcp(
                self.workspace,
                "codex",
                approve=True,
                remove=False,
                runtime_dir=self.runtime_dir,
                source_dir=SCRIPTS,
            )


class PluginManifestTests(unittest.TestCase):
    def test_native_plugin_manifests_share_identity_and_stdio_server(self) -> None:
        claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())

        self.assertEqual(claude["name"], codex["name"])
        self.assertEqual(claude["version"], codex["version"])
        self.assertEqual("./skills/", codex["skills"])
        self.assertEqual(
            "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_server.py",
            claude["mcpServers"]["marshmallow"]["command"],
        )
        self.assertEqual(
            "./scripts/mcp_server.py",
            codex["mcpServers"]["marshmallow"]["command"],
        )
        interface = codex["interface"]
        for field in ("composerIcon", "logo", "logoDark"):
            self.assertEqual("./assets/marsh-avatar-01.png", interface[field])
            self.assertTrue((ROOT / interface[field]).is_file())
        self.assertEqual(["./assets/marshy-hero.png"], interface["screenshots"])
        self.assertTrue((ROOT / "assets/marshy-hero.png").is_file())
        self.assertEqual("#D946EF", interface["brandColor"])

    def test_codex_marketplace_points_at_repo_plugin(self) -> None:
        marketplace = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text())
        entry = marketplace["plugins"][0]
        self.assertEqual("marshmallow", entry["name"])
        self.assertEqual("./", entry["source"]["path"])
        self.assertEqual("AVAILABLE", entry["policy"]["installation"])

    def test_shared_skills_explain_cross_harness_root_resolution(self) -> None:
        for name in ("start", "learn", "tune"):
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            self.assertIn("In other\nplugin hosts, resolve the plugin root", text)
            self.assertIn("substitute that absolute path", text)


if __name__ == "__main__":
    unittest.main()
