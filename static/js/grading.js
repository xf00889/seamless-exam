document.addEventListener('DOMContentLoaded', function() {
  initializeGrading();
});

function initializeGrading() {
  document.querySelectorAll('.grade-essay-btn').forEach(function(b) {
    b.addEventListener('click', handleGradeEssay);
  });
  document.querySelectorAll('.essay-points-input').forEach(function(i) {
    i.addEventListener('input', validatePoints);
    i.addEventListener('change', function() { updateScoreProgress(i); });
    updateScoreProgress(i);
  });
  document.querySelectorAll('.ai-grade-essay-btn').forEach(function(b) {
    b.addEventListener('click', handleAiGradeEssay);
  });
  document.querySelectorAll('[data-auto-resize="true"]').forEach(function(ta) {
    autoResizeTextarea(ta);
    ta.addEventListener('input', function() { autoResizeTextarea(ta); });
  });
  document.querySelectorAll('.essay-feedback-input').forEach(function(ta) {
    ta.addEventListener('keydown', function(e) {
      if (e.ctrlKey && e.key === 'Enter') {
        var btn = document.querySelector('.grade-essay-btn[data-answer-id="' + ta.getAttribute('data-answer-id') + '"]');
        if (btn) btn.click();
      }
    });
  });
  document.querySelectorAll('.feedback-chip').forEach(function(chip) {
    chip.addEventListener('click', handleFeedbackChip);
  });
}

function autoResizeTextarea(el) {
  el.style.height = 'auto';
  el.style.height = Math.max(el.scrollHeight, 30) + 'px';
}

function validatePoints(e) {
  var input = e.target;
  var max = parseFloat(input.getAttribute('data-max-points'));
  var val = parseFloat(input.value);
  if (val < 0) input.value = 0;
  else if (val > max) input.value = max;
  updateScoreProgress(input);
}

function updateScoreProgress(input) {
  var max = parseFloat(input.getAttribute('data-max-points'));
  var val = parseFloat(input.value);
  if (isNaN(val)) val = 0;
  if (isNaN(max)) max = 1;
  var pct = max > 0 ? Math.min((val / max) * 100, 100) : 0;
  var section = input.closest('.grading-section');
  if (!section) return;
  var bar = section.querySelector('.score-visual-bar');
  if (bar) bar.style.width = pct + '%';
  var label = section.querySelector('.score-pct-label');
  if (label) label.textContent = Math.round(pct) + '%';
}

/* ── Feedback chips ────────────────────────────────────────── */

function handleFeedbackChip(e) {
  var chip = e.currentTarget;
  var text = chip.getAttribute('data-text');
  if (!text) return;
  var section = chip.closest('.grading-section');
  if (!section) return;
  var answerId = section.getAttribute('data-answer-id');
  var ta = document.querySelector('.essay-feedback-input[data-answer-id="' + answerId + '"]');
  if (!ta) return;
  var existing = ta.value.trim();
  ta.value = existing ? existing + '\n– ' + text : '– ' + text;
  ta.dispatchEvent(new Event('input', { bubbles: true }));
  chip.classList.add('bg-purple-100', 'border-purple-300', 'text-purple-700');
  chip.classList.remove('bg-white', 'border-gray-200', 'text-gray-600');
}

/* ── Save grade ────────────────────────────────────────────── */

