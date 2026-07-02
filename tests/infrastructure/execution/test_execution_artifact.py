# tests/infrastructure/execution/test_execution_artifact.py

import pytest
from pydantic import ValidationError
from infrastructure.execution.contracts.execution_artifact import (
    ExecutionArtifact,
    ArtifactKind,
)


class TestArtifactKindValues:
    def test_all_expected_values(self):
        values = {k.value for k in ArtifactKind}
        assert values == {
            "stdout",
            "stderr",
            "compiled_bytecode",
            "transpiled_source",
            "coverage_report",
            "profile_trace",
            "sandbox_log",
        }


class TestExecutionArtifactConstruction:
    def test_stdout_artifact(self):
        a = ExecutionArtifact(
            kind=ArtifactKind.STDOUT,
            name="stdout",
            content="hello\n",
            size_bytes=6,
        )
        assert a.kind == ArtifactKind.STDOUT
        assert a.content == "hello\n"
        assert a.size_bytes == 6
        assert a.truncated is False

    def test_defaults(self):
        a = ExecutionArtifact(kind=ArtifactKind.STDERR, name="stderr")
        assert a.content == ""
        assert a.size_bytes == 0
        assert a.truncated is False
        assert a.encoding == "utf-8"

    def test_truncated_artifact(self):
        a = ExecutionArtifact(
            kind=ArtifactKind.STDOUT,
            name="stdout",
            content="...",
            size_bytes=1_048_576,
            truncated=True,
        )
        assert a.truncated is True

    def test_all_kinds_constructable(self):
        for kind in ArtifactKind:
            a = ExecutionArtifact(kind=kind, name=f"artifact-{kind.value}")
            assert a.kind == kind

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            ExecutionArtifact(kind=ArtifactKind.STDOUT, name="")

    def test_negative_size_rejected(self):
        with pytest.raises(ValidationError):
            ExecutionArtifact(kind=ArtifactKind.STDOUT, name="out", size_bytes=-1)

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            ExecutionArtifact(kind=ArtifactKind.STDOUT, name="x", extra="y")


class TestExecutionArtifactSerialization:
    def test_round_trip(self):
        a = ExecutionArtifact(
            kind=ArtifactKind.SANDBOX_LOG,
            name="sandbox_log",
            content="[INFO] started",
            size_bytes=14,
        )
        restored = ExecutionArtifact.model_validate(a.model_dump())
        assert restored == a

    def test_frozen(self):
        a = ExecutionArtifact(kind=ArtifactKind.STDOUT, name="out")
        with pytest.raises(ValidationError):
            a.content = "modified"
