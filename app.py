# app.py — Hugging Face Spaces entrypoint

import os

from app.core.logger import configure_logging, get_logger
from app.ui.app import build_app
from services.corpus_persistence.corpus_loader import ensure_corpus

configure_logging()
logger = get_logger(__name__)

hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
ensure_corpus(hf_token=hf_token)

logger.info("Building Gradio app for HF Spaces...")

demo = build_app()

def _audit_api_schema(demo):
    import json

    def _find_ap_bool(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                cur = f"{path}.{k}"
                if k == "additionalProperties" and isinstance(v, bool):
                    logger.error(
                        "[SCHEMA_AUDIT] additionalProperties=%s at %s | keys=%s | fragment=%s",
                        v, cur, list(obj.keys()), json.dumps(obj)[:500],
                    )
                else:
                    _find_ap_bool(v, cur)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _find_ap_bool(item, f"{path}[{i}]")

    blocks = demo.get_blocks() if hasattr(demo, "get_blocks") else demo

    # Log raw api_info for components 33 and 34 directly from live block instances
    try:
        for block_id, block in blocks.blocks.items():
            if block_id in (33, 34) or getattr(block, "skip_api", True) is False:
                for method in ("api_info", "api_info_as_input", "api_info_as_output"):
                    fn = getattr(block, method, None)
                    if callable(fn):
                        try:
                            schema = fn()
                            logger.info(
                                "[COMPONENT_AUDIT] id=%s class=%s method=%s schema=%s",
                                block_id, type(block).__name__, method, json.dumps(schema)[:800],
                            )
                        except Exception as e:
                            logger.error("[COMPONENT_AUDIT] id=%s method=%s error=%s", block_id, method, e)
    except Exception as e:
        logger.error("[COMPONENT_AUDIT] block scan failed: %s", e)

    try:
        api_info = blocks.get_api_info()
        logger.info("[SCHEMA_AUDIT] get_api_info() succeeded — no crash")
        _find_ap_bool(api_info, "api_info")
    except Exception as exc:
        logger.error("[SCHEMA_AUDIT] get_api_info() crashed: %s", exc)
        try:
            config = blocks.config
            for comp in config.get("components", []):
                for key in ("api_info", "api_info_as_input", "api_info_as_output"):
                    schema = comp.get(key)
                    if schema:
                        _find_ap_bool(schema, f"component[{comp.get('id')}].{key}")
        except Exception as inner:
            logger.error("[SCHEMA_AUDIT] component scan failed: %s", inner)
        raise


_audit_api_schema(demo)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        share=False,
    )
