# services/interview_orchestration/interview_orchestrator.py

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from domain.contracts.user.role import (
    RoleType,
)

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.candidate_pool.candidate_pool_builder import (
    CandidatePoolBuilder,
)

from services.interview_policy.policy_factory import (
    PolicyFactory,
)

from services.interview_planning.interview_constraints import (
    InterviewConstraints,
)

from services.interview_planning.constraint_based_planner import (
    ConstraintBasedPlanner,
)

from services.interview_selection.adaptive_interview_assembler import (
    AdaptiveInterviewAssembler,
)

from services.interview_orchestration.orchestration_result import (
    OrchestrationResult,
)

from services.planning_validation.planning_validator import (
    PlanningValidator,
)


class InterviewOrchestrator:

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
        # CANDIDATE POOL
        # -------------------------------------------------

        pool_builder = CandidatePoolBuilder()

        pool = pool_builder.build(
            items=items,
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
        # PLANNING
        # -------------------------------------------------

        planner = ConstraintBasedPlanner()

        planning_result = planner.plan(
            items=pool.eligible_questions,
            constraints=constraints,
        )

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        validator = PlanningValidator()

        validation_result = validator.validate(
            result=planning_result,
            constraints=constraints,
        )

        # -------------------------------------------------
        # ASSEMBLY
        # -------------------------------------------------

        assembler = AdaptiveInterviewAssembler()

        assembly_result = assembler.assemble(
            items=planning_result.selected_questions,
            policy=policy,
            max_questions=max_questions,
        )

        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        return OrchestrationResult(
            candidate_pool=pool,
            planning_result=planning_result,
            validation_result=validation_result,
            assembly_result=assembly_result,
        )
