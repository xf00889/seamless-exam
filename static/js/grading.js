document.addEventListener('DOMContentLoaded', function() {
  initializeGrading();
});

function initializeGrading() {
  document.querySelectorAll('.grade-essay-btn').forEach(function(b) {
    b.addEventListener('click', handleGradeEssay);
  });
  document.querySelectorAll('.essay-points-input').forEach(function(i) {
    i.addEventListener('input', validatePoints);
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
  document.querySelectorAll('.apply-ai-score-btn').forEach(function(b) {
    b.addEventListener('click', handleApplyAiScore);
  });
}

function autoResizeTextarea(el) {
  el.style.height = 'auto';
  el.style.height = Math.max(el.scrollHeight, 72) + 'px';
}

function validatePoints(e) {
  var input = e.target;
  var max = parseFloat(input.getAttribute('data-max-points'));
  var val = parseFloat(input.value);
  if (val < 0) input.value = 0;
  else if (val > max) input.value = max;
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

/* ── Apply AI Score ────────────────────────────────────────── */

function handleApplyAiScore(e) {
  var btn = e.currentTarget;
  var section = btn.closest('.grading-section');
  if (!section) return;
  var answerId = section.getAttribute('data-answer-id');
  var aiScore = section.querySelector('.ai-suggested-score');
  if (!aiScore) return;
  var score = parseFloat(aiScore.textContent);
  if (isNaN(score)) return;
  var input = document.querySelector('.essay-points-input[data-answer-id="' + answerId + '"]');
  if (!input) return;
  var max = parseFloat(input.getAttribute('data-max-points'));
  input.value = Math.min(score, max);
  input.dispatchEvent(new Event('input', { bubbles: true }));
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
  button.innerHTML = '<svg class="inline-block w-3.5 h-3.5 animate-spin mr-1" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> Saving...';
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
  var el = document.getElementById('final-score');
  if (el) el.innerHTML = score.toFixed(2) + ' <span class="text-lg font-normal text-gray-400">pts</span>';
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
  }
  if (feedbackInput && data.feedback) {
    feedbackInput.value = data.feedback;
    feedbackInput.dispatchEvent(new Event('input', { bubbles: true }));
  }

  /* Show results panel, hide placeholder */
  var placeholder = section.querySelector('.ai-eval-placeholder');
  var results = section.querySelector('.ai-eval-results');
  if (placeholder) placeholder.classList.add('hidden');
  if (results) results.classList.remove('hidden');

  /* Score */
  var scoreEl = section.querySelector('.ai-suggested-score');
  if (scoreEl) {
    var pts = Number(data.points_earned || 0).toFixed(1);
    scoreEl.textContent = pts;
  }

  /* Timestamp */
  var tsEl = section.querySelector('.ai-eval-timestamp');
  if (tsEl) {
    var now = new Date();
    tsEl.textContent = now.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  }

  /* Confidence */
  var confidence = data.confidence || data.confidence_score;
  if (confidence != null) {
    var confWrap = section.querySelector('.ai-confidence-wrap');
    var confBar = section.querySelector('.ai-confidence-bar');
    var confLabel = section.querySelector('.ai-confidence-label');
    if (confWrap) confWrap.classList.remove('hidden');
    var pct = Math.round(confidence * 100);
    if (confBar) {
      confBar.style.width = pct + '%';
      confBar.className = 'ai-confidence-bar h-full rounded-full transition-all duration-700 ease-out ' +
        (pct >= 80 ? 'bg-green-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-orange-500');
    }
    if (confLabel) confLabel.textContent = pct + '%';
  }

  /* Rubric */
  var bd = data.breakdown || {};
  var rubricKeys = ['relevance', 'correctness', 'depth', 'critical_thinking', 'writing_quality'];
  var rubricLabels = { relevance: 'Relevance', correctness: 'Correctness', depth: 'Depth', critical_thinking: 'Critical Thinking', writing_quality: 'Writing Quality' };
  var hasRubric = rubricKeys.some(function(k) { return bd[k] != null; });

  if (hasRubric) {
    var rubricEl = section.querySelector('.ai-rubric');
    var barsEl = section.querySelector('.ai-rubric-bars');
    if (rubricEl) rubricEl.classList.remove('hidden');
    if (barsEl) {
      barsEl.innerHTML = '';
      rubricKeys.forEach(function(key) {
        var val = bd[key];
        if (val == null) return;
        var pct = (val / 10) * 100;
        var label = rubricLabels[key] || key;
        var div = document.createElement('div');
        div.className = 'space-y-0.5';
        div.innerHTML =
          '<div class="flex justify-between text-xs">' +
          '  <span class="text-gray-600">' + label + '</span>' +
          '  <span class="font-medium text-gray-800">' + val.toFixed(1) + '/10</span>' +
          '</div>' +
          '<div class="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">' +
          '  <div class="h-full rounded-full transition-all duration-500 bg-purple-500" style="width:' + pct + '%"></div>' +
          '</div>';
        barsEl.appendChild(div);
      });
    }
  }

  /* Reasoning */
  if (data.reasoning) {
    var reasoningEl = section.querySelector('.ai-reasoning');
    var reasoningText = section.querySelector('.ai-reasoning-text');
    if (reasoningEl) reasoningEl.classList.remove('hidden');
    if (reasoningText) reasoningText.textContent = data.reasoning;
  }

  /* Show Apply button */
  var applyBtn = section.querySelector('.apply-ai-score-btn');
  if (applyBtn) applyBtn.classList.remove('hidden');

  /* Change assess button to "Reassess" */
  var assessBtn = section.querySelector('.ai-grade-essay-btn');
  if (assessBtn) {
    var label = assessBtn.querySelector('.ai-grade-label');
    if (label) label.textContent = 'Re-assess';
  }
}

async function handleAiGradeEssay(event) {
  var button = event.currentTarget;
  var answerId = button.getAttribute('data-answer-id');
  var url = button.getAttribute('data-ai-grade-url');
  if (!url) { showError('AI grade URL not configured.'); return; }

  var origHTML = button.innerHTML;
  button.innerHTML = '<svg class="inline-block w-4 h-4 animate-spin mr-1" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> Assessing...';
  button.disabled = true;

  try {
    var data = await fetchAiGrade(answerId, url);
    populateAiGradeResult(answerId, data);
    var pts = Number(data.points_earned || 0).toFixed(2);
    var max = Number(data.max_points || 0).toFixed(2);
    if (window.NotificationManager) {
      NotificationManager.success('AI suggested ' + pts + ' / ' + max + '. Review and save.', 3500);
    }
  } catch (err) {
    console.error('AI grade error:', err);
    showError(err.message || 'Network error. Could not reach AI service.');
  } finally {
    button.disabled = false;
    button.innerHTML = origHTML;
    var label = button.querySelector('.ai-grade-label');
    if (label) label.textContent = 'Re-assess';
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

async function handleBatchAiGrade(event) {
  var button = event.target.closest('#batch-ai-grade-btn');
  if (!button) return;
  var sections = document.querySelectorAll('.grading-section');
  var ungraded = Array.from(sections).filter(function(s) { return s.getAttribute('data-is-graded') === 'false'; });
  if (ungraded.length === 0) { showError('No ungraded essays to grade.'); return; }

  showBatchModal('Grading Essays');
  document.getElementById('batchModalStatus').textContent = 'Preparing...';

  var origHTML = button.innerHTML;
  button.innerHTML = '<svg class="inline-block w-4 h-4 animate-spin mr-1.5" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> Grading...';
  button.disabled = true;
  button.style.opacity = '0.7';
  button.style.cursor = 'wait';

  await new Promise(function(r) { setTimeout(r, 100); });

  var completed = 0, failed = [], total = ungraded.length;

  for (var idx = 0; idx < ungraded.length; idx++) {
    var section = ungraded[idx];
    var answerId = section.getAttribute('data-answer-id');
    var aiBtn = section.querySelector('.ai-grade-essay-btn');
    var url = aiBtn ? aiBtn.getAttribute('data-ai-grade-url') : null;

    updateBatchModal(completed, total, 'Grading essay ' + (completed + 1) + ' of ' + total);

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

  updateBatchModal(completed, total, 'Finalising...');
  await new Promise(function(r) { setTimeout(r, 300); });
  button.innerHTML = origHTML;
  showBatchModalResult(completed - failed.length, failed.length);
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
  button.innerHTML = '<svg class="inline-block w-4 h-4 animate-spin mr-1.5" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> Saving...';
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
}
