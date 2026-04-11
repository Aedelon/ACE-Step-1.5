"""Unit tests for the multi-LoRA dataframe handlers."""

from __future__ import annotations

import unittest
from typing import Any

from acestep.ui.gradio.events.generation import lora_actions
from acestep.ui.gradio.events.generation.lora_actions import (
    ACTIVE_MARKER,
    INACTIVE_MARKER,
    handle_add_lora,
    handle_clear_active,
    handle_dataframe_edit,
    handle_remove_by_name,
    handle_remove_lora,
    handle_row_select,
    handle_set_active,
    handle_set_active_by_name,
    handle_set_scale_by_name,
    handle_unload_all,
    status_to_rows,
)


class _FakeDitHandler:
    """In-memory stub of the LoRA portion of ``AceStepHandler``."""

    def __init__(self, adapter_type: str = "lora") -> None:
        self.calls: list[tuple[str, tuple, dict]] = []
        self._adapters: dict[str, float] = {}
        self._active: str | None = None
        self._adapter_type: str = adapter_type

    # ---- recording helper ----------------------------------------------
    def _record(self, name: str, *args: Any, **kwargs: Any) -> None:
        self.calls.append((name, args, kwargs))

    # ---- handler API mirrored from AceStepHandler ----------------------
    def get_lora_status(self) -> dict[str, Any]:
        return {
            "loaded": bool(self._adapters),
            "active": True,
            "scale": 1.0,
            "scales": dict(self._adapters),
            "active_adapter": self._active,
            "adapters": list(self._adapters.keys()),
            "adapter_type": self._adapter_type,
        }

    def add_lora(self, path: str, adapter_name: str | None = None) -> str:
        self._record("add_lora", path, adapter_name)
        name = adapter_name or path.rsplit("/", 1)[-1] or "default"
        self._adapters[name] = 1.0
        if self._active is None:
            self._active = name
        return f"✅ LoRA '{name}' loaded"

    def remove_lora(self, adapter_name: str) -> str:
        self._record("remove_lora", adapter_name)
        if adapter_name not in self._adapters:
            return f"❌ Unknown adapter: {adapter_name}"
        del self._adapters[adapter_name]
        if self._active == adapter_name:
            self._active = next(iter(self._adapters), None)
        return f"✅ Removed {adapter_name}"

    def set_active_lora_adapter(self, adapter_name: str) -> str:
        self._record("set_active_lora_adapter", adapter_name)
        if adapter_name not in self._adapters:
            return f"❌ Unknown adapter: {adapter_name}"
        self._active = adapter_name
        return f"✅ Active LoRA adapter: {adapter_name}"

    def clear_active_lora_adapter(self) -> str:
        self._record("clear_active_lora_adapter")
        if self._active is None:
            return "ℹ️ No adapter was active."
        previous = self._active
        self._active = None
        return f"✅ LoRA adapter '{previous}' deactivated."

    def set_lora_scale(self, adapter_name: str, scale: float) -> str:
        self._record("set_lora_scale", adapter_name, scale)
        if adapter_name not in self._adapters:
            return f"❌ Unknown adapter: {adapter_name}"
        self._adapters[adapter_name] = float(scale)
        return f"✅ LoRA scale ({adapter_name}): {scale:.2f}"

    def unload_lora(self) -> str:
        self._record("unload_lora")
        self._adapters.clear()
        self._active = None
        return "✅ LoRA unloaded, using base model"


