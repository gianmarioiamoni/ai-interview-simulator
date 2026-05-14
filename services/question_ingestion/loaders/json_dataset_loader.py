# services/question_ingestion/loaders/json_dataset_loader.py

import json

from pathlib import Path
from typing import List

from services.question_ingestion.contracts import (
    RawQuestionRecord,
)


class JSONDatasetLoader:

    # =====================================================
    # PUBLIC
    # =====================================================

    def load(
        self,
        dataset_path: str,
        source: str,
    ) -> List[RawQuestionRecord]:

        path = Path(dataset_path)

        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")

        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        if not isinstance(raw_data, list):
            raise ValueError("Dataset root must be a JSON array")

        records: List[RawQuestionRecord] = []

        for item in raw_data:

            if not isinstance(item, dict):
                continue

            records.append(
                RawQuestionRecord(
                    source=source,
                    raw_payload=item,
                )
            )

        return records
