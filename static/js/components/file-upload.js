/**
 * File Upload Component
 * Provides client-side validation and user feedback for file uploads
 * Moved from root directory to components for better organization
 */

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('document');
    
    if (uploadForm && fileInput) {
        // File size validation (50 MB)
        const MAX_FILE_SIZE = 50 * 1024 * 1024;
        
        // Allowed file extensions
        const ALLOWED_EXTENSIONS = ['.pdf', '.docx'];
        
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            
            if (!file) {
                return;
            }
            
            // Check file size
            if (file.size > MAX_FILE_SIZE) {
                fileInput.value = '';
                return;
            }
            
            // Check file extension
            const fileName = file.name.toLowerCase();
            const fileExt = fileName.substring(fileName.lastIndexOf('.'));
            
            if (!ALLOWED_EXTENSIONS.includes(fileExt)) {
                fileInput.value = '';
                return;
            }
            
            // File validation passed
        });
        
        // Form submission handling
        uploadForm.addEventListener('submit', function(e) {
            const file = fileInput.files[0];
            
            if (!file) {
                e.preventDefault();
                return false;
            }
            
            // Show loading state
            const submitButton = uploadForm.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = 'Uploading...';
            }
            
            return true;
        });
    }
});