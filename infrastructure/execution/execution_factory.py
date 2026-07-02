# infrastructure/execution/execution_factory.py

import uuid
from typing import Optional

from infrastructure.execution.contracts.execution_environment import ExecutionEnvironment
from infrastructure.execution.contracts.execution_limits import ExecutionLimits
from infrastructure.execution.contracts.execution_request import ExecutionRequest


class ExecutionFactory:
    """Constructs ExecutionRequest from components."""

    def build_request(
        self,
        execution_id: str,
        question_id: str,
        language_id: str,
        candidate_code: str,
        environment: ExecutionEnvironment,
        limits: Optional[ExecutionLimits] = None,
        hidden_test_suite: str = "",
        visible_test_suite: str = "",
    ) -> ExecutionRequest:
        if language_id != environment.language_id:
            raise ValueError(
                f"language_id '{language_id}' does not match "
                f"environment.language_id '{environment.language_id}'"
            )

        resolved_id = execution_id if execution_id else str(uuid.uuid4())
        resolved_limits = limits if limits is not None else ExecutionLimits()

        return ExecutionRequest(
            execution_id=resolved_id,
            question_id=question_id,
            language_id=language_id,
            candidate_code=candidate_code,
            hidden_test_suite=hidden_test_suite,
            visible_test_suite=visible_test_suite,
            environment=environment,
            limits=resolved_limits,
        )
