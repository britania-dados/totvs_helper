"""UI flow state for Totvs Helper."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from pyodbc import Connection

    from totvs_helper.services.script_generator import GeneratedScripts


class FlowStep(Enum):
    """Wizard steps shown in the main window."""

    DSN = "dsn"
    TABLE = "table"
    RESULTS = "results"
    HISTORY = "history"


class SidebarView(Enum):
    """Active content area (wizard step or history)."""

    DSN = "dsn"
    TABLE = "table"
    RESULTS = "results"
    HISTORY = "history"


@dataclass
class HistoryEntry:
    """One script generation snapshot in the current session."""

    dsn: str
    table: str
    include_free_fields: bool
    multi_company: bool
    scripts: "GeneratedScripts"
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def label(self) -> str:
        time_str = self.created_at.strftime("%H:%M")
        return f"{self.table} ({time_str})"


@dataclass
class SessionHistory:
    """In-memory history capped at 10 entries."""

    entries: List[HistoryEntry] = field(default_factory=list)
    max_entries: int = 10

    def add(self, entry: HistoryEntry) -> None:
        self.entries.insert(0, entry)
        self.entries = self.entries[: self.max_entries]

    def clear(self) -> None:
        self.entries.clear()


@dataclass
class SessionState:
    """Mutable session data shared across wizard steps."""

    step: FlowStep = FlowStep.DSN
    view: SidebarView = SidebarView.DSN
    selected_odbc: Optional[str] = None
    selected_table: Optional[str] = None
    include_free_fields: bool = True
    multi_company: bool = True
    tables: List[str] = field(default_factory=list)
    connection: Optional["Connection"] = None
    scripts: Optional["GeneratedScripts"] = None
    history: SessionHistory = field(default_factory=SessionHistory)

    def reset_for_new_process(self) -> None:
        """Clear selections and return to DSN step."""
        self.step = FlowStep.DSN
        self.view = SidebarView.DSN
        self.selected_odbc = None
        self.selected_table = None
        self.include_free_fields = True
        self.multi_company = True
        self.tables = []
        self.scripts = None
