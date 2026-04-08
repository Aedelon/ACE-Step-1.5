"""ACE-Step dark theme for Gradio.

Professional music-app appearance using zinc/blue/amber palette.
Forces dark appearance by setting BOTH light and dark variables
to the same dark values, bypassing Gradio's theme toggle entirely.
"""

from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes


class ACEStepDark(Base):
    """Dark theme optimized for music generation workflows.

    Sets both light-mode and dark-mode CSS variables to identical
    dark values so the UI is always dark regardless of browser
    preference or Gradio's theme toggle state.
    """

    def __init__(self):
        super().__init__(
            primary_hue=colors.blue,
            secondary_hue=colors.amber,
            neutral_hue=colors.zinc,
            font=(
                fonts.GoogleFont("Inter"),
                "ui-sans-serif",
                "system-ui",
                "sans-serif",
            ),
            font_mono=(
                fonts.GoogleFont("JetBrains Mono"),
                "ui-monospace",
                "monospace",
            ),
            radius_size=sizes.radius_md,
        )
        # Build kwargs that set both light and dark to the same value
        dark_vars = {
            # Body
            "body_background_fill": "*neutral_950",
            "body_text_color": "*neutral_100",
            "body_text_color_subdued": "*neutral_400",
            # Blocks
            "background_fill_primary": "*neutral_900",
            "background_fill_secondary": "*neutral_800",
            "border_color_primary": "*neutral_700",
            "block_background_fill": "*neutral_900",
            "block_border_color": "*neutral_700",
            "block_label_background_fill": "*neutral_800",
            "block_label_text_color": "*neutral_300",
            "block_title_background_fill": "*neutral_800",
            "block_title_text_color": "*neutral_200",
            # Panels
            "panel_background_fill": "*neutral_900",
            "panel_border_color": "*neutral_700",
            # Inputs
            "input_background_fill": "*neutral_800",
            "input_border_color": "*neutral_600",
            "input_placeholder_color": "*neutral_500",
            # Primary button (Generate) - blue
            "button_primary_background_fill": "*primary_600",
            "button_primary_background_fill_hover": "*primary_500",
            "button_primary_text_color": "white",
            "button_primary_border_color": "*primary_500",
            # Secondary button
            "button_secondary_background_fill": "*neutral_700",
            "button_secondary_background_fill_hover": "*neutral_600",
            "button_secondary_text_color": "*neutral_200",
            "button_secondary_border_color": "*neutral_600",
            # Checkbox / Radio
            "checkbox_background_color": "*neutral_700",
            "checkbox_border_color": "*neutral_500",
            "checkbox_label_text_color": "*neutral_200",
            # Slider
            "slider_color": "*primary_500",
            # Color accent
            "color_accent_soft": "*primary_500",
        }
        # Set both light and dark variants to the same dark value
        merged = {}
        for key, value in dark_vars.items():
            merged[key] = value
            merged[f"{key}_dark"] = value
        self.set(**merged)
