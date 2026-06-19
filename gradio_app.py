# gradio_app.py — DEPRECATED
#
# This entry point is superseded by:
#   app/main.py  — local development
#   app.py       — Hugging Face Spaces (production)
#
# It is retained only for historical reference and will be removed post-R4.
# Do NOT use this entry point; it lacks corpus validation and startup hardening.

raise SystemExit(
    "gradio_app.py is deprecated. "
    "Use 'python -m app.main' for local runs or app.py for HF Spaces."
)
