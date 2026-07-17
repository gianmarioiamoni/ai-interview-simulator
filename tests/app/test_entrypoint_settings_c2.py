# tests/app/test_entrypoint_settings_c2.py
#
# EPIC-08 P1/C2 — production entrypoints read runtime config via Settings only.

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_APP_PY = _REPO_ROOT / "app.py"
_APP_MAIN_PY = _REPO_ROOT / "app" / "main.py"


def _source_uses_os_environ(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "environ":
            if isinstance(node.value, ast.Name) and node.value.id == "os":
                return True
        if isinstance(node, ast.Attribute) and node.attr == "getenv":
            if isinstance(node.value, ast.Name) and node.value.id == "os":
                return True
    return False


class TestProductionEntrypointsNoOsEnviron:
    def test_app_py_has_no_os_environ_reads(self) -> None:
        assert _APP_PY.is_file()
        assert _source_uses_os_environ(_APP_PY) is False

    def test_app_main_py_has_no_os_environ_reads(self) -> None:
        assert _APP_MAIN_PY.is_file()
        assert _source_uses_os_environ(_APP_MAIN_PY) is False


class TestMainUsesSettings:
    def test_main_launches_with_settings_host_and_port(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from infrastructure.config import settings as settings_module

        monkeypatch.setattr(settings_module.settings, "server_host", "127.0.0.1")
        monkeypatch.setattr(settings_module.settings, "server_port", 9999)
        monkeypatch.setattr(settings_module.settings, "hf_token", "hf_test_token")

        mock_app = MagicMock()
        monkeypatch.setattr("app.main.build_app", lambda: mock_app)
        monkeypatch.setattr("app.main.ensure_corpus", MagicMock())

        from app.main import main

        main()

        mock_app.launch.assert_called_once_with(
            server_name="127.0.0.1",
            server_port=9999,
            share=False,
            quiet=False,
        )

    def test_main_passes_settings_hf_token_to_ensure_corpus(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from infrastructure.config import settings as settings_module

        monkeypatch.setattr(settings_module.settings, "hf_token", "hf_from_settings")
        monkeypatch.setattr(settings_module.settings, "server_host", "0.0.0.0")
        monkeypatch.setattr(settings_module.settings, "server_port", 7860)

        mock_ensure = MagicMock()
        mock_app = MagicMock()
        monkeypatch.setattr("app.main.ensure_corpus", mock_ensure)
        monkeypatch.setattr("app.main.build_app", lambda: mock_app)

        from app.main import main

        main()

        mock_ensure.assert_called_once_with(hf_token="hf_from_settings")
