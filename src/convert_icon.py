#!/usr/bin/env python3
"""
Script to convert icon.png to icon.ico for Windows application.
"""
from pathlib import Path
from PIL import Image

def convert_png_to_ico(png_path: Path, ico_path: Path) -> None:
    """Convert PNG to ICO format with multiple sizes."""
    img = Image.open(png_path)
    # Ensure square image
    size = max(img.size)
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    # Create ICO with multiple sizes
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = []
    for s in sizes:
        if s[0] <= size:
            icons.append(img.resize(s, Image.Resampling.LANCZOS))
    img.save(ico_path, format='ICO', sizes=sizes)

if __name__ == "__main__":
    assets_dir = Path(__file__).resolve().parent.parent / "assets"
    png_path = assets_dir / "icon.png"
    ico_path = assets_dir / "icon.ico"

    if png_path.exists():
        assets_dir.mkdir(parents=True, exist_ok=True)
        convert_png_to_ico(png_path, ico_path)
        print(f"Converted {png_path} to {ico_path}")
    else:
        print(f"Error: {png_path} not found")