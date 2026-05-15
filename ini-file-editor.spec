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

# Auto-generate icon.ico from icon*.png if missing or stale.
import glob
import shutil
from pathlib import Path

icon_sources = sorted(glob.glob(os.path.join(ASSETS_DIR, 'icon*.png')))
if icon_sources:
    ico_stale = (
        not os.path.isfile(ICON_PATH)
        or max(os.path.getmtime(p) for p in icon_sources) > os.path.getmtime(ICON_PATH)
    )
    if ico_stale:
        try:
            from src.convert_icon import convert_pngs_to_ico
            convert_pngs_to_ico([Path(p) for p in icon_sources], Path(ICON_PATH))
            labels = ", ".join(os.path.basename(p) for p in icon_sources)
            print(f'[spec] Generated {ICON_PATH} from [{labels}]')
        except ImportError:
            print('[spec] Pillow not installed — skipping icon*.png -> icon.ico conversion')

asset_datas = [
    (src, 'assets') for src in (LOGO_PATH, ICON_PATH) if os.path.isfile(src)
]
exe_icon = ICON_PATH if os.path.isfile(ICON_PATH) else None

# Generate PDFs from Markdown manuals (skipped if weasyprint/Markdown not installed).
MANUALS_DIR = os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'docs', 'manuals')
try:
    import io as _io
    import markdown as _md_lib
    from xhtml2pdf import pisa as _pisa

    _CSS = (
        '@page{margin:2cm 3cm}'
        'body{font-family:Helvetica,Arial,sans-serif;font-size:11pt;line-height:1.5;color:#222}'
        'h1,h2,h3{color:#1a1a2e}'
        'code{background:#f4f4f4;padding:1px 4px;font-size:9pt}'
        'pre{background:#f4f4f4;padding:8pt}'
        'table{border-collapse:collapse;width:100%}'
        'th,td{border:1px solid #ccc;padding:6px 10px}th{background:#f0f0f0}'
    )
    for _src in sorted(glob.glob(os.path.join(MANUALS_DIR, '*.md'))):
        _src_path = Path(_src)
        _pdf_path = _src_path.with_suffix('.pdf')
        _body = _md_lib.markdown(
            _src_path.read_text(encoding='utf-8'),
            extensions=['tables', 'fenced_code', 'toc'],
        )
        _html = (
            f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<style>{_CSS}</style></head><body>{_body}</body></html>"
        )
        with open(str(_pdf_path), 'wb') as _f:
            _status = _pisa.CreatePDF(_html, dest=_f)
        if _status.err:
            print(f'[spec] WARNING: PDF generation had errors for {_src_path.name}')
        else:
            print(f'[spec] Generated {_pdf_path.name}')
    del _io, _md_lib, _pisa, _CSS
except ImportError:
    print('[spec] xhtml2pdf/Markdown not installed — skipping manual PDF generation')

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

# Copy PDF manuals to dist/ so they ship alongside the executable.
_dist = os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'dist')
os.makedirs(_dist, exist_ok=True)
for _pdf in glob.glob(os.path.join(MANUALS_DIR, '*.pdf')):
    shutil.copy2(_pdf, _dist)
    print(f'[spec] Copied {os.path.basename(_pdf)} -> dist/')
