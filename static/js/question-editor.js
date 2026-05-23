/**
 * Question Editor JavaScript
 * Handles question editing, deletion, and approval functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Select all functionality
    const selectAllBtn = document.getElementById('select-all-btn');
    const questionCheckboxes = document.querySelectorAll('.question-checkbox');
    let allSelected = false;
    
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function() {
            allSelected = !allSelected;
            questionCheckboxes.forEach(checkbox => {
                checkbox.checked = allSelected;
            });
            selectAllBtn.textContent = allSelected ? 'Deselect All' : 'Select All';
        });
    }
    
    // Delete question functionality
    const deleteButtons = document.querySelectorAll('.delete-question-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const questionIndex = parseInt(this.dataset.index);
            
            if (confirm('Are you sure you want to delete this question?')) {
                deleteQuestion(questionIndex);
            }
        });
    });
    
    // Edit question functionality
    const editButtons = document.querySelectorAll('.edit-question-btn');
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const questionIndex = parseInt(this.dataset.index);
            editQuestion(questionIndex);
        });
    });
    
    // Approve selected functionality
    const approveBtn = document.getElementById('approve-selected-btn');
    if (approveBtn) {
        approveBtn.addEventListener('click', function() {
            const selectedIndices = getSelectedQuestionIndices();
            
            if (selectedIndices.length === 0) {
                return;
            }
            
            showApprovalModal(selectedIndices);
        });
    }
    
    // Modal functionality
    const approvalModal = document.getElementById('approval-modal');
    const cancelApprovalBtn = document.getElementById('cancel-approval-btn');
    
    if (cancelApprovalBtn) {
        cancelApprovalBtn.addEventListener('click', function() {
            hideApprovalModal();
        });
    }
    
    // Close modal on outside click
    if (approvalModal) {
        approvalModal.addEventListener('click', function(e) {
            if (e.target === approvalModal) {
                hideApprovalModal();
            }
        });
    }
    
    /**
     * Get indices of selected questions
     */
    function getSelectedQuestionIndices() {
        const selected = [];
        questionCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                selected.push(parseInt(checkbox.dataset.index));
            }
        });
        return selected;
    }
    
    /**
     * Delete a question
     */
    function deleteQuestion(questionIndex) {
        const documentId = getDocumentId();
        const url = `/uploads/review/${documentId}/question/${questionIndex}/delete/`;
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove question card from DOM
                const questionCard = document.querySelector(`.question-card[data-index="${questionIndex}"]`);
                if (questionCard) {
                    questionCard.remove();
                }
                
                // Reindex remaining questions
                reindexQuestions();
            }
        })
        .catch(error => {
            // Error handled silently
        });
    }
    
    /**
     * Edit a question (simplified - opens prompt for now)
     */
    function editQuestion(questionIndex) {
        // Question editing interface coming soon
    }
    
    /**
     * Show approval modal
     */
    function showApprovalModal(selectedIndices) {
        const modal = document.getElementById('approval-modal');
        const indicesInput = document.getElementById('question-indices-input');
        
        // Set selected indices
        indicesInput.value = JSON.stringify(selectedIndices);
        
        // Load exams into select
        loadExams();
        
        // Show modal
        modal.classList.remove('hidden');
    }
    
    /**
     * Hide approval modal
     */
    function hideApprovalModal() {
        const modal = document.getElementById('approval-modal');
        modal.classList.add('hidden');
    }
    
    /**
     * Load exams for approval
     */
    function loadExams() {
        const examSelect = document.getElementById('exam-select');
        
        // For now, add a placeholder
        // In production, this would fetch from an API endpoint
        examSelect.innerHTML = '<option value="">-- Select an Exam --</option>';
        
        // TODO: Fetch exams from API
        // This is a placeholder - in real implementation, fetch from server
        const placeholderExams = [
            { id: 1, title: 'Midterm Exam' },
            { id: 2, title: 'Final Exam' },
            { id: 3, title: 'Quiz 1' }
        ];
        
        placeholderExams.forEach(exam => {
            const option = document.createElement('option');
            option.value = exam.id;
            option.textContent = exam.title;
            examSelect.appendChild(option);
        });
    }
    
    /**
     * Reindex questions after deletion
     */
    function reindexQuestions() {
        const questionCards = document.querySelectorAll('.question-card');
        questionCards.forEach((card, index) => {
            card.dataset.index = index;
            
            // Update question number display
            const questionNumber = card.querySelector('.text-lg.font-semibold');
            if (questionNumber) {
                questionNumber.textContent = `Question ${index + 1}`;
            }
            
            // Update checkbox index
            const checkbox = card.querySelector('.question-checkbox');
            if (checkbox) {
                checkbox.dataset.index = index;
            }
            
            // Update button indices
            const editBtn = card.querySelector('.edit-question-btn');
            const deleteBtn = card.querySelector('.delete-question-btn');
            if (editBtn) editBtn.dataset.index = index;
            if (deleteBtn) deleteBtn.dataset.index = index;
        });
    }
    
    /**
     * Get document ID from URL
     */
    function getDocumentId() {
        const pathParts = window.location.pathname.split('/');
        const reviewIndex = pathParts.indexOf('review');
        if (reviewIndex !== -1 && pathParts.length > reviewIndex + 1) {
            return pathParts[reviewIndex + 1];
        }
        return null;
    }
});
