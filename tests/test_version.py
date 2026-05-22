"""Ensure release version is defined in a single module."""

from __future__ import annotations

import re
from pathlib import Path

from totvs_helper.version import __version__


def test_windows_version_info_matches_package_version() -> None:
    root = Path(__file__).resolve().parents[1]
    info_path = root / "packaging" / "windows_version_info.txt"
    content = info_path.read_text(encoding="utf-8")
    assert f"u'{__version__}'" in content or f'u"{__version__}"' in content
    assert re.search(r"filevers=\(\d+, \d+, \d+, 0\)", content)
    major, minor, patch = (int(part) for part in __version__.split("."))
    assert f"filevers=({major}, {minor}, {patch}, 0)" in content
