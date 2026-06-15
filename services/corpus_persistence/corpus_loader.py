# services/corpus_persistence/corpus_loader.py

import os
import shutil
import tarfile
import tempfile
from pathlib import Path

from app.core.logger import get_logger
from services.question_corpus.constants.vector_store_constants import (
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIRECTORY,
)

logger = get_logger(__name__)

_HF_REPO_ENV = "CORPUS_HF_REPO"
_HF_FILENAME = "chroma_corpus.tar.gz"
_MIN_EXPECTED_DOCS = 100


def corpus_is_present() -> bool:
    """Return True if the Chroma persist directory is non-empty."""
    path = Path(CHROMA_PERSIST_DIRECTORY)
    if not path.exists():
        return False
    files = list(path.rglob("*"))
    return any(f.is_file() for f in files)


def validate_corpus() -> int:
    """
    Open the Chroma collection and return the document count.
    Raises RuntimeError if the collection is absent or below minimum.
    """
    try:
        import chromadb

        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)
        collection = client.get_collection(CHROMA_COLLECTION_NAME)
        count = collection.count()
    except Exception as exc:
        raise RuntimeError(f"Corpus validation failed: {exc}") from exc

    if count < _MIN_EXPECTED_DOCS:
        raise RuntimeError(
            f"Corpus too small: expected >= {_MIN_EXPECTED_DOCS}, got {count}"
        )

    return count


def restore_corpus_from_hf(*, hf_repo: str, hf_token: str | None = None) -> int:
    """
    Download the pre-built Chroma artifact from an HF Dataset repo,
    extract it, validate it, and return the document count.
    """
    from huggingface_hub import hf_hub_download  # noqa: PLC0415 — lazy to avoid hard dep at import time

    logger.info("CORPUS_RESTORE_START repo=%s file=%s", hf_repo, _HF_FILENAME)

    with tempfile.TemporaryDirectory() as tmp:
        local_path = hf_hub_download(
            repo_id=hf_repo,
            filename=_HF_FILENAME,
            repo_type="dataset",
            token=hf_token,
            local_dir=tmp,
        )

        dest = Path(CHROMA_PERSIST_DIRECTORY)
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        with tarfile.open(local_path, "r:gz") as tar:
            tar.extractall(path=dest.parent)

    count = validate_corpus()
    logger.info(
        "CORPUS_RESTORED collection_name=%s document_count=%d",
        CHROMA_COLLECTION_NAME,
        count,
    )
    return count


def ensure_corpus(*, hf_token: str | None = None) -> None:
    """
    Startup guard: validates existing corpus or restores from HF Dataset.
    Raises SystemExit on unrecoverable failure.
    """
    if corpus_is_present():
        try:
            count = validate_corpus()
            logger.info(
                "CORPUS_OK collection_name=%s document_count=%d",
                CHROMA_COLLECTION_NAME,
                count,
            )
            return
        except RuntimeError as exc:
            logger.warning("Existing corpus invalid, will attempt restore: %s", exc)

    hf_repo = os.environ.get(_HF_REPO_ENV)
    if not hf_repo:
        logger.error(
            "CORPUS_LOAD_FAILED: corpus missing and %s env var not set", _HF_REPO_ENV
        )
        raise SystemExit(1)

    try:
        restore_corpus_from_hf(hf_repo=hf_repo, hf_token=hf_token)
    except Exception as exc:
        logger.error("CORPUS_LOAD_FAILED: %s", exc)
        raise SystemExit(1)
