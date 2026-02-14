/**
 * Tooltips Component for ReadySetClass
 *
 * Adds helpful hover tooltips throughout the app
 * Usage: <span class="tooltip-trigger" data-tooltip="Helpful text">?</span>
 */

(function() {
    // Tooltip styles (injected once)
    const style = document.createElement('style');
    style.textContent = `
        /* Tooltip trigger styling */
        .tooltip-trigger {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: var(--accent-gold, #C9A961);
            color: white;
            font-size: 12px;
            font-weight: 600;
            cursor: help;
            margin-left: 6px;
            position: relative;
            user-select: none;
            transition: all 0.2s ease;
        }

        .tooltip-trigger:hover {
            background: var(--primary-navy, #1E3A5F);
            transform: scale(1.1);
        }

        /* Tooltip bubble */
        .tooltip-bubble {
            position: absolute;
            bottom: calc(100% + 8px);
            left: 50%;
            transform: translateX(-50%);
            background: var(--primary-navy, #1E3A5F);
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
            line-height: 1.5;
            white-space: normal;
            max-width: 300px;
            min-width: 200px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            z-index: 10000;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease;
        }

        .tooltip-bubble::after {
            content: '';
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border: 6px solid transparent;
            border-top-color: var(--primary-navy, #1E3A5F);
        }

        .tooltip-trigger:hover .tooltip-bubble {
            opacity: 1;
        }

        /* Tooltip icon variants */
        .tooltip-trigger.info {
            background: var(--info, #3b82f6);
        }

        .tooltip-trigger.success {
            background: var(--success, #10b981);
        }

        .tooltip-trigger.warning {
            background: var(--warning, #f59e0b);
        }

        /* Help section styling */
        .help-section {
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
        }

        .help-section-header {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            color: var(--primary-navy, #1E3A5F);
            margin-bottom: 8px;
            cursor: pointer;
        }

        .help-section-content {
            color: var(--text-dark, #2C3E50);
            font-size: 14px;
            line-height: 1.6;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }

        .help-section-content.expanded {
            max-height: 500px;
            margin-top: 12px;
        }

        .help-section-content ul {
            margin: 8px 0;
            padding-left: 20px;
        }

        .help-section-content li {
            margin: 4px 0;
        }

        /* Inline hint text */
        .inline-hint {
            display: block;
            color: var(--text-light, #666);
            font-size: 13px;
            margin-top: 6px;
            font-style: italic;
        }

        /* Quick tip badge */
        .quick-tip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #fef3c7;
            border: 1px solid #fde047;
            color: #854d0e;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 13px;
            margin: 12px 0;
        }

        .quick-tip::before {
            content: '💡';
            font-size: 16px;
        }
    `;
    document.head.appendChild(style);

    // Initialize tooltips when DOM is ready
    function initTooltips() {
        document.querySelectorAll('.tooltip-trigger').forEach(trigger => {
            const tooltipText = trigger.getAttribute('data-tooltip');
            if (!tooltipText) return;

            // Create tooltip bubble
            const bubble = document.createElement('div');
            bubble.className = 'tooltip-bubble';
            bubble.textContent = tooltipText;
            trigger.appendChild(bubble);
        });
    }

    // Toggle help sections
    function initHelpSections() {
        document.querySelectorAll('.help-section-header').forEach(header => {
            header.addEventListener('click', function() {
                const content = this.nextElementSibling;
                content.classList.toggle('expanded');

                // Update arrow
                const arrow = this.querySelector('.help-arrow');
                if (arrow) {
                    arrow.textContent = content.classList.contains('expanded') ? '▼' : '▶';
                }
            });
        });
    }

    // Create tooltip helper function
    window.createTooltip = function(text, variant = 'default') {
        const span = document.createElement('span');
        span.className = `tooltip-trigger ${variant}`;
        span.setAttribute('data-tooltip', text);
        span.textContent = '?';

        const bubble = document.createElement('div');
        bubble.className = 'tooltip-bubble';
        bubble.textContent = text;
        span.appendChild(bubble);

        return span;
    };

    // Create help section helper
    window.createHelpSection = function(title, content) {
        return `
            <div class="help-section">
                <div class="help-section-header">
                    <span class="help-arrow">▶</span>
                    <span>${title}</span>
                </div>
                <div class="help-section-content">
                    ${content}
                </div>
            </div>
        `;
    };

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initTooltips();
            initHelpSections();
        });
    } else {
        initTooltips();
        initHelpSections();
    }

    // Re-initialize when content changes (for dynamic content)
    window.reinitTooltips = function() {
        initTooltips();
        initHelpSections();
    };
})();

// Common tooltip messages (reusable)
window.TOOLTIPS = {
    // Grading Setup
    GRADING_SETUP: "Configure how grades are calculated in your Canvas course. Set up weighted categories like Quizzes (20%), Assignments (30%), etc.",
    GRADING_CATEGORIES: "Categories are the types of assignments (Quizzes, Essays, Exams) and their weight toward the final grade. They must total 100%.",
    DROP_LOWEST: "Automatically drop the lowest score(s) in this category. Great for quizzes where you want to drop the worst 1-2 grades.",
    WEIGHTED_BY_POINTS: "Calculate grades based on points earned vs total points, rather than averaging percentages.",

    // AI Grading
    AI_GRADING: "AI grades student submissions in 3-5 minutes, then you review and approve. Saves ~90% of grading time (10 hours → 1 hour for 25 submissions).",
    RUBRIC: "A rubric defines grading criteria (Thesis: 20pts, Evidence: 30pts, etc.). AI uses this to grade consistently.",
    CONFIDENCE: "AI marks grades as High, Medium, or Low confidence. Review flagged submissions first.",
    STRICTNESS: "Lenient = generous grading, Balanced = fair, Strict = high standards. Affects how AI interprets rubric.",
    AI_CONTENT_DETECTION: "Flags submissions that may have been written by ChatGPT or other AI tools.",

    // Canvas Integration
    CANVAS_TOKEN: "Your Canvas API token lets ReadySetClass read courses and post content. Found in Canvas → Account → Settings → New Access Token.",
    CANVAS_URL: "Your institution's Canvas URL (e.g., institution.instructure.com). Don't include /courses or other paths.",

    // General
    SAVE_TIME: "This feature is designed to save you hours of repetitive work. Let AI handle the heavy lifting!",
    BETA_FEATURE: "This feature is in beta. We're actively improving it based on user feedback.",
};
