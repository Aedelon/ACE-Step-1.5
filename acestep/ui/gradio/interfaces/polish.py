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

/* ---------- Accordions (Accordion.svelte: button.label-wrap inside .block) ----------
   The accordion header (button.label-wrap) is the biggest "label" in
   the whole app — there are 8+ sections and each header needs to
   feel like a real section divider, not a flat line of text.

   Design:
   - Subtle horizontal gradient so the header has visible depth
     against the darker block body below.
   - Thin accent bar on the left edge (4px) that lights up on hover
     and on open (:not([aria-expanded="false"])). Uses a box-shadow
     inset instead of a border so nothing pushes the label text
     horizontally when the bar turns on.
   - Bottom divider line only shown when the accordion is open so
     the closed state stays visually compact.
   - Chevron (Gradio's svg) picks up the accent color on hover.
*/
.block:has(> .label-wrap),
.block:has(> button.label-wrap) {
    border-radius: var(--ace-radius-lg);
    box-shadow: var(--ace-shadow-raised);
    transition: border-color var(--ace-duration-fast) var(--ace-easing-out),
                box-shadow var(--ace-duration-fast) var(--ace-easing-out);
}
.block:has(> .label-wrap):hover,
.block:has(> button.label-wrap):hover {
    border-color: var(--ace-border-strong);
    box-shadow: var(--ace-shadow-raised), 0 0 0 1px var(--ace-border-strong);
}

.label-wrap {
    position: relative;
    padding: 14px 18px 14px 22px;
    background: linear-gradient(
        180deg,
        rgba(255, 255, 255, 0.04) 0%,
        rgba(255, 255, 255, 0.015) 100%
    );
    border: none;
    border-radius: var(--ace-radius-lg) var(--ace-radius-lg) 0 0;
    /* 3px inset accent bar on the left edge, dim by default. */
    box-shadow: inset 3px 0 0 0 rgba(255, 255, 255, 0.08);
    transition: background var(--ace-duration-fast) var(--ace-easing-out),
                box-shadow var(--ace-duration-fast) var(--ace-easing-out);
}
.label-wrap:hover {
    background: linear-gradient(
        180deg,
        rgba(59, 130, 246, 0.08) 0%,
        rgba(59, 130, 246, 0.025) 100%
    );
    box-shadow: inset 3px 0 0 0 var(--ace-accent);
}
/* Accordion.svelte sets aria-expanded on the button.label-wrap.
   Open = "true" → keep the accent bar lit + add bottom divider. */
button.label-wrap[aria-expanded="true"] {
    background: linear-gradient(
        180deg,
        rgba(59, 130, 246, 0.06) 0%,
        rgba(59, 130, 246, 0.015) 100%
    );
    box-shadow:
        inset 3px 0 0 0 var(--ace-accent),
        inset 0 -1px 0 0 rgba(255, 255, 255, 0.06);
}
.label-wrap > span,
.label-wrap > .label-text {
    font-size: 14px;
    font-weight: 600;
    color: var(--ace-text-primary);
    letter-spacing: 0.005em;
}
/* Accordion chevron (the <svg> Gradio ships inside button.label-wrap)
   picks up the accent color on hover / open so the state change is
   obvious even without animation. */
.label-wrap svg,
.label-wrap > .icon {
    transition: transform var(--ace-duration-fast) var(--ace-easing-out),
                color var(--ace-duration-fast) var(--ace-easing-out);
}
.label-wrap:hover svg,
button.label-wrap[aria-expanded="true"] svg {
    color: var(--ace-accent);
}

