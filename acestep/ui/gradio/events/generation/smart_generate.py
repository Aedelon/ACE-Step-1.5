"""Smart Generate pre-handler for Simple mode.

Auto-runs AI Draft (Create Sample) before Generate when the user clicks
Generate in Simple mode without having drafted first.
"""

import gradio as gr
from loguru import logger

from .llm_sample_actions import handle_create_sample


def smart_generate_pre_handler(
    generation_mode,
    simple_sample_created,
    query,
    instrumental,
    vocal_lang,
    lm_temperature,
    lm_top_k,
    lm_top_p,
    constrained_decoding_debug,
    llm_handler,
):
    """Auto-run AI Draft before Generate when in Simple mode.

    If mode is not Simple or the sample was already created, returns
    gr.skip() for all 15 outputs so the downstream chain proceeds
    unchanged.

    Args:
        generation_mode: Current mode string ("Simple", "Custom", etc.).
        simple_sample_created: Whether AI Draft already ran this session.
        query: Simple mode text input.
        instrumental: Whether instrumental mode is on.
        vocal_lang: Preferred vocal language.
        lm_temperature: LLM temperature.
        lm_top_k: LLM top-k.
        lm_top_p: LLM top-p.
        constrained_decoding_debug: Debug flag.
        llm_handler: LLM handler instance.

    Returns:
        Tuple of 15 UI updates (same shape as handle_create_sample output).
    """
    if generation_mode != "Simple" or simple_sample_created:
        return tuple(gr.skip() for _ in range(15))

    logger.info("[Smart Generate] Auto-running AI Draft before Generate...")
    return handle_create_sample(
        llm_handler,
        query,
        instrumental,
        vocal_lang,
        lm_temperature,
        lm_top_k,
        lm_top_p,
        constrained_decoding_debug,
        switch_mode=False,
    )
