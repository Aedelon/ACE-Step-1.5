"""Unit tests for the hero section renderer."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from acestep.ui.gradio.interfaces.hero import (
    HERO_ELEM_ID,
    derive_config_display_name,
    rebuild_hero_html,
    render_hero_html,
)


class RenderHeroHtmlTests(unittest.TestCase):
    def test_minimal_call_renders_section(self) -> None:
        html = render_hero_html(title="Hello", subtitle="World")
        # The inner <section> uses the .ace-hero CLASS only — the id
        # belongs to the outer Gradio wrapper (gr.HTML(elem_id=HERO_ELEM_ID)).
        # Putting the same id on both would be invalid HTML.
        self.assertIn('class="ace-hero"', html)
        self.assertNotIn(f'id="{HERO_ELEM_ID}"', html)
        self.assertIn("<h1", html)
        self.assertIn("Hello", html)
        self.assertIn("World", html)

    def test_default_status_pills_present(self) -> None:
        html = render_hero_html(title="t", subtitle="s")
        # Three pills are always rendered (model, language, mode), each
        # with a base class + at least one modifier. The exact occurrence
        # count is brittle (depends on whether modifiers stack), so just
        # assert the three modifier classes are present.
        self.assertIn("ace-status-pill--model", html)
        self.assertIn("ace-status-pill--lang", html)
        self.assertIn("ace-status-pill--mode", html)

    def test_model_loaded_uses_green_dot(self) -> None:
        html = render_hero_html(
            title="t", subtitle="s", model_loaded=True, model_name="XL Turbo"
        )
        self.assertIn("ace-dot--green", html)
        self.assertIn("XL Turbo", html)
        self.assertNotIn("Model not loaded", html)

    def test_model_not_loaded_uses_amber_dot_and_fallback(self) -> None:
        html = render_hero_html(title="t", subtitle="s", model_loaded=False)
        self.assertIn("ace-dot--amber", html)
        self.assertIn("Model not loaded", html)
        self.assertIn("ace-status-pill--needs-init", html)

    def test_language_code_uppercased(self) -> None:
        html = render_hero_html(title="t", subtitle="s", language_code="fr")
        self.assertIn("FR", html)
        # Lowercase variant should not survive (the "fr" we passed in
        # doesn't appear anywhere outside the dot class names).
        self.assertNotIn(">fr</span>", html)

    def test_user_mode_expert_label(self) -> None:
        html = render_hero_html(title="t", subtitle="s", user_mode="expert")
        self.assertIn("Expert", html)
        self.assertNotIn(">Beginner<", html)

    def test_user_mode_beginner_label(self) -> None:
        html = render_hero_html(title="t", subtitle="s", user_mode="beginner")
        self.assertIn("Beginner", html)

    def test_html_special_chars_escaped(self) -> None:
        html = render_hero_html(
            title="<script>alert(1)</script>",
            subtitle="A & B",
            eyebrow="<b>EYE</b>",
            model_name='evil"onload=hack',
        )
        # Tags must be escaped, no live <script> in the output
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("A &amp; B", html)
        self.assertIn("&lt;b&gt;EYE", html)
        self.assertIn("&quot;onload=hack", html)

    def test_eyebrow_default_value(self) -> None:
        html = render_hero_html(title="t", subtitle="s")
        self.assertIn("ACE-STEP", html)
        self.assertIn("MUSIC GENERATION", html)


class DeriveConfigDisplayNameTests(unittest.TestCase):
    def test_strips_dirname_and_json_suffix(self) -> None:
        self.assertEqual(
            derive_config_display_name("/path/to/config_1_5_xl_turbo.json"),
            "config_1_5_xl_turbo",
        )

    def test_bare_filename_without_suffix(self) -> None:
        self.assertEqual(
            derive_config_display_name("acestep_v15_base"),
            "acestep_v15_base",
        )

    def test_none_returns_none(self) -> None:
        self.assertIsNone(derive_config_display_name(None))

    def test_empty_string_returns_none(self) -> None:
        self.assertIsNone(derive_config_display_name(""))


class RebuildHeroHtmlTests(unittest.TestCase):
    """Covers ``rebuild_hero_html`` which is what the event handlers call
    after init_btn.click or user_mode_radio.change to refresh the pills.
    """

    def test_initialized_expert_mode(self) -> None:
        with patch(
            "acestep.ui.gradio.interfaces.hero.t",
            side_effect=lambda key: {
                "app.hero_title": "Localised Title",
                "app.hero_subtitle": "Localised Subtitle",
            }.get(key, ""),
        ):
            html = rebuild_hero_html(
                initialized=True,
                model_name="config_1_5_xl_turbo",
                language_code="fr",
                user_mode="expert",
            )
        self.assertIn("ace-dot--green", html)  # model pill green
        self.assertIn("ace-dot--blue", html)  # mode pill blue (expert)
        self.assertIn("config_1_5_xl_turbo", html)
        self.assertIn("FR", html)
        self.assertIn("Expert", html)
        self.assertIn("Localised Title", html)
        self.assertIn("Localised Subtitle", html)

    def test_cold_start_beginner_mode(self) -> None:
        with patch(
            "acestep.ui.gradio.interfaces.hero.t",
            side_effect=lambda key: {
                "app.hero_title": "Cold",
                "app.hero_subtitle": "Start",
            }.get(key, ""),
        ):
            html = rebuild_hero_html(
                initialized=False,
                model_name=None,
                language_code="en",
                user_mode="beginner",
            )
        self.assertIn("ace-dot--amber", html)  # model pill amber (needs init)
        self.assertIn("Model not loaded", html)
        self.assertIn("Beginner", html)

    def test_resolve_hero_strings_uses_localised_title(self) -> None:
        """Regression test for the bug where ``app.title``'s lstrip
        heuristic always returned the hardcoded English fallback for
        non-English locales. With the new ``app.hero_title`` key the
        localised value must pass through unchanged."""
        with patch(
            "acestep.ui.gradio.interfaces.hero.t",
            side_effect=lambda key: {
                "app.hero_title": "Génère de la musique à partir de texte.",
                "app.hero_subtitle": "Propulsé par ACE-Step v1.5.",
            }.get(key, ""),
        ):
            html = rebuild_hero_html(
                initialized=False,
                model_name=None,
                language_code="fr",
                user_mode="beginner",
            )
        # The French title must appear verbatim — no ACE-fallback leak.
        self.assertIn("Génère de la musique", html)
        self.assertNotIn("Generate music from text and lyrics.", html)


if __name__ == "__main__":
    unittest.main()