async function handleGradeEssay(event) {
  var button = event.target;
  var answerId = button.getAttribute('data-answer-id');
  var pointsInput = document.querySelector('.essay-points-input[data-answer-id="' + answerId + '"]');
  var feedbackInput = document.querySelector('.essay-feedback-input[data-answer-id="' + answerId + '"]');
  var statusDiv = document.querySelector('.grading-status[data-answer-id="' + answerId + '"]');

  if (!pointsInput) { showError('Points input not found'); return; }

  var pointsEarned = parseFloat(pointsInput.value);
  var teacherFeedback = feedbackInput ? feedbackInput.value.trim() : '';
  var maxPoints = parseFloat(pointsInput.getAttribute('data-max-points'));

  if (isNaN(pointsEarned) || pointsEarned < 0 || pointsEarned > maxPoints) {
    showError('Points must be between 0 and ' + maxPoints);
    return;
  }

  var origHTML = button.innerHTML;
  button.innerHTML = '<svg class="inline-block w-3.5 h-3.5 btn-spinner mr-1" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> Saving...';
  button.disabled = true;

  try {
    var isUpdate = statusDiv && statusDiv.textContent.indexOf('Saved') !== -1;
    var url = isUpdate
      ? '/attempts/teacher/grading/essay/' + answerId + '/update/'
      : '/attempts/teacher/grading/essay/' + answerId + '/grade/';

    var resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
      body: JSON.stringify({ points_earned: pointsEarned, teacher_feedback: teacherFeedback || null })
    });
    var data = await resp.json();

    if (resp.ok && data.success) {
      updateGradingUI(answerId, data);
      showSuccess(data.message);
      updateFinalScore(data.total_score);
      if (typeof data.total_questions === 'number') {
        updateGradingStatusBadge(data.graded_questions || 0, data.total_questions || 0);
      }
      var section = document.querySelector('.grading-section[data-answer-id="' + answerId + '"]');
      if (section) {
        var td = section.querySelector('.teacher-score-display');
        if (td) td.textContent = Number(data.points_earned || 0).toFixed(1);
      }
      button.innerHTML = 'Update Grade';

      var allSections = Array.from(document.querySelectorAll('.grading-section'));
      var curIdx = allSections.findIndex(function(s) { return s.getAttribute('data-answer-id') === answerId; });
      for (var i = curIdx + 1; i < allSections.length; i++) {
        if (allSections[i].getAttribute('data-is-graded') === 'false') {
          allSections[i].scrollIntoView({ behavior: 'smooth', block: 'center' });
          var ni = allSections[i].querySelector('.essay-points-input');
          if (ni) setTimeout(function(el) { el.focus(); }, 600, ni);
          break;
        }
      }
    } else {
      showError(data.error || 'Failed to save grade');
    }
  } catch (err) {
    console.error('Error grading essay:', err);
    showError('An error occurred while saving the grade');
  } finally {
    button.disabled = false;
    if (button.innerHTML.indexOf('Saving') !== -1) button.innerHTML = origHTML;
  }
}

function updateGradingUI(answerId, data) {
  var statusDiv = document.querySelector('.grading-status[data-answer-id="' + answerId + '"]');
  if (statusDiv) {
    var now = new Date();
    var d = now.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true });
    statusDiv.innerHTML = '<span class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-green-50 text-green-700 rounded-full text-xs font-medium border border-green-200">' +
      '<svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>' +
      'Saved ' + d + '</span>';
  }

  var section = document.querySelector('.grading-section[data-answer-id="' + answerId + '"]');
  if (section) {
    section.setAttribute('data-is-graded', 'true');
    var parent = section.closest('.bg-white');
    if (parent) {
      parent.classList.remove('ring-1', 'ring-yellow-300');
      var badge = parent.querySelector('.bg-yellow-50');
      if (badge) {
        var newBadge = document.createElement('span');
        newBadge.className = 'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-200';
        newBadge.innerHTML = '<svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg> Graded: ' + data.points_earned.toFixed(2);
        badge.replaceWith(newBadge);
      }
    }
  }
}

function updateFinalScore(score) {
  document.querySelectorAll('.overall-score').forEach(function(el) {
    el.textContent = score.toFixed(2) + ' pts';
  });
}

/* ── CSRF, notifications ───────────────────────────────────── */

function getCsrfToken() { return CookieUtils.getCSRFToken(); }
function showSuccess(msg) { NotificationManager.success(msg, 3000); }
function showError(msg) { NotificationManager.error(msg, 3000); }

/* ── Fetch AI grade ────────────────────────────────────────── */

async function fetchAiGrade(answerId, url) {
  var resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
    body: JSON.stringify({})
  });
  var raw = await resp.text();
  var data = null;
  try { data = raw ? JSON.parse(raw) : null; } catch (e) {}
  if (!resp.ok || !data || !data.success) {
    throw new Error((data && data.error) || 'AI grading failed (HTTP ' + resp.status + ')');
  }
  return data;
}

