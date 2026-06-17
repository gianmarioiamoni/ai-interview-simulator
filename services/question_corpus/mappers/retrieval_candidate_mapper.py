# services/question_corpus/mappers/retrieval_candidate_mapper.py

from datetime import datetime, timezone

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.user.role import Role, RoleType

from app.core.logger import get_logger

_logger = get_logger(__name__)
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.utils.domain_parser import parse_domains
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata


# Sentinel used because current corpus index does not provide per-document ingestion timestamps.
UNAVAILABLE_INDEX_INGESTION_TIMESTAMP_SENTINEL = datetime(
    1970,
    1,
    1,
    tzinfo=timezone.utc,
)

CORPUS_INDEX_DATASET_VERSION = "corpus_index_unversioned"

LEGACY_PAGE_CONTENT_MARKERS = (
    "Role:",
    "Area:",
    "Seniority:",
    "Domains:",
    "Topics:",
)

LEGACY_METADATA_LINE_PREFIXES = (
    "Role:",
    "Area:",
    "Seniority:",
    "Domains:",
    "Topics:",
)


class CorpusCandidateMappingError(ValueError):
    pass


class RetrievalCandidateMapper:

    # =====================================================
    # PUBLIC
    # =====================================================

    def map(
        self,
        candidates: list[RetrievalCandidate],
    ) -> list[QuestionBankItem]:
        items: list[QuestionBankItem] = []
        for candidate in candidates:
            try:
                items.append(self.map_one(candidate))
            except CorpusCandidateMappingError as exc:
                doc_id = candidate.document.metadata.get("document_id", "<unknown>")
                _logger.warning(
                    f"[RetrievalCandidateMapper] Skipping document {doc_id!r}: {exc}"
                )
        return items

    def map_one(
        self,
        candidate: RetrievalCandidate,
    ) -> QuestionBankItem:

        metadata = candidate.document.metadata

        text = self._clean_page_content(
            candidate.document.page_content,
        )

        if not text or not text.strip():
            raise CorpusCandidateMappingError("Empty candidate page_content.")

        document_id = self._required_str(
            metadata=metadata,
            key="document_id",
        )

        role_value = self._required_str(
            metadata=metadata,
            key="role",
        )

        area_value = self._required_str(
            metadata=metadata,
            key="area",
        )

        seniority_value = self._required_str(
            metadata=metadata,
            key="seniority",
        )

        difficulty_raw = metadata.get("difficulty")

        if difficulty_raw is None:
            raise CorpusCandidateMappingError("Missing required metadata: difficulty.")

        try:
            difficulty = int(difficulty_raw)
        except (TypeError, ValueError) as exc:
            raise CorpusCandidateMappingError(
                f"Invalid difficulty value: {difficulty_raw!r}."
            ) from exc

        difficulty = max(
            1,
            min(5, difficulty),
        )

        source_name = self._required_str(
            metadata=metadata,
            key="source",
        )

        retrieval_score = (
            candidate.adaptive_score
            if candidate.adaptive_score is not None
            else candidate.final_score
        )

        ingestion_metadata = IngestionMetadata(
            source_name=source_name,
            source_type="question_corpus",
            dataset_version=CORPUS_INDEX_DATASET_VERSION,
            ingestion_timestamp=UNAVAILABLE_INDEX_INGESTION_TIMESTAMP_SENTINEL,
        )

        provenance = QuestionProvenance(
            origin_type=QuestionOriginType.RETRIEVAL,
            source_name=source_name,
            source_type="question_corpus",
            dataset_version=CORPUS_INDEX_DATASET_VERSION,
            retrieval_score=retrieval_score,
        )

        try:
            role_type = RoleType(role_value)
            # RoleType.OTHER requires a custom_name (domain constraint) and is
            # not a valid corpus role — treat it like any other unknown value.
            if role_type == RoleType.OTHER:
                raise ValueError(f"role_value {role_value!r} is not a valid corpus role")
            role = Role(type=role_type)
        except ValueError:
            raise CorpusCandidateMappingError(
                f"Invalid corpus role value: {role_value!r}. "
                "Document will be skipped by map()."
            )

        try:
            area = InterviewArea(area_value)
        except ValueError as exc:
            raise CorpusCandidateMappingError(
                f"Invalid area value: {area_value!r}."
            ) from exc

        try:
            level = SeniorityLevel(seniority_value)
        except ValueError as exc:
            raise CorpusCandidateMappingError(
                f"Invalid seniority value: {seniority_value!r}."
            ) from exc

        domains = parse_domains(metadata.get("domains"))

        return QuestionBankItem(
            id=document_id,
            text=text,
            interview_type=InterviewType.TECHNICAL,
            role=role,
            area=area,
            level=level,
            difficulty=difficulty,
            domains=domains,
            ingestion_metadata=ingestion_metadata,
            provenance=provenance,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _clean_page_content(
        self,
        page_content: str,
    ) -> str:

        if not any(
            marker in page_content for marker in LEGACY_PAGE_CONTENT_MARKERS
        ):
            return page_content.strip()

        cleaned_lines: list[str] = []

        for line in page_content.splitlines():

            stripped = line.strip()

            if any(
                stripped.startswith(prefix)
                for prefix in LEGACY_METADATA_LINE_PREFIXES
            ):
                continue

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    def _required_str(
        self,
        metadata: dict,
        key: str,
    ) -> str:

        value = metadata.get(key)

        if value is None:
            raise CorpusCandidateMappingError(f"Missing required metadata: {key}.")

        if not isinstance(value, str) or not value.strip():
            raise CorpusCandidateMappingError(f"Invalid required metadata: {key}.")

        return value.strip()
