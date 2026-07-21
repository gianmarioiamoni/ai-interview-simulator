# tests/infrastructure/architecture/test_epic10_cleanup_architecture.py
#
# EPIC-10 architecture gates:
# AT-02: Deleted stubs absent (gradio_app, EvaluationBridgeDetector) — Macro C / P4.
# AT-04: INDEX Official Patterns lists OP-01…06 + P-08 cross-ref (AR-01, AR-02, REG-*).
# AT-05: No Projection-as-PAT-04 mislabels in domain/contracts/report (AR-09, REG-06).

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
INDEX_PATH = REPO_ROOT / "docs" / "master-plan" / "INDEX.md"
REPORT_CONTRACTS_ROOT = REPO_ROOT / "domain" / "contracts" / "report"

DELETED_STUB_PATHS: tuple[str, ...] = (
    "gradio_app.py",
    "services/interview_reasoner/pattern_detection/detectors/"
    "evaluation_bridge_detector.py",
    "tests/services/interview_reasoner/pattern_detection/detectors/"
    "test_evaluation_bridge_detector.py",
)

RETIRED_MIG_SCAFFOLDING_TESTS: tuple[str, ...] = (
    "tests/domain/profile/test_candidate_profile_derivation_service.py",
    "tests/domain/profile/test_derived_profile_data.py",
    "tests/domain/profile/test_derivation_rules.py",
)

REQUIRED_OP_IDS: tuple[str, ...] = (
    "OP-01",
    "OP-02",
    "OP-03",
    "OP-04",
    "OP-05",
    "OP-06",
)

# Projection mislabeled as PAT-04 (TCP) — must use OP-02 instead.
PROJECTION_AS_PAT04_PATTERN = re.compile(
    r"Projection\s+Artifact\s*\(\s*PAT-04\s*\)",
    re.IGNORECASE,
)


def _read_index() -> str:
    assert INDEX_PATH.is_file(), f"Missing INDEX: {INDEX_PATH}"
    return INDEX_PATH.read_text(encoding="utf-8")


class TestAT02DeletedStubsAbsent:
    """AT-02 / CLN-01 / CLN-02 — deleted stubs must remain absent."""

    def test_gradio_app_and_evaluation_bridge_detector_absent(self) -> None:
        present = [
            relative
            for relative in DELETED_STUB_PATHS
            if (REPO_ROOT / relative).exists()
        ]
        assert present == [], f"Deleted stubs still present: {present}"

    def test_evaluation_bridge_detector_not_importable(self) -> None:
        import importlib

        try:
            importlib.import_module(
                "services.interview_reasoner.pattern_detection.detectors."
                "evaluation_bridge_detector"
            )
        except ModuleNotFoundError:
            return
        raise AssertionError("EvaluationBridgeDetector module must not be importable")

    def test_retired_mig_scaffolding_tests_absent(self) -> None:
        """CLN-04 — obsolete MIG-06 derivation scaffolding tests retired."""
        present = [
            relative
            for relative in RETIRED_MIG_SCAFFOLDING_TESTS
            if (REPO_ROOT / relative).exists()
        ]
        assert present == [], f"Retired MIG scaffolding tests still present: {present}"


class TestAT04IndexOfficialPatterns:
    """AT-04 — INDEX lists OP-01…06 + P-08 under Official Patterns (ARC-01)."""

    def test_official_patterns_section_present(self) -> None:
        text = _read_index()
        assert "## Official Patterns (ARC-01)" in text

    def test_op_01_through_op_06_listed(self) -> None:
        text = _read_index()
        section_start = text.index("## Official Patterns (ARC-01)")
        section_end = text.index("## ", section_start + 1)
        section = text[section_start:section_end]
        for op_id in REQUIRED_OP_IDS:
            assert op_id in section, f"{op_id} missing from Official Patterns section"

    def test_p08_cross_reference_present(self) -> None:
        text = _read_index()
        section_start = text.index("## Official Patterns (ARC-01)")
        section_end = text.index("## ", section_start + 1)
        section = text[section_start:section_end]
        assert "P-08" in section
        assert "Reconstruction Completeness" in section

    def test_five_new_pats_wording_note(self) -> None:
        text = _read_index()
        assert "five new PATs" in text
        assert "OP-01" in text and "P-08" in text


class TestAT05NoProjectionAsPat04InReportContracts:
    """AT-05 — domain/contracts/report must not label Projection Artifact as PAT-04."""

    def test_no_projection_artifact_pat04_in_report_contracts(self) -> None:
        assert REPORT_CONTRACTS_ROOT.is_dir()
        violations: list[str] = []
        for path in sorted(REPORT_CONTRACTS_ROOT.rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            if PROJECTION_AS_PAT04_PATTERN.search(source):
                relative = path.relative_to(REPO_ROOT).as_posix()
                violations.append(relative)
        assert violations == [], (
            "Projection Artifact labeled as PAT-04 (use OP-02): "
            + ", ".join(violations)
        )