class StatusToRowsTests(unittest.TestCase):
    def test_returns_empty_when_no_lora_loaded(self) -> None:
        handler = _FakeDitHandler()
        self.assertEqual(status_to_rows(handler), [])

    def test_marks_active_adapter(self) -> None:
        handler = _FakeDitHandler()
        handler.add_lora("/tmp/style_a")
        handler.add_lora("/tmp/style_b")
        rows = status_to_rows(handler)
        self.assertEqual(len(rows), 2)
        markers = {row[1]: row[0] for row in rows}
        self.assertEqual(markers["style_a"], ACTIVE_MARKER)
        self.assertEqual(markers["style_b"], INACTIVE_MARKER)

    def test_row_includes_lora_badge(self) -> None:
        handler = _FakeDitHandler(adapter_type="lora")
        handler.add_lora("/tmp/style_a")
        rows = status_to_rows(handler)
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]), 4)
        self.assertEqual(rows[0][3], "LoRA")

    def test_row_includes_lokr_badge(self) -> None:
        handler = _FakeDitHandler(adapter_type="lokr")
        handler.add_lora("/tmp/voice")
        rows = status_to_rows(handler)
        self.assertEqual(rows[0][3], "LoKr")

    def test_row_defaults_to_lora_badge_when_type_missing(self) -> None:
        handler = _FakeDitHandler(adapter_type="")
        handler.add_lora("/tmp/x")
        rows = status_to_rows(handler)
        self.assertEqual(rows[0][3], "LoRA")

    def test_handles_handler_exception_gracefully(self) -> None:
        class _Broken:
            def get_lora_status(self) -> dict[str, Any]:
                raise RuntimeError("boom")

        self.assertEqual(status_to_rows(_Broken()), [])


class HandleAddLoraTests(unittest.TestCase):
    def test_rejects_empty_path(self) -> None:
        handler = _FakeDitHandler()
        msg, rows = handle_add_lora("   ", "name", handler)
        self.assertIn("provide a LoRA path", msg)
        self.assertEqual(rows, [])
        self.assertEqual(handler.calls, [])

    def test_passes_clean_arguments(self) -> None:
        handler = _FakeDitHandler()
        msg, rows = handle_add_lora("  /tmp/style  ", "  voice  ", handler)
        self.assertEqual(handler.calls, [("add_lora", ("/tmp/style", "voice"), {})])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "voice")
        self.assertTrue(msg.startswith("✅"))

    def test_blank_name_falls_back_to_default(self) -> None:
        handler = _FakeDitHandler()
        handle_add_lora("/tmp/style", "", handler)
        self.assertEqual(handler.calls[0][1], ("/tmp/style", None))


class HandleRemoveAndActiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.handler = _FakeDitHandler()
        self.handler.add_lora("/tmp/a")
        self.handler.add_lora("/tmp/b")
        self.handler.calls.clear()

    def test_remove_no_selection(self) -> None:
        msg, rows = handle_remove_lora(None, self.handler)
        self.assertIn("Select", msg)
        self.assertEqual(len(rows), 2)
        self.assertEqual(self.handler.calls, [])

    def test_remove_invalid_index(self) -> None:
        msg, rows = handle_remove_lora(99, self.handler)
        self.assertIn("Invalid", msg)
        self.assertEqual(len(rows), 2)
        self.assertEqual(self.handler.calls, [])

    def test_remove_by_index(self) -> None:
        msg, rows = handle_remove_lora(1, self.handler)
        self.assertEqual(self.handler.calls, [("remove_lora", ("b",), {})])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "a")
        self.assertTrue(msg.startswith("✅"))

    def test_set_active_by_index(self) -> None:
        msg, rows = handle_set_active(1, self.handler)
        self.assertEqual(self.handler.calls, [("set_active_lora_adapter", ("b",), {})])
        markers = {row[1]: row[0] for row in rows}
        self.assertEqual(markers["b"], ACTIVE_MARKER)
        self.assertEqual(markers["a"], INACTIVE_MARKER)
        self.assertTrue(msg.startswith("✅"))

    def test_clear_active_removes_marker(self) -> None:
        # "a" is active from setUp. Clearing should drop the ⭐ marker
        # from every row while keeping the adapters loaded.
        msg, rows = handle_clear_active(self.handler)
        self.assertEqual(self.handler.calls, [("clear_active_lora_adapter", (), {})])
        self.assertTrue(msg.startswith("✅"))
        # Both rows still present, neither carries the active marker.
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(
                row[0],
                INACTIVE_MARKER,
                f"row {row[1]} still marked active",
            )

    def test_clear_active_when_nothing_active(self) -> None:
        self.handler._active = None
        self.handler.calls.clear()
        msg, rows = handle_clear_active(self.handler)
        self.assertIn("No adapter was active", msg)
        self.assertEqual(self.handler.calls, [("clear_active_lora_adapter", (), {})])
        # Rows still present, still no active markers.
        self.assertEqual(len(rows), 2)

    def test_set_active_by_name_and_remove_by_name(self) -> None:
        """Per-row handlers used by @gr.render should act on name, not idx."""
        msg, rows = handle_set_active_by_name("b", self.handler)
        self.assertEqual(self.handler.calls, [("set_active_lora_adapter", ("b",), {})])
        markers = {row[1]: row[0] for row in rows}
        self.assertEqual(markers["b"], ACTIVE_MARKER)
        self.assertTrue(msg.startswith("✅"))

        self.handler.calls.clear()
        msg, rows = handle_remove_by_name("a", self.handler)
        self.assertEqual(self.handler.calls, [("remove_lora", ("a",), {})])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "b")

    def test_set_scale_by_name_applies_float(self) -> None:
        msg, rows = handle_set_scale_by_name("a", 0.65, self.handler)
        self.assertEqual(self.handler.calls, [("set_lora_scale", ("a", 0.65), {})])
        scales = {row[1]: row[2] for row in rows}
        self.assertAlmostEqual(scales["a"], 0.65)
        self.assertTrue(msg.startswith("✅"))

    def test_set_scale_by_name_rejects_invalid(self) -> None:
        msg, _ = handle_set_scale_by_name("a", "oops", self.handler)
        self.assertEqual(self.handler.calls, [])
        self.assertIn("Invalid", msg)


