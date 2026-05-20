# services/question_ingestion/dataset_discovery_registry_loader.py

import json

from pathlib import Path

from services.question_ingestion.contracts import (
    DatasetCandidate,
)


class DatasetDiscoveryRegistryLoader:

    # =====================================================
    # PUBLIC
    # =====================================================

    def load(
        self,
        path: str,
    ) -> list[DatasetCandidate]:

        registry_path = Path(path)

        if not registry_path.exists():

            raise FileNotFoundError(("Discovery registry " "not found: " f"{path}"))

        with open(
            registry_path,
            "r",
            encoding="utf-8",
        ) as f:

            raw_data = json.load(f)

        return [DatasetCandidate(**item) for item in raw_data]