/* ---------- Component labels (sliders / inputs / dropdowns)
   Gradio 6 renders <label> + a child span that carries the label
   text, plus a separate span[data-testid="block-info"] for the
   info= line. Lift the main label with slightly brighter text and
   a muted info line so the hierarchy reads: "parameter name"
   bigger, "what it does" dimmer.
*/
.block > label > span:not(.has-info) ,
.block > label > span.svelte-1gfkn6j,
label > span[data-testid="block-title"] {
    font-size: 12.5px;
    font-weight: 600;
    letter-spacing: 0.01em;
    color: var(--ace-text-primary);
    text-transform: none;
}
span[data-testid="block-info"] {
    font-size: 11.5px;
    font-weight: 400;
    color: var(--ace-text-secondary);
    letter-spacing: 0.005em;
    line-height: 1.45;
    margin-top: 2px;
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

/* ============================================================
   Migrated rules — used to live in gr.Blocks(css="…") inline
   in interfaces/__init__.py, but Gradio 6 IGNORES the Blocks
   constructor css= when launch(css=…) overrides it (verified
   in gradio/blocks.py:2566). Those rules never reached the
   browser in production. Bringing them here so the elem_classes
   they target actually get styled.
   ============================================================ */

/* Service init output: bigger, prominent, centred so the first-time
   user notices the init feedback. Still a Textbox so the textarea
   selector stays valid. */
#acestep-init-status {
    min-height: 100px;
}
#acestep-init-status textarea {
    font-size: 1.05rem;
    font-weight: 600;
    text-align: center;
    padding: 14px 16px;
    letter-spacing: 0.015em;
    min-height: 80px;
}

/* Generation status panel — now a gr.Markdown inside a gr.Group so
   status strings can render emojis + bold. The panel mimics a
   readonly card: soft border, subtle background, centred text. The
   heading sits on top with a muted uppercase label. */
.acestep-status-panel {
    background: var(--block-background-fill);
    border: 1px solid var(--border-color-primary);
    border-radius: 10px;
    padding: 10px 14px 14px 14px;
    margin-top: 8px;
}
.acestep-status-panel .acestep-status-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    opacity: 0.65;
    margin-bottom: 4px;
}
.acestep-status-panel .acestep-status-label h5 {
    margin: 0;
    font-size: inherit;
    font-weight: inherit;
    letter-spacing: inherit;
    text-transform: inherit;
}
#acestep-status-output {
    min-height: 48px;
    font-size: 1rem;
    font-weight: 500;
    line-height: 1.5;
    text-align: center;
    padding: 6px 4px 2px 4px;
}
#acestep-status-output p {
    margin: 4px 0;
}

/* Auto-toggle row under metadata fields (BPM Auto, Key Auto, …).
   Compact, centred, dimmed by default and full opacity on hover. */
.auto-toggles-row {
    margin-top: -8px !important;
    margin-bottom: 0 !important;
    padding: 0 !important;
    gap: 16px !important;
    min-height: 0 !important;
}
.auto-toggle {
    text-align: center;
}
.auto-toggle label {
    font-size: 0.8rem;
    gap: 4px;
    white-space: nowrap;
    cursor: pointer;
    opacity: 0.55;
    transition: opacity 0.15s var(--ace-easing-out);
    justify-content: center;
}
.auto-toggle:hover label,
.auto-toggle input[type="checkbox"]:checked + span {
    opacity: 1;
}
.auto-toggle input[type="checkbox"] {
    width: 13px;
    height: 13px;
}

/* Equal-height row for the Instrumental checkbox + Enhance Lyrics
   button so they sit on a single baseline at the bottom of the
   lyrics editor. */
.instrumental-row {
    align-items: stretch !important;
}
.instrumental-row > div {
    display: flex;
    align-items: stretch;
}
.instrumental-row > div > div {
    flex: 1;
    display: flex;
    align-items: center;
}
.instrumental-row button,
.instrumental-row > div > button {
    height: 100%;
    min-height: 42px;
}

/* Two-line icon button wrapper: emoji on top, text below. Used
   on the small Load / Save / Sample buttons next to file inputs. */
.icon-btn-wrap button,
.icon-btn-wrap > button {
    word-spacing: 100vw;
    text-align: center;
    line-height: 1.4;
}

/* Inline help button (?) created by help_content.create_help_button.
   Phase A's tooltip system hijacks the click to open a unified modal,
   but the visual chip itself still needs styling. */
