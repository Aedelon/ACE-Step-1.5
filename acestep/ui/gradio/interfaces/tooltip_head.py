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
/* ===== ACE-Step Help System ===== */

/* (?) icon button placed next to each label */
.acestep-info-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    margin-left: 8px;
    padding: 0;
    border: 1.5px solid var(--border-color-primary, #555);
    background: transparent;
    color: var(--body-text-color-subdued, #aaa);
    font-size: 12px;
    font-weight: 700;
    line-height: 1;
    cursor: pointer;
    font-family: inherit;
    vertical-align: middle;
    transition: all 0.15s ease;
    flex-shrink: 0;
}
.acestep-info-icon:hover,
.acestep-info-icon.acestep-active {
    color: #fff;
    border-color: #3b82f6;
    background: #3b82f6;
}

/* Hide the native Gradio info element after our system has upgraded it.
   The info element is the sibling of the block-info span (which holds
   the label). We mark it with .acestep-tt-hidden in JS. */
.acestep-tt-hidden {
    display: none !important;
}

/* Bubble popup (lives in <body>, position: fixed) shown on (?) click */
#acestep-info-bubble {
    position: fixed;
    z-index: 999998;
    max-width: 460px;
    max-height: 70vh;
    overflow-y: auto;
    padding: 18px 20px;
    border-radius: 10px;
    background: rgba(20, 20, 30, 0.98);
    color: #f0f0f0;
    border: 1px solid #3b82f6;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
    font-size: 14px;
    line-height: 1.6;
    font-weight: 400;
    pointer-events: auto;
    display: none;
    backdrop-filter: blur(10px);
    animation: acestep-bubble-fade-in 0.12s ease-out;
    white-space: pre-wrap;
    word-wrap: break-word;
}
#acestep-info-bubble.visible {
    display: block;
}
@keyframes acestep-bubble-fade-in {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
}
#acestep-info-bubble::-webkit-scrollbar {
    width: 6px;
}
#acestep-info-bubble::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 3px;
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
    const BUBBLE_ID = 'acestep-info-bubble';
    const HOST_SELECTOR = '.acestep-tt';
    let activeBubbleTrigger = null;

    /** Create or return the bubble element used for parameter (?) tooltips. */
    function ensureBubble() {
        let bubble = document.getElementById(BUBBLE_ID);
        if (bubble) return bubble;

        bubble = document.createElement('div');
        bubble.id = BUBBLE_ID;
        document.body.appendChild(bubble);

        // Click outside closes bubble (handled by document listener below)
        // Escape closes
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && bubble.classList.contains('visible')) {
                hideBubble();
            }
        });
        return bubble;
    }

    function hideBubble() {
        const bubble = document.getElementById(BUBBLE_ID);
        if (bubble) bubble.classList.remove('visible');
        if (activeBubbleTrigger) {
            activeBubbleTrigger.classList.remove('acestep-active');
            activeBubbleTrigger = null;
        }
    }

    function showBubble(triggerEl, text) {
        const bubble = ensureBubble();
        bubble.textContent = text || '';
        bubble.classList.add('visible');

        if (activeBubbleTrigger && activeBubbleTrigger !== triggerEl) {
            activeBubbleTrigger.classList.remove('acestep-active');
        }
        activeBubbleTrigger = triggerEl;
        triggerEl.classList.add('acestep-active');

        // Position relative to trigger using viewport coordinates
        const rect = triggerEl.getBoundingClientRect();
        const vh = window.innerHeight;
        const vw = window.innerWidth;
        const BUBBLE_MAX_W = 480;

        // Reset positioning so we can measure
        bubble.style.top = '';
        bubble.style.bottom = '';
        bubble.style.left = '';
        bubble.style.right = '';

        // Horizontal: prefer aligning to trigger left, clamp inside viewport
        const left = Math.max(8, Math.min(rect.left, vw - BUBBLE_MAX_W - 8));
        bubble.style.left = left + 'px';

        // Vertical: prefer below, flip above if not enough room
        const belowRoom = vh - rect.bottom;
        const bubbleHeight = bubble.offsetHeight || 200;
        if (belowRoom > bubbleHeight + 16 || belowRoom > vh * 0.4) {
            bubble.style.top = (rect.bottom + 6) + 'px';
        } else {
            bubble.style.top = Math.max(8, rect.top - bubbleHeight - 6) + 'px';
        }
    }

    // Click anywhere outside bubble closes it
    document.addEventListener('click', (e) => {
        const bubble = document.getElementById(BUBBLE_ID);
        if (!bubble || !bubble.classList.contains('visible')) return;
        if (bubble.contains(e.target)) return;
        if (e.target.classList && e.target.classList.contains('acestep-info-icon')) return;
        hideBubble();
    });

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

    function showModal(title, content, isHtml) {
        const overlay = ensureModal();
        const titleEl = overlay.querySelector('#acestep-info-modal-title');
        const bodyEl = overlay.querySelector('#acestep-info-modal-body');
        titleEl.textContent = title || 'Parameter info';
        if (isHtml) {
            bodyEl.innerHTML = content || '';
        } else {
            bodyEl.textContent = content || '';
        }
        overlay.classList.add('visible');
    }

    /** Hijack existing .help-inline-btn elements to use our unified modal.
     *  These buttons were created by help_content.py with inline onclick that
     *  may not work reliably in Gradio 6 (CSP, sanitization, scoping). */
    function upgradeHelpButton(btn) {
        if (btn.dataset.acestepHelpUpgraded === '1') return;
        btn.dataset.acestepHelpUpgraded = '1';

        // The original onclick is `document.getElementById('help-modal-N').style.display='flex'`
        // Extract the modal ID from the onclick attribute string
        const onclickStr = btn.getAttribute('onclick') || '';
        const m = onclickStr.match(/getElementById\\('([^']+)'\\)/);
        if (!m) return;
        const modalId = m[1];

        // Remove the inline onclick to prevent double-handling
        btn.removeAttribute('onclick');

        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const sourceModal = document.getElementById(modalId);
            if (!sourceModal) {
                console.warn('[acestep] Help modal not found:', modalId);
                return;
            }
            // Find the title (from button parent) and the content (from .help-modal-body)
            const bodyEl = sourceModal.querySelector('.help-modal-body');
            const html = bodyEl ? bodyEl.innerHTML : '';
            // Use button's nearest section header as title
            const section = btn.closest('.gradio-accordion, .accordion, .block, .gradio-row');
            const titleEl = section ? section.querySelector('.label-wrap, label, h1, h2, h3, h4, summary') : null;
            const title = titleEl ? titleEl.textContent.trim().replace(/\\?+$/, '').trim() : 'Help';
            showModal(title, html, true);
        });
    }

    function scanHelpButtons(root) {
        if (!root || !root.querySelectorAll) return;
        root.querySelectorAll('.help-inline-btn').forEach(upgradeHelpButton);
    }

    function hideModal() {
        const overlay = document.getElementById(OVERLAY_ID);
        if (overlay) overlay.classList.remove('visible');
    }

    /** Find {labelEl, labelText, infoEl, infoText} in a .acestep-tt host.
     *  Tries multiple strategies because Gradio renders info= differently
     *  for Slider/Dropdown vs Checkbox. Returns null if no info found. */
    function findInfoInHost(host) {
        // Strategy 1: Slider/Dropdown — span[data-testid="block-info"]
        // contains the label, info is the nextElementSibling.
        const blockInfoSpans = host.querySelectorAll('span[data-testid="block-info"]');
        for (const span of blockInfoSpans) {
            if (span.closest(HOST_SELECTOR) !== host) continue;
            const next = span.nextElementSibling;
            if (next) {
                const txt = (next.textContent || '').trim();
                if (txt) {
                    return {
                        labelEl: span,
                        labelText: (span.textContent || '').trim(),
                        infoEl: next,
                        infoText: txt,
                    };
                }
            }
        }

        // Strategy 2: Checkbox — span.label-text inside <label>, info is
        // a sibling element. Walk descendants and find one that contains
        // text but is not part of the input control.
        const labelTextSpan = host.querySelector('span.label-text');
        if (labelTextSpan) {
            const labelText = (labelTextSpan.textContent || '').trim();
            const labelParent = labelTextSpan.closest('label');
            // Look for any element under host that's NOT inside the label
            // and contains text content distinct from the label.
            const allDescendants = host.querySelectorAll('div, span, p');
            for (const el of allDescendants) {
                if (labelParent && labelParent.contains(el)) continue;
                if (el.querySelector('input, select, textarea')) continue;
                if (el.querySelector('button')) continue;
                if (el.querySelector('span.label-text')) continue;
                if (el.querySelector('span[data-testid="block-info"]')) continue;
                const txt = (el.textContent || '').trim();
                if (!txt || txt === labelText) continue;
                // Skip if too long (likely a container, not info)
                // Info text is typically <500 chars
                if (txt.length > 1000) continue;
                // Avoid picking large container divs: must have only inline children or none
                const childElements = Array.from(el.children);
                const hasOnlyInlineChildren = childElements.every(c =>
                    ['SPAN', 'STRONG', 'EM', 'B', 'I', 'A', 'CODE', 'BR'].includes(c.tagName)
                );
                if (childElements.length > 0 && !hasOnlyInlineChildren) continue;
                return {
                    labelEl: labelTextSpan,
                    labelText: labelText,
                    infoEl: el,
                    infoText: txt,
                };
            }
        }

        return null;
    }

    /** Skip hosts that are clearly Accordions/Groups/Containers, not leaf
     *  components with info= text. We detect them by looking for elements
     *  that suggest a container: <details>/<summary>, gradio-accordion class,
     *  or hosts that contain other .acestep-tt descendants. */
    function isContainerHost(host) {
        if (host.tagName === 'DETAILS') return true;
        if (host.querySelector('summary')) return true;
        // Gradio Accordion uses .gradio-accordion class on the wrapper
        if (host.classList && host.classList.contains('gradio-accordion')) return true;
        // If host contains nested .acestep-tt elements, it's a container
        const nested = host.querySelectorAll(HOST_SELECTOR);
        if (nested.length > 0) return true;
        return false;
    }

    function upgradeHost(host) {
        if (host.dataset.acestepTtUpgraded === '1') return;

        if (isContainerHost(host)) {
            host.dataset.acestepTtUpgraded = '1';
            // Un-hide any elements we may have wrongly hidden in a previous
            // pass before the container check existed
            host.querySelectorAll('.acestep-tt-hidden').forEach(el => {
                el.classList.remove('acestep-tt-hidden');
            });
            return;
        }

        const found = findInfoInHost(host);
        if (!found) {
            host.dataset.acestepTtUpgraded = '1';
            return;
        }

        host.dataset.acestepTtUpgraded = '1';

        const labelEl = found.labelEl;
        const labelText = (found.labelText || '').replace(/\\s+/g, ' ');
        const infoEl = found.infoEl;
        const infoText = found.infoText;

        // Hide the info element so only the (?) bubble shows it
        if (infoEl) {
            infoEl.classList.add('acestep-tt-hidden');
        }

        // Don't add icon twice
        if (labelEl.querySelector('.acestep-info-icon')) return;

        const icon = document.createElement('button');
        icon.type = 'button';
        icon.className = 'acestep-info-icon';
        icon.textContent = '?';
        icon.setAttribute('aria-label', 'Help: ' + labelText.substring(0, 50));
        icon.setAttribute('data-tooltip', infoText);
        icon.setAttribute('data-tooltip-title', labelText);
        icon.tabIndex = 0;

        icon.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const bubble = document.getElementById(BUBBLE_ID);
            if (bubble && bubble.classList.contains('visible') && activeBubbleTrigger === icon) {
                hideBubble();
            } else {
                showBubble(icon, infoText);
            }
        });

        labelEl.appendChild(icon);
    }

    function scanAndUpgrade(root) {
        if (!root || !root.querySelectorAll) return;
        const hosts = root.querySelectorAll(HOST_SELECTOR);
        hosts.forEach(upgradeHost);
        scanHelpButtons(root);
    }

    function startObserver() {
        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) {
                        if (node.matches && node.matches(HOST_SELECTOR)) {
                            upgradeHost(node);
                        }
                        if (node.matches && node.matches('.help-inline-btn')) {
                            upgradeHelpButton(node);
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
