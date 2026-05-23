/**
 * Utility JavaScript Module
 * Common helper functions for the Gradely
 */

// ============================================================================
// AJAX Utilities
// ============================================================================

/**
 * AJAX Client with error handling and retry logic
 */
class AjaxClient {
    constructor(options = {}) {
        this.maxRetries = options.maxRetries || 3;
        this.retryDelay = options.retryDelay || 1000;
        this.timeout = options.timeout || 30000;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'X-CSRFToken': CookieUtils.getCSRFToken(),
            ...options.headers
        };
    }

    /**
     * Perform GET request
     * @param {string} url - Request URL
     * @param {Object} options - Additional fetch options
     * @returns {Promise<Response>} - Fetch response
     */
    async get(url, options = {}) {
        return this.request(url, {
            method: 'GET',
            ...options
        });
    }

    /**
     * Perform POST request
     * @param {string} url - Request URL
     * @param {Object} data - Request body data
     * @param {Object} options - Additional fetch options
     * @returns {Promise<Response>} - Fetch response
     */
    async post(url, data, options = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data),
            ...options
        });
    }

    /**
     * Perform PUT request
     * @param {string} url - Request URL
     * @param {Object} data - Request body data
     * @param {Object} options - Additional fetch options
     * @returns {Promise<Response>} - Fetch response
     */
    async put(url, data, options = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data),
            ...options
        });
    }

    /**
     * Perform DELETE request
     * @param {string} url - Request URL
     * @param {Object} options - Additional fetch options
     * @returns {Promise<Response>} - Fetch response
     */
    async delete(url, options = {}) {
        return this.request(url, {
            method: 'DELETE',
            ...options
        });
    }

    /**
     * Perform HTTP request with retry logic
     * @param {string} url - Request URL
     * @param {Object} options - Fetch options
     * @returns {Promise<Response>} - Fetch response
     */
    async request(url, options = {}) {
        const mergedOptions = {
            ...options,
            headers: {
                ...this.defaultHeaders,
                ...options.headers
            }
        };

        let lastError;
        for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.timeout);

                const response = await fetch(url, {
                    ...mergedOptions,
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                if (!response.ok) {
                    throw new HttpError(response.status, response.statusText, response);
                }

                return response;
            } catch (error) {
                lastError = error;

                // Don't retry on client errors (4xx) except 408 (timeout)
                if (error instanceof HttpError && 
                    error.status >= 400 && 
                    error.status < 500 && 
                    error.status !== 408) {
                    throw error;
                }

                // Don't retry if this was the last attempt
                if (attempt === this.maxRetries) {
                    break;
                }

                // Calculate exponential backoff delay
                const delay = this.retryDelay * Math.pow(2, attempt);
                console.warn(`Request failed (attempt ${attempt + 1}/${this.maxRetries + 1}). Retrying in ${delay}ms...`);
                
                await this.sleep(delay);
            }
        }

        throw lastError;
    }

    /**
     * Sleep for specified milliseconds
     * @param {number} ms - Milliseconds to sleep
     * @returns {Promise<void>}
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

/**
 * Custom HTTP Error class
 */
class HttpError extends Error {
    constructor(status, statusText, response) {
        super(`HTTP ${status}: ${statusText}`);
        this.name = 'HttpError';
        this.status = status;
        this.statusText = statusText;
        this.response = response;
    }
}

// ============================================================================
// Cookie Utilities
// ============================================================================

const CookieUtils = {
    /**
     * Get cookie value by name
     * @param {string} name - Cookie name
     * @returns {string|null} - Cookie value or null if not found
     */
    getCookie(name) {
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
    },
    
    /**
     * Get CSRF token from cookie (checks both custom and default names)
     * @returns {string|null} - CSRF token or null if not found
     */
    getCSRFToken() {
        // Try custom cookie name first, then fall back to default
        return this.getCookie('exam_csrftoken') || this.getCookie('csrftoken');
    },

    /**
     * Set cookie
     * @param {string} name - Cookie name
     * @param {string} value - Cookie value
     * @param {number} days - Days until expiration
     * @param {Object} options - Additional cookie options
     */
    setCookie(name, value, days = 7, options = {}) {
        let expires = '';
        if (days) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = `; expires=${date.toUTCString()}`;
        }

        const path = options.path || '/';
        const domain = options.domain ? `; domain=${options.domain}` : '';
        const secure = options.secure ? '; secure' : '';
        const sameSite = options.sameSite ? `; samesite=${options.sameSite}` : '';

        document.cookie = `${name}=${encodeURIComponent(value)}${expires}; path=${path}${domain}${secure}${sameSite}`;
    },

    /**
     * Delete cookie
     * @param {string} name - Cookie name
     */
    deleteCookie(name) {
        this.setCookie(name, '', -1);
    }
};