.help-inline-container {
    min-height: 0;
    padding: 0;
    margin: 0;
    display: inline-flex;
    align-items: center;
    flex-shrink: 0;
    max-width: 32px;
    min-width: 32px;
    overflow: visible;
}
.help-inline-wrapper {
    display: inline-flex;
    align-items: center;
    line-height: 1;
}
.help-inline-btn {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    border: 1.5px solid var(--ace-border-default);
    background: transparent;
    color: var(--ace-text-secondary);
    font-size: 12px;
    font-weight: 600;
    line-height: 20px;
    text-align: center;
    cursor: pointer;
    padding: 0;
    transition: all 0.15s var(--ace-easing-out);
    flex-shrink: 0;
}
.help-inline-btn:hover {
    background: var(--ace-accent);
    color: #fff;
    border-color: var(--ace-accent);
    transform: scale(1.1);
}

/* ============================================================
   Phase D.4 — "Fais tout" polish additions
   ============================================================
   Everything below was added in response to a "what else would
   you improve" exchange. All selectors verified against Gradio
   6.2.0 frontend bundles:
     - Dropdown classes from Index-cUEohYhS.css (.select-wrap,
       .dropdown-arrow, .dropdown-filter-options, .filter-option)
     - Audio classes from StaticAudio-CCIOWZuh.css (.waveform-
       wrapper, .waveform-container, .play-pause-button,
       .component-wrapper, .controls)
*/

/* ---------- Dropdown / select polish ----------
   Gradio 6 renders gr.Dropdown as a .select-wrap div containing
   a text input (for the searchable variant) + a portal list
   (.dropdown-filter-options) populated with .filter-option items.
   The native HTML <select> is NOT used — which is why targeting
   `select {…}` had no effect in the previous polish pass.
*/
.select-wrap {
    background: var(--ace-bg-surface);
    border: 1px solid var(--ace-border-default);
    border-radius: var(--ace-radius-sm);
    transition: border-color var(--ace-duration-fast) var(--ace-easing-out),
                box-shadow var(--ace-duration-fast) var(--ace-easing-out);
}
.select-wrap:hover {
    border-color: var(--ace-border-strong);
}
.select-wrap:focus-within {
    border-color: var(--ace-accent);
    box-shadow: 0 0 0 3px var(--ace-accent-ring);
}
.select-wrap > input {
    /* The searchable text field inside the dropdown already matches
       the text-input rules above, but we want a tighter padding so
       the chevron sits flush on the right. */
    background: transparent;
    border: none;
    padding: 9px 34px 9px 12px;
    font-size: 13px;
    color: var(--ace-text-primary);
}
.select-wrap > input:focus {
    outline: none;
    box-shadow: none;
    border: none;
}
.dropdown-arrow {
    color: var(--ace-text-secondary);
    transition: transform var(--ace-duration-fast) var(--ace-easing-out),
                color var(--ace-duration-fast) var(--ace-easing-out);
    right: 10px;
}
.select-wrap:hover .dropdown-arrow,
.select-wrap:focus-within .dropdown-arrow {
    color: var(--ace-accent);
}
.dropdown-filter-options {
    background: var(--ace-bg-elevated);
    border: 1px solid var(--ace-border-default);
    border-radius: var(--ace-radius-sm);
    box-shadow: var(--ace-shadow-floating);
    padding: 4px;
    margin-top: 4px;
    max-height: 280px;
    overflow-y: auto;
}
.dropdown-filter-options > .filter-option {
    padding: 8px 12px;
    border-radius: var(--ace-radius-xs);
    font-size: 13px;
    color: var(--ace-text-primary);
    cursor: pointer;
    transition: background var(--ace-duration-fast) var(--ace-easing-out),
                color var(--ace-duration-fast) var(--ace-easing-out);
}
.dropdown-filter-options > .filter-option:hover {
    background: var(--ace-accent-soft);
    color: var(--ace-text-primary);
}
.dropdown-filter-options > .filter-option.selected {
    background: var(--ace-accent);
    color: #ffffff;
    font-weight: 600;
}

/* ---------- Number input steppers — hide the native spinner ----------
   The up/down micro-arrows next to <input type="number"> look cheap
   on a dark theme and conflict with Gradio's own +/- buttons on the
   slider variant. Hide them; users who need precision can type.
*/
input[type="number"]::-webkit-outer-spin-button,
input[type="number"]::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
}
input[type="number"] {
    -moz-appearance: textfield;
}

