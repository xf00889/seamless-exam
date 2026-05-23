/**
 * AJAX Helper Utility
 * Provides convenient methods for making AJAX requests with proper error handling
 * Integrates with CSRFHelper for security
 */
class AjaxHelper {
    /**
     * Default request configuration
     */
    static defaultConfig = {
        timeout: 30000,
        retryAttempts: 3,
        retryDelay: 1000
    };
    
    /**
     * Make a GET request
     * @param {string} url - Request URL
     * @param {Object} options - Request options
     * @returns {Promise} Response promise
     */
    static async get(url, options = {}) {
        return this.request(url, {
            method: 'GET',
            ...options
        });
    }
    
    /**
     * Make a POST request
     * @param {string} url - Request URL
     * @param {Object} data - Request data
     * @param {Object} options - Request options
     * @returns {Promise} Response promise
     */
    static async post(url, data = {}, options = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data),
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
    }
    
    /**
     * Make a form data POST request
     * @param {string} url - Request URL
     * @param {FormData} formData - Form data
     * @param {Object} options - Request options
     * @returns {Promise} Response promise
     */
    static async postForm(url, formData, options = {}) {
        return this.request(url, {
            method: 'POST',
            body: formData,
            // Don't set Content-Type for FormData, let browser set it
            ...options
        });
    }
    
    /**
     * Make a PUT request
     * @param {string} url - Request URL
     * @param {Object} data - Request data
     * @param {Object} options - Request options
     * @returns {Promise} Response promise
     */
    static async put(url, data = {}, options = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data),
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
    }
    
    /**
     * Make a DELETE request
     * @param {string} url - Request URL
     * @param {Object} options - Request options
     * @returns {Promise} Response promise
     */
    static async delete(url, options = {}) {
        return this.request(url, {
            method: 'DELETE',
            ...options
        });
    }
    
    /**
     * Make a request with automatic CSRF handling and error management
     * @param {string} url - Request URL
     * @param {Object} options - Request options
     * @returns {Promise} Response promise
     */
    static async request(url, options = {}) {
        const config = { ...this.defaultConfig, ...options };
        
        // Add CSRF token for non-GET requests
        if (options.method && !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(options.method.toUpperCase())) {
            const token = window.CSRFHelper ? window.CSRFHelper.getToken() : null;
            if (token) {
                config.headers = {
                    'X-CSRFToken': token,
                    ...config.headers
                };
            }
        }
        
        // Add default headers
        config.headers = {
            'X-Requested-With': 'XMLHttpRequest',
            ...config.headers
        };
        
        // Add credentials for same-origin requests
        config.credentials = config.credentials || 'same-origin';
        
        let lastError;
        
        // Retry logic
        for (let attempt = 0; attempt <= config.retryAttempts; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), config.timeout);
                
                const response = await fetch(url, {
                    ...config,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                return response;
                
            } catch (error) {
                lastError = error;
                
                // Don't retry on certain errors
                if (error.name === 'AbortError' || 
                    (error.message && error.message.includes('HTTP 4'))) {
                    break;
                }
                
                // Wait before retry
                if (attempt < config.retryAttempts) {
                    await this.delay(config.retryDelay * (attempt + 1));
                }
            }
        }
        
        throw lastError;
    }
    
    /**
     * Make a JSON request and parse response
     * @param {string} url - Request URL
     * @param {Object} options - Request options
     * @returns {Promise} Parsed JSON response
     */
    static async requestJSON(url, options = {}) {
        const response = await this.request(url, options);
        return response.json();
    }
    
    /**
     * Submit a form via AJAX
     * @param {HTMLFormElement} form - Form element
     * @param {Object} options - Request options
     * @returns {Promise} Response promise
     */
    static async submitForm(form, options = {}) {
        if (!form || form.tagName !== 'FORM') {
            throw new Error('Invalid form element');
        }
        
        const formData = new FormData(form);
        const url = options.url || form.action || window.location.href;
        const method = options.method || form.method || 'POST';
        
        return this.request(url, {
            method: method.toUpperCase(),
            body: formData,
            ...options
        });
    }
    
    /**
     * Load content into an element
     * @param {string} url - Content URL
     * @param {HTMLElement} element - Target element
     * @param {Object} options - Request options
     * @returns {Promise} Load promise
     */
    static async loadContent(url, element, options = {}) {
        if (!element) {
            throw new Error('Target element is required');
        }
        
        try {
            const response = await this.request(url, options);
            const content = await response.text();
            element.innerHTML = content;
            
            // Trigger custom event
            element.dispatchEvent(new CustomEvent('contentLoaded', {
                detail: { url, content }
            }));
            
            return content;
        } catch (error) {
            element.innerHTML = '<div class="alert alert-danger">Failed to load content</div>';
            throw error;
        }
    }
    
    /**
     * Handle common AJAX errors
     * @param {Error} error - Error object
     * @param {Object} options - Error handling options
     */
    static handleError(error, options = {}) {
        console.error('AJAX Error:', error);
        
        let message = 'An error occurred';
        
        if (error.name === 'AbortError') {
            message = 'Request timed out';
        } else if (error.message.includes('HTTP 403')) {
            message = 'Access denied';
        } else if (error.message.includes('HTTP 404')) {
            message = 'Resource not found';
        } else if (error.message.includes('HTTP 500')) {
            message = 'Server error';
        } else if (!navigator.onLine) {
            message = 'No internet connection';
        }
        
        if (options.showAlert && window.Swal) {
            window.Swal.fire({
                icon: 'error',
                title: 'Error',
                text: message
            });
        }
        
        if (options.callback && typeof options.callback === 'function') {
            options.callback(error, message);
        }
        
        return { error, message };
    }
    
    /**
     * Delay utility for retry logic
     * @param {number} ms - Milliseconds to delay
     * @returns {Promise} Delay promise
     */
    static delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AjaxHelper;
}