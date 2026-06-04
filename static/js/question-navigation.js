/**
 * Question Navigation
 * Lightweight click-to-scroll + scroll-spy for read-only question pages
 * (exam detail, attempt detail). Does NOT use pagination.
 *
 * Expects:
 *   - .question-nav-btn buttons with data-question-id
 *   - .question-card elements with data-question-id and id="question-{id}"
 */
(function () {
    'use strict';

    function init() {
        const navButtons = Array.from(document.querySelectorAll('.question-nav-btn'));
        const questionCards = Array.from(document.querySelectorAll('.question-card[data-question-id]'));
        if (!navButtons.length || !questionCards.length) return;

        const baseClasses = ['bg-gray-100', 'border-gray-300', 'text-gray-600'];
        const currentClasses = ['bg-blue-100', 'border-blue-500', 'text-blue-700', 'font-bold'];

        function setCurrentButton(button) {
            navButtons.forEach((btn) => {
                btn.classList.remove(...currentClasses);
                btn.classList.add(...baseClasses);
            });
            if (!button) return;
            button.classList.remove(...baseClasses);
            button.classList.add(...currentClasses);
        }

        function getButtonForId(id) {
            return navButtons.find((b) => b.getAttribute('data-question-id') === String(id));
        }

        function scrollToQuestion(id) {
            const card = document.getElementById('question-' + id);
            if (!card) return;
            const offset = 80;
            const top = card.getBoundingClientRect().top + window.pageYOffset - offset;
            window.scrollTo({ top, behavior: 'smooth' });
        }

        navButtons.forEach((btn) => {
            btn.addEventListener('click', () => {
                const id = btn.getAttribute('data-question-id');
                setCurrentButton(btn);
                scrollToQuestion(id);
            });
        });

        // Scroll-spy: highlight the nav button for the question currently in view.
        if ('IntersectionObserver' in window) {
            const visible = new Map();
            const observer = new IntersectionObserver(
                (entries) => {
                    entries.forEach((entry) => {
                        const id = entry.target.getAttribute('data-question-id');
                        if (entry.isIntersecting) {
                            visible.set(id, entry.intersectionRatio);
                        } else {
                            visible.delete(id);
                        }
                    });
                    if (visible.size === 0) return;
                    // Pick the most-visible question in viewport
                    let bestId = null;
                    let bestRatio = -1;
                    visible.forEach((ratio, id) => {
                        if (ratio > bestRatio) {
                            bestRatio = ratio;
                            bestId = id;
                        }
                    });
                    if (bestId) setCurrentButton(getButtonForId(bestId));
                },
                { rootMargin: '-80px 0px -55% 0px', threshold: [0, 0.25, 0.5, 0.75, 1] }
            );
            questionCards.forEach((card) => observer.observe(card));
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
