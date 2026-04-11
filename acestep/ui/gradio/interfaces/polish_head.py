"""Phase D — Polish CSS that must bypass Gradio's ``prefix_css``.

Gradio 6.2 wraps everything passed via ``launch(css=…)`` under
``.gradio-container.gradio-container-{version} .contain``. That means
the following selectors **never match** when injected via ``css=`` :

- ``body`` / ``html`` / ``:root`` (would become ``... .contain body``)
- ``.gradio-container`` itself (becomes a self-nested no-op)
- ``@font-face`` / ``@import`` (scoped under a parent selector → invalid)

To style those targets we have to inject the rules through
``launch(head=…)``, where Gradio injects the literal HTML without any
rewriting. This module owns those head-injected rules so the polish.py
companion file can stay focused on the in-container selectors.

Verified against ``js/core/src/css.ts`` (function ``prefix_css``).
"""

from __future__ import annotations


def get_polish_head() -> str:
    """Return the ``<style>`` block injected via ``Blocks(head=…)``."""
    return f"<style>{_HEAD_CSS}</style>"


_HEAD_CSS = """
/* ============================================================
   ACE-Step Phase D — Head-injected polish (bypasses prefix_css)
   ============================================================ */

/* ---------- Body backdrop ---------- */
body {
    background: radial-gradient(
        ellipse at top,
        #0f1117 0%,
        #08090d 65%
    );
    color: #f4f4f5;
    font-feature-settings: "ss01", "cv11";
}

/* ---------- App container max-width + breathing space ---------- */
.gradio-container,
.gradio-container.gradio-container-6-2-0 {
    max-width: 1480px;
    margin: 0 auto;
    padding: 24px 28px 60px 28px;
}

/* ---------- Hero header (targeted via .main-header div from index) ---------- */
.main-header {
    text-align: left;
    margin-bottom: 24px;
    padding: 8px 4px 16px 4px;
}
.main-header h1 {
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin: 6px 0 4px 0;
    color: #f4f4f5;
}
.main-header p {
    color: #a1a1aa;
    font-size: 14px;
    margin: 0;
    letter-spacing: 0.005em;
}

/* ---------- Responsive container ---------- */
@media (max-width: 1100px) {
    .gradio-container,
    .gradio-container.gradio-container-6-2-0 {
        padding: 16px 14px 40px 14px;
    }
    .main-header h1 {
        font-size: 26px;
    }
}
"""
