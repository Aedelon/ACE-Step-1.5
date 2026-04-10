"""Primary advanced-settings controls for generation UI."""

from typing import Any

import gradio as gr

from acestep.ui.gradio.i18n import t


def build_lora_controls() -> dict[str, Any]:
    """Create the multi-LoRA adapter management UI.

    The "loaded adapters" area is a dynamic ``@gr.render`` block driven
    by a hidden ``gr.State`` holding ``list[[marker, name, scale]]``
    rows. Each row gets its own Slider + Activate/Deactivate + Remove
    controls — no dataframe, because ``gr.Dataframe`` cannot embed
    interactive sliders per cell.

    The bulk actions area (``lora_set_active_btn`` / ``lora_remove_btn``
    etc.) is kept around for API compatibility with existing wiring
    contracts, but the buttons are hidden — per-row controls replace
    them. ``lora_selected_idx`` is similarly kept as a no-op state for
    the same reason.
    """

    with gr.Accordion(
        t("generation.lora_accordion_title"), open=False, elem_classes=["acestep-tt"]
    ):
        gr.Markdown(
            t("generation.lora_lokr_warning"),
            elem_classes=["no-tooltip"],
        )

        # --- Section 1: Add adapter form -------------------------------
        gr.Markdown(
            "### " + t("generation.lora_section_add"),
            elem_classes=["no-tooltip"],
        )
        with gr.Row():
            lora_path = gr.Textbox(
                label=t("generation.lora_path_label"),
                placeholder=t("generation.lora_path_placeholder"),
                info=t("generation.lora_path_info"),
                scale=3,
                elem_classes=["acestep-tt"],
            )
            lora_browse_btn = gr.Button(
                t("generation.lora_browse_btn"),
                variant="secondary",
                scale=0,
                min_width=140,
            )
        with gr.Row():
            lora_adapter_name = gr.Textbox(
                label=t("generation.lora_adapter_name_label"),
                placeholder=t("generation.lora_adapter_name_placeholder"),
                info=t("generation.lora_adapter_name_info"),
                scale=3,
                elem_classes=["acestep-tt"],
            )
            load_lora_btn = gr.Button(
                t("generation.add_lora_btn"),
                variant="primary",
                scale=0,
                min_width=140,
            )

        # --- Section 2: Dynamic per-adapter rows -----------------------
        gr.Markdown(
            "### " + t("generation.lora_section_loaded"),
            elem_classes=["no-tooltip"],
        )

        # Shared state: list of [marker, name, scale] rows. Every
        # add/remove/set-active/scale handler reads + writes this state,
        # and @gr.render below listens to it to redraw the per-row UI.
        lora_state = gr.State(value=[])

        # The @gr.render block is wired by the service wiring layer (it
        # needs access to dit_handler which lives there). We expose the
        # state here and the wiring layer attaches the render decorator.
        # For now we create a placeholder container; the wiring layer
        # will populate it via a deferred @gr.render call.
        lora_rows_container = gr.Column(elem_classes=["acestep-lora-rows"])

        with gr.Row():
            unload_lora_btn = gr.Button(
                t("generation.lora_unload_all_btn"),
                variant="secondary",
                scale=1,
            )
            use_lora_checkbox = gr.Checkbox(
                label=t("generation.use_lora_label"),
                value=False,
                info=t("generation.use_lora_info"),
                scale=2,
                elem_classes=["acestep-tt"],
            )

        lora_status = gr.Textbox(
            label=t("generation.lora_status_label"),
            value=t("generation.lora_status_default"),
            interactive=False,
            lines=1,
            elem_classes=["no-tooltip"],
        )

        # --- Legacy bulk-action buttons (hidden, kept for contract) ----
        # The wiring layer still references these keys in older code
        # paths; we render them invisibly so the contract tests stay
        # green without asking every caller to stop using them.
        lora_set_active_btn = gr.Button("set_active", visible=False)
        lora_clear_active_btn = gr.Button("clear_active", visible=False)
        lora_remove_btn = gr.Button("remove", visible=False)
        lora_selected_idx = gr.State(value=-1)

    return {
        "lora_path": lora_path,
        "lora_adapter_name": lora_adapter_name,
        "lora_browse_btn": lora_browse_btn,
        "load_lora_btn": load_lora_btn,
        "unload_lora_btn": unload_lora_btn,
        "lora_state": lora_state,
        "lora_rows_container": lora_rows_container,
        "lora_set_active_btn": lora_set_active_btn,
        "lora_clear_active_btn": lora_clear_active_btn,
        "lora_remove_btn": lora_remove_btn,
        "lora_selected_idx": lora_selected_idx,
        "use_lora_checkbox": use_lora_checkbox,
        "lora_status": lora_status,
    }


