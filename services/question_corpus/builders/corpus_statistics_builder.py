# services/question_corpus/builders/corpus_statistics_builder.py

from statistics import mean

from services.question_corpus.contracts.curated_corpus import CuratedCorpus
from services.question_corpus.contracts.corpus_statistics import CorpusStatistics


class CorpusStatisticsBuilder:

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        corpus: CuratedCorpus,
    ) -> CorpusStatistics:

        questions = corpus.questions

        if not questions:

            return CorpusStatistics(
                total_questions=0,
                total_roles=0,
                total_areas=0,
                total_domains=0,
                average_quality_score=0.0,
            )

        unique_roles = {q.role for q in questions}

        unique_areas = {q.area for q in questions}

        unique_domains = {domain for q in questions for domain in q.domains}

        avg_quality = mean(q.quality_score for q in questions)

        return CorpusStatistics(
            total_questions=len(questions),
            total_roles=len(unique_roles),
            total_areas=len(unique_areas),
            total_domains=len(unique_domains),
            average_quality_score=round(
                avg_quality,
                2,
            ),
        )
