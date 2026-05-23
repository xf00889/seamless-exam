/**
 * Profile Forms Page JavaScript
 * Client-side validation for profile forms.
 * Provides real-time validation for profile editing, password changes, and profile picture uploads.
 * Moved from root directory to pages for better organization
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize profile edit form validation
    const profileEditForm = document.getElementById('profile-edit-form');
    if (profileEditForm) {
        initializeProfileEditValidation(profileEditForm);
    }
    
    // Initialize password change form validation
    const passwordChangeForm = document.getElementById('password-change-form');
    if (passwordChangeForm) {
        initializePasswordChangeValidation(passwordChangeForm);
    }
    
    // Initialize profile picture form validation
    const profilePictureForm = document.getElementById('profile-picture-form');
    if (profilePictureForm) {
        initializeProfilePictureValidation(profilePictureForm);
    }
});

/**
 * Initialize validation for profile edit form.
 * Requirements: 3.2, 3.4
 */
function initializeProfileEditValidation(form) {
    const firstNameInput = form.querySelector('#id_first_name');
    const lastNameInput = form.querySelector('#id_last_name');
    const bioInput = form.querySelector('#id_bio');
    
    // Real-time validation for first name
    if (firstNameInput) {
        firstNameInput.addEventListener('blur', function() {
            validateFirstName(firstNameInput);
        });
        
        firstNameInput.addEventListener('input', function() {
            clearFieldError(firstNameInput);
        });
    }
    
    // Real-time validation for last name
    if (lastNameInput) {
        lastNameInput.addEventListener('blur', function() {
            validateLastName(lastNameInput);
        });
        
        lastNameInput.addEventListener('input', function() {
            clearFieldError(lastNameInput);
        });
    }
    
    // Real-time validation for bio
    if (bioInput) {
        bioInput.addEventListener('input', function() {
            validateBio(bioInput);
        });
    }
    
    // Form submission validation
    form.addEventListener('submit', function(event) {
        let isValid = true;
        
        if (firstNameInput && !validateFirstName(firstNameInput)) {
            isValid = false;
        }
        
        if (lastNameInput && !validateLastName(lastNameInput)) {
            isValid = false;
        }
        
        if (bioInput && !validateBio(bioInput)) {
            isValid = false;
        }
        
        if (!isValid) {
            event.preventDefault();
            event.stopPropagation();
            
            // Scroll to first error
            const firstError = form.querySelector('.border-red-500');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstError.focus();
            }
        }
    });
}

/**
 * Validate first name field.
 * Requirement: 3.2
 */
function validateFirstName(input) {
    const value = input.value.trim();
    
    if (value === '') {
        showFieldError(input, 'First name is required');
        return false;
    }
    
    if (value.length > 100) {
        showFieldError(input, 'First name must not exceed 100 characters');
        return false;
    }
    
    clearFieldError(input);
    return true;
}

/**
 * Validate last name field.
 * Requirement: 3.2
 */
function validateLastName(input) {
    const value = input.value.trim();
    
    if (value === '') {
        showFieldError(input, 'Last name is required');
        return false;
    }
    
    if (value.length > 100) {
        showFieldError(input, 'Last name must not exceed 100 characters');
        return false;
    }
    
    clearFieldError(input);
    return true;
}

/**
 * Validate bio field.
 * Requirement: 3.4
 */
function validateBio(input) {
    const value = input.value;
    const maxLength = 500;
    const remaining = maxLength - value.length;
    
    // Update character counter if it exists
    const counter = input.parentElement.querySelector('.char-counter');
    if (counter) {
        counter.textContent = `${remaining} characters remaining`;
        
        if (remaining < 0) {
            counter.classList.add('text-red-600');
            counter.classList.remove('text-gray-500');
        } else {
            counter.classList.remove('text-red-600');
            counter.classList.add('text-gray-500');
        }
    }
    
    if (value.length > maxLength) {
        showFieldError(input, `Bio must not exceed ${maxLength} characters`);
        return false;
    }
    
    clearFieldError(input);
    return true;
}

/**
 * Initialize validation for password change form.
 * Requirements: 5.2, 5.4
 */
