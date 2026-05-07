"""
main.py – Application entry point.
"""
import sys
from pathlib import Path

# Support running from the repo root, from the src directory, and in a PyInstaller bundle.
base_dir = Path(__file__).parent
if getattr(sys, "frozen", False):
    base_dir = Path(sys._MEIPASS)

sys.path.insert(0, str(base_dir))
sys.path.insert(0, str(base_dir / "src"))

from src.main_window import main

if __name__ == "__main__":
    main()
