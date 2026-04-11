"""Unit tests for the hero section renderer."""

from __future__ import annotations

import unittest

from acestep.ui.gradio.interfaces.hero import HERO_ELEM_ID, render_hero_html


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


if __name__ == "__main__":
    unittest.main()
