// Main JavaScript file for Gradely
// Uses utility functions from utils.js

// Utility function for AJAX requests (uses AjaxClient from utils.js)
async function fetchJSON(url, options = {}) {
    try {
        const client = new AjaxClient({ maxRetries: 1 });
        const response = await client.request(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });
        
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

// Show alert message (uses NotificationManager from utils.js)
function showAlert(message, type = 'info') {
    NotificationManager.show(message, type);
}

// Form validation helper
function validateForm(formElement) {
    const inputs = formElement.querySelectorAll('[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('border-red-500');
        } else {
            input.classList.remove('border-red-500');
        }
    });
    
    return isValid;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add form validation to all forms
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
                showAlert('Please fill in all required fields', 'error');
            }
        });
    });
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
    
    // Handle dismissible alerts
    const alertCloseButtons = document.querySelectorAll('.alert-close');
    alertCloseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const alertContainer = this.closest('.alert-container');
            if (alertContainer) {
                alertContainer.style.opacity = '0';
                setTimeout(() => alertContainer.remove(), 300);
            }
        });
    });
});

