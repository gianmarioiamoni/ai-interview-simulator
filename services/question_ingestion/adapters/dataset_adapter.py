# services/question_ingestion/adapters/dataset_adapter.py

from abc import ABC
from abc import abstractmethod

from services.question_ingestion.contracts import (
    RawQuestionRecord,
)


class DatasetAdapter(ABC):

    # =====================================================
    # PUBLIC
    # =====================================================

    @abstractmethod
    def adapt(
        self,
        payload: dict,
        source: str,
        source_type: str,
        dataset_version: str,
    ) -> RawQuestionRecord:

        pass
