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
// Notification Manager (Notyf Wrapper)
// ============================================================================

/** Valid notification types accepted by the Notyf wrapper. */
const NOTIFICATION_VALID_TYPES = ['success', 'error', 'warning', 'info'];

/**
 * Per-type default durations (ms). 0 means "persistent until dismissed".
 * Mirrors section 4 of the design and Requirement 5.3.
 */
const NOTIFICATION_DEFAULT_DURATIONS = {
    success: 5000,
    error: 0,
    warning: 7000,
    info: 5000
};

/**
 * Build a `NotificationHandle` wrapping a real `NotyfNotification`.
 *
 * The handle exposes:
 *   - `notyfNotification`: the underlying Notyf object (or `null` for inert).
 *   - `dismiss()`: dismisses the toast on the given Notyf instance, tolerating
 *     a missing notification or instance.
 *   - `then(onFulfilled, onRejected)`: returns `Promise.resolve(undefined)`
 *     run through the supplied callbacks, so legacy SweetAlert2-style chains
 *     such as `NotificationManager.success(msg).then(reload)` keep working.
 *
 * @param {object} notyfNotification - The `NotyfNotification` returned by
 *   `instance.open(...)`.
 * @param {object} instance - The Notyf instance backing this handle.
 * @returns {NotificationHandle}
 */
function _createNotificationHandle(notyfNotification, instance) {
    return {
        notyfNotification: notyfNotification,
        dismiss() {
            if (notyfNotification && instance && typeof instance.dismiss === 'function') {
                instance.dismiss(notyfNotification);
            }
        },
        then(onFulfilled, onRejected) {
            return Promise.resolve(undefined).then(onFulfilled, onRejected);
        }
    };
}

/**
 * Build an inert `NotificationHandle` used when no toast was actually opened
 * (invalid message, or Notyf not yet loaded so the call was queued).
 *
 * The inert handle's `dismiss()` is a no-op and its `then(...)` resolves
 * immediately so callers cannot tell the difference from a real handle.
 *
 * @returns {NotificationHandle}
 */
function _createInertNotificationHandle() {
    return {
        notyfNotification: null,
        dismiss() { /* no-op */ },
        then(onFulfilled, onRejected) {
            return Promise.resolve(undefined).then(onFulfilled, onRejected);
        }
    };
}

/**
 * Notification Manager — thin wrapper around a single lazy Notyf instance.
 *
 * Public API (preserved from the prior SweetAlert2-backed wrapper):
 *   show(message, type, duration), success(...), error(...),
 *   warning(...), info(...).
 *
 * Per-type default durations live on the Notyf instance's type config and are
 * applied automatically when `duration` is omitted: success/info = 5000ms,
 * warning = 7000ms, error = 0 (persistent).
 *
 * Skeleton wiring (subtask 2.1):
 *   - `_instance` is constructed lazily on first call via `_ensureInstance()`.
 *   - If `Notyf` has not yet loaded (script load race), calls are pushed onto
 *     `_queue` and replayed once `window` fires `load`. If `Notyf` is still
 *     undefined after `load`, queued entries are warned and dropped.
 *   - Exactly one Notyf instance is constructed and reused for every toast.
 *
 * Input normalization (subtask 2.2):
 *   - `message` is required to be a non-empty string after `String(...).trim()`;
 *     anything else returns an inert handle without calling `notyf.open`.
 *   - `type` outside `{success, error, warning, info}` becomes `'info'`.
 *   - `duration` that is not a finite non-negative `Number` becomes the
 *     per-type default from `NOTIFICATION_DEFAULT_DURATIONS`.
 *   - The returned `NotificationHandle` exposes `notyfNotification`,
 *     `dismiss()`, and a thenable `then(...)` that resolves to `undefined`.
 *
 * Subtask 2.3 fills in:
 *   - `dismiss(handle)`, `dismissAll()`, and the `showError` alias.
 */
