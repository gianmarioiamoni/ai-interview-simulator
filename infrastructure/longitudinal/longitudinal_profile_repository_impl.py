# infrastructure/longitudinal/longitudinal_profile_repository_impl.py
# EPIC-02 — P3/C1 — Concrete implementation of LongitudinalProfileRepository
# Governing: ADR-034 Decision 8, EPIC-02-DATA-MODEL.md §4–§7
#
# Technology: JSON files, one file per candidate_identity_id.
# Serialization: Pydantic v2 model_dump_json / model_validate_json (lossless round-trip).
# Replace-on-write: write atomically via temp file + rename to avoid partial-write corruption.
# Serialization format satisfies DATA-MODEL.md §7 requirements:
#   - tuple[T,...] serialised as JSON arrays (Pydantic v2 native)
#   - datetime serialised as ISO 8601 UTC strings (Pydantic v2 native with timezone-aware datetimes)
#   - extra="forbid" on all domain models prevents unknown-field deserialization

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional

from domain.contracts.longitudinal.longitudinal_profile import LongitudinalProfile
from domain.contracts.longitudinal.longitudinal_profile_repository import (
    LongitudinalProfileRepository,
)


class JsonFileLongitudinalProfileRepository(LongitudinalProfileRepository):
    """JSON-file-backed implementation of LongitudinalProfileRepository.

    Storage layout: one JSON file per candidate, named <candidate_identity_id>.json,
    located inside `storage_dir`. The directory is created on first use.

    Replace-on-write semantics are achieved via atomic rename (write to tmp, rename).
    This prevents partial-write corruption if the process is interrupted.

    Satisfies DATA-MODEL.md §4.1–§4.3 and §7 serialization rules.
    """

    def __init__(self, storage_dir: Path) -> None:
        self._storage_dir = storage_dir

    def _ensure_dir(self) -> None:
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def _profile_path(self, candidate_identity_id: str) -> Path:
        return self._storage_dir / f"{candidate_identity_id}.json"

    def get(self, candidate_identity_id: str) -> Optional[LongitudinalProfile]:
        """Return the stored LongitudinalProfile, or None if absent."""
        path = self._profile_path(candidate_identity_id)
        if not path.exists():
            return None
        raw = path.read_text(encoding="utf-8")
        return LongitudinalProfile.model_validate_json(raw)

    def save(self, profile: LongitudinalProfile) -> None:
        """Persist profile using atomic replace-on-write semantics."""
        self._ensure_dir()
        path = self._profile_path(profile.candidate_identity_id)
        serialized = profile.model_dump_json()
        dir_fd = self._storage_dir
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=dir_fd,
            suffix=".tmp",
            delete=False,
        ) as tmp:
            tmp.write(serialized)
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, path)

    def exists(self, candidate_identity_id: str) -> bool:
        """Return True if a profile file exists for the given candidate."""
        return self._profile_path(candidate_identity_id).exists()
