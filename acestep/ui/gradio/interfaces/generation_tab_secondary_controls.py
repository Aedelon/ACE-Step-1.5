"""Secondary generation-tab controls (cover, custom prompt, repaint)."""

from typing import Any

import gradio as gr

from acestep.ui.gradio.help_content import create_help_button
from acestep.ui.gradio.i18n import t


def build_cover_strength_controls() -> dict[str, Any]:
    """Create code/remix strength controls used by non-simple generation modes.

    Args:
        None.

    Returns:
        A component map containing audio/code strength sliders and remix help group.
    """

    audio_cover_strength = gr.Slider(
        minimum=0.0,
        maximum=1.0,
        value=1.0,
        step=0.01,
        label=t("generation.codes_strength_label"),
        info=t("generation.codes_strength_info"),
        elem_classes=["acestep-tt"],
        visible=True,
    )
    with gr.Group(visible=False) as remix_help_group:
        create_help_button("generation_remix")
    cover_noise_strength = gr.Slider(
        minimum=0.0,
        maximum=1.0,
        value=0.0,
        step=0.01,
        label=t("generation.cover_noise_strength_label"),
        info=t("generation.cover_noise_strength_info"),
        elem_classes=["acestep-tt"],
        visible=False,
    )
    return {
        "audio_cover_strength": audio_cover_strength,
        "remix_help_group": remix_help_group,
        "cover_noise_strength": cover_noise_strength,
    }


def build_custom_mode_controls() -> dict[str, Any]:
    """Create custom-mode caption, lyrics, and reference-audio controls.

    Args:
        None.

    Returns:
        A component map containing custom-mode text/audio inputs and formatting actions.
    """

    with gr.Group(visible=True, elem_classes=["acestep-tt"]) as custom_mode_group:
        create_help_button("generation_custom")
        with gr.Row(equal_height=True):
            # Reference audio compressed from scale=2 to scale=1 — 95% of
            # sessions don't upload a reference, the previous 20% width
            # was wasted screen real estate. Caption + lyrics get the
            # extra room.
            with gr.Column(scale=1, min_width=180):
                reference_audio = gr.Audio(
                    label=t("generation.reference_audio"),
                    type="filepath",
                    show_label=True,
                )
            with gr.Column(scale=9):
                with gr.Row(equal_height=True):
                    with gr.Column(scale=1):
                        captions = gr.Textbox(
                            label=t("generation.caption_label"),
                            placeholder=t("generation.caption_placeholder"),
                            lines=12,
                            max_lines=12,
                        )
                        with gr.Row(elem_classes="instrumental-row"):
                            format_caption_btn = gr.Button(
                                t("generation.format_caption_btn"),
                                variant="secondary",
                                size="sm",
                            )
                    with gr.Column(scale=1):
                        lyrics = gr.Textbox(
                            label=t("generation.lyrics_label"),
                            placeholder=t("generation.lyrics_placeholder"),
                            lines=12,
                            max_lines=12,
                        )
                        with gr.Row(elem_classes="instrumental-row"):
                            instrumental_checkbox = gr.Checkbox(
                                label=t("generation.instrumental_label"),
                                value=False,
                                scale=1,
                            )
                            format_lyrics_btn = gr.Button(
                                t("generation.format_lyrics_btn"),
                                variant="secondary",
                                size="sm",
                                scale=2,
                            )
            with gr.Column(scale=1, min_width=80, elem_classes="icon-btn-wrap"):
                sample_btn = gr.Button(
                    t("generation.sample_btn"), variant="primary", size="lg"
                )
    return {
        "custom_mode_group": custom_mode_group,
        "reference_audio": reference_audio,
        "captions": captions,
        "format_caption_btn": format_caption_btn,
        "lyrics": lyrics,
        "instrumental_checkbox": instrumental_checkbox,
        "format_lyrics_btn": format_lyrics_btn,
        "sample_btn": sample_btn,
    }


