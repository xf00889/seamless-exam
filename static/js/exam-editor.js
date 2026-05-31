/**
 * Exam editor JavaScript for managing question creation.
 * Handles modal display and dynamic form fields based on question type.
 */

document.addEventListener('DOMContentLoaded', function() {
    
    const modal = document.getElementById('questionModal');
    const addQuestionBtn = document.getElementById('addQuestionBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const questionTypeSelect = document.getElementById('question_type');
    const typeSpecificFields = document.getElementById('typeSpecificFields');
    const questionForm = document.getElementById('questionForm');
    const modalTitle = document.getElementById('modalTitle');
    const submitBtn = document.getElementById('submitBtn');
    const questionIdInput = document.getElementById('questionId');
    
    // Debug: Check if elements exist
    if (!modal || !modalTitle || !submitBtn || !questionIdInput) {
        console.error('Exam editor: Required modal elements not found');
        return;
    }
    console.log('Exam editor initialized');
    
    let isEditMode = false;
    
    // Show modal for adding
    if (addQuestionBtn) {
        addQuestionBtn.addEventListener('click', function() {
            isEditMode = false;
            modalTitle.textContent = 'Add New Question';
            submitBtn.textContent = 'Add Question';
            questionForm.reset();
            questionIdInput.value = '';
            typeSpecificFields.innerHTML = '';
            modal.classList.remove('hidden');
        });
    }
    
    // Show modal for editing
    const editButtons = document.querySelectorAll('.edit-question-btn');
    console.log('Found edit buttons:', editButtons.length);
    
    editButtons.forEach((btn, index) => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const questionId = parseInt(this.dataset.questionId);
            console.log('Edit clicked for question:', questionId, 'Modal exists:', !!modal);

            // Find question data from global array
            if (!window.questionsData || !Array.isArray(window.questionsData)) {
                console.warn('Questions data not initialized');
                return;
            }
            
            console.log('Searching in', window.questionsData.length, 'questions');
            const questionData = window.questionsData.find(q => q.id === questionId);
            
            if (!questionData) {
                console.warn('Question not found in data');
                return;
            }
            
            isEditMode = true;
            
            if (modalTitle) {
                modalTitle.textContent = 'Edit Question';
            }
            
            if (submitBtn) {
                submitBtn.textContent = 'Update Question';
            }
            
            // Extract data from questionData object
            const questionType = questionData.type;
            const questionText = questionData.text;
            const points = questionData.points;
            const correctAnswer = questionData.correct_answer;
            const options = questionData.options;
            
            // Populate form
            if (questionIdInput) {
                questionIdInput.value = questionId;
            }
            
            const questionTypeField = document.getElementById('question_type');
            const questionTextField = document.getElementById('question_text');
            const pointsField = document.getElementById('points');
            
            if (questionTypeField) {
                questionTypeField.value = questionType;
            }
            
            if (questionTextField) {
                questionTextField.value = questionText;
            }
            
            if (pointsField) {
                pointsField.value = points;
            }
            
            // Trigger type change to load type-specific fields
            if (questionTypeSelect) {
                const event = new Event('change');
                questionTypeSelect.dispatchEvent(event);
            }
            
            // Wait for fields to be created, then populate them
            setTimeout(() => {
                populateTypeSpecificFields(questionType, correctAnswer, options);
            }, 100);
            
            if (modal) {
                modal.classList.remove('hidden');
            }
        });
    });
    
    // Hide modal
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            modal.classList.add('hidden');
            questionForm.reset();
            typeSpecificFields.innerHTML = '';
        });
    }
    
    // Close modal when clicking outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.classList.add('hidden');
            questionForm.reset();
            typeSpecificFields.innerHTML = '';
        }
    });
    
    // Handle question type change
    if (questionTypeSelect) {
        questionTypeSelect.addEventListener('change', function() {
            const selectedType = this.value;
            typeSpecificFields.innerHTML = '';
            
            if (selectedType === 'MCQ') {
                typeSpecificFields.innerHTML = getMCQFields();
                initializeMCQHandlers();
            } else if (selectedType === 'IDENTIFICATION') {
                typeSpecificFields.innerHTML = getIdentificationFields();
            } else if (selectedType === 'ENUMERATION') {
                typeSpecificFields.innerHTML = getEnumerationFields();
            } else if (selectedType === 'TRUE_FALSE') {
                typeSpecificFields.innerHTML = getTrueFalseFields();
            } else if (selectedType === 'ESSAY') {
                typeSpecificFields.innerHTML = '<p class="text-sm text-gray-500">Essay questions do not require a correct answer.</p>';
            }
        });
    }
    
    // Handle form submission
    if (questionForm) {
        questionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(questionForm);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            // Determine the action URL based on mode
            let actionUrl = questionForm.action;
            if (isEditMode && questionIdInput.value) {
                // Update the action to the edit endpoint
                const examId = actionUrl.split('/').filter(Boolean).pop();
                actionUrl = `/exams/question/${questionIdInput.value}/edit/`;
            }
            
            fetch(actionUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                }
            })
            .catch(error => {
                // Error handled silently
            });
        });
    }
});

