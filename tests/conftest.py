# tests/conftest.py
"""
Root test configuration.

Stubs broken native extensions before any test module is imported:

  1. sentence_transformers  — x86_64 PIL/_imaging.so crash on Apple Silicon
  2. jiter                  — x86_64 jiter.cpython-312-darwin.so crash on
                              Apple Silicon (pulled in transitively by openai)

Providing these stubs at the sys.modules level prevents ImportError during
test collection and lets every unit test run in isolation without needing
real ML / OpenAI infrastructure.

Production code is not affected; these stubs are only active during test runs.
"""

import sys
import types
from unittest.mock import MagicMock


# ─────────────────────────────────────────────────────────────────────────────
# 1.  sentence_transformers stub
# ─────────────────────────────────────────────────────────────────────────────

def _build_sentence_transformers_stub() -> tuple[
    types.ModuleType, types.ModuleType, types.ModuleType
]:
    st = types.ModuleType("sentence_transformers")

    class _Tensor(float):
        def item(self) -> float:
            return float(self)

    class SentenceTransformer:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def encode(self, text, convert_to_tensor: bool = False, **kwargs):
            return _Tensor(0.0) if convert_to_tensor else [0.0]

    st.SentenceTransformer = SentenceTransformer  # type: ignore[attr-defined]

    util = types.ModuleType("sentence_transformers.util")
    util.cos_sim = lambda a, b: _Tensor(0.0)  # type: ignore[attr-defined]
    st.util = util  # type: ignore[attr-defined]

    backend = types.ModuleType("sentence_transformers.backend")
    backend.load_onnx_model = MagicMock()  # type: ignore[attr-defined]
    backend.load_openvino_model = MagicMock()  # type: ignore[attr-defined]
    st.backend = backend  # type: ignore[attr-defined]

    return st, util, backend


_st_stub, _st_util_stub, _st_backend_stub = _build_sentence_transformers_stub()
sys.modules.setdefault("sentence_transformers", _st_stub)
sys.modules.setdefault("sentence_transformers.util", _st_util_stub)
sys.modules.setdefault("sentence_transformers.backend", _st_backend_stub)


# ─────────────────────────────────────────────────────────────────────────────
# 2.  jiter stub  (openai → openai.lib.streaming.chat._completions → jiter)
# ─────────────────────────────────────────────────────────────────────────────

def _build_jiter_stub() -> types.ModuleType:
    jiter = types.ModuleType("jiter")

    def from_json(data: bytes, **kwargs):  # noqa: D103
        import json
        return json.loads(data)

    jiter.from_json = from_json  # type: ignore[attr-defined]

    # jiter is a C extension that exposes a bare `*` export; mirror that.
    jiter.__all__ = ["from_json"]  # type: ignore[attr-defined]
    return jiter


sys.modules.setdefault("jiter", _build_jiter_stub())


# ─────────────────────────────────────────────────────────────────────────────
# 3.  pydub / audioop stub  (gradio → pydub → audioop missing on Python 3.13)
# ─────────────────────────────────────────────────────────────────────────────

for _mod in ("audioop", "pyaudioop", "pydub", "pydub.utils", "pydub.audio_segment"):
    sys.modules.setdefault(_mod, MagicMock())


# ─────────────────────────────────────────────────────────────────────────────
# 4.  weasyprint stub  (requires system libs not present in test runner)
# ─────────────────────────────────────────────────────────────────────────────

sys.modules.setdefault("weasyprint", MagicMock())
