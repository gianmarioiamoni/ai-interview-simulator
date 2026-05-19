# services/question_ingestion/loaders/huggingface_dataset_loader.py

from typing import List

from datasets import load_dataset

from services.question_ingestion.contracts import (
    RawQuestionRecord,
)

from services.question_ingestion.adapters.dataset_adapter import (
    DatasetAdapter,
)


class HuggingFaceDatasetLoader:

    # =====================================================
    # PUBLIC
    # =====================================================

    def load(
        self,
        dataset_name: str,
        split: str,
        source: str,
        source_type: str,
        dataset_version: str,
        adapter: DatasetAdapter,
        limit: int = 100,
    ) -> List[RawQuestionRecord]:

        dataset = load_dataset(
            dataset_name,
            split=split,
        )

        records: List[RawQuestionRecord] = []

        for index, item in enumerate(dataset):

            if index >= limit:
                break

            if not isinstance(item, dict):
                continue

            record = adapter.adapt(
                payload=item,
                source=source,
                source_type=source_type,
                dataset_version=dataset_version,
            )

            records.append(record)

        return records