function populateTypeSpecificFields(questionType, correctAnswer, options) {
    if (questionType === 'MCQ' && options) {
        // First, we need to add more option fields if needed
        const mcqOptions = document.getElementById('mcqOptions');
        const correctAnswerSelect = document.getElementById('correct_answer');
        
        if (!mcqOptions || !correctAnswerSelect) {
            return;
        }
        
        // Get existing option inputs
        let existingInputs = document.querySelectorAll('[name="option_values[]"]');
        
        // Add more option fields if needed
        const optionLetters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
        
        while (existingInputs.length < options.length) {
            const index = existingInputs.length;
            const letter = optionLetters[index];
            
            const optionDiv = document.createElement('div');
            optionDiv.className = 'flex space-x-2';
            optionDiv.innerHTML = `
                <input type="text" name="option_keys[]" value="${letter}" class="w-16 px-3 py-2 border border-gray-300 rounded-md" readonly>
                <input type="text" name="option_values[]" placeholder="Option ${letter}" class="flex-1 px-3 py-2 border border-gray-300 rounded-md" required>
            `;
            mcqOptions.appendChild(optionDiv);
            
            // Add to correct answer dropdown
            const option = document.createElement('option');
            option.value = letter;
            option.textContent = letter;
            correctAnswerSelect.appendChild(option);
            
            // Re-query to get updated list
            existingInputs = document.querySelectorAll('[name="option_values[]"]');
        }
        
        // Now populate all option values
        const optionInputs = document.querySelectorAll('[name="option_values[]"]');
        options.forEach((option, index) => {
            if (optionInputs[index]) {
                optionInputs[index].value = option.value;
            }
        });
        
        // Set correct answer
        if (correctAnswerSelect && correctAnswer) {
            correctAnswerSelect.value = correctAnswer;
        }
        
    } else if (questionType === 'IDENTIFICATION' && correctAnswer) {
        const answerInput = document.getElementById('correct_answer');
        
        if (answerInput) {
            // Handle array or string
            if (Array.isArray(correctAnswer)) {
                answerInput.value = correctAnswer.join(', ');
            } else {
                answerInput.value = correctAnswer;
            }
        }
        
    } else if (questionType === 'ENUMERATION' && correctAnswer) {
        const answersTextarea = document.getElementById('correct_answers');
        const minRequiredInput = document.getElementById('min_required');
        
        if (answersTextarea && correctAnswer.items) {
            answersTextarea.value = correctAnswer.items.join(', ');
        }
        
        if (minRequiredInput && correctAnswer.min_required) {
            minRequiredInput.value = correctAnswer.min_required;
        }
        
    } else if (questionType === 'TRUE_FALSE') {
        const radioButtons = document.querySelectorAll('[name="correct_answer"]');
        
        radioButtons.forEach(radio => {
            if ((correctAnswer === true && radio.value === 'true') ||
                (correctAnswer === false && radio.value === 'false')) {
                radio.checked = true;
            }
        });
    }
}

