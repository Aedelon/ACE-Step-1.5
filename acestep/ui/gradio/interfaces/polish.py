"""Phase D — Visual polish for the ACE-Step Gradio UI.

Sérieuse réécriture après audit anti-hallucination des sélecteurs Gradio
6.2.0 contre la source officielle (Embed.svelte, Block.svelte, Tabs.svelte,
Accordion.svelte, Button.svelte, etc.). Le précédent polish utilisait des
classes inventées (`.gradio-accordion`, `.gradio-button`, `.gradio-row`)
qui n'existent pas dans Gradio 6 — c'est pour ça qu'aucune règle ne
s'appliquait correctement.

Les **vrais** sélecteurs Gradio 6.2 (vérifiés contre js/ source) :

- ``.gradio-container.gradio-container-{version}`` : div racine, présente
  dans ``Embed.svelte``. Mais ``css=`` est wrappé par ``prefix_css`` qui
  scope tout sous ``.gradio-container .contain``, donc cibler ``body`` ou
  ``:root`` depuis ``css=`` ne marche pas — il faut passer par ``head=``.
- ``.block`` : wrapper de TOUT composant Gradio (Block.svelte)
- ``.label-wrap`` : button qui sert d'entête d'``Accordion`` (Accordion.svelte)
- ``.tabs > .tab-wrapper > .tab-container > button.selected`` : nav des tabs
- ``.tabitem`` : panneau d'onglet (TabItem.svelte)
- ``.row`` / ``.column`` / ``.form`` : Row/Column/Form natifs
- ``button.primary`` / ``button.secondary`` / ``button.stop`` : variants
- ``button.sm`` / ``button.md`` / ``button.lg`` : sizes
- ``span[data-testid="block-info"]`` : label slot des composants
- ``input[type="range"]`` / ``--range_progress`` : slider natif (la var
  ``--ace-slider-percent`` du précédent polish n'existait pas)

Tokens : on aligne sur les variables Gradio natives plutôt que de
dupliquer (theme.py les expose déjà via ``set()``).
"""

from __future__ import annotations


def get_polish_css() -> str:
    """Return the polish CSS appended after the tooltip CSS in
    ``get_acestep_css()``."""
    return _POLISH_CSS


