"""Sphinx configuration for the ini-file-editor API documentation."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make the src/ package importable so autodoc can introspect modules.
_repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_root / "src"))
sys.path.insert(0, str(_repo_root))

# Headless Qt: required so importing src.main_window does not pop a GUI on CI.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from src._version import __version__ as _pkg_version
except Exception:  # pragma: no cover
    _pkg_version = "dev"

project = "ini-file-editor"
author = "ini-file-editor contributors"
copyright = "%Y, ini-file-editor contributors"
release = _pkg_version
version = ".".join(_pkg_version.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
]

autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_typehints = "description"
autodoc_class_signature = "separated"

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
# Use :ivar: for attribute sections so dataclass fields documented in the
# class docstring don't clash with autodoc's per-field rendering.
napoleon_use_ivar = True
# Recognise the custom "Signals:" section we use on PyQt widgets.
napoleon_custom_sections = [("Signals", "params_style")]

# Mock heavy GUI dependencies so an import-time failure does not break the build.
autodoc_mock_imports = [
    "PyQt6",
    "yaml",
    "lxml",
    "PIL",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
language = "en"

html_theme = "furo"
html_static_path = ["_static"]
html_title = f"{project} {release}"
