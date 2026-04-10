"""ACE-Step custom tooltip system.

Provides a robust hover tooltip system using opt-in via the `acestep-tt`
CSS class. The tooltip layer lives as a direct child of <body> in
position:fixed to escape all stacking contexts created by Gradio's nested
divs (transform, opacity, contain).

Why opt-in:
    The previous tooltip system used `has-info-container` which was
    applied to many elements including Accordions and Groups. CSS
    selectors targeting descendants of `.has-info-container` ended up
    matching live components and hiding them. This system uses a strict
    opt-in marker `acestep-tt` placed ONLY on leaf components (Slider,
    Dropdown, Checkbox, Number, Textbox).

How it works:
    1. CSS injects styles for `.acestep-info-icon` (the visible ?) and
       `#acestep-tooltip-layer` (the popup container in <body>).
    2. JS scans `document.querySelectorAll('.acestep-tt')` and finds
       each `span[data-testid="block-info"]` inside.
    3. Hides the native info span and creates a sibling `<button>`
       with the info text stored in `data-tooltip`.
    4. On mouseenter, positions the tooltip layer using
       getBoundingClientRect() relative to the trigger button.
    5. Auto-flips to above the trigger when there's not enough room
       below.
    6. 200ms grace period on mouseleave so the user can move into the
       tooltip and scroll long content.
    7. MutationObserver covers components added dynamically (e.g. when
       a mode change reveals new components).
"""


def get_tooltip_head() -> str:
    """Return the HTML string to inject into the Gradio Blocks head=.

    The string contains a <style> block and a <script> block that
    together implement the opt-in hover tooltip system.

    Returns:
        HTML string ready for concatenation with other head= content.
    """
    return _TOOLTIP_HEAD