function populateAiGradeResult(answerId, data) {
  var section = document.querySelector('.grading-section[data-answer-id="' + answerId + '"]');
  if (!section) return;

  var pointsInput = section.querySelector('.essay-points-input');
  var feedbackInput = section.querySelector('.essay-feedback-input');

  if (pointsInput) {
    pointsInput.value = data.points_earned;
    pointsInput.dispatchEvent(new Event('input', { bubbles: true }));
    pointsInput.dispatchEvent(new Event('change', { bubbles: true }));
    updateScoreProgress(pointsInput);
  }
  if (feedbackInput && data.feedback) {
    feedbackInput.value = data.feedback;
    feedbackInput.dispatchEvent(new Event('input', { bubbles: true }));
  }

  /* Hide placeholder (and primary assess btn), show results */
  var placeholder = section.querySelector('.ai-eval-placeholder');
  var results = section.querySelector('.ai-eval-results');
  if (placeholder) placeholder.classList.add('hidden');
  if (results) results.classList.remove('hidden');

  /* Grade Summary bar score */
  var aiScoreEl = section.querySelector('.ai-suggested-score');
  if (aiScoreEl) {
    aiScoreEl.textContent = Number(data.points_earned || 0).toFixed(1);
  }

  /* Score Hero */
  var heroEl = section.querySelector('.ai-suggested-score-hero');
  if (heroEl) {
    heroEl.textContent = Number(data.points_earned || 0).toFixed(1);
  }

  /* SVG Ring: animate stroke-dashoffset to show score proportion */
  var ringFg = section.querySelector('.ai-score-ring .ring-fg');
  var maxPts = pointsInput ? parseFloat(pointsInput.getAttribute('data-max-points')) : 1;
  var pct = maxPts > 0 ? Math.min(Number(data.points_earned || 0) / maxPts, 1) : 0;
  var circumference = 188.5;
  if (ringFg) {
    var offset = circumference - (circumference * pct);
    ringFg.setAttribute('stroke-dashoffset', offset);
  }

  /* Confidence Badge */
  var confidence = data.confidence || data.confidence_score;
  var confWrap = section.querySelector('.ai-confidence-badge-wrap');
  if (confWrap) {
    if (confidence != null) {
      confWrap.classList.remove('hidden');
      var pct = Math.round(confidence * 100);
      var dot = confWrap.querySelector('.ai-confidence-dot');
      var pctEl = confWrap.querySelector('.ai-confidence-pct');
      if (dot) {
        dot.className = 'w-2 h-2 rounded-full ai-confidence-dot ' +
          (pct >= 80 ? 'bg-green-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-red-500');
      }
      if (pctEl) pctEl.textContent = pct + '%';
    } else {
      confWrap.classList.add('hidden');
    }
  }

  /* Rubric bars with visual chart */
  var bd = data.breakdown || {};
  var rubricKeys = ['relevance', 'correctness', 'depth', 'critical_thinking', 'writing_quality'];
  var rubricLabels = { relevance: 'Rel', correctness: 'Cor', depth: 'Dep', critical_thinking: 'CT', writing_quality: 'WQ' };
  var rubricColors = { relevance: 'bg-violet-400', correctness: 'bg-blue-400', depth: 'bg-emerald-400', critical_thinking: 'bg-amber-400', writing_quality: 'bg-rose-400' };
  var hasRubric = rubricKeys.some(function(k) { return bd[k] != null; });

  var rubricWrap = section.querySelector('.ai-rubric');
  var cardsEl = section.querySelector('.ai-rubric-cards');
  if (rubricWrap && cardsEl) {
    if (hasRubric) {
      rubricWrap.classList.remove('hidden');
      cardsEl.innerHTML = '';
      rubricKeys.forEach(function(key) {
        var val = bd[key];
        if (val == null) return;
        var maxRubric = 10;
        var barPct = Math.min(val / maxRubric * 100, 100);
        var row = document.createElement('div');
        row.className = 'flex items-center gap-2';
        row.innerHTML = '<span class="text-[11px] font-medium text-gray-600 w-6 shrink-0">' + rubricLabels[key] + '</span>' +
          '<div class="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">' +
          '<div class="h-full rounded-full ' + (rubricColors[key] || 'bg-purple-400') + ' transition-all duration-500" style="width:' + barPct + '%"></div></div>' +
          '<span class="text-[11px] font-bold text-gray-700 w-8 text-right shrink-0">' + val.toFixed(1) + '</span>';
        cardsEl.appendChild(row);
      });
    } else {
      rubricWrap.classList.add('hidden');
    }
  }

  /* Reasoning Callout */
  if (data.reasoning) {
    var reasoningEl = section.querySelector('.ai-reasoning');
    var reasoningText = section.querySelector('.ai-reasoning-text');
    if (reasoningEl) reasoningEl.classList.remove('hidden');
    if (reasoningText) reasoningText.textContent = data.reasoning;
  }

  /* Update results assess button label to "Re-assess" */
  var resultsAssessBtn = section.querySelector('.ai-eval-results .ai-grade-essay-btn');
  if (resultsAssessBtn) {
    var label = resultsAssessBtn.querySelector('.ai-grade-label');
    if (label) label.textContent = 'Re-assess';
  }
}

