/**
 * CSRF Helper Utility
 * Provides methods for handling Django CSRF tokens in AJAX requests
 * Following ExamMaker system conventions for security
 * 
 * @author ExamMaker Development Team
 * @version 1.0.0
 * @since 2024
 * 
 * Requirements: 10.1, 10.2, 10.4 - Coding standards compliance
 */
class CSRFHelper {
    /**
     * Get CSRF token from Django's cookie or meta tag
     * @returns {string|null} CSRF token or null if not found
     */
    static getToken() {
        // First try to get from cookie (Django's default)
        let token = this.getCookie('exammaker_csrftoken') || this.getCookie('csrftoken');
        
        // Fallback to meta tag if cookie not found
        if (!token) {
            const metaTag = document.querySelector('meta[name=csrf-token]');
            token = metaTag ? metaTag.getAttribute('content') : null;
        }
        
        // Last resort: try to get from form input
        if (!token) {
            const csrfInput = document.querySelector('input[name=csrfmiddlewaretoken]');
            token = csrfInput ? csrfInput.value : null;
        }
        
        return token;
    }
    
    /**
     * Get cookie value by name
     * @param {string} name - Cookie name
     * @returns {string|null} Cookie value or null if not found
     */
    static getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    /**
     * Setup AJAX headers with CSRF token for jQuery or fetch requests
     * Call this once on page load to configure all AJAX requests
     */
    static setupAjaxHeaders() {
        const token = this.getToken();
        if (!token) {
            console.warn('CSRF token not found. AJAX requests may fail.');
            return;
        }
        
        // Setup for jQuery if available
        if (typeof $ !== 'undefined' && $.ajaxSetup) {
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!this.crossDomain && !/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.noCSRF) {
                        xhr.setRequestHeader("X-CSRFToken", token);
                    }
                }
            });
        }
        
        // Setup for fetch API
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            if (options.method && !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(options.method.toUpperCase())) {
                options.headers = options.headers || {};
                if (!options.headers['X-CSRFToken']) {
                    options.headers['X-CSRFToken'] = token;
                }
            }
            return originalFetch(url, options);
        };
    }
    
    /**
     * Add CSRF token to a form element
     * @param {HTMLFormElement} form - Form element to add token to
     */
    static addTokenToForm(form) {
        if (!form || form.tagName !== 'FORM') {
            console.error('Invalid form element provided to addTokenToForm');
            return;
        }
        
        const token = this.getToken();
        if (!token) {
            console.warn('CSRF token not found. Form submission may fail.');
            return;
        }
        
        // Check if token already exists
        let csrfInput = form.querySelector('input[name=csrfmiddlewaretoken]');
        if (!csrfInput) {
            csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            form.appendChild(csrfInput);
        }
        
        csrfInput.value = token;
    }
    
    /**
     * Create AJAX request with proper CSRF handling
     * @param {string} url - Request URL
     * @param {Object} options - Request options
     * @returns {Promise} Fetch promise
     */
    static async request(url, options = {}) {
        const token = this.getToken();
        if (!token) {
            throw new Error('CSRF token not found');
        }
        
        const defaultOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': token
            },
            credentials: 'same-origin'
        };
        
        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };
        
        return fetch(url, mergedOptions);
    }
}

// Auto-setup CSRF headers when script loads
document.addEventListener('DOMContentLoaded', function() {
    CSRFHelper.setupAjaxHeaders();
});

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CSRFHelper;
}