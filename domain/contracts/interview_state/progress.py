# domain/contracts/interview_state/progress.py

from domain.contracts.interview_progress import InterviewProgress


class InterviewStateProgressMixin:

    def advance_question(self):

        if self.is_last_question:
            self.progress = InterviewProgress.COMPLETED
            return

        self.current_question_index += 1
        self.progress = InterviewProgress.IN_PROGRESS

    def reset_current_question(self):

        q = self.current_question

        if q is None:
            return

        qid = q.id

        # remove result
        if qid in self.results_by_question:
            new_map = dict(self.results_by_question)
            del new_map[qid]
            self.results_by_question = new_map

