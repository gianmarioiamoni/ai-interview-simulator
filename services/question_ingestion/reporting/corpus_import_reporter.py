# services/question_ingestion/reporting/corpus_import_reporter.py

from collections import Counter
from pathlib import Path

from domain.contracts.corpus.curated_question import CuratedQuestion


class CorpusImportReporter:

    # =====================================================
    # PUBLIC
    # =====================================================

    def print_summary(
        self,
        raw_count: int,
        curated_questions: list[CuratedQuestion],
        export_path: Path,
    ) -> None:

        print()
        print(f"RAW RECORDS:       {raw_count}")
        print(f"CURATED QUESTIONS: {len(curated_questions)}")
        print(f"EXPORT PATH:       {export_path}")

        if export_path.exists():
            size_bytes = export_path.stat().st_size
            print(f"EXPORT FILE SIZE:  {size_bytes} bytes")

        print()
        self._print_distribution(
            title="AREA DISTRIBUTION",
            counter=Counter(
                question.area.value for question in curated_questions
            ),
        )

        self._print_distribution(
            title="LEVEL DISTRIBUTION",
            counter=Counter(
                question.seniority.value for question in curated_questions
            ),
        )

        self._print_distribution(
            title="DIFFICULTY DISTRIBUTION",
            counter=Counter(
                str(question.difficulty) for question in curated_questions
            ),
        )

    def print_sample_questions(
        self,
        curated_questions: list[CuratedQuestion],
        sample_size: int = 10,
    ) -> None:

        print()
        print(f"FIRST {sample_size} CURATED QUESTIONS")
        print()

        for question in curated_questions[:sample_size]:

            print(f"id:         {question.id}")
            print(f"area:       {question.area.value}")
            print(f"role:       {question.role.value}")
            print(f"level:      {question.seniority.value}")
            print(f"difficulty: {question.difficulty}")
            print(f"source:     {question.source}")
            print(f"question:   {question.question}")
            print()

    # =====================================================
    # INTERNALS
    # =====================================================

    def _print_distribution(
        self,
        title: str,
        counter: Counter[str],
    ) -> None:

        print(title)

        if not counter:
            print("  (empty)")
            print()
            return

        for key, count in sorted(counter.items()):
            print(f"  {key}: {count}")

        print()
