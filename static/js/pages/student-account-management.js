/**
 * Student Account Management Page JavaScript
 * Handles custom success display for student account creation
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('create-student-form');
    const successMessage = document.getElementById('success-message');

    if (form && successMessage) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            const validator = ComponentRegistry.get('FormValidator')
                .find(v => v.element === form);

            if (validator && !validator.validateForm()) {
                return;
            }

            try {
                const data = await AjaxFormHandler.submit(form, {
                    showSuccess: false,
                    resetOnSuccess: false,
                    onSuccess: (data) => {
                        document.getElementById('created-id').textContent = data.student.school_id;
                        document.getElementById('created-name').textContent = data.student.name;
                        document.getElementById('created-password').textContent = data.student.password;
                        document.getElementById('created-class').textContent = data.student.class;

                        successMessage.classList.remove('hidden');

                        form.reset();
                        if (validator) {
                            validator.reset();
                        }

                        successMessage.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                });
            } catch (error) {
                console.error('Student account creation failed:', error);
            }
        });

        // Close button for success message
        const closeBtn = document.getElementById('close-success-message');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                successMessage.classList.add('hidden');
            });
        }
    }
});