function initializePasswordChangeValidation(form) {
    const currentPasswordInput = form.querySelector('#id_current_password');
    const newPasswordInput = form.querySelector('#id_new_password');
    const confirmPasswordInput = form.querySelector('#id_confirm_password');
    
    // Real-time validation for current password
    if (currentPasswordInput) {
        currentPasswordInput.addEventListener('blur', function() {
            validateCurrentPassword(currentPasswordInput);
        });
        
        currentPasswordInput.addEventListener('input', function() {
            clearFieldError(currentPasswordInput);
        });
    }
    
    // Real-time validation for new password with strength indicator
    if (newPasswordInput) {
        newPasswordInput.addEventListener('input', function() {
            validateNewPassword(newPasswordInput);
            updatePasswordStrengthIndicator(newPasswordInput);
            
            // Re-validate confirm password if it has a value
            if (confirmPasswordInput && confirmPasswordInput.value) {
                validateConfirmPassword(confirmPasswordInput, newPasswordInput);
            }
        });
        
        newPasswordInput.addEventListener('blur', function() {
            validateNewPassword(newPasswordInput);
        });
    }
    
    // Real-time validation for confirm password
    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            validateConfirmPassword(confirmPasswordInput, newPasswordInput);
        });
        
        confirmPasswordInput.addEventListener('blur', function() {
            validateConfirmPassword(confirmPasswordInput, newPasswordInput);
        });
    }
    
    // Form submission validation
    form.addEventListener('submit', function(event) {
        let isValid = true;
        
        if (currentPasswordInput && !validateCurrentPassword(currentPasswordInput)) {
            isValid = false;
        }
        
        if (newPasswordInput && !validateNewPassword(newPasswordInput)) {
            isValid = false;
        }
        
        if (confirmPasswordInput && !validateConfirmPassword(confirmPasswordInput, newPasswordInput)) {
            isValid = false;
        }
        
        if (!isValid) {
            event.preventDefault();
            event.stopPropagation();
            
            // Scroll to first error
            const firstError = form.querySelector('.border-red-500');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstError.focus();
            }
        }
    });
}

/**
 * Validate current password field.
 * Requirement: 5.2
 */
function validateCurrentPassword(input) {
    const value = input.value;
    
    if (value === '') {
        showFieldError(input, 'Current password is required');
        return false;
    }
    
    clearFieldError(input);
    return true;
}

/**
 * Validate new password field with security requirements.
 * Requirement: 5.4
 */
function validateNewPassword(input) {
    const value = input.value;
    const errors = [];
    
    if (value === '') {
        showFieldError(input, 'New password is required');
        return false;
    }
    
    // Minimum 8 characters
    if (value.length < 8) {
        errors.push('at least 8 characters');
    }
    
    // At least one uppercase letter
    if (!/[A-Z]/.test(value)) {
        errors.push('one uppercase letter');
    }
    
    // At least one lowercase letter
    if (!/[a-z]/.test(value)) {
        errors.push('one lowercase letter');
    }
    
    // At least one digit
    if (!/[0-9]/.test(value)) {
        errors.push('one digit');
    }
    
    if (errors.length > 0) {
        showFieldError(input, `Password must contain ${errors.join(', ')}`);
        return false;
    }
    
    clearFieldError(input);
    return true;
}

/**
 * Validate confirm password field.
 * Requirement: 5.3
 */
function validateConfirmPassword(confirmInput, newPasswordInput) {
    const confirmValue = confirmInput.value;
    const newPasswordValue = newPasswordInput ? newPasswordInput.value : '';
    
    if (confirmValue === '') {
        showFieldError(confirmInput, 'Password confirmation is required');
        return false;
    }
    
    if (confirmValue !== newPasswordValue) {
        showFieldError(confirmInput, 'Passwords do not match');
        return false;
    }
    
    clearFieldError(confirmInput);
    return true;
}

/**
 * Update password strength indicator.
 * Requirement: 5.4
 */
