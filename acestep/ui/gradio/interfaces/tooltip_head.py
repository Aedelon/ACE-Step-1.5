"""ACE-Step click-to-open help modal system.

Provides a small (?) icon next to each label that opens a centered modal
with the parameter description on click. Replaces the previous hover
tooltip approach because:

1. Hover tooltips are not accessible on touch devices
2. Hover tooltips are inherently fragile in nested DOM trees
3. WCAG 2.2 SC 1.4.13 prefers persistent dismissible content
4. Click+modal is the same pattern as the existing help_content.py

How it works:
    1. CSS in get_tooltip_css() defines the small (?) icon and the
       fullscreen modal overlay.
    2. JS in get_tooltip_js() runs on page load (via launch(js=...)).
    3. JS scans for `.acestep-tt` elements, finds the native info span,
       hides it, and adds a small (?) button next to the label.
    4. Click on the button creates/shows a modal centered in the
       viewport with the info text.
    5. Click outside the modal or on close button hides it.
    6. MutationObserver covers components added dynamically.

Why opt-in via class:
    The previous tooltip system used `has-info-container` which was
    applied to many elements including Accordions. CSS selectors
    targeting descendants ended up matching live components. This
    system uses a strict opt-in marker `acestep-tt`, and the JS uses
    closest() to ensure each info span belongs to the right host.

Why CSS and JS are exposed separately:
    In Gradio 6, head=/css=/js= must be passed to demo.launch(), not
    to gr.Blocks(). Crucially, <script> tags inside head= are inserted
    via innerHTML and never execute (HTML5 spec). The js= parameter is
    the only way to run custom JavaScript on page load.
"""


def get_tooltip_css() -> str:
    """Return the CSS for the help modal system, suitable for css= parameter."""
    return _TOOLTIP_CSS


def get_tooltip_js() -> str:
    """Return JavaScript function string for the js= parameter.

    The js= parameter expects a JavaScript function expression. The
    function is called once on page load.
    """
    return _TOOLTIP_JS


def get_tooltip_head() -> str:
    """[DEPRECATED] Return CSS+JS as a single <style>+<script> string.

    Kept for backward compatibility. Prefer get_tooltip_css() and
    get_tooltip_js() for Gradio 6 launch(css=..., js=...).
    """
    return f"<style>{_TOOLTIP_CSS}</style>"


_TOOLTIP_CSS = """
/* ===== ACE-Step Help Modal System ===== */

/* Small (?) icon button placed next to each label */
.acestep-info-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 13px;
    height: 13px;
    border-radius: 50%;
    margin-left: 5px;
    padding: 0;
    border: 1px solid var(--border-color-primary, #555);
    background: transparent;
    color: var(--body-text-color-subdued, #aaa);
    font-size: 9px;
    font-weight: 700;
    line-height: 1;
    cursor: pointer;
    font-family: inherit;
    vertical-align: middle;
    transition: all 0.15s ease;
    flex-shrink: 0;
}
.acestep-info-icon:hover {
    color: #fff;
    border-color: #3b82f6;
    background: #3b82f6;
}

/* Hide native Gradio info span when our system has upgraded it */
.acestep-tt span[data-testid="block-info"].acestep-tt-hidden {
    display: none !important;
}

/* Modal overlay (full viewport, dimmed) */
#acestep-info-modal-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    z-index: 999999;
    display: none;
    justify-content: center;
    align-items: center;
    backdrop-filter: blur(4px);
}
#acestep-info-modal-overlay.visible {
    display: flex;
}

/* Modal content card */
#acestep-info-modal-content {
    background: rgba(20, 20, 30, 0.98);
    color: #f0f0f0;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    max-width: 560px;
    width: 90%;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    position: relative;
    animation: acestep-modal-fade-in 0.15s ease-out;
}
@keyframes acestep-modal-fade-in {
    from { opacity: 0; transform: translateY(-10px) scale(0.98); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

#acestep-info-modal-title {
    padding: 18px 24px 8px 24px;
    font-size: 14px;
    font-weight: 600;
    color: #3b82f6;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 12px;
    margin-bottom: 0;
}

#acestep-info-modal-body {
    padding: 16px 24px 24px 24px;
    overflow-y: auto;
    line-height: 1.6;
    font-size: 13px;
    color: #e4e4e7;
}

#acestep-info-modal-close {
    position: absolute;
    top: 12px;
    right: 12px;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    border: none;
    background: rgba(255, 255, 255, 0.1);
    color: #f0f0f0;
    font-size: 16px;
    line-height: 1;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
}
#acestep-info-modal-close:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: scale(1.05);
}

#acestep-info-modal-body::-webkit-scrollbar {
    width: 8px;
}
#acestep-info-modal-body::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
}
"""


_TOOLTIP_JS = """
(() => {
    'use strict';
    const OVERLAY_ID = 'acestep-info-modal-overlay';
    const HOST_SELECTOR = '.acestep-tt';

    function ensureModal() {
        let overlay = document.getElementById(OVERLAY_ID);
        if (overlay) return overlay;

        overlay = document.createElement('div');
        overlay.id = OVERLAY_ID;
        overlay.innerHTML = `
            <div id="acestep-info-modal-content">
                <button id="acestep-info-modal-close" aria-label="Close">×</button>
                <div id="acestep-info-modal-title">Parameter info</div>
                <div id="acestep-info-modal-body"></div>
            </div>
        `;
        document.body.appendChild(overlay);

        // Click outside content closes
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) hideModal();
        });
        // Close button
        const closeBtn = overlay.querySelector('#acestep-info-modal-close');
        closeBtn.addEventListener('click', hideModal);
        // Escape key closes
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && overlay.classList.contains('visible')) {
                hideModal();
            }
        });

        return overlay;
    }

    function showModal(title, text) {
        const overlay = ensureModal();
        const titleEl = overlay.querySelector('#acestep-info-modal-title');
        const bodyEl = overlay.querySelector('#acestep-info-modal-body');
        titleEl.textContent = title || 'Parameter info';
        bodyEl.textContent = text || '';
        overlay.classList.add('visible');
    }

    function hideModal() {
        const overlay = document.getElementById(OVERLAY_ID);
        if (overlay) overlay.classList.remove('visible');
    }

    function upgradeHost(host) {
        if (host.dataset.acestepTtUpgraded === '1') return;

        // Find info span where the closest acestep-tt ancestor is THIS host
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

        // Find the label to attach the icon to
        const label = host.querySelector('label, .label-wrap, .block-title');
        if (!label) return;
        if (label.querySelector('.acestep-info-icon')) return;

        // Try to extract a clean title from the label text
        const labelText = (label.textContent || '').trim().replace(/\\s+/g, ' ');

        const icon = document.createElement('button');
        icon.type = 'button';
        icon.className = 'acestep-info-icon';
        icon.textContent = '?';
        icon.setAttribute('aria-label', 'Help: ' + labelText.substring(0, 50));
        icon.setAttribute('data-tooltip', text);
        icon.setAttribute('data-tooltip-title', labelText);
        icon.tabIndex = 0;

        icon.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            showModal(labelText, text);
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

    // Initial scan + observer
    scanAndUpgrade(document);
    startObserver();

    // Delayed re-scans to catch components mounted after the js= callback
    setTimeout(() => scanAndUpgrade(document), 500);
    setTimeout(() => scanAndUpgrade(document), 1500);
    setTimeout(() => scanAndUpgrade(document), 3000);
})();
"""
