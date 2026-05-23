/**
 * Teacher Profile Page JavaScript
 * Handles profile picture upload and deletion functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Handle profile picture upload with AJAX
    const uploadForm = document.getElementById('profile-picture-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(uploadForm);
            const submitBtn = uploadForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            
            // Disable button and show loading state
            submitBtn.disabled = true;
            submitBtn.textContent = 'Uploading...';
            
            // Get upload URL from data attribute
            const uploadUrl = uploadForm.dataset.uploadUrl;
            
            fetch(uploadUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Reload page to show updated picture
                    window.location.reload();
                } else {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                }
            })
            .catch(error => {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            });
        });
    }
    
    // Handle profile picture deletion
    const deleteBtn = document.getElementById('delete-picture-btn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            if (!confirm('Are you sure you want to remove your profile picture?')) {
                return;
            }
            
            const originalText = deleteBtn.textContent;
            deleteBtn.disabled = true;
            deleteBtn.textContent = 'Removing...';
            
            // Get delete URL from data attribute
            const deleteUrl = deleteBtn.dataset.deleteUrl;
            
            fetch(deleteUrl, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Reload page to show default avatar
                    window.location.reload();
                } else {
                    deleteBtn.disabled = false;
                    deleteBtn.textContent = originalText;
                }
            })
            .catch(error => {
                deleteBtn.disabled = false;
                deleteBtn.textContent = originalText;
            });
        });
    }
});