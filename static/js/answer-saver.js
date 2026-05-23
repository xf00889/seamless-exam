/**
 * Answer Saver
 * Handles auto-saving of student answers during exam
 * Implements AJAX requests with retry logic and connection drop handling
 * Requirements: 11.1, 11.2, 19.1
 */

class AnswerSaver {
    constructor(attemptId) {
        this.attemptId = attemptId;
        this.saveQueue = new Map(); // questionId -> answer data
        this.saveInProgress = new Set(); // questionIds currently being saved
        this.retryAttempts = new Map(); // questionId -> retry count
        this.maxRetries = 3;
        this.retryDelay = 1000; // Start with 1 second
        this.saveDebounceTime = 1000; // Wait 1 second after typing stops
        this.debounceTimers = new Map(); // questionId -> timer
        this.isOnline = navigator.onLine;
        
        this.initializeEventListeners();
        this.setupConnectionMonitoring();
    }
    
    initializeEventListeners() {
        // Listen to all answer inputs
        const answerInputs = document.querySelectorAll('.answer-input');
        
        answerInputs.forEach(input => {
            const questionId = input.getAttribute('data-question-id');
            
            if (input.type === 'radio') {
                // For radio buttons, save immediately on change
                input.addEventListener('change', () => {
                    this.handleAnswerChange(questionId, input);
                });
            } else {
                // For text inputs and textareas, debounce the save
                input.addEventListener('input', () => {
                    this.handleAnswerChange(questionId, input);
                });
                
                // Also save on blur (when user leaves the field)
                input.addEventListener('blur', () => {
                    this.clearDebounce(questionId);
                    this.saveAnswer(questionId);
                });
            }
        });
        
        // Setup submit button
        const submitBtn = document.getElementById('submit-exam-btn');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                this.handleExamSubmit();
            });
        }
        
        // Setup modal buttons
        const confirmBtn = document.getElementById('confirm-submit-btn');
        const cancelBtn = document.getElementById('cancel-submit-btn');
        
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => {
                this.confirmSubmit();
            });
        }
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.hideSubmitModal();
            });
        }
        
        // Save all answers before page unload
        window.addEventListener('beforeunload', (e) => {
            // Try to save any pending answers
            if (this.saveQueue.size > 0) {
                this.saveAllPending();
                // Show warning if there are unsaved changes
                e.preventDefault();
                e.returnValue = '';
            }
        });
    }
    
    setupConnectionMonitoring() {
        // Monitor online/offline status
        window.addEventListener('online', () => {
            // Connection restored
            this.isOnline = true;
            this.showConnectionStatus('Connection restored', 'success');
            // Retry any failed saves
            this.retryFailedSaves();
        });
        
        window.addEventListener('offline', () => {
            // Connection lost
            this.isOnline = false;
            this.showConnectionStatus('Connection lost - answers will be saved when connection is restored', 'warning');
        });
    }
    
    handleAnswerChange(questionId, input) {
        // Get the answer value
        let answerValue;
        
            if (input.type === 'radio') {
                // For radio buttons, get the checked value
                const radioGroup = document.querySelectorAll(`input[name="${input.name}"]:checked`);
                if (radioGroup.length > 0) {
                    answerValue = radioGroup[0].value;
                }
            } else {
                // For text inputs and textareas
                answerValue = input.value;
            }
            
            // Store in queue
            this.saveQueue.set(questionId, {
                question_id: parseInt(questionId),
                answer_text: answerValue
            });
            
            // Update sidebar immediately for visual feedback (even before save completes)
            if (window.examNavigation && answerValue) {
                window.examNavigation.markQuestionAnswered(questionId);
            }
            
            // Clear existing debounce timer
            this.clearDebounce(questionId);
            
            // For radio buttons, save immediately
            if (input.type === 'radio') {
                this.saveAnswer(questionId);
            } else {
                // For text inputs, debounce the save
                const timer = setTimeout(() => {
                    this.saveAnswer(questionId);
                }, this.saveDebounceTime);
                
                this.debounceTimers.set(questionId, timer);
            }
    }
    
    clearDebounce(questionId) {
        if (this.debounceTimers.has(questionId)) {
            clearTimeout(this.debounceTimers.get(questionId));
            this.debounceTimers.delete(questionId);
        }
    }
    
    async saveAnswer(questionId) {
        // Check if we have data to save
        if (!this.saveQueue.has(questionId)) {
            return;
        }
        
        // Check if already saving this question
        if (this.saveInProgress.has(questionId)) {
            return;
        }
        
        const answerData = this.saveQueue.get(questionId);
        
        // Mark as saving
        this.saveInProgress.add(questionId);
        this.updateSaveStatus(questionId, 'saving');
        
        try {
            // Use AjaxClient if available, otherwise fallback to fetch
            let response;
            if (window.AjaxClient) {
                const client = new AjaxClient({ maxRetries: 0 }); // We handle retries ourselves
                response = await client.post(`/attempts/student/attempts/${this.attemptId}/save/`, answerData);
            } else {
                response = await fetch(`/attempts/student/attempts/${this.attemptId}/save/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify(answerData)
                });
            }
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success) {
                    // Remove from queue and reset retry count
                    this.saveQueue.delete(questionId);
                    this.retryAttempts.delete(questionId);
                    this.updateSaveStatus(questionId, 'saved');
                    
                    // Update sidebar navigation
                    if (window.examNavigation) {
                        window.examNavigation.markQuestionAnswered(questionId);
                    }
                    
                    // Answer saved successfully
                } else {
                    throw new Error(data.error || 'Failed to save answer');
                }
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error(`Error saving answer for question ${questionId}:`, error);
            
            // Handle retry logic
            await this.handleSaveError(questionId, error);
        } finally {
            this.saveInProgress.delete(questionId);
        }
    }
    
    async handleSaveError(questionId, error) {
        const retryCount = this.retryAttempts.get(questionId) || 0;
        
        if (retryCount < this.maxRetries) {
            // Increment retry count
            this.retryAttempts.set(questionId, retryCount + 1);
            
            // Calculate exponential backoff delay
            const delay = this.retryDelay * Math.pow(2, retryCount);
            
            // Schedule retry with exponential backoff
            
            this.updateSaveStatus(questionId, 'retrying');
            
            // Wait and retry
            await this.sleep(delay);
            
            // Only retry if still online or connection restored
            if (this.isOnline) {
                await this.saveAnswer(questionId);
            } else {
                this.updateSaveStatus(questionId, 'pending');
                this.showConnectionStatus('Answer will be saved when connection is restored', 'warning');
            }
        } else {
            // Max retries reached
            console.error(`Failed to save answer for question ${questionId} after ${this.maxRetries} attempts`);
            this.updateSaveStatus(questionId, 'error');
            this.showConnectionStatus('Failed to save answer. Please check your connection.', 'error');
        }
    }
    
    async retryFailedSaves() {
        // Retry all answers in the queue
        const questionIds = Array.from(this.saveQueue.keys());
        
        for (const questionId of questionIds) {
            // Reset retry count for fresh attempts
            this.retryAttempts.set(questionId, 0);
            await this.saveAnswer(questionId);
        }
    }
    
    saveAllPending() {
        // Synchronously save all pending answers (for beforeunload)
        const questionIds = Array.from(this.saveQueue.keys());
        
        for (const questionId of questionIds) {
            const answerData = this.saveQueue.get(questionId);
            
            // Use sendBeacon for reliable delivery during page unload
            const formData = new FormData();
            formData.append('question_id', answerData.question_id);
            formData.append('answer_text', answerData.answer_text);
            
            const blob = new Blob([JSON.stringify(answerData)], { type: 'application/json' });
            navigator.sendBeacon(
                `/attempts/student/attempts/${this.attemptId}/save/`,
                blob
            );
        }
    }
    
    updateSaveStatus(questionId, status) {
        const statusElement = document.querySelector(`.save-status[data-question-id="${questionId}"]`);
        if (!statusElement) return;
        
        const savedIndicator = statusElement.querySelector('.saved-indicator');
        const savingIndicator = statusElement.querySelector('.saving-indicator');
        
        // Hide all indicators first
        savedIndicator.classList.add('hidden');
        savingIndicator.classList.add('hidden');
        
        switch (status) {
            case 'saving':
            case 'retrying':
                savingIndicator.classList.remove('hidden');
                savingIndicator.textContent = status === 'retrying' ? 'Retrying...' : 'Saving...';
                break;
            case 'saved':
                savedIndicator.classList.remove('hidden');
                // Hide after 3 seconds
                setTimeout(() => {
                    savedIndicator.classList.add('hidden');
                }, 3000);
                break;
            case 'error':
                savingIndicator.classList.remove('hidden');
                savingIndicator.textContent = 'Save failed';
                savingIndicator.classList.add('text-red-600');
                break;
            case 'pending':
                savingIndicator.classList.remove('hidden');
                savingIndicator.textContent = 'Pending...';
                savingIndicator.classList.add('text-yellow-600');
                break;
        }
    }
    
    showConnectionStatus(message, type) {
        // Use NotificationManager from utils.js
        NotificationManager.show(message, type);
    }
    
    handleExamSubmit() {
        // Check if there are unsaved answers
        if (this.saveQueue.size > 0 || this.saveInProgress.size > 0) {
            this.showConnectionStatus('Please wait while we save your answers...', 'warning');
            
            // Wait for all saves to complete, then redirect to review page
            this.waitForSavesToComplete().then(() => {
                this.redirectToReview();
            });
        } else {
            this.redirectToReview();
        }
    }
    
    redirectToReview() {
        // Redirect to review page
        window.location.href = `/attempts/student/attempts/${this.attemptId}/review/`;
    }
    
    async waitForSavesToComplete() {
        // Wait for all pending saves to complete
        while (this.saveQueue.size > 0 || this.saveInProgress.size > 0) {
            await this.sleep(100);
        }
    }
    
    showSubmitModal() {
        const modal = document.getElementById('submit-modal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }
    
    hideSubmitModal() {
        const modal = document.getElementById('submit-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }
    
    async confirmSubmit() {
        const confirmBtn = document.getElementById('confirm-submit-btn');
        if (confirmBtn) {
            confirmBtn.disabled = true;
            confirmBtn.textContent = 'Submitting...';
        }
        
        try {
            const response = await fetch(`/attempts/student/attempts/${this.attemptId}/submit/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                // Clear timer state
                localStorage.removeItem(`exam_timer_${this.attemptId}`);
                
                // Redirect to submission confirmation page
                window.location.href = data.redirect_url || `/attempts/student/attempts/${this.attemptId}/submitted/`;
            } else {
                throw new Error(data.error || 'Failed to submit exam');
            }
        } catch (error) {
            console.error('Error submitting exam:', error);
            this.showConnectionStatus('Failed to submit exam. Please try again.', 'error');
            
            if (confirmBtn) {
                confirmBtn.disabled = false;
                confirmBtn.textContent = 'Yes, Submit';
            }
        }
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Helper function to get CSRF token (uses CookieUtils from utils.js)
function getCookie(name) {
    return CookieUtils.getCookie(name);
}

function getCSRFToken() {
    return CookieUtils.getCSRFToken();
}

// Initialize answer saver when page loads
document.addEventListener('DOMContentLoaded', function() {
    const examForm = document.getElementById('exam-form');
    if (examForm) {
        const attemptId = examForm.getAttribute('data-attempt-id');
        const answerSaver = new AnswerSaver(parseInt(attemptId));
        
        // Make it globally accessible for debugging
        window.answerSaver = answerSaver;
    }
});
