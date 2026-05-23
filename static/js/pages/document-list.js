/**
 * Document List Page JavaScript
 * Provides delete confirmation for document deletion
 * Moved from root directory to pages for better organization
 */

document.addEventListener('DOMContentLoaded', function() {
    // Handle delete form submissions
    const deleteForms = document.querySelectorAll('.delete-form');
    
    deleteForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const confirmed = confirm('Are you sure you want to delete this document?');
            
            if (!confirmed) {
                e.preventDefault();
                return false;
            }
            
            return true;
        });
    });
});