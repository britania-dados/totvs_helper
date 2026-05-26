"""Project paths for development and PyInstaller frozen builds."""

from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    """Repository root (parent of src/totvs_helper)."""
    return Path(__file__).resolve().parents[2]


def bundle_root() -> Path:
    """PyInstaller extract dir when frozen; else project root."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return project_root()


def assets_dir() -> Path:
    """Directory with logos, icons, splash images."""
    bundle = bundle_root()
    candidate = bundle / "assets"
    if candidate.is_dir():
        return candidate
    return project_root() / "assets"


def pentaho_templates_dir() -> Path:
    """Packaged Pentaho KTR/KJB templates."""
    if getattr(sys, "frozen", False):
        return bundle_root() / "packaging" / "pentaho" / "templates"
    return project_root() / "packaging" / "pentaho" / "templates"


def env_search_paths(env_file: str = ".env") -> list[Path]:
    """Paths to try when loading .env (exe dir first, then bundle)."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        bundle_dir = Path(getattr(sys, "_MEIPASS", exe_dir))
        return [exe_dir / env_file, bundle_dir / env_file]
    return [project_root() / env_file]
