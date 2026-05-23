/**
 * Tooltip Manager Component
 * Provides tooltip functionality for elements with data-tooltip attributes
 * Moved from root directory to components for better organization
 */

class TooltipManager {
    constructor() {
        this.tooltips = new Map();
        this.activeTooltip = null;
        this.init();
    }

    init() {
        // Initialize tooltips on page load
        this.attachTooltips();
        
        // Handle window resize to reposition tooltips
        window.addEventListener('resize', () => {
            if (this.activeTooltip) {
                this.hide(this.activeTooltip);
            }
        });
        
        // Hide tooltip on scroll
        window.addEventListener('scroll', () => {
            if (this.activeTooltip) {
                this.hide(this.activeTooltip);
            }
        }, true);
    }

    attachTooltips() {
        // Find all elements with data-tooltip attribute
        const triggers = document.querySelectorAll('[data-tooltip]');
        
        triggers.forEach(trigger => {
            const tooltipText = trigger.getAttribute('data-tooltip');
            
            if (tooltipText) {
                // Create tooltip element
                const tooltip = this.createTooltip(tooltipText);
                this.tooltips.set(trigger, tooltip);
                
                // Attach event listeners
                trigger.addEventListener('mouseenter', () => this.show(tooltip, trigger));
                trigger.addEventListener('mouseleave', () => this.hide(tooltip));
                trigger.addEventListener('focus', () => this.show(tooltip, trigger));
                trigger.addEventListener('blur', () => this.hide(tooltip));
                
                // Handle touch devices
                trigger.addEventListener('touchstart', (e) => {
                    e.preventDefault();
                    if (this.activeTooltip === tooltip) {
                        this.hide(tooltip);
                    } else {
                        this.show(tooltip, trigger);
                    }
                }, { passive: false });
            }
        });
    }

    createTooltip(text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip-popup';
        tooltip.textContent = text;
        tooltip.setAttribute('role', 'tooltip');
        document.body.appendChild(tooltip);
        return tooltip;
    }

    show(tooltip, anchor) {
        // Hide any currently active tooltip
        if (this.activeTooltip && this.activeTooltip !== tooltip) {
            this.hide(this.activeTooltip);
        }

        // Position the tooltip
        this.position(tooltip, anchor);
        
        // Show tooltip with a slight delay for better UX
        setTimeout(() => {
            tooltip.classList.add('tooltip-visible');
            this.activeTooltip = tooltip;
        }, 100);
    }

    hide(tooltip) {
        tooltip.classList.remove('tooltip-visible');
        if (this.activeTooltip === tooltip) {
            this.activeTooltip = null;
        }
    }

    position(tooltip, anchor) {
        const anchorRect = anchor.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        // Calculate position (centered above the anchor)
        let top = anchorRect.top - tooltipRect.height - 8;
        let left = anchorRect.left + (anchorRect.width / 2) - (tooltipRect.width / 2);
        
        // Ensure tooltip stays within viewport
        const padding = 8;
        
        // Adjust horizontal position if needed
        if (left < padding) {
            left = padding;
        } else if (left + tooltipRect.width > window.innerWidth - padding) {
            left = window.innerWidth - tooltipRect.width - padding;
        }
        
        // If tooltip would go above viewport, show it below instead
        if (top < padding) {
            top = anchorRect.bottom + 8;
            // Flip arrow direction (would need CSS adjustment for full implementation)
        }
        
        // Apply position
        tooltip.style.top = `${top + window.scrollY}px`;
        tooltip.style.left = `${left + window.scrollX}px`;
    }

    // Public method to refresh tooltips (useful for dynamically added content)
    refresh() {
        // Clear existing tooltips
        this.tooltips.forEach((tooltip, trigger) => {
            tooltip.remove();
        });
        this.tooltips.clear();
        this.activeTooltip = null;
        
        // Reattach tooltips
        this.attachTooltips();
    }

    // Public method to destroy all tooltips
    destroy() {
        this.tooltips.forEach((tooltip, trigger) => {
            tooltip.remove();
        });
        this.tooltips.clear();
        this.activeTooltip = null;
    }
}

// Initialize tooltip manager when DOM is ready
let tooltipManager;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        tooltipManager = new TooltipManager();
    });
} else {
    tooltipManager = new TooltipManager();
}

// Export for use in other scripts if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TooltipManager;
}