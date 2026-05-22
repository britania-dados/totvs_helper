"""Generate application ICO from the official Totvs Helper logo."""

from __future__ import annotations

from pathlib import Path


def _fit_logo_to_square(image):
    """Fit the full logo into a square canvas for Windows icon sizes."""
    from PIL import Image

    image = image.convert("RGBA")
    margin = 12
    max_size = 256 - (margin * 2)
    fitted = image.copy()
    fitted.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (256, 256), (255, 255, 255, 255))
    offset = ((256 - fitted.width) // 2, (256 - fitted.height) // 2)
    canvas.paste(fitted, offset, fitted)
    return canvas


def generate_icon(output_path: Path, source_path: Path) -> Path:
    from PIL import Image

    image = Image.open(source_path)
    icon_image = _fit_logo_to_square(image)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    icon_image.save(
        output_path,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    return output_path


def main() -> None:
    try:
        from PIL import Image  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "Pillow is required to generate the icon. Run: pip install Pillow"
        ) from exc

    project_root = Path(__file__).resolve().parents[1]
    source = project_root / "assets" / "totvs_helper_logo.png"
    output = project_root / "assets" / "totvs_helper.ico"

    if not source.exists():
        raise SystemExit(
            f"Logo source not found: {source}\n"
            "Place the official logo at assets/totvs_helper_logo.png"
        )

    generate_icon(output, source)
    print(f"Icon generated from logo: {output}")


if __name__ == "__main__":
    main()
