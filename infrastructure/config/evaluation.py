# infrastructure/config/evaluation.py
# Single source of truth for all evaluation governance thresholds, weights, and constants.

# =============================================================================
# HIRE DECISION
# =============================================================================

HIRE_SCORE_THRESHOLD: float = 85.0
LEAN_HIRE_SCORE_THRESHOLD: float = 70.0
LEAN_NO_HIRE_SCORE_THRESHOLD: float = 60.0

# =============================================================================
# DIMENSION GATE RULES
# =============================================================================

SYSTEM_DESIGN_GATE_THRESHOLD: float = 60.0
SYSTEM_DESIGN_PENALTY: float = 0.9

TECHNICAL_DEPTH_GATE_THRESHOLD: float = 50.0
TECHNICAL_DEPTH_PENALTY: float = 0.95

# =============================================================================
# SCORING — Per-question
# =============================================================================

WRITTEN_PASS_THRESHOLD: float = 60.0
WRITTEN_QUALITY_CORRECT_THRESHOLD: float = 75.0
WRITTEN_QUALITY_PARTIAL_THRESHOLD: float = 50.0

CODING_QUALITY_CORRECT_THRESHOLD: float = 80.0
CODING_QUALITY_PARTIAL_THRESHOLD: float = 50.0
CODING_QUALITY_IMPROVEMENT_THRESHOLD: float = 90.0

EXECUTION_SLOW_MS: float = 300.0
EXECUTION_FAST_MS: float = 50.0
EXECUTION_SLOW_PENALTY: float = 5.0
EXECUTION_FAST_BONUS: float = 2.0

# =============================================================================
# SCORING — Interview-level
# =============================================================================

ENRICHMENT_ALPHA: float = 0.3

LEVEL_POOR_THRESHOLD: float = 50.0
LEVEL_AVERAGE_THRESHOLD: float = 65.0
LEVEL_STRONG_THRESHOLD: float = 80.0

HIRING_PROBABILITY_WEAKEST_LOW: float = 70.0
HIRING_PROBABILITY_WEAKEST_HIGH: float = 90.0
HIRING_PROBABILITY_WEAKEST_LOW_PENALTY: float = 5.0
HIRING_PROBABILITY_WEAKEST_HIGH_BONUS: float = 3.0

MAX_RETRY_ATTEMPTS: int = 3

# =============================================================================
# SIGNAL EXTRACTOR WEIGHTS
# =============================================================================

SIGNAL_PRIMARY_ERROR_WEIGHT: float = 0.6
SIGNAL_FAILED_TEST_PS_WEIGHT: float = 0.2
SIGNAL_TEST_ERROR_TD_WEIGHT: float = 0.3
SIGNAL_FAILURE_RATIO_PS_WEIGHT: float = 0.4
SIGNAL_PERFECT_PS_WEIGHT: float = 0.6
SIGNAL_PERFECT_TD_WEIGHT: float = 0.4
SIGNAL_PASS_RATE_PS_WEIGHT: float = 0.4
SIGNAL_PASS_RATE_THRESHOLD: float = 0.7
SIGNAL_SLOW_EXEC_SD_WEIGHT: float = 0.3
SIGNAL_SLOW_EXEC_MS: float = 200.0

# =============================================================================
# FEEDBACK CONFIDENCE CONSTANTS
# =============================================================================

FEEDBACK_CONFIDENCE_WRITTEN: float = 0.9
FEEDBACK_CONFIDENCE_SUCCESS: float = 0.95
FEEDBACK_CONFIDENCE_SUCCESS_PARTIAL: float = 0.85
FEEDBACK_CONFIDENCE_HINT: float = 0.85
FEEDBACK_CONFIDENCE_SCORE: float = 0.95
FEEDBACK_CONFIDENCE_RUNTIME_ERROR: float = 0.95
FEEDBACK_CONFIDENCE_FALLBACK: float = 0.4

FEEDBACK_CONFIDENCE_MIN_QUESTIONS: int = 2
FEEDBACK_CONFIDENCE_LOW_SAMPLE: float = 0.7

