"""Unit tests for the Beginner / Expert user mode helpers."""

from __future__ import annotations

import unittest
from typing import Any

from acestep.ui.gradio.interfaces.user_mode import (
    USER_MODE_DEFAULT,
    apply_user_mode,
    collect_mode_driven_outputs,
)


class _DummyComponent:
    """Sentinel object that stands in for a Gradio component handle."""

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<DummyComponent {self.name}>"


class ApplyUserModeTests(unittest.TestCase):
    def test_returns_one_update_per_expert_only_key(self) -> None:
        # Five entries: dit_accordion, lm_accordion, automation_accordion,
        # latent_shift, latent_rescale.
        beginner = apply_user_mode("beginner")
        expert = apply_user_mode("expert")
        self.assertEqual(len(beginner), 5)
        self.assertEqual(len(expert), 5)

    def test_beginner_hides_everything(self) -> None:
        updates = apply_user_mode("beginner")
        for update in updates:
            self.assertFalse(_visibility(update))

    def test_expert_shows_everything(self) -> None:
        updates = apply_user_mode("expert")
        for update in updates:
            self.assertTrue(_visibility(update))

    def test_unknown_mode_falls_back_to_default(self) -> None:
        updates = apply_user_mode("garbage")
        # Default is beginner → all hidden.
        for update in updates:
            self.assertFalse(_visibility(update))

    def test_default_constant_is_beginner(self) -> None:
        self.assertEqual(USER_MODE_DEFAULT, "beginner")


class CollectModeDrivenOutputsTests(unittest.TestCase):
    def test_returns_only_keys_present_in_section(self) -> None:
        section: dict[str, Any] = {
            "dit_accordion": _DummyComponent("dit"),
            "automation_accordion": _DummyComponent("auto"),
            "latent_rescale": _DummyComponent("rescale"),
            # lm_accordion + latent_shift intentionally missing
            "unrelated_other_key": _DummyComponent("other"),
        }
        outputs = collect_mode_driven_outputs(section)
        # 3 of the 5 expert-only keys are present.
        self.assertEqual(len(outputs), 3)
        names = {component.name for component in outputs}
        self.assertEqual(names, {"dit", "auto", "rescale"})

    def test_empty_section_returns_empty_list(self) -> None:
        self.assertEqual(collect_mode_driven_outputs({}), [])


def _visibility(update: Any) -> bool:
    """Read the ``visible`` flag from a Gradio update payload.

    ``gr.update(visible=...)`` returns a dict in normal usage; we use
    ``.get("visible")`` to stay compatible across Gradio versions that
    sometimes return a custom object.
    """
    if isinstance(update, dict):
        return bool(update.get("visible"))
    visible = getattr(update, "visible", None)
    return bool(visible)


if __name__ == "__main__":
    unittest.main()
