#!/usr/bin/env python3
"""V1.0 Release Audit - 4 end-to-end interview evaluations."""
import sys, json
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')

from infrastructure.llm.llm_factory import get_raw_llm
from services.interview_evaluation_service import InterviewEvaluationService
from domain.contracts.question.question_result import QuestionResult
from domain.contracts.question.question import Question, QuestionType, QuestionDifficulty
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.interview.interview_context_profile import InterviewContextProfile
from domain.contracts.interview.business_context import BusinessContext
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.role import RoleType


def make_q(qid, area, prompt, qtype=QuestionType.WRITTEN, diff=QuestionDifficulty.MEDIUM):
    return Question(id=qid, area=area, type=qtype, prompt=prompt, difficulty=diff)


def make_qr(qid, q, score, feedback, strengths, weaknesses, passed):
    ev = QuestionEvaluation(
        question_id=qid, score=score, max_score=100.0,
        feedback=feedback, strengths=strengths, weaknesses=weaknesses, passed=passed
    )
    return QuestionResult(question_id=qid, question=q, evaluation=ev)


def report(label, r):
    issues = []
    if not r.went_well:
        issues.append("EMPTY:went_well")
    if not r.held_you_back:
        issues.append("EMPTY:held_you_back")
    if not r.knowledge_gaps:
        issues.append("EMPTY:knowledge_gaps")
    if not r.next_strategy:
        issues.append("EMPTY:next_strategy")
    if len(r.executive_summary) < 200:
        issues.append(f"SHORT:exec_summary({len(r.executive_summary)})")
    
    print(f"\n{'='*60}")
    print(f"[{label}]")
    print(f"  overall_score: {r.overall_score:.1f}")
    print(f"  hire_decision: {r.hire_decision}")
    print(f"  level:         {r.level}")
    print(f"  percentile:    {r.percentile_rank:.1f}")
    print(f"  exec_summary:  {len(r.executive_summary)} chars")
    print(f"  went_well:     {len(r.went_well)} items")
    print(f"  held_back:     {len(r.held_you_back)} items")
    print(f"  gaps:          {len(r.knowledge_gaps)} items")
    print(f"  next_strategy: {len(r.next_strategy)} items")
    print(f"  improvement_suggestions: {len(r.improvement_suggestions)}")
    print(f"  ISSUES:        {issues if issues else 'NONE'}")
    # Sample content for overlap check
    if r.held_you_back and r.next_strategy:
        hb0 = str(r.held_you_back[0])[:80]
        ns0 = str(r.next_strategy[0])[:80]
        print(f"  held_back[0]:  {hb0}")
        print(f"  next_strat[0]: {ns0}")
    return issues


llm = get_raw_llm()
svc = InterviewEvaluationService(llm)

# ============================================================
# PROFILE 1: Senior Backend Generic - EXCELLENT (expect HIRE)
# ============================================================
qs1 = [
    make_q("q1", InterviewArea.TECH_TECHNICAL_KNOWLEDGE, "Explain the CAP theorem and its practical implications for distributed systems design."),
    make_q("q2", InterviewArea.TECH_BACKGROUND, "Describe a complex system you architected. What tradeoffs did you make?"),
    make_q("q3", InterviewArea.TECH_CASE_STUDY, "Design a rate-limiting system for a high-traffic API (10k RPS)."),
    make_q("q4", InterviewArea.TECH_TECHNICAL_KNOWLEDGE, "How does consistent hashing work and where would you apply it?"),
]
qrs1 = [
    make_qr("q1", qs1[0], 93, "Outstanding depth on CAP with real-world Cassandra/Zookeeper examples and nuanced PACELC awareness.", ["Deep CP vs AP tradeoffs", "PACELC mentioned", "Real system examples"], [], True),
    make_qr("q2", qs1[1], 90, "Led event-sourcing migration at scale. 40% latency reduction, clear risk mitigation approach.", ["Event sourcing architecture", "Quantified impact", "Rollback planning"], [], True),
    make_qr("q3", qs1[2], 88, "Token bucket + Redis with multi-region awareness and fallback strategy.", ["Burst handling", "Multi-region replication", "Rate limit headers"], [], True),
    make_qr("q4", qs1[3], 91, "Textbook virtual nodes explanation with Dynamo and load balancer examples.", ["Virtual nodes", "Hot spot mitigation", "Replication factor"], [], True),
]