# =============================================================================
# REPORT THRESHOLDS
# =============================================================================

REPORT_DIMENSION_STRONG_THRESHOLD: float = 85.0
REPORT_DIMENSION_MODERATE_THRESHOLD: float = 70.0

REPORT_SCORE_GREEN_THRESHOLD: float = 80.0
REPORT_SCORE_YELLOW_THRESHOLD: float = 60.0

REPORT_CONFIDENCE_HIGH_THRESHOLD: float = 0.85
REPORT_CONFIDENCE_MODERATE_THRESHOLD: float = 0.65

REPORT_IMPACT_HIGH_THRESHOLD: float = 60.0
REPORT_IMPACT_MEDIUM_THRESHOLD: float = 30.0

REPORT_IMPROVEMENT_PRIORITY_THRESHOLD: float = 80.0

PERCENTILE_TOP_10: float = 90.0
PERCENTILE_TOP_25: float = 75.0
PERCENTILE_ABOVE_AVG: float = 50.0
PERCENTILE_BELOW_AVG: float = 25.0

# Failure pass-rate severity bands (used in FailureBlock)
FAILURE_PASS_RATE_MINOR: float = 0.8
FAILURE_PASS_RATE_PARTIAL: float = 0.5

# =============================================================================
# NARRATIVE CLASSIFICATION BANDS
# =============================================================================

NARRATIVE_EXCELLENT_THRESHOLD: float = 90.0
NARRATIVE_STRONG_THRESHOLD: float = 80.0
NARRATIVE_MODERATE_THRESHOLD: float = 70.0

NARRATIVE_BALANCE_BALANCED_SPREAD: float = 15.0
NARRATIVE_BALANCE_SLIGHTLY_UNEVEN_SPREAD: float = 25.0

NARRATIVE_DRIVER_SIGNAL_THRESHOLD: float = 0.8
NARRATIVE_DRIVER_SCORE_THRESHOLD: float = 85.0

NARRATIVE_BLOCKER_SCORE_THRESHOLD: float = 75.0
NARRATIVE_BLOCKER_SIGNAL_THRESHOLD: float = 0.7
NARRATIVE_BLOCKER_SIGNAL_SCORE_THRESHOLD: float = 80.0

NARRATIVE_CAUSAL_SIGNAL_STRONG: float = 0.8
NARRATIVE_CAUSAL_SIGNAL_SUPPORTED: float = 0.5
NARRATIVE_CAUSAL_SIGNAL_PARTIAL: float = 0.3
NARRATIVE_CAUSAL_SCORE_WEAK: float = 70.0
NARRATIVE_CAUSAL_SCORE_GAPS: float = 80.0

NARRATIVE_FALLBACK_DRIVER_STRONG: float = 90.0
NARRATIVE_FALLBACK_DRIVER_SOLID: float = 80.0
NARRATIVE_FALLBACK_BLOCKER_DEVELOPMENT: float = 70.0

NARRATIVE_WEAKEST_BLOCKER_MILD: float = 85.0
NARRATIVE_WEAKEST_BLOCKER_MODERATE: float = 75.0

# =============================================================================
# ADAPTIVE RETRIEVAL THRESHOLDS
# =============================================================================

ADAPTIVE_WEAK_THRESHOLD: float = 0.6
ADAPTIVE_STRONG_THRESHOLD: float = 0.85

ADAPTIVE_DIFFICULTY_HIGH: int = 5
ADAPTIVE_DIFFICULTY_HIGH_SCORE: float = 0.85
ADAPTIVE_DIFFICULTY_MEDIUM: int = 4
ADAPTIVE_DIFFICULTY_MEDIUM_SCORE: float = 0.70
ADAPTIVE_DIFFICULTY_BASE: int = 3

# =============================================================================
# FOLLOW-UP / HUMANIZER
# =============================================================================
# FOLLOW_UP_SCORE_THRESHOLD migrated to infrastructure/config/settings.py (follow_up_score_threshold).
# Do not re-add here.
