# scripts/question_corpus/run_corpus_merge_audit.py

from services.question_corpus.audit.corpus_merge_audit import CorpusMergeAudit

DEFAULT_SOURCE_PATHS = [
    "datasets/curated/hf_import",
    "datasets/curated/interview_seed",
]


def main() -> None:

    audit = CorpusMergeAudit()

    report = audit.run(
        source_paths=DEFAULT_SOURCE_PATHS,
    )

    print()
    print("CORPUS MERGE AUDIT")
    print("=" * 60)
    print()

    print("SOURCES")
    print("-" * 60)

    for source in report.sources:

        print(f"path:     {source.path}")
        print(f"count:    {source.question_count}")
        print(f"areas:    {source.areas_distribution}")
        print()

    print("MERGE TOTALS")
    print("-" * 60)
    print(f"raw_count:              {report.merge_totals.raw_count}")
    print(f"unique_id_count:          {report.merge_totals.unique_id_count}")
    print(f"unique_text_count:        {report.merge_totals.unique_text_count}")
    print(f"duplicate_text_count:     {report.merge_totals.duplicate_text_count}")
    print()

    print("SCHEMA VALIDATION")
    print("-" * 60)
    print(f"total_questions: {report.schema_validation.total_questions}")
    print(f"total_issues:    {report.schema_validation.total_issues}")
    print(f"errors:          {report.schema_validation.errors}")
    print(f"warnings:        {report.schema_validation.warnings}")

    if report.schema_validation.issues:

        print()
        print("schema issues:")

        for issue in report.schema_validation.issues:

            print(
                f"  [{issue.severity}] "
                f"{issue.category}: "
                f"{issue.message}"
            )

    print()
    print("NEAR DUPLICATES (TOKEN JACCARD @ 0.90)")
    print("-" * 60)
    print(f"pairs: {len(report.near_duplicates_token)}")

    for issue in report.near_duplicates_token:

        print(
            f"  [{issue.severity}] "
            f"{issue.category} "
            f"id={issue.question_id}: "
            f"{issue.message}"
        )

    print()
    print("STATISTICS")
    print("-" * 60)
    print(f"total_questions:       {report.statistics.total_questions}")
    print(f"average_quality_score: {report.statistics.average_quality_score}")
    print(f"roles:                 {report.statistics.roles_distribution}")
    print(f"areas:                 {report.statistics.areas_distribution}")
    print(f"domains:               {report.statistics.domains_distribution}")
    print(f"difficulties:          {report.statistics.difficulty_distribution}")
    print()

    print("DIAGNOSTICS")
    print("-" * 60)
    print(f"total_questions:      {report.diagnostics.total_questions}")
    print(f"unique_questions:     {report.diagnostics.unique_questions}")
    print(f"duplicate_questions:  {report.diagnostics.duplicate_questions}")
    print(f"duplicate_ratio:      {report.diagnostics.duplicate_ratio}")
    print(f"role_distribution:    {report.diagnostics.role_distribution}")
    print(f"level_distribution:   {report.diagnostics.level_distribution}")
    print(f"area_distribution:    {report.diagnostics.area_distribution}")
    print(f"source_distribution:  {report.diagnostics.source_distribution}")
    print()

    print("BALANCING")
    print("-" * 60)
    print(f"total_issues: {report.balancing.total_issues}")

    for issue in report.balancing.issues:

        print(
            f"  [{issue.severity}] "
            f"{issue.dimension}={issue.value} "
            f"count={issue.count}: "
            f"{issue.recommendation}"
        )

    print()
    print("FULL JSON REPORT")
    print("-" * 60)
    print(
        report.model_dump_json(
            indent=2,
        )
    )
    print()


if __name__ == "__main__":

    main()
