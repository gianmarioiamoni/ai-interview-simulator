# services/question_intelligence/corpus_quota_resolver.py

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from app.settings.constants import TECHNICAL_AREA_CORPUS_FRACTION


def resolve_corpus_quota(
    area: InterviewArea,
    interview_type: InterviewType,
    questions_per_area: int,
) -> int | None:
    """
    Return the maximum number of corpus questions allowed for this area, or
    None to use legacy behaviour (fill with corpus first, LLM fills the rest).

    For TECHNICAL interviews the quota is derived from the validated
    area-specific corpus fraction (Phase 7E-D / Phase 7E-G).
    For HR interviews no quota is imposed (legacy 70/30 behaviour preserved).
    """
    if interview_type != InterviewType.TECHNICAL:
        return None

    frac = TECHNICAL_AREA_CORPUS_FRACTION.get(area.value)
    if frac is None:
        return None

    return max(1, round(questions_per_area * frac))
