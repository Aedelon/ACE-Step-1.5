"""Generation service-layer event wiring helpers.

This module contains wiring related to service initialization, LoRA controls,
auto-checkbox controls, and visibility updates for generation components.
"""

from typing import Any

import gradio as gr

from .. import generation_handlers as gen_h
from ...i18n import (
    get_i18n,
    reset_language_context,
    save_language,
    set_language_context,
)
from .context import (
    GenerationWiringContext,
    build_auto_checkbox_inputs,
    build_auto_checkbox_outputs,
)


def register_generation_service_handlers(
    context: GenerationWiringContext,
) -> tuple[list[Any], list[Any]]:
    """Register generation service/init handlers and return auto-checkbox lists."""

    dataset_section = context.dataset_section
    generation_section = context.generation_section
    results_section = context.results_section
    dit_handler = context.dit_handler
    llm_handler = context.llm_handler
    dataset_handler = context.dataset_handler

    # ========== Dataset Handlers ==========
    dataset_section["import_dataset_btn"].click(
        fn=dataset_handler.import_dataset,
        inputs=[dataset_section["dataset_type"]],
        outputs=[dataset_section["data_status"]],
    )

    # ========== Service Initialization ==========
    generation_section["refresh_btn"].click(
        fn=lambda: gen_h.refresh_checkpoints(dit_handler),
        outputs=[generation_section["checkpoint_dropdown"]],
    )

    generation_section["language_dropdown"].change(
        fn=lambda language: _apply_runtime_language(language),
        inputs=[generation_section["language_dropdown"]],
        outputs=[generation_section["language_dropdown"]],
    ).then(
        fn=None,
        # The Python handler re-execs the process. Give the new server time
        # to bind its port, then reload the page to pick up the fresh UI.
        # If the first reload hits a dead socket, retry every 800 ms.
        js=(
            "() => {"
            "  const banner = document.createElement('div');"
            "  banner.style.cssText = 'position:fixed;top:0;left:0;right:0;"
            "z-index:99999;background:#1f2937;color:#f9fafb;padding:14px 20px;"
            "text-align:center;font:600 14px system-ui,sans-serif;"
            "box-shadow:0 2px 8px rgba(0,0,0,.4)';"
            "  banner.textContent = '⟳ Switching language — restarting UI…';"
            "  document.body.appendChild(banner);"
            "  const tryReload = () => {"
            "    fetch(window.location.href, {cache: 'no-store'})"
            "      .then(r => { if (r.ok) window.location.reload(); "
            "                   else setTimeout(tryReload, 800); })"
            "      .catch(() => setTimeout(tryReload, 800));"
            "  };"
            "  setTimeout(tryReload, 2500);"
            "}"
        ),
    )

    generation_section["config_path"].change(
        fn=gen_h.update_model_type_settings,
        inputs=[
            generation_section["config_path"],
            generation_section["generation_mode"],
        ],
        outputs=[
            generation_section["inference_steps"],
            generation_section["guidance_scale"],
            generation_section["use_adg"],
            generation_section["shift"],
            generation_section["cfg_interval_start"],
            generation_section["cfg_interval_end"],
            generation_section["task_type"],
            generation_section["generation_mode"],
            generation_section["init_llm_checkbox"],
        ],
    )

    # ========== Tier Override ==========
    generation_section["tier_dropdown"].change(
        fn=lambda tier: gen_h.on_tier_change(tier, llm_handler),
        inputs=[generation_section["tier_dropdown"]],
        outputs=[
            generation_section["offload_to_cpu_checkbox"],
            generation_section["offload_dit_to_cpu_checkbox"],
            generation_section["compile_model_checkbox"],
            generation_section["quantization_checkbox"],
            generation_section["backend_dropdown"],
            generation_section["lm_model_path"],
            generation_section["init_llm_checkbox"],
            generation_section["batch_size_input"],
            generation_section["audio_duration"],
            generation_section["gpu_info_display"],
        ],
    )

    generation_section["init_btn"].click(
        fn=lambda *args: gen_h.init_service_wrapper(dit_handler, llm_handler, *args),
        inputs=[
            generation_section["checkpoint_dropdown"],
            generation_section["config_path"],
            generation_section["device"],
            generation_section["init_llm_checkbox"],
            generation_section["lm_model_path"],
            generation_section["backend_dropdown"],
            generation_section["use_flash_attention_checkbox"],
            generation_section["offload_to_cpu_checkbox"],
            generation_section["offload_dit_to_cpu_checkbox"],
            generation_section["compile_model_checkbox"],
            generation_section["quantization_checkbox"],
            generation_section["mlx_dit_checkbox"],
            generation_section["generation_mode"],
            generation_section["batch_size_input"],
        ],
        outputs=[
            generation_section["init_status"],
            generation_section["generate_btn"],
            generation_section["service_config_accordion"],
            generation_section["inference_steps"],
            generation_section["guidance_scale"],
            generation_section["use_adg"],
            generation_section["shift"],
            generation_section["cfg_interval_start"],
            generation_section["cfg_interval_end"],
            generation_section["task_type"],
            generation_section["generation_mode"],
            generation_section["init_llm_checkbox"],
            generation_section["audio_duration"],
            generation_section["batch_size_input"],
            generation_section["think_checkbox"],
        ],
    )

    # ========== Multi-LoRA Handlers ==========
    from ..generation.lora_actions import (
        handle_add_lora,
        handle_dataframe_edit,
        handle_remove_lora,
        handle_row_select,
        handle_set_active,
        handle_unload_all,
    )

    lora_status_out = generation_section["lora_status"]
    lora_df_out = generation_section["lora_adapters_df"]

    # Add a new adapter from path + optional name, then refresh the table.
    generation_section["load_lora_btn"].click(
        fn=lambda path, name: handle_add_lora(path, name, dit_handler),
        inputs=[
            generation_section["lora_path"],
            generation_section["lora_adapter_name"],
        ],
        outputs=[lora_status_out, lora_df_out],
    ).then(
        fn=lambda: gr.update(value=True),
        outputs=[generation_section["use_lora_checkbox"]],
    )

    # Unload every adapter and clear the table.
    generation_section["unload_lora_btn"].click(
        fn=lambda: handle_unload_all(dit_handler),
        outputs=[lora_status_out, lora_df_out],
    ).then(
        fn=lambda: gr.update(value=False),
        outputs=[generation_section["use_lora_checkbox"]],
    ).then(
        fn=lambda: -1,
        outputs=[generation_section["lora_selected_idx"]],
    )

    # Master toggle (enable/disable the active adapter).
    generation_section["use_lora_checkbox"].change(
        fn=dit_handler.set_use_lora,
        inputs=[generation_section["use_lora_checkbox"]],
        outputs=[lora_status_out],
    )

    # Track the selected row in a hidden gr.State so set-active and
    # remove buttons know which adapter to act on.
    generation_section["lora_adapters_df"].select(
        fn=handle_row_select,
        outputs=[generation_section["lora_selected_idx"]],
    )

    # Edits in the dataframe (Scale column) are committed via .change().
    generation_section["lora_adapters_df"].change(
        fn=lambda df: handle_dataframe_edit(df, dit_handler),
        inputs=[generation_section["lora_adapters_df"]],
        outputs=[lora_status_out, lora_df_out],
    )

    generation_section["lora_set_active_btn"].click(
        fn=lambda idx: handle_set_active(idx, dit_handler),
        inputs=[generation_section["lora_selected_idx"]],
        outputs=[lora_status_out, lora_df_out],
    )

    generation_section["lora_remove_btn"].click(
        fn=lambda idx: handle_remove_lora(idx, dit_handler),
        inputs=[generation_section["lora_selected_idx"]],
        outputs=[lora_status_out, lora_df_out],
    ).then(
        fn=lambda: -1,
        outputs=[generation_section["lora_selected_idx"]],
    )

    # ========== MLX VAE Chunk Size ==========
    generation_section["mlx_vae_chunk_size"].change(
        fn=lambda val: setattr(dit_handler, "mlx_vae_chunk_size", int(val)),
        inputs=[generation_section["mlx_vae_chunk_size"]],
    )

    # ========== DiT Quality Preset ==========
    from acestep.ui.gradio.events.generation.dit_presets import handle_dit_preset_change

    generation_section["dit_preset"].change(
        fn=handle_dit_preset_change,
        inputs=[generation_section["dit_preset"]],
        outputs=[
            generation_section["inference_steps"],
            generation_section["shift"],
            generation_section["sampler_mode"],
        ],
    )

    # ========== Auto Checkbox Handlers ==========
    auto_field_map = {
        "bpm_auto": ("bpm", "bpm"),
        "key_auto": ("key_scale", "key_scale"),
        "timesig_auto": ("time_signature", "time_signature"),
        "vocal_lang_auto": ("vocal_language", "vocal_language"),
        "duration_auto": ("audio_duration", "audio_duration"),
    }
    for auto_key, (field_name, comp_key) in auto_field_map.items():
        generation_section[auto_key].change(
            fn=lambda checked, fn=field_name: gen_h.on_auto_checkbox_change(
                checked, fn
            ),
            inputs=[generation_section[auto_key]],
            outputs=[generation_section[comp_key]],
        )

    auto_checkbox_outputs = build_auto_checkbox_outputs(context)
    auto_checkbox_inputs = build_auto_checkbox_inputs(context)

    generation_section["reset_all_auto_btn"].click(
        fn=gen_h.reset_all_auto,
        outputs=auto_checkbox_outputs,
    )

    # ========== UI Visibility Updates ==========
    generation_section["init_llm_checkbox"].change(
        fn=gen_h.update_negative_prompt_visibility,
        inputs=[generation_section["init_llm_checkbox"]],
        outputs=[generation_section["lm_negative_prompt"]],
    )

    generation_section["batch_size_input"].change(
        fn=gen_h.update_audio_components_visibility,
        inputs=[generation_section["batch_size_input"]],
        outputs=[
            results_section["audio_col_1"],
            results_section["audio_col_2"],
            results_section["audio_col_3"],
            results_section["audio_col_4"],
            results_section["audio_row_5_8"],
            results_section["audio_col_5"],
            results_section["audio_col_6"],
            results_section["audio_col_7"],
            results_section["audio_col_8"],
        ],
    )

    return auto_checkbox_inputs, auto_checkbox_outputs


