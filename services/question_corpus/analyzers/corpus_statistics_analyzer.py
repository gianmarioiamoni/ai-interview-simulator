# services/question_corpus/analyzers/corpus_statistics_analyzer.py

from collections import Counter

from domain.contracts.corpus import QuestionCorpus

from services.question_corpus.contracts.corpus_statistics_report import CorpusStatisticsReport


class CorpusStatisticsAnalyzer:

    # =====================================================
    # PUBLIC
    # =====================================================

    def analyze(
        self,
        corpus: QuestionCorpus,
    ) -> CorpusStatisticsReport:

        roles = Counter()
        areas = Counter()
        domains = Counter()
        difficulties = Counter()

        quality_scores: list[float] = []

        for question in corpus.questions:

            roles[question.role.value] += 1

            areas[question.area.value] += 1

            difficulties[question.difficulty] += 1

            for domain in question.domains:

                domains[domain] += 1

            quality_scores.append(
                question.quality_score,
            )

        average_quality = 0.0

        if quality_scores:

            average_quality = round(
                sum(quality_scores) / len(quality_scores),
                2,
            )

        return CorpusStatisticsReport(
            total_questions=len(corpus.questions),
            roles_distribution=dict(roles),
            areas_distribution=dict(areas),
            domains_distribution=dict(domains),
            difficulty_distribution=dict(difficulties),
            average_quality_score=average_quality,
        )
