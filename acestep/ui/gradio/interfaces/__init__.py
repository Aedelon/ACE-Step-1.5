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
from acestep.ui.gradio.help_content import create_help_button, HELP_MODAL_CSS
from acestep.ui.gradio.theme import ACEStepDark
from acestep.ui.gradio.interfaces.tooltip_head import (
    get_tooltip_css,
    get_tooltip_head,
    get_tooltip_js,
)


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
    return get_audio_player_preferences_head() + (
        ""
        if service_mode
        else (get_user_preferences_head() + get_user_mode_save_head())
    )


def get_acestep_css() -> str:
    """Return CSS to pass to ``launch(css=...)`` in Gradio 6.

    Includes the tooltip system CSS. Combined with the existing inline CSS
    on gr.Blocks() (legacy path).
    """
    return get_tooltip_css()


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

    with gr.Blocks(
        title=t("app.title"),
        theme=ACEStepDark(),
        head=get_audio_player_preferences_head()
        + ("" if service_mode else get_user_preferences_head())
        + get_tooltip_head(),
        css="""
        .main-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        /* Status bars - prominent and readable */
        #acestep-status-output,
        #acestep-init-status {
            min-height: 100px !important;
        }
        #acestep-status-output textarea,
        #acestep-init-status textarea {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            text-align: center !important;
            padding: 16px !important;
            letter-spacing: 0.02em !important;
            min-height: 80px !important;
        }
        .section-header {
            background: var(--block-label-background-fill);
            color: var(--body-text-color);
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .lm-hints-row {
            align-items: stretch;
        }
        .lm-hints-col {
            display: flex;
        }
        .lm-hints-col > div {
            flex: 1;
            display: flex;
        }
        .lm-hints-btn button {
            height: 100%;
            width: 100%;
        }
        /* Position Audio time labels lower to avoid scrollbar overlap */
        .component-wrapper > .timestamps {
            transform: translateY(15px);
        }
        /* Equal-height row for instrumental checkbox + enhance lyrics button */
        .instrumental-row {
            align-items: stretch !important;
        }
        .instrumental-row > div {
            display: flex !important;
            align-items: stretch !important;
        }
        .instrumental-row > div > div {
            flex: 1;
            display: flex;
            align-items: center;
        }
        .instrumental-row button {
            height: 100% !important;
            min-height: 42px;
        }
        /* Ensure buttons in instrumental-row fill height */
        .instrumental-row > div > button {
            height: 100% !important;
            min-height: 42px;
        }
        /* Two-line icon buttons: emoji on top, text below */
        .icon-btn-wrap button, .icon-btn-wrap > button {
            word-spacing: 100vw;
            text-align: center;
            line-height: 1.4;
        }

        /* Custom tooltip system removed — was breaking Gradio 6 component
           rendering inside accordions. Gradio's native info= display is used. */

        /* --- Auto-toggle checkbox row --- */
        /* Compact row of Auto checkboxes that mirrors the field row above */
        .auto-toggles-row {
            margin-top: -8px !important;
            margin-bottom: 0 !important;
            padding: 0 !important;
            gap: 16px !important;
            min-height: 0 !important;
        }
        .auto-toggle {
            text-align: center !important;
        }
        .auto-toggle label {
            font-size: 0.8rem !important;
            gap: 4px !important;
            white-space: nowrap !important;
            cursor: pointer !important;
            opacity: 0.5;
            transition: opacity 0.15s;
            justify-content: center !important;
        }
        .auto-toggle:hover label {
            opacity: 1;
        }
        .auto-toggle input[type="checkbox"] {
            width: 13px !important;
            height: 13px !important;
        }
        """
        + HELP_MODAL_CSS,
    ) as demo:
        gr.HTML(f"""
        <div class="main-header">
            <h1>{t("app.title")}</h1>
            <p>{t("app.subtitle")}</p>
        </div>
        """)
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
        generation_section = {}
        generation_section.update(settings_section)
        generation_section.update(gen_section)

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
