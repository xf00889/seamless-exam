/**
 * Bulk Student Assignment Page JavaScript
 * Handles select all / deselect all functionality for student checkboxes
 */

document.addEventListener('DOMContentLoaded', function() {
    const studentCheckboxes = document.querySelectorAll('input[name="students"]');
    
    // Add a select all button
    const studentContainer = document.querySelector('.space-y-2');
    if (studentContainer && studentCheckboxes.length > 0) {
        const selectAllDiv = document.createElement('div');
        selectAllDiv.className = 'flex items-center pb-2 mb-2 border-b border-gray-300';
        selectAllDiv.innerHTML = `
            <button type="button" id="select-all-btn" class="text-sm text-blue-600 hover:text-blue-800 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1">
                Select All
            </button>
            <span class="mx-2 text-gray-400">|</span>
            <button type="button" id="deselect-all-btn" class="text-sm text-blue-600 hover:text-blue-800 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1">
                Deselect All
            </button>
            <span class="ml-auto text-sm text-gray-600" id="selected-count">0 selected</span>
        `;
        studentContainer.insertBefore(selectAllDiv, studentContainer.firstChild);
        
        // Update count
        function updateCount() {
            const checked = document.querySelectorAll('input[name="students"]:checked').length;
            document.getElementById('selected-count').textContent = `${checked} selected`;
        }
        
        // Select all handler
        document.getElementById('select-all-btn').addEventListener('click', function() {
            studentCheckboxes.forEach(cb => cb.checked = true);
            updateCount();
        });
        
        // Deselect all handler
        document.getElementById('deselect-all-btn').addEventListener('click', function() {
            studentCheckboxes.forEach(cb => cb.checked = false);
            updateCount();
        });
        
        // Update count on checkbox change
        studentCheckboxes.forEach(cb => {
            cb.addEventListener('change', updateCount);
        });
        
        // Initial count
        updateCount();
    }
});