_TOOLTIP_HEAD = """
<style>
/* ===== ACE-Step Tooltip System ===== */

/* The (?) icon button placed next to each label */
.acestep-info-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    margin-left: 6px;
    padding: 0;
    border: 1px solid var(--border-color-primary, #555);
    background: transparent;
    color: var(--body-text-color-subdued, #aaa);
    font-size: 11px;
    font-weight: 600;
    line-height: 1;
    cursor: help;
    font-family: inherit;
    vertical-align: middle;
    transition: all 0.15s ease;
    flex-shrink: 0;
}
.acestep-info-icon:hover {
    color: #fff;
    border-color: #3b82f6;
    background: #3b82f6;
    transform: scale(1.1);
}

/* The tooltip popup layer (lives in <body>, position: fixed) */
#acestep-tooltip-layer {
    position: fixed;
    z-index: 999999;
    max-width: 360px;
    max-height: 60vh;
    overflow-y: auto;
    padding: 12px 16px;
    border-radius: 8px;
    background: rgba(20, 20, 30, 0.98);
    color: #f0f0f0;
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
    font-size: 13px;
    line-height: 1.5;
    font-weight: 400;
    pointer-events: auto;
    display: none;
    backdrop-filter: blur(10px);
}
#acestep-tooltip-layer.visible {
    display: block;
}
#acestep-tooltip-layer::-webkit-scrollbar {
    width: 8px;
}
#acestep-tooltip-layer::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
}
</style>
<script>
(function() {
    'use strict';
    const LAYER_ID = 'acestep-tooltip-layer';
    const HOST_SELECTOR = '.acestep-tt';
    const HIDE_DELAY_MS = 200;
    let hideTimer = null;

    /** Create or return the singleton tooltip layer attached to <body>. */
    function ensureLayer() {
        let layer = document.getElementById(LAYER_ID);
        if (!layer) {
            layer = document.createElement('div');
            layer.id = LAYER_ID;
            document.body.appendChild(layer);
            // Keep layer visible while user hovers it (to scroll long content)
            layer.addEventListener('mouseenter', () => {
                if (hideTimer) {
                    clearTimeout(hideTimer);
                    hideTimer = null;
                }
            });
            layer.addEventListener('mouseleave', scheduleHide);
        }
        return layer;
    }

    function scheduleHide() {
        if (hideTimer) clearTimeout(hideTimer);
        hideTimer = setTimeout(() => {
            const layer = document.getElementById(LAYER_ID);
            if (layer) layer.classList.remove('visible');
        }, HIDE_DELAY_MS);
    }

    function showTooltip(triggerEl) {
        if (hideTimer) {
            clearTimeout(hideTimer);
            hideTimer = null;
        }
        const layer = ensureLayer();
        const text = triggerEl.getAttribute('data-tooltip') || '';
        if (!text) return;

        layer.textContent = text;
        layer.classList.add('visible');

        // Position relative to trigger using viewport coordinates
        const rect = triggerEl.getBoundingClientRect();
        const vh = window.innerHeight;
        const vw = window.innerWidth;
        const TOOLTIP_MAX_W = 380;

        // Horizontal: clamp inside viewport with 8px margin
        const left = Math.max(8, Math.min(rect.left, vw - TOOLTIP_MAX_W - 8));
        layer.style.left = left + 'px';

        // Vertical: prefer below, flip above if not enough room
        const belowRoom = vh - rect.bottom;
        if (belowRoom > 220 || belowRoom > vh * 0.4) {
            layer.style.top = (rect.bottom + 6) + 'px';
            layer.style.bottom = '';
        } else {
            layer.style.top = '';
            layer.style.bottom = (vh - rect.top + 6) + 'px';
        }
    }

    /** Upgrade a single .acestep-tt host element to display a hover icon. */
    function upgradeHost(host) {
        if (host.dataset.acestepTtUpgraded === '1') return;

        // Find the native info span Gradio created from the info= prop.
        // Critical: the span must "belong" to THIS host, not to a nested
        // acestep-tt descendant (e.g. an accordion containing sliders).
        const candidates = host.querySelectorAll('span[data-testid="block-info"]');
        let infoSpan = null;
        for (const candidate of candidates) {
            if (candidate.closest(HOST_SELECTOR) === host) {
                infoSpan = candidate;
                break;
            }
        }
        if (!infoSpan) {
            // Mark as scanned so we don't retry on every observer tick.
            host.dataset.acestepTtUpgraded = '1';
            return;
        }

        const text = (infoSpan.textContent || '').trim();
        if (!text) return;

        host.dataset.acestepTtUpgraded = '1';

        // Hide the native info span (don't remove — Gradio may re-render)
        infoSpan.style.display = 'none';

        // Find the label to attach the icon to
        const label = host.querySelector('label, .label-wrap, .block-title');
        if (!label) return;

        // Avoid duplicates
        if (label.querySelector('.acestep-info-icon')) return;

        // Create the (?) button
        const icon = document.createElement('button');
        icon.type = 'button';
        icon.className = 'acestep-info-icon';
        icon.textContent = '?';
        icon.setAttribute('aria-label', 'Help: ' + text.substring(0, 50));
        icon.setAttribute('data-tooltip', text);
        icon.tabIndex = 0;

        // Hover events
        icon.addEventListener('mouseenter', () => showTooltip(icon));
        icon.addEventListener('mouseleave', scheduleHide);
        // Keyboard accessibility
        icon.addEventListener('focus', () => showTooltip(icon));
        icon.addEventListener('blur', scheduleHide);
        // Click toggles (for touch devices)
        icon.addEventListener('click', (e) => {
            e.preventDefault();
            const layer = document.getElementById(LAYER_ID);
            if (layer && layer.classList.contains('visible') &&
                layer.textContent === text) {
                scheduleHide();
            } else {
                showTooltip(icon);
            }
        });

        label.appendChild(icon);
    }

    /** Scan a root element and upgrade all .acestep-tt descendants. */
    function scanAndUpgrade(root) {
        if (!root || !root.querySelectorAll) return;
        const hosts = root.querySelectorAll(HOST_SELECTOR);
        hosts.forEach(upgradeHost);
    }

    /** MutationObserver to handle dynamically added components. */
    function startObserver() {
        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) {
                        // Element node
                        if (node.matches && node.matches(HOST_SELECTOR)) {
                            upgradeHost(node);
                        }
                        scanAndUpgrade(node);
                    }
                });
            }
        });
        observer.observe(document.body, {
            childList: true,
            subtree: true,
        });
    }

    function init() {
        scanAndUpgrade(document);
        startObserver();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
</script>
"""