// ============================================================================
// Local Storage Utilities
// ============================================================================

const StorageUtils = {
    /**
     * Get item from local storage
     * @param {string} key - Storage key
     * @param {*} defaultValue - Default value if key doesn't exist
     * @returns {*} - Stored value or default
     */
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error(`Error reading from localStorage: ${error}`);
            return defaultValue;
        }
    },

    /**
     * Set item in local storage
     * @param {string} key - Storage key
     * @param {*} value - Value to store
     * @returns {boolean} - Success status
     */
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error(`Error writing to localStorage: ${error}`);
            return false;
        }
    },

    /**
     * Remove item from local storage
     * @param {string} key - Storage key
     */
    remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error(`Error removing from localStorage: ${error}`);
        }
    },

    /**
     * Clear all items from local storage
     */
    clear() {
        try {
            localStorage.clear();
        } catch (error) {
            console.error(`Error clearing localStorage: ${error}`);
        }
    },

    /**
     * Check if key exists in local storage
     * @param {string} key - Storage key
     * @returns {boolean} - True if key exists
     */
    has(key) {
        return localStorage.getItem(key) !== null;
    },

    /**
     * Get all keys from local storage
     * @returns {string[]} - Array of keys
     */
    keys() {
        return Object.keys(localStorage);
    }
};

// ============================================================================
// Form Utilities
// ============================================================================

const FormUtils = {
    /**
     * Serialize form data to object
     * @param {HTMLFormElement} form - Form element
     * @returns {Object} - Form data as object
     */
    serialize(form) {
        const formData = new FormData(form);
        const data = {};

        for (const [key, value] of formData.entries()) {
            // Handle multiple values for same key (checkboxes, multi-select)
            if (data.hasOwnProperty(key)) {
                if (!Array.isArray(data[key])) {
                    data[key] = [data[key]];
                }
                data[key].push(value);
            } else {
                data[key] = value;
            }
        }

        return data;
    },

    /**
     * Serialize form data to JSON string
     * @param {HTMLFormElement} form - Form element
     * @returns {string} - JSON string
     */
    serializeJSON(form) {
        return JSON.stringify(this.serialize(form));
    },

    /**
     * Serialize form data to URL query string
     * @param {HTMLFormElement} form - Form element
     * @returns {string} - URL query string
     */
    serializeQuery(form) {
        const formData = new FormData(form);
        return new URLSearchParams(formData).toString();
    },

    /**
     * Populate form with data
     * @param {HTMLFormElement} form - Form element
     * @param {Object} data - Data to populate
     */
    populate(form, data) {
        for (const [key, value] of Object.entries(data)) {
            const input = form.elements[key];
            if (!input) continue;

            if (input.type === 'checkbox') {
                input.checked = Boolean(value);
            } else if (input.type === 'radio') {
                const radio = form.querySelector(`input[name="${key}"][value="${value}"]`);
                if (radio) radio.checked = true;
            } else if (input.tagName === 'SELECT' && input.multiple) {
                const values = Array.isArray(value) ? value : [value];
                Array.from(input.options).forEach(option => {
                    option.selected = values.includes(option.value);
                });
            } else {
                input.value = value;
            }
        }
    },

    /**
     * Reset form and clear validation errors
     * @param {HTMLFormElement} form - Form element
     */
    reset(form) {
        form.reset();
        
        // Clear validation errors
        const errorElements = form.querySelectorAll('.error-message');
        errorElements.forEach(el => el.remove());
        
        const errorInputs = form.querySelectorAll('.border-red-500');
        errorInputs.forEach(input => {
            input.classList.remove('border-red-500');
            input.classList.add('border-gray-300');
        });
    },

    /**
     * Disable form inputs
     * @param {HTMLFormElement} form - Form element
     */
    disable(form) {
        const inputs = form.querySelectorAll('input, textarea, select, button');
        inputs.forEach(input => input.disabled = true);
    },

    /**
     * Enable form inputs
     * @param {HTMLFormElement} form - Form element
     */
    enable(form) {
        const inputs = form.querySelectorAll('input, textarea, select, button');
        inputs.forEach(input => input.disabled = false);
    }
};

