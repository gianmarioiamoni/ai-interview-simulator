# services/question_ingestion/loaders/csv_dataset_loader.py

import csv

from pathlib import Path
from typing import List

from services.question_ingestion.contracts import (
    RawQuestionRecord,
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

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:

                records.append(
                    RawQuestionRecord(
                        source=source,
                        raw_payload=dict(row),
                    )
                )

        return records
