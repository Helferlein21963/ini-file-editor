"""Generate a PyInstaller version_info.txt with embedded Windows VERSIONINFO resource."""

import os
import subprocess
import sys
from datetime import datetime

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)

# --- Edit these to brand the Windows VERSIONINFO string resource -----------
COMPANY_NAME = "Thomas Reichenbach"
COPYRIGHT_HOLDER = "Thomas Reichenbach"
# Set to the project's founding year to render a range (e.g. "2024-2026").
# Leave as ``None`` to render only the current year.
COPYRIGHT_START_YEAR: int | None = None
LICENSE_NOTICE = "Licensed under the MIT License"
# ---------------------------------------------------------------------------


def _get_commit_hash() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=_PROJECT_ROOT,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def _build_copyright() -> str:
    """Return ``Copyright (c) <year(-range)> <holder>. <license_notice>.``"""
    current_year = datetime.now().year
    if COPYRIGHT_START_YEAR and COPYRIGHT_START_YEAR < current_year:
        year_str = f"{COPYRIGHT_START_YEAR}-{current_year}"
    else:
        year_str = str(current_year)
    parts = [f"Copyright (c) {year_str} {COPYRIGHT_HOLDER}"]
    if LICENSE_NOTICE:
        parts.append(LICENSE_NOTICE)
    return ". ".join(parts) + "."


def _escape(value: str) -> str:
    """Escape a string for embedding inside the u'...' literal."""
    return value.replace("\\", "\\\\").replace("'", "\\'")


def generate(major: int, minor: int, patch: int, out_path: str = "version_info.txt") -> None:
    commit_hash = _get_commit_hash()
    company = _escape(COMPANY_NAME)
    legal_copyright = _escape(_build_copyright())
    content = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major}, {minor}, {patch}, 0),
    prodvers=({major}, {minor}, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{company}'),
         StringStruct(u'FileDescription', u'Comment-preserving INI file editor'),
         StringStruct(u'FileVersion', u'{major}.{minor}.{patch}'),
         StringStruct(u'InternalName', u'ini-file-editor'),
         StringStruct(u'LegalCopyright', u'{legal_copyright}'),
         StringStruct(u'OriginalFilename', u'ini-file-editor.exe'),
         StringStruct(u'ProductName', u'ini-file-editor'),
         StringStruct(u'ProductVersion', u'{commit_hash}')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1031, 1200])])
  ]
)
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    version_py = os.path.join(_PROJECT_ROOT, "src", "_version.py")
    with open(version_py, "w", encoding="utf-8") as f:
        f.write(f'__version__ = "{major}.{minor}.{patch}"\n')

    print(f"Generated {out_path} and src/_version.py: {major}.{minor}.{patch}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: generate_version_info.py <major> <minor> <patch>")
        sys.exit(1)
    generate(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
