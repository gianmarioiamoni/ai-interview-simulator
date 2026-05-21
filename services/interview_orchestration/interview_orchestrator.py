# services/interview_orchestration/interview_orchestrator.py

from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.candidate_pool.candidate_pool_builder import CandidatePoolBuilder

from services.interview_policy.policy_factory import PolicyFactory
from services.interview_planning.interview_constraints import InterviewConstraints
from services.interview_selection.adaptive_interview_assembler import AdaptiveInterviewAssembler
from services.interview_orchestration.orchestration_result import OrchestrationResult

from services.replanning.recovery_replanner import RecoveryReplanner

from services.interview_orchestration.orchestration_intent_builder import OrchestrationIntentBuilder

from services.retrieval.planner_retrieval_service import PlannerRetrievalService
from services.retrieval.retrieval_runtime_mapper import RetrievalRuntimeMapper
from services.retrieval.memory_aware_retrieval_pipeline import MemoryAwareRetrievalPipeline
from services.retrieval.retrieval_session_memory import RetrievalSessionMemory


class InterviewOrchestrator:

    def __init__(self) -> None:

        self._retrieval_memory = RetrievalSessionMemory()

        self._retrieval_pipeline = MemoryAwareRetrievalPipeline(
            memory=self._retrieval_memory,
        )

    # =====================================================
    # PUBLIC
    # =====================================================

    def orchestrate(
        self,
        items: list[QuestionBankItem],
        role: RoleType,
        level: SeniorityLevel,
        max_questions: int = 5,
    ) -> OrchestrationResult:

        # -------------------------------------------------
        # RETRIEVAL INTENT
        # -------------------------------------------------

        intent_builder = OrchestrationIntentBuilder()

        intent = intent_builder.build(
            role=role,
            level=level,
        )

        # -------------------------------------------------
        # RUNTIME RETRIEVAL
        # -------------------------------------------------

        retrieval_service = PlannerRetrievalService()

        symbolic_results = retrieval_service.retrieve_candidates(
            intent=intent,
            corpus_path="datasets/curated/tech_interview_handbook.json",
        )

        retrieval_results = self._retrieval_pipeline.process(
            results=symbolic_results,
        )

        # -------------------------------------------------
        # RETRIEVED NORMALIZED RECORDS
        # -------------------------------------------------

        retrieved_records = [
            result.symbolic_result.record
            for result in retrieval_results
        ]

        # -------------------------------------------------
        # RUNTIME ITEM MAPPING
        # -------------------------------------------------

        mapper = RetrievalRuntimeMapper()

        retrieved_questions = mapper.map(
            records=retrieved_records,
        )

        # -------------------------------------------------
        # CANDIDATE POOL
        # -------------------------------------------------

        pool_builder = CandidatePoolBuilder()

        pool = pool_builder.build(
            items=retrieved_questions,
            role=role,
            level=level,
        )

        # -------------------------------------------------
        # POLICY
        # -------------------------------------------------

        policy_factory = PolicyFactory()

        policy = policy_factory.build(
            role=role,
            level=level,
        )

        # -------------------------------------------------
        # CONSTRAINTS
        # -------------------------------------------------

        constraints = InterviewConstraints(
            required_areas=policy.preferred_areas,
            excluded_areas=[],
            max_questions_per_area=(policy.max_questions_per_area),
            minimum_average_difficulty=(policy.target_average_difficulty),
            minimum_total_questions=max_questions,
        )

        # -------------------------------------------------
        # REPLANNING
        # -------------------------------------------------

        replanner = RecoveryReplanner()

        replanning_result = replanner.replan(
            items=pool.eligible_questions,
            constraints=constraints,
        )



        # -------------------------------------------------
        # ASSEMBLY
        # -------------------------------------------------

        assembler = AdaptiveInterviewAssembler()

        assembly_result = assembler.assemble(
            items=replanning_result.final_planning_result.selected_questions,
            policy=policy,
            max_questions=max_questions,
        )

        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        return OrchestrationResult(
            candidate_pool=pool,
            planning_result=(
                replanning_result
                .final_planning_result
            ),
            validation_result=(
                replanning_result
                .final_validation_result
            ),
            replanning_result=(
                replanning_result
            ),
            assembly_result=assembly_result,
        )