def build_repainting_controls() -> dict[str, Any]:
    """Create repainting range controls used by repaint/lego flows.

    Args:
        None.

    Returns:
        A component map containing repainting group, header, and start/end controls.
    """

    with gr.Group(visible=False) as repainting_group:
        create_help_button("generation_repaint")
        repainting_header_html = gr.HTML(
            f"<h5>{t('generation.repainting_controls')}</h5>"
        )
        with gr.Row():
            repainting_start = gr.Number(
                label=t("generation.repainting_start"),
                value=0.0,
                step=0.1,
            )
            repainting_end = gr.Number(
                label=t("generation.repainting_end"),
                value=-1,
                minimum=-1,
                step=0.1,
            )
        with gr.Row():
            repaint_mode = gr.Dropdown(
                label="Repaint Mode",
                choices=["conservative", "balanced", "aggressive"],
                value="balanced",
                info=(
                    "How the model treats the source audio in the repaint zone. "
                    "Conservative = preserves the source as much as possible (subtle edits). "
                    "Balanced = mixes preservation and regeneration based on Repaint Strength. "
                    "Aggressive = full regeneration of the zone, ignores source content."
                ),
                elem_classes=["acestep-tt"],
            )
            repaint_strength = gr.Slider(
                label="Repaint Strength",
                minimum=0.0,
                maximum=1.0,
                step=0.05,
                value=0.5,
                info=(
                    "Only used in Balanced mode. Controls the blend between source "
                    "preservation and regeneration. 0.0 = pure conservative (keep source), "
                    "1.0 = pure aggressive (full regeneration). Ignored in Conservative/Aggressive modes."
                ),
                elem_classes=["acestep-tt"],
            )
        with gr.Row():
            chunk_mask_mode = gr.Dropdown(
                label="Chunk Mask Mode",
                choices=["auto", "explicit"],
                value="auto",
                info=(
                    "How the repaint zone is masked for the diffusion model. "
                    "Auto = the model decides which regions to regenerate based on context (recommended). "
                    "Explicit = strict 0/1 binary mask matching exactly the Repainting Start/End range. "
                    "Auto produces smoother transitions, Explicit gives precise control."
                ),
                elem_classes=["acestep-tt"],
            )
            repaint_latent_crossfade_frames = gr.Slider(
                label="Latent Crossfade Frames",
                minimum=0,
                maximum=50,
                step=1,
                value=10,
                info=(
                    "Width of the latent-space crossfade at repaint zone boundaries, in 25Hz frames. "
                    "10 frames ≈ 0.4s. Smooths the join between original and repainted audio at the latent level "
                    "(before VAE decode). Higher = smoother transitions but more bleed-through. "
                    "Set to 0 for hard cuts."
                ),
                elem_classes=["acestep-tt"],
            )
            repaint_wav_crossfade_sec = gr.Slider(
                label="Waveform Crossfade (s)",
                minimum=0.0,
                maximum=2.0,
                step=0.05,
                value=0.0,
                info=(
                    "Additional crossfade applied to the final waveform at repaint zone boundaries, in seconds. "
                    "0.0 = hard cut at the splice point (default). "
                    "Higher values = smoother audio splice (e.g. 0.1-0.5s for natural transitions). "
                    "Applied AFTER VAE decode, on top of Latent Crossfade Frames."
                ),
                elem_classes=["acestep-tt"],
            )
        repaint_strength_memory = gr.State(value=0.5)
    return {
        "repainting_group": repainting_group,
        "repainting_header_html": repainting_header_html,
        "repainting_start": repainting_start,
        "repainting_end": repainting_end,
        "repaint_mode": repaint_mode,
        "repaint_strength": repaint_strength,
        "repaint_strength_memory": repaint_strength_memory,
        "chunk_mask_mode": chunk_mask_mode,
        "repaint_latent_crossfade_frames": repaint_latent_crossfade_frames,
        "repaint_wav_crossfade_sec": repaint_wav_crossfade_sec,
    }
