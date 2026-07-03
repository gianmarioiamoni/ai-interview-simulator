# domain/contracts/replay/replay_enums.py
# ADR-026 §B2, §B3, §B5 — Replay mode and level enumerations

from __future__ import annotations

from enum import Enum


class ReplayMode(str, Enum):
    """Replay operation mode (ADR-026 §D ReplayManifest).

    Standard: normal replay from KnowledgeSnapshot.
    Migration: exceptional, operator-triggered reconstruction (MP-01).
    Recovery: exceptional, operator-triggered recovery path.
    """

    STANDARD = "standard"
    MIGRATION = "migration"
    RECOVERY = "recovery"


class ReplayLevel(str, Enum):
    """Replay depth level (ADR-026 §B3).

    Level 1 — Presentation Replay: candidate-facing view.
    Level 2 — Knowledge Replay: operator / calibration view with provenance.
    Level 3 — Reasoning Replay: reserved for V1.3+.
    """

    PRESENTATION = "level_1_presentation"
    KNOWLEDGE = "level_2_knowledge"
    REASONING = "level_3_reasoning_reserved"


class ReplaySourcePriority(int, Enum):
    """Source priority levels in the Replay source hierarchy (ADR-026 §B2).

    Priority 1 is the highest (most authoritative) source.
    """

    KNOWLEDGE_SNAPSHOT = 1
    CANDIDATE_PROFILE_SNAPSHOT = 2
    NARRATIVE = 3
    COACHING_PLAN = 4
    REPLAY_METADATA = 5
    FEATURE_ENGINE_RECOMPUTATION = 6
