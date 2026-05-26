/**
 * Message Handler Component
 * Handles Django messages display using SweetAlert2 integration
 */

class MessageHandler {
    constructor() {
        this.init();
    }

    init() {
        this.setupMessageDisplay();
    }

    /**
     * Setup message display system
     */
    setupMessageDisplay() {
        // Check if messages data is available
        const messagesData = this.getMessagesData();
        if (!messagesData || messagesData.length === 0) return;

        // Display each message
        messagesData.forEach(message => {
            this.displayMessage(message.text, message.type);
        });
    }

    /**
     * Get messages data from DOM or global variable
     * @returns {Array} - Array of message objects
     */
    getMessagesData() {
        // Try to get from JSON script tag first
        const messagesScript = document.getElementById('django-messages-data');
        if (messagesScript) {
            try {
                return JSON.parse(messagesScript.textContent);
            } catch (e) {
                console.warn('Failed to parse messages data:', e);
            }
        }

        // Fallback to global variable if available
        if (window.djangoMessages) {
            return window.djangoMessages;
        }

        return [];
    }

    /**
     * Display a message using the notification system
     * @param {string} text - Message text
     * @param {string} type - Message type (success, error, warning, info)
     * @param {number} duration - Display duration in milliseconds
     */
    displayMessage(text, type = 'info', duration = 5000) {
        if (window.Notyf) {
            this.displayWithNotyf(text, type, duration);
            return;
        }

        if (window.Swal) {
            this.displayWithSweetAlert(text, type);
            return;
        }

        this.displayFallback(text, type);
    }

    /**
     * Display message using Notyf
     * @param {string} text - Message text
     * @param {string} type - Message type
     * @param {number} duration - Display duration in milliseconds
     */
    displayWithNotyf(text, type, duration = 5000) {
        if (!this._notyf) {
            this._notyf = new Notyf({
                duration: duration,
                position: { x: 'right', y: 'top' },
                dismissible: true,
                ripple: true,
                types: [
                    {
                        type: 'info',
                        background: '#3b82f6',
                        icon: { className: 'notyf__icon--info', tagName: 'i' }
                    },
                    {
                        type: 'warning',
                        background: '#f59e0b',
                        icon: { className: 'notyf__icon--warning', tagName: 'i' }
                    }
                ]
            });
        }

        const notyfType = (type === 'danger') ? 'error' : type;

        if (notyfType === 'success') {
            this._notyf.success(text);
        } else if (notyfType === 'error') {
            this._notyf.error(text);
        } else {
            this._notyf.open({ type: notyfType, message: text });
        }
    }

    /**
     * Display message using SweetAlert2 directly
     * @param {string} text - Message text
     * @param {string} type - Message type
     */
    displayWithSweetAlert(text, type) {
        const swalConfig = {
            text: text,
            icon: this.mapMessageTypeToSwalIcon(type),
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 5000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer);
                toast.addEventListener('mouseleave', Swal.resumeTimer);
            }
        };

        Swal.fire(swalConfig);
    }

    /**
     * Fallback message display
     * @param {string} text - Message text
     * @param {string} type - Message type
     */
    displayFallback(text, type) {
        // Log to console
        const logMethod = this.getConsoleMethod(type);
        console[logMethod](`[${type.toUpperCase()}] ${text}`);

        // Try to create a simple toast notification
        this.createSimpleToast(text, type);
    }

    /**
     * Create a simple toast notification
     * @param {string} text - Message text
     * @param {string} type - Message type
     */
    createSimpleToast(text, type) {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'fixed top-4 right-4 z-50 space-y-2';
            document.body.appendChild(toastContainer);
        }

        // Create toast element
        const toast = document.createElement('div');
        toast.className = `max-w-sm p-4 rounded-lg shadow-lg text-white transform transition-all duration-300 translate-x-full ${this.getToastBackgroundClass(type)}`;
        toast.textContent = text;

        // Add to container
        toastContainer.appendChild(toast);

        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);

        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 5000);

        // Allow manual dismissal
        toast.addEventListener('click', () => {
            toast.classList.add('translate-x-full');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        });
    }

    /**
     * Map Django message type to SweetAlert2 icon
     * @param {string} type - Django message type
     * @returns {string} - SweetAlert2 icon type
     */
    mapMessageTypeToSwalIcon(type) {
        const typeMap = {
            'success': 'success',
            'error': 'error',
            'danger': 'error',
            'warning': 'warning',
            'info': 'info',
            'debug': 'info'
        };

        return typeMap[type] || 'info';
    }

    /**
     * Get appropriate console method for message type
     * @param {string} type - Message type
     * @returns {string} - Console method name
     */
    getConsoleMethod(type) {
        const methodMap = {
            'success': 'log',
            'error': 'error',
            'danger': 'error',
            'warning': 'warn',
            'info': 'info',
            'debug': 'debug'
        };

        return methodMap[type] || 'log';
    }

    /**
     * Get background class for simple toast
     * @param {string} type - Message type
     * @returns {string} - CSS class for background
     */
    getToastBackgroundClass(type) {
        const classMap = {
            'success': 'bg-green-500',
            'error': 'bg-red-500',
            'danger': 'bg-red-500',
            'warning': 'bg-yellow-500',
            'info': 'bg-blue-500',
            'debug': 'bg-gray-500'
        };

        return classMap[type] || 'bg-blue-500';
    }

    /**
     * Map Django message tags to standard types
     * @param {string} tags - Django message tags
     * @returns {string} - Standardized message type
     */
    mapDjangoTags(tags) {
        if (tags.includes('success')) return 'success';
        if (tags.includes('error') || tags.includes('danger')) return 'error';
        if (tags.includes('warning')) return 'warning';
        if (tags.includes('debug')) return 'debug';
        return 'info';
    }

    /**
     * Static method to display a message programmatically
     * @param {string} text - Message text
     * @param {string} type - Message type
     * @param {number} duration - Display duration
     */
    static show(text, type = 'info', duration = 5000) {
        const handler = new MessageHandler();
        handler.displayMessage(text, type, duration);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MessageHandler();
});

// Make MessageHandler available globally for programmatic use
window.MessageHandler = MessageHandler;