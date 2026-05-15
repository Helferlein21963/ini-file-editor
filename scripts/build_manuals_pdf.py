"""Convert docs/manuals/*.md to PDF files.

Usage:
    python scripts/build_manuals_pdf.py              # writes to docs/manuals/
    python scripts/build_manuals_pdf.py <out_dir>    # writes to <out_dir>

Requires: weasyprint>=60.0, Markdown>=3.6
"""

import sys
import argparse
from pathlib import Path

_CSS = """
@page { margin: 2cm 3cm; }
body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #222;
}
h1, h2, h3 { color: #1a1a2e; }
code { background: #f4f4f4; padding: 1px 4px; font-size: 9pt; }
pre { background: #f4f4f4; padding: 8pt; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left; }
th { background: #f0f0f0; font-weight: bold; }
blockquote { border-left: 4px solid #ccc; margin: 0; padding-left: 1em; color: #555; }
"""

_REPO_ROOT = Path(__file__).parent.parent
_MANUALS_DIR = _REPO_ROOT / "docs" / "manuals"


def convert_manual(md_path: Path, out_dir: Path) -> Path:
    """Convert a single Markdown manual to PDF.

    Args:
        md_path: Path to the source .md file.
        out_dir: Directory in which to write the .pdf file.

    Returns:
        Path to the generated PDF file.
    """
    import markdown as md_lib
    from xhtml2pdf import pisa

    html_body = md_lib.markdown(
        md_path.read_text(encoding="utf-8"),
        extensions=["tables", "fenced_code", "toc"],
    )
    html = (
        "<!DOCTYPE html><html>"
        f"<head><meta charset='utf-8'><style>{_CSS}</style></head>"
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

    errors = 0
    for md_file in md_files:
        try:
            pdf_path = convert_manual(md_file, out_dir)
            print(f"  Generated: {pdf_path}")
        except Exception as exc:
            print(f"  ERROR converting {md_file.name}: {exc}", file=sys.stderr)
            errors += 1

    if errors:
        sys.exit(1)
    print(f"Done: {len(md_files)} PDF(s) written to {out_dir}")


if __name__ == "__main__":
    main()