print("Running Profile 1: Senior Backend Generic (EXCELLENT)...")
r1 = svc.evaluate(qrs1, qs1, InterviewType.TECHNICAL, RoleType.BACKEND_ENGINEER, seniority_level="senior")
issues1 = report("P1-SENIOR-BACKEND-EXCELLENT", r1)

# ============================================================
# PROFILE 2: Mid Backend Fintech - GOOD (expect personalization)
# ============================================================
qs2 = [
    make_q("q1", InterviewArea.TECH_TECHNICAL_KNOWLEDGE, "How would you design a payment processing system that handles idempotency and exactly-once delivery?"),
    make_q("q2", InterviewArea.TECH_CASE_STUDY, "Design a fraud detection pipeline for real-time transaction scoring."),
    make_q("q3", InterviewArea.TECH_TECHNICAL_KNOWLEDGE, "Explain database isolation levels and when you'd use each in a financial system."),
    make_q("q4", InterviewArea.TECH_BACKGROUND, "Tell me about a time you improved system reliability in a high-stakes environment."),
]
qrs2 = [
    make_qr("q1", qs2[0], 78, "Good idempotency key design, mentioned distributed locks but missed saga pattern.", ["Idempotency keys", "Retry strategies", "Webhook reliability"], ["Missed saga pattern", "No compensating transactions"], True),
    make_qr("q2", qs2[1], 75, "Solid ML pipeline overview but light on feature engineering for fraud signals.", ["Real-time scoring concept", "Feature store mention"], ["No velocity features", "Weak on model monitoring"], True),
    make_qr("q3", qs2[2], 82, "Strong isolation level coverage with practical financial use cases.", ["Serializable for critical ops", "Repeatable read tradeoffs"], [], True),
    make_qr("q4", qs2[3], 72, "Circuit breaker pattern applied well, but limited quantitative impact.", ["Circuit breaker", "SLA monitoring"], ["No SLO definition", "Vague metrics"], True),
]

ctx2 = InterviewContextProfile(
    job_description="Senior Backend Engineer at a payments startup handling 500k daily transactions",
    company_description="Fintech company building payment infrastructure for merchants and banks. We handle transaction processing, settlement, and fraud detection.",
    business_context=BusinessContext.FINTECH,
)

print("\nRunning Profile 2: Mid Backend Fintech (GOOD)...")
r2 = svc.evaluate(qrs2, qs2, InterviewType.TECHNICAL, RoleType.BACKEND_ENGINEER, context_profile=ctx2, seniority_level="mid")
issues2 = report("P2-MID-BACKEND-FINTECH-GOOD", r2)

# ============================================================
# PROFILE 3: Junior Backend Generic - WEAK (expect NO_HIRE)
# ============================================================
qs3 = [
    make_q("q1", InterviewArea.TECH_TECHNICAL_KNOWLEDGE, "What is a REST API and how does it differ from GraphQL?"),
    make_q("q2", InterviewArea.TECH_TECHNICAL_KNOWLEDGE, "Explain indexing in relational databases."),
    make_q("q3", InterviewArea.TECH_CASE_STUDY, "Design a simple URL shortener."),
    make_q("q4", InterviewArea.TECH_BACKGROUND, "Tell me about a project you worked on."),
]
qrs3 = [
    make_qr("q1", qs3[0], 45, "Basic REST understanding, confused GraphQL with REST endpoints.", ["Knows HTTP methods"], ["Confused GraphQL mutations with REST PUT", "No mention of schema/typing", "No performance tradeoffs"], False),
    make_qr("q2", qs3[1], 40, "Knows indexes exist but couldn't explain B-tree or query plan impact.", ["Knows indexes speed up queries"], ["No B-tree knowledge", "No composite index awareness", "Confused index with primary key"], False),
    make_qr("q3", qs3[2], 38, "Basic hash map idea but no DB design, no collision handling, no scaling.", ["Identified need for unique short codes"], ["No persistence design", "No collision strategy", "No analytics consideration", "No CDN/caching"], False),
    make_qr("q4", qs3[3], 50, "Described a todo app with basic CRUD. Limited depth.", ["Completed a project"], ["No architectural decisions discussed", "No scaling or error handling", "Very simple scope"], False),
]

