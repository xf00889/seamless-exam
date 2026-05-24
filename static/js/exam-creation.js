/**
 * Simple Exam Creation Form Navigation
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const nextBtn = document.getElementById('nextBtn');
    const prevBtn = document.getElementById('prevBtn');
    const submitBtn = document.getElementById('submitBtn');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const uploadSection = document.getElementById('uploadSection');

    let currentStep = 1;
    const totalSteps = 4;
    let aiGenerationComplete = false;
    let aiGeneratedExamId = null;

    function showStep(step) {
        if (step < 1 || step > totalSteps) return;

        document.querySelectorAll('.form-step').forEach(el => {
            el.classList.add('hidden');
        });

        const stepEl = document.getElementById('step' + step);
        if (stepEl) {
            stepEl.classList.remove('hidden');
        }

        const percentage = (step / totalSteps) * 100;
        progressBar.style.width = percentage + '%';
        progressText.textContent = 'Step ' + step + ' of ' + totalSteps;

        updateStepIndicators(step);
        updateButtons(step);

        if (step === 3) {
            updateMethodOptions();
        } else if (step === 4) {
            updateSummary();
        }
    }

    function updateButtons(step) {
        nextBtn.classList.add('hidden');
        prevBtn.classList.add('hidden');
        submitBtn.classList.add('hidden');

        if (step === 1) {
            nextBtn.classList.remove('hidden');
        } else if (step === totalSteps) {
            prevBtn.classList.remove('hidden');
            submitBtn.classList.remove('hidden');
            if (aiGenerationComplete) {
                submitBtn.textContent = 'Go to Exam Editor';
                submitBtn.innerHTML = '<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>Go to Exam Editor';
            }
        } else {
            nextBtn.classList.remove('hidden');
            prevBtn.classList.remove('hidden');
        }
    }

    function updateStepIndicators(step) {
        document.querySelectorAll('.step-indicator').forEach(function(el, index) {
            var stepNum = index + 1;
            var circle = el.querySelector('div');
            var text = el.querySelector('p');
            var checkmark = el.querySelector('.step-check');

            if (stepNum < step) {
                circle.className = 'w-10 h-10 rounded-full bg-green-600 text-white text-sm font-bold flex items-center justify-center mx-auto shadow-md transition-all duration-300';
                text.className = 'text-sm font-medium text-green-600 mb-1';
                if (checkmark) checkmark.classList.remove('hidden');
                el.classList.add('active');
            } else if (stepNum === step) {
                circle.className = 'w-10 h-10 rounded-full bg-blue-600 text-white text-sm font-bold flex items-center justify-center mx-auto shadow-md transition-all duration-300';
                text.className = 'text-sm font-medium text-blue-600 mb-1';
                if (checkmark) checkmark.classList.add('hidden');
                el.classList.add('active');
            } else {
                circle.className = 'w-10 h-10 rounded-full bg-gray-300 text-white text-sm font-bold flex items-center justify-center mx-auto shadow-md transition-all duration-300';
                text.className = 'text-sm font-medium text-gray-500 mb-1';
                if (checkmark) checkmark.classList.add('hidden');
                el.classList.remove('active');
            }
        });
    }

    function updateMethodOptions() {
        var methodInputs = document.querySelectorAll('input[name="generation_method"]');
        var aiSection = document.getElementById('aiSection');

        methodInputs.forEach(function(input) {
            input.addEventListener('change', function() {
                if (this.value === 'upload') {
                    uploadSection.classList.remove('hidden');
                    if (aiSection) aiSection.classList.add('hidden');
                } else if (this.value === 'ai_generate') {
                    if (aiSection) aiSection.classList.remove('hidden');
                    uploadSection.classList.add('hidden');
                } else {
                    uploadSection.classList.add('hidden');
                    if (aiSection) aiSection.classList.add('hidden');
                }
            });
        });

        var selectedMethod = document.querySelector('input[name="generation_method"]:checked');
        if (selectedMethod && selectedMethod.value === 'upload') {
            uploadSection.classList.remove('hidden');
        } else if (selectedMethod && selectedMethod.value === 'ai_generate') {
            if (aiSection) aiSection.classList.remove('hidden');
        }
    }

    function updateSummary() {
        var title = document.getElementById('title').value || 'Not specified';
        var subject = document.getElementById('subject').value || 'Not specified';
        var duration = document.getElementById('duration_minutes').value;
        var method = document.querySelector('input[name="generation_method"]:checked');
        var classes = document.querySelectorAll('input[name="assigned_classes"]:checked');

        document.getElementById('summary-title').textContent = title;
        document.getElementById('summary-subject').textContent = subject;
        document.getElementById('summary-duration').textContent = duration ? duration + ' minutes' : 'Not specified';

        var methodText = 'Manual Entry';
        if (method) {
            if (method.value === 'ai_generate') methodText = 'AI Generate';
            else if (method.value === 'upload') methodText = 'File Upload';
        }
        document.getElementById('summary-method').textContent = methodText;
        document.getElementById('summary-classes').textContent = classes.length > 0 ? classes.length + ' selected' : 'None selected';
    }

    function validateStep(step) {
        if (step === 1) {
            var title = document.getElementById('title').value.trim();
            var duration = document.getElementById('duration_minutes').value;

            if (!title) {
                document.getElementById('title').focus();
                return false;
            }
            if (!duration || duration < 1) {
                document.getElementById('duration_minutes').focus();
                return false;
            }
        }
        return true;
    }

    function getSelectedMethod() {
        var el = document.querySelector('input[name="generation_method"]:checked');
        return el ? el.value : 'manual';
    }

    function showAiOverlay() {
        var overlay = document.getElementById('aiCreateOverlay');
        if (overlay) overlay.style.display = 'flex';
        animateProgress();
    }

    function hideAiOverlay() {
        var overlay = document.getElementById('aiCreateOverlay');
        if (overlay) overlay.style.display = 'none';
    }

    function animateProgress() {
        var bar = document.getElementById('aiProgressBar');
        var text = document.getElementById('aiProgressText');
        if (!bar) return;

        var progress = 0;
        var messages = ['Starting...', 'Connecting to AI...', 'Generating questions...', 'Processing responses...', 'Almost done...'];
        var interval = setInterval(function() {
            progress += Math.random() * 8 + 2;
            if (progress > 90) progress = 90;
            bar.style.width = progress + '%';
            var msgIdx = Math.min(Math.floor(progress / 20), messages.length - 1);
            if (text) text.textContent = messages[msgIdx];
        }, 1000);

        window._aiProgressInterval = interval;
    }

    function completeProgress() {
        if (window._aiProgressInterval) clearInterval(window._aiProgressInterval);
        var bar = document.getElementById('aiProgressBar');
        var text = document.getElementById('aiProgressText');
        if (bar) bar.style.width = '100%';
        if (text) text.textContent = 'Complete!';
    }

    async function handleAiGeneration() {
        var topic = document.getElementById('ai_topic').value.trim();
        var typeCounts = {};
        ['MCQ', 'TRUE_FALSE', 'IDENTIFICATION', 'ENUMERATION', 'ESSAY'].forEach(function(qt) {
            var el = document.getElementById('ai_count_' + qt);
            var count = el ? parseInt(el.value) || 0 : 0;
            if (count > 0) typeCounts[qt] = count;
        });

        if (!topic) {
            alert('Please enter at least one topic.');
            return false;
        }
        if (Object.keys(typeCounts).length === 0) {
            alert('Please set at least one question type count greater than 0.');
            return false;
        }

        showAiOverlay();

        var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        var formData = new FormData(document.getElementById('examForm'));
        formData.set('generation_method', 'ai_generate');

        try {
            var response = await fetch(document.getElementById('examForm').action, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: formData,
            });

            var data = await response.json();
            completeProgress();

            if (data.success) {
                aiGenerationComplete = true;
                aiGeneratedExamId = data.exam_id;

                setTimeout(function() {
                    hideAiOverlay();
                    showAiResults(data);
                    currentStep = 4;
                    showStep(4);
                }, 600);
                return true;
            } else {
                hideAiOverlay();
                alert(data.error || 'AI generation failed. Please try again.');
                return false;
            }
        } catch (err) {
            completeProgress();
            setTimeout(function() {
                hideAiOverlay();
                alert('Network error. Please try again.');
            }, 500);
            return false;
        }
    }

    function showAiResults(data) {
        var summaryEl = document.querySelector('#step4 .bg-gradient-to-br');
        if (!summaryEl) return;

        var aiResultsDiv = document.getElementById('aiResultsSummary');
        if (!aiResultsDiv) {
            aiResultsDiv = document.createElement('div');
            aiResultsDiv.id = 'aiResultsSummary';
            aiResultsDiv.className = 'mt-6 p-5 bg-green-50 border border-green-200 rounded-xl';
            summaryEl.appendChild(aiResultsDiv);
        }

        var questionsHtml = '';
        if (data.questions_by_type) {
            Object.keys(data.questions_by_type).forEach(function(type) {
                questionsHtml += '<span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-white border border-green-300 text-green-700 mr-2 mb-2">' + type + ': ' + data.questions_by_type[type] + '</span>';
            });
        }

        aiResultsDiv.innerHTML = '<div class="flex items-center mb-3">' +
            '<svg class="w-6 h-6 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>' +
            '<h4 class="text-lg font-semibold text-green-800">AI Generation Complete</h4></div>' +
            '<p class="text-green-700 mb-3"><strong>' + (data.total_questions || 0) + ' questions</strong> generated successfully.</p>' +
            '<div class="flex flex-wrap">' + questionsHtml + '</div>';
    }

    nextBtn.addEventListener('click', async function() {
        if (!validateStep(currentStep)) return;

        if (currentStep === 3 && getSelectedMethod() === 'ai_generate') {
            await handleAiGeneration();
            return;
        }

        if (currentStep < totalSteps) {
            currentStep++;
            showStep(currentStep);
        }
    });

    prevBtn.addEventListener('click', function() {
        if (currentStep > 1) {
            currentStep--;
            showStep(currentStep);
        }
    });

    submitBtn.addEventListener('click', function(e) {
        if (aiGenerationComplete && aiGeneratedExamId) {
            e.preventDefault();
            window.location.href = '/exams/' + aiGeneratedExamId + '/edit/';
        }
    });

    showStep(1);
});