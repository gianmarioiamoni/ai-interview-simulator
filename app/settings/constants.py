# app/settings/constants.py

QUESTIONS_PER_AREA = 1 # Number of questions per area (corpus retrieval batch unit)

USE_BATCH_QUESTION_GENERATION = False

DEDUPLICATION_THRESHOLD = 0.85 # 85% similarity threshold for deduplication

# ------------------------------------------------------------
# Interview Type Constants
# ------------------------------------------------------------

INTERVIEW_TYPE_TECHNICAL = "technical"
INTERVIEW_TYPE_NON_TECHNICAL = "non-technical"

# ------------------------------------------------------------
# Seniority Level Constants
# ------------------------------------------------------------

SENIORITY_LEVEL_JUNIOR = "junior"
SENIORITY_LEVEL_MID = "mid"
SENIORITY_LEVEL_SENIOR = "senior"

# ------------------------------------------------------------
# Production Interview Configuration (Phase 7E-F validated)
# ------------------------------------------------------------

# Default total questions per interview session (standard mode).
# Validated by Phase 7E-F production readiness simulation.
DEFAULT_INTERVIEW_LENGTH = 20

# Follow-up probability applied by HumanizerPolicyEngine.
# 20% of base questions receive an adaptive follow-up (Phase 7E-D).
DEFAULT_FOLLOWUP_RATE = 0.20

# Maximum consecutive follow-ups per interview.
# Single source of truth: infrastructure/config/settings.py (max_follow_ups_per_interview).
# This re-export preserves backward compatibility for all existing imports.
from infrastructure.config.settings import settings as _settings
MAX_FOLLOW_UPS_PER_INTERVIEW: int = _settings.max_follow_ups_per_interview

# Technical interview area weights (must sum to 1.0).
# Validated by Phase 7E-C (practical allocation) and Phase 7E-F.
TECHNICAL_AREA_WEIGHTS: dict[str, float] = {
    "technical_background":           0.10,
    "technical_technical_knowledge":  0.20,
    "technical_case_study":           0.25,
    "technical_database":             0.20,
    "technical_coding":               0.25,
}

# Area-specific corpus fraction (validated by Phase 7E-D, candidate_a).
# Corpus fraction = questions drawn from the retrieval corpus.
# LLM fraction = 1 - corpus_fraction (generated on-the-fly).
# Higher corpus fraction → higher evaluation consistency.
# Lower corpus fraction → higher diversity for that area.
TECHNICAL_AREA_CORPUS_FRACTION: dict[str, float] = {
    "technical_background":           0.50,  # open-ended: high LLM variety acceptable
    "technical_technical_knowledge":  0.80,  # precision-sensitive: corpus anchoring required
    "technical_case_study":           0.60,  # complex multi-part: balance variety and depth
    "technical_database":             0.80,  # schema-precise: high corpus preferred
    "technical_coding":               0.90,  # validated test cases: corpus strongly preferred
}

# Derived: expected questions per area for DEFAULT_INTERVIEW_LENGTH = 20.
# Computed as floor(weight * 20) with remainder distributed to largest fractions.
# Manually verified: 2 + 4 + 5 + 4 + 5 = 20.
TECHNICAL_AREA_QUESTION_COUNT: dict[str, int] = {
    "technical_background":           2,
    "technical_technical_knowledge":  4,
    "technical_case_study":           5,
    "technical_database":             4,
    "technical_coding":               5,
}