function showAiGradeOverlay() {
  var overlay = document.getElementById('aiGradeOverlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'aiGradeOverlay';
    overlay.innerHTML =
      '<div style="position:fixed;inset:0;background:rgba(255,255,255,0.85);z-index:9999;display:flex;align-items:center;justify-content:center;">' +
        '<div style="background:#ffffff;border-radius:16px;padding:2.5rem;text-align:center;max-width:400px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,0.15);border:1px solid #e2e8f0;">' +
          '<div style="width:48px;height:48px;border:4px solid #e2e8f0;border-top-color:#8b5cf6;border-radius:50%;animation:aiGradeSpin 0.8s linear infinite;margin:0 auto 1.25rem;"></div>' +
          '<h3 style="color:#1e293b;font-size:1.125rem;font-weight:600;margin-bottom:0.5rem;">Assessing Essay with AI...</h3>' +
          '<p style="color:#64748b;font-size:0.8125rem;margin:0 0 1rem;">Analyzing content against rubric criteria. This may take up to 30 seconds.</p>' +
          '<div style="width:100%;height:6px;background:#e2e8f0;border-radius:3px;overflow:hidden;">' +
            '<div id="aiGradeProgressBar" style="width:0%;height:100%;background:linear-gradient(90deg,#8b5cf6,#3b82f6);border-radius:3px;transition:width 0.5s ease;"></div>' +
          '</div>' +
          '<p id="aiGradeProgressText" style="color:#94a3b8;font-size:0.75rem;margin-top:0.5rem;">Starting...</p>' +
        '</div>' +
      '</div>' +
      '<style>@keyframes aiGradeSpin{to{transform:rotate(360deg)}}</style>';
    document.body.appendChild(overlay);
  }
  overlay.style.display = '';
  var bar = document.getElementById('aiGradeProgressBar');
  var text = document.getElementById('aiGradeProgressText');
  if (bar) bar.style.width = '0%';
  if (text) text.textContent = 'Starting...';
}

function hideAiGradeOverlay() {
  var overlay = document.getElementById('aiGradeOverlay');
  if (overlay) overlay.style.display = 'none';
}

var aiGradeProgressInterval = null;

function startAiGradeProgress() {
  var progress = 0;
  var messages = ['Connecting to AI...', 'Reading essay content...', 'Evaluating rubric criteria...', 'Calculating scores...', 'Generating feedback...', 'Finalizing assessment...'];
  aiGradeProgressInterval = setInterval(function() {
    progress = Math.min(progress + Math.random() * 8 + 2, 90);
    var bar = document.getElementById('aiGradeProgressBar');
    var text = document.getElementById('aiGradeProgressText');
    if (bar) bar.style.width = progress + '%';
    if (text) text.textContent = messages[Math.min(Math.floor(progress / 16), messages.length - 1)];
  }, 1500);
}

function stopAiGradeProgress(done) {
  if (aiGradeProgressInterval) {
    clearInterval(aiGradeProgressInterval);
    aiGradeProgressInterval = null;
  }
  var bar = document.getElementById('aiGradeProgressBar');
  var text = document.getElementById('aiGradeProgressText');
  if (bar) bar.style.width = done ? '100%' : '0%';
  if (text) text.textContent = done ? 'Done!' : 'Failed';
}

