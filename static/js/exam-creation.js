/**
 * Simple Exam Creation Form Navigation
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize exam form
    
    // Elements
    const nextBtn = document.getElementById('nextBtn');
    const prevBtn = document.getElementById('prevBtn');
    const submitBtn = document.getElementById('submitBtn');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const uploadSection = document.getElementById('uploadSection');
    
    // Current step
    let currentStep = 1;
    const totalSteps = 4;
    
    // Show step function
    function showStep(step) {
        // Validate step number
        if (step < 1 || step > 3) return;
        
        // Hide all steps
        document.querySelectorAll('.form-step').forEach(el => {
            el.classList.add('hidden');
        });
        
        // Show current step
        const stepEl = document.getElementById('step' + step);
        if (stepEl) {
            stepEl.classList.remove('hidden');
        }
        
        // Update progress
        const percentage = (step / totalSteps) * 100;
        progressBar.style.width = percentage + '%';
        progressText.textContent = `Step ${step} of ${totalSteps}`;
        
        // Update step indicators
        updateStepIndicators(step);
        
        // Update buttons
        updateButtons(step);
        
        // Update step-specific content
        if (step === 3) {
            updateMethodOptions();
        } else if (step === 4) {
            updateSummary();
        }
    }
    
    // Update button visibility
    function updateButtons(step) {
        // Hide all buttons first
        nextBtn.classList.add('hidden');
        prevBtn.classList.add('hidden');
        submitBtn.classList.add('hidden');
        
        if (step === 1) {
            // First step: show only Next
            nextBtn.classList.remove('hidden');
        } else if (step === totalSteps) {
            // Last step: show Previous and Submit
            prevBtn.classList.remove('hidden');
            submitBtn.classList.remove('hidden');
        } else {
            // Middle steps: show Next and Previous
            nextBtn.classList.remove('hidden');
            prevBtn.classList.remove('hidden');
        }
    }
    
    // Update step indicators with system-consistent styling
    function updateStepIndicators(step) {
        document.querySelectorAll('.step-indicator').forEach((el, index) => {
            const stepNum = index + 1;
            const circle = el.querySelector('div');
            const text = el.querySelector('p');
            const checkmark = el.querySelector('.step-check');
            
            if (stepNum < step) {
                // Completed step - green with checkmark
                circle.className = 'w-10 h-10 rounded-full bg-green-600 text-white text-sm font-bold flex items-center justify-center mx-auto shadow-md transition-all duration-300';
                text.className = 'text-sm font-medium text-green-600 mb-1';
                if (checkmark) checkmark.classList.remove('hidden');
                el.classList.add('active');
            } else if (stepNum === step) {
                // Current step - blue
                circle.className = 'w-10 h-10 rounded-full bg-blue-600 text-white text-sm font-bold flex items-center justify-center mx-auto shadow-md transition-all duration-300';
                text.className = 'text-sm font-medium text-blue-600 mb-1';
                if (checkmark) checkmark.classList.add('hidden');
                el.classList.add('active');
            } else {
                // Future step - gray
                circle.className = 'w-10 h-10 rounded-full bg-gray-300 text-white text-sm font-bold flex items-center justify-center mx-auto shadow-md transition-all duration-300';
                text.className = 'text-sm font-medium text-gray-500 mb-1';
                if (checkmark) checkmark.classList.add('hidden');
                el.classList.remove('active');
            }
        });
    }
    
    // Update method options
    function updateMethodOptions() {
        const methodInputs = document.querySelectorAll('input[name="generation_method"]');
        
        methodInputs.forEach(input => {
            input.addEventListener('change', function() {
                if (this.value === 'upload') {
                    uploadSection.classList.remove('hidden');
                } else {
                    uploadSection.classList.add('hidden');
                }
            });
        });
        
        // Check initial state
        const selectedMethod = document.querySelector('input[name="generation_method"]:checked');
        if (selectedMethod && selectedMethod.value === 'upload') {
            uploadSection.classList.remove('hidden');
        }
    }
    
    // Update summary
    function updateSummary() {
        const title = document.getElementById('title').value || 'Not specified';
        const subject = document.getElementById('subject').value || 'Not specified';
        const duration = document.getElementById('duration_minutes').value;
        const method = document.querySelector('input[name="generation_method"]:checked');
        const classes = document.querySelectorAll('input[name="assigned_classes"]:checked');
        
        document.getElementById('summary-title').textContent = title;
        document.getElementById('summary-subject').textContent = subject;
        document.getElementById('summary-duration').textContent = duration ? duration + ' minutes' : 'Not specified';
        document.getElementById('summary-method').textContent = method ? (method.value === 'manual' ? 'Manual Entry' : 'File Upload') : 'Manual Entry';
        document.getElementById('summary-classes').textContent = classes.length > 0 ? classes.length + ' selected' : 'None selected';
    }
    
    // Validate step
    function validateStep(step) {
        if (step === 1) {
            const title = document.getElementById('title').value.trim();
            const duration = document.getElementById('duration_minutes').value;
            
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
    
    // Event listeners
    nextBtn.addEventListener('click', function() {
        // Validate current step before proceeding
        
        if (validateStep(currentStep)) {
            if (currentStep < totalSteps) {
                currentStep++;
                showStep(currentStep);
            }
        }
    });
    
    prevBtn.addEventListener('click', function() {
        // Go to previous step
        
        if (currentStep > 1) {
            currentStep--;
            showStep(currentStep);
        }
    });
    
    submitBtn.addEventListener('click', function() {
        // Final form submission
        // Form will submit normally
    });
    
    // Initialize
    showStep(1);
    // Exam form initialized
});