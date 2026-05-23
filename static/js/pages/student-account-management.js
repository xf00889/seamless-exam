/**
 * Student Account Management Page JavaScript
 * Handles custom success display for student account creation
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('create-student-form');
    const successMessage = document.getElementById('success-message');
    
    if (form && successMessage) {
        // Override the default AJAX handler for custom success display
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Validate form first
            const validator = ComponentRegistry.get('FormValidator')
                .find(v => v.element === form);
            
            if (validator && !validator.validateForm()) {
                return;
            }
            
            try {
                const data = await AjaxFormHandler.submit(form, {
                    showSuccess: false, // We'll handle success display ourselves
                    resetOnSuccess: false, // We'll handle reset ourselves
                    onSuccess: (data) => {
                        // Display success message with student details
                        document.getElementById('created-id').textContent = data.student.school_id;
                        document.getElementById('created-name').textContent = data.student.name;
                        document.getElementById('created-password').textContent = data.student.password;
                        document.getElementById('created-class').textContent = data.student.class;
                        
                        successMessage.classList.remove('hidden');
                        
                        // Reset form and validator
                        form.reset();
                        if (validator) {
                            validator.reset();
                        }
                        
                        // Scroll to success message
                        successMessage.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                        
                        // Reload page after 5 seconds to show new student in list
                        setTimeout(() => {
                            window.location.reload();
                        }, 5000);
                    }
                });
            } catch (error) {
                console.error('Student account creation failed:', error);
            }
        });
    }
});