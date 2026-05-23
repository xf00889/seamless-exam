/**
 * Class List Page JavaScript
 * Handles delete modal functionality for class management
 */

let currentClassId = null;

function openDeleteModal(classId, className) {
    currentClassId = classId;
    document.getElementById('className').textContent = className;
    document.getElementById('deletePassword').value = '';
    document.getElementById('passwordError').classList.add('hidden');
    document.getElementById('deleteModal').classList.remove('hidden');
    document.getElementById('deletePassword').focus();
}

function closeDeleteModal() {
    document.getElementById('deleteModal').classList.add('hidden');
    currentClassId = null;
}

function confirmDelete() {
    const password = document.getElementById('deletePassword').value;
    const errorDiv = document.getElementById('passwordError');
    
    if (!password) {
        errorDiv.textContent = 'Password is required';
        errorDiv.classList.remove('hidden');
        return;
    }
    
    // Update form action and submit
    const form = document.getElementById('deleteForm');
    form.action = `/users/teacher/classes/${currentClassId}/delete/`;
    form.submit();
}

// Initialize event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Close modal when clicking outside
    const deleteModal = document.getElementById('deleteModal');
    if (deleteModal) {
        deleteModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeDeleteModal();
            }
        });
    }

    // Handle Enter key in password field
    const deletePassword = document.getElementById('deletePassword');
    if (deletePassword) {
        deletePassword.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                confirmDelete();
            }
        });
    }
});