def build_lm_controls(service_mode: bool) -> dict[str, Any]:
    """Create language-model generation controls for advanced settings.

    Args:
        service_mode: Whether the UI is running in service mode (disables some controls).

    Returns:
        A component map containing LM sampling, CoT, negative prompt, and batch controls.
    """

    with gr.Accordion(
        t("generation.advanced_lm_section"), open=False, elem_classes=["acestep-tt"]
    ):
        with gr.Row():
            lm_temperature = gr.Slider(
                label=t("generation.lm_temperature_label"),
                minimum=0.0,
                maximum=2.0,
                value=0.85,
                step=0.1,
                scale=1,
                info=t("generation.lm_temperature_info"),
                elem_classes=["acestep-tt"],
            )
            lm_cfg_scale = gr.Slider(
                label=t("generation.lm_cfg_scale_label"),
                minimum=1.0,
                maximum=3.0,
                value=2.0,
                step=0.1,
                scale=1,
                info=t("generation.lm_cfg_scale_info"),
                elem_classes=["acestep-tt"],
            )
        with gr.Row():
            lm_top_k = gr.Slider(
                label=t("generation.lm_top_k_label"),
                minimum=0,
                maximum=100,
                value=0,
                step=1,
                scale=1,
                info=t("generation.lm_top_k_info"),
                elem_classes=["acestep-tt"],
            )
            lm_top_p = gr.Slider(
                label=t("generation.lm_top_p_label"),
                minimum=0.0,
                maximum=1.0,
                value=0.9,
                step=0.01,
                scale=1,
                info=t("generation.lm_top_p_info"),
                elem_classes=["acestep-tt"],
            )
        with gr.Row():
            lm_negative_prompt = gr.Textbox(
                label=t("generation.lm_negative_prompt_label"),
                value="NO USER INPUT",
                placeholder=t("generation.lm_negative_prompt_placeholder"),
                info=t("generation.lm_negative_prompt_info"),
                elem_classes=["acestep-tt"],
                lines=2,
            )
        with gr.Row():
            use_cot_metas = gr.Checkbox(
                label=t("generation.cot_metas_label"),
                value=True,
                info=t("generation.cot_metas_info"),
                scale=1,
                elem_classes=["acestep-tt"],
            )
            use_cot_language = gr.Checkbox(
                label=t("generation.cot_language_label"),
                value=True,
                info=t("generation.cot_language_info"),
                scale=1,
                elem_classes=["acestep-tt"],
            )
            constrained_decoding_debug = gr.Checkbox(
                label=t("generation.constrained_debug_label"),
                value=False,
                info=t("generation.constrained_debug_info"),
                scale=1,
                interactive=not service_mode,
                elem_classes=["acestep-tt"],
            )
        with gr.Row():
            allow_lm_batch = gr.Checkbox(
                label=t("generation.parallel_thinking_label"),
                value=True,
                info=t("generation.parallel_thinking_info"),
                scale=1,
                elem_classes=["acestep-tt"],
            )
            use_cot_caption = gr.Checkbox(
                label=t("generation.caption_rewrite_label"),
                value=False,
                info=t("generation.caption_rewrite_info"),
                scale=1,
                elem_classes=["acestep-tt"],
            )

    return {
        "lm_temperature": lm_temperature,
        "lm_cfg_scale": lm_cfg_scale,
        "lm_top_k": lm_top_k,
        "lm_top_p": lm_top_p,
        "lm_negative_prompt": lm_negative_prompt,
        "use_cot_metas": use_cot_metas,
        "use_cot_language": use_cot_language,
        "constrained_decoding_debug": constrained_decoding_debug,
        "allow_lm_batch": allow_lm_batch,
        "use_cot_caption": use_cot_caption,
    }
