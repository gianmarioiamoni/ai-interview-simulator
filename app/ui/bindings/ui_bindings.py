# app/ui/bindings/ui_bindings.py

from app.ui.bindings.orchestrators.ui_event_orchestrator import UIEventOrchestrator


def bind_events(components) -> None:
    orchestrator = UIEventOrchestrator(components)
    orchestrator.bind()