_POLISH_CSS = """
/* ============================================================
   ACE-Step Phase D — UI Polish (Gradio 6.2.0 verified selectors)
   ============================================================ */

/* ---------- Design tokens (aligned on Gradio native vars) ----- */
.gradio-container {
    --ace-radius-xs: 4px;
    --ace-radius-sm: 6px;
    --ace-radius-md: 8px;
    --ace-radius-lg: 12px;
    --ace-radius-xl: 16px;

    --ace-space-1: 4px;
    --ace-space-2: 8px;
    --ace-space-3: 12px;
    --ace-space-4: 16px;
    --ace-space-5: 20px;
    --ace-space-6: 24px;
    --ace-space-8: 32px;

    --ace-shadow-raised:
        0 1px 2px rgba(0, 0, 0, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.04);
    --ace-shadow-floating:
        0 8px 16px rgba(0, 0, 0, 0.5),
        0 2px 4px rgba(0, 0, 0, 0.3);
    --ace-shadow-cta:
        0 4px 14px rgba(59, 130, 246, 0.35),
        0 1px 2px rgba(0, 0, 0, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.12);

    --ace-duration-fast: 150ms;
    --ace-duration-base: 200ms;
    --ace-easing-out: cubic-bezier(0.16, 1, 0.3, 1);
    --ace-easing-standard: cubic-bezier(0.4, 0, 0.2, 1);

    /* Re-export Gradio's own tokens under our namespace so future code
       can reference them without having to know whether the value lives
       in theme.py or polish.py. */
    --ace-text-primary: var(--body-text-color);
    --ace-text-secondary: var(--body-text-color-subdued);
    --ace-text-muted: var(--input-placeholder-color);
    --ace-bg-canvas: var(--body-background-fill);
    --ace-bg-surface: var(--block-background-fill);
    --ace-bg-elevated: var(--background-fill-secondary);
    --ace-border-subtle: rgba(255, 255, 255, 0.06);
    --ace-border-default: var(--border-color-primary);
    --ace-border-strong: var(--input-border-color);
    --ace-accent: var(--color-accent);
    --ace-accent-soft: rgba(59, 130, 246, 0.18);
    --ace-accent-ring: rgba(59, 130, 246, 0.35);
    --ace-amber: #fbbf24;
    --ace-rose: #f43f5e;
    --ace-emerald: #34d399;
}

/* ---------- Typography polish on labels ---------- */
span[data-testid="block-info"] {
    color: var(--ace-text-primary);
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.005em;
}

/* ---------- Tabs (Tabs.svelte structure) ---------- */
.tabs > .tab-wrapper > .tab-container {
    border-bottom: 1px solid var(--ace-border-default);
    padding: 0 var(--ace-space-1);
    gap: var(--ace-space-1);
}
.tabs > .tab-wrapper > .tab-container > button {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--ace-text-secondary);
    padding: var(--ace-space-3) var(--ace-space-5);
    font-weight: 600;
    font-size: 14px;
    transition: color var(--ace-duration-fast) var(--ace-easing-out),
                border-color var(--ace-duration-fast) var(--ace-easing-out);
    border-radius: 0;
}
.tabs > .tab-wrapper > .tab-container > button:hover {
    color: var(--ace-text-primary);
}
.tabs > .tab-wrapper > .tab-container > button.selected {
    color: var(--ace-accent);
    border-bottom-color: var(--ace-accent);
}

/* ---------- Accordions (Accordion.svelte: button.label-wrap inside .block) ---------- */
.block:has(> .label-wrap),
.block:has(> button.label-wrap) {
    border-radius: var(--ace-radius-lg);
    box-shadow: var(--ace-shadow-raised);
    transition: border-color var(--ace-duration-fast) var(--ace-easing-out);
}
.block:has(> .label-wrap):hover,
.block:has(> button.label-wrap):hover {
    border-color: var(--ace-border-strong);
}
.label-wrap {
    padding: var(--ace-space-4) var(--ace-space-5);
    background: transparent;
    border: none;
    transition: background var(--ace-duration-fast) var(--ace-easing-out);
}
.label-wrap:hover {
    background: rgba(255, 255, 255, 0.025);
}
.label-wrap > span,
.label-wrap > .label-text {
    font-size: 14px;
    font-weight: 600;
    color: var(--ace-text-primary);
    letter-spacing: 0.005em;
}

/* ---------- Inputs (textarea, input[type="text"], input[type="number"]) ---------- */
input[type="text"],
input[type="number"],
input[type="search"],
textarea {
    background: var(--ace-bg-surface);
    border: 1px solid var(--ace-border-default);
    border-radius: var(--ace-radius-sm);
    color: var(--ace-text-primary);
    padding: 9px 12px;
    font-size: 13px;
    transition: border-color var(--ace-duration-fast) var(--ace-easing-out),
                box-shadow var(--ace-duration-fast) var(--ace-easing-out);
}
input[type="text"]::placeholder,
input[type="number"]::placeholder,
textarea::placeholder {
    color: var(--ace-text-muted);
}
input[type="text"]:hover,
input[type="number"]:hover,
textarea:hover {
    border-color: var(--ace-border-strong);
}
input[type="text"]:focus,
input[type="number"]:focus,
textarea:focus {
    outline: none;
    border-color: var(--ace-accent);
    box-shadow: 0 0 0 3px var(--ace-accent-ring);
}
input[readonly],
textarea[readonly] {
    background: rgba(15, 17, 24, 0.7);
    color: var(--ace-text-secondary);
    border-style: dashed;
    cursor: default;
}

/* ---------- Buttons (Button.svelte: .primary / .secondary / .stop + .sm / .md / .lg) ---------- */
button.primary,
button.secondary,
button.stop {
    border-radius: var(--ace-radius-sm);
    font-weight: 600;
    letter-spacing: 0.01em;
    transition: background var(--ace-duration-fast) var(--ace-easing-out),
                border-color var(--ace-duration-fast) var(--ace-easing-out),
                color var(--ace-duration-fast) var(--ace-easing-out);
    box-shadow: var(--ace-shadow-raised);
}
button.lg {
    padding: 12px 22px;
    font-size: 14px;
}
button.sm {
    padding: 6px 12px;
    font-size: 12.5px;
}

/* ---------- Generate Music CTA (the only button with hover lift) ---------- */
#acestep-generate-btn {
    min-width: 240px;
    height: 52px;
    padding: 16px 32px;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 0.01em;
    color: #ffffff;
    background: #3b82f6;
    border: none;
    border-radius: var(--ace-radius-md);
    box-shadow: var(--ace-shadow-cta);
    transition: background var(--ace-duration-fast) var(--ace-easing-out),
                box-shadow var(--ace-duration-fast) var(--ace-easing-out),
                transform var(--ace-duration-fast) var(--ace-easing-out);
    cursor: pointer;
}
#acestep-generate-btn:hover:not(:disabled) {
    background: #60a5fa;
    box-shadow:
        0 6px 20px rgba(59, 130, 246, 0.5),
        0 2px 4px rgba(0, 0, 0, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.16);
    transform: translateY(-1px);
}
#acestep-generate-btn:active:not(:disabled) {
    background: #2563eb;
    transform: translateY(0);
}
#acestep-generate-btn:disabled {
    background: #3f3f46;
    color: #71717a;
    box-shadow: none;
    cursor: not-allowed;
    transform: none;
}
#acestep-generate-btn.is-loading {
    background: #1e40af;
    cursor: progress;
    pointer-events: none;
}
#acestep-generate-btn.is-loading::before {
    content: "";
    display: inline-block;
    width: 16px;
    height: 16px;
    margin-right: 10px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: #ffffff;
    border-radius: 50%;
    animation: ace-spin 0.8s linear infinite;
    vertical-align: -2px;
}
@keyframes ace-spin {
    to { transform: rotate(360deg); }
}

/* ---------- Slider (input[type="range"], --range_progress is set by Gradio JS) ---------- */
input[type="range"] {
    height: 6px;
}
input[type="range"]::-webkit-slider-runnable-track {
    background: linear-gradient(
        to right,
        var(--ace-accent) 0%,
        var(--ace-accent) var(--range_progress, 50%),
        rgba(255, 255, 255, 0.12) var(--range_progress, 50%),
        rgba(255, 255, 255, 0.12) 100%
    );
    height: 6px;
    border-radius: 3px;
}
input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: white;
    border: 2px solid var(--ace-accent);
    cursor: pointer;
    margin-top: -6px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
    transition: transform var(--ace-duration-fast) var(--ace-easing-out);
}
input[type="range"]::-webkit-slider-thumb:hover {
    transform: scale(1.15);
    box-shadow: 0 0 0 6px var(--ace-accent-ring),
                0 2px 8px rgba(0, 0, 0, 0.5);
}
input[type="range"]::-moz-range-track {
    background: rgba(255, 255, 255, 0.12);
    height: 6px;
    border-radius: 3px;
}
input[type="range"]::-moz-range-thumb {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: white;
    border: 2px solid var(--ace-accent);
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
}

/* ---------- Checkboxes & radios ---------- */
input[type="checkbox"],
input[type="radio"] {
    accent-color: var(--ace-accent);
    cursor: pointer;
    width: 16px;
    height: 16px;
}

/* ---------- Spacing rhythm on Gradio-real selectors ---------- */
.row {
    gap: 14px;
}
.column {
    gap: 12px;
}
.tabitem {
    padding: 20px 0;
}

/* ---------- User mode radio (Beginner/Expert) — sober card, NOT a gradient ---------- */
#acestep-user-mode {
    background: var(--ace-bg-surface);
    border: 1px solid var(--ace-border-subtle);
    border-radius: var(--ace-radius-lg);
    padding: 12px 16px;
    margin: 12px 0 20px 0;
    box-shadow: var(--ace-shadow-raised);
}
#acestep-user-mode > label,
#acestep-user-mode .label-wrap > span {
    color: var(--ace-text-secondary);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-size: 11px;
}
#acestep-user-mode input[type="radio"]:checked + span {
    color: var(--ace-accent);
    font-weight: 700;
}

/* ---------- LoRA empty state (no Python required) ---------- */
.acestep-lora-rows:empty::before {
    content: "No adapters loaded — add a path above and click Add LoRA";
    display: block;
    text-align: center;
    padding: 20px;
    color: var(--ace-text-muted);
    font-size: 12.5px;
    font-style: italic;
    border: 1px dashed var(--ace-border-default);
    border-radius: var(--ace-radius-sm);
    margin: 8px 0;
}

/* ---------- Custom dark scrollbars (global) ---------- */
*::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}
*::-webkit-scrollbar-track {
    background: rgba(15, 17, 24, 0.4);
    border-radius: 6px;
}
*::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.12);
    border-radius: 6px;
    border: 2px solid transparent;
    background-clip: padding-box;
}
*::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.22);
    background-clip: padding-box;
}

/* ---------- Accessibility focus ring (keyboard nav) ---------- */
button:focus-visible,
input:focus-visible,
textarea:focus-visible,
select:focus-visible,
[tabindex]:focus-visible {
    outline: 2px solid var(--ace-accent);
    outline-offset: 2px;
    transition: outline-offset 100ms ease-out;
}

/* ---------- Responsive: tighten spacing on narrow viewports ---------- */
@media (max-width: 1100px) {
    .block:has(> .label-wrap),
    .block:has(> button.label-wrap) {
        margin: 10px 0;
    }
    #acestep-generate-btn {
        min-width: 100%;
    }
}
"""
