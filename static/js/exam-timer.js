/**
 * Exam Timer
 * Handles countdown timer and auto-submission on timeout
 * Implements timer persistence across page refresh
 */

class ExamTimer {
    constructor(remainingSeconds, attemptId) {
        this.remainingSeconds = remainingSeconds;
        this.attemptId = attemptId;
        this.timerElement = document.getElementById('timer');
        this.intervalId = null;
        this.storageKey = `exam_timer_${attemptId}`;
        
        // Load saved timer state if available
        this.loadTimerState();
    }
    
    start() {
        // Update display immediately
        this.updateDisplay();
        
        // Start countdown
        this.intervalId = setInterval(() => {
            this.remainingSeconds--;
            this.updateDisplay();
            this.saveTimerState();
            
            // Check if time is up
            if (this.remainingSeconds <= 0) {
                this.stop();
                this.autoSubmit();
            }
            
            // Warning at 5 minutes
            if (this.remainingSeconds === 300) {
                this.showWarning('5 minutes remaining!');
            }
            
            // Warning at 1 minute
            if (this.remainingSeconds === 60) {
                this.showWarning('1 minute remaining!');
            }
        }, 1000);
    }
    
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
    
    updateDisplay() {
        const minutes = Math.floor(this.remainingSeconds / 60);
        const seconds = this.remainingSeconds % 60;
        
        const display = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        this.timerElement.textContent = display;
        
        // Change color when time is running out
        if (this.remainingSeconds <= 60) {
            this.timerElement.classList.remove('text-blue-600');
            this.timerElement.classList.add('text-red-600');
        } else if (this.remainingSeconds <= 300) {
            this.timerElement.classList.remove('text-blue-600');
            this.timerElement.classList.add('text-yellow-600');
        }
    }
    
    saveTimerState() {
        const state = {
            remainingSeconds: this.remainingSeconds,
            timestamp: Date.now()
        };
        localStorage.setItem(this.storageKey, JSON.stringify(state));
    }
    
    loadTimerState() {
        const savedState = localStorage.getItem(this.storageKey);
        if (savedState) {
            try {
                const state = JSON.parse(savedState);
                const elapsed = Math.floor((Date.now() - state.timestamp) / 1000);
                this.remainingSeconds = Math.max(0, state.remainingSeconds - elapsed);
            } catch (error) {
                console.error('Error loading timer state:', error);
            }
        }
    }
    
    clearTimerState() {
        localStorage.removeItem(this.storageKey);
    }
    
    showWarning(message) {
        // Use NotificationManager from utils.js
        NotificationManager.warning(message);
    }
    
    async autoSubmit() {
        
        // Show notification
        const notification = document.createElement('div');
        notification.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50';
        notification.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-sm">
                <h3 class="text-lg font-semibold text-gray-900 mb-2">Time's Up!</h3>
                <p class="text-gray-600 mb-4">Your exam is being submitted automatically...</p>
                <div class="flex justify-center">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
            </div>
        `;
        document.body.appendChild(notification);
        
        // Submit the exam with retry logic
        try {
            let response;
            if (window.AjaxClient) {
                const client = new AjaxClient({ maxRetries: 3, retryDelay: 2000 });
                response = await client.post(`/attempts/student/attempts/${this.attemptId}/submit/`, {});
            } else {
                response = await fetch(`/attempts/student/attempts/${this.attemptId}/submit/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    }
                });
            }
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.clearTimerState();
                // Redirect to submission confirmation page
                window.location.href = data.redirect_url || `/attempts/student/attempts/${this.attemptId}/submitted/`;
            } else {
                throw new Error(data.error || 'Failed to submit exam');
            }
        } catch (error) {
            console.error('Error auto-submitting exam:', error);
            
            // Show user-friendly error message
            NotificationManager.error(
                'Failed to submit exam automatically. Please submit manually or contact your teacher.',
                0  // Persistent notification
            );
            
            // Remove loading notification
            notification.remove();
        }
    }
}

// Initialize timer when page loads
document.addEventListener('DOMContentLoaded', function() {
    const timerElement = document.getElementById('timer');
    if (timerElement) {
        const remainingSeconds = parseInt(timerElement.getAttribute('data-remaining'));
        const attemptId = parseInt(timerElement.getAttribute('data-attempt-id'));
        
        const timer = new ExamTimer(remainingSeconds, attemptId);
        timer.start();
        
        // Handle page unload
        window.addEventListener('beforeunload', function() {
            timer.saveTimerState();
        });
    }
});

// Helper function to get CSRF token (uses CookieUtils from utils.js)
function getCookie(name) {
    return CookieUtils.getCookie(name);
}
