"""Data models for Linux setup verification.

This module contains only small, dependency-light data structures.
Keeping the models isolated makes the rest of the verification system easier to test
and reason about:

- probes only produce model instances
- notifiers only render model instances
- the verifier only coordinates model instances

That separation is a straightforward application of the Single Responsibility Principle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class StatusEntry:
    """Represents one environment check result.

    A status entry is the smallest meaningful unit of information in the system.
    Everything else in the verifier builds on top of these entries.

    Attributes:
        label: Human-readable name of the thing we checked.
        status: One of OK, WARNING, or ERROR.
        detail: Extra explanation shown to the user.
        blocking: Whether this failed check should block startup.
    """

    label: str
    status: str
    detail: str
    blocking: bool

    @property
    def ok(self) -> bool:
        """Return True when the status is a successful check."""
        return self.status == "OK"


@dataclass
class VerificationReport:
    """Aggregates all checks performed during setup verification.

    This is the main object passed between the probe, verifier, and notifier layers.
    It centralizes the logic for categorizing entries, which avoids duplicating the
    same filtering rules across multiple modules.
    """

    session_type: str
    entries: List[StatusEntry] = field(default_factory=list)

    def add_entry(self, label: str, ok: bool, detail: str, blocking: bool = True) -> None:
        """Append a check result to the report.

        We encode the text status here so the rest of the system works with a
        consistent vocabulary.
        """
        status = "OK" if ok else ("WARNING" if not blocking else "ERROR")
        self.entries.append(StatusEntry(label, status, detail, blocking))

    @property
    def blocking_missing(self) -> List[StatusEntry]:
        """Return all failed checks that must stop startup."""
        return [entry for entry in self.entries if not entry.ok and entry.blocking]

    @property
    def warning_missing(self) -> List[StatusEntry]:
        """Return all failed checks that are informative but non-blocking."""
        return [entry for entry in self.entries if not entry.ok and not entry.blocking]

    @property
    def has_blocking_failures(self) -> bool:
        return bool(self.blocking_missing)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warning_missing)