async function handleAiGradeEssay(event) {
  var button = event.currentTarget;
  var answerId = button.getAttribute('data-answer-id');
  var url = button.getAttribute('data-ai-grade-url');
  if (!url) { showError('AI grade URL not configured.'); return; }

  showAiGradeOverlay();
  startAiGradeProgress();

  try {
    var data = await fetchAiGrade(answerId, url);
    stopAiGradeProgress(true);
    setTimeout(function() { hideAiGradeOverlay(); }, 600);
    populateAiGradeResult(answerId, data);
    var pts = Number(data.points_earned || 0).toFixed(2);
    var max = Number(data.max_points || 0).toFixed(2);
    if (window.NotificationManager) {
      NotificationManager.success('AI suggested ' + pts + ' / ' + max + '. Review and save.', 3500);
    }
  } catch (err) {
    console.error('AI grade error:', err);
    stopAiGradeProgress(false);
    hideAiGradeOverlay();
    showError(err.message || 'Network error. Could not reach AI service.');
  }
}

/* ── Modal helpers ─────────────────────────────────────────── */

function showBatchModal(title) {
  var modal = document.getElementById('batchActionModal');
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
  var pct = total > 0 ? Math.round((current / total) * 100) : 0;
  var bar = document.getElementById('batchModalBar');
  var pctEl = document.getElementById('batchModalPercent');
  var statusEl = document.getElementById('batchModalStatus');
  var subEl = document.getElementById('batchModalSubtext');
  if (bar) bar.style.width = pct + '%';
  if (pctEl) pctEl.textContent = pct + '%';
  if (statusEl) statusEl.textContent = statusText || (current + ' of ' + total);
  if (subEl) subEl.textContent = subText || '';
}

