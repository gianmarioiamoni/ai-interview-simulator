# tests/ui/presenters/feedback/blocks/test_runtime_error_block.py
# EPIC-07 P4/C8 — RuntimeErrorBlock uses EC-EX-01; no traceback chrome.

import types

from app.ui.presenters.feedback.blocks.runtime_error_block import RuntimeErrorBlock
from app.ui.presentation import get_execution_error_entry, ExecutionErrorKind
from domain.contracts.feedback.error_type import ErrorType


def _analysis(error: str = "", error_type=ErrorType.RUNTIME, has_runtime_error: bool = True):
    a = types.SimpleNamespace()
    a.primary_error = error
    a.error_type = error_type
    a.has_runtime_error = has_runtime_error
    return a


def _execution(test_results=None, hidden_failure_sample=None):
    e = types.SimpleNamespace()
    e.test_results = test_results or []
    e.hidden_failure_sample = hidden_failure_sample
    return e


def _test_result(status_value: str, args=None):
    t = types.SimpleNamespace()
    t.status = types.SimpleNamespace(value=status_value)
    t.args = args
    return t


class TestRuntimeErrorBlock:

    def setup_method(self):
        self.block = RuntimeErrorBlock()

    def test_can_handle_true_when_has_runtime_error(self):
        assert self.block.can_handle(None, None, None, _analysis()) is True

    def test_can_handle_false_when_no_runtime_error(self):
        a = _analysis(has_runtime_error=False)
        assert self.block.can_handle(None, None, None, a) is False

    def test_content_uses_catalog_not_traceback(self):
        a = _analysis(
            error=(
                "Traceback (most recent call last):\n"
                "  File x.py, line 1\n"
                "NameError: name 'x' not defined"
            )
        )
        result = self.block.build(None, None, None, _execution(), a, None)
        expected = get_execution_error_entry(ExecutionErrorKind.RUNTIME).candidate_message
        assert expected in result.content
        assert "Traceback" not in result.content
        assert "NameError" not in result.content
        assert ".py" not in result.content
        assert "```" not in result.content

    def test_content_includes_input_from_hidden_sample(self):
        a = _analysis(error="NameError: name 'x'")
        sample = {"args": [1, 2, 3], "expected": 6, "actual": None}
        result = self.block.build(
            None, None, None, _execution(hidden_failure_sample=sample), a, None
        )
        assert "Input" in result.content
        assert "[1, 2, 3]" in result.content

    def test_content_includes_input_from_failed_test_result(self):
        a = _analysis(error="NameError: name 'x'")
        t = _test_result("failed", args=[5, 10])
        result = self.block.build(
            None, None, None, _execution(test_results=[t]), a, None
        )
        assert "Input" in result.content
        assert "[5, 10]" in result.content

    def test_content_no_input_section_when_none_available(self):
        a = _analysis(error="SyntaxError: invalid syntax", error_type=ErrorType.SYNTAX)
        result = self.block.build(None, None, None, _execution(), a, None)
        assert "Input" not in result.content
        assert get_execution_error_entry(ExecutionErrorKind.SYNTAX).candidate_message in (
            result.content
        )

    def test_timeout_title(self):
        a = _analysis(error_type=ErrorType.TIMEOUT)
        result = self.block.build(None, None, None, _execution(), a, None)
        assert "Timeout" in result.title

    def test_syntax_title(self):
        a = _analysis(error_type=ErrorType.SYNTAX)
        result = self.block.build(None, None, None, _execution(), a, None)
        assert "Syntax" in result.title

    def test_signal_uses_catalog_message_not_exception_line(self):
        a = _analysis(error="line1\nline2\nNameError: bad name")
        result = self.block.build(None, None, None, _execution(), a, None)
        assert result.signals[0].message == get_execution_error_entry(
            ExecutionErrorKind.RUNTIME
        ).candidate_message
        assert "NameError" not in result.signals[0].message

    def test_raw_traceback_not_shown(self):
        full = "Traceback (most recent call last):\n  File foo.py, line 3\nNameError: bad"
        a = _analysis(error=full)
        result = self.block.build(None, None, None, _execution(), a, None)
        assert "File foo.py" not in result.content
        assert "Traceback" not in result.content
