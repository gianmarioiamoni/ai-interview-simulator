"""
scripts/audit_report_quality.py

Product quality audit: runs 6 synthetic interviews through the production
evaluation pipeline and captures report content for human review.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env before any settings import
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from unittest.mock import Mock
from typing import List

from domain.contracts.question.question import Question, QuestionType, QuestionDifficulty
from domain.contracts.question.question_result import QuestionResult
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.interview.interview_context_profile import InterviewContextProfile
from domain.contracts.interview.business_context import BusinessContext
from domain.contracts.interview_state import InterviewState
from domain.contracts.user.role import Role, RoleType
from domain.contracts.interview.answer import Answer
from services.interview_evaluation_service import InterviewEvaluationService
from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.views.report_view import build_report_markdown


# ---------------------------------------------------------------------------
# Real LLM helper (uses whatever LLM is configured in the project)
# ---------------------------------------------------------------------------

def get_real_llm():
    try:
        from infrastructure.llm.llm_adapter import DefaultLLMAdapter
        return DefaultLLMAdapter()
    except Exception as e:
        print(f"WARNING: Could not create DefaultLLMAdapter: {e}")
    # Fallback mock
    llm = Mock()
    llm.invoke.return_value = type("R", (), {"content": "Strong technical performance with clear communication skills."})()
    llm.invoke_json.side_effect = ValueError("mock")
    return llm


# ---------------------------------------------------------------------------
# Builder helpers
# ---------------------------------------------------------------------------

def make_question(qid: str, area: InterviewArea, prompt: str, difficulty: QuestionDifficulty = QuestionDifficulty.MEDIUM) -> Question:
    return Question(
        id=qid,
        area=area,
        type=QuestionType.WRITTEN,
        prompt=prompt,
        difficulty=difficulty,
    )


def make_result(qid: str, score: float, feedback: str, strengths: List[str], weaknesses: List[str]) -> QuestionResult:
    return QuestionResult(
        question_id=qid,
        evaluation=QuestionEvaluation(
            question_id=qid,
            score=score,
            max_score=100.0,
            feedback=feedback,
            strengths=strengths,
            weaknesses=weaknesses,
            passed=score >= 60,
        ),
        execution=None,
        ai_hint=None,
        hint_level=None,
    )


def build_state(role: RoleType, seniority: str, company: str,
                context_profile: InterviewContextProfile,
                questions: List[Question], answers: List[Answer]) -> InterviewState:
    return InterviewState(
        interview_id=f"audit-{role.value}-{seniority}",
        role=Role(type=role),
        company=company,
        interview_type=InterviewType.TECHNICAL,
        language="en",
        questions=questions,
        answers=answers,
        current_question_index=len(questions),
        seniority_level=seniority,
        context_profile=context_profile,
    )


# ---------------------------------------------------------------------------
# 6 Candidate Profiles
# ---------------------------------------------------------------------------

PROFILES = []

# ── 1. Junior Backend Generic ────────────────────────────────────────────────
def profile_junior_backend_generic():
    questions = [
        make_question("q1", InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
                      "Explain the difference between REST and RPC.", QuestionDifficulty.EASY),
        make_question("q2", InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
                      "What is a database index and when would you use one?", QuestionDifficulty.EASY),
        make_question("q3", InterviewArea.TECH_CODING,
                      "Write a function to find duplicates in a list.", QuestionDifficulty.EASY),
        make_question("q4", InterviewArea.TECH_CASE_STUDY,
                      "Design a basic URL shortener.", QuestionDifficulty.MEDIUM),
    ]
    results = [
        make_result("q1", 55, "Basic understanding of REST but confused RPC with gRPC.",
                    ["Mentioned HTTP verbs correctly"], ["Didn't explain statelessness", "No mention of contracts"]),
        make_result("q2", 62, "Explained B-tree indexes but missed composite index trade-offs.",
                    ["Correct B-tree description", "Mentioned SELECT speed"], ["No mention of write overhead", "Missed covering indexes"]),
        make_result("q3", 70, "Correct solution using a set; missed edge cases.",
                    ["Used set for O(n)", "Clean syntax"], ["No null handling", "No test cases considered"]),
        make_result("q4", 45, "Listed components but no capacity estimates.",
                    ["Mentioned hashing"], ["No database choice justification", "No scaling considerations", "No collision handling"]),
    ]
    context = InterviewContextProfile(business_context=BusinessContext.GENERIC)
    answers = [Answer(question_id=q.id, content="...", attempt=1) for q in questions]
    state = build_state(RoleType.BACKEND_ENGINEER, "junior", "TechCo", context, questions, answers)
    return "Junior Backend Generic", state, results, questions


# ── 2. Mid Backend Fintech ────────────────────────────────────────────────────
def profile_mid_backend_fintech():
    questions = [
        make_question("q1", InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
                      "How do you ensure ACID compliance in a payment processing system?", QuestionDifficulty.MEDIUM),
        make_question("q2", InterviewArea.TECH_CASE_STUDY,
                      "Design a ledger service for a digital wallet.", QuestionDifficulty.HARD),
        make_question("q3", InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
                      "Explain idempotency keys and why they matter in payment APIs.", QuestionDifficulty.MEDIUM),
        make_question("q4", InterviewArea.TECH_CODING,
                      "Implement a thread-safe rate limiter.", QuestionDifficulty.HARD),
        make_question("q5", InterviewArea.TECH_DATABASE,
                      "Explain how you would handle double-spend prevention at database level.", QuestionDifficulty.HARD),
    ]
    results = [
        make_result("q1", 72, "Good ACID coverage; missed isolation levels nuance.",
                    ["Correct transaction boundaries", "Mentioned rollback"], ["Confused REPEATABLE READ vs SERIALIZABLE", "No mention of distributed transactions"]),
        make_result("q2", 65, "Designed append-only ledger but no CQRS pattern.",
                    ["Append-only design", "Mentioned event sourcing vaguely"], ["No CQRS", "No reconciliation process", "Missed audit trail requirements"]),
        make_result("q3", 80, "Solid idempotency explanation with practical examples.",
                    ["UUID key strategy", "Explained retry safety", "Mentioned 24h TTL"], ["No mention of distributed key storage", "Missed partial failures"]),
        make_result("q4", 58, "Used mutex but implementation had race condition.",
                    ["Correct token bucket concept"], ["Race condition in check-then-act", "No distributed lock consideration", "Missed sliding window alternative"]),
        make_result("q5", 68, "Used SELECT FOR UPDATE correctly but no optimistic locking.",
                    ["SELECT FOR UPDATE mentioned", "Understood serialization"], ["No optimistic locking", "No mention of application-level checks"]),
    ]
    context = InterviewContextProfile(
        company_description="A fintech startup processing payments and transactions",
        business_context=BusinessContext.FINTECH,
    )
    answers = [Answer(question_id=q.id, content="...", attempt=1) for q in questions]
    state = build_state(RoleType.BACKEND_ENGINEER, "mid", "PayFlow", context, questions, answers)
    return "Mid Backend Fintech", state, results, questions


# ── 3. Senior Backend Healthcare ──────────────────────────────────────────────
def profile_senior_backend_healthcare():
    questions = [
        make_question("q1", InterviewArea.TECH_CASE_STUDY,
                      "Design a HIPAA-compliant EHR API with audit logging.", QuestionDifficulty.HARD),
        make_question("q2", InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
                      "How do you handle HL7/FHIR data ingestion at scale?", QuestionDifficulty.HARD),
        make_question("q3", InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
                      "Explain microservices trade-offs in a clinical workflow system.", QuestionDifficulty.HARD),
        make_question("q4", InterviewArea.TECH_DATABASE,
                      "Design a patient timeline data model supporting temporal queries.", QuestionDifficulty.HARD),
        make_question("q5", InterviewArea.TECH_CODING,
                      "Implement a circuit breaker for downstream clinical service calls.", QuestionDifficulty.HARD),
    ]
    results = [
        make_result("q1", 60, "Covered basic HIPAA requirements but audit logging was shallow.",
                    ["Mentioned field-level encryption", "Role-based access"], ["Audit log schema missing", "No breach detection mention", "FHIR compliance not addressed"]),
        make_result("q2", 52, "Surface-level HL7 knowledge; no FHIR R4 specifics.",
                    ["Mentioned parsing HL7 v2"], ["No FHIR R4", "No validation pipeline", "No error quarantine", "Missed schema evolution"]),
        make_result("q3", 68, "Good trade-off analysis but missed saga pattern.",
                    ["Mentioned eventual consistency", "Service boundaries rationale"], ["No saga/choreography pattern", "Missed distributed tracing", "No circuit breaking mention"]),
        make_result("q4", 58, "Relational model but missed temporal tables.",
                    ["Correct normalization"], ["No temporal/bitemporal model", "No partitioning strategy", "Missing effective dating"]),
        make_result("q5", 55, "Basic state machine but no half-open state handling.",
                    ["Correct OPEN/CLOSED states"], ["Missing HALF-OPEN", "No fallback strategy", "No metrics integration"]),
    ]
    context = InterviewContextProfile(
        company_description="Healthcare platform managing patient records and clinical workflows",
        business_context=BusinessContext.HEALTHCARE,
    )
    answers = [Answer(question_id=q.id, content="...", attempt=1) for q in questions]
    state = build_state(RoleType.BACKEND_ENGINEER, "senior", "MedSys", context, questions, answers)
    return "Senior Backend Healthcare", state, results, questions


# ── 4. Senior Fullstack Startup ───────────────────────────────────────────────
def profile_senior_fullstack_startup():
    questions = [
        make_question("q1", InterviewArea.TECH_CASE_STUDY,
                      "Design a real-time collaborative editing system like Notion.", QuestionDifficulty.HARD),
        make_question("q2", InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
                      "Explain SSR vs CSR vs ISR trade-offs for a SaaS dashboard.", QuestionDifficulty.MEDIUM),
        make_question("q3", InterviewArea.TECH_CODING,
                      "Implement a debounce + throttle utility in TypeScript.", QuestionDifficulty.MEDIUM),
        make_question("q4", InterviewArea.TECH_DATABASE,
                      "Design a multi-tenant SaaS database schema.", QuestionDifficulty.HARD),
        make_question("q5", InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
                      "How do you approach feature flags and progressive rollouts?", QuestionDifficulty.MEDIUM),
    ]
    results = [
        make_result("q1", 75, "Good CRDT concept mention; WebSocket design solid.",
                    ["CRDT awareness", "WebSocket + presence design", "Conflict resolution outlined"], ["No operational transform detail", "Persistence strategy vague"]),
        make_result("q2", 85, "Excellent SSR/CSR/ISR analysis with concrete examples.",
                    ["Clear trade-off matrix", "Mentioned stale-while-revalidate", "React Server Components awareness"], ["Minor: no mention of streaming SSR"]),
        make_result("q3", 90, "Clean TypeScript implementation with generics.",
                    ["Type-safe generics", "Correct closure usage", "Edge cases handled"], ["No test coverage mentioned"]),
        make_result("q4", 78, "Chose row-level tenancy with good justification.",
                    ["Row-level vs schema-level trade-offs", "RLS policy design"], ["No mention of cross-tenant analytics", "Missed index strategy per tenant"]),
        make_result("q5", 82, "Solid feature flag strategy with LaunchDarkly reference.",
                    ["Gradual rollout strategy", "Kill switch design", "Targeting rules"], ["No mention of flag debt/cleanup"]),
    ]
    context = InterviewContextProfile(
        company_description="B2B SaaS startup building a collaborative workspace platform",
        business_context=BusinessContext.SAAS,
    )
    answers = [Answer(question_id=q.id, content="...", attempt=1) for q in questions]
    state = build_state(RoleType.FULLSTACK_ENGINEER, "senior", "CollabHQ", context, questions, answers)
    return "Senior Fullstack Startup", state, results, questions


# ── 5. Mid Backend E-commerce ─────────────────────────────────────────────────
def profile_mid_backend_ecommerce():
    questions = [
        make_question("q1", InterviewArea.TECH_CASE_STUDY,
                      "Design a product catalog service for a marketplace.", QuestionDifficulty.MEDIUM),
        make_question("q2", InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
                      "How do you handle inventory consistency during flash sales?", QuestionDifficulty.HARD),
        make_question("q3", InterviewArea.TECH_DATABASE,
                      "Optimize a slow ORDER JOIN PRODUCT query with 50M rows.", QuestionDifficulty.MEDIUM),
        make_question("q4", InterviewArea.TECH_CODING,
                      "Implement a shopping cart with item quantity constraints.", QuestionDifficulty.MEDIUM),
    ]
    results = [
        make_result("q1", 70, "Good catalog design but no search indexing strategy.",
                    ["Elasticsearch mention", "Category hierarchy design"], ["No full-text search detail", "Missing faceted search", "No caching layer"]),
        make_result("q2", 58, "Used pessimistic locking but missed Redis-based reservation.",
                    ["Understood overselling problem"], ["No Redis reservation pattern", "No optimistic locking fallback", "Missed queue-based approach"]),
        make_result("q3", 75, "Added composite index correctly; missed query plan analysis.",
                    ["Correct index columns", "Avoided SELECT *"], ["No EXPLAIN plan step", "Missed covering index", "No partitioning consideration"]),
        make_result("q4", 68, "Working cart logic but no concurrency handling.",
                    ["Clean data structure", "Validation present"], ["No concurrent update handling", "No idempotency for add-item", "Missing cart expiry logic"]),
    ]
    context = InterviewContextProfile(
        company_description="E-commerce marketplace with products, orders, and inventory management",
        business_context=BusinessContext.ECOMMERCE,
    )
    answers = [Answer(question_id=q.id, content="...", attempt=1) for q in questions]
    state = build_state(RoleType.BACKEND_ENGINEER, "mid", "ShopMart", context, questions, answers)
    return "Mid Backend E-commerce", state, results, questions


# ── 6. Senior Backend Generic (Excellent) ─────────────────────────────────────
def profile_senior_backend_excellent():
    questions = [
        make_question("q1", InterviewArea.TECH_CASE_STUDY,
                      "Design a distributed rate limiting system for a public API.", QuestionDifficulty.HARD),
        make_question("q2", InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
                      "Explain CAP theorem trade-offs in practice with concrete examples.", QuestionDifficulty.HARD),
        make_question("q3", InterviewArea.TECH_CODING,
                      "Implement a consistent hashing ring for a cache cluster.", QuestionDifficulty.HARD),
        make_question("q4", InterviewArea.TECH_DATABASE,
                      "Design a write-heavy time-series storage with efficient range queries.", QuestionDifficulty.HARD),
        make_question("q5", InterviewArea.TECH_CASE_STUDY,
                      "How would you migrate a monolith to microservices without downtime?", QuestionDifficulty.HARD),
    ]
    results = [
        make_result("q1", 92, "Excellent: token bucket + Redis Lua script + sliding window.",
                    ["Atomic Lua script", "Redis cluster awareness", "Token bucket + sliding window hybrid", "Fallback strategy"], ["Minor: no mention of rate limit headers"]),
        make_result("q2", 95, "Outstanding CAP analysis with Dynamo, Spanner, Cassandra examples.",
                    ["Concrete DB examples", "PACELC mention", "Partition handling strategies", "Real-world trade-offs"], []),
        make_result("q3", 88, "Correct consistent hashing with virtual nodes.",
                    ["Virtual nodes for balance", "Correct hash ring", "Replication factor consideration"], ["No mention of hotspot detection"]),
        make_result("q4", 90, "LSM-tree design with compaction strategy; excellent.",
                    ["LSM-tree choice justified", "Compaction strategy", "Bloom filter usage", "TTL management"], ["Column family design could be expanded"]),
        make_result("q5", 93, "Strangler fig + feature flags + shadow mode; near-perfect.",
                    ["Strangler fig pattern", "Traffic shadowing", "Canary deployments", "Rollback plan"], ["No mention of data synchronization lag"]),
    ]
    context = InterviewContextProfile(business_context=BusinessContext.GENERIC)
    answers = [Answer(question_id=q.id, content="...", attempt=1) for q in questions]
    state = build_state(RoleType.BACKEND_ENGINEER, "senior", "TechCorp", context, questions, answers)
    return "Senior Backend Excellent", state, results, questions


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_audit():
    llm = get_real_llm()
    service = InterviewEvaluationService(llm)

    profiles = [
        profile_junior_backend_generic,
        profile_mid_backend_fintech,
        profile_senior_backend_healthcare,
        profile_senior_fullstack_startup,
        profile_mid_backend_ecommerce,
        profile_senior_backend_excellent,
    ]

    for profile_fn in profiles:
        name, state, results, questions = profile_fn()
        print(f"\n{'='*70}")
        print(f"PROFILE: {name}")
        print(f"{'='*70}")

        try:
            evaluation = service.evaluate(
                question_results=results,
                questions=questions,
                interview_type=InterviewType.TECHNICAL,
                role=state.role.type,
                context_profile=state.context_profile,
                seniority_level=state.seniority_level,
            )

            # Build report DTO (requires InterviewState with results_by_question)
            results_by_question = {r.question_id: r for r in results}
            state = state.model_copy(update={"results_by_question": results_by_question,
                                              "interview_evaluation": evaluation})

            # EPIC-V13-05 Phase 6 / F-W-06: FinalReportDTO.from_report is the sole factory.
            if state.report is not None:
                report_dto = FinalReportDTO.from_report(state.report)
                report_html = build_report_markdown(report_dto)
                print(f"\n--- FINAL REPORT DTO (from_report) ---")
                print(f"  session_id: {report_dto.session_id}")
                print(f"  overall_score: {report_dto.overall_score:.1f}")
                print(f"  study_recommendations: {len(report_dto.study_recommendations)}")
                print(f"  html_length: {len(report_html)}")
            else:
                print(f"\n--- FINAL REPORT DTO ---")
                print(
                    "  Skipped: state.report is None "
                    "(from_report requires Report; legacy dual factory is forbidden)"
                )

            # Print key report sections for audit
            print(f"\n--- SCORES ---")
            print(f"  Overall: {evaluation.overall_score:.1f}")
            print(f"  Hire Decision: {evaluation.hire_decision}")
            print(f"  Hiring Probability: {evaluation.hiring_probability:.1f}%")
            print(f"  Percentile: {evaluation.percentile_rank:.1f}")

            print(f"\n--- EXECUTIVE SUMMARY ---")
            print(evaluation.executive_summary)

            print(f"\n--- WHAT YOU DID WELL ({len(evaluation.went_well)} items) ---")
            for i, item in enumerate(evaluation.went_well, 1):
                print(f"  {i}. {item}")

            print(f"\n--- WHAT HELD YOU BACK ({len(evaluation.held_you_back)} items) ---")
            for i, item in enumerate(evaluation.held_you_back, 1):
                if isinstance(item, dict):
                    print(f"  {i}. [{item.get('area','?')}] {item.get('issue', item.get('description', item))}")
                    if 'why_it_matters' in item:
                        print(f"     WHY: {item['why_it_matters']}")
                else:
                    print(f"  {i}. {item}")

            print(f"\n--- KNOWLEDGE GAP SUMMARY ({len(evaluation.knowledge_gaps)} items) ---")
            for i, item in enumerate(evaluation.knowledge_gaps, 1):
                if isinstance(item, dict):
                    topic = item.get('topic', item.get('area', '?'))
                    gap = item.get('gap', item.get('description', ''))
                    resource = item.get('resource', item.get('learn', ''))
                    print(f"  {i}. [{topic}] {gap}")
                    if resource:
                        print(f"     LEARN: {resource}")
                else:
                    print(f"  {i}. {item}")

            print(f"\n--- NEXT INTERVIEW STRATEGY ({len(evaluation.next_strategy)} items) ---")
            for i, item in enumerate(evaluation.next_strategy, 1):
                if isinstance(item, dict):
                    action = item.get('action', item.get('strategy', item.get('description', item)))
                    print(f"  {i}. {action}")
                else:
                    print(f"  {i}. {item}")

            print(f"\n--- PERCENTILE EXPLANATION ---")
            print(evaluation.percentile_explanation)

        except Exception as e:
            import traceback
            print(f"ERROR running profile '{name}': {e}")
            traceback.print_exc()

    print(f"\n{'='*70}")
    print("AUDIT COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    run_audit()
