# services/question_ingestion/adapters/adapter_registry.py

from services.question_ingestion.adapters.dataset_adapter import (
    DatasetAdapter,
)

from services.question_ingestion.adapters.generic_dataset_adapter import (
    GenericDatasetAdapter,
)

from services.question_ingestion.adapters.system_design_dataset_adapter import (
    SystemDesignDatasetAdapter,
)


class AdapterRegistry:

    # =====================================================
    # PUBLIC
    # =====================================================

    def get(
        self,
        adapter_name: str,
    ) -> DatasetAdapter:

        registry = {
            "generic": (GenericDatasetAdapter()),
            "system_design": (SystemDesignDatasetAdapter()),
        }

        adapter = registry.get(adapter_name)

        if adapter is None:

            raise ValueError(("Unknown adapter: " f"{adapter_name}"))

        return adapter
