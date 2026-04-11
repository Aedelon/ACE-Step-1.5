"""
Gradio UI Components Module
Contains all Gradio interface component definitions and layouts

Layout:
  ┌──────────────────────────────────────┐
  │  Header                              │
  ├──────────────────────────────────────┤
  │  Dataset Explorer (hidden accordion) │
  ├──────────────────────────────────────┤
  │  Settings (accordion, collapsed)     │
  │   ├─ Service Configuration           │
  │   ├─ DiT Parameters                  │
  │   ├─ LM Parameters                   │
  │   └─ Output / Automation             │
  ├──────────────────────────────────────┤
  │  ┌─ Generation ─┬─ Training ──────┐  │
  │  │  Mode Radio   │  Dataset/LoRA  │  │
  │  │  Inputs       │                │  │
  │  │  Results      │                │  │
  │  └───────────────┴────────────────┘  │
  └──────────────────────────────────────┘
"""

import gradio as gr
from acestep.ui.gradio.i18n import get_i18n, t
from acestep.ui.gradio.interfaces.dataset import create_dataset_section
from acestep.ui.gradio.interfaces.generation import (
    create_advanced_settings_section,
    create_generation_tab_section,
)
from acestep.ui.gradio.interfaces.audio_player_preferences import (
    get_audio_player_preferences_head,
)
from acestep.ui.gradio.interfaces.user_preferences import (
    get_user_preferences_head,
    wire_preference_restore,
)
from acestep.ui.gradio.interfaces.user_mode import (
    get_user_mode_save_head,
    wire_user_mode,
)
from acestep.ui.gradio.interfaces.result import create_results_section
from acestep.ui.gradio.interfaces.training import create_training_section
from acestep.ui.gradio.events import setup_event_handlers, setup_training_event_handlers
from acestep.ui.gradio.help_content import create_help_button
from acestep.ui.gradio.theme import ACEStepDark
from acestep.ui.gradio.interfaces.tooltip_head import (
    get_tooltip_css,
    get_tooltip_js,
)
from acestep.ui.gradio.interfaces.polish import get_polish_css
from acestep.ui.gradio.interfaces.polish_head import get_polish_head
from acestep.ui.gradio.interfaces.hero import build_hero_section


def get_acestep_head_html(service_mode: bool = False) -> str:
    """Return the full head= HTML to inject when launching Gradio.

    Note: <script> tags inside head= are NOT executed in Gradio 6 because
    they are inserted via innerHTML (HTML5 spec). Use get_acestep_js() for
    JavaScript that must run on page load and get_acestep_css() for styles.

    This helper is kept for the audio_player_preferences and user_preferences
    scripts which use a different injection mechanism (DOM script tag at
    page load via Gradio's loader).

    Args:
        service_mode: When True, the user preferences script is omitted.

    Returns:
        HTML string ready for ``launch(head=...)``.
    """
    return (
        get_polish_head()
        + get_audio_player_preferences_head()
        + (
            ""
            if service_mode
            else (get_user_preferences_head() + get_user_mode_save_head())
        )
    )


def get_acestep_css() -> str:
    """Return CSS to pass to ``launch(css=...)`` in Gradio 6.

    Concatenates the tooltip system CSS (bubble + modal + per-LoRA
    rows) with the Phase D polish stylesheet (typography hierarchy,
    accordion gradients, button states, slider thumbs, focus rings,
    custom scrollbars, responsive spacing).
    """
    return get_tooltip_css() + "\n" + get_polish_css()


def get_acestep_js(language: str = "en") -> str:
    """Return JavaScript function string for ``launch(js=...)`` in Gradio 6.

    The js= parameter expects a JS function expression (e.g. ``() => {...}``)
    that runs once on page load. We use it to install the tooltip system,
    which cannot be done via head= because <script> tags inserted via
    innerHTML do not execute (HTML5 spec). The active language is forwarded
    so the tooltip system can recover original markdown sources.
    """
    return get_tooltip_js(language)


