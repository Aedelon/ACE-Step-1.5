"""Multi-LoRA dataframe handlers.

Bridges the Gradio UI ``build_lora_controls()`` widgets with the runtime
LoRA management methods on ``AceStepHandler``: ``add_lora``, ``remove_lora``,
``set_active_lora_adapter``, ``set_lora_scale``, ``unload_lora``,
``set_use_lora`` and ``get_lora_status``.

The dataframe shape is fixed to three columns:

    [active_marker, name, scale]

where ``active_marker`` is ``"★"`` for the active adapter and an empty
string otherwise. ``scale`` is a Python ``float`` between 0.0 and 1.0.

All handlers return a 2-tuple ``(status_text, dataframe_rows)`` so the
caller can wire a single ``.click()`` to update both outputs at once.
"""

from __future__ import annotations

from typing import Any

import gradio as gr


ACTIVE_MARKER = "★"


def status_to_rows(dit_handler: Any) -> list[list[Any]]:
    """Convert ``dit_handler.get_lora_status()`` to dataframe rows.

    Args:
        dit_handler: The DiT handler exposing ``get_lora_status``.

    Returns:
        A list of ``[active_marker, name, scale]`` rows. Empty list when
        no LoRA is loaded or when the handler raises.
    """
    try:
        status = dit_handler.get_lora_status()
    except Exception:
        return []
    if not isinstance(status, dict) or not status.get("loaded"):
        return []
    scales = status.get("scales") or {}
    active = status.get("active_adapter") or ""
    rows: list[list[Any]] = []
    for name, scale in scales.items():
        marker = ACTIVE_MARKER if name == active else ""
        try:
            scale_value = float(scale)
        except (TypeError, ValueError):
            scale_value = 1.0
        rows.append([marker, str(name), scale_value])
    return rows


def _no_selection_message() -> str:
    return "⚠️ Select a row in the adapters table first."


def handle_add_lora(
    path: str,
    adapter_name: str,
    dit_handler: Any,
) -> tuple[str, list[list[Any]]]:
    """Add a LoRA adapter and refresh the dataframe.

    Args:
        path: Filesystem path to the LoRA adapter directory or file.
        adapter_name: Optional adapter name; empty/whitespace falls back
            to the default derived from the path.
        dit_handler: Active DiT handler instance.

    Returns:
        ``(status_text, new_rows)``.
    """
    clean_path = (path or "").strip()
    if not clean_path:
        return "❌ Please provide a LoRA path.", status_to_rows(dit_handler)
    clean_name = (adapter_name or "").strip() or None
    msg = dit_handler.add_lora(clean_path, adapter_name=clean_name)
    return msg, status_to_rows(dit_handler)


def handle_remove_lora(
    selected_idx: int | None,
    dit_handler: Any,
) -> tuple[str, list[list[Any]]]:
    """Remove the adapter referenced by ``selected_idx``.

    Args:
        selected_idx: Row index captured by ``handle_row_select``.
        dit_handler: Active DiT handler instance.

    Returns:
        ``(status_text, new_rows)``.
    """
    rows = status_to_rows(dit_handler)
    if selected_idx is None or selected_idx < 0:
        return _no_selection_message(), rows
    if selected_idx >= len(rows):
        return "⚠️ Invalid selection.", rows
    name = rows[selected_idx][1]
    msg = dit_handler.remove_lora(name)
    return msg, status_to_rows(dit_handler)


def handle_set_active(
    selected_idx: int | None,
    dit_handler: Any,
) -> tuple[str, list[list[Any]]]:
    """Mark the adapter at ``selected_idx`` as active.

    Args:
        selected_idx: Row index captured by ``handle_row_select``.
        dit_handler: Active DiT handler instance.

    Returns:
        ``(status_text, new_rows)``.
    """
    rows = status_to_rows(dit_handler)
    if selected_idx is None or selected_idx < 0:
        return _no_selection_message(), rows
    if selected_idx >= len(rows):
        return "⚠️ Invalid selection.", rows
    name = rows[selected_idx][1]
    msg = dit_handler.set_active_lora_adapter(name)
    return msg, status_to_rows(dit_handler)


def handle_unload_all(dit_handler: Any) -> tuple[str, list[list[Any]]]:
    """Unload every adapter and clear the dataframe.

    Args:
        dit_handler: Active DiT handler instance.

    Returns:
        ``("✅ ...", [])`` when successful, otherwise the error message
        and the current rows.
    """
    msg = dit_handler.unload_lora()
    return msg, status_to_rows(dit_handler)


def _coerce_rows(value: Any) -> list[list[Any]]:
    """Best-effort conversion of a Gradio dataframe payload to list[list]."""
    if value is None:
        return []
    # gr.Dataframe(.change) hands us a pandas DataFrame in some Gradio
    # versions and a plain list of lists in others. Handle both shapes.
    rows_attr = getattr(value, "values", None)
    if rows_attr is not None and hasattr(rows_attr, "tolist"):
        return [list(row) for row in rows_attr.tolist()]
    if isinstance(value, list):
        return [list(row) for row in value]
    return []


def handle_dataframe_edit(
    new_value: Any,
    dit_handler: Any,
) -> tuple[str, list[list[Any]]]:
    """Apply scale edits committed in the dataframe.

    Compares the rows submitted by Gradio against the current handler
    state and calls ``set_lora_scale(name, scale)`` for any row whose
    scale changed. Other columns are read-only by design — edits to
    them are reverted by re-emitting the canonical rows.

    Args:
        new_value: The dataframe value reported by ``.change()``.
        dit_handler: Active DiT handler instance.

    Returns:
        ``(status_text, canonical_rows)``.
    """
    new_rows = _coerce_rows(new_value)
    canonical = status_to_rows(dit_handler)
    if not canonical:
        return "⚠️ No LoRA loaded.", []

    current_scales = {row[1]: row[2] for row in canonical}
    messages: list[str] = []
    for row in new_rows:
        if len(row) < 3:
            continue
        name = str(row[1])
        try:
            new_scale = float(row[2])
        except (TypeError, ValueError):
            continue
        old_scale = current_scales.get(name)
        if old_scale is None:
            continue
        if abs(old_scale - new_scale) > 1e-6:
            messages.append(dit_handler.set_lora_scale(name, new_scale))

    if not messages:
        return "ℹ️ No scale changes applied.", canonical
    return " | ".join(messages), status_to_rows(dit_handler)


def handle_row_select(evt: gr.SelectData) -> int:
    """Capture the clicked row index from a dataframe ``.select()`` event.

    Args:
        evt: Gradio SelectData payload (or anything with an ``index``
            attribute).

    Returns:
        Zero-based row index, or ``-1`` if the click did not target a
        valid row.
    """
    if evt is None:
        return -1
    index = getattr(evt, "index", None)
    if index is None:
        return -1
    if isinstance(index, (list, tuple)):
        if not index:
            return -1
        try:
            return int(index[0])
        except (TypeError, ValueError):
            return -1
    try:
        return int(index)
    except (TypeError, ValueError):
        return -1