function updatePasswordStrengthIndicator(input) {
    const password = input.value;
    
    // Find or create strength indicator
    let indicator = input.parentElement.querySelector('.password-strength-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'password-strength-indicator mt-2';
        input.parentElement.appendChild(indicator);
    }
    
    if (password === '') {
        indicator.innerHTML = '';
        return;
    }
    
    // Calculate strength
    let strength = 0;
    let strengthText = '';
    let strengthColor = '';
    
    const checks = {
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        digit: /[0-9]/.test(password),
        special: /[^a-zA-Z0-9]/.test(password)
    };
    
    strength = Object.values(checks).filter(Boolean).length;
    
    if (strength <= 2) {
        strengthText = 'Weak';
        strengthColor = 'text-red-600';
    } else if (strength === 3 || strength === 4) {
        strengthText = 'Medium';
        strengthColor = 'text-yellow-600';
    } else {
        strengthText = 'Strong';
        strengthColor = 'text-green-600';
    }
    
    // Build indicator HTML
    const checkmarks = `
        <div class="text-xs space-y-1 mt-1">
            <div class="${checks.length ? 'text-green-600' : 'text-gray-400'}">
                ${checks.length ? '✓' : '○'} At least 8 characters
            </div>
            <div class="${checks.uppercase ? 'text-green-600' : 'text-gray-400'}">
                ${checks.uppercase ? '✓' : '○'} One uppercase letter
            </div>
            <div class="${checks.lowercase ? 'text-green-600' : 'text-gray-400'}">
                ${checks.lowercase ? '✓' : '○'} One lowercase letter
            </div>
            <div class="${checks.digit ? 'text-green-600' : 'text-gray-400'}">
                ${checks.digit ? '✓' : '○'} One digit
            </div>
        </div>
    `;
    
    indicator.innerHTML = `
        <div class="text-sm ${strengthColor} font-medium">
            Password Strength: ${strengthText}
        </div>
        ${checkmarks}
    `;
}

/**
 * Initialize validation for profile picture form.
 * Requirement: 4.2
 */
function initializeProfilePictureValidation(form) {
    const fileInput = form.querySelector('#id_profile_picture');
    
    if (fileInput) {
        // Add preview functionality
        fileInput.addEventListener('change', function() {
            validateProfilePicture(fileInput);
            previewProfilePicture(fileInput);
        });
    }
    
    // Form submission validation
    form.addEventListener('submit', function(event) {
        if (fileInput && !validateProfilePicture(fileInput)) {
            event.preventDefault();
            event.stopPropagation();
        }
    });
}

/**
 * Validate profile picture file.
 * Requirements: 4.2, 4.3
 */
function validateProfilePicture(input) {
    if (!input.files || input.files.length === 0) {
        showFieldError(input, 'Please select an image file');
        return false;
    }
    
    const file = input.files[0];
    
    // Validate file type (Requirement 4.2)
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
        showFieldError(input, 'Only JPEG, PNG, and GIF images are allowed');
        return false;
    }
    
    // Validate file size (5MB max) - Requirement 4.3
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        showFieldError(input, `File size (${sizeMB}MB) exceeds maximum allowed size (5MB)`);
        return false;
    }
    
    clearFieldError(input);
    return true;
}

/**
 * Preview profile picture before upload.
 * Requirement: 4.1
 */
function previewProfilePicture(input) {
    if (!input.files || input.files.length === 0) {
        return;
    }
    
    const file = input.files[0];
    const reader = new FileReader();
    
    reader.onload = function(e) {
        // Find or create preview element
        let preview = document.getElementById('profile-picture-preview');
        if (!preview) {
            preview = document.createElement('img');
            preview.id = 'profile-picture-preview';
            preview.className = 'mt-4 w-32 h-32 rounded-full object-cover border-2 border-gray-300';
            input.parentElement.appendChild(preview);
        }
        
        preview.src = e.target.result;
        preview.style.display = 'block';
    };
    
    reader.readAsDataURL(file);
}

/**
 * Show error message for a field.
 */
function showFieldError(input, message) {
    // Add error styling
    input.classList.add('border-red-500');
    input.classList.remove('border-gray-300');
    
    // Remove existing error message if any
    const existingError = input.parentElement.querySelector('.field-error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Create and insert error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error-message text-red-600 text-sm mt-1';
    errorDiv.textContent = message;
    input.parentElement.appendChild(errorDiv);
}

/**
 * Clear error state from a field.
 */
function clearFieldError(input) {
    input.classList.remove('border-red-500');
    input.classList.add('border-gray-300');
    
    const errorMessage = input.parentElement.querySelector('.field-error-message');
    if (errorMessage) {
        errorMessage.remove();
    }
}

/**
 * Add character counter to textarea.
 */
function addCharacterCounter(textarea, maxLength) {
    const counter = document.createElement('div');
    counter.className = 'char-counter text-sm text-gray-500 mt-1';
    const remaining = maxLength - textarea.value.length;
    counter.textContent = `${remaining} characters remaining`;
    textarea.parentElement.appendChild(counter);
}

// Initialize character counters for bio fields
document.addEventListener('DOMContentLoaded', function() {
    const bioInput = document.querySelector('#id_bio');
    if (bioInput) {
        addCharacterCounter(bioInput, 500);
    }
});