# services/question_ingestion/loaders/csv_dataset_loader.py

import csv

from pathlib import Path
from typing import List

from services.question_ingestion.contracts import (
    RawQuestionRecord,
)
from services.question_ingestion.adapters.generic_dataset_adapter import (
    GenericDatasetAdapter,
)

class CSVDatasetLoader:

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

            reader = csv.DictReader(f)

            for row in reader:

                records.append(
                    adapter.adapt(
                        payload=dict(row),
                        source=source,
                        source_type="csv",
                        dataset_version="v1",
                    )
                )

        return records
