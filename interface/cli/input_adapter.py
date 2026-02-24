# interface/cli/input_adapter.py

# CLIInputAdapter
#
# Responsibility:
# - Handle user input from CLI without domain logic
# - No scoring logic
# - No direct state modifications
# - Return raw data

from domain.contracts.question import Question


class CLIInputAdapter:
    # Handles user input from CLI without domain logic

    def get_answer(self, question: Question) -> str:
        # Display prompt for user answer
        print("\nYour answer:")
        user_input = input("> ")
        return user_input.strip()

    def get_follow_up_answer(self) -> str:
        # Used when evaluator generates a follow-up
        print("\nFollow-up answer:")
        user_input = input("> ")
        return user_input.strip()
