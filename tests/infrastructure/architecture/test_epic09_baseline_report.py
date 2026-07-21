# tests/infrastructure/architecture/test_epic09_baseline_report.py
#
# EPIC-09 P7/C11 — AR-19 / PRD-02/03 / O-01: baseline report artifact checklist.

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_REPORT = REPO_ROOT / "docs" / "ops" / "PERFORMANCE-BASELINE-REPORT.md"

# AR-19 required sections + explicit SLO-D N/A (PRD-03 / O-01).
REQUIRED_HEADINGS: tuple[str, ...] = (
    "## 1. Methodology",
    "## 2. Measurements (in-scope SLOs)",
    "## 3. Profiles",
    "## 4. Load results",
    "## 5. P0 disposition",
    "## 6. SLO-D — N/A V1.3",
    "## 7. ARC-01 / Category A compliance note",
)

REQUIRED_PHRASES: tuple[str, ...] = (
    "N/A V1.3",
    "P0-ABSENT",
    "Deterministic stub",
    "ARC-01",
    "SessionHistory DB read",
)


class TestPerformanceBaselineReportArtifact:
    """PRD-02/03 — release baseline report present with AR-19 content."""

    def test_baseline_report_exists(self) -> None:
        assert BASELINE_REPORT.is_file(), (
            "PRD-02: missing docs/ops/PERFORMANCE-BASELINE-REPORT.md"
        )

    def test_ar19_sections_present(self) -> None:
        text = BASELINE_REPORT.read_text(encoding="utf-8")
        missing = [heading for heading in REQUIRED_HEADINGS if heading not in text]
        assert missing == [], f"AR-19 missing sections: {missing}"

    def test_slo_d_na_and_core_phrases_present(self) -> None:
        text = BASELINE_REPORT.read_text(encoding="utf-8")
        missing = [phrase for phrase in REQUIRED_PHRASES if phrase not in text]
        assert missing == [], f"PRD-03/O-01 missing required phrases: {missing}"