function showBatchModalResult(successCount, failCount) {
  document.getElementById('batchModalLoading').classList.add('hidden');
  var resultDiv = document.getElementById('batchModalResult');
  var iconWrap = document.getElementById('batchModalIconWrap');
  var icon = document.getElementById('batchModalIcon');
  var titleEl = document.getElementById('batchModalResultTitle');
  var detailEl = document.getElementById('batchModalResultDetail');
  var closeBtn = document.getElementById('batchModalCloseBtn');

  var total = successCount + failCount;
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
  closeBtn.onclick = function() {
    document.getElementById('batchActionModal').classList.add('hidden');
    var firstGraded = document.querySelector('[data-is-graded="true"]');
    if (firstGraded) firstGraded.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  if (total > 0) {
    document.querySelectorAll('.batch-action-btn').forEach(function(b) { b.disabled = false; b.style.opacity = ''; b.style.cursor = ''; });
    refreshGradingStats();
  }
}

/* ── Grade all ─────────────────────────────────────────────── */

function showBatchGradeOverlay(total) {
  var overlay = document.getElementById('aiGradeOverlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'aiGradeOverlay';
    document.body.appendChild(overlay);
  }
  overlay.innerHTML =
    '<div style="position:fixed;inset:0;background:rgba(255,255,255,0.85);z-index:9999;display:flex;align-items:center;justify-content:center;">' +
      '<div style="background:#ffffff;border-radius:16px;padding:2.5rem;text-align:center;max-width:400px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,0.15);border:1px solid #e2e8f0;">' +
        '<div style="width:48px;height:48px;border:4px solid #e2e8f0;border-top-color:#8b5cf6;border-radius:50%;animation:aiGradeSpin 0.8s linear infinite;margin:0 auto 1.25rem;"></div>' +
        '<h3 style="color:#1e293b;font-size:1.125rem;font-weight:600;margin-bottom:0.5rem;">Batch Grading ' + total + ' Essays</h3>' +
        '<p style="color:#64748b;font-size:0.8125rem;margin:0 0 1rem;">Grading all ungraded essays with AI. This may take a moment.</p>' +
        '<div style="width:100%;height:6px;background:#e2e8f0;border-radius:3px;overflow:hidden;">' +
          '<div id="aiGradeProgressBar" style="width:0%;height:100%;background:linear-gradient(90deg,#8b5cf6,#3b82f6);border-radius:3px;transition:width 0.5s ease;"></div>' +
        '</div>' +
        '<p id="aiGradeProgressText" style="color:#94a3b8;font-size:0.75rem;margin-top:0.5rem;">Starting...</p>' +
      '</div>' +
    '</div>';
  overlay.style.display = '';
  var bar = document.getElementById('aiGradeProgressBar');
  var text = document.getElementById('aiGradeProgressText');
  if (bar) bar.style.width = '0%';
  if (text) text.textContent = 'Starting...';
}

async function handleBatchAiGrade(event) {
  var button = event.target.closest('#batch-ai-grade-btn');
  if (!button) return;
  var sections = document.querySelectorAll('.grading-section');
  var ungraded = Array.from(sections).filter(function(s) { return s.getAttribute('data-is-graded') === 'false'; });
  if (ungraded.length === 0) { showError('No ungraded essays to grade.'); return; }

  var total = ungraded.length;
  showBatchGradeOverlay(total);
  startAiGradeProgress();

  var completed = 0, failed = [];

  for (var idx = 0; idx < ungraded.length; idx++) {
    var section = ungraded[idx];
    var answerId = section.getAttribute('data-answer-id');
    var aiBtn = section.querySelector('.ai-grade-essay-btn');
    var url = aiBtn ? aiBtn.getAttribute('data-ai-grade-url') : null;

    var pct = Math.round((completed / total) * 100);
    var bar = document.getElementById('aiGradeProgressBar');
    var text = document.getElementById('aiGradeProgressText');
    if (bar) bar.style.width = pct + '%';
    if (text) text.textContent = 'Grading ' + (completed + 1) + ' of ' + total + '...';

    if (!url) { failed.push({ id: answerId, error: 'No AI grade URL' }); completed++; continue; }

    try {
      var data = await fetchAiGrade(answerId, url);
      populateAiGradeResult(answerId, data);
    } catch (err) {
      console.error('AI grade error for answer ' + answerId + ':', err);
      failed.push({ id: answerId, error: err.message });
    }
    completed++;
  }

  stopAiGradeProgress(true);
  var bar2 = document.getElementById('aiGradeProgressBar');
  var text2 = document.getElementById('aiGradeProgressText');
  if (bar2) bar2.style.width = '100%';
  if (text2) text2.textContent = failed.length === 0 ? 'All ' + total + ' complete!' : (completed - failed.length) + ' of ' + total + ' complete';
  setTimeout(function() { hideAiGradeOverlay(); }, 1500);
  if (failed.length === 0) {
    NotificationManager.success('All ' + total + ' essays graded.', 3000);
  } else {
    NotificationManager.error(failed.length + ' of ' + total + ' failed.', 4000);
  }
  refreshGradingStats();
}

/* ── Save all ──────────────────────────────────────────────── */

async function handleSaveAllGrades(event) {
  var button = event.target.closest('#save-all-grades-btn');
  if (!button) return;
  var sections = document.querySelectorAll('.grading-section');
  var ungraded = Array.from(sections).filter(function(s) { return s.getAttribute('data-is-graded') === 'false'; });
  if (ungraded.length === 0) { showError('No ungraded essays to save.'); return; }

  if (ungraded.length > 5 && !confirm('Save grades for ' + ungraded.length + ' ungraded essays? Make sure you have reviewed each one.')) return;

  showBatchModal('Saving Grades');
  document.getElementById('batchModalStatus').textContent = 'Preparing...';
  document.getElementById('batchModalHeader').className = 'px-6 py-5 bg-gradient-to-r from-emerald-600 to-green-600 text-white flex items-center gap-3';
  document.getElementById('batchModalBar').className = 'h-full bg-gradient-to-r from-emerald-500 to-green-500 rounded-full transition-all duration-300';

  var origHTML = button.innerHTML;
  button.innerHTML = '<svg class="inline-block w-4 h-4 btn-spinner mr-1.5" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> Saving...';
  button.disabled = true;
  button.style.opacity = '0.7';
  button.style.cursor = 'wait';

  await new Promise(function(r) { setTimeout(r, 100); });

  var completed = 0, failed = [], total = ungraded.length;

  for (var idx = 0; idx < ungraded.length; idx++) {
    var section = ungraded[idx];
    var answerId = section.getAttribute('data-answer-id');
    var pointsInput = document.querySelector('.essay-points-input[data-answer-id="' + answerId + '"]');
    var feedbackInput = document.querySelector('.essay-feedback-input[data-answer-id="' + answerId + '"]');

    if (!pointsInput) { failed.push({ id: answerId, error: 'Input not found' }); completed++; updateBatchModal(completed, total); continue; }

    var pointsEarned = parseFloat(pointsInput.value);
    var teacherFeedback = feedbackInput ? feedbackInput.value.trim() : '';
    var maxPoints = parseFloat(pointsInput.getAttribute('data-max-points'));

    if (isNaN(pointsEarned) || pointsEarned < 0 || pointsEarned > maxPoints) {
      failed.push({ id: answerId, error: 'Invalid points' }); completed++; updateBatchModal(completed, total); continue;
    }

    updateBatchModal(completed, total, 'Saving ' + (completed + 1) + ' of ' + total);

    try {
      var resp = await fetch('/attempts/teacher/grading/essay/' + answerId + '/grade/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify({ points_earned: pointsEarned, teacher_feedback: teacherFeedback || null })
      });
      var data = await resp.json();
      if (resp.ok && data.success) {
        updateGradingUI(answerId, data);
        updateFinalScore(data.total_score);
        var sec = document.querySelector('.grading-section[data-answer-id="' + answerId + '"]');
        if (sec) {
          var td = sec.querySelector('.teacher-score-display');
          if (td) td.textContent = Number(data.points_earned || 0).toFixed(1);
        }
      } else {
        failed.push({ id: answerId, error: data.error || 'Save failed' });
      }
    } catch (err) {
      console.error('Save error for answer ' + answerId + ':', err);
      failed.push({ id: answerId, error: err.message });
    }
    completed++;
  }

  updateBatchModal(completed, total, 'Finalising...');
  await new Promise(function(r) { setTimeout(r, 300); });
  button.innerHTML = origHTML;
  showBatchModalResult(completed - failed.length, failed.length);
}