// ============================================================================
// DOM Utilities
// ============================================================================

const DOMUtils = {
    /**
     * Create element with attributes and content
     * @param {string} tag - HTML tag name
     * @param {Object} attributes - Element attributes
     * @param {string|HTMLElement|HTMLElement[]} content - Element content
     * @returns {HTMLElement} - Created element
     */
    createElement(tag, attributes = {}, content = null) {
        const element = document.createElement(tag);

        // Set attributes
        for (const [key, value] of Object.entries(attributes)) {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'dataset') {
                for (const [dataKey, dataValue] of Object.entries(value)) {
                    element.dataset[dataKey] = dataValue;
                }
            } else {
                element.setAttribute(key, value);
            }
        }

        // Set content
        if (content !== null) {
            if (typeof content === 'string') {
                element.textContent = content;
            } else if (Array.isArray(content)) {
                content.forEach(child => {
                    if (child instanceof HTMLElement) {
                        element.appendChild(child);
                    }
                });
            } else if (content instanceof HTMLElement) {
                element.appendChild(content);
            }
        }

        return element;
    },

    /**
     * Remove element from DOM
     * @param {HTMLElement|string} element - Element or selector
     */
    remove(element) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (el && el.parentNode) {
            el.parentNode.removeChild(el);
        }
    },

    /**
     * Show element
     * @param {HTMLElement|string} element - Element or selector
     */
    show(element) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (el) {
            el.classList.remove('hidden');
        }
    },

    /**
     * Hide element
     * @param {HTMLElement|string} element - Element or selector
     */
    hide(element) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (el) {
            el.classList.add('hidden');
        }
    },

    /**
     * Toggle element visibility
     * @param {HTMLElement|string} element - Element or selector
     */
    toggle(element) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (el) {
            el.classList.toggle('hidden');
        }
    }
};

// ============================================================================
// Notification Manager (SweetAlert2 Wrapper)
// ============================================================================

const NotificationManager = {
    /**
     * Show notification message using SweetAlert2
     * @param {string} message - Message text
     * @param {string} type - Message type (success, error, warning, info)
     * @param {number} duration - Duration in milliseconds (0 for persistent)
     * @returns {Promise} - SweetAlert2 promise
     */
    show(message, type = 'info', duration = 5000) {
        // Check if SweetAlert2 is loaded
        if (typeof Swal === 'undefined') {
            return Promise.resolve();
        }

        // Validate parameters
        if (!message || typeof message !== 'string') {
            return Promise.resolve();
        }

        if (!['success', 'error', 'warning', 'info'].includes(type)) {
            type = 'info';
        }

        if (typeof duration !== 'number' || duration < 0) {
            duration = 5000;
        }

        // Base SweetAlert2 toast configuration
        const config = {
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            icon: type,
            title: message,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer);
                toast.addEventListener('mouseleave', Swal.resumeTimer);
            }
        };

        // Handle duration (0 means persistent)
        if (duration > 0) {
            config.timer = duration;
        } else {
            config.showCloseButton = true;
        }

        return Swal.fire(config);
    },

    /**
     * Show success notification
     * @param {string} message - Message text
     * @param {number} duration - Duration in milliseconds
     * @returns {Promise} - SweetAlert2 promise
     */
    success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    },

    /**
     * Show error notification
     * @param {string} message - Message text
     * @param {number} duration - Duration in milliseconds
     * @returns {Promise} - SweetAlert2 promise
     */
    error(message, duration = 5000) {
        return this.show(message, 'error', duration);
    },

    /**
     * Show warning notification
     * @param {string} message - Message text
     * @param {number} duration - Duration in milliseconds
     * @returns {Promise} - SweetAlert2 promise
     */
    warning(message, duration = 5000) {
        return this.show(message, 'warning', duration);
    },

    /**
     * Show info notification
     * @param {string} message - Message text
     * @param {number} duration - Duration in milliseconds
     * @returns {Promise} - SweetAlert2 promise
     */
    info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    }
};

// ============================================================================
// String Utilities
// ============================================================================

