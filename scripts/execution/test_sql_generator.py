# scripts/test_sql_generator.py

from services.question_intelligence.sql_question_generator import SQLQuestionGenerator
from services.execution_engine import ExecutionEngine

from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel


def main():

    # ---------------------------------------------------------
    # GENERATION
    # ---------------------------------------------------------

    generator = SQLQuestionGenerator()

    questions = generator.generate(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        n=1,
    )

    q = questions[0]

    print("\n=== QUESTION ===")
    print(q.prompt)

    print("\n=== TYPE ===")
    print(q.type)

    print("\n=== REFERENCE QUERY ===")
    print(q.reference_solution)

    print("\n=== TEST CASES ===")
    for tc in q.sql_test_cases:
        print(f"- {tc.id}: {tc.expected_query} (ordered={tc.ordered})")

    # ---------------------------------------------------------
    # EXECUTION TEST (NEW)
    # ---------------------------------------------------------

    print("\n=== EXECUTION TEST ===")

    engine = ExecutionEngine()

    # usiamo la reference come risposta "corretta"
    result = engine.execute(
        question=q,
        user_answer=q.reference_solution,
    )

    print("\n=== EXECUTION RESULT ===")
    print(f"Success: {result.success}")
    print(f"Status: {result.status}")
    print(f"Passed tests: {result.passed_tests}/{result.total_tests}")
    print(f"Execution time (ms): {result.execution_time_ms}")

    if result.error:
        print("\n=== ERROR ===")
        print(result.error)

    print("\n=== OUTPUT ===")
    print(result.output)


if __name__ == "__main__":
    main()
