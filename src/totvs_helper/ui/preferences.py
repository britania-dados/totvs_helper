"""Persistent UI preferences stored under %APPDATA%/TotvsHelper."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

MAX_RECENT_TABLES = 10
VALID_APPEARANCE = frozenset({"dark", "light", "system"})


@dataclass
class UserPreferences:
    appearance_mode: str = "dark"
    last_dsn: Optional[str] = None
    recent_tables: List[str] = field(default_factory=list)
    last_export_dir: Optional[str] = None
    default_export_dir: Optional[str] = None
    ask_open_folder: bool = True

    def add_recent_table(self, table: str) -> None:
        if not table:
            return
        updated = [table] + [t for t in self.recent_tables if t != table]
        self.recent_tables = updated[:MAX_RECENT_TABLES]

    def remember_dsn(self, dsn: str) -> None:
        if dsn:
            self.last_dsn = dsn

    def export_directory(self) -> str:
        for candidate in (self.default_export_dir, self.last_export_dir):
            if candidate and Path(candidate).is_dir():
                return candidate
        return str(Path.home())


def preferences_path() -> Path:
    app_data = Path(os.getenv("APPDATA", Path.home()))
    directory = app_data / "TotvsHelper"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "preferences.json"


def load_preferences() -> UserPreferences:
    path = preferences_path()
    if not path.exists():
        return UserPreferences()

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        mode = str(raw.get("appearance_mode", "dark"))
        if mode not in VALID_APPEARANCE:
            mode = "dark"
        return UserPreferences(
            appearance_mode=mode,
            last_dsn=raw.get("last_dsn"),
            recent_tables=list(raw.get("recent_tables", [])),
            last_export_dir=raw.get("last_export_dir"),
            default_export_dir=raw.get("default_export_dir"),
            ask_open_folder=bool(raw.get("ask_open_folder", True)),
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        logger.warning("Preferencias invalidas; usando padrao.", exc_info=True)
        return UserPreferences()


def save_preferences(preferences: UserPreferences) -> None:
    path = preferences_path()
    try:
        path.write_text(
            json.dumps(asdict(preferences), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:
        logger.warning("Nao foi possivel salvar preferencias.", exc_info=True)
