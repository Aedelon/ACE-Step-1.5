"""Unit tests for the status_format helpers."""

from __future__ import annotations

import unittest

from acestep.ui.gradio.events.results.status_format import (
    format_status_busy,
    format_status_err,
    format_status_ok,
    format_status_warn,
)


class StatusFormatTests(unittest.TestCase):
    def test_ok_uses_status_ok_class(self) -> None:
        out = format_status_ok("✅ Generation Complete")
        self.assertIn('class="status-ok"', out)
        self.assertIn("✅ Generation Complete", out)

    def test_err_uses_status_err_class(self) -> None:
        out = format_status_err("❌ OOM")
        self.assertIn('class="status-err"', out)
        self.assertIn("❌ OOM", out)

    def test_warn_uses_status_warn_class(self) -> None:
        out = format_status_warn("⚠️ Cache miss")
        self.assertIn('class="status-warn"', out)

    def test_busy_returns_escaped_plain_text(self) -> None:
        out = format_status_busy("⏳ Encoding...")
        # No span wrapper for busy — chip styling from base CSS
        self.assertNotIn("<span", out)
        self.assertIn("⏳ Encoding...", out)

    def test_html_is_escaped(self) -> None:
        out = format_status_ok('<script>alert("x")</script>')
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)
        self.assertIn("&quot;x&quot;", out)

    def test_ampersand_and_quotes_escaped(self) -> None:
        out = format_status_err("A & B failed")
        self.assertIn("A &amp; B failed", out)


if __name__ == "__main__":
    unittest.main()
