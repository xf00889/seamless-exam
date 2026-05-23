/**
 * Grading Interface JavaScript
 * Handles essay grading interactions and AJAX submissions
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeGrading();
});

/**
 * Initialize grading interface
 */
function initializeGrading() {
    const gradeButtons = document.querySelectorAll('.grade-essay-btn');
    
    gradeButtons.forEach(button => {
        button.addEventListener('click', handleGradeEssay);
    });
    
    // Add input validation for points
    const pointsInputs = document.querySelectorAll('.essay-points-input');
    pointsInputs.forEach(input => {
        input.addEventListener('input', validatePoints);
    });
}

/**
 * Validate points input
 */
function validatePoints(event) {
    const input = event.target;
    const maxPoints = parseFloat(input.getAttribute('data-max-points'));
    const value = parseFloat(input.value);
    
    if (value < 0) {
        input.value = 0;
    } else if (value > maxPoints) {
        input.value = maxPoints;
    }
}

/**
 * Handle essay grading submission
 */
async function handleGradeEssay(event) {
    const button = event.target;
    const answerId = button.getAttribute('data-answer-id');
    
    // Get input values
    const pointsInput = document.querySelector(`.essay-points-input[data-answer-id="${answerId}"]`);
    const feedbackInput = document.querySelector(`.essay-feedback-input[data-answer-id="${answerId}"]`);
    const statusDiv = document.querySelector(`.grading-status[data-answer-id="${answerId}"]`);
    
    if (!pointsInput) {
        showError('Points input not found');
        return;
    }
    
    const pointsEarned = parseFloat(pointsInput.value);
    const teacherFeedback = feedbackInput ? feedbackInput.value.trim() : '';
    const maxPoints = parseFloat(pointsInput.getAttribute('data-max-points'));
    
    // Validate points
    if (isNaN(pointsEarned) || pointsEarned < 0 || pointsEarned > maxPoints) {
        showError(`Points must be between 0 and ${maxPoints}`);
        return;
    }
    
    // Disable button during submission
    button.disabled = true;
    button.textContent = 'Saving...';
    
    try {
        // Determine if this is a new grade or update
        const isUpdate = button.textContent.includes('Update') || statusDiv.textContent.includes('Graded');
        const url = isUpdate 
            ? `/attempts/teacher/grading/essay/${answerId}/update/`
            : `/attempts/teacher/grading/essay/${answerId}/grade/`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                points_earned: pointsEarned,
                teacher_feedback: teacherFeedback || null
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Update UI
            updateGradingUI(answerId, data);
            showSuccess(data.message);
            
            // Update final score
            updateFinalScore(data.total_score);
            
            // Update button text
            button.textContent = 'Update Grade';
        } else {
            showError(data.error || 'Failed to save grade');
        }
    } catch (error) {
        console.error('Error grading essay:', error);
        showError('An error occurred while saving the grade');
    } finally {
        button.disabled = false;
        if (button.textContent === 'Saving...') {
            button.textContent = 'Save Grade';
        }
    }
}

/**
 * Update grading UI after successful submission
 */
function updateGradingUI(answerId, data) {
    const statusDiv = document.querySelector(`.grading-status[data-answer-id="${answerId}"]`);
    
    if (statusDiv) {
        const now = new Date();
        const formattedDate = now.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
        
        statusDiv.innerHTML = `
            <span class="text-green-600">
                <svg class="inline w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                </svg>
                Graded on ${formattedDate}
            </span>
        `;
    }
    
    // Update the graded badge in the header
    const section = document.querySelector(`.grading-section[data-answer-id="${answerId}"]`);
    if (section) {
        const header = section.closest('.bg-white').querySelector('.flex.items-center.mb-2');
        if (header) {
            // Remove "Needs Grading" badge if exists
            const needsGradingBadge = header.querySelector('.bg-yellow-100');
            if (needsGradingBadge) {
                needsGradingBadge.remove();
            }
            
            // Add or update "Graded" badge
            let gradedBadge = header.querySelector('.bg-green-100');
            if (!gradedBadge) {
                gradedBadge = document.createElement('span');
                gradedBadge.className = 'ml-2 px-2 py-1 text-xs font-semibold rounded bg-green-100 text-green-800';
                header.appendChild(gradedBadge);
            }
            gradedBadge.textContent = `Graded: ${data.points_earned.toFixed(2)} pts`;
        }
    }
}

/**
 * Update final score display
 */
function updateFinalScore(totalScore) {
    const finalScoreElement = document.getElementById('final-score');
    if (finalScoreElement) {
        finalScoreElement.textContent = `${totalScore.toFixed(2)} points`;
    }
}

/**
 * Get CSRF token from cookie (uses CookieUtils from utils.js)
 */
function getCsrfToken() {
    return CookieUtils.getCSRFToken();
}

/**
 * Show success message (uses NotificationManager from utils.js)
 */
function showSuccess(message) {
    NotificationManager.success(message, 3000);
}

/**
 * Show error message (uses NotificationManager from utils.js)
 */
function showError(message) {
    NotificationManager.error(message, 3000);
}
