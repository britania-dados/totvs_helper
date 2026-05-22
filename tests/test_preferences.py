"""Tests for UI preferences persistence."""

from __future__ import annotations

from pathlib import Path

from totvs_helper.ui.preferences import (
    UserPreferences,
    load_preferences,
    preferences_path,
    save_preferences,
)


def test_user_preferences_recent_tables_dedup() -> None:
    prefs = UserPreferences()
    prefs.add_recent_table("customer")
    prefs.add_recent_table("order")
    prefs.add_recent_table("customer")

    assert prefs.recent_tables == ["customer", "order"]


def test_save_and_load_preferences(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "totvs_helper.ui.preferences.preferences_path",
        lambda: tmp_path / "preferences.json",
    )

    prefs = UserPreferences(
        appearance_mode="light",
        last_dsn="TOTVS_PROD",
        recent_tables=["tab-a"],
        last_export_dir="C:/exports",
        default_export_dir="C:/default",
        ask_open_folder=False,
    )
    save_preferences(prefs)

    loaded = load_preferences()
    assert loaded.appearance_mode == "light"
    assert loaded.last_dsn == "TOTVS_PROD"
    assert loaded.recent_tables == ["tab-a"]
    assert loaded.last_export_dir == "C:/exports"
    assert loaded.default_export_dir == "C:/default"
    assert loaded.ask_open_folder is False


def test_export_directory_prefers_default(tmp_path: Path) -> None:
    default = tmp_path / "default"
    default.mkdir()
    prefs = UserPreferences(default_export_dir=str(default), last_export_dir="C:/other")
    assert prefs.export_directory() == str(default)


def test_load_preferences_invalid_json(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "preferences.json"
    monkeypatch.setattr(
        "totvs_helper.ui.preferences.preferences_path",
        lambda: path,
    )
    path.write_text("{invalid", encoding="utf-8")

    loaded = load_preferences()
    assert loaded.appearance_mode == "dark"
    assert loaded.last_dsn is None


def test_preferences_path_creates_directory(monkeypatch, tmp_path: Path) -> None:
    app_dir = tmp_path / "TotvsHelper"
    monkeypatch.setenv("APPDATA", str(tmp_path))
    path = preferences_path()
    assert path.parent == app_dir
    assert app_dir.exists()
