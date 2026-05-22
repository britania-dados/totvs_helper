"""Legacy root entrypoint kept for compatibility."""

import sys
from pathlib import Path


def _configure_path() -> None:
    root_dir = Path(__file__).resolve().parent
    src_dir = root_dir / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))


def main() -> int:
    _configure_path()
    from totvs_helper.app.main import run

    return run()


if __name__ == "__main__":
    raise SystemExit(main())