/* ── Refresh summary ───────────────────────────────────────── */

function refreshGradingStats() {
  var graded = 0, ungraded = 0;
  document.querySelectorAll('.grading-section').forEach(function(s) {
    if (s.getAttribute('data-is-graded') === 'true') graded++; else ungraded++;
  });
  var total = graded + ungraded;

  var ttl = document.getElementById('summary-graded');
  var ung = document.getElementById('summary-ungraded');
  var scr = document.getElementById('summary-score');
  var batchBar = document.getElementById('batch-ai-bar');

  if (ttl) ttl.textContent = graded;
  if (ung) {
    ung.textContent = ungraded;
    if (ungraded === 0 && batchBar) batchBar.remove();
  }

  updateGradingStatusBadge(graded, total);
}

/* ── Update header status badge ─────────────────────────────── */

var STATUS_BADGE_CLASSES = {
  graded:   { wrap: 'bg-emerald-100 text-emerald-700 border-2 border-emerald-300', dot: 'bg-emerald-500',   label: 'Graded' },
  partial:  { wrap: 'bg-blue-100 text-blue-700 border-2 border-blue-300',           dot: 'bg-blue-500',      label: 'Partial' },
  awaiting: { wrap: 'bg-amber-100 text-amber-700 border-2 border-amber-300',        dot: 'bg-amber-500',     label: 'Awaiting Review' },
};

function updateGradingStatusBadge(graded, total) {
  var badge = document.getElementById('grading-status-badge');
  if (!badge) return;

  var state;
  if (total <= 0) {
    state = 'awaiting';
  } else if (graded >= total) {
    state = 'graded';
  } else if (graded <= 0) {
    state = 'awaiting';
  } else {
    state = 'partial';
  }

  var classes = STATUS_BADGE_CLASSES[state];
  var wrap = badge.className.split(' ').filter(function(c) {
    return !/^bg-(emerald|blue|amber)-100$/.test(c)
      && !/^text-(emerald|blue|amber)-700$/.test(c)
      && !/^border-2$/.test(c)
      && !/^border-(emerald|blue|amber)-300$/.test(c);
  }).concat(classes.wrap.split(' ')).join(' ');
  badge.className = wrap;

  var dot = badge.querySelector('.grading-status-dot');
  if (dot) {
    dot.className = 'grading-status-dot w-2 h-2 rounded-full animate-pulse ' + classes.dot;
  }

  var label = badge.querySelector('.grading-status-label');
  if (label) label.textContent = classes.label;

  badge.setAttribute('data-graded', graded);
  badge.setAttribute('data-total', total);
}
