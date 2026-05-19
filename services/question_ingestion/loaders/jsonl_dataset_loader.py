# services/question_ingestion/loaders/jsonl_dataset_loader.py

import json

from pathlib import Path
from typing import List

from services.question_ingestion.contracts import (
    RawQuestionRecord,
)
from services.question_ingestion.adapters.generic_dataset_adapter import (
    GenericDatasetAdapter,
)

class JSONLDatasetLoader:

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

        records: List[RawQuestionRecord] = []

        adapter = GenericDatasetAdapter()

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as f:

            for line in f:

                line = line.strip()

                if not line:
                    continue

                item = json.loads(line)

                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                records.append(
                    adapter.adapt(
                        payload=item,
                        source=source,
                        source_type="jsonl",
                        dataset_version="v1",
                    )
                )

        return records