print("\nRunning Profile 3: Junior Backend Generic (WEAK)...")
r3 = svc.evaluate(qrs3, qs3, InterviewType.TECHNICAL, RoleType.BACKEND_ENGINEER, seniority_level="junior")
issues3 = report("P3-JUNIOR-BACKEND-WEAK", r3)

# ============================================================
# PROFILE 4: Senior Backend Healthcare - ACCEPTABLE (expect LEAN_NO_HIRE)
# ============================================================
qs4 = [
    make_q("q1", InterviewArea.TECH_TECHNICAL_KNOWLEDGE, "How would you design a HIPAA-compliant data storage system for patient records?"),
    make_q("q2", InterviewArea.TECH_CASE_STUDY, "Design a real-time patient monitoring system for ICU vitals."),
    make_q("q3", InterviewArea.TECH_TECHNICAL_KNOWLEDGE, "Explain event-driven architecture and its benefits for healthcare workflows."),
    make_q("q4", InterviewArea.TECH_BACKGROUND, "Describe your experience with high-availability systems in regulated industries."),
]
qrs4 = [
    make_qr("q1", qs4[0], 65, "Knows encryption at rest/transit, some HIPAA concepts but missed audit logging detail.", ["Encryption awareness", "Access controls mentioned"], ["No audit log design", "Missed BAA mention", "No data retention policy"], True),
    make_qr("q2", qs4[1], 60, "Proposed pub/sub for vitals but missed alert escalation and fault tolerance.", ["Streaming pipeline concept"], ["No alert threshold design", "No fault tolerance for sensor failures", "Missing offline resilience"], True),
    make_qr("q3", qs4[2], 68, "Good event-driven overview but shallow on healthcare-specific patterns.", ["Decoupling benefits", "Kafka mention"], ["No HL7/FHIR event schemas", "No compliance for event storage"], True),
    make_qr("q4", qs4[3], 62, "Two years regulated industry but mostly compliance checkbox awareness.", ["Regulatory awareness", "Incident response familiarity"], ["No concrete HA design", "No DR strategy discussed"], True),
]

ctx4 = InterviewContextProfile(
    job_description="Senior Backend Engineer at a digital health company building EHR integrations",
    company_description="Healthcare technology company providing clinical workflow software for hospitals, patient management, EHR systems, and FHIR-based integrations.",
    business_context=BusinessContext.HEALTHCARE,
)

print("\nRunning Profile 4: Senior Backend Healthcare (ACCEPTABLE)...")
r4 = svc.evaluate(qrs4, qs4, InterviewType.TECHNICAL, RoleType.BACKEND_ENGINEER, context_profile=ctx4, seniority_level="senior")
issues4 = report("P4-SENIOR-BACKEND-HEALTHCARE-ACCEPTABLE", r4)

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "="*60)
print("SCORE SEPARATION CHECK:")
scores = [r1.overall_score, r2.overall_score, r3.overall_score, r4.overall_score]
labels = ["Senior-Excellent", "Mid-Good", "Junior-Weak", "Senior-Acceptable"]
for l, s in zip(labels, scores):
    print(f"  {l}: {s:.1f}")

print(f"\nDecisions: {[r.hire_decision for r in [r1,r2,r3,r4]]}")
print(f"Levels:    {[r.level for r in [r1,r2,r3,r4]]}")
print(f"\nTotal issues: {len(issues1+issues2+issues3+issues4)}")
all_issues = issues1 + issues2 + issues3 + issues4
if all_issues:
    print("Issues found:", all_issues)
else:
    print("No structural issues found.")
