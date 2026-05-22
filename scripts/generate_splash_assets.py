"""Generate splash images for PyInstaller and in-app startup screen."""

from __future__ import annotations

from pathlib import Path

_BG = (20, 20, 20)
_ACCENT = (200, 16, 46)


def _open_logo(source: Path):
    from PIL import Image

    return Image.open(source).convert("RGBA")


def generate_splash_assets(
    source_logo: Path,
    splash_png: Path,
    ui_logo_png: Path,
) -> None:
    from PIL import Image, ImageDraw

    logo = _open_logo(source_logo)

    # PyInstaller bootloader splash (shown during .exe unpack)
    splash_w, splash_h = 520, 340
    splash = Image.new("RGB", (splash_w, splash_h), _BG)
    draw = ImageDraw.Draw(splash)
    draw.rectangle((0, 0, splash_w, 5), fill=_ACCENT)

    fitted = logo.copy()
    fitted.thumbnail((300, 200), Image.Resampling.LANCZOS)
    x = (splash_w - fitted.width) // 2
    y = 48 + (200 - fitted.height) // 2
    splash.paste(fitted, (x, y), fitted)
    splash_png.parent.mkdir(parents=True, exist_ok=True)
    splash.save(splash_png, format="PNG", optimize=True)

    # Smaller logo for tkinter (avoids clipping from subsample)
    ui_logo = logo.copy()
    ui_logo.thumbnail((280, 180), Image.Resampling.LANCZOS)
    ui_logo.save(ui_logo_png, format="PNG", optimize=True)


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    source = project / "assets" / "totvs_helper_logo.png"
    if not source.exists():
        raise SystemExit(f"Logo not found: {source}")

    generate_splash_assets(
        source,
        project / "assets" / "splash.png",
        project / "assets" / "splash_logo_ui.png",
    )
    print("Generated assets/splash.png and assets/splash_logo_ui.png")


if __name__ == "__main__":
    main()
