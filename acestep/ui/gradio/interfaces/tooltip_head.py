"""ACE-Step custom tooltip system.

Provides a robust hover tooltip system using opt-in via the `acestep-tt`
CSS class. The tooltip layer lives as a direct child of <body> in
position:fixed to escape all stacking contexts created by Gradio's nested
divs (transform, opacity, contain).

Why this exists:
    Gradio 6 has no native tooltip component. Components only support
    `info=` which renders as static text below the label. We want hover
    tooltips on a (?) icon next to the label.

Why opt-in via class:
    The previous tooltip system used `has-info-container` which was
    applied to many elements including Accordions. CSS selectors targeting
    descendants of `.has-info-container` ended up matching live components
    and hiding them. This system uses a strict opt-in marker `acestep-tt`
    placed on Slider/Dropdown/Checkbox/Number/Textbox components, and
    the JS uses `closest()` to ensure each info span belongs to the right
    host (preventing accordion-level upgrades).

Why CSS and JS are exposed separately:
    In Gradio 6, head=/css=/js= must be passed to demo.launch(), not to
    gr.Blocks(). Crucially, <script> tags inside head= are inserted via
    innerHTML and therefore NEVER execute (HTML5 spec). The js= parameter
    is the ONLY way to run custom JavaScript on page load. We expose
    get_tooltip_css() for the css= parameter and get_tooltip_js() for the
    js= parameter so they can be passed correctly at launch time.
"""


def get_tooltip_css() -> str:
    """Return the CSS for the tooltip system, suitable for css= parameter."""
    return _TOOLTIP_CSS


def get_tooltip_js() -> str:
    """Return a JavaScript function string suitable for the js= parameter.

    The js= parameter expects a JavaScript function expression. This function
    is called once on page load. We use it to install the tooltip system,
    then start a MutationObserver for dynamically added components.
    """
    return _TOOLTIP_JS


def get_tooltip_head() -> str:
    """[DEPRECATED] Return tooltip CSS+JS as a single <style>+<script> string.

    Kept for backward compatibility. Prefer get_tooltip_css() and
    get_tooltip_js() for Gradio 6 launch(css=..., js=...).
    """
    return f"<style>{_TOOLTIP_CSS}</style>\n<script>{_TOOLTIP_JS_INLINE}</script>"


_TOOLTIP_CSS = """
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

/* Hide native Gradio info span when our tooltip system has upgraded it */
.acestep-tt span[data-testid="block-info"].acestep-tt-hidden {
    display: none !important;
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
"""


# JavaScript wrapped as a function expression for the js= parameter.
# Gradio passes this string to the browser and calls it as `(function...)()`.
_TOOLTIP_JS = """
() => {
    'use strict';
    const LAYER_ID = 'acestep-tooltip-layer';
    const HOST_SELECTOR = '.acestep-tt';
    const HIDE_DELAY_MS = 200;
    let hideTimer = null;

    function ensureLayer() {
        let layer = document.getElementById(LAYER_ID);
        if (!layer) {
            layer = document.createElement('div');
            layer.id = LAYER_ID;
            document.body.appendChild(layer);
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

        const rect = triggerEl.getBoundingClientRect();
        const vh = window.innerHeight;
        const vw = window.innerWidth;
        const TOOLTIP_MAX_W = 380;

        const left = Math.max(8, Math.min(rect.left, vw - TOOLTIP_MAX_W - 8));
        layer.style.left = left + 'px';

        const belowRoom = vh - rect.bottom;
        if (belowRoom > 220 || belowRoom > vh * 0.4) {
            layer.style.top = (rect.bottom + 6) + 'px';
            layer.style.bottom = '';
        } else {
            layer.style.top = '';
            layer.style.bottom = (vh - rect.top + 6) + 'px';
        }
    }

    function upgradeHost(host) {
        if (host.dataset.acestepTtUpgraded === '1') return;

        const candidates = host.querySelectorAll('span[data-testid="block-info"]');
        let infoSpan = null;
        for (const candidate of candidates) {
            if (candidate.closest(HOST_SELECTOR) === host) {
                infoSpan = candidate;
                break;
            }
        }
        if (!infoSpan) {
            host.dataset.acestepTtUpgraded = '1';
            return;
        }

        const text = (infoSpan.textContent || '').trim();
        if (!text) {
            host.dataset.acestepTtUpgraded = '1';
            return;
        }

        host.dataset.acestepTtUpgraded = '1';
        infoSpan.classList.add('acestep-tt-hidden');

        const label = host.querySelector('label, .label-wrap, .block-title');
        if (!label) return;
        if (label.querySelector('.acestep-info-icon')) return;

        const icon = document.createElement('button');
        icon.type = 'button';
        icon.className = 'acestep-info-icon';
        icon.textContent = '?';
        icon.setAttribute('aria-label', 'Help: ' + text.substring(0, 50));
        icon.setAttribute('data-tooltip', text);
        icon.tabIndex = 0;

        icon.addEventListener('mouseenter', () => showTooltip(icon));
        icon.addEventListener('mouseleave', scheduleHide);
        icon.addEventListener('focus', () => showTooltip(icon));
        icon.addEventListener('blur', scheduleHide);
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

    function scanAndUpgrade(root) {
        if (!root || !root.querySelectorAll) return;
        const hosts = root.querySelectorAll(HOST_SELECTOR);
        hosts.forEach(upgradeHost);
    }

    function startObserver() {
        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) {
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

    // Run scan now and start observer
    scanAndUpgrade(document);
    startObserver();

    // Run a delayed second scan to catch components that mount after this js= callback
    setTimeout(() => scanAndUpgrade(document), 500);
    setTimeout(() => scanAndUpgrade(document), 1500);
}
"""

# Inline version (without the function wrapping) for the legacy head= path
_TOOLTIP_JS_INLINE = (
    _TOOLTIP_JS.replace("() => {", "(function() {").rstrip().rstrip("}") + "})();"
)
