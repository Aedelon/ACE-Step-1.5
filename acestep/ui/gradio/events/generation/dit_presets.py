"""DiT quality preset handler."""

import gradio as gr

PRESET_VALUES = {
    "Fast (8 steps, euler)": {
        "inference_steps": 8,
        "shift": 3.0,
        "sampler_mode": "euler",
    },
    "Balanced (15 steps, euler)": {
        "inference_steps": 15,
        "shift": 3.0,
        "sampler_mode": "euler",
    },
    "Quality (30 steps, heun)": {
        "inference_steps": 30,
        "shift": 3.0,
        "sampler_mode": "heun",
    },
}


def handle_dit_preset_change(preset):
    """Update DiT parameters based on selected preset.

    Returns:
        Tuple of (inference_steps, shift, sampler_mode) updates.
    """
    if preset == "Custom" or preset not in PRESET_VALUES:
        return gr.skip(), gr.skip(), gr.skip()

    vals = PRESET_VALUES[preset]
    return (
        gr.update(value=vals["inference_steps"]),
        gr.update(value=vals["shift"]),
        gr.update(value=vals["sampler_mode"]),
    )
