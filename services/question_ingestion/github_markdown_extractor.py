# services/question_ingestion/github_markdown_extractor.py

from services.question_ingestion.contracts import GitHubDocument
from services.question_ingestion.contracts.candidate_question import CandidateQuestion
from services.question_ingestion.markdown_section_parser import MarkdownSectionParser
from services.question_ingestion.semantic_candidate_extractor import SemanticCandidateExtractor


class GitHubMarkdownExtractor:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._section_parser = MarkdownSectionParser()

        self._candidate_extractor = SemanticCandidateExtractor()

    # =====================================================
    # PUBLIC
    # =====================================================

    def extract_questions(
        self,
        document: GitHubDocument,
    ) -> list[CandidateQuestion]:

        sections = self._section_parser.parse(
            content=document.content,
            source_path=document.path,
        )

        return self._candidate_extractor.extract(
            sections=sections,
        )
