"""Color-coded helpers for the generation status Markdown panel.

The status panel (``#acestep-status-output``) is a ``gr.Markdown`` that
accepts inline HTML. Wrap text in one of ``.status-ok`` / ``.status-err``
/ ``.status-warn`` spans so the matching CSS rules in ``polish.py`` tint
the resulting chip emerald / rose / amber.

Why wrap instead of Markdown-style formatting (**bold**, color:red):
- Markdown bold cannot carry a color token
- Inline ``style="color:…"`` is stripped by Gradio's sanitizer in some
  versions; class-based styling routes through our stylesheet and
  stays consistent with the rest of the theme
- Centralising the wrapper here means handlers only learn one API and
  we can add new states (``.status-info``, ``.status-busy``) without
  touching every call site
"""

from __future__ import annotations

from html import escape

__all__ = [
    "format_status_ok",
    "format_status_err",
    "format_status_warn",
    "format_status_busy",
]


def _wrap(text: str, klass: str) -> str:
    """Return ``text`` wrapped in a span carrying ``klass``.

    The text is HTML-escaped so user-originated error messages cannot
    smuggle markup into the status panel. Emojis pass through untouched.
    """
    return f'<span class="{klass}">{escape(text)}</span>'


def format_status_ok(text: str) -> str:
    """Green success chip (e.g. "✅ Generation Complete")."""
    return _wrap(text, "status-ok")


def format_status_err(text: str) -> str:
    """Red error chip (e.g. "❌ OOM during denoising")."""
    return _wrap(text, "status-err")


def format_status_warn(text: str) -> str:
    """Amber warning chip (e.g. "⚠️ Cache miss, recomputing")."""
    return _wrap(text, "status-warn")


def format_status_busy(text: str) -> str:
    """Neutral "in-progress" chip — no color modifier class, just the
    base chip styling from ``#acestep-status-output p``."""
    return escape(text)
