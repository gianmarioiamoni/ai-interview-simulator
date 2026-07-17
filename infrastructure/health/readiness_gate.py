# infrastructure/health/readiness_gate.py
#
# EPIC-08 P4/C11 — CI/deploy readiness gate.
# Consumes GET /health/ready only; does not reimplement probes (AR-10, HLT-06).

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from infrastructure.config.settings import Settings, settings as default_settings
from infrastructure.health.http import READINESS_PATH

UrlOpen = Callable[..., Any]


def build_readiness_gate_url(settings: Settings) -> str:
    base = settings.readiness_gate_base_url.rstrip("/")
    return f"{base}{READINESS_PATH}"


def check_readiness_gate(
    settings: Settings | None = None,
    *,
    urlopen: UrlOpen | None = None,
) -> int:
    """
    Query the centralized readiness HTTP interface.

    Returns process exit code:
      0 — ready (HTTP 200 and body.ready == true)
      1 — not ready, transport error, or unexpected response
    """
    resolved = settings if settings is not None else default_settings
    url = build_readiness_gate_url(resolved)
    opener: UrlOpen = urlopen if urlopen is not None else urllib.request.urlopen
    request = urllib.request.Request(url, method="GET")

    try:
        with opener(request, timeout=resolved.readiness_gate_timeout_s) as response:
            status = getattr(response, "status", None)
            if status is None:
                status = response.getcode()
            body = response.read()
            if int(status) != 200:
                _print_failure(url, int(status), body)
                return 1
            payload = _parse_json_object(body)
            if payload.get("ready") is not True:
                _print_failure(url, int(status), body)
                return 1
            return 0
    except urllib.error.HTTPError as exc:
        body = exc.read() if hasattr(exc, "read") else b""
        _print_failure(url, int(exc.code), body)
        return 1
    except Exception as exc:
        print(
            f"readiness gate failed: url={url} error_type={type(exc).__name__} detail={exc}",
            file=sys.stderr,
        )
        return 1


def main(argv: list[str] | None = None) -> int:
    del argv  # Settings/env driven; no CLI flags required for C11.
    return check_readiness_gate()


def _parse_json_object(body: bytes) -> dict[str, Any]:
    if not body:
        return {}
    parsed = json.loads(body.decode("utf-8"))
    if not isinstance(parsed, dict):
        return {}
    return parsed


def _print_failure(url: str, status: int, body: bytes) -> None:
    text = body.decode("utf-8", errors="replace") if body else ""
    print(
        f"readiness gate failed: url={url} http_status={status} body={text}",
        file=sys.stderr,
    )
