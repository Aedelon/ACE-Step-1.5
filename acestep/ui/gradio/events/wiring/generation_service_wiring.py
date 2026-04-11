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

    init_click = generation_section["init_btn"].click(
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

    # Hero pills refresh — after init_service_wrapper returns, rebuild
    # the hero HTML so the model pill flips amber → green with the
    # actual model name. Chained via ``.then()`` instead of extending
    # init_service_wrapper's already 15-wide return tuple, which would
    # require touching every caller / test.
    hero_html = generation_section.get("hero_html")
    user_mode_radio = generation_section.get("user_mode_radio")
    ui_language = generation_section.get("_ui_language", "en")
    if hero_html is not None:
        import os

        from acestep.ui.gradio.interfaces.hero import rebuild_hero_html

        def _derive_display_name(config_value: Any) -> str | None:
            """Turn a raw config path into a human-readable pill label.

            Strips the directory and ``.json`` suffix so the pill says
            ``config_1_5_xl_turbo`` rather than the full filesystem path.
            Returns ``None`` when no config was supplied so the hero
            falls back to its "Model not loaded" default.
            """
            if not config_value:
                return None
            base = os.path.basename(str(config_value))
            if base.endswith(".json"):
                base = base[: -len(".json")]
            return base or None

        if user_mode_radio is not None:

            def _refresh_hero_after_init(config_value: Any, mode_value: Any) -> str:
                return rebuild_hero_html(
                    initialized=dit_handler.model is not None,
                    model_name=_derive_display_name(config_value)
                    if dit_handler.model is not None
                    else None,
                    language_code=ui_language,
                    user_mode=str(mode_value or "beginner"),
                )

            init_click.then(
                fn=_refresh_hero_after_init,
                inputs=[generation_section["config_path"], user_mode_radio],
                outputs=[hero_html],
            )
        else:
            # Service mode: no user_mode_radio, always render as beginner.
            def _refresh_hero_after_init_service(config_value: Any) -> str:
                return rebuild_hero_html(
                    initialized=dit_handler.model is not None,
                    model_name=_derive_display_name(config_value)
                    if dit_handler.model is not None
                    else None,
                    language_code=ui_language,
                    user_mode="beginner",
                )

            init_click.then(
                fn=_refresh_hero_after_init_service,
                inputs=[generation_section["config_path"]],
                outputs=[hero_html],
            )

    # ========== Multi-LoRA Handlers ==========
    from ..generation.lora_actions import (
        ACTIVE_MARKER,
        handle_add_lora,
        handle_remove_by_name,
        handle_set_active_by_name,
        handle_set_scale_by_name,
        handle_unload_all,
        status_to_rows,
    )

    lora_status_out = generation_section["lora_status"]
    lora_state_out = generation_section["lora_state"]

    # Add a new adapter from path + optional name, then refresh state.
    generation_section["load_lora_btn"].click(
        fn=lambda path, name: handle_add_lora(path, name, dit_handler),
        inputs=[
            generation_section["lora_path"],
            generation_section["lora_adapter_name"],
        ],
        outputs=[lora_status_out, lora_state_out],
    ).then(
        fn=lambda: gr.update(value=True),
        outputs=[generation_section["use_lora_checkbox"]],
    )

    # Unload every adapter and clear the list.
    generation_section["unload_lora_btn"].click(
        fn=lambda: handle_unload_all(dit_handler),
        outputs=[lora_status_out, lora_state_out],
    ).then(
        fn=lambda: gr.update(value=False),
        outputs=[generation_section["use_lora_checkbox"]],
    )

    # Master toggle (enable/disable the active adapter).
    generation_section["use_lora_checkbox"].change(
        fn=dit_handler.set_use_lora,
        inputs=[generation_section["use_lora_checkbox"]],
        outputs=[lora_status_out],
    )

    # ---- Dynamic per-row UI via @gr.render ------------------------------
    # The render block is attached to the container created by
    # build_lora_controls. It redraws itself every time lora_state
    # changes — when we add/remove/activate/scale an adapter the state
    # updates and @gr.render re-runs, emitting one full row per adapter
    # with its own Slider + Activate/Deactivate + Remove button.
    container = generation_section["lora_rows_container"]

    # @gr.render must be declared INSIDE the target container's ``with``
    # context so the dynamically-created children attach to the right
    # parent. Without this, Gradio inserts them at the Blocks root.
    with container:

        @gr.render(inputs=[lora_state_out])
        def _render_lora_rows(rows):  # noqa: D401 - Gradio render hook
            if not rows:
                gr.Markdown(
                    "_No LoRA adapter loaded. Add one above to get started._",
                    elem_classes=["no-tooltip"],
                )
                return

            for row in rows:
                if not isinstance(row, (list, tuple)) or len(row) < 3:
                    continue
                marker = row[0]
                name = str(row[1])
                try:
                    current_scale = float(row[2])
                except (TypeError, ValueError):
                    current_scale = 1.0
                badge = str(row[3]) if len(row) >= 4 else "LoRA"
                is_active = marker == ACTIVE_MARKER
                badge_class = (
                    "acestep-lora-badge-lokr"
                    if badge.lower() == "lokr"
                    else "acestep-lora-badge-lora"
                )

                with gr.Row(equal_height=True, variant="panel"):
                    # Header column: marker + name + badge on a single line.
                    with gr.Column(scale=3, min_width=200):
                        gr.Markdown(
                            f"### {marker} &nbsp; **{name}** &nbsp; `{badge}`",
                            elem_classes=[
                                "no-tooltip",
                                "acestep-lora-row-header",
                                badge_class,
                            ],
                        )

                    # Intensity slider.
                    with gr.Column(scale=4, min_width=240):
                        row_slider = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            step=0.05,
                            value=current_scale,
                            label="Intensity",
                            interactive=True,
                            elem_classes=["no-tooltip"],
                        )

                    # Action buttons, side by side with visible text.
                    with gr.Column(scale=3, min_width=300):
                        with gr.Row():
                            if is_active:
                                toggle_btn = gr.Button(
                                    "⭕ Deactivate",
                                    variant="secondary",
                                    size="sm",
                                )
                                toggle_btn.click(
                                    fn=lambda: (
                                        dit_handler.clear_active_lora_adapter(),
                                        status_to_rows(dit_handler),
                                    ),
                                    outputs=[lora_status_out, lora_state_out],
                                )
                            else:
                                toggle_btn = gr.Button(
                                    "⭐ Activate",
                                    variant="primary",
                                    size="sm",
                                )
                                toggle_btn.click(
                                    fn=lambda n=name: handle_set_active_by_name(
                                        n, dit_handler
                                    ),
                                    outputs=[lora_status_out, lora_state_out],
                                )
                            remove_btn = gr.Button(
                                "🗑️ Remove",
                                variant="stop",
                                size="sm",
                            )

                    row_slider.release(
                        fn=lambda val, n=name: handle_set_scale_by_name(
                            n, val, dit_handler
                        ),
                        inputs=[row_slider],
                        outputs=[lora_status_out, lora_state_out],
                    )
                    remove_btn.click(
                        fn=lambda n=name: handle_remove_by_name(n, dit_handler),
                        outputs=[lora_status_out, lora_state_out],
                    )

    # Refresh the state on page load so reconnecting to an already
    # initialized server shows the adapters that were loaded beforehand.
    context.demo.load(
        fn=lambda: status_to_rows(dit_handler),
        outputs=[lora_state_out],
    )

    # ---- LoRA folder picker (native OS dialog) -------------------------
    # Shell out to the platform's native folder chooser (osascript on
    # macOS, zenity/kdialog on Linux, PowerShell on Windows). Only works
    # when Gradio is accessed on the same machine that serves it — the
    # expected localhost dev usage for ACE-Step.
    from ..generation.native_folder_picker import pick_folder as _native_pick_folder

    def _browse_lora_folder(current_path: str) -> Any:
        picked = _native_pick_folder(title="Select a LoRA adapter folder")
        if not picked:
            # User cancelled or picker unavailable: leave the existing
            # path untouched.
            return gr.update()
        return gr.update(value=picked)

    generation_section["lora_browse_btn"].click(
        fn=_browse_lora_folder,
        inputs=[generation_section["lora_path"]],
        outputs=[generation_section["lora_path"]],
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
