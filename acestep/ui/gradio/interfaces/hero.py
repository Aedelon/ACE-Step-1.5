"""Hero section for the ACE-Step Gradio UI.

Replaces the previous ``<div class="main-header">`` with a richer
``<section id="acestep-hero">`` block that exposes:

- Eyebrow tag (uppercase, micro typography)
- Solid app title (no marketing gradient — Linear/Vercel/Arc style)
- Subtitle line
- Three status pills: model, language, beginner/expert mode
  (rendered with a colored dot + label, colors driven by current state)

The pills give users a persistent at-a-glance view of:
1. Whether the service is initialized (orange dot = "needs init",
   green dot = "ready")
2. The current UI language code
3. Their selected user mode

Updates flow through ``render_hero_html()``: handlers like
``init_btn.click`` and ``user_mode_radio.change`` push a fresh HTML
string into the ``hero_html`` component, mirroring the same
data-shape that ``status_to_rows`` already uses for the LoRA list.
"""

from __future__ import annotations

import os
from html import escape
from typing import Any

import gradio as gr

from acestep.ui.gradio.i18n import t


def derive_config_display_name(config_value: Any) -> str | None:
    """Turn a raw config path into a human-readable pill label.

    Strips the directory and ``.json`` suffix so the hero pill says
    ``config_1_5_xl_turbo`` rather than the full filesystem path.
    Returns ``None`` when no config was supplied (so callers can fall
    back to the hero's "Model not loaded" default).

    Centralised here (instead of duplicated in the service wiring and
    user_mode modules) so a future rename of the config convention
    only needs one edit.
    """
    if not config_value:
        return None
    base = os.path.basename(str(config_value))
    if base.endswith(".json"):
        base = base[: -len(".json")]
    return base or None


HERO_ELEM_ID = "acestep-hero"


def render_hero_html(
    *,
    title: str,
    subtitle: str,
    eyebrow: str = "ACE-STEP · MUSIC GENERATION",
    model_name: str | None = None,
    model_loaded: bool = False,
    language_code: str = "EN",
    user_mode: str = "beginner",
) -> str:
    """Build the hero ``<section>`` HTML string.

    Args:
        title: Main headline shown after the eyebrow.
        subtitle: Description line below the title.
        eyebrow: Small uppercase tag rendered above the title.
        model_name: Display name of the currently loaded model
            (e.g. ``"ACE-Step v1.5 XL Turbo"``). Falls back to
            "Model not loaded" when ``None``.
        model_loaded: When True, the model status pill turns
            emerald. When False, it stays amber to nudge the user
            toward initialization.
        language_code: 2-letter UI language code shown in the
            language pill. Always uppercase.
        user_mode: Either ``"beginner"`` or ``"expert"`` — drives
            the third pill's label and dot color.

    Returns:
        Sanitised HTML string ready to be passed to ``gr.HTML``.
    """
    safe_title = escape(title)
    safe_subtitle = escape(subtitle)
    safe_eyebrow = escape(eyebrow)
    safe_lang = escape(language_code.upper())
    safe_model = escape(model_name or "Model not loaded")

    model_dot_class = "ace-dot--green" if model_loaded else "ace-dot--amber"
    model_pill_class = "ace-status-pill--model"
    if not model_loaded:
        model_pill_class += " ace-status-pill--needs-init"

    mode_label = "Expert" if user_mode == "expert" else "Beginner"
    mode_dot_class = "ace-dot--blue" if user_mode == "expert" else "ace-dot--green"

    # IMPORTANT: do NOT put id="acestep-hero" on the inner <section>.
    # Gradio's gr.HTML(elem_id="acestep-hero") wraps our value in a
    # <div id="acestep-hero"> already (verified against Index-*.js
    # source: ``a.set_attribute(l, "id", s.shared.elem_id)``). Adding
    # the same id here would create a duplicate-id HTML invariant
    # violation and break querySelector / accessibility tools.
    return f"""
<section class="ace-hero">
  <div class="ace-hero-eyebrow">{safe_eyebrow}</div>
  <h1 class="ace-hero-title">{safe_title}</h1>
  <p class="ace-hero-subtitle">{safe_subtitle}</p>
  <div class="ace-hero-status">
    <span class="ace-status-pill {model_pill_class}">
      <span class="ace-dot {model_dot_class}"></span>{safe_model}
    </span>
    <span class="ace-status-pill ace-status-pill--lang">
      <span class="ace-dot ace-dot--amber"></span>{safe_lang}
    </span>
    <span class="ace-status-pill ace-status-pill--mode">
      <span class="ace-dot {mode_dot_class}"></span>{mode_label}
    </span>
  </div>
</section>
""".strip()


def _resolve_hero_strings() -> tuple[str, str]:
    """Return ``(title, subtitle)`` used across every hero rebuild.

    Uses two dedicated i18n keys — ``app.hero_title`` and
    ``app.hero_subtitle`` — that carry the localised hero text. The
    previous implementation tried to derive the title from
    ``app.title`` by lstrip-ping the ``🎛️`` emoji and overwriting
    with hardcoded English whenever the remainder started with
    ``"ACE"``, which produced an English-only hero on all locales
    (the stripped text always started with "ACE" because the shared
    ``app.title`` was "🎛️ ACE-Step V1.5 Playground💡").

    Fallbacks below only trigger when an i18n file is missing the
    key entirely (which the unit tests cover).
    """
    title = t("app.hero_title") or "Generate music from text and lyrics."
    subtitle = t("app.hero_subtitle") or (
        "Powered by ACE-Step v1.5 — open-source latent diffusion music model."
    )
    return title, subtitle


def rebuild_hero_html(
    *,
    initialized: bool,
    model_name: str | None,
    language_code: str,
    user_mode: str,
) -> str:
    """Produce a fresh ``<section>`` string to push into the hero HTML.

    Used by event handlers (``init_btn.click`` / ``user_mode_radio.change``)
    to refresh the status pills after the underlying state changes. The
    title/subtitle are pulled from i18n so the pills update without a
    full page reload.
    """
    title, subtitle = _resolve_hero_strings()
    return render_hero_html(
        title=title,
        subtitle=subtitle,
        model_name=model_name,
        model_loaded=initialized,
        language_code=language_code,
        user_mode=user_mode,
    )


def build_hero_section(
    *,
    initialized: bool = False,
    model_name: str | None = None,
    language_code: str = "en",
    user_mode: str = "beginner",
) -> dict[str, Any]:
    """Create the ``hero_html`` component map.

    The hero is a single ``gr.HTML`` whose value is rebuilt by every
    handler that touches the underlying state (init service, change
    language, switch user mode).
    """
    hero_html = gr.HTML(
        value=rebuild_hero_html(
            initialized=initialized,
            model_name=model_name,
            language_code=language_code,
            user_mode=user_mode,
        ),
        elem_id=HERO_ELEM_ID,
    )
    return {"hero_html": hero_html}
