# services/question_ingestion/dataset_registry_loader.py

import json

from pathlib import Path

from services.question_ingestion.contracts.dataset_descriptor import (
    DatasetDescriptor,
)


class DatasetRegistryLoader:

    # =====================================================
    # PUBLIC
    # =====================================================

    def load(
        self,
        path: str,
    ) -> list[DatasetDescriptor]:

        registry_path = Path(path)

        with open(
            registry_path,
            "r",
            encoding="utf-8",
        ) as f:

            raw_data = json.load(f)

        return [DatasetDescriptor(**item) for item in raw_data]
