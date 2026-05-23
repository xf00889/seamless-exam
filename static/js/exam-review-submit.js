/**
 * Exam Review Submit
 * Handles submission from the review page
 */

class ExamReviewSubmit {
    constructor(attemptId) {
        this.attemptId = attemptId;
        this.submitBtn = document.getElementById('submit-exam-btn');
        this.confirmBtn = document.getElementById('confirm-submit-btn');
        this.cancelBtn = document.getElementById('cancel-submit-btn');
        this.submitModal = document.getElementById('submit-modal');
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        if (this.submitBtn) {
            this.submitBtn.addEventListener('click', () => {
                this.showSubmitModal();
            });
        }
        
        if (this.confirmBtn) {
            this.confirmBtn.addEventListener('click', () => {
                this.confirmSubmit();
            });
        }
        
        if (this.cancelBtn) {
            this.cancelBtn.addEventListener('click', () => {
                this.hideSubmitModal();
            });
        }
        
        // Close modal on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.submitModal.classList.contains('hidden')) {
                this.hideSubmitModal();
            }
        });
    }
    
    showSubmitModal() {
        if (this.submitModal) {
            this.submitModal.classList.remove('hidden');
        }
    }
    
    hideSubmitModal() {
        if (this.submitModal) {
            this.submitModal.classList.add('hidden');
        }
    }
    
    async confirmSubmit() {
        if (this.confirmBtn) {
            this.confirmBtn.disabled = true;
            this.confirmBtn.textContent = 'Submitting...';
        }
        
        try {
            // Get CSRF token
            const csrfToken = this.getCSRFToken();
            
            const response = await fetch(`/attempts/student/attempts/${this.attemptId}/submit/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
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
            // Show error message
            if (window.NotificationManager) {
                window.NotificationManager.show('Failed to submit exam. Please try again.', 'error');
            }
            
            if (this.confirmBtn) {
                this.confirmBtn.disabled = false;
                this.confirmBtn.textContent = 'Yes, Submit';
            }
        }
    }
    
    getCSRFToken() {
        // Try to get from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        // Try to get from meta tag
        const metaTag = document.querySelector('meta[name=csrf-token]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        // Try to get from form
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            return csrfInput.value;
        }
        
        return '';
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Get attempt ID from global variable or URL path
    let attemptId = null;
    
    if (window.REVIEW_ATTEMPT_ID) {
        attemptId = window.REVIEW_ATTEMPT_ID;
    } else {
        // Fallback: get from URL path
        const pathMatch = window.location.pathname.match(/\/attempts\/student\/attempts\/(\d+)\//);
        if (pathMatch) {
            attemptId = parseInt(pathMatch[1]);
        }
    }
    
    if (attemptId) {
        window.examReviewSubmit = new ExamReviewSubmit(attemptId);
    } else {
        console.error('Could not find attempt ID');
    }
});