/* ---------- Monospace for numeric fields (slider values, seed) ----------
   Parameter values benefit from a monospaced readout so 1000 and 999
   visually align at the same width. Target only type="number" inputs;
   text inputs stay on the body font. */
input[type="number"] {
    font-family: "JetBrains Mono", "SF Mono", Menlo, ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
    letter-spacing: 0.01em;
}

/* ---------- Accordion closed-state hover lift ----------
   Closed accordions sit flat on the page with nothing telling the
   user they are clickable. A small 1px translateY on hover + a
   slightly stronger shadow adds just enough affordance without
   jumping the whole layout. Gradio sets aria-expanded="false" on
   the header button when the accordion is closed. */
.block:has(> button.label-wrap[aria-expanded="false"]):hover {
    transform: translateY(-1px);
    box-shadow:
        0 4px 12px rgba(0, 0, 0, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.06);
    transition: transform var(--ace-duration-fast) var(--ace-easing-out),
                box-shadow var(--ace-duration-fast) var(--ace-easing-out);
}

/* ---------- Accordion body fade-in on open ----------
   Gradio toggles the child .wrap display at open/close time with no
   animation — the body pops into place. Target the wrap when the
   parent's header is open and run a short slide+fade so opening a
   section feels considered. */
.block:has(> button.label-wrap[aria-expanded="true"]) > .wrap,
.block:has(> button.label-wrap[aria-expanded="true"]) > .form {
    animation: ace-accordion-reveal 240ms var(--ace-easing-out) both;
}
@keyframes ace-accordion-reveal {
    from {
        opacity: 0;
        transform: translateY(-4px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* ---------- Section headings inside accordions (Markdown h3/h4) ----------
   Subsections inside a long accordion (DiT body, LM body, Output body)
   use Markdown headings like `### Sampling` or `### Velocity tricks`.
   Default Markdown styling renders them as plain bold text, which
   blends with the surrounding sliders. Give them a distinct micro-
   label look: uppercase, letter-spaced, accent underline 2px. */
.tabitem h3,
.tabitem h4,
.acestep-subsection-heading {
    position: relative;
    display: inline-block;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 11.5px;
    font-weight: 700;
    color: var(--ace-text-secondary);
    padding: 0 0 6px 0;
    margin: 18px 0 10px 0;
    border: none;
}
.tabitem h3::after,
.tabitem h4::after,
.acestep-subsection-heading::after {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: 2px;
    background: linear-gradient(
        90deg,
        var(--ace-accent) 0%,
        rgba(59, 130, 246, 0.2) 100%
    );
    border-radius: 1px;
}

/* ---------- Section dividers between grouped rows ----------
   Long forms (DiT accordion, Output accordion) have 10+ sliders
   stacked on top of each other with no breathing room. Use a thin
   dashed divider between every .form > .block pair beyond the
   first so the eye can chunk them. Opted-out via `.no-divider`
   if the hierarchy calls for it. */
.form > .block + .block:not(.no-divider) {
    position: relative;
}
.form > .block + .block:not(.no-divider)::before {
    content: "";
    position: absolute;
    top: 0;
    left: 12px;
    right: 12px;
    height: 1px;
    background: rgba(255, 255, 255, 0.035);
    pointer-events: none;
}

/* ---------- Audio player polish ----------
   StaticAudio-CCIOWZuh.css ships the structure: .component-wrapper
   holds the whole player, .waveform-container hosts the canvas,
   .controls holds the play/pause + time + volume. Re-tint without
   touching the canvas drawing (that's JS-side). */
.component-wrapper:has(> .waveform-wrapper),
.component-wrapper:has(> .waveform-container) {
    background: var(--ace-bg-elevated);
    border: 1px solid var(--ace-border-subtle);
    border-radius: var(--ace-radius-md);
    padding: 8px;
    transition: border-color var(--ace-duration-fast) var(--ace-easing-out);
}
.component-wrapper:has(> .waveform-wrapper):hover,
.component-wrapper:has(> .waveform-container):hover {
    border-color: var(--ace-border-strong);
}
.waveform-container,
.waveform-wrapper {
    border-radius: var(--ace-radius-sm);
    overflow: hidden;
}
.play-pause-button {
    color: var(--ace-accent) !important;
    transition: transform var(--ace-duration-fast) var(--ace-easing-out);
}
.play-pause-button:hover {
    transform: scale(1.08);
}
.timestamps,
.timestamp {
    font-family: "JetBrains Mono", "SF Mono", Menlo, monospace;
    font-size: 11.5px;
    color: var(--ace-text-secondary);
    letter-spacing: 0;
}
.controls .volume input[type="range"] {
    /* The volume slider inherits our global range styling, but
       the track here is narrower and benefits from a thinner thumb. */
    max-width: 80px;
}

/* ---------- Init service status — terminal / log viewer look ----------
   The init Textbox is where the ~30s of first-run feedback lives.
   The textbox rendering is fine, but the surrounding block needs to
   feel more like a pro log viewer: monospace content, dim scanlines,
   and a subtle pulsing dot in the top-right so users know something
   is happening even while no new line is printed. */
#acestep-init-status {
    border-radius: var(--ace-radius-md);
    background:
        linear-gradient(
            180deg,
            rgba(15, 17, 24, 0.65) 0%,
            rgba(10, 11, 15, 0.65) 100%
        );
    border: 1px solid var(--ace-border-subtle);
    position: relative;
    overflow: hidden;
}
#acestep-init-status::before {
    /* 8px dot in the top-right that pulses while the init is running.
       We have no "is running" class pushed from Python, so the dot is
       always rendered — the pulse is cheap enough that it can stay
       on at rest without feeling noisy. */
    content: "";
    position: absolute;
    top: 10px;
    right: 12px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--ace-emerald);
    box-shadow: 0 0 10px rgba(52, 211, 153, 0.5);
    animation: ace-pulse-dot 1.8s ease-in-out infinite;
    z-index: 2;
}
@keyframes ace-pulse-dot {
    0%, 100% {
        opacity: 0.4;
        transform: scale(0.9);
    }
    50% {
        opacity: 1;
        transform: scale(1.1);
    }
}
#acestep-init-status textarea {
    font-family: "JetBrains Mono", "SF Mono", Menlo, ui-monospace, monospace !important;
    font-size: 12.5px !important;
    line-height: 1.55 !important;
    letter-spacing: 0 !important;
    text-align: left !important;
    background: transparent !important;
    color: var(--ace-text-primary) !important;
    padding: 14px 36px 14px 16px !important;
}

