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

    // Auto-resize feedback textareas
    const autoResizeTextareas = document.querySelectorAll('[data-auto-resize="true"]');
    autoResizeTextareas.forEach(ta => {
        autoResizeTextarea(ta);
        ta.addEventListener('input', function () { autoResizeTextarea(ta); });
    });

    // Ctrl+Enter to save on feedback textareas
    document.querySelectorAll('.essay-feedback-input').forEach(function (ta) {
        ta.addEventListener('keydown', function (e) {
            if (e.ctrlKey && e.key === 'Enter') {
                var btn = document.querySelector('.grade-essay-btn[data-answer-id="' + ta.getAttribute('data-answer-id') + '"]');
                if (btn) btn.click();
            }
        });
    });

}

function autoResizeTextarea(el) {
    el.style.height = 'auto';
    el.style.height = Math.max(el.scrollHeight, 72) + 'px';
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
    var origBtnHTML = button.innerHTML;
    button.innerHTML = '<svg class="inline-block w-3.5 h-3.5 animate-spin mr-1" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> Saving...';
    button.disabled = true;
    
    try {
        const isUpdate = statusDiv && statusDiv.textContent.includes('Graded');
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
            updateGradingUI(answerId, data);
            showSuccess(data.message);
            updateFinalScore(data.total_score);
            button.innerHTML = 'Update Grade';

            // Auto-scroll to next ungraded essay
            var allSections = Array.from(document.querySelectorAll('.grading-section'));
            var currentIdx = allSections.findIndex(function (s) { return s.getAttribute('data-answer-id') === answerId; });
            for (var i = currentIdx + 1; i < allSections.length; i++) {
                if (allSections[i].getAttribute('data-is-graded') === 'false') {
                    allSections[i].scrollIntoView({ behavior: 'smooth', block: 'center' });
                    var nextInput = allSections[i].querySelector('.essay-points-input');
                    if (nextInput) setTimeout(function (el) { el.focus(); }, 600, nextInput);
                    break;
                }
            }
        } else {
            showError(data.error || 'Failed to save grade');
        }
    } catch (error) {
        console.error('Error grading essay:', error);
        showError('An error occurred while saving the grade');
    } finally {
        button.disabled = false;
        if (button.innerHTML === 'Saving...' || button.innerHTML.indexOf('Saving') !== -1) {
            button.innerHTML = origBtnHTML;
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
 * Fetch an AI grade suggestion from the server for a single answer.
 * Returns the parsed JSON result on success.
 */
async function fetchAiGrade(answerId, url) {
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
        throw new Error(msg);
    }

    return data;
}

/**
 * Populate grading form fields with an AI grade result (draft only).
 */
function populateAiGradeResult(answerId, data) {
    const pointsInput = document.querySelector(`.essay-points-input[data-answer-id="${answerId}"]`);
    const feedbackInput = document.querySelector(`.essay-feedback-input[data-answer-id="${answerId}"]`);
    const feedbackPanel = document.querySelector(`.ai-grade-feedback[data-answer-id="${answerId}"]`);

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
            let prefix = 'Suggested';
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
            metaEl.textContent = parts.join(' · ');
        }

        feedbackPanel.classList.remove('hidden');
    }
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
    var origBtnHTML = button.innerHTML;

    button.disabled = true;
    button.innerHTML = '<svg class="inline-block w-3.5 h-3.5 animate-spin mr-1" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> Grading...';
    button.style.opacity = '0.7';
    button.style.cursor = 'wait';

    try {
        const data = await fetchAiGrade(answerId, url);
        populateAiGradeResult(answerId, data);

        if (window.NotificationManager) {
            const pts = Number(data.points_earned || 0).toFixed(2);
            const max = Number(data.max_points || 0).toFixed(2);
            window.NotificationManager.success(`AI suggested ${pts} / ${max}. Review and Save Grade.`, 3500);
        }
    } catch (error) {
        console.error('AI grade error:', error);
        showError(error.message || 'Network error. Could not reach AI service.');
    } finally {
        button.disabled = false;
        button.innerHTML = origBtnHTML;
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

/* ── Modal helpers ─────────────────────────────────────────── */

function showBatchModal(title) {
    const modal = document.getElementById('batchActionModal');
    if (!modal) return;
    document.getElementById('batchModalTitle').textContent = title || 'Batch Grading';
    document.getElementById('batchModalLoading').classList.remove('hidden');
    document.getElementById('batchModalResult').classList.add('hidden');
    document.getElementById('batchModalCloseBtn').classList.add('hidden');
    document.getElementById('batchModalBar').style.width = '0%';
    document.getElementById('batchModalPercent').textContent = '0%';
    modal.classList.remove('hidden');
}

function updateBatchModal(current, total, statusText, subText) {
    const pct = total > 0 ? Math.round((current / total) * 100) : 0;
    const bar = document.getElementById('batchModalBar');
    const pctEl = document.getElementById('batchModalPercent');
    const statusEl = document.getElementById('batchModalStatus');
    const subEl = document.getElementById('batchModalSubtext');
    if (bar) bar.style.width = pct + '%';
    if (pctEl) pctEl.textContent = pct + '%';
    if (statusEl) statusEl.textContent = statusText || (current + ' of ' + total);
    if (subEl) subEl.textContent = subText || '';
}

function showBatchModalResult(successCount, failCount) {
    document.getElementById('batchModalLoading').classList.add('hidden');
    const resultDiv = document.getElementById('batchModalResult');
    const iconWrap = document.getElementById('batchModalIconWrap');
    const icon = document.getElementById('batchModalIcon');
    const titleEl = document.getElementById('batchModalResultTitle');
    const detailEl = document.getElementById('batchModalResultDetail');
    const closeBtn = document.getElementById('batchModalCloseBtn');

    const total = successCount + failCount;
    if (failCount === 0) {
        iconWrap.className = 'mx-auto mb-4 w-16 h-16 rounded-full flex items-center justify-center bg-green-100';
        icon.className = 'w-9 h-9 text-green-600';
        icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>';
        titleEl.textContent = 'All ' + total + ' complete';
        detailEl.textContent = successCount === 1 ? '1 essay graded.' : successCount + ' essays graded.';
    } else if (successCount === 0) {
        iconWrap.className = 'mx-auto mb-4 w-16 h-16 rounded-full flex items-center justify-center bg-red-100';
        icon.className = 'w-9 h-9 text-red-600';
        icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>';
        titleEl.textContent = 'Failed';
        detailEl.textContent = failCount + ' of ' + total + ' failed.';
    } else {
        iconWrap.className = 'mx-auto mb-4 w-16 h-16 rounded-full flex items-center justify-center bg-yellow-100';
        icon.className = 'w-9 h-9 text-yellow-600';
        icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/>';
        titleEl.textContent = successCount + ' of ' + total + ' complete';
        detailEl.textContent = failCount + ' failed.';
    }

    resultDiv.classList.remove('hidden');
    closeBtn.classList.remove('hidden');
    closeBtn.onclick = function () {
        document.getElementById('batchActionModal').classList.add('hidden');
        // Scroll to first graded essay
        var firstGraded = document.querySelector('.grading-section[data-is-graded="true"]');
        if (firstGraded) {
            firstGraded.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    };

    if (total > 0) {
        document.querySelectorAll('.batch-action-btn').forEach(function (b) { b.disabled = false; b.style.opacity = ''; b.style.cursor = ''; });
        refreshGradingStats();
    }
}

/* ── AI grade all ──────────────────────────────────────────── */

async function handleBatchAiGrade(event) {
    const button = event.target.closest('#batch-ai-grade-btn');
    if (!button) return;
    const sections = document.querySelectorAll('.grading-section');
    const ungradedSections = Array.from(sections).filter(
        section => section.getAttribute('data-is-graded') === 'false'
    );
    if (ungradedSections.length === 0) {
        showError('No ungraded essays to grade.');
        return;
    }

    showBatchModal('Grading Essays');
    document.getElementById('batchModalStatus').textContent = 'Preparing...';

    var origHTML = button.innerHTML;
    button.innerHTML = '<svg class="inline-block w-4 h-4 animate-spin mr-1.5" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> Grading...';
    button.disabled = true;
    button.style.opacity = '0.7';
    button.style.cursor = 'wait';

    await new Promise(function (r) { setTimeout(r, 100); });

    let completed = 0;
    let failed = [];
    const total = ungradedSections.length;

    for (const section of ungradedSections) {
        const answerId = section.getAttribute('data-answer-id');
        const aiButton = section.querySelector('.ai-grade-essay-btn');
        const url = aiButton ? aiButton.getAttribute('data-ai-grade-url') : null;

        updateBatchModal(completed, total, 'Grading essay ' + (completed + 1) + ' of ' + total);

        if (!url) {
            failed.push({ id: answerId, error: 'No AI grade URL' });
            completed++;
            continue;
        }

        try {
            const data = await fetchAiGrade(answerId, url);
            populateAiGradeResult(answerId, data);
        } catch (error) {
            console.error('AI grade error for answer ' + answerId + ':', error);
            failed.push({ id: answerId, error: error.message });
        }
        completed++;
    }

    updateBatchModal(completed, total, 'Finalising...');
    await new Promise(function (r) { setTimeout(r, 300); });
    button.innerHTML = origHTML;
    showBatchModalResult(completed - failed.length, failed.length);
}

/* ── Save all grades ───────────────────────────────────────── */

async function handleSaveAllGrades(event) {
    const button = event.target.closest('#save-all-grades-btn');
    if (!button) return;
    const sections = document.querySelectorAll('.grading-section');
    const ungradedSections = Array.from(sections).filter(
        section => section.getAttribute('data-is-graded') === 'false'
    );
    if (ungradedSections.length === 0) {
        showError('No ungraded essays to save.');
        return;
    }

    if (ungradedSections.length > 5 && !confirm('Save grades for ' + ungradedSections.length + ' ungraded essays? Make sure you have reviewed each one.')) {
        return;
    }

    showBatchModal('Saving Grades');
    document.getElementById('batchModalStatus').textContent = 'Preparing...';
    document.getElementById('batchModalHeader').className = 'px-6 py-5 bg-gradient-to-r from-emerald-600 to-green-600 text-white flex items-center gap-3';
    document.getElementById('batchModalBar').className = 'h-full bg-gradient-to-r from-emerald-500 to-green-500 rounded-full transition-all duration-300';

    var origHTML = button.innerHTML;
    button.innerHTML = '<svg class="inline-block w-4 h-4 animate-spin mr-1.5" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> Saving...';
    button.disabled = true;
    button.style.opacity = '0.7';
    button.style.cursor = 'wait';

    await new Promise(function (r) { setTimeout(r, 100); });

    let completed = 0;
    let failed = [];
    const total = ungradedSections.length;

    for (const section of ungradedSections) {
        const answerId = section.getAttribute('data-answer-id');
        const pointsInput = document.querySelector('.essay-points-input[data-answer-id="' + answerId + '"]');
        const feedbackInput = document.querySelector('.essay-feedback-input[data-answer-id="' + answerId + '"]');

        if (!pointsInput) {
            failed.push({ id: answerId, error: 'Input not found' });
            completed++;
            updateBatchModal(completed, total);
            continue;
        }

        const pointsEarned = parseFloat(pointsInput.value);
        const teacherFeedback = feedbackInput ? feedbackInput.value.trim() : '';
        const maxPoints = parseFloat(pointsInput.getAttribute('data-max-points'));

        if (isNaN(pointsEarned) || pointsEarned < 0 || pointsEarned > maxPoints) {
            failed.push({ id: answerId, error: 'Invalid points' });
            completed++;
            updateBatchModal(completed, total);
            continue;
        }

        updateBatchModal(completed, total, 'Saving ' + (completed + 1) + ' of ' + total);

        try {
            const response = await fetch('/attempts/teacher/grading/essay/' + answerId + '/grade/', {
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
                updateGradingUI(answerId, data);
                updateFinalScore(data.total_score);
            } else {
                failed.push({ id: answerId, error: data.error || 'Save failed' });
            }
        } catch (error) {
            console.error('Save error for answer ' + answerId + ':', error);
            failed.push({ id: answerId, error: error.message });
        }
        completed++;
    }

    updateBatchModal(completed, total, 'Finalising...');
    await new Promise(function (r) { setTimeout(r, 300); });
    button.innerHTML = origHTML;
    showBatchModalResult(completed - failed.length, failed.length);
}

/* ── Refresh grading summary counts ────────────────────────── */

function refreshGradingStats() {
    var graded = 0;
    var ungraded = 0;
    document.querySelectorAll('.grading-section').forEach(function (s) {
        if (s.getAttribute('data-is-graded') === 'true') graded++;
        else ungraded++;
    });
    var total = graded + ungraded;

    var totalEl = document.querySelector('.grid.grid-cols-1.md\\:grid-cols-4 .text-2xl.font-bold.text-gray-900');
    var gradedEl = document.querySelector('.grid.grid-cols-1.md\\:grid-cols-4 .text-2xl.font-bold.text-green-600');
    var ungradedEl = document.querySelector('.grid.grid-cols-1.md\\:grid-cols-4 .text-2xl.font-bold.text-yellow-600');
    var batchBar = document.getElementById('batch-ai-bar');

    if (totalEl) totalEl.textContent = total;
    if (gradedEl) gradedEl.textContent = graded;
    if (ungradedEl) {
        ungradedEl.textContent = ungraded;
        if (ungraded === 0 && batchBar) batchBar.remove();
    }
}
