# scripts/test_sql_generator.py

from services.question_intelligence.sql_question_generator import SQLQuestionGenerator
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel


def main():

    generator = SQLQuestionGenerator()

    questions = generator.generate(
        role=RoleType.BACKEND_ENGINEER,  # oppure quello che hai definito
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


if __name__ == "__main__":
    main()
