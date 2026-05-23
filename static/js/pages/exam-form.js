/**
 * Exam Form JavaScript
 * Handles exam creation form navigation, validation, and submission
 */

class ExamForm {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 2; // Basic info and confirmation
        this.init();
    }

    init() {
        this.setupFormValidation();
        this.setupNavigation();
        this.setupFormSubmission();
    }

    /**
     * Setup form validation
     */
    setupFormValidation() {
        const form = document.getElementById('examForm');
        if (!form) return;

        // Real-time validation for required fields
        const requiredFields = form.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            field.addEventListener('blur', () => {
                this.validateField(field);
            });

            field.addEventListener('input', () => {
                this.clearFieldError(field);
            });
        });

        // Duration validation
        const durationField = document.getElementById('duration_minutes');
        if (durationField) {
            durationField.addEventListener('input', () => {
                this.validateDuration(durationField);
            });
        }
    }

    /**
     * Setup navigation between form steps
     */
    setupNavigation() {
        const nextBtn = document.getElementById('nextBtn');
        const prevBtn = document.getElementById('prevBtn');
        const submitBtn = document.getElementById('submitBtn');

        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                this.handleNextStep();
            });
        }

        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                this.handlePreviousStep();
            });
        }
    }

    /**
     * Setup form submission
     */
    setupFormSubmission() {
        const form = document.getElementById('examForm');
        if (!form) return;

        form.addEventListener('submit', (e) => {
            if (!this.validateForm()) {
                e.preventDefault();
                return false;
            }

            this.handleFormSubmission(form);
        });
    }

    /**
     * Handle next step navigation
     */
    handleNextStep() {
        if (!this.validateCurrentStep()) {
            return;
        }

        if (this.currentStep < this.totalSteps) {
            this.currentStep++;
            this.updateStepDisplay();
        }
    }

    /**
     * Handle previous step navigation
     */
    handlePreviousStep() {
        if (this.currentStep > 1) {
            this.currentStep--;
            this.updateStepDisplay();
        }
    }

    /**
     * Update step display and button visibility
     */
    updateStepDisplay() {
        const nextBtn = document.getElementById('nextBtn');
        const prevBtn = document.getElementById('prevBtn');
        const submitBtn = document.getElementById('submitBtn');

        // Show/hide previous button
        if (prevBtn) {
            if (this.currentStep > 1) {
                prevBtn.classList.remove('hidden');
            } else {
                prevBtn.classList.add('hidden');
            }
        }

        // Show/hide next/submit buttons
        if (this.currentStep === this.totalSteps) {
            if (nextBtn) nextBtn.classList.add('hidden');
            if (submitBtn) submitBtn.classList.remove('hidden');
        } else {
            if (nextBtn) nextBtn.classList.remove('hidden');
            if (submitBtn) submitBtn.classList.add('hidden');
        }

        // Update step indicators if they exist
        this.updateStepIndicators();
    }

    /**
     * Update step indicators
     */
    updateStepIndicators() {
        const indicators = document.querySelectorAll('[data-step-indicator]');
        indicators.forEach((indicator, index) => {
            const stepNumber = index + 1;
            if (stepNumber === this.currentStep) {
                indicator.classList.add('active');
            } else if (stepNumber < this.currentStep) {
                indicator.classList.add('completed');
                indicator.classList.remove('active');
            } else {
                indicator.classList.remove('active', 'completed');
            }
        });
    }

    /**
     * Validate current step
     * @returns {boolean} - Whether current step is valid
     */
    validateCurrentStep() {
        const form = document.getElementById('examForm');
        if (!form) return false;

        // For step 1, validate basic form fields
        if (this.currentStep === 1) {
            return this.validateBasicFields();
        }

        return true;
    }

    /**
     * Validate basic form fields
     * @returns {boolean} - Whether basic fields are valid
     */
    validateBasicFields() {
        const titleField = document.getElementById('title');
        const durationField = document.getElementById('duration_minutes');

        let isValid = true;

        if (!this.validateField(titleField)) {
            isValid = false;
        }

        if (!this.validateDuration(durationField)) {
            isValid = false;
        }

        return isValid;
    }

    /**
     * Validate entire form
     * @returns {boolean} - Whether form is valid
     */
    validateForm() {
        const form = document.getElementById('examForm');
        if (!form) return false;

        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        return isValid;
    }

    /**
     * Validate individual field
     * @param {HTMLInputElement} field - Field to validate
     * @returns {boolean} - Whether field is valid
     */
    validateField(field) {
        if (!field) return true;

        const value = field.value.trim();
        
        if (field.hasAttribute('required') && !value) {
            this.showFieldError(field, 'This field is required');
            return false;
        }

        if (field.type === 'number') {
            const numValue = parseFloat(value);
            const min = parseFloat(field.getAttribute('min'));
            const max = parseFloat(field.getAttribute('max'));

            if (isNaN(numValue)) {
                this.showFieldError(field, 'Please enter a valid number');
                return false;
            }

            if (min !== null && numValue < min) {
                this.showFieldError(field, `Value must be at least ${min}`);
                return false;
            }

            if (max !== null && numValue > max) {
                this.showFieldError(field, `Value must be no more than ${max}`);
                return false;
            }
        }

        this.clearFieldError(field);
        return true;
    }

    /**
     * Validate duration field specifically
     * @param {HTMLInputElement} durationField - Duration field
     * @returns {boolean} - Whether duration is valid
     */
    validateDuration(durationField) {
        if (!durationField) return true;

        const duration = parseInt(durationField.value);
        
        if (isNaN(duration) || duration < 1) {
            this.showFieldError(durationField, 'Duration must be at least 1 minute');
            return false;
        }

        if (duration > 480) { // 8 hours max
            this.showFieldError(durationField, 'Duration cannot exceed 8 hours (480 minutes)');
            return false;
        }

        this.clearFieldError(durationField);
        return true;
    }

    /**
     * Handle form submission
     * @param {HTMLFormElement} form - Form element
     */
    handleFormSubmission(form) {
        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating Exam...';
        }

        // Form will submit normally unless we prevent it
        // Add any additional submission logic here if needed
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
        errorElement.className = 'mt-1 text-sm text-red-600';
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
        // Use existing notification system if available, otherwise use alert
        if (window.NotificationManager) {
            window.NotificationManager.showError(message);
        } else {
            console.error(message);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ExamForm();
});