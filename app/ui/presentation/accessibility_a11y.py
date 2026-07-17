# app/ui/presentation/accessibility_a11y.py
# EPIC-07 EC-AX-01 AX-02…AX-05 / Data Model §4.6 — report/replay a11y verification.

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final, Iterable

# Gradio/unit-suite automation limit (AR-14 / NI-02): full browser axe-core is out
# of band; evidence is structural HTML + catalog text-presence audits.


AX02_REQUIREMENT_ID: Final[str] = "AX-02"
AX03_REQUIREMENT_ID: Final[str] = "AX-03"
AX04_REQUIREMENT_ID: Final[str] = "AX-04"
AX05_REQUIREMENT_ID: Final[str] = "AX-05"

AX02_VERIFICATION_ARTIFACT_TYPE: Final[str] = "Report a11y audit/test"
AX03_VERIFICATION_ARTIFACT_TYPE: Final[str] = "Replay a11y audit/test"
AX04_VERIFICATION_ARTIFACT_TYPE: Final[str] = "Copy presence test"
AX05_VERIFICATION_ARTIFACT_TYPE: Final[str] = "A11y audit/test"

AX02_SURFACES: Final[frozenset[str]] = frozenset({"report"})
AX03_SURFACES: Final[frozenset[str]] = frozenset({"replay"})
AX04_SURFACES: Final[frozenset[str]] = frozenset(
    {"setup", "question", "feedback", "report", "replay", "progress", "history"}
)
AX05_SURFACES: Final[frozenset[str]] = frozenset({"report", "replay"})

# Matches existing report contrast regression (WCAG contrast proxy).
BANNED_LOW_CONTRAST_COLOR: Final[str] = "#6b7280"

_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_IMG_ALT_RE = re.compile(r"\balt\s*=\s*([\"'])(.*?)\1", re.IGNORECASE)
_ALPHA_WORD_RE = re.compile(r"[A-Za-z]{2,}")
_ICON_ONLY_RE = re.compile(
    r"^[\s\W_🎟⚠✅❌🔴🟢🟡⚪⚫⭐✨💡📌▶◀↑↓←→•·]+$",
    re.UNICODE,
)


@dataclass(frozen=True)
class AccessibilityRequirementRow:
    requirement_id: str
    statement: str
    applies_to_surfaces: frozenset[str]
    verification_artifact_type: str


ACCESSIBILITY_REQUIREMENT_ROWS: Final[tuple[AccessibilityRequirementRow, ...]] = (
    AccessibilityRequirementRow(
        requirement_id=AX02_REQUIREMENT_ID,
        statement="Report targets WCAG 2.1 AA",
        applies_to_surfaces=AX02_SURFACES,
        verification_artifact_type=AX02_VERIFICATION_ARTIFACT_TYPE,
    ),
    AccessibilityRequirementRow(
        requirement_id=AX03_REQUIREMENT_ID,
        statement="Replay targets WCAG 2.1 AA",
        applies_to_surfaces=AX03_SURFACES,
        verification_artifact_type=AX03_VERIFICATION_ARTIFACT_TYPE,
    ),
    AccessibilityRequirementRow(
        requirement_id=AX04_REQUIREMENT_ID,
        statement="Errors/empty/loading text perceivable (not icon-only)",
        applies_to_surfaces=AX04_SURFACES,
        verification_artifact_type=AX04_VERIFICATION_ARTIFACT_TYPE,
    ),
    AccessibilityRequirementRow(
        requirement_id=AX05_REQUIREMENT_ID,
        statement="Decorative chrome not sole meaning carrier for scores/errors",
        applies_to_surfaces=AX05_SURFACES,
        verification_artifact_type=AX05_VERIFICATION_ARTIFACT_TYPE,
    ),
)


def is_perceivable_text(text: str) -> bool:
    """AX-04: candidate-facing copy must carry readable words (not icon-only)."""
    stripped = text.strip()
    if not stripped:
        return False
    if _ICON_ONLY_RE.match(stripped):
        return False
    return _ALPHA_WORD_RE.search(stripped) is not None


def assert_perceivable_text(text: str, *, context: str) -> None:
    if not is_perceivable_text(text):
        raise AssertionError(f"AX-04: text not perceivable ({context}): {text!r}")


def assert_html_images_have_alt(html: str, *, context: str) -> None:
    """AX-02/AX-03: every <img> must expose a non-empty alt (WCAG 1.1.1 proxy)."""
    for tag in _IMG_TAG_RE.findall(html):
        match = _IMG_ALT_RE.search(tag)
        if match is None or not match.group(2).strip():
            raise AssertionError(f"{context}: image missing non-empty alt: {tag}")


def assert_no_banned_low_contrast_color(html: str, *, context: str) -> None:
    if BANNED_LOW_CONTRAST_COLOR in html.lower():
        raise AssertionError(
            f"{context}: banned low-contrast color {BANNED_LOW_CONTRAST_COLOR} present"
        )


def assert_score_meaning_not_color_only(html: str, *, context: str) -> None:
    """AX-05: score/error meaning must include digits or textual labels."""
    has_numeric = bool(re.search(r"\d", html))
    has_textual_score_label = bool(
        re.search(
            r"(N/A|Score|Overall|percentile|Hire|Strong|Medium|Weak|EXCEPTIONAL|"
            r"ACCEPTABLE|INCORRECT|/100)",
            html,
            re.IGNORECASE,
        )
    )
    if not (has_numeric or has_textual_score_label):
        raise AssertionError(
            f"AX-05: {context} carries no textual/numeric score meaning"
        )


def assert_report_html_a11y_hooks(html: str) -> None:
    """AX-02 (+ AX-05 report) automatable WCAG target hooks."""
    if "<h1" not in html.lower():
        raise AssertionError("AX-02: report HTML missing h1 landmark text")
    assert_html_images_have_alt(html, context="AX-02 report")
    assert_no_banned_low_contrast_color(html, context="AX-02 report")
    assert_score_meaning_not_color_only(html, context="report")


def assert_replay_html_a11y_hooks(html_fragments: Iterable[str]) -> None:
    """AX-03 (+ AX-05 replay) automatable WCAG target hooks across panel HTML."""
    combined = "\n".join(html_fragments)
    if not combined.strip():
        raise AssertionError("AX-03: replay HTML fragments empty")
    assert_html_images_have_alt(combined, context="AX-03 replay")
    assert_no_banned_low_contrast_color(combined, context="AX-03 replay")
    for fragment in html_fragments:
        if not fragment.strip():
            continue
        if "replay-error" in fragment or "Score" in fragment or "Overall" in fragment:
            assert_perceivable_text(
                re.sub(r"<[^>]+>", " ", fragment),
                context="AX-03/AX-05 replay fragment",
            )
    assert_score_meaning_not_color_only(combined, context="replay")
