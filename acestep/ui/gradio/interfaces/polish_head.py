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

/* ---------- Display font import ----------
   Space Grotesk is a display-weight grotesk used only on the
   hero title (see .ace-hero-title in polish.py). Imported here
   via @import because Gradio's prefix_css scopes css= rules
   under .gradio-container .contain, which breaks @font-face /
   @import. head= is injected literally so the rule works.
   Falls back to Inter / system sans if the network import fails. */
@import url("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&display=swap");

/* ---------- Design tokens exposed on :root ----------
   polish.py re-exports Gradio's theme tokens on .gradio-container,
   but that scope doesn't reach ``body`` / ``html`` rules here
   because they're ancestors of the container. We redeclare the
   subset of tokens that head-injected rules actually need so
   polish_head.py and polish.py stay aligned on a single source
   of truth — change these values here and the whole backdrop
   updates in step.

   These values are duplicated by design: they must survive
   initial paint before any Gradio-scoped var is available, and
   must work without depending on the Gradio theme cascade. */
:root {
    --ace-bg-canvas-start: #0f1117;
    --ace-bg-canvas-end: #08090d;
    --ace-head-text-primary: #f4f4f5;
    --ace-head-text-secondary: #d4d4d8;
    --ace-head-text-muted: #71717a;
    --ace-head-pill-bg: rgba(24, 24, 27, 0.85);
    --ace-head-pill-border: rgba(255, 255, 255, 0.08);
    --ace-head-pill-border-hover: rgba(255, 255, 255, 0.15);
    --ace-head-hero-divider: rgba(255, 255, 255, 0.06);
}

/* ---------- Body backdrop ---------- */
body {
    background: radial-gradient(
        ellipse at top,
        var(--ace-bg-canvas-start) 0%,
        var(--ace-bg-canvas-end) 65%
    );
    color: var(--ace-head-text-primary);
    font-feature-settings: "ss01", "cv11";
}

/* ---------- App container max-width + breathing space ---------- */
.gradio-container,
.gradio-container.gradio-container-6-2-0 {
    max-width: 1480px;
    margin: 0 auto;
    padding: 24px 28px 60px 28px;
}

/* ---------- Hero section ----------
   Two layers: ``#acestep-hero`` is the Gradio wrapper div created by
   ``gr.HTML(elem_id="acestep-hero")``. ``.ace-hero`` is the inner
   <section> we render ourselves. Padding/border on the wrapper,
   typography on the inner section so they don't fight.
*/
#acestep-hero,
.ace-hero {
    padding: 24px 4px 28px 4px;
    margin-bottom: 16px;
}
.ace-hero {
    border-bottom: 1px solid var(--ace-head-hero-divider);
    padding: 0 0 28px 0;
    margin-bottom: 0;
}
#acestep-hero {
    padding-bottom: 0;
    border-bottom: none;
}
.ace-hero-eyebrow {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--ace-head-text-muted);
    margin: 0 0 10px 0;
}
.ace-hero-title {
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin: 0 0 6px 0;
    color: var(--ace-head-text-primary);
    line-height: 1.15;
}
.ace-hero-subtitle {
    color: var(--ace-head-text-secondary);
    font-size: 14px;
    margin: 0 0 18px 0;
    letter-spacing: 0.005em;
    max-width: 720px;
}
.ace-hero-status {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
}
.ace-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: var(--ace-head-pill-bg);
    border: 1px solid var(--ace-head-pill-border);
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 500;
    color: var(--ace-head-text-secondary);
    transition: border-color 150ms cubic-bezier(0.16, 1, 0.3, 1);
}
.ace-status-pill:hover {
    border-color: var(--ace-head-pill-border-hover);
}
.ace-status-pill--needs-init {
    border-color: rgba(251, 191, 36, 0.35);
    background: rgba(251, 191, 36, 0.06);
    color: #fde68a;
}
.ace-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
}
.ace-dot--green {
    background: #34d399;
    box-shadow: 0 0 8px rgba(52, 211, 153, 0.55);
}
.ace-dot--amber {
    background: #fbbf24;
    box-shadow: 0 0 8px rgba(251, 191, 36, 0.55);
}
.ace-dot--blue {
    background: #60a5fa;
    box-shadow: 0 0 8px rgba(96, 165, 250, 0.55);
}
.ace-dot--grey {
    background: var(--ace-head-text-muted);
}

/* ---------- Responsive container ---------- */
@media (max-width: 1100px) {
    .gradio-container,
    .gradio-container.gradio-container-6-2-0 {
        padding: 16px 14px 40px 14px;
    }
    .ace-hero-title {
        font-size: 26px;
    }
    .ace-hero-status {
        gap: 6px;
    }
    .ace-status-pill {
        padding: 5px 10px;
        font-size: 11px;
    }
}
"""
