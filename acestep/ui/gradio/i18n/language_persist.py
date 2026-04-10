"""Persist UI language choice across server restarts.

Gradio builds component labels once at startup; a language change requires
a full process restart to rebuild the interface. This module stores the
user's choice in a small file so the next startup picks it up automatically.
"""

from __future__ import annotations

import os
from pathlib import Path


def _state_file() -> Path:
    """Return the path to the persisted language state file."""
    # Honor XDG_STATE_HOME when present, otherwise use the user's home dir.
    xdg = os.environ.get("XDG_STATE_HOME")
    if xdg:
        base = Path(xdg) / "ace-step"
    else:
        base = Path.home() / ".config" / "ace-step"
    return base / "ui_language"


def save_language(code: str) -> None:
    """Write the selected UI language code to disk."""
    if not code:
        return
    path = _state_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code.strip(), encoding="utf-8")


def load_language(default: str = "en") -> str:
    """Return the persisted UI language code, or *default* if none is saved."""
    path = _state_file()
    if not path.exists():
        return default
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        return default
    return value or default
