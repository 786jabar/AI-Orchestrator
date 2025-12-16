"""
Structured logging and audit trail utilities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List


@dataclass
class AuditEvent:
    name: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class AuditLogger:
    def __init__(self, name: str = "audit"):
        self.name = name
        self.events: List[AuditEvent] = []

    def log_event(self, name: str, payload: Dict[str, Any]) -> None:
        self.events.append(AuditEvent(name=name, payload=payload))

    def list_events(self) -> List[AuditEvent]:
        return self.events