/* ---------- Results grid polish ----------
   Each generated-audio column is wrapped in .acestep-sample-col
   (applied via elem_classes in result.py::_create_audio_column)
   plus a .acestep-sample-label micro-header. Treat the whole
   column as a sample card: subtle bg + border on hover, tight
   padding so 4 cards fit across the tab width. */
.acestep-sample-col {
    padding: 12px 10px 8px 10px;
    border-radius: var(--ace-radius-md);
    border: 1px solid transparent;
    transition: background var(--ace-duration-fast) var(--ace-easing-out),
                border-color var(--ace-duration-fast) var(--ace-easing-out);
}
.acestep-sample-col:hover {
    background: rgba(255, 255, 255, 0.02);
    border-color: var(--ace-border-subtle);
}
/* Sample number micro-label: tighten the margin so it hugs the
   player above. Inherits uppercase / accent underline from
   .acestep-subsection-heading. */
.acestep-sample-label {
    margin-top: 0 !important;
    margin-bottom: 6px !important;
    padding-bottom: 4px !important;
    font-size: 10.5px !important;
    opacity: 0.75;
}
/* Fallback for columns that don't carry the elem_classes (e.g.
   older builds) — still catch them via :has() on waveforms so
   no sample stays visually bare. */
.column:has(> .block > .component-wrapper:has(.waveform-wrapper)):not(.acestep-sample-col) {
    padding: 10px 8px;
    border-radius: var(--ace-radius-md);
    transition: background var(--ace-duration-fast) var(--ace-easing-out);
}
.column:has(> .block > .component-wrapper:has(.waveform-wrapper)):not(.acestep-sample-col):hover {
    background: rgba(255, 255, 255, 0.015);
}

