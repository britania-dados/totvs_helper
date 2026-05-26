"""UI flow state for Totvs Helper."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from pyodbc import Connection

    from totvs_helper.infra.odbc_client import FieldMeta
    from totvs_helper.services.script_generator import GeneratedScripts


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
    ecom_keys: bool = False
    table_fields: List["FieldMeta"] = field(default_factory=list)
    table_pk_fields: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def history_key(self) -> tuple[str, str]:
        return (self.dsn.casefold(), self.table.casefold())

    @property
    def label(self) -> str:
        time_str = self.created_at.strftime("%H:%M")
        return f"{self.table} ({time_str})"


@dataclass
class SessionHistory:
    """Generation history (persisted on disk, capped at 20 entries)."""

    entries: List[HistoryEntry] = field(default_factory=list)
    max_entries: int = 20

    def add(self, entry: HistoryEntry) -> None:
        key = entry.history_key
        self.entries = [e for e in self.entries if e.history_key != key]
        self.entries.insert(0, entry)
        self.entries = self.entries[: self.max_entries]

    def clear(self) -> None:
        self.entries.clear()


@dataclass
class SessionState:
    """Mutable session data shared across wizard steps."""

    view: SidebarView = SidebarView.DSN
    selected_odbc: Optional[str] = None
    selected_table: Optional[str] = None
    include_free_fields: bool = True
    multi_company: bool = True
    ecom_keys: bool = False
    tables: List[str] = field(default_factory=list)
    table_fields: List["FieldMeta"] = field(default_factory=list)
    table_pk_fields: List[str] = field(default_factory=list)
    connection: Optional["Connection"] = None
    scripts: Optional["GeneratedScripts"] = None
    history: SessionHistory = field(default_factory=SessionHistory)

    def release_connection(self) -> None:
        """Close ODBC connection if open."""
        if self.connection is None:
            return
        try:
            self.connection.close()
        except Exception:
            pass
        self.connection = None

    def reset_for_new_process(self) -> None:
        """Clear selections and return to DSN step."""
        self.release_connection()
        self.view = SidebarView.DSN
        self.selected_odbc = None
        self.selected_table = None
        self.include_free_fields = True
        self.multi_company = True
        self.ecom_keys = False
        self.tables = []
        self.table_fields = []
        self.table_pk_fields = []
        self.scripts = None