class HandleUnloadAllTests(unittest.TestCase):
    def test_clears_dataframe(self) -> None:
        handler = _FakeDitHandler()
        handler.add_lora("/tmp/a")
        handler.add_lora("/tmp/b")
        handler.calls.clear()
        msg, rows = handle_unload_all(handler)
        self.assertEqual(rows, [])
        self.assertEqual(handler.calls, [("unload_lora", (), {})])
        self.assertTrue(msg.startswith("✅"))


class HandleDataframeEditTests(unittest.TestCase):
    def test_no_lora_loaded(self) -> None:
        handler = _FakeDitHandler()
        msg, rows = handle_dataframe_edit([], handler)
        self.assertIn("No LoRA loaded", msg)
        self.assertEqual(rows, [])

    def test_applies_changed_scales_only(self) -> None:
        handler = _FakeDitHandler()
        handler.add_lora("/tmp/a")
        handler.add_lora("/tmp/b")
        handler.calls.clear()
        # Edit only the scale of "a" from 1.0 to 0.5; leave "b" at 1.0
        new_value = [
            [ACTIVE_MARKER, "a", 0.5],
            ["", "b", 1.0],
        ]
        msg, rows = handle_dataframe_edit(new_value, handler)
        self.assertEqual(handler.calls, [("set_lora_scale", ("a", 0.5), {})])
        self.assertTrue(msg.startswith("✅"))
        scales = {row[1]: row[2] for row in rows}
        self.assertAlmostEqual(scales["a"], 0.5)
        self.assertAlmostEqual(scales["b"], 1.0)

    def test_no_change_returns_info_message(self) -> None:
        handler = _FakeDitHandler()
        handler.add_lora("/tmp/a")
        handler.calls.clear()
        new_value = [[ACTIVE_MARKER, "a", 1.0]]
        msg, _ = handle_dataframe_edit(new_value, handler)
        self.assertIn("No scale changes applied", msg)
        self.assertEqual(handler.calls, [])

    def test_invalid_scale_is_ignored(self) -> None:
        handler = _FakeDitHandler()
        handler.add_lora("/tmp/a")
        handler.calls.clear()
        new_value = [[ACTIVE_MARKER, "a", "not-a-number"]]
        msg, _ = handle_dataframe_edit(new_value, handler)
        self.assertEqual(handler.calls, [])
        self.assertIn("No scale changes applied", msg)


class HandleRowSelectTests(unittest.TestCase):
    class _Evt:
        def __init__(self, index: Any) -> None:
            self.index = index

    def test_none(self) -> None:
        self.assertEqual(handle_row_select(None), -1)

    def test_scalar_index(self) -> None:
        self.assertEqual(handle_row_select(self._Evt(2)), 2)

    def test_list_index(self) -> None:
        self.assertEqual(handle_row_select(self._Evt([3, 1])), 3)

    def test_invalid_index(self) -> None:
        self.assertEqual(handle_row_select(self._Evt("oops")), -1)
        self.assertEqual(handle_row_select(self._Evt([])), -1)


if __name__ == "__main__":
    unittest.main()
