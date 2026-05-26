"""Bump __version__ and packaging/windows_version_info.txt."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
VERSION_PY = PROJECT / "src" / "totvs_helper" / "version.py"
WIN_INFO = PROJECT / "packaging" / "windows_version_info.txt"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="New version, e.g. 2.1.2")
    args = parser.parse_args()

    text = VERSION_PY.read_text(encoding="utf-8")
    text = re.sub(
        r'__version__\s*=\s*["\'][^"\']+["\']',
        f'__version__ = "{args.version}"',
        text,
        count=1,
    )
    VERSION_PY.write_text(text, encoding="utf-8")

    parts = [int(p) for p in args.version.split(".")]
    while len(parts) < 4:
        parts.append(0)
    filevers = tuple(parts[:4])

    info = WIN_INFO.read_text(encoding="utf-8")
    info = re.sub(r"filevers=\([^)]+\)", f"filevers={filevers}", info)
    info = re.sub(r"prodvers=\([^)]+\)", f"prodvers={filevers}", info)
    info = re.sub(
        r"StringStruct\(u'FileVersion', u'[^']+'\)",
        f"StringStruct(u'FileVersion', u'{args.version}')",
        info,
    )
    info = re.sub(
        r"StringStruct\(u'ProductVersion', u'[^']+'\)",
        f"StringStruct(u'ProductVersion', u'{args.version}')",
        info,
    )
    WIN_INFO.write_text(info, encoding="utf-8")
    print(f"Versao atualizada para {args.version}")


if __name__ == "__main__":
    main()