def create_gradio_interface(
    dit_handler, llm_handler, dataset_handler, init_params=None, language="en"
) -> gr.Blocks:
    """
    Create Gradio interface

    Args:
        dit_handler: DiT handler instance
        llm_handler: LM handler instance
        dataset_handler: Dataset handler instance
        init_params: Dictionary containing initialization parameters and state.
                    If None, service will not be pre-initialized.
        language: UI language code ('en', 'zh', 'ja', default: 'en')

    Returns:
        Gradio Blocks instance
    """
    # Update i18n with selected language
    i18n = get_i18n(language)

    # Check if running in service mode (hide training tab)
    service_mode = init_params is not None and init_params.get("service_mode", False)

    # NOTE on Gradio 6: ``head=``, ``css=``, ``js=`` and ``theme=``
    # passed to ``gr.Blocks(...)`` are DEPRECATED and OVERRIDDEN by
    # whatever is passed to ``demo.launch(head=…, css=…, js=…)``
    # at runtime (verified in gradio/blocks.py:2566). The real
    # injection path is ``acestep_v15_pipeline.py`` which calls
    # ``launch(head=get_acestep_head_html(...), css=get_acestep_css())``.
    # We keep ``theme=`` here only so that smoke tests / standalone
    # calls to ``create_gradio_interface`` still get a dark surface
    # for visual debugging.
    with gr.Blocks(
        title=t("app.title"),
        theme=ACEStepDark(),
    ) as demo:
        # Hero section: rich app header with eyebrow + title + subtitle
        # + status pills (model state, language, beginner/expert mode).
        # Replaces the previous bare <div class="main-header"><h1>…</h1>
        # which was hard to style and gave no at-a-glance state info.
        hero_section = build_hero_section(
            initialized=bool(init_params and init_params.get("pre_initialized")),
            model_name=(init_params or {}).get("config_path"),
            language_code=language,
            user_mode="beginner",
        )
        create_help_button("getting_started")

        # Dataset Explorer Section (hidden)
        dataset_section = create_dataset_section(dataset_handler)

        # ═══════════════════════════════════════════
        # Top-level: Settings (contains Service Config + Advanced Settings)
        # ═══════════════════════════════════════════
        settings_section = create_advanced_settings_section(
            dit_handler, llm_handler, init_params=init_params, language=language
        )

        # ═══════════════════════════════════════════
        # Tabs: Generation | Training
        # ═══════════════════════════════════════════
        with gr.Tabs():
            # --- Generation Tab ---
            with gr.Tab(t("generation.tab_title")):
                gen_section = create_generation_tab_section(
                    dit_handler, llm_handler, init_params=init_params, language=language
                )

                # Results Section (inside the Generation tab, wrapped for visibility control)
                with gr.Column(visible=True) as results_wrapper:
                    results_section = create_results_section(dit_handler)
                # Store the wrapper in gen_section so event handlers can toggle it
                gen_section["results_wrapper"] = results_wrapper

            # --- Training Tab ---
            with gr.Tab(t("training.tab_title"), visible=not service_mode):
                training_section = create_training_section(
                    dit_handler, llm_handler, init_params=init_params
                )

        # ═══════════════════════════════════════════
        # Merge all generation-related component dicts for event wiring
        # ═══════════════════════════════════════════
        # The event handlers expect a single "generation_section" dict with all
        # components from settings (service config + advanced) and generation tab.
        # The hero section is also merged in so handlers can push fresh HTML into
        # ``hero_html`` after init / mode toggle (status pills stay in sync).
        generation_section = {}
        generation_section.update(hero_section)
        generation_section.update(settings_section)
        generation_section.update(gen_section)
        # Stash the active language so hero refresh handlers can re-render
        # the language pill with the correct code without reading i18n state.
        generation_section["_ui_language"] = language
        # Stash the DiT handler too so the user_mode refresh handler can
        # read ``dit_handler.model`` at runtime to decide whether the
        # status pill should stay amber or flip green. Using an underscore
        # prefix keeps it out of the way of any loop that treats the dict
        # as a component collection.
        generation_section["_dit_handler_ref"] = dit_handler

        # Connect event handlers
        setup_event_handlers(
            demo,
            dit_handler,
            llm_handler,
            dataset_handler,
            dataset_section,
            generation_section,
            results_section,
        )

        # Connect training event handlers
        setup_training_event_handlers(demo, dit_handler, llm_handler, training_section)

        # Restore user preferences from browser localStorage on page load.
        # In service mode, skip restore so localStorage cannot override
        # server-configured init_params or locked controls.
        wire_preference_restore(demo, generation_section, service_mode=service_mode)

        # Beginner / Expert mode toggle — hides advanced accordions and
        # sliders when Beginner is selected, reveals them for Expert.
        # Persists via its own localStorage key.
        wire_user_mode(demo, generation_section, service_mode=service_mode)

    return demo
