"""Beginner / Expert mode toggle for the generation UI.

Hides the advanced accordions and individual expert sliders when the
user selects **Beginner** mode so newcomers aren't overwhelmed, and
reveals them when they flip to **Expert**. The choice persists via
browser localStorage so it survives reloads and language switches.

Hidden in Beginner mode:
    - DiT Diffusion accordion (inference steps, guidance scale, shift,
      samplers, velocity tricks, custom timesteps, CFG interval…)
    - LM Generation accordion (temperature, top-k/p, CFG scale, CoT
      debug, parallel thinking, caption rewrite…)
    - Automation & Batch accordion (auto score, auto LRC, batch chunk,
      code strength, score sensitivity…)
    - Inside the Output accordion: latent_shift + latent_rescale
      (advanced post-processing, not normalization / fade / format)

The LoRA Adapter accordion and the Output accordion shell stay visible
in both modes — users still need normalization, fade, format, LoRA
loading even as beginners.
"""

from __future__ import annotations

import json
from typing import Any

import gradio as gr

from acestep.ui.gradio.i18n import t


USER_MODE_DEFAULT = "beginner"
USER_MODE_STORAGE_KEY = "acestep.ui.user_mode"
USER_MODE_ELEM_ID = "acestep-user-mode"

# Component keys (from generation_section) whose visibility is driven by
# the mode. Includes both Accordion handles and individual sliders that
# live inside an accordion we want to keep visible.
_EXPERT_ONLY_KEYS: tuple[str, ...] = (
    "dit_accordion",
    "lm_accordion",
    "automation_accordion",
    "latent_shift",
    "latent_rescale",
)


def build_user_mode_selector(default: str = USER_MODE_DEFAULT) -> dict[str, Any]:
    """Create the Beginner / Expert radio selector.

    Args:
        default: Initial mode value. Falls back to ``beginner`` if the
            caller passes anything else.

    Returns:
        Component map keyed by ``user_mode_radio``.
    """
    initial = default if default in ("beginner", "expert") else USER_MODE_DEFAULT
    user_mode_radio = gr.Radio(
        choices=[
            (t("generation.user_mode_beginner"), "beginner"),
            (t("generation.user_mode_expert"), "expert"),
        ],
        value=initial,
        label=t("generation.user_mode_label"),
        info=t("generation.user_mode_info"),
        elem_id=USER_MODE_ELEM_ID,
        elem_classes=["acestep-tt", "acestep-user-mode"],
        interactive=True,
    )
    return {"user_mode_radio": user_mode_radio}


def apply_user_mode(mode: str) -> tuple[Any, ...]:
    """Return ``gr.update`` payloads toggling every expert-only control.

    The tuple's order matches ``_EXPERT_ONLY_KEYS`` and the outputs list
    wired to the radio ``.change()`` handler.
    """
    is_expert = (mode or USER_MODE_DEFAULT) == "expert"
    return tuple(gr.update(visible=is_expert) for _ in _EXPERT_ONLY_KEYS)


def collect_mode_driven_outputs(generation_section: dict[str, Any]) -> list[Any]:
    """Collect the component handles affected by ``apply_user_mode``.

    Entries whose key is missing from ``generation_section`` are silently
    skipped so the wiring stays robust to partial builds (e.g. unit
    tests using mock handlers).
    """
    outputs: list[Any] = []
    for key in _EXPERT_ONLY_KEYS:
        component = generation_section.get(key)
        if component is not None:
            outputs.append(component)
    return outputs


def _save_js() -> str:
    """Return an IIFE that observes the radio and writes its value to
    localStorage on change."""
    return (
        "(() => { try { "
        "const key = " + json.dumps(USER_MODE_STORAGE_KEY) + "; "
        "const elemId = " + json.dumps(USER_MODE_ELEM_ID) + "; "
        "const wired = new WeakSet(); "
        "const wire = () => { "
        "  const wrapper = document.getElementById(elemId); "
        "  if (!wrapper) return; "
        "  wrapper.querySelectorAll('input[type=\"radio\"]').forEach(inp => { "
        "    if (wired.has(inp)) return; "
        "    wired.add(inp); "
        "    inp.addEventListener('change', () => { "
        "      try { if (inp.checked) window.localStorage.setItem(key, inp.value); } "
        "      catch (_e) {} "
        "    }, { passive: true }); "
        "  }); "
        "}; "
        "const boot = () => { "
        "  wire(); "
        "  const target = document.querySelector('.gradio-container') || document.body; "
        "  new MutationObserver(() => wire()).observe(target, {childList:true, subtree:true}); "
        "}; "
        "if (document.readyState === 'loading') "
        "  document.addEventListener('DOMContentLoaded', boot, {once:true}); "
        "else boot(); "
        "} catch (_e) {} })();"
    )


def _restore_js() -> str:
    """Return a JS function (not IIFE) used by ``demo.load()`` to read
    the persisted mode from localStorage and feed it back to Gradio."""
    return (
        "() => { "
        "try { "
        "  const v = window.localStorage.getItem("
        + json.dumps(USER_MODE_STORAGE_KEY)
        + "); "
        "  return v === 'expert' ? 'expert' : 'beginner'; "
        "} catch (_e) { return 'beginner'; } "
        "}"
    )


def wire_user_mode(
    demo: Any,
    generation_section: dict[str, Any],
    *,
    service_mode: bool = False,
) -> None:
    """Attach the mode radio to its visibility and persistence handlers.

    Must be called **inside** the ``with gr.Blocks() as demo:`` context.

    - ``.change()`` on the radio updates every expert-only component.
    - ``demo.load()`` reads localStorage on page load, sets the radio
      value, and propagates the initial visibility so the UI matches
      the persisted mode without waiting for a manual click.
    - Save side: a small JS block appended to the head writes the
      current selection back to localStorage whenever the user clicks.

    In service mode the wiring is a no-op: hosted deployments typically
    run with a locked, pre-configured UI and should not let a browser
    preference mutate the visible control set.
    """
    if service_mode:
        return

    radio = generation_section.get("user_mode_radio")
    if radio is None:
        return

    outputs = collect_mode_driven_outputs(generation_section)
    if not outputs:
        return

    radio.change(
        fn=apply_user_mode,
        inputs=[radio],
        outputs=outputs,
    )

    # On page load: read localStorage → feed value into the radio AND
    # propagate visibility updates for the expert-only components. The
    # restore JS returns only the persisted mode string; the Python fn
    # expands it into the full outputs tuple.
    def _restore_on_load(mode: str) -> tuple[Any, ...]:
        safe = mode if mode in ("beginner", "expert") else USER_MODE_DEFAULT
        radio_update = gr.update(value=safe)
        visibility_updates = apply_user_mode(safe)
        return (radio_update, *visibility_updates)

    demo.load(
        fn=_restore_on_load,
        inputs=[radio],
        outputs=[radio, *outputs],
        js=_restore_js(),
    )


def get_user_mode_save_head() -> str:
    """Return the ``<script>`` block injected via ``Blocks(head=…)``."""
    return f"<script>{_save_js()}</script>"
