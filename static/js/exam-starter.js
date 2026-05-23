/**
 * Exam Starter
 * Handles starting exams and creating attempts
 */

let currentExamId = null;
let currentButton = null;

document.addEventListener('DOMContentLoaded', function() {
    const startButtons = document.querySelectorAll('.start-exam-btn');
    const modal = document.getElementById('monitoring-modal');
    const cancelBtn = document.getElementById('cancel-exam-btn');
    const acceptBtn = document.getElementById('accept-start-btn');
    
    // Show modal when Start Exam is clicked
    startButtons.forEach(button => {
        button.addEventListener('click', function() {
            currentExamId = this.getAttribute('data-exam-id');
            currentButton = this;
            modal.classList.remove('hidden');
        });
    });
    
    // Cancel button - close modal
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            modal.classList.add('hidden');
            currentExamId = null;
            currentButton = null;
        });
    }
    
    // Accept button - start the exam
    if (acceptBtn) {
        acceptBtn.addEventListener('click', function() {
            modal.classList.add('hidden');
            if (currentExamId && currentButton) {
                startExam(currentExamId, currentButton);
            }
        });
    }
    
    // Close modal when clicking outside
    modal?.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.classList.add('hidden');
            currentExamId = null;
            currentButton = null;
        }
    });
});

async function startExam(examId, button) {
    // Disable button to prevent double-clicks
    button.disabled = true;
    button.textContent = 'Starting...';
    
    try {
        // Get CSRF token (try global function first, then fallback to local)
        const csrfToken = (typeof getCSRFToken !== 'undefined') 
            ? getCSRFToken() 
            : (getCookie('exam_csrftoken') || getCookie('csrftoken'));
        
        const response = await fetch(`/attempts/student/exams/${examId}/start/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            // Server returned HTML instead of JSON (likely an error page or redirect)
            console.error('Server returned non-JSON response:', response.status);
            
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/student/login/';
                return;
            }
            
            throw new Error('Server returned an unexpected response. Please try again.');
        }
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Redirect to exam taking page
            window.location.href = `/attempts/student/attempts/${data.attempt_id}/take/`;
        } else {
            button.disabled = false;
            button.textContent = 'Start Exam';
        }
    } catch (error) {
        button.disabled = false;
        button.textContent = 'Start Exam';
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
