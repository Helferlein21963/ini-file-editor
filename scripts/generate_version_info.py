"""Generate a PyInstaller version_info.txt with embedded Windows VERSIONINFO resource."""

import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)


def generate(major: int, minor: int, patch: int, out_path: str = "version_info.txt") -> None:
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
        [StringStruct(u'FileDescription', u'Comment-preserving INI file editor'),
         StringStruct(u'FileVersion', u'{major}.{minor}.{patch}'),
         StringStruct(u'InternalName', u'ini-file-editor'),
         StringStruct(u'LegalCopyright', u''),
         StringStruct(u'OriginalFilename', u'ini-file-editor.exe'),
         StringStruct(u'ProductName', u'ini-file-editor'),
         StringStruct(u'ProductVersion', u'{major}.{minor}')])
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
