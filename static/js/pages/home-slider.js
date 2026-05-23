/**
 * Homepage slider controls for premium landing experience.
 * Keeps behavior isolated to pages that include [data-slider].
 */
document.addEventListener("DOMContentLoaded", function () {
    const slider = document.querySelector("[data-slider]");

    if (!slider) {
        return;
    }

    const track = slider.querySelector(".hero-slider__track");
    const slides = Array.from(slider.querySelectorAll("[data-slide]"));
    const dots = Array.from(slider.querySelectorAll("[data-slider-dot]"));
    const previousButton = slider.querySelector("[data-slider-prev]");
    const nextButton = slider.querySelector("[data-slider-next]");
    const autoplayIntervalMs = 5500;
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let currentIndex = 0;
    let autoplayTimer = null;

    if (!track || slides.length === 0) {
        return;
    }

    function renderSlide(nextIndex) {
        currentIndex = (nextIndex + slides.length) % slides.length;

        track.style.setProperty("--slider-index", String(currentIndex));

        slides.forEach(function (slide, slideIndex) {
            const isActive = slideIndex === currentIndex;
            slide.classList.toggle("is-active", isActive);
            slide.setAttribute("aria-hidden", isActive ? "false" : "true");
        });

        dots.forEach(function (dot, dotIndex) {
            const isActive = dotIndex === currentIndex;
            dot.classList.toggle("is-active", isActive);
            dot.setAttribute("aria-selected", isActive ? "true" : "false");
            dot.setAttribute("tabindex", isActive ? "0" : "-1");
        });
    }

    function stopAutoplay() {
        if (autoplayTimer) {
            clearInterval(autoplayTimer);
            autoplayTimer = null;
        }
    }

    function startAutoplay() {
        stopAutoplay();
        autoplayTimer = setInterval(function () {
            renderSlide(currentIndex + 1);
        }, autoplayIntervalMs);
    }

    if (previousButton) {
        previousButton.addEventListener("click", function () {
            renderSlide(currentIndex - 1);
            startAutoplay();
        });
    }

    if (nextButton) {
        nextButton.addEventListener("click", function () {
            renderSlide(currentIndex + 1);
            startAutoplay();
        });
    }

    dots.forEach(function (dot) {
        dot.addEventListener("click", function () {
            const dotIndex = Number(dot.getAttribute("data-slider-dot"));

            if (Number.isNaN(dotIndex)) {
                return;
            }

            renderSlide(dotIndex);
            startAutoplay();
        });
    });

    slider.addEventListener("keydown", function (event) {
        if (event.key === "ArrowLeft") {
            event.preventDefault();
            renderSlide(currentIndex - 1);
            startAutoplay();
        }

        if (event.key === "ArrowRight") {
            event.preventDefault();
            renderSlide(currentIndex + 1);
            startAutoplay();
        }
    });

    slider.addEventListener("mouseenter", stopAutoplay);
    slider.addEventListener("mouseleave", startAutoplay);
    slider.addEventListener("focusin", stopAutoplay);
    slider.addEventListener("focusout", function (event) {
        if (!slider.contains(event.relatedTarget)) {
            startAutoplay();
        }
    });

    document.addEventListener("visibilitychange", function () {
        if (document.hidden) {
            stopAutoplay();
            return;
        }

        startAutoplay();
    });

    renderSlide(0);

    if (!prefersReducedMotion) {
        startAutoplay();
    }
});
