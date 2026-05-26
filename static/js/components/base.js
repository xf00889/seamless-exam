/**
 * Base Component JavaScript
 * Common functionality shared across multiple components
 * Following ExamMaker system patterns
 */

/**
 * Base Component Class
 * Provides common functionality for all UI components
 */
class BaseComponent {
    constructor(element, options = {}) {
        this.element = element;
        this.options = { ...this.constructor.defaultOptions, ...options };
        this.initialized = false;
        
        if (this.element) {
            this.init();
        }
    }
    
    /**
     * Initialize the component
     */
    init() {
        if (this.initialized) {
            return;
        }
        
        this.bindEvents();
        this.initialized = true;
        this.trigger('initialized');
    }
    
    /**
     * Bind event listeners
     * Override in subclasses
     */
    bindEvents() {
        // Override in subclasses
    }
    
    /**
     * Destroy the component
     */
    destroy() {
        this.unbindEvents();
        this.initialized = false;
        this.trigger('destroyed');
    }
    
    /**
     * Unbind event listeners
     * Override in subclasses
     */
    unbindEvents() {
        // Override in subclasses
    }
    
    /**
     * Trigger a custom event
     * @param {string} eventName - Event name
     * @param {*} detail - Event detail data
     */
    trigger(eventName, detail = null) {
        if (!this.element) return;
        
        const event = new CustomEvent(eventName, {
            detail,
            bubbles: true,
            cancelable: true
        });
        
        this.element.dispatchEvent(event);
    }
    
    /**
     * Add event listener with automatic cleanup
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     * @param {Object} options - Event options
     */
    on(event, handler, options = {}) {
        if (!this.element) return;
        
        this.element.addEventListener(event, handler, options);
        
        // Store for cleanup
        if (!this._eventHandlers) {
            this._eventHandlers = [];
        }
        this._eventHandlers.push({ event, handler, options });
    }
    
    /**
     * Remove event listener
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     */
    off(event, handler) {
        if (!this.element) return;
        
        this.element.removeEventListener(event, handler);
        
        // Remove from stored handlers
        if (this._eventHandlers) {
            this._eventHandlers = this._eventHandlers.filter(
                h => h.event !== event || h.handler !== handler
            );
        }
    }
    
    /**
     * Get option value with fallback
     * @param {string} key - Option key
     * @param {*} fallback - Fallback value
     * @returns {*} Option value
     */
    getOption(key, fallback = null) {
        return this.options[key] !== undefined ? this.options[key] : fallback;
    }
    
    /**
     * Set option value
     * @param {string} key - Option key
     * @param {*} value - Option value
     */
    setOption(key, value) {
        this.options[key] = value;
    }
    
    /**
     * Default options for all components
     */
    static defaultOptions = {
        debug: false
    };
}

/**
 * Component Registry
 * Manages component instances and provides utilities
 */
class ComponentRegistry {
    static components = new Map();
    
    /**
     * Register a component instance
     * @param {string} name - Component name
     * @param {BaseComponent} instance - Component instance
     */
    static register(name, instance) {
        if (!this.components.has(name)) {
            this.components.set(name, []);
        }
        this.components.get(name).push(instance);
    }
    
    /**
     * Get component instances by name
     * @param {string} name - Component name
     * @returns {Array} Component instances
     */
    static get(name) {
        return this.components.get(name) || [];
    }
    
    /**
     * Destroy all components of a type
     * @param {string} name - Component name
     */
    static destroyAll(name) {
        const instances = this.get(name);
        instances.forEach(instance => instance.destroy());
        this.components.delete(name);
    }
    
    /**
     * Initialize components from DOM
     * @param {string} selector - CSS selector
     * @param {Function} ComponentClass - Component class
     * @param {Object} options - Default options
     */
    static initFromDOM(selector, ComponentClass, options = {}) {
        const elements = document.querySelectorAll(selector);
        const instances = [];
        
        elements.forEach(element => {
            const instance = new ComponentClass(element, options);
            instances.push(instance);
            this.register(ComponentClass.name, instance);
        });
        
        return instances;
    }
}

// Extend the global DOMUtils (from utils.js) with a ready() helper if not present
if (typeof DOMUtils !== 'undefined' && !DOMUtils.ready) {
    DOMUtils.ready = function(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            callback();
        }
    };
}

/**
 * Event Bus for component communication
 */
class EventBus {
    static events = new Map();
    
    /**
     * Subscribe to an event
     * @param {string} event - Event name
     * @param {Function} callback - Event callback
     */
    static on(event, callback) {
        if (!this.events.has(event)) {
            this.events.set(event, []);
        }
        this.events.get(event).push(callback);
    }
    
    /**
     * Unsubscribe from an event
     * @param {string} event - Event name
     * @param {Function} callback - Event callback
     */
    static off(event, callback) {
        if (!this.events.has(event)) return;
        
        const callbacks = this.events.get(event);
        const index = callbacks.indexOf(callback);
        if (index > -1) {
            callbacks.splice(index, 1);
        }
    }
    
    /**
     * Emit an event
     * @param {string} event - Event name
     * @param {*} data - Event data
     */
    static emit(event, data = null) {
        if (!this.events.has(event)) return;
        
        this.events.get(event).forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`Error in event handler for '${event}':`, error);
            }
        });
    }
}

// Auto-initialize when DOM is ready
DOMUtils.ready(() => {
    // Initialize CSRF helper if available
    if (window.CSRFHelper) {
        window.CSRFHelper.setupAjaxHeaders();
    }
    
    // Emit DOM ready event
    EventBus.emit('dom:ready');
});

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        BaseComponent,
        ComponentRegistry,
        DOMUtils,
        EventBus
    };
}