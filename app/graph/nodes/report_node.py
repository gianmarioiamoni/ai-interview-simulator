# app/graph/nodes/report_node.py

from domain.contracts.interview_state import InterviewState
from services.evaluation_aggregator import EvaluationAggregator
from services.report_builder import ReportBuilder


def report_node(state: InterviewState) -> InterviewState:

    evaluations = state.evaluations_list

    aggregation = EvaluationAggregator.aggregate(evaluations)

    new_state = ReportBuilder.build(state, aggregation)

    return new_state
