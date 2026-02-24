# Backward compatibility layer
#
# This module preserves the original EvaluationResult contract
# by aliasing it to QuestionEvaluation.
# It avoids breaking legacy imports after Phase 5 refactor.

from domain.contracts.question_evaluation import QuestionEvaluation

EvaluationResult = QuestionEvaluation