const NotificationManager = {
    /** Lazy-constructed Notyf instance. Built once on first use. */
    _instance: null,

    /** Pending entries buffered while `window.Notyf` is undefined. */
    _queue: [],

    /** Whether the one-shot `load` listener has already been registered. */
    _loadListenerRegistered: false,

    /**
     * Construct (or return) the single Notyf instance with the design's full
     * type configuration: top-right position, dismissible + ripple, the four
     * type definitions with their backgrounds, icons, and per-type durations.
     *
     * @returns {object|null} The Notyf instance, or `null` if `Notyf` is not
     *   yet loaded. Callers must queue and register the load listener in that
     *   case.
     */
    _ensureInstance() {
        if (this._instance) {
            return this._instance;
        }
        if (typeof Notyf === 'undefined') {
            return null;
        }
        this._instance = new Notyf({
            duration: 5000,
            position: { x: 'right', y: 'top' },
            dismissible: true,
            ripple: true,
            types: [
                {
                    type: 'success',
                    background: '#16a34a',
                    duration: 5000,
                    dismissible: true,
                    icon: { className: 'notyf__icon--success', tagName: 'span' }
                },
                {
                    type: 'error',
                    background: '#dc2626',
                    duration: 0,
                    dismissible: true,
                    icon: { className: 'notyf__icon--error', tagName: 'span' }
                },
                {
                    type: 'warning',
                    background: '#d97706',
                    duration: 7000,
                    dismissible: true,
                    icon: { className: 'notyf__icon--warning', tagName: 'span' },
                    className: 'notyf__toast--warning'
                },
                {
                    type: 'info',
                    background: '#2563eb',
                    duration: 5000,
                    dismissible: true,
                    icon: { className: 'notyf__icon--info', tagName: 'span' },
                    className: 'notyf__toast--info'
                }
            ]
        });
        return this._instance;
    },

    /**
     * Register a single one-shot `load` listener that flushes the queue once
     * Notyf becomes available. Subsequent registrations are no-ops.
     */
    _registerLoadListener() {
        if (this._loadListenerRegistered) {
            return;
        }
        if (typeof window === 'undefined' || typeof window.addEventListener !== 'function') {
            return;
        }
        this._loadListenerRegistered = true;
        const self = this;
        window.addEventListener('load', function flushOnLoad() {
            self._flushQueue();
        }, { once: true });
    },

    /**
     * Replay every queued entry through the Notyf instance in arrival order.
     * If Notyf is still unavailable, log a warning and drop each entry.
     *
     * Each queued entry has already been input-normalized by `show(...)` so
     * `type` is a member of `NOTIFICATION_VALID_TYPES` and `duration` is a
     * finite non-negative `Number`.
     */
    _flushQueue() {
        const queued = this._queue;
        this._queue = [];
        const instance = this._ensureInstance();
        if (!instance) {
            queued.forEach(entry => {
                console.warn(
                    'NotificationManager: Notyf is not available; dropping queued message:',
                    entry && entry.message
                );
            });
            return;
        }
        queued.forEach(entry => {
            instance.open({
                type: entry.type,
                message: entry.message,
                duration: entry.duration
            });
        });
    },

    /**
     * Show a toast.
     *
     * Input normalization (Requirements 2.2, 2.3, 2.5):
     *   - `message` must be a non-empty string. Non-strings drop with an
     *     inert handle (Requirement 2.4 / Property 2). Strings that are
     *     empty or contain only whitespace after `.trim()` are also dropped.
     *     Non-empty strings (including multi-line) are passed through to
     *     `notyf.open` verbatim — `.trim()` is used only as the empty check,
     *     not to reformat the rendered text.
     *   - `type` is normalized to `'info'` if it is not one of
     *     `{success, error, warning, info}` (Requirement 2.3).
     *   - `duration` is normalized to the per-type default from the design's
     *     section 4 table if it is not a finite non-negative `Number`
     *     (Requirement 2.5).
     *
     * Output (Requirement 2.6):
     *   - Returns a `NotificationHandle` exposing `notyfNotification`,
     *     `dismiss()`, and a thenable `then(...)` that resolves to
     *     `undefined`. Legacy `NotificationManager.success(msg).then(...)`
     *     chains keep working.
     *   - When Notyf is not yet loaded, the call is queued (with normalized
     *     values) and an inert handle is returned whose `dismiss()` is a
     *     no-op and whose `then(...)` resolves immediately (Requirement 2.7).
     *
     * @param {string} message
     * @param {string} [type='info']
     * @param {number} [duration]
     * @returns {NotificationHandle}
     */
    show(message, type, duration) {
        // Coerce + validate message. Per Requirement 2.4 / Property 2, both
        // non-strings and empty strings drop. We additionally apply a
        // defensive `String(...)` and `.trim()` to detect whitespace-only
        // strings (e.g. '   ') as empty.
        if (typeof message !== 'string') {
            return _createInertNotificationHandle();
        }
        let coercedMessage;
        try {
            coercedMessage = String(message);
        } catch (err) {
            return _createInertNotificationHandle();
        }
        if (coercedMessage.trim() === '') {
            return _createInertNotificationHandle();
        }

        // Normalize type: anything outside the valid set becomes 'info'.
        const resolvedType = NOTIFICATION_VALID_TYPES.indexOf(type) !== -1
            ? type
            : 'info';

        // Normalize duration: anything that is not a finite non-negative
        // Number becomes the per-type default. `Number.isFinite` rejects
        // strings, NaN, and ±Infinity without coercion.
        const resolvedDuration =
            typeof duration === 'number' && Number.isFinite(duration) && duration >= 0
                ? duration
                : NOTIFICATION_DEFAULT_DURATIONS[resolvedType];

        const instance = this._ensureInstance();
        if (!instance) {
            this._queue.push({
                message: coercedMessage,
                type: resolvedType,
                duration: resolvedDuration
            });
            this._registerLoadListener();
            return _createInertNotificationHandle();
        }

        const notyfNotification = instance.open({
            type: resolvedType,
            message: coercedMessage,
            duration: resolvedDuration
        });
        return _createNotificationHandle(notyfNotification, instance);
    },

    /**
     * Show a success toast. Default duration is the per-type default (5000ms)
     * applied by Notyf's type config when `duration` is omitted.
     */
    success(message, duration) {
        return this.show(message, 'success', duration);
    },

    /**
     * Show an error toast. Default duration is 0 (persistent) per the per-type
     * configuration; the user must dismiss it manually.
     */
    error(message, duration) {
        return this.show(message, 'error', duration);
    },

    /** Show a warning toast. Default duration is 7000ms. */
    warning(message, duration) {
        return this.show(message, 'warning', duration);
    },

    /** Show an info toast. Default duration is 5000ms. */
    info(message, duration) {
        return this.show(message, 'info', duration);
    },

    /**
     * Alias of `error(message, duration)`. Kept to absorb existing typo call
     * sites (`NotificationManager.showError(...)`) in `pages/exam-form.js` and
     * `pages/student-profile.js` without rewriting every caller.
     *
     * Validates: Requirement 7.4.
     */
    showError(message, duration) {
        return this.error(message, duration);
    },

    /**
     * Dismiss a single toast given its handle.
     *
     * Tolerates `null`, `undefined`, and inert handles (whose own `dismiss()`
     * is a no-op because the toast was queued before Notyf loaded). Any
     * non-handle value with no `dismiss` method is silently ignored.
     *
     * Validates: Requirement 5.6.
     *
     * @param {NotificationHandle|null|undefined} handle
     */
    dismiss(handle) {
        if (handle && typeof handle.dismiss === 'function') {
            handle.dismiss();
        }
    },

    /**
     * Dismiss every visible toast.
     *
     * If the Notyf instance has been built, delegate to `notyf.dismissAll()`.
     * Otherwise the only "visible" toasts are the entries still pending in
     * `_queue` (Notyf has not loaded yet); empty the queue so nothing replays
     * once `load` fires.
     *
     * Validates: Requirement 5.6.
     */
    dismissAll() {
        if (this._instance && typeof this._instance.dismissAll === 'function') {
            this._instance.dismissAll();
            return;
        }
        this._queue = [];
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

