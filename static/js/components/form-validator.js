/**
 * Form Validator Component
 * Provides reusable form validation functionality for the ExamMaker system
 * Extracted from first_time_setup.html and student_account_management.html
 * 
 * @author ExamMaker Development Team
 * @version 1.0.0
 * @since 2024
 * 
 * Requirements: 10.1, 10.2, 10.4 - Coding standards compliance
 */

class FormValidator extends BaseComponent {
    constructor(element, options = {}) {
        super(element, options);
    }
    
    static defaultOptions = {
        ...BaseComponent.defaultOptions,
        validateOnInput: true,
        validateOnBlur: true,
        showErrors: true,
        errorClass: 'form-error',
        successClass: 'form-success',
        passwordMinLength: 8,
        requiredFields: [],
        customValidators: {}
    };
    
    bindEvents() {
        if (!this.element) return;
        
        this.inputs = this.element.querySelectorAll('input, select, textarea');
        this.passwordFields = this.element.querySelectorAll('input[type="password"]');
        
        if (this.getOption('validateOnInput')) {
            this.inputs.forEach(input => {
                input.addEventListener('input', (e) => this.validateField(e.target));
            });
        }
        
        if (this.getOption('validateOnBlur')) {
            this.inputs.forEach(input => {
                input.addEventListener('blur', (e) => this.validateField(e.target));
            });
        }
        
        this.element.addEventListener('submit', (e) => this.handleSubmit(e));
        this.setupPasswordMatching();
        this.setupPasswordGeneration();
    }
    
    setupPasswordMatching() {
        const passwordField = this.element.querySelector('#password');
        const confirmField = this.element.querySelector('#password_confirm');
        
        if (passwordField && confirmField) {
            const validatePasswords = () => {
                if (passwordField.value !== confirmField.value) {
                    confirmField.setCustomValidity('Passwords do not match');
                    this.showFieldError(confirmField, 'Passwords do not match');
                } else {
                    confirmField.setCustomValidity('');
                    this.clearFieldError(confirmField);
                }
            };
            
            passwordField.addEventListener('input', validatePasswords);
            confirmField.addEventListener('input', validatePasswords);
        }
    }
    
    setupPasswordGeneration() {
        const previewBtn = this.element.querySelector('#preview-btn');
        const passwordPreview = this.element.querySelector('#password-preview');
        const previewPassword = this.element.querySelector('#preview-password');
        const schoolIdInput = this.element.querySelector('#id_school_id');
        const lastNameInput = this.element.querySelector('#id_last_name');
        
        if (previewBtn && passwordPreview && previewPassword && schoolIdInput && lastNameInput) {
            previewBtn.addEventListener('click', () => {
                const schoolId = schoolIdInput.value.trim();
                const lastName = lastNameInput.value.trim();
                
                if (!schoolId || !lastName) {
                    this.showError('Please enter Student ID and Last Name to preview password');
                    return;
                }
                
                const password = this.generatePassword(schoolId, lastName);
                previewPassword.textContent = password;
                passwordPreview.classList.remove('hidden');
            });
            
            const updatePreview = () => {
                if (passwordPreview.classList.contains('hidden')) return;
                const schoolId = schoolIdInput.value.trim();
                const lastName = lastNameInput.value.trim();
                if (schoolId && lastName) {
                    previewPassword.textContent = this.generatePassword(schoolId, lastName);
                }
            };
            
            schoolIdInput.addEventListener('input', updatePreview);
            lastNameInput.addEventListener('input', updatePreview);
        }
    }
    
    generatePassword(schoolId, lastName) {
        let digits = schoolId.replace(/\D/g, '').substring(0, 4);
        if (digits.length < 4) {
            digits = digits.padEnd(4, '0');
        }
        
        let letters = lastName.replace(/[^a-zA-Z]/g, '').substring(0, 4).toUpperCase();
        if (letters.length < 4) {
            letters = letters.padEnd(4, 'X');
        }
        
        return digits + letters;
    }
    
    validateField(field) {
        if (!field) return true;
        
        let isValid = true;
        let errorMessage = '';
        
        if (field.hasAttribute('required') && !field.value.trim()) {
            isValid = false;
            errorMessage = 'This field is required';
        }
        
        if (isValid && field.hasAttribute('minlength')) {
            const minLength = parseInt(field.getAttribute('minlength'));
            if (field.value.length < minLength) {
                isValid = false;
                errorMessage = `Minimum ${minLength} characters required`;
            }
        }
        
        if (isValid && field.type === 'email' && field.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(field.value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address';
            }
        }
        
        if (isValid && field.type === 'password' && field.value) {
            const minLength = this.getOption('passwordMinLength');
            if (field.value.length < minLength) {
                isValid = false;
                errorMessage = `Password must be at least ${minLength} characters`;
            }
        }
        
        const customValidators = this.getOption('customValidators');
        if (isValid && customValidators[field.name]) {
            const validator = customValidators[field.name];
            const result = validator(field.value, field);
            if (result !== true) {
                isValid = false;
                errorMessage = result || 'Invalid value';
            }
        }
        
        if (this.getOption('showErrors')) {
            if (isValid) {
                this.clearFieldError(field);
            } else {
                this.showFieldError(field, errorMessage);
            }
        }
        
        return isValid;
    }
    
