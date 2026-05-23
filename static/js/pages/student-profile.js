/**
 * Student Profile Page JavaScript
 * Handles profile picture upload, deletion, and password change functionality
 */

class StudentProfile {
    constructor() {
        this.init();
    }

    init() {
        this.setupProfilePictureUpload();
        this.setupProfilePictureDeletion();
        this.setupPasswordChangeValidation();
    }

    /**
     * Setup profile picture upload with AJAX
     */
    setupProfilePictureUpload() {
        const uploadForm = document.getElementById('profile-picture-form');
        if (!uploadForm) return;

        uploadForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleProfilePictureUpload(uploadForm);
        });
    }

    /**
     * Handle profile picture upload
     * @param {HTMLFormElement} form - The upload form
     */
    async handleProfilePictureUpload(form) {
        const formData = new FormData(form);
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        
        // Get upload URL from data attribute or form action
        const uploadUrl = form.dataset.uploadUrl || form.action;
        
        // Disable button and show loading state
        submitBtn.disabled = true;
        submitBtn.textContent = 'Uploading...';
        
        try {
            const response = await fetch(uploadUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Reload page to show updated picture
                window.location.reload();
            } else {
                this.showError('Error: ' + (data.error || 'Failed to upload picture'));
                this.resetButton(submitBtn, originalText);
            }
        } catch (error) {
            this.showError('Error uploading picture. Please try again.');
            this.resetButton(submitBtn, originalText);
        }
    }

    /**
     * Setup profile picture deletion
     */
    setupProfilePictureDeletion() {
        const deleteBtn = document.getElementById('delete-picture-btn');
        if (!deleteBtn) return;

        deleteBtn.addEventListener('click', () => {
            this.handleProfilePictureDeletion(deleteBtn);
        });
    }

    /**
     * Handle profile picture deletion
     * @param {HTMLButtonElement} deleteBtn - The delete button
     */
    async handleProfilePictureDeletion(deleteBtn) {
        if (!confirm('Are you sure you want to remove your profile picture?')) {
            return;
        }
        
        const originalText = deleteBtn.textContent;
        deleteBtn.disabled = true;
        deleteBtn.textContent = 'Removing...';
        
        // Get delete URL from data attribute or use upload URL
        const deleteUrl = deleteBtn.dataset.deleteUrl || 
                         document.getElementById('profile-picture-form')?.action;
        
        if (!deleteUrl) {
            this.showError('Delete URL not found');
            this.resetButton(deleteBtn, originalText);
            return;
        }
        
        try {
            const response = await fetch(deleteUrl, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Reload page to show default avatar
                window.location.reload();
            } else {
                this.showError('Error: ' + (data.error || 'Failed to delete picture'));
                this.resetButton(deleteBtn, originalText);
            }
        } catch (error) {
            this.showError('Error deleting picture. Please try again.');
            this.resetButton(deleteBtn, originalText);
        }
    }

    /**
     * Setup password change form validation
     */
    setupPasswordChangeValidation() {
        const passwordForm = document.getElementById('password-change-form');
        if (!passwordForm) return;

        const newPasswordField = document.getElementById('id_new_password');
        const confirmPasswordField = document.getElementById('id_confirm_password');

        if (newPasswordField && confirmPasswordField) {
            // Real-time password confirmation validation
            confirmPasswordField.addEventListener('input', () => {
                this.validatePasswordMatch(newPasswordField, confirmPasswordField);
            });

            // Password strength validation
            newPasswordField.addEventListener('input', () => {
                this.validatePasswordStrength(newPasswordField);
            });
        }

        // Form submission validation
        passwordForm.addEventListener('submit', (e) => {
            if (!this.validatePasswordForm(passwordForm)) {
                e.preventDefault();
            }
        });
    }

    /**
     * Validate password match
     * @param {HTMLInputElement} newPasswordField - New password field
     * @param {HTMLInputElement} confirmPasswordField - Confirm password field
     */
    validatePasswordMatch(newPasswordField, confirmPasswordField) {
        const newPassword = newPasswordField.value;
        const confirmPassword = confirmPasswordField.value;

        if (confirmPassword && newPassword !== confirmPassword) {
            confirmPasswordField.setCustomValidity('Passwords do not match');
            this.showFieldError(confirmPasswordField, 'Passwords do not match');
        } else {
            confirmPasswordField.setCustomValidity('');
            this.clearFieldError(confirmPasswordField);
        }
    }

    /**
     * Validate password strength
     * @param {HTMLInputElement} passwordField - Password field
     */
    validatePasswordStrength(passwordField) {
        const password = passwordField.value;
        const requirements = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            number: /\d/.test(password)
        };

        const isValid = Object.values(requirements).every(req => req);
        
        if (password && !isValid) {
            const missingReqs = [];
            if (!requirements.length) missingReqs.push('at least 8 characters');
            if (!requirements.uppercase) missingReqs.push('uppercase letter');
            if (!requirements.lowercase) missingReqs.push('lowercase letter');
            if (!requirements.number) missingReqs.push('number');
            
            const message = `Password must contain: ${missingReqs.join(', ')}`;
            this.showFieldError(passwordField, message);
        } else {
            this.clearFieldError(passwordField);
        }
    }

    /**
     * Validate entire password form
     * @param {HTMLFormElement} form - Password form
     * @returns {boolean} - Whether form is valid
     */
    validatePasswordForm(form) {
        const currentPassword = form.querySelector('#id_current_password').value;
        const newPassword = form.querySelector('#id_new_password').value;
        const confirmPassword = form.querySelector('#id_confirm_password').value;

        if (!currentPassword) {
            this.showError('Current password is required');
            return false;
        }

        if (!newPassword) {
            this.showError('New password is required');
            return false;
        }

        if (newPassword !== confirmPassword) {
            this.showError('New passwords do not match');
            return false;
        }

        if (newPassword.length < 8) {
            this.showError('New password must be at least 8 characters long');
            return false;
        }

        return true;
    }

    /**
     * Show field-specific error
     * @param {HTMLInputElement} field - Input field
     * @param {string} message - Error message
     */
    showFieldError(field, message) {
        // Remove existing error
        this.clearFieldError(field);

        // Add error styling
        field.classList.add('border-red-500', 'focus:ring-red-500', 'focus:border-red-500');
        field.classList.remove('border-gray-300', 'focus:ring-blue-500', 'focus:border-blue-500');

        // Create error message element
        const errorElement = document.createElement('p');
        errorElement.className = 'mt-1 text-xs text-red-600';
        errorElement.textContent = message;
        errorElement.setAttribute('data-field-error', field.id);

        // Insert error message after field
        field.parentNode.insertBefore(errorElement, field.nextSibling);
    }

    /**
     * Clear field-specific error
     * @param {HTMLInputElement} field - Input field
     */
    clearFieldError(field) {
        // Remove error styling
        field.classList.remove('border-red-500', 'focus:ring-red-500', 'focus:border-red-500');
        field.classList.add('border-gray-300', 'focus:ring-blue-500', 'focus:border-blue-500');

        // Remove error message
        const errorElement = field.parentNode.querySelector(`[data-field-error="${field.id}"]`);
        if (errorElement) {
            errorElement.remove();
        }
    }

    /**
     * Show general error message
     * @param {string} message - Error message
     */
    showError(message) {
        // Use existing notification system if available
        if (window.NotificationManager) {
            window.NotificationManager.showError(message);
        }
    }

    /**
     * Reset button to original state
     * @param {HTMLButtonElement} button - Button element
     * @param {string} originalText - Original button text
     */
    resetButton(button, originalText) {
        button.disabled = false;
        button.textContent = originalText;
    }

    /**
     * Get CSRF token from form or cookie
     * @returns {string} - CSRF token
     */
    getCSRFToken() {
        // Try to get from form first
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            return csrfInput.value;
        }

        // Fallback to cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }

        return '';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new StudentProfile();
});