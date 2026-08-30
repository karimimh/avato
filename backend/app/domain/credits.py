from __future__ import annotations

from dataclasses import dataclass, field


class InsufficientCredits(ValueError):
    pass


@dataclass(frozen=True)
class CreditEvent:
    key: str
    amount: int
    reason: str
    project_id: str | None = None


@dataclass
class CreditAccount:
    """Pure invariant model mirrored by the transactional SQL service."""

    events: dict[str, CreditEvent] = field(default_factory=dict)

    @property
    def balance(self) -> int:
        return sum(event.amount for event in self.events.values())

    def grant(self, key: str, amount: int, reason: str = "purchase") -> bool:
        if key in self.events:
            return False
        if amount <= 0:
            raise ValueError("grant amount must be positive")
        self.events[key] = CreditEvent(key, amount, reason)
        return True

    def charge_successful_export(self, export_id: str, project_id: str, successful: bool) -> bool:
        if not successful:
            return False
        key = f"export:{export_id}"
        if key in self.events:
            return False
        if any(
            event.reason == "export_charge" and event.project_id == project_id
            for event in self.events.values()
        ):
            return False
        if self.balance < 1:
            raise InsufficientCredits("paid export requires one credit")
        self.events[key] = CreditEvent(key, -1, "export_charge", project_id)
        return True

    def reconcile(self, key: str, amount: int) -> bool:
        if key in self.events:
            return False
        if amount == 0:
            raise ValueError("reconciliation amount cannot be zero")
        self.events[key] = CreditEvent(key, amount, "reconciliation")
        return True