/* ---------- Display font on the hero title ----------
   The body uses Gradio's default Inter via the theme.py font list.
   The hero title deserves something with a bit more character —
   Space Grotesk is a display-friendly grotesk that pairs with
   Inter for body without clashing. Imported via polish_head.py
   (same file that carries the body backdrop + container rules)
   so @import and @font-face reach the browser unscoped. The
   class name ace-hero-title is applied in hero.py. */
.ace-hero-title {
    font-family: "Space Grotesk", "Inter", system-ui, -apple-system, sans-serif;
    font-weight: 700;
    letter-spacing: -0.025em;
}

/* ---------- Checkbox grid (service config toggles) ----------
   Previous attempts used ``div.acestep-checkbox-grid`` which has
   specificity 0-1-1 (1 class + 1 tag). Gradio 6 ships
   ``.gradio-container-6-2-0 .flex.svelte-239wnu`` = 0-3-0 which
   WINS the cascade even with !important (specificity beats
   !important ties). That's why the grid layout never applied —
   Daisy's screenshot showed a 500px flex row instead of a full-
   width grid.

   Fix: target the Row via elem_id — an ID selector has
   specificity 1-0-0, which beats any Gradio class combo.
   Two ids so we can evolve each group independently later:
     - #acestep-init-checkbox-grid (2 tiles)
     - #acestep-memory-checkbox-grid (5 tiles)

   Every cell gets the same width (1fr), every row the same
   height (align-items: stretch), auto-fill reflows extras onto
   a new line when the viewport can't fit another 240px column.
*/
#acestep-init-checkbox-grid,
#acestep-memory-checkbox-grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)) !important;
    width: 100% !important;
    max-width: none !important;
    gap: 10px !important;
    align-items: stretch !important;
    align-self: stretch !important;
    flex: 1 1 100% !important;
    flex-wrap: initial !important;
    flex-direction: initial !important;
    box-sizing: border-box !important;
}
/* Every direct child becomes a grid item. We target both ``.block``
   (the common case for gr.Checkbox) and ``> *`` (anything Gradio
   might wrap in, e.g. a Column or a plain div) so no sizing leaks
   from the Gradio flex defaults reach the tile. */
#acestep-init-checkbox-grid > *,
#acestep-memory-checkbox-grid > * {
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
    flex: initial !important;
}
#acestep-init-checkbox-grid > .block,
#acestep-memory-checkbox-grid > .block {
    /* Tile itself — column layout so the checkbox header sits at
       the top and the info line grows beneath. Fixed padding +
       border so every tile has an identical frame. */
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
    padding: 12px 14px !important;
    margin: 0 !important;
    border: 1px solid var(--ace-border-subtle) !important;
    border-radius: var(--ace-radius-md) !important;
    background: rgba(255, 255, 255, 0.012) !important;
    box-shadow: none !important;
    transition: background var(--ace-duration-fast) var(--ace-easing-out),
                border-color var(--ace-duration-fast) var(--ace-easing-out),
                box-shadow var(--ace-duration-fast) var(--ace-easing-out);
    /* Cancel Gradio's default flex-grow on block children so each
       tile occupies exactly one grid cell. Grid already handles
       stretching via align-items/grid-template-columns. */
    flex: initial !important;
    min-width: 0 !important;
    width: auto !important;
}
#acestep-init-checkbox-grid > .block:hover,
#acestep-memory-checkbox-grid > .block:hover {
    background: rgba(255, 255, 255, 0.035) !important;
    border-color: var(--ace-border-strong) !important;
}
/* Tile lights up when its checkbox is checked. Uses :has() against
   the nested input so no Python state change is needed — CSS-only. */
#acestep-init-checkbox-grid > .block:has(input[type="checkbox"]:checked),
#acestep-memory-checkbox-grid > .block:has(input[type="checkbox"]:checked) {
    background: rgba(59, 130, 246, 0.07) !important;
    border-color: rgba(59, 130, 246, 0.45) !important;
    box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.22) !important;
}
#acestep-init-checkbox-grid > .block:has(input[type="checkbox"]:checked:hover),
#acestep-memory-checkbox-grid > .block:has(input[type="checkbox"]:checked:hover) {
    background: rgba(59, 130, 246, 0.11) !important;
}
/* Disabled / non-interactive tile (e.g. flash_attention when the GPU
   cannot do it). Dim the whole tile so the user understands it's
   not something they can toggle. */
