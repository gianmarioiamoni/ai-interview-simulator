# app/ui/presenters/feedback/blocks/runtime_error_block.py

import re


class RuntimeErrorBlock:

    def can_handle(self, result, evaluation, execution, analysis) -> bool:
        return bool(analysis and analysis.has_runtime_error)

    def build(self, state, result, evaluation, execution, analysis) -> str:

        lines = []

        clean_error = self._extract_clean_error(analysis.primary_error)
        fast_hint = self._generate_runtime_hint(clean_error)
        ai_hint = result.ai_hint if result else None

        lines.append("## ⚠️ Runtime Error\n")
        lines.append(f"`{clean_error}`\n")

        if fast_hint:
            lines.append("### 💡 Quick Hint")
            lines.append(fast_hint + "\n")

        if ai_hint:
            lines.append("### 🤖 AI Hint")
            lines.append(f"**Explanation:** {ai_hint.explanation}")
            lines.append(f"**Suggestion:** {ai_hint.suggestion}")

        return "\n".join(lines)

    def _extract_clean_error(self, error: str) -> str:
        return error.strip().splitlines()[-1] if error else ""

    def _generate_runtime_hint(self, error: str) -> str:
        match = re.search(r"NameError: name '(.+?)' is not defined", error)
        if match:
            return f"'{match.group(1)}' is not defined. Missing import."
        return ""
