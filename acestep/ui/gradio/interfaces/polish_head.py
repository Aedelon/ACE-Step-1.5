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

/* ---------- Hero section (#acestep-hero from build_hero_section) ---------- */
#acestep-hero {
    padding: 24px 4px 28px 4px;
    margin-bottom: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.ace-hero-eyebrow {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #71717a;
    margin: 0 0 10px 0;
}
.ace-hero-title {
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin: 0 0 6px 0;
    color: #fafafa;
    line-height: 1.15;
}
.ace-hero-subtitle {
    color: #a1a1aa;
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
    background: rgba(24, 24, 27, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 500;
    color: #d4d4d8;
    transition: border-color 150ms cubic-bezier(0.16, 1, 0.3, 1);
}
.ace-status-pill:hover {
    border-color: rgba(255, 255, 255, 0.15);
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
    background: #71717a;
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