#acestep-init-checkbox-grid > .block:has(input[type="checkbox"]:disabled),
#acestep-memory-checkbox-grid > .block:has(input[type="checkbox"]:disabled) {
    opacity: 0.5 !important;
    cursor: not-allowed !important;
    background: rgba(255, 255, 255, 0.008) !important;
}
#acestep-init-checkbox-grid > .block:has(input[type="checkbox"]:disabled),
#acestep-memory-checkbox-grid > .block:has(input[type="checkbox"]:disabled):hover {
    background: rgba(255, 255, 255, 0.008) !important;
    border-color: var(--ace-border-subtle) !important;
    box-shadow: none !important;
}
/* Label row inside a tile: checkbox on the left, label text
   stretched across the remaining width. Fixed-height row so all
   tiles on a grid line share the same label baseline even if one
   label wraps to two lines and another fits on one. */
#acestep-init-checkbox-grid > .block > label,
#acestep-memory-checkbox-grid > .block > label {
    display: flex !important;
    align-items: flex-start !important;
    gap: 10px !important;
    cursor: pointer !important;
    padding: 0 !important;
    margin: 0 !important;
    min-height: 38px !important;  /* accommodates a 2-line wrapped label */
}
#acestep-init-checkbox-grid > .block > label > input[type="checkbox"],
#acestep-memory-checkbox-grid > .block > label > input[type="checkbox"] {
    flex-shrink: 0 !important;
    margin-top: 2px !important;
    width: 16px !important;
    height: 16px !important;
}
#acestep-init-checkbox-grid > .block > label > span,
#acestep-memory-checkbox-grid > .block > label > span {
    flex: 1 !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    line-height: 1.35 !important;
    color: var(--ace-text-primary) !important;
    /* Guarantee the label text area is the same height across tiles
       even if one wraps to two lines: reserves two lines worth of
       vertical space so the separator between label and info sits
       on the same baseline for every tile. */
    min-height: calc(1.35em * 2) !important;
}
/* Info line below the label — muted, indented 26px so it aligns
   past the checkbox. */
#acestep-init-checkbox-grid > .block > span[data-testid="block-info"],
#acestep-memory-checkbox-grid > .block > span[data-testid="block-info"] {
    margin: 8px 0 0 26px !important;
    font-size: 11.5px !important;
    font-weight: 400 !important;
    color: var(--ace-text-secondary) !important;
    line-height: 1.45 !important;
}

/* ---------- Color-coded status via first-character / content sniffing ----------
   The generation status panel pushes strings starting with ✅ / ❌ /
   ⚠️ / ⏳ but Markdown renders them as plain text. CSS can't parse
   text directly, but we can use a clever trick: each status string
   becomes a first paragraph inside #acestep-status-output, so we
   tint the whole paragraph based on explicit marker classes that
   handlers can opt into later. For now, give the default paragraph
   a soft outline to feel like a real "status chip".

   Until handlers start wrapping their strings with .status-ok /
   .status-err / .status-warn classes, the base rule just provides
   a consistent visual treatment for every status line. */
#acestep-status-output p {
    display: inline-block;
    max-width: 100%;
    padding: 4px 10px;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--ace-border-subtle);
    margin: 4px auto;
}
#acestep-status-output p:has(> .status-ok),
#acestep-status-output .status-ok {
    background: rgba(52, 211, 153, 0.08);
    border-color: rgba(52, 211, 153, 0.28);
    color: var(--ace-emerald);
}
#acestep-status-output p:has(> .status-err),
#acestep-status-output .status-err {
    background: rgba(244, 63, 94, 0.08);
    border-color: rgba(244, 63, 94, 0.28);
    color: var(--ace-rose);
}
#acestep-status-output p:has(> .status-warn),
#acestep-status-output .status-warn {
    background: rgba(251, 191, 36, 0.08);
    border-color: rgba(251, 191, 36, 0.28);
    color: var(--ace-amber);
}
"""
