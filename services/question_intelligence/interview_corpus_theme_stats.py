# services/question_intelligence/interview_corpus_theme_stats.py

from __future__ import annotations

import json
from collections import Counter
from functools import lru_cache
from pathlib import Path

from domain.contracts.interview.interview_area import InterviewArea
from services.question_corpus.utils.domain_parser import parse_domains as _parse_domains

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CORPUS_ROOTS = (
    _PROJECT_ROOT / "datasets/curated/hf_import",
    _PROJECT_ROOT / "datasets/curated/interview_seed",
    _PROJECT_ROOT / "datasets/curated/local_import",
    _PROJECT_ROOT / "datasets/curated",
)

_AREA_MIRROR_DOMAINS = {
    InterviewArea.TECH_BACKGROUND.value,
    InterviewArea.TECH_TECHNICAL_KNOWLEDGE.value,
    InterviewArea.TECH_CASE_STUDY.value,
    InterviewArea.TECH_DATABASE.value,
    InterviewArea.TECH_CODING.value,
}


@lru_cache(maxsize=1)
def compute_technical_thematic_domain_counts() -> dict[str, int]:

    counts: Counter[str] = Counter()

    for root in _CORPUS_ROOTS:
        if not root.exists():
            continue

        for path in root.rglob("*.json"):
            try:
                payload = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                continue

            if not isinstance(payload, list):
                continue

            for item in payload:
                if not isinstance(item, dict):
                    continue

                area = item.get("area")

                if area not in _AREA_MIRROR_DOMAINS:
                    continue

                domains = _parse_domains(item.get("domains"))

                for domain in domains:
                    if domain in _AREA_MIRROR_DOMAINS or domain.startswith("hr_"):
                        continue

                    counts[domain] += 1

    return dict(counts)


def load_preview_texts_for_area(
    area: InterviewArea,
    limit: int = 12,
) -> list[str]:

    texts: list[str] = []

    for root in _CORPUS_ROOTS:
        if not root.exists():
            continue

        for path in root.rglob("*.json"):
            try:
                payload = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                continue

            if not isinstance(payload, list):
                continue

            for item in payload:
                if not isinstance(item, dict):
                    continue

                if item.get("area") != area.value:
                    continue

                text = item.get("text") or item.get("prompt")

                if not text:
                    continue

                texts.append(str(text))

                if len(texts) >= limit:
                    return texts

    return texts
