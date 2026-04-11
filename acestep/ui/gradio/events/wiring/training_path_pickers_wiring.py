"""Wire native OS folder/file pickers to every Browse button in the training tab.

The training tab has a dozen path Textboxes (load dataset JSON, audio
scan folder, preprocessed tensors directory, LoRA/LoKr output dirs,
export paths, checkpoint resume, etc). Rather than repeating the same
``.click(...)`` block for each, this module enumerates them once and
attaches a native OS picker via
``acestep.ui.gradio.events.generation.native_folder_picker``.

Only fires on localhost usage — the picker opens on the machine running
the Gradio server, which for ACE-Step is the same box as the browser.
"""

from __future__ import annotations

from typing import Any

import gradio as gr

from ..generation.native_folder_picker import pick_file, pick_folder


def _attach_folder_picker(
    button: Any,
    target_textbox: Any,
    *,
    title: str,
) -> None:
    """Wire a button click to open the folder picker and fill *target_textbox*."""

    def _handler(current_value: str) -> Any:  # noqa: ARG001 - kept for symmetry
        picked = pick_folder(title=title)
        if not picked:
            return gr.update()
        return gr.update(value=picked)

    button.click(
        fn=_handler,
        inputs=[target_textbox],
        outputs=[target_textbox],
    )


def _attach_file_picker(
    button: Any,
    target_textbox: Any,
    *,
    title: str,
    extensions: tuple[str, ...] = (),
) -> None:
    """Wire a button click to open the file picker and fill *target_textbox*."""

    def _handler(current_value: str) -> Any:  # noqa: ARG001
        picked = pick_file(title=title, extensions=extensions)
        if not picked:
            return gr.update()
        return gr.update(value=picked)

    button.click(
        fn=_handler,
        inputs=[target_textbox],
        outputs=[target_textbox],
    )


# Static plan of every path Textbox that gets a Browse button and the
# picker kind to attach. "folder" → pick_folder, "json" → pick_file with
# a JSON filter. Entries whose button key is missing from the training
# section are silently skipped so this helper stays tolerant of partial
# UI rollouts.
_TRAINING_PICKERS: tuple[tuple[str, str, str, str], ...] = (
    # (button_key, target_key, kind, title)
    ("load_json_path_browse_btn", "load_json_path", "json", "Load dataset JSON"),
    (
        "audio_directory_browse_btn",
        "audio_directory",
        "folder",
        "Select the audio folder",
    ),
    ("save_path_browse_btn", "save_path", "json", "Select dataset JSON path"),
    (
        "load_existing_dataset_path_browse_btn",
        "load_existing_dataset_path",
        "json",
        "Load dataset JSON",
    ),
    (
        "preprocess_output_dir_browse_btn",
        "preprocess_output_dir",
        "folder",
        "Select the preprocessed tensors folder",
    ),
    (
        "training_tensor_dir_browse_btn",
        "training_tensor_dir",
        "folder",
        "Select the preprocessed tensors folder",
    ),
    (
        "lora_output_dir_browse_btn",
        "lora_output_dir",
        "folder",
        "Select the LoRA output folder",
    ),
    (
        "resume_checkpoint_dir_browse_btn",
        "resume_checkpoint_dir",
        "folder",
        "Select the checkpoint folder to resume from",
    ),
    (
        "export_path_browse_btn",
        "export_path",
        "folder",
        "Select the LoRA export destination",
    ),
    (
        "lokr_training_tensor_dir_browse_btn",
        "lokr_training_tensor_dir",
        "folder",
        "Select the preprocessed tensors folder",
    ),
    (
        "lokr_output_dir_browse_btn",
        "lokr_output_dir",
        "folder",
        "Select the LoKr output folder",
    ),
    (
        "lokr_export_path_browse_btn",
        "lokr_export_path",
        "folder",
        "Select the LoKr export destination",
    ),
)


def register_training_path_pickers(training_section: dict[str, Any]) -> None:
    """Wire every Browse button in *training_section* to its native picker."""
    for button_key, target_key, kind, title in _TRAINING_PICKERS:
        button = training_section.get(button_key)
        target = training_section.get(target_key)
        if button is None or target is None:
            # UI panel didn't render that control (e.g. section-specific
            # builders called in isolation); safely skip it.
            continue
        if kind == "json":
            _attach_file_picker(
                button,
                target,
                title=title,
                extensions=("json",),
            )
        else:
            _attach_folder_picker(button, target, title=title)
