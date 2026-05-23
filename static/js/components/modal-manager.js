/**
 * Modal Manager Component
 * Provides reusable modal functionality for the ExamMaker system
 * Extracted from class_list.html and exam_list.html templates
 * 
 * @author ExamMaker Development Team
 * @version 1.0.0
 * @since 2024
 * 
 * Requirements: 10.1, 10.2, 10.4 - Coding standards compliance
 */

class ModalManager {
    /**
     * Open a modal with the specified configuration
     * @param {string} modalId - The ID of the modal element
     * @param {Object} config - Modal configuration options
     */
    static openModal(modalId, config = {}) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`Modal with ID '${modalId}' not found`);
            return;
        }

        // Apply configuration if provided
        if (config.title) {
            const titleElement = modal.querySelector('.modal-title');
            if (titleElement) {
                titleElement.textContent = config.title;
            }
        }

        if (config.content) {
            const contentElement = modal.querySelector('.modal-description');
            if (contentElement) {
                contentElement.innerHTML = config.content;
            }
        }

        // Show the modal
        modal.classList.remove('hidden');

        // Focus on first input if available
        const firstInput = modal.querySelector('input, textarea, select');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }

        // Set up click outside to close
        this._setupClickOutsideClose(modal);
    }

    /**
     * Close a modal
     * @param {string} modalId - The ID of the modal element
     */
    static closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`Modal with ID '${modalId}' not found`);
            return;
        }

        modal.classList.add('hidden');
        
        // Clear any form data
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }

        // Clear any error messages
        const errorElements = modal.querySelectorAll('.modal-error, .hidden');
        errorElements.forEach(el => {
            if (el.classList.contains('modal-error')) {
                el.classList.add('hidden');
            }
        });
    }

    /**
     * Open a delete confirmation modal
     * @param {Object} config - Configuration object
     * @param {number} config.id - ID of the item to delete
     * @param {string} config.name - Name/title of the item to delete
     * @param {string} config.type - Type of item (exam, class, etc.)
     * @param {string} config.deleteUrl - URL to submit delete request to
     * @param {string} [config.modalId='deleteModal'] - ID of the delete modal
     */
    static openDeleteModal(config) {
        const {
            id,
            name,
            type = 'item',
            deleteUrl,
            modalId = 'deleteModal'
        } = config;

        // Store current item data
        this.currentDeleteConfig = config;

        // Update modal content
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`Delete modal with ID '${modalId}' not found`);
            return;
        }

        // Update item name
        const nameElement = modal.querySelector('#examTitle, #className, .modal-item-name');
        if (nameElement) {
            nameElement.textContent = name;
        }

        // Update form action
        const form = modal.querySelector('#deleteForm, form');
        if (form && deleteUrl) {
            form.action = deleteUrl;
        }

        // Clear password and errors
        const passwordInput = modal.querySelector('#deletePassword, input[type="password"]');
        if (passwordInput) {
            passwordInput.value = '';
        }

        const errorDiv = modal.querySelector('#passwordError, .modal-error');
        if (errorDiv) {
            errorDiv.classList.add('hidden');
        }

        // Show modal
        this.openModal(modalId);
    }

    /**
     * Confirm delete action
     * @param {string} [modalId='deleteModal'] - ID of the delete modal
     */
    static confirmDelete(modalId = 'deleteModal') {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`Delete modal with ID '${modalId}' not found`);
            return;
        }

        const passwordInput = modal.querySelector('#deletePassword, input[type="password"]');
        const errorDiv = modal.querySelector('#passwordError, .modal-error');
        const form = modal.querySelector('#deleteForm, form');

        if (!passwordInput || !form) {
            console.error('Required elements not found in delete modal');
            return;
        }

        const password = passwordInput.value.trim();

        if (!password) {
            if (errorDiv) {
                errorDiv.textContent = 'Password is required';
                errorDiv.classList.remove('hidden');
            }
            return;
        }

        // Submit the form
        form.submit();
    }

    /**
     * Open a reopen exam modal with student selection
     * @param {Object} config - Configuration object
     * @param {number} config.examId - ID of the exam to reopen
     * @param {string} config.examTitle - Title of the exam
     * @param {string} [config.modalId='reopenModal'] - ID of the reopen modal
     */
    static openReopenModal(config) {
        const {
            examId,
            examTitle,
            modalId = 'reopenModal'
        } = config;

        // Store current exam data
        this.currentReopenConfig = config;
        this.selectedStudentIds = new Set();
        this.allStudents = [];

        // Update modal content
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`Reopen modal with ID '${modalId}' not found`);
            return;
        }

        const titleElement = modal.querySelector('#reopenExamTitle, .modal-exam-title');
        if (titleElement) {
            titleElement.textContent = examTitle;
        }

        // Reset UI state
        const selectAllCheckbox = modal.querySelector('#selectAllStudents');
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = false;
        }

        const confirmBtn = modal.querySelector('#confirmReopenBtn');
        if (confirmBtn) {
            confirmBtn.disabled = true;
        }

        // Show loading state
        this._showStudentsLoading(modal);

        // Show modal
        this.openModal(modalId);

        // Fetch students
        this._fetchStudentsForReopen(examId, modal);
    }

    /**
     * Confirm reopen action
     * @param {string} [modalId='reopenModal'] - ID of the reopen modal
     */
    static confirmReopen(modalId = 'reopenModal') {
        if (!this.currentReopenConfig || this.selectedStudentIds.size === 0) {
            return;
        }

        const { examId } = this.currentReopenConfig;
        const modal = document.getElementById(modalId);
        const selectAllCheckbox = modal?.querySelector('#selectAllStudents');

        // Create and submit form
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/exams/${examId}/activate/`;

        // Add CSRF token
        const csrfToken = this._getCSRFToken();
        if (!csrfToken) {
            return;
        }

        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);

        // Add selected student IDs
        this.selectedStudentIds.forEach(studentId => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'student_ids';
            input.value = studentId;
            form.appendChild(input);
        });

        // Add select_all flag if all students are selected
        if (selectAllCheckbox?.checked) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'select_all';
            input.value = '1';
            form.appendChild(input);
        }

        document.body.appendChild(form);
        form.submit();
    }

    /**
     * Toggle student selection in reopen modal
     * @param {number} studentId - ID of the student to toggle
     */
    static toggleStudent(studentId) {
        const checkbox = document.getElementById(`student_${studentId}`);
        if (!checkbox) return;

        if (checkbox.checked) {
            this.selectedStudentIds.add(studentId);
        } else {
            this.selectedStudentIds.delete(studentId);
            const selectAllCheckbox = document.getElementById('selectAllStudents');
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = false;
            }
        }

        this._updateConfirmButton();
    }

    /**
     * Toggle select all students
     */
    static toggleSelectAll() {
        const selectAllCheckbox = document.getElementById('selectAllStudents');
        if (!selectAllCheckbox) return;

        const isChecked = selectAllCheckbox.checked;

        this.allStudents.forEach(student => {
            const checkbox = document.getElementById(`student_${student.id}`);
            if (checkbox) {
                checkbox.checked = isChecked;
                
                if (isChecked) {
                    this.selectedStudentIds.add(student.id);
                } else {
                    this.selectedStudentIds.delete(student.id);
                }
            }
        });

        this._updateConfirmButton();
    }

    // Private helper methods

    /**
     * Set up click outside to close functionality
     * @private
     */
    static _setupClickOutsideClose(modal) {
        const clickHandler = (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
                modal.removeEventListener('click', clickHandler);
            }
        };
        modal.addEventListener('click', clickHandler);
    }

    /**
     * Get CSRF token from various sources
     * @private
     */
    static _getCSRFToken() {
        // Try form input first
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            return csrfInput.value;
        }

        // Try meta tag
        const metaTag = document.querySelector('meta[name=csrf-token]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }

        // Try cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }

        return null;
    }

    /**
     * Show loading state for students list
     * @private
     */
    static _showStudentsLoading(modal) {
        const loadingEl = modal.querySelector('#studentsLoading');
        const listEl = modal.querySelector('#studentsList');
        const errorEl = modal.querySelector('#studentsError');
        const emptyEl = modal.querySelector('#studentsEmpty');

        if (loadingEl) loadingEl.classList.remove('hidden');
        if (listEl) listEl.classList.add('hidden');
        if (errorEl) errorEl.classList.add('hidden');
        if (emptyEl) emptyEl.classList.add('hidden');
    }

    /**
     * Fetch students for reopen modal
     * @private
     */
    static _fetchStudentsForReopen(examId, modal) {
        fetch(`/exams/${examId}/students/`)
            .then(response => response.json())
            .then(data => {
                const loadingEl = modal.querySelector('#studentsLoading');
                if (loadingEl) loadingEl.classList.add('hidden');

                if (data.success && data.students.length > 0) {
                    this.allStudents = data.students;
                    this._renderStudentsList(modal);
                    const listEl = modal.querySelector('#studentsList');
                    if (listEl) listEl.classList.remove('hidden');
                } else {
                    const emptyEl = modal.querySelector('#studentsEmpty');
                    if (emptyEl) emptyEl.classList.remove('hidden');
                }
            })
            .catch(error => {
                console.error('Error fetching students:', error);
                const loadingEl = modal.querySelector('#studentsLoading');
                const errorEl = modal.querySelector('#studentsError');
                if (loadingEl) loadingEl.classList.add('hidden');
                if (errorEl) errorEl.classList.remove('hidden');
            });
    }

    /**
     * Render students list in modal
     * @private
     */
    static _renderStudentsList(modal) {
        const container = modal.querySelector('#studentsList');
        if (!container) return;

        container.innerHTML = '';

        this.allStudents.forEach(student => {
            const div = document.createElement('div');
            div.className = 'modal-student-item';
            div.innerHTML = `
                <input type="checkbox" 
                       id="student_${student.id}" 
                       value="${student.id}" 
                       onchange="ModalManager.toggleStudent(${student.id})"
                       class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500">
                <label for="student_${student.id}" class="ml-2 flex-1 cursor-pointer">
                    <span class="modal-student-name">${student.full_name}</span>
                    <span class="modal-student-id">${student.school_id}</span>
                    <span class="modal-student-class">(${student.class_name})</span>
                </label>
            `;
            container.appendChild(div);
        });
    }

    /**
     * Update confirm button state
     * @private
     */
    static _updateConfirmButton() {
        const btn = document.getElementById('confirmReopenBtn');
        if (btn) {
            btn.disabled = this.selectedStudentIds.size === 0;
        }
    }
}

// Global functions for backward compatibility with existing templates
window.openDeleteModal = function(id, name, type = 'exam') {
    const deleteUrl = type === 'exam' ? `/exams/${id}/delete/` : `/users/teacher/classes/${id}/delete/`;
    ModalManager.openDeleteModal({
        id,
        name,
        type,
        deleteUrl
    });
};

window.closeDeleteModal = function() {
    ModalManager.closeModal('deleteModal');
};

window.confirmDelete = function() {
    ModalManager.confirmDelete('deleteModal');
};

window.openReopenModal = function(examId, examTitle) {
    ModalManager.openReopenModal({
        examId,
        examTitle
    });
};

window.closeReopenModal = function() {
    ModalManager.closeModal('reopenModal');
};

window.confirmReopen = function() {
    ModalManager.confirmReopen('reopenModal');
};

window.toggleStudent = function(studentId) {
    ModalManager.toggleStudent(studentId);
};

window.toggleSelectAll = function() {
    ModalManager.toggleSelectAll();
};

// Initialize modal manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set up keyboard event handlers for modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            // Close any open modals
            const openModals = document.querySelectorAll('.modal-overlay:not(.hidden)');
            openModals.forEach(modal => {
                modal.classList.add('hidden');
            });
        }
    });

    // Set up Enter key handlers for password fields in modals
    const passwordInputs = document.querySelectorAll('.modal-password-input, #deletePassword');
    passwordInputs.forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const modal = input.closest('.modal-overlay');
                if (modal && modal.id === 'deleteModal') {
                    ModalManager.confirmDelete('deleteModal');
                }
            }
        });
    });
});