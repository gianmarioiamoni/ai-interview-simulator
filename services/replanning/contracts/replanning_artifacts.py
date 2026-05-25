# services/replanning/contracts/replanning_artifacts.py

from pydantic import BaseModel

from services.replanning.contracts.retrieval_expansion_telemetry import (
    RetrievalExpansionTelemetry,
)


class ReplanningArtifacts(BaseModel):

    retrieval_expansion_telemetry: RetrievalExpansionTelemetry | None = None

    model_config = {
        "frozen": True,
    }
