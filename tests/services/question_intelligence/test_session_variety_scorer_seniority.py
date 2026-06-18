# tests/services/question_intelligence/test_session_variety_scorer_seniority.py

import pytest
from unittest.mock import MagicMock

from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_intelligence.session_variety_scorer import SessionVarietyScorer


def _make_candidate(seniority: str | None = None) -> MagicMock:
    metadata = {"difficulty": 3, "area": "technical_technical_knowledge"}
    if seniority is not None:
        metadata["seniority"] = seniority

    doc = MagicMock()
    doc.metadata = metadata
    doc.page_content = "What is a binary tree?"

    candidate = MagicMock()
    candidate.document = doc
    return candidate


class TestSessionVarietyScorerSeniority:

    def test_to_bank_item_reads_junior_seniority_from_metadata(self):
        scorer = SessionVarietyScorer()
        candidate = _make_candidate(seniority="junior")

        item = scorer.to_bank_item(candidate)

        assert item.level == SeniorityLevel.JUNIOR

    def test_to_bank_item_reads_senior_seniority_from_metadata(self):
        scorer = SessionVarietyScorer()
        candidate = _make_candidate(seniority="senior")

        item = scorer.to_bank_item(candidate)

        assert item.level == SeniorityLevel.SENIOR

    def test_to_bank_item_reads_mid_seniority_from_metadata(self):
        scorer = SessionVarietyScorer()
        candidate = _make_candidate(seniority="mid")

        item = scorer.to_bank_item(candidate)

        assert item.level == SeniorityLevel.MID

    def test_to_bank_item_falls_back_to_mid_when_seniority_missing(self):
        scorer = SessionVarietyScorer()
        candidate = _make_candidate(seniority=None)

        item = scorer.to_bank_item(candidate)

        assert item.level == SeniorityLevel.MID

    def test_to_bank_item_falls_back_to_mid_on_invalid_seniority(self):
        scorer = SessionVarietyScorer()
        candidate = _make_candidate(seniority="unknown_level")

        item = scorer.to_bank_item(candidate)

        assert item.level == SeniorityLevel.MID

    def test_to_bank_item_does_not_hardcode_mid_for_junior(self):
        scorer = SessionVarietyScorer()
        candidate = _make_candidate(seniority="junior")

        item = scorer.to_bank_item(candidate)

        assert item.level != SeniorityLevel.MID
