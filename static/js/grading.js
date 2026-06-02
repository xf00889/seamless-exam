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

    // AI Grade buttons
    const aiButtons = document.querySelectorAll('.ai-grade-essay-btn');
    aiButtons.forEach(button => {
        button.addEventListener('click', handleAiGradeEssay);
    });

    // Dismiss button for AI grade feedback panel
    const dismissButtons = document.querySelectorAll('.ai-grade-dismiss');
    dismissButtons.forEach(button => {
        button.addEventListener('click', handleAiGradeDismiss);
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


/**
 * Handle AI grade essay button click.
 * Fetches a suggested score and feedback from the AI service,
 * then populates the points input and feedback textarea as a DRAFT.
 * The teacher still must click "Save Grade" to confirm.
 */
async function handleAiGradeEssay(event) {
    const button = event.currentTarget;
    const answerId = button.getAttribute('data-answer-id');
    const url = button.getAttribute('data-ai-grade-url');
    if (!url) {
        showError('AI grade URL not configured for this answer.');
        return;
    }

    const labelEl = button.querySelector('.ai-grade-label');
    const originalLabel = labelEl ? labelEl.textContent : 'AI Grade';
    const pointsInput = document.querySelector(`.essay-points-input[data-answer-id="${answerId}"]`);
    const feedbackInput = document.querySelector(`.essay-feedback-input[data-answer-id="${answerId}"]`);
    const feedbackPanel = document.querySelector(`.ai-grade-feedback[data-answer-id="${answerId}"]`);

    // Disable button + show loading
    button.disabled = true;
    if (labelEl) labelEl.textContent = 'Grading...';
    button.style.opacity = '0.7';
    button.style.cursor = 'wait';

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({}),
        });

        const raw = await response.text();
        let data = null;
        try { data = raw ? JSON.parse(raw) : null; } catch (e) { /* non-JSON */ }

        if (!response.ok || !data || !data.success) {
            const msg = (data && data.error) || `AI grading failed (HTTP ${response.status})`;
            showError(msg);
            return;
        }

        if (pointsInput) {
            pointsInput.value = data.points_earned;
            pointsInput.dispatchEvent(new Event('input', { bubbles: true }));
        }
        if (feedbackInput && data.feedback) {
            feedbackInput.value = data.feedback;
        }

        if (feedbackPanel) {
            const reasoningEl = feedbackPanel.querySelector('.ai-grade-reasoning');
            const suggestedEl = feedbackPanel.querySelector('.ai-grade-suggested');
            const metaEl = feedbackPanel.querySelector('.ai-grade-meta');

            if (reasoningEl) {
                let prefix = 'AI suggestion';
                if (data.is_blank) prefix = 'Blank answer';
                else if (data.is_off_topic) prefix = 'Off-topic answer';
                reasoningEl.textContent = prefix + ' — review and edit before saving.';
            }
            if (suggestedEl) {
                const pts = Number(data.points_earned || 0).toFixed(2);
                const max = Number(data.max_points || 0).toFixed(2);
                let txt = `Suggested score: ${pts} / ${max}`;
                if (data.reasoning) txt += ' — ' + data.reasoning;
                suggestedEl.textContent = txt;
            }
            if (metaEl) {
                const bd = data.breakdown || {};
                const parts = [];
                if (bd.relevance != null) parts.push(`Relevance ${bd.relevance}/10`);
                if (bd.correctness != null) parts.push(`Correctness ${bd.correctness}/10`);
                if (bd.depth != null) parts.push(`Depth ${bd.depth}/10`);
                if (data.model_used) parts.push('Model: ' + data.model_used);
                metaEl.textContent = parts.join(' · ');
            }

            feedbackPanel.classList.remove('hidden');
        }

        if (window.NotificationManager) {
            const pts = Number(data.points_earned || 0).toFixed(2);
            const max = Number(data.max_points || 0).toFixed(2);
            window.NotificationManager.success(`AI suggested ${pts} / ${max}. Review and Save Grade.`, 3500);
        }
    } catch (error) {
        console.error('AI grade error:', error);
        showError('Network error. Could not reach AI service.');
    } finally {
        button.disabled = false;
        if (labelEl) labelEl.textContent = originalLabel;
        button.style.opacity = '';
        button.style.cursor = '';
    }
}

function handleAiGradeDismiss(event) {
    const button = event.currentTarget;
    const panel = button.closest('.ai-grade-feedback');
    if (panel) panel.classList.add('hidden');
}
