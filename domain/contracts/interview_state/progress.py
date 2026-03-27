# domain/contracts/interview_state/progress.py

from domain.contracts.interview_progress import InterviewProgress


class InterviewStateProgressMixin:

    def clear_result_for_question(self, qid: str):

        if qid not in self.results_by_question:
            return self
    
        new_map = dict(self.results_by_question)
        del new_map[qid]
    
        return self.model_copy(update={
            "results_by_question": new_map
        })