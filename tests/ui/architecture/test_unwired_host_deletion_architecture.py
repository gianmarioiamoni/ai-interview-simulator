# tests/ui/architecture/test_unwired_host_deletion_architecture.py
# EPIC-07 C13 — EC-UH-01 / R-14: DELETE_TARGET modules not imported by live bind path.

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

# EC-UH-01 closed inventory (Data Model §4.7) — modules still present until C14.
DELETE_TARGET_MODULES: frozenset[str] = frozenset(
    {
        "app.ui.views.setup_view",
        "app.ui.views.interview_written_view",
        "app.ui.views.interview_coding_view",
        "app.ui.views.interview_database_view",
        "app.ui.utils.loading_utils",
        "app.ui.response.sections.error_hint_builder",
        "app.ui.presenters.result_presenter",
    }
)

# Sole live Gradio host entry (AR-06): layout + event bind.
LIVE_BIND_ENTRYPOINTS: tuple[str, ...] = (
    "app.ui.app",
)


def _module_to_path(module_name: str) -> Path | None:
    file_path = REPO_ROOT / Path(*module_name.split(".")).with_suffix(".py")
    if file_path.is_file():
        return file_path
    package_init = REPO_ROOT / Path(*module_name.split(".")) / "__init__.py"
    if package_init.is_file():
        return package_init
    return None


def _resolve_import_from(current_module: str, node: ast.ImportFrom) -> list[str]:
    resolved: list[str] = []
    if node.level == 0:
        base = node.module or ""
    else:
        parts = current_module.split(".")
        package_parts = parts[:-1]
        if node.level > 1:
            package_parts = package_parts[: -(node.level - 1)]
        if node.module:
            base = ".".join([*package_parts, *node.module.split(".")])
        else:
            base = ".".join(package_parts)

    if not base:
        return resolved

    resolved.append(base)
    for alias in node.names:
        if alias.name == "*":
            continue
        candidate = f"{base}.{alias.name}"
        if _module_to_path(candidate) is not None:
            resolved.append(candidate)
    return resolved


def _collect_import_closure(entrypoints: tuple[str, ...]) -> set[str]:
    seen: set[str] = set()
    stack = list(entrypoints)

    while stack:
        module_name = stack.pop()
        if module_name in seen:
            continue
        seen.add(module_name)

        path = _module_to_path(module_name)
        if path is None:
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    stack.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                stack.extend(_resolve_import_from(module_name, node))

    return seen


@pytest.fixture(scope="module")
def live_bind_closure() -> set[str]:
    return _collect_import_closure(LIVE_BIND_ENTRYPOINTS)


class TestDeleteTargetInventory:
    def test_inventory_matches_ec_uh_01_paths(self) -> None:
        expected_paths = {
            "app/ui/views/setup_view.py",
            "app/ui/views/interview_written_view.py",
            "app/ui/views/interview_coding_view.py",
            "app/ui/views/interview_database_view.py",
            "app/ui/utils/loading_utils.py",
            "app/ui/response/sections/error_hint_builder.py",
            "app/ui/presenters/result_presenter.py",
        }
        actual_paths = {
            module.replace(".", "/") + ".py" for module in DELETE_TARGET_MODULES
        }
        assert actual_paths == expected_paths

    def test_delete_target_modules_still_present_on_disk(self) -> None:
        """C13 proves non-import before C14 deletion; targets must still exist."""
        for module_name in sorted(DELETE_TARGET_MODULES):
            path = _module_to_path(module_name)
            assert path is not None and path.is_file(), (
                f"DELETE_TARGET module missing before C14: {module_name}"
            )


class TestLiveBindDoesNotImportDeleteTargets:
    def test_live_bind_closure_excludes_delete_targets(
        self, live_bind_closure: set[str]
    ) -> None:
        hits = sorted(
            module_name
            for module_name in live_bind_closure
            if module_name in DELETE_TARGET_MODULES
            or any(
                module_name.startswith(f"{target}.")
                for target in DELETE_TARGET_MODULES
            )
        )
        assert hits == [], (
            "I-UH-01 / R-14 violation: live bind path imports DELETE_TARGET "
            f"modules: {hits}"
        )

    @pytest.mark.parametrize("target", sorted(DELETE_TARGET_MODULES))
    def test_live_bind_modules_do_not_reference_delete_target_import(
        self, target: str, live_bind_closure: set[str]
    ) -> None:
        forbidden_fragments = (
            target,
            target.replace(".", "/"),
            target.rsplit(".", 1)[-1],
        )
        # Class/module leaf names that uniquely identify DELETE_TARGET hosts.
        unique_symbols = {
            "app.ui.views.setup_view": ("SetupView", "setup_view"),
            "app.ui.views.interview_written_view": (
                "InterviewWrittenView",
                "interview_written_view",
            ),
            "app.ui.views.interview_coding_view": (
                "InterviewCodingView",
                "interview_coding_view",
            ),
            "app.ui.views.interview_database_view": (
                "InterviewDatabaseView",
                "interview_database_view",
            ),
            "app.ui.utils.loading_utils": ("loading_utils",),
            "app.ui.response.sections.error_hint_builder": (
                "ErrorHintBuilder",
                "error_hint_builder",
            ),
            "app.ui.presenters.result_presenter": (
                "ResultPresenter",
                "result_presenter",
            ),
        }[target]

        for module_name in sorted(live_bind_closure):
            path = _module_to_path(module_name)
            if path is None:
                continue
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            imported: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    imported.update(_resolve_import_from(module_name, node))
                    if node.module:
                        imported.add(node.module)
                    for alias in node.names:
                        imported.add(alias.name)

            assert target not in imported, (
                f"{module_name} imports DELETE_TARGET {target}"
            )
            for symbol in unique_symbols:
                assert symbol not in imported, (
                    f"{module_name} imports DELETE_TARGET symbol {symbol!r} "
                    f"(target {target})"
                )
            for fragment in forbidden_fragments[:2]:
                assert fragment not in imported, (
                    f"{module_name} imports DELETE_TARGET fragment {fragment!r}"
                )
