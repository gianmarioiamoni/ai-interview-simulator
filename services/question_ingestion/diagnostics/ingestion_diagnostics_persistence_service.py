# services/question_ingestion/diagnostics/ingestion_diagnostics_persistence_service.py

from datetime import datetime
from pathlib import Path
import json

from services.question_ingestion.diagnostics.ingestion_diagnostics_report import IngestionDiagnosticsReport


class IngestionDiagnosticsPersistenceService:

    REPORTS_DIR = Path("data/ingestion_reports")

    # =====================================================
    # PUBLIC
    # =====================================================

    def persist(
        self,
        report: IngestionDiagnosticsReport,
    ) -> Path:

        self.REPORTS_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        filename = f"{timestamp}_{report.dataset_name}.json"

        output_path = self.REPORTS_DIR / filename

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                report.model_dump(),
                file,
                indent=2,
            )

        return output_path
