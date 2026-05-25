# services/replanning/contracts/retrieval_expansion_telemetry.py

from pydantic import BaseModel

from domain.contracts.user.role import RoleType


class RetrievalExpansionTelemetry(BaseModel):

    original_role: RoleType

    expanded_roles: list[RoleType]

    recovered_candidates_count: int

    recovery_successful: bool

    retrieval_duration_ms: float

    model_config = {
        "frozen": True,
    }
