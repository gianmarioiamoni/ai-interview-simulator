# app/ui/controllers/interview_controller.py

from typing import Union

from domain.contracts.interview_state import InterviewState
from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.mappers.interview_state_mapper import InterviewStateMapper


class InterviewController:
    
    # Application-level controller.
    # Coordinates LangGraph execution and maps domain state to UI DTOs.

    def __init__(self, graph, mapper: InterviewStateMapper):
        self._graph = graph
        self._mapper = mapper

    # ---------------------------------------------------------
    # Start Interview
    # ---------------------------------------------------------

    def start_interview(self, initial_state: InterviewState) -> InterviewSessionDTO:
        # Starts the interview by invoking the graph with initial state.

        updated_state: InterviewState = self._graph.invoke(initial_state)

        return self._mapper.to_session_dto(updated_state)

    # ---------------------------------------------------------
    # Submit Answer
    # ---------------------------------------------------------

    def submit_answer(
        self,
        current_state: InterviewState,
    ) -> Union[InterviewSessionDTO, FinalReportDTO]:
        # Continues the interview flow.

        updated_state: InterviewState = self._graph.invoke(current_state)

        if updated_state.progress.name == "COMPLETED":
            return self._mapper.to_final_report_dto(updated_state)

        return self._mapper.to_session_dto(updated_state)
