# -*- mode: python ; coding: utf-8 -*-

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(SPEC)))

from scripts.generate_version_info import generate

major = int(os.environ.get('MAJOR_VERSION', '1'))
minor = int(os.environ.get('MINOR_VERSION', '0'))
try:
    patch = int(subprocess.check_output(['git', 'rev-list', '--count', 'HEAD'], text=True).strip())
except Exception:
    patch = 0

generate(major, minor, patch)

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'assets')
LOGO_PATH = os.path.join(ASSETS_DIR, 'logo.png')
ICON_PNG_PATH = os.path.join(ASSETS_DIR, 'icon.png')
ICON_PATH = os.path.join(ASSETS_DIR, 'icon.ico')

# Auto-generate icon.ico from icon.png if missing or stale.
if os.path.isfile(ICON_PNG_PATH):
    ico_stale = (
        not os.path.isfile(ICON_PATH)
        or os.path.getmtime(ICON_PNG_PATH) > os.path.getmtime(ICON_PATH)
    )
    if ico_stale:
        try:
            from src.convert_icon import convert_png_to_ico
            convert_png_to_ico(ICON_PNG_PATH, ICON_PATH)
            print(f'[spec] Generated {ICON_PATH} from {ICON_PNG_PATH}')
        except ImportError:
            print('[spec] Pillow not installed — skipping icon.png -> icon.ico conversion')

asset_datas = [
    (src, 'assets') for src in (LOGO_PATH, ICON_PATH) if os.path.isfile(src)
]
exe_icon = ICON_PATH if os.path.isfile(ICON_PATH) else None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=asset_datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ini-file-editor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon=exe_icon,
)