    validateForm() {
        let isValid = true;
        
        this.inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    showFieldError(field, message) {
        if (!field) return;
        
        this.clearFieldError(field);
        
        field.classList.add(this.getOption('errorClass'));
        field.classList.remove(this.getOption('successClass'));
        
        const errorElement = document.createElement('div');
        errorElement.className = 'form-error-message text-red-500 text-sm mt-1';
        errorElement.textContent = message;
        errorElement.setAttribute('data-error-for', field.name || field.id);
        
        const container = field.closest('.form-group') || field.parentNode;
        container.appendChild(errorElement);
        
        field.setCustomValidity(message);
    }
    
    clearFieldError(field) {
        if (!field) return;
        
        field.classList.remove(this.getOption('errorClass'));
        
        const errorElement = this.element.querySelector(`[data-error-for="${field.name || field.id}"]`);
        if (errorElement) {
            errorElement.remove();
        }
        
        field.setCustomValidity('');
    }
    
    showError(message) {
        // Error handled silently
    }
    
    handleSubmit(event) {
        if (!this.validateForm()) {
            event.preventDefault();
            this.showError('Please correct the errors in the form');
            return false;
        }
        
        this.trigger('form:valid', {
            form: this.element,
            data: new FormData(this.element)
        });
        
        return true;
    }
    
    reset() {
        this.inputs.forEach(input => {
            this.clearFieldError(input);
            input.classList.remove(this.getOption('errorClass'), this.getOption('successClass'));
        });
        
        const passwordPreview = this.element.querySelector('#password-preview');
        if (passwordPreview) {
            passwordPreview.classList.add('hidden');
        }
    }
}

class PasswordToggle {
    static toggle(inputId, iconId) {
        const input = document.getElementById(inputId);
        const icon = document.getElementById(iconId);
        
        if (!input || !icon) return;
        
        if (input.type === 'password') {
            input.type = 'text';
            icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />`;
        } else {
            input.type = 'password';
            icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />`;
        }
    }
    
    static init(containerSelector = 'body') {
        const container = document.querySelector(containerSelector);
        if (!container) return;
        
        const toggleButtons = container.querySelectorAll('.password-toggle-btn');
        toggleButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const inputId = button.getAttribute('data-target') || 
                              button.closest('.form-relative').querySelector('input').id;
                const iconId = button.querySelector('svg').id;
                
                if (inputId && iconId) {
                    PasswordToggle.toggle(inputId, iconId);
                }
            });
        });
    }
}

class AjaxFormHandler {
    static async submit(form, options = {}) {
        const defaults = {
            method: 'POST',
            showSuccess: true,
            showErrors: true,
            resetOnSuccess: true,
            onSuccess: null,
            onError: null
        };
        
        const config = { ...defaults, ...options };
        const formData = new FormData(form);
        
        if (window.CSRFHelper) {
            const token = window.CSRFHelper.getToken();
            if (token) {
                formData.set('csrfmiddlewaretoken', token);
            }
        }
        
        try {
            const response = await fetch(form.action || window.location.href, {
                method: config.method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken') || ''
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                if (config.resetOnSuccess) {
                    form.reset();
                    
                    const validator = ComponentRegistry.get('FormValidator')
                        .find(v => v.element === form);
                    if (validator) {
                        validator.reset();
                    }
                }
                
                if (config.onSuccess) {
                    config.onSuccess(data);
                }
                
                return data;
            } else {
                throw new Error(data.error || 'Form submission failed');
            }
        } catch (error) {
            if (config.onError) {
                config.onError(error);
            }
            
            throw error;
        }
    }
}

// Global function for backward compatibility
window.togglePassword = PasswordToggle.toggle;

// Auto-initialize form validators when DOM is ready
DOMUtils.ready(() => {
    ComponentRegistry.initFromDOM('form[data-validate]', FormValidator);
    PasswordToggle.init();
    
    const ajaxForms = document.querySelectorAll('form[data-ajax]');
    ajaxForms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const validator = ComponentRegistry.get('FormValidator')
                .find(v => v.element === form);
            
            if (validator && !validator.validateForm()) {
                return;
            }
            
            try {
                await AjaxFormHandler.submit(form);
            } catch (error) {
                console.error('AJAX form submission failed:', error);
            }
        });
    });
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        FormValidator,
        PasswordToggle,
        AjaxFormHandler
    };
}