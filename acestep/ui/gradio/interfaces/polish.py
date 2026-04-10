"""Phase D — Visual polish for the ACE-Step Gradio UI.

A central CSS injection that overlays the ACEStepDark theme with the
finishing touches Gradio's defaults skip:

- Hero header with gradient title and subtitle hierarchy
- Accordion headers with icons, gradient backgrounds, hover states
- Form inputs with consistent sizing, focus rings, and label
  typography
- Buttons with consistent padding, hover/active feedback, smooth
  transitions, and clear primary vs secondary vs destructive variants
- Slider track and thumb that match the theme's primary blue
- Custom dark scrollbars throughout
- Negative space everywhere — Gradio default packs controls too
  tight to feel premium

The CSS lives in this module rather than ``tooltip_head.py`` so each
file stays focused: tooltips do the markdown bubble system, polish
does pure visual styling.
"""

from __future__ import annotations


def get_polish_css() -> str:
    """Return the polish CSS appended to the active Gradio stylesheet."""
    return _POLISH_CSS


_POLISH_CSS = """
/* ============================================================
   ACE-Step Phase D — UI Polish
   ============================================================ */

/* ---------- Design tokens ---------- */
:root {
    --ace-radius-sm: 8px;
    --ace-radius: 10px;
    --ace-radius-lg: 14px;
    --ace-radius-xl: 18px;
    --ace-shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.25);
    --ace-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    --ace-shadow-lg: 0 10px 30px rgba(0, 0, 0, 0.45);
    --ace-transition: 150ms cubic-bezier(0.16, 1, 0.3, 1);
    --ace-bg-elevated: rgba(30, 33, 45, 0.92);
    --ace-bg-subtle: rgba(20, 22, 32, 0.55);
    --ace-border-soft: rgba(255, 255, 255, 0.08);
    --ace-border: rgba(255, 255, 255, 0.12);
    --ace-border-strong: rgba(255, 255, 255, 0.2);
    --ace-text: #f4f4f5;
    --ace-text-muted: #a1a1aa;
    --ace-text-faint: #71717a;
    --ace-accent: #3b82f6;
    --ace-accent-soft: rgba(59, 130, 246, 0.18);
    --ace-accent-glow: rgba(59, 130, 246, 0.35);
    --ace-amber: #fbbf24;
    --ace-rose: #f43f5e;
    --ace-emerald: #34d399;
}

/* ---------- Body & containers ---------- */
.gradio-container {
    max-width: 1480px !important;
    margin: 0 auto !important;
    padding: 24px 28px 60px 28px !important;
    font-feature-settings: "ss01", "cv11";
}
body {
    background: radial-gradient(
        ellipse at top,
        #0f1117 0%,
        #08090d 65%
    ) !important;
}

/* ---------- Hero header (app title block) ---------- */
.gradio-container > .main > div:first-child h1,
.gradio-container > div > h1 {
    font-size: 32px !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
    margin: 6px 0 4px 0 !important;
    background: linear-gradient(
        135deg,
        #60a5fa 0%,
        #93c5fd 35%,
        #fbbf24 100%
    ) !important;
    -webkit-background-clip: text !important;
    background-clip: text !important;
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
}
.gradio-container > .main > div:first-child p,
.gradio-container > div > p {
    color: var(--ace-text-muted) !important;
    font-size: 14px !important;
    margin: 0 0 18px 0 !important;
    letter-spacing: 0.005em !important;
}

/* ---------- Tabs polish ---------- */
.tabs > .tab-nav {
    border-bottom: 1px solid var(--ace-border) !important;
    padding: 0 4px !important;
    gap: 4px !important;
}
.tabs > .tab-nav > button {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    color: var(--ace-text-muted) !important;
    padding: 12px 18px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: all var(--ace-transition) !important;
    border-radius: 0 !important;
}
.tabs > .tab-nav > button:hover {
    color: var(--ace-text) !important;
    background: rgba(255, 255, 255, 0.03) !important;
}
.tabs > .tab-nav > button.selected {
    color: var(--ace-accent) !important;
    border-bottom-color: var(--ace-accent) !important;
    background: transparent !important;
}

/* ---------- Accordions ---------- */
.gradio-accordion {
    border: 1px solid var(--ace-border) !important;
    border-radius: var(--ace-radius-lg) !important;
    background: var(--ace-bg-elevated) !important;
    box-shadow: var(--ace-shadow-sm) !important;
    margin: 14px 0 !important;
    overflow: hidden !important;
    transition: border-color var(--ace-transition),
                box-shadow var(--ace-transition) !important;
}
.gradio-accordion:hover {
    border-color: var(--ace-border-strong) !important;
}
.gradio-accordion > .label-wrap,
.gradio-accordion > button {
    padding: 14px 18px !important;
    background: linear-gradient(
        180deg,
        rgba(40, 44, 60, 0.85) 0%,
        rgba(30, 33, 45, 0.92) 100%
    ) !important;
    border-bottom: 1px solid var(--ace-border-soft) !important;
    transition: background var(--ace-transition) !important;
}
.gradio-accordion > .label-wrap:hover,
.gradio-accordion > button:hover {
    background: linear-gradient(
        180deg,
        rgba(50, 55, 75, 0.9) 0%,
        rgba(40, 44, 60, 0.95) 100%
    ) !important;
}
.gradio-accordion > .label-wrap > span,
.gradio-accordion > button > span {
    font-size: 14px !important;
    font-weight: 600 !important;
    color: var(--ace-text) !important;
    letter-spacing: 0.01em !important;
}
/* Nested accordions get a slightly less prominent background */
.gradio-accordion .gradio-accordion {
    background: rgba(25, 28, 38, 0.7) !important;
    border-color: rgba(255, 255, 255, 0.06) !important;
}

/* ---------- Form labels & info text ---------- */
span[data-testid="block-info"] {
    color: var(--ace-text) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    letter-spacing: 0.005em !important;
}
/* The native info paragraph is hidden by the tooltip system, so we
   only style the visible label-info span here. */

/* ---------- Inputs (textbox, number, dropdown) ---------- */
input[type="text"],
input[type="number"],
input[type="search"],
textarea {
    background: var(--ace-bg-subtle) !important;
    border: 1px solid var(--ace-border) !important;
    border-radius: var(--ace-radius-sm) !important;
    color: var(--ace-text) !important;
    padding: 9px 12px !important;
    font-size: 13px !important;
    transition: all var(--ace-transition) !important;
}
input[type="text"]::placeholder,
input[type="number"]::placeholder,
textarea::placeholder {
    color: var(--ace-text-faint) !important;
}
input[type="text"]:hover,
input[type="number"]:hover,
textarea:hover {
    border-color: var(--ace-border-strong) !important;
}
input[type="text"]:focus,
input[type="number"]:focus,
textarea:focus,
input[type="text"]:focus-visible,
textarea:focus-visible {
    outline: none !important;
    border-color: var(--ace-accent) !important;
    box-shadow: 0 0 0 3px var(--ace-accent-soft) !important;
}

/* Dropdowns inherit the same look */
.gradio-dropdown .wrap {
    background: var(--ace-bg-subtle) !important;
    border: 1px solid var(--ace-border) !important;
    border-radius: var(--ace-radius-sm) !important;
    transition: all var(--ace-transition) !important;
}
.gradio-dropdown .wrap:hover {
    border-color: var(--ace-border-strong) !important;
}
.gradio-dropdown:focus-within .wrap {
    border-color: var(--ace-accent) !important;
    box-shadow: 0 0 0 3px var(--ace-accent-soft) !important;
}

/* ---------- Buttons ---------- */
button.lg, button.gr-button-lg, button.large {
    padding: 12px 22px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
}
button.sm, button.gr-button-sm, button.small {
    padding: 6px 12px !important;
    font-size: 12.5px !important;
}
button.gradio-button,
button[class*="primary"],
button[class*="secondary"],
button[class*="stop"] {
    border-radius: var(--ace-radius-sm) !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
    transition: all var(--ace-transition) !important;
    box-shadow: var(--ace-shadow-sm) !important;
    border-width: 1px !important;
}
button.gradio-button:hover,
button[class*="primary"]:hover,
button[class*="secondary"]:hover,
button[class*="stop"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: var(--ace-shadow) !important;
}
button.gradio-button:active,
button[class*="primary"]:active,
button[class*="secondary"]:active,
button[class*="stop"]:active {
    transform: translateY(0) !important;
    box-shadow: var(--ace-shadow-sm) !important;
}
button:focus-visible {
    outline: none !important;
    box-shadow: 0 0 0 3px var(--ace-accent-soft), var(--ace-shadow) !important;
}

/* The big "Generate Music" button gets extra love */
#acestep-generate-btn {
    font-size: 16px !important;
    font-weight: 700 !important;
    padding: 16px 28px !important;
    background: linear-gradient(
        135deg,
        #2563eb 0%,
        #3b82f6 50%,
        #60a5fa 100%
    ) !important;
    border: none !important;
    box-shadow: 0 6px 18px rgba(59, 130, 246, 0.35) !important;
    letter-spacing: 0.015em !important;
    text-transform: none !important;
}
#acestep-generate-btn:hover {
    background: linear-gradient(
        135deg,
        #1d4ed8 0%,
        #3b82f6 50%,
        #60a5fa 100%
    ) !important;
    box-shadow: 0 10px 24px rgba(59, 130, 246, 0.5) !important;
    transform: translateY(-2px) !important;
}
#acestep-generate-btn:active {
    transform: translateY(0) !important;
}
#acestep-generate-btn:disabled {
    background: linear-gradient(
        135deg,
        rgba(59, 130, 246, 0.3) 0%,
        rgba(37, 99, 235, 0.3) 100%
    ) !important;
    box-shadow: none !important;
    cursor: not-allowed !important;
}

/* ---------- Sliders ---------- */
input[type="range"] {
    height: 6px !important;
}
input[type="range"]::-webkit-slider-runnable-track {
    background: linear-gradient(
        to right,
        var(--ace-accent) 0%,
        var(--ace-accent) var(--ace-slider-percent, 50%),
        rgba(255, 255, 255, 0.12) var(--ace-slider-percent, 50%),
        rgba(255, 255, 255, 0.12) 100%
    ) !important;
    height: 6px !important;
    border-radius: 3px !important;
}
input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none !important;
    appearance: none !important;
    width: 18px !important;
    height: 18px !important;
    border-radius: 50% !important;
    background: white !important;
    border: 2px solid var(--ace-accent) !important;
    cursor: pointer !important;
    margin-top: -6px !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4) !important;
    transition: transform var(--ace-transition),
                box-shadow var(--ace-transition) !important;
}
input[type="range"]::-webkit-slider-thumb:hover {
    transform: scale(1.15) !important;
    box-shadow: 0 0 0 6px var(--ace-accent-soft),
                0 2px 8px rgba(0, 0, 0, 0.5) !important;
}
input[type="range"]::-moz-range-track {
    background: rgba(255, 255, 255, 0.12) !important;
    height: 6px !important;
    border-radius: 3px !important;
}
input[type="range"]::-moz-range-thumb {
    width: 16px !important;
    height: 16px !important;
    border-radius: 50% !important;
    background: white !important;
    border: 2px solid var(--ace-accent) !important;
    cursor: pointer !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4) !important;
}

/* ---------- Checkboxes & radios ---------- */
input[type="checkbox"],
input[type="radio"] {
    accent-color: var(--ace-accent) !important;
    cursor: pointer !important;
    width: 16px !important;
    height: 16px !important;
}
label > input[type="checkbox"] + span,
label > input[type="radio"] + span {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: var(--ace-text) !important;
    margin-left: 6px !important;
}

/* ---------- Tab panels ---------- */
.gradio-container .tabitem {
    padding: 20px 0 !important;
}

/* ---------- Block titles ---------- */
.gradio-container span.svelte-1gfkn6j,
.gradio-container .gradio-markdown h1,
.gradio-container .gradio-markdown h2,
.gradio-container .gradio-markdown h3 {
    color: var(--ace-text) !important;
    font-weight: 700 !important;
    letter-spacing: -0.005em !important;
}

/* ---------- Status / progress textboxes ---------- */
input[readonly], textarea[readonly] {
    background: rgba(15, 17, 24, 0.7) !important;
    color: var(--ace-text-muted) !important;
    border-style: dashed !important;
    cursor: default !important;
}

/* ---------- Custom scrollbars ---------- */
*::-webkit-scrollbar {
    width: 10px !important;
    height: 10px !important;
}
*::-webkit-scrollbar-track {
    background: rgba(15, 17, 24, 0.4) !important;
    border-radius: 6px !important;
}
*::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.12) !important;
    border-radius: 6px !important;
    border: 2px solid transparent !important;
    background-clip: padding-box !important;
}
*::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.22) !important;
    background-clip: padding-box !important;
}

/* ---------- Audio player polish ---------- */
.gradio-audio {
    background: var(--ace-bg-elevated) !important;
    border: 1px solid var(--ace-border) !important;
    border-radius: var(--ace-radius) !important;
    padding: 8px !important;
}

/* ---------- Spacing rhythm ---------- */
.gradio-row {
    gap: 14px !important;
}
.gradio-column {
    gap: 12px !important;
}
.form > * + * {
    margin-top: 14px !important;
}

/* ---------- User mode radio (Beginner/Expert) ---------- */
#acestep-user-mode {
    background: linear-gradient(
        135deg,
        rgba(59, 130, 246, 0.08) 0%,
        rgba(251, 191, 36, 0.06) 100%
    ) !important;
    border: 1px solid rgba(59, 130, 246, 0.25) !important;
    border-radius: var(--ace-radius-lg) !important;
    padding: 14px 18px !important;
    margin: 4px 0 18px 0 !important;
}
#acestep-user-mode label {
    color: var(--ace-accent) !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    font-size: 11px !important;
}
#acestep-user-mode .wrap {
    gap: 12px !important;
}

/* ---------- Animated focus indicators for accessibility ---------- */
:focus-visible {
    outline: 2px solid var(--ace-accent) !important;
    outline-offset: 2px !important;
    transition: outline-offset 100ms ease-out !important;
}

/* ---------- Responsive: tighten spacing on narrow viewports ---------- */
@media (max-width: 1100px) {
    .gradio-container {
        padding: 16px 14px 40px 14px !important;
    }
    .gradio-accordion {
        margin: 10px 0 !important;
    }
}
"""
