# Contributing

Thank you for your interest in contributing to AI Interview Simulator.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Running tests

```bash
python -m pytest tests/
```

All 1427 tests must pass before submitting a pull request.

## Code standards

- Python 3.11+
- All public functions must have type annotations
- No `any` types
- New features require unit tests
- Prompts live in `app/prompts/` — changes must be validated with real LLM runs

## Architecture

Before contributing to the evaluation pipeline, scoring, or report generation, read:

- `docs/architecture/evaluation-pipeline.md`
- `docs/architecture/configuration.md`
- `docs/architecture/system_overview.md`

Evaluation thresholds in `infrastructure/config/evaluation.py` are governance constants. Changes require explicit justification and benchmark re-validation.

## Pull requests

- One concern per PR
- Include test coverage for changed logic
- Update `CHANGELOG.md` under `[Unreleased]`
- Documentation updates required for architectural changes
