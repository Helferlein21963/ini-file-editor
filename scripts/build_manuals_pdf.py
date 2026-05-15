"""Convert docs/manuals/*.md to PDF files.

Usage:
    python scripts/build_manuals_pdf.py              # writes to docs/manuals/
    python scripts/build_manuals_pdf.py <out_dir>    # writes to <out_dir>

Requires: xhtml2pdf>=0.2.11, Markdown>=3.6

Notes on glyph coverage:
- xhtml2pdf renders via ReportLab.  Its default Helvetica is a Type-1 font
  with only Latin-1 coverage, which is why arrows, geometric shapes, and
  fullwidth symbols come out as black boxes by default.
- We therefore register a system TrueType font (Arial / DejaVu Sans) and
  use it as the body font.  That covers ≠ ★ ↓ ▼ ▶ ◀ ⇔ etc.
- Color emoji fonts are not supported by ReportLab, so emoji characters are
  stripped before conversion.  The Markdown sources keep all emoji; only the
  rendered PDF is affected.
- Fullwidth forms (＋ － ＝) are absent from Arial as well — they are mapped
  to their ASCII equivalents.
"""

import os
import re
import sys
import argparse
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_MANUALS_DIR = _REPO_ROOT / "docs" / "manuals"


def _register_body_font() -> str | None:
    """Register a TTF font with broad Unicode coverage for body text.

    Returns:
        The ReportLab font name to use in CSS, or ``None`` if no suitable
        font file was found.
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    candidates: list[Path] = []
    if os.name == "nt":
        windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
        candidates += [
            windir / "Fonts" / "arial.ttf",
            windir / "Fonts" / "ARIAL.TTF",
            windir / "Fonts" / "segoeui.ttf",
        ]
    # Linux — common DejaVu Sans locations
    candidates += [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
    ]
    # macOS
    candidates += [
        Path("/Library/Fonts/Arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    ]

    for path in candidates:
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont("BodyFont", str(path)))
                return "BodyFont"
            except Exception:
                continue
    return None


# Characters to strip before PDF conversion.  ReportLab cannot render color
# emoji fonts, so emoji come out as missing-glyph boxes regardless of the
# body font we pick.  The Markdown sources are not modified.
#   SMP block U+1F000–U+1FFFF covers 💾 📁 🗑 📋 🌍 🔍 🔀 🔄 etc.
#   U+FE0F is the emoji presentation variation selector.
#   ✏ ➕ ⤵ ℹ are BMP emoji that appear in the manuals.
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FFFF️✏➕⤵ℹ]",
    flags=re.UNICODE,
)

# Fullwidth and other special characters that even broad-coverage Western
# TTFs (Arial / DejaVu Sans) typically don't include.  Mapped to their
# closest ASCII equivalents so the diff-status table reads cleanly.
_FALLBACK_SUBSTITUTIONS = {
    "＋": "+",
    "－": "-",
    "＝": "=",
}


def _normalize_for_pdf(text: str) -> str:
    """Apply emoji-stripping and fullwidth-symbol substitutions."""
    text = _EMOJI_RE.sub("", text)
    for src, dst in _FALLBACK_SUBSTITUTIONS.items():
        text = text.replace(src, dst)
    return text


def _build_css(body_font: str | None) -> str:
    family = f"'{body_font}', " if body_font else ""
    return f"""
@page {{ margin: 2cm 3cm; }}
body {{
    font-family: {family}"Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #222;
}}
h1, h2, h3 {{ color: #1a1a2e; }}
code {{ background: #f4f4f4; padding: 1px 4px; font-size: 9pt; }}
pre {{ background: #f4f4f4; padding: 8pt; }}
pre code {{ background: none; padding: 0; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
th {{ background: #f0f0f0; font-weight: bold; }}
blockquote {{ border-left: 4px solid #ccc; margin: 0; padding-left: 1em; color: #555; }}
"""


def convert_manual(md_path: Path, out_dir: Path, body_font: str | None) -> Path:
    """Convert a single Markdown manual to PDF.

    Args:
        md_path: Path to the source .md file.
        out_dir: Directory in which to write the .pdf file.
        body_font: ReportLab name of the registered body font, or ``None``
            to fall back to the default Helvetica.

    Returns:
        Path to the generated PDF file.
    """
    import markdown as md_lib
    from xhtml2pdf import pisa

    html_body = md_lib.markdown(
        md_path.read_text(encoding="utf-8"),
        extensions=["tables", "fenced_code", "toc"],
    )
    css = _build_css(body_font)
    html = _normalize_for_pdf(
        "<!DOCTYPE html><html>"
        f"<head><meta charset='utf-8'><style>{css}</style></head>"
        f"<body>{html_body}</body></html>"
    )
    out_path = out_dir / (md_path.stem + ".pdf")
    with open(out_path, "wb") as f:
        status = pisa.CreatePDF(html, dest=f)
    if status.err:
        raise RuntimeError(f"PDF generation failed with {status.err} error(s)")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert manuals to PDF")
    parser.add_argument(
        "out_dir",
        nargs="?",
        default=str(_MANUALS_DIR),
        help="Output directory (default: docs/manuals/)",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    md_files = sorted(_MANUALS_DIR.glob("*.md"))
    if not md_files:
        print("No .md files found in docs/manuals/")
        return

    body_font = _register_body_font()
    if body_font is None:
        print(
            "  WARNING: no broad-coverage TTF font found — falling back to "
            "Helvetica.  Symbols outside Latin-1 may render as black boxes.",
            file=sys.stderr,
        )

    errors = 0
    for md_file in md_files:
        try:
            pdf_path = convert_manual(md_file, out_dir, body_font)
            print(f"  Generated: {pdf_path}")
        except Exception as exc:
            print(f"  ERROR converting {md_file.name}: {exc}", file=sys.stderr)
            errors += 1

    if errors:
        sys.exit(1)
    print(f"Done: {len(md_files)} PDF(s) written to {out_dir}")


if __name__ == "__main__":
    main()