function getMCQFields() {
    return `
        <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">
                Options <span class="text-red-500">*</span>
            </label>
            <div id="mcqOptions" class="space-y-2">
                <div class="flex space-x-2">
                    <input type="text" name="option_keys[]" value="A" class="w-16 px-3 py-2 border border-gray-300 rounded-md" readonly>
                    <input type="text" name="option_values[]" placeholder="Option A" class="flex-1 px-3 py-2 border border-gray-300 rounded-md" required>
                </div>
                <div class="flex space-x-2">
                    <input type="text" name="option_keys[]" value="B" class="w-16 px-3 py-2 border border-gray-300 rounded-md" readonly>
                    <input type="text" name="option_values[]" placeholder="Option B" class="flex-1 px-3 py-2 border border-gray-300 rounded-md" required>
                </div>
            </div>
            <button type="button" id="addOptionBtn" class="mt-2 text-sm text-blue-600 hover:text-blue-800">
                + Add Option
            </button>
        </div>
        
        <div class="mb-4">
            <label for="correct_answer" class="block text-sm font-medium text-gray-700 mb-2">
                Correct Answer <span class="text-red-500">*</span>
            </label>
            <select name="correct_answer" id="correct_answer" class="w-full px-3 py-2 border border-gray-300 rounded-md" required>
                <option value="">Select correct answer...</option>
                <option value="A">A</option>
                <option value="B">B</option>
            </select>
        </div>
    `;
}

function getIdentificationFields() {
    return `
        <div class="mb-4">
            <label for="correct_answer" class="block text-sm font-medium text-gray-700 mb-2">
                Correct Answer <span class="text-red-500">*</span>
            </label>
            <input 
                type="text" 
                name="correct_answer" 
                id="correct_answer"
                class="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
            >
        </div>
    `;
}

function getEnumerationFields() {
    return `
        <div class="mb-4">
            <label for="correct_answers" class="block text-sm font-medium text-gray-700 mb-2">
                Correct Answers (comma-separated) <span class="text-red-500">*</span>
            </label>
            <textarea 
                name="correct_answers" 
                id="correct_answers"
                rows="3"
                placeholder="Answer 1, Answer 2, Answer 3"
                class="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
            ></textarea>
        </div>
        
        <div class="mb-4">
            <label for="min_required" class="block text-sm font-medium text-gray-700 mb-2">
                Minimum Required Answers
            </label>
            <input 
                type="number" 
                name="min_required" 
                id="min_required"
                min="1"
                class="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
            <p class="text-xs text-gray-500 mt-1">Leave blank to require all answers</p>
        </div>
    `;
}

function getTrueFalseFields() {
    return `
        <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">
                Correct Answer <span class="text-red-500">*</span>
            </label>
            <div class="space-y-2">
                <label class="flex items-center">
                    <input type="radio" name="correct_answer" value="true" class="mr-2" required>
                    <span>True</span>
                </label>
                <label class="flex items-center">
                    <input type="radio" name="correct_answer" value="false" class="mr-2" required>
                    <span>False</span>
                </label>
            </div>
        </div>
    `;
}

function initializeMCQHandlers() {
    const addOptionBtn = document.getElementById('addOptionBtn');
    const mcqOptions = document.getElementById('mcqOptions');
    const correctAnswerSelect = document.getElementById('correct_answer');
    
    let optionCount = 2;
    const optionLetters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    
    if (addOptionBtn) {
        addOptionBtn.addEventListener('click', function() {
            if (optionCount < 26) {
                const letter = optionLetters[optionCount];
                const optionDiv = document.createElement('div');
                optionDiv.className = 'flex space-x-2';
                optionDiv.innerHTML = `
                    <input type="text" name="option_keys[]" value="${letter}" class="w-16 px-3 py-2 border border-gray-300 rounded-md" readonly>
                    <input type="text" name="option_values[]" placeholder="Option ${letter}" class="flex-1 px-3 py-2 border border-gray-300 rounded-md" required>
                `;
                mcqOptions.appendChild(optionDiv);
                
                // Add to correct answer dropdown
                const option = document.createElement('option');
                option.value = letter;
                option.textContent = letter;
                correctAnswerSelect.appendChild(option);
                
                optionCount++;
            }
        });
    }
}
