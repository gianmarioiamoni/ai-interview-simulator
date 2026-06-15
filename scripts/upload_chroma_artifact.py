#!/usr/bin/env python3
# scripts/upload_chroma_artifact.py
#
# One-time helper: packages storage/chroma/interview_corpus into a tar.gz
# and uploads it to an HF Dataset repo.
#
# Usage:
#   HF_TOKEN=hf_xxx python scripts/upload_chroma_artifact.py \
#       --repo <hf-username>/<dataset-repo-name>
#
# Required env vars:
#   HF_TOKEN — HuggingFace write token

import argparse
import os
import sys
import tarfile
import tempfile
from pathlib import Path

from huggingface_hub import upload_file

CORPUS_PATH = "storage/chroma/interview_corpus"
ARTIFACT_NAME = "chroma_corpus.tar.gz"


def _package(src: Path, dest: Path) -> None:
    print(f"Packaging {src} → {dest} ...")
    with tarfile.open(dest, "w:gz") as tar:
        tar.add(src, arcname=src.name)
    size_mb = dest.stat().st_size / 1024 / 1024
    print(f"Archive size: {size_mb:.1f} MB")


def _upload(artifact: Path, repo: str, token: str) -> None:
    print(f"Uploading to HF Dataset repo: {repo} ...")
    url = upload_file(
        path_or_fileobj=str(artifact),
        path_in_repo=ARTIFACT_NAME,
        repo_id=repo,
        repo_type="dataset",
        token=token,
    )
    print(f"Upload complete: {url}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload Chroma corpus to HF Dataset")
    parser.add_argument("--repo", required=True, help="HF Dataset repo id (owner/name)")
    args = parser.parse_args()

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if not token:
        print("ERROR: HF_TOKEN or HUGGINGFACE_TOKEN env var required", file=sys.stderr)
        sys.exit(1)

    src = Path(CORPUS_PATH)
    if not src.exists():
        print(f"ERROR: corpus directory not found: {src}", file=sys.stderr)
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmp:
        artifact = Path(tmp) / ARTIFACT_NAME
        _package(src, artifact)
        _upload(artifact, args.repo, token)


if __name__ == "__main__":
    main()
