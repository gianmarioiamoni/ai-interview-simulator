# tests/performance/conftest.py
# EPIC-V13-09 — register performance markers (load tests may be slow).


def pytest_configure(config) -> None:  # type: ignore[no-untyped-def]
    config.addinivalue_line(
        "markers",
        "slow: longer-running performance / load certification tests",
    )
