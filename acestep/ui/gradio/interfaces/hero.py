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

from html import escape
from typing import Any

import gradio as gr

from acestep.ui.gradio.i18n import t


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
    title = t("app.title").lstrip("🎛️").strip() or "Generate music from text and lyrics."
    if title.startswith("ACE"):
        title = "Generate music from text and lyrics."
    subtitle = t("app.subtitle") or (
        "Powered by ACE-Step v1.5 — open-source latent diffusion music model."
    )

    hero_html = gr.HTML(
        value=render_hero_html(
            title=title,
            subtitle=subtitle,
            model_name=model_name,
            model_loaded=initialized,
            language_code=language_code,
            user_mode=user_mode,
        ),
        elem_id=HERO_ELEM_ID,
    )
    return {"hero_html": hero_html}
