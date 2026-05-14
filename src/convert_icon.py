#!/usr/bin/env python3
"""
Convert one or more PNG files into a Windows multi-resolution .ico.

Single source: ``icon.png`` is rescaled to the standard ICO sizes.
Multiple sources: each ``icon*.png`` contributes one frame at its
native size; non-square sources are centered on a transparent square
canvas so no stretching occurs. Remaining standard sizes are filled
in by scaling the largest source.
"""
from pathlib import Path
from typing import Iterable

from PIL import Image


STANDARD_SIZES = (16, 32, 48, 64, 128, 256)


def _square(img: Image.Image) -> Image.Image:
    if img.size[0] == img.size[1]:
        return img.convert("RGBA") if img.mode != "RGBA" else img
    side = max(img.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    source = img.convert("RGBA")
    offset = ((side - source.size[0]) // 2, (side - source.size[1]) // 2)
    canvas.paste(source, offset, source)
    return canvas


def convert_pngs_to_ico(png_paths: Iterable[Path], ico_path: Path) -> None:
    """Combine multiple PNGs into one Windows .ico.

    Each PNG is embedded at its own native size; non-square sources are
    padded with transparency to a square canvas. Any missing standard
    sizes (16/32/48/64/128/256) up to the largest source are generated
    by scaling the largest provided image.
    """
    images = [_square(Image.open(p)) for p in png_paths]
    if not images:
        raise ValueError("at least one PNG is required")
    images.sort(key=lambda im: im.size[0], reverse=True)

    largest = images[0].size[0]
    native = {im.size[0] for im in images}
    all_sizes = sorted(native | {s for s in STANDARD_SIZES if s <= largest}, reverse=True)
    sizes = [(s, s) for s in all_sizes]

    base, extras = images[0], images[1:]
    base.save(ico_path, format='ICO', sizes=sizes, append_images=extras)


def convert_png_to_ico(png_path: Path, ico_path: Path) -> None:
    """Backward-compatible single-PNG wrapper around :func:`convert_pngs_to_ico`."""
    convert_pngs_to_ico([png_path], ico_path)


if __name__ == "__main__":
    assets_dir = Path(__file__).resolve().parent.parent / "assets"
    ico_path = assets_dir / "icon.ico"
    sources = sorted(assets_dir.glob("icon*.png"))

    if not sources:
        print(f"Error: no icon*.png found in {assets_dir}")
    else:
        assets_dir.mkdir(parents=True, exist_ok=True)
        convert_pngs_to_ico(sources, ico_path)
        labels = ", ".join(p.name for p in sources)
        print(f"Converted [{labels}] to {ico_path}")
