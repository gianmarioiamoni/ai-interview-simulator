# scripts/question_corpus/build_technical_background_seed.py

import hashlib
import json
import re
from pathlib import Path

BEHAVIORAL_PATH = Path(
    "datasets/curated/local_import/behavioral_interview_questions.json",
)
AK_INTERVIEW_PATH = Path("datasets/curated/hf_import/ak_interview.json")
OUTPUT_PATH = Path(
    "datasets/curated/local_import/technical_background_seed.json",
)

TARGET_MIN = 40
TARGET_MAX = 50

INCLUDE_PATTERNS = [
    r"^tell me about yourself\b",
    r"\bcareer goal",
    r"\bwhere do you see yourself",
    r"^describe your project\b",
    r"^describe your ideal workplace\b",
    r"^what have you built\b",
    r"^why do you want\b",
    r"^why do you like\b",
    r"what are you looking for in your next",
    r"what are you excited about",
    r"^tell me about your (past |most |interesting |challenging )?project",
    r"^talk about your favorite project\b",
    r"interesting projects you have worked on",
    r"^why do you want this job\b",
    r"leave your current",
    r"^why lyft\b",
    r"join slack",
    r"work at bytedance",
    r"work for amazon",
    r"^what project are you currently working\b",
    r"^explain a project that you worked on\b",
    r"biggest achievement in your previous projects",
    r"hope to achieve in the first six months",
    r"colleagues use to describe you",
    r"manager say about you",
    r"mission resonates",
]

EXCLUDE_PATTERNS = [
    r"tell me about a time",
    r"describe a time",
    r"give an example when",
    r"give me an example of a time",
    r"\bconflict\b",
    r"\bdisagreement\b",
    r"\btight deadline\b",
    r"\brecent failure\b",
    r"\buncomfortable\b",
    r"\bterrible news\b",
    r"\boverwhelming\b",
    r"\bnot responsive\b",
    r"\bconstructive feedback\b",
    r"\bfrustrat",
    r"difference of opinion",
    r"worked on something without getting approval",
    r"unlimited budget",
    r"gerbil",
    r"grandmother",
    r"analytical problem",
    r"difficult bug",
    r"hardest technical problem",
    r"stay up to date with the latest technologies",
    r"remove from the .+ experience",
    r"human resources means",
]

PROJECT_NARRATIVE_PATTERNS = [
    r"project",
    r"worked on",
    r"working on",
    r"built",
    r"achievement in your previous",
]

MANUAL_QUESTIONS: list[dict[str, str | int]] = [
    {
        "question": (
            "Describe your technical journey: how you moved into software engineering "
            "and the main transitions in your career so far."
        ),
        "role": "fullstack_engineer",
        "seniority": "mid",
        "difficulty": 2,
        "source": "manual_seed/technical_background",
        "tags": ["career_evolution", "technical_journey"],
        "expected_topics": ["motivation", "growth", "role_transitions"],
    },
    {
        "question": (
            "Walk me through the most complex system you have worked on: your role, "
            "the architecture, and the technical decisions you influenced."
        ),
        "role": "backend_engineer",
        "seniority": "senior",
        "difficulty": 4,
        "source": "manual_seed/technical_background",
        "tags": ["architecture", "project_experience"],
        "expected_topics": ["system_design", "ownership", "trade_offs"],
    },
    {
        "question": (
            "Describe your experience designing and operating distributed backend "
            "systems in production."
        ),
        "role": "fullstack_engineer",
        "seniority": "mid",
        "difficulty": 3,
        "source": "manual_seed/technical_background",
        "tags": ["architecture", "distributed_systems"],
        "expected_topics": ["scalability", "reliability", "operations"],
    },
    {
        "question": (
            "How do you choose technologies for a new project? Describe a real example "
            "including alternatives you considered and why you rejected them."
        ),
        "role": "fullstack_engineer",
        "seniority": "mid",
        "difficulty": 3,
        "source": "manual_seed/technical_background",
        "tags": ["technology_choices"],
        "expected_topics": ["trade_offs", "constraints", "team_context"],
    },
    {
        "question": (
            "Tell me about a production service you owned end-to-end: deployment, "
            "monitoring, incidents, and follow-up improvements."
        ),
        "role": "backend_engineer",
        "seniority": "mid",
        "difficulty": 3,
        "source": "manual_seed/technical_background",
        "tags": ["project_experience", "ownership"],
        "expected_topics": ["reliability", "observability", "iteration"],
    },
    {
        "question": (
            "How has your engineering scope evolved over the last few years—from "
            "implementation to design, mentoring, or cross-team work?"
        ),
        "role": "fullstack_engineer",
        "seniority": "senior",
        "difficulty": 3,
        "source": "manual_seed/technical_background",
        "tags": ["career_evolution"],
        "expected_topics": ["seniority_growth", "impact", "leadership"],
    },
    {
        "question": (
            "Describe a technical migration or refactor you led. What was the legacy "
            "state, target architecture, and how did you de-risk the rollout?"
        ),
        "role": "backend_engineer",
        "seniority": "senior",
        "difficulty": 4,
        "source": "manual_seed/technical_background",
        "tags": ["architecture", "project_experience"],
        "expected_topics": ["migration", "risk_management", "rollout"],
    },
    {
        "question": (
            "What is your current tech stack, and how did your stack choices change "
            "across your last two roles?"
        ),
        "role": "frontend_engineer",
        "seniority": "mid",
        "difficulty": 2,
        "source": "manual_seed/technical_background",
        "tags": ["technology_choices", "technical_journey"],
        "expected_topics": ["stack", "context", "evolution"],
    },
    {
        "question": (
            "Summarize your professional background in under two minutes, focusing on "
            "roles, domains, and the kinds of engineering problems you solve best."
        ),
        "role": "fullstack_engineer",
        "seniority": "mid",
        "difficulty": 2,
        "source": "manual_seed/technical_background",
        "tags": ["technical_journey"],
        "expected_topics": ["self_introduction", "strengths", "focus_areas"],
    },
    {
        "question": (
            "Describe a cross-functional project where you partnered with product and "
            "infrastructure teams. What technical boundaries did you own?"
        ),
        "role": "devops_engineer",
        "seniority": "mid",
        "difficulty": 3,
        "source": "manual_seed/technical_background",
        "tags": ["project_experience"],
        "expected_topics": ["collaboration", "ownership", "delivery"],
    },
]


