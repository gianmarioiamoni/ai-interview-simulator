# tests/services/corpus_persistence/test_corpus_loader.py

import tarfile
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import services.corpus_persistence.corpus_loader as loader_module
from services.corpus_persistence.corpus_loader import (
    corpus_is_present,
    ensure_corpus,
    restore_corpus_from_hf,
    validate_corpus,
)


# ---------------------------------------------------------
# corpus_is_present
# ---------------------------------------------------------


def test_corpus_present_when_dir_has_files(tmp_path):
    (tmp_path / "file.bin").write_bytes(b"x")
    with patch.object(loader_module, "CHROMA_PERSIST_DIRECTORY", str(tmp_path)):
        assert corpus_is_present() is True


def test_corpus_absent_when_dir_missing(tmp_path):
    missing = tmp_path / "nonexistent"
    with patch.object(loader_module, "CHROMA_PERSIST_DIRECTORY", str(missing)):
        assert corpus_is_present() is False


def test_corpus_absent_when_dir_empty(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with patch.object(loader_module, "CHROMA_PERSIST_DIRECTORY", str(empty)):
        assert corpus_is_present() is False


# ---------------------------------------------------------
# validate_corpus
# ---------------------------------------------------------


def test_validate_corpus_returns_count(tmp_path):
    mock_collection = MagicMock()
    mock_collection.count.return_value = 1129
    mock_client = MagicMock()
    mock_client.get_collection.return_value = mock_collection

    with (
        patch.object(loader_module, "CHROMA_PERSIST_DIRECTORY", str(tmp_path)),
        patch("chromadb.PersistentClient", return_value=mock_client),
    ):
        count = validate_corpus()

    assert count == 1129
    mock_client.get_collection.assert_called_once_with("interview_questions")


def test_validate_corpus_raises_when_too_small(tmp_path):
    mock_collection = MagicMock()
    mock_collection.count.return_value = 5
    mock_client = MagicMock()
    mock_client.get_collection.return_value = mock_collection

    with (
        patch.object(loader_module, "CHROMA_PERSIST_DIRECTORY", str(tmp_path)),
        patch("chromadb.PersistentClient", return_value=mock_client),
    ):
        with pytest.raises(RuntimeError, match="too small"):
            validate_corpus()


def test_validate_corpus_raises_on_chroma_error(tmp_path):
    with (
        patch.object(loader_module, "CHROMA_PERSIST_DIRECTORY", str(tmp_path)),
        patch("chromadb.PersistentClient", side_effect=Exception("db error")),
    ):
        with pytest.raises(RuntimeError, match="Corpus validation failed"):
            validate_corpus()


def test_validate_corpus_raises_on_type_error_from_version_mismatch(tmp_path):
    """
    Simulate chromadb version mismatch: count() internally calls len() on an int
    (seq_id stored as int in newer schema, decoded as bytes in older chromadb).
    TypeError must be caught and re-raised as RuntimeError.
    """
    mock_collection = MagicMock()
    mock_collection.count.side_effect = TypeError("object of type 'int' has no len()")
    mock_client = MagicMock()
    mock_client.get_collection.return_value = mock_collection

    with (
        patch.object(loader_module, "CHROMA_PERSIST_DIRECTORY", str(tmp_path)),
        patch("chromadb.PersistentClient", return_value=mock_client),
    ):
        with pytest.raises(RuntimeError, match="Corpus validation failed"):
            validate_corpus()


# ---------------------------------------------------------
# restore_corpus_from_hf
# ---------------------------------------------------------


def _make_tar_corpus(dest_dir: Path, corpus_dir: Path) -> Path:
    """Create a minimal tar.gz mimicking the corpus archive structure."""
    artifact = dest_dir / "chroma_corpus.tar.gz"
    (corpus_dir / "chroma.sqlite3").write_bytes(b"fake")
    with tarfile.open(artifact, "w:gz") as tar:
        tar.add(corpus_dir, arcname=corpus_dir.name)
    return artifact


def test_restore_corpus_from_hf_success(tmp_path):
    corpus_src = tmp_path / "interview_corpus"
    corpus_src.mkdir()
    artifact = _make_tar_corpus(tmp_path, corpus_src)

    mock_collection = MagicMock()
    mock_collection.count.return_value = 200
    mock_client = MagicMock()
    mock_client.get_collection.return_value = mock_collection

    target = tmp_path / "restored"
    target.mkdir()

    with (
        patch.object(loader_module, "CHROMA_PERSIST_DIRECTORY", str(target / "interview_corpus")),
        patch(
            "huggingface_hub.hf_hub_download",
            return_value=str(artifact),
        ),
        patch("chromadb.PersistentClient", return_value=mock_client),
    ):
        count = restore_corpus_from_hf(hf_repo="owner/repo", hf_token="tok")

    assert count == 200


# ---------------------------------------------------------
# ensure_corpus
# ---------------------------------------------------------


def test_ensure_corpus_skips_restore_when_present(tmp_path):
    (tmp_path / "data.bin").write_bytes(b"x")

    mock_collection = MagicMock()
    mock_collection.count.return_value = 1129
    mock_client = MagicMock()
    mock_client.get_collection.return_value = mock_collection

    with (
        patch.object(loader_module, "CHROMA_PERSIST_DIRECTORY", str(tmp_path)),
        patch("chromadb.PersistentClient", return_value=mock_client),
    ):
        ensure_corpus()


def test_ensure_corpus_restores_when_missing(tmp_path, monkeypatch):
    missing = tmp_path / "missing"
    monkeypatch.setenv("CORPUS_HF_REPO", "owner/repo")

    mock_collection = MagicMock()
    mock_collection.count.return_value = 300
    mock_client = MagicMock()
    mock_client.get_collection.return_value = mock_collection

    corpus_src = tmp_path / "interview_corpus"
    corpus_src.mkdir()
    artifact = _make_tar_corpus(tmp_path, corpus_src)

    with (
        patch.object(loader_module, "CHROMA_PERSIST_DIRECTORY", str(missing / "interview_corpus")),
        patch(
            "huggingface_hub.hf_hub_download",
            return_value=str(artifact),
        ),
        patch("chromadb.PersistentClient", return_value=mock_client),
    ):
        ensure_corpus()


def test_ensure_corpus_exits_when_missing_and_no_repo(tmp_path, monkeypatch):
    missing = tmp_path / "missing"
    monkeypatch.delenv("CORPUS_HF_REPO", raising=False)

    with patch.object(loader_module, "CHROMA_PERSIST_DIRECTORY", str(missing)):
        with pytest.raises(SystemExit):
            ensure_corpus()


def test_ensure_corpus_exits_on_restore_failure(tmp_path, monkeypatch):
    missing = tmp_path / "missing"
    monkeypatch.setenv("CORPUS_HF_REPO", "owner/repo")

    with (
        patch.object(loader_module, "CHROMA_PERSIST_DIRECTORY", str(missing)),
        patch(
            "huggingface_hub.hf_hub_download",
            side_effect=Exception("download error"),
        ),
    ):
        with pytest.raises(SystemExit):
            ensure_corpus()