const StringUtils = {
    /**
     * Capitalize first letter of string
     * @param {string} str - Input string
     * @returns {string} - Capitalized string
     */
    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    },

    /**
     * Convert string to title case
     * @param {string} str - Input string
     * @returns {string} - Title case string
     */
    titleCase(str) {
        return str.toLowerCase().split(' ').map(word => this.capitalize(word)).join(' ');
    },

    /**
     * Truncate string to specified length
     * @param {string} str - Input string
     * @param {number} length - Maximum length
     * @param {string} suffix - Suffix to add (default: '...')
     * @returns {string} - Truncated string
     */
    truncate(str, length, suffix = '...') {
        if (str.length <= length) return str;
        return str.substring(0, length - suffix.length) + suffix;
    },

    /**
     * Escape HTML special characters
     * @param {string} str - Input string
     * @returns {string} - Escaped string
     */
    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    /**
     * Strip HTML tags from string
     * @param {string} html - HTML string
     * @returns {string} - Plain text
     */
    stripHtml(html) {
        const div = document.createElement('div');
        div.innerHTML = html;
        return div.textContent || div.innerText || '';
    }
};

// ============================================================================
// Validation Utilities
// ============================================================================

const ValidationUtils = {
    /**
     * Validate email format
     * @param {string} email - Email address
     * @returns {boolean} - True if valid
     */
    isEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    },

    /**
     * Validate URL format
     * @param {string} url - URL string
     * @returns {boolean} - True if valid
     */
    isUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    },

    /**
     * Validate number
     * @param {*} value - Value to validate
     * @returns {boolean} - True if valid number
     */
    isNumber(value) {
        return !isNaN(parseFloat(value)) && isFinite(value);
    },

    /**
     * Validate integer
     * @param {*} value - Value to validate
     * @returns {boolean} - True if valid integer
     */
    isInteger(value) {
        return Number.isInteger(Number(value));
    },

    /**
     * Check if value is empty
     * @param {*} value - Value to check
     * @returns {boolean} - True if empty
     */
    isEmpty(value) {
        if (value === null || value === undefined) return true;
        if (typeof value === 'string') return value.trim() === '';
        if (Array.isArray(value)) return value.length === 0;
        if (typeof value === 'object') return Object.keys(value).length === 0;
        return false;
    }
};

// ============================================================================
// Date/Time Utilities
// ============================================================================

const DateUtils = {
    /**
     * Format date to readable string
     * @param {Date|string|number} date - Date to format
     * @param {Object} options - Intl.DateTimeFormat options
     * @returns {string} - Formatted date string
     */
    format(date, options = {}) {
        const d = date instanceof Date ? date : new Date(date);
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            ...options
        };
        return new Intl.DateTimeFormat('en-US', defaultOptions).format(d);
    },

    /**
     * Format time to readable string
     * @param {Date|string|number} date - Date to format
     * @returns {string} - Formatted time string
     */
    formatTime(date) {
        const d = date instanceof Date ? date : new Date(date);
        return d.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
    },

    /**
     * Format date and time
     * @param {Date|string|number} date - Date to format
     * @returns {string} - Formatted date and time string
     */
    formatDateTime(date) {
        return `${this.format(date)} ${this.formatTime(date)}`;
    },

    /**
     * Get relative time string (e.g., "2 hours ago")
     * @param {Date|string|number} date - Date to compare
     * @returns {string} - Relative time string
     */
    relative(date) {
        const d = date instanceof Date ? date : new Date(date);
        const now = new Date();
        const seconds = Math.floor((now - d) / 1000);

        if (seconds < 60) return 'just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`;
        
        return this.format(d);
    }
};

// ============================================================================
// Export utilities to global scope
// ============================================================================

window.AjaxClient = AjaxClient;
window.HttpError = HttpError;
window.CookieUtils = CookieUtils;
window.StorageUtils = StorageUtils;
window.FormUtils = FormUtils;
window.DOMUtils = DOMUtils;
window.NotificationManager = NotificationManager;
window.StringUtils = StringUtils;
window.ValidationUtils = ValidationUtils;
window.DateUtils = DateUtils;

// Legacy compatibility - expose getCookie globally for existing code
window.getCookie = CookieUtils.getCookie;
window.getCSRFToken = CookieUtils.getCSRFToken.bind(CookieUtils);