def _matches_include(text: str) -> bool:
    lower = text.lower()
    return any(re.search(pattern, lower) for pattern in INCLUDE_PATTERNS)


def _matches_exclude(text: str) -> bool:
    lower = text.lower()
    return any(re.search(pattern, lower) for pattern in EXCLUDE_PATTERNS)


def _matches_project_narrative(text: str) -> bool:
    lower = text.lower()
    if _matches_exclude(lower):
        return False
    return any(re.search(pattern, lower) for pattern in PROJECT_NARRATIVE_PATTERNS)


def _is_suitable(text: str, *, allow_project_narrative: bool) -> bool:
    if _matches_exclude(text):
        return False
    if _matches_include(text):
        return True
    return allow_project_narrative and _matches_project_narrative(text)


def _make_id(question: str) -> str:
    digest = hashlib.sha256(question.strip().lower().encode()).hexdigest()[:16]
    return f"tb_{digest}"


def _to_seed_entry(
    item: dict,
    *,
    source_override: str | None = None,
) -> dict:

    question = item["question"].strip()

    return {
        "id": _make_id(question),
        "question": question,
        "role": item["role"],
        "seniority": item["seniority"],
        "area": "technical_background",
        "domains": ["technical_background"],
        "difficulty": item["difficulty"],
        "source": source_override or item.get("source", "technical_background_seed"),
        "quality_score": item.get("quality_score", 0.8),
        "tags": list(item.get("tags", [])),
        "expected_topics": list(item.get("expected_topics", [])),
        "follow_up_hints": list(item.get("follow_up_hints", [])),
    }


def _load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _select_from_sources() -> list[dict]:
    selected: list[dict] = []
    seen_questions: set[str] = set()

    for path in (BEHAVIORAL_PATH, AK_INTERVIEW_PATH):
        for item in _load_json(path):
            question = (item.get("question") or "").strip()
            if not question:
                continue
            key = question.lower()
            if key in seen_questions:
                continue
            if not _is_suitable(
                question,
                allow_project_narrative=path == BEHAVIORAL_PATH,
            ):
                continue
            seen_questions.add(key)
            selected.append(_to_seed_entry(item))

    return selected


def _add_manual(selected: list[dict]) -> list[dict]:
    seen = {entry["question"].strip().lower() for entry in selected}
    for manual in MANUAL_QUESTIONS:
        question = str(manual["question"]).strip()
        key = question.lower()
        if key in seen:
            continue
        seen.add(key)
        selected.append(_to_seed_entry(manual))
    return selected


def build_seed() -> list[dict]:
    entries = _select_from_sources()
    entries = _add_manual(entries)

    if len(entries) < TARGET_MIN:
        raise ValueError(
            f"Only {len(entries)} technical_background questions; need at least {TARGET_MIN}.",
        )

    if len(entries) > TARGET_MAX:
        entries = entries[:TARGET_MAX]

    return entries


def main() -> None:
    entries = build_seed()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(entries, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {len(entries)} questions to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
