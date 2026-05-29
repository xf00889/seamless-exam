/**
 * Class Management Page JavaScript
 * Handles dynamic interactions for class management features
 * Moved from root directory to pages for better organization
 * Requirements: 8.1, 8.2
 */

(function() {
    'use strict';

    /**
     * Initialize bulk student assignment functionality
     * Implements AJAX for bulk student assignment
     * Requirement: 8.1, 8.2
     */
    function initBulkAssignment() {
        const bulkAssignForm = document.getElementById('bulk-assign-form');
        if (!bulkAssignForm) return;

        bulkAssignForm.addEventListener('submit', function(e) {
            e.preventDefault();

            // Validate student selection before submitting
            const checkedStudents = bulkAssignForm.querySelectorAll('[name="students"]:checked');
            if (checkedStudents.length === 0) {
                showMessage('error', 'Please select at least one student');
                return;
            }

            const formData = new FormData(bulkAssignForm);
            const submitButton = bulkAssignForm.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.textContent;

            // Disable submit button and show loading state
            submitButton.disabled = true;
            submitButton.textContent = 'Assigning...';

            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            fetch(bulkAssignForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message
                    showMessage('success', data.message || 'Students assigned successfully');

                    // Reset form after short delay
                    setTimeout(() => {
                        bulkAssignForm.reset();
                        // Optionally reload page to show updated data
                        if (data.reload) {
                            window.location.reload();
                        }
                    }, 2000);
                } else {
                    // Show error message
                    showMessage('error', data.error || 'Failed to assign students');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage('error', 'An error occurred while assigning students');
            })
            .finally(() => {
                // Re-enable submit button
                submitButton.disabled = false;
                submitButton.textContent = originalButtonText;
            });
        });
    }

    /**
     * Initialize client-side form validation
     * Requirement: 8.1, 8.2
     */
    function initFormValidation() {
        // Class form validation
        const classForm = document.getElementById('class-form');
        if (classForm) {
            classForm.addEventListener('submit', function(e) {
                const gradeLevel = classForm.querySelector('[name="grade_level"]');
                const strand = classForm.querySelector('[name="strand"]');
                const section = classForm.querySelector('[name="section"]');

                let isValid = true;
                let errorMessage = '';

                // Validate required fields
                if (!gradeLevel || !gradeLevel.value.trim()) {
                    isValid = false;
                    errorMessage = 'Grade level is required';
                    highlightField(gradeLevel);
                }

                if (!strand || !strand.value.trim()) {
                    isValid = false;
                    errorMessage = 'Strand is required';
                    highlightField(strand);
                }

                if (!section || !section.value.trim()) {
                    isValid = false;
                    errorMessage = 'Section is required';
                    highlightField(section);
                }

                if (!isValid) {
                    e.preventDefault();
                    showMessage('error', errorMessage);
                    return false;
                }
            });
        }

        // Bulk assignment validation is handled in initBulkAssignment
    }

    /**
     * Initialize filtering without page reload
     * Requirement: 8.1, 8.2
     */
    function initDynamicFiltering() {
        const filterForm = document.getElementById('filter-form');
        if (!filterForm) return;

        const filterSelects = filterForm.querySelectorAll('select');
        
        filterSelects.forEach(select => {
            select.addEventListener('change', function() {
                // Auto-submit form on filter change
                filterForm.submit();
            });
        });
    }

    /**
     * Initialize student selection helpers
     * Adds "Select All" / "Deselect All" functionality
     */
    function initStudentSelection() {
        const selectAllBtn = document.getElementById('select-all-students');
        const deselectAllBtn = document.getElementById('deselect-all-students');
        const studentCheckboxes = document.querySelectorAll('[name="students"]');

        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', function(e) {
                e.preventDefault();
                studentCheckboxes.forEach(checkbox => {
                    checkbox.checked = true;
                });
                updateSelectionCount();
            });
        }

        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', function(e) {
                e.preventDefault();
                studentCheckboxes.forEach(checkbox => {
                    checkbox.checked = false;
                });
                updateSelectionCount();
            });
        }

        // Update count on checkbox change
        studentCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updateSelectionCount);
        });

        // Initial count
        updateSelectionCount();
    }

    /**
     * Update the count of selected students
     */
    function updateSelectionCount() {
        const studentCheckboxes = document.querySelectorAll('[name="students"]:checked');
        const countDisplay = document.getElementById('selected-count');
        
        if (countDisplay) {
            const count = studentCheckboxes.length;
            countDisplay.textContent = `${count} student${count !== 1 ? 's' : ''} selected`;
        }
    }

    /**
     * Highlight a form field with error styling
     */
    function highlightField(field) {
        if (!field) return;
        
        field.classList.add('border-red-500', 'focus:ring-red-500');
        field.classList.remove('border-gray-300', 'focus:ring-blue-500');
        
        // Remove highlight after user interacts with field
        field.addEventListener('input', function() {
            field.classList.remove('border-red-500', 'focus:ring-red-500');
            field.classList.add('border-gray-300', 'focus:ring-blue-500');
        }, { once: true });
    }

    /**
     * Show a message to the user
     */
    function showMessage(type, message) {
        // Check if message container exists
        let messageContainer = document.querySelector('.message-container');
        
        if (!messageContainer) {
            // Create message container if it doesn't exist
            messageContainer = document.createElement('div');
            messageContainer.className = 'message-container fixed top-4 right-4 z-50 max-w-md';
            document.body.appendChild(messageContainer);
        }

        const messageDiv = document.createElement('div');
        const bgColor = type === 'success' ? 'bg-green-100 border-green-500 text-green-900' : 'bg-red-100 border-red-500 text-red-900';
        
        messageDiv.className = `${bgColor} border-l-4 p-4 mb-4 rounded shadow-lg`;
        messageDiv.innerHTML = `
            <div class="flex items-center justify-between">
                <p class="text-sm font-medium">${message}</p>
                <button class="ml-4 text-gray-500 hover:text-gray-700" onclick="this.parentElement.parentElement.remove()">
                    <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                    </svg>
                </button>
            </div>
        `;

        messageContainer.appendChild(messageDiv);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }

    /**
     * Initialize all class management features
     */
    function init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                initBulkAssignment();
                initFormValidation();
                initDynamicFiltering();
                initStudentSelection();
            });
        } else {
            initBulkAssignment();
            initFormValidation();
            initDynamicFiltering();
            initStudentSelection();
        }
    }

    // Initialize
    init();
})();