def _apply_runtime_language(language: str) -> dict[str, Any]:
    """Persist the selected UI language and restart the server.

    Gradio builds component labels once at startup via ``t()`` — dynamic
    switching would require updating ~280 components individually. The
    pragmatic fix: persist the choice to disk and re-exec the Python
    process so the fresh startup reads the new language via
    ``load_language()`` and rebuilds the interface.

    The in-memory language is also updated synchronously so any handler
    running concurrently during the restart window sees the new value.

    Args:
        language: Selected UI language code from the language dropdown.

    Returns:
        A ``gr.update`` payload preserving the selected dropdown value.
    """
    import os
    import sys
    import threading

    # Persist for the next startup.
    try:
        save_language(language)
    except Exception as exc:  # noqa: BLE001 - best-effort persistence
        print(f"[language] failed to persist UI language: {exc}")

    # Update in-memory i18n for any still-running handlers.
    token = set_language_context(language)
    try:
        get_i18n(language)
    finally:
        reset_language_context(token)

    # Schedule a re-exec after the handler has returned so the client
    # receives the dropdown ack before the server dies. The JS chained
    # on ``.then()`` reloads the page, which will reconnect once the
    # restarted server is back up.
    def _restart_process() -> None:
        import time

        time.sleep(0.5)
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:  # noqa: BLE001
            pass
        try:
            os.execv(sys.executable, [sys.executable, *sys.argv])
        except Exception as exc:  # noqa: BLE001
            print(f"[language] os.execv failed: {exc}; forcing exit")
            os._exit(0)

    threading.Thread(target=_restart_process, daemon=True).start()

    return gr.update(value=language)
