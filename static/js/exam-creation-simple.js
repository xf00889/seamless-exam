/**
 * Simplified Exam Creation Form JavaScript
 * Basic functionality to get the form working
 */

// Simple DOM ready function
function simpleReady(callback) {
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(callback, 0);
    } else {
        document.addEventListener('DOMContentLoaded', callback);
    }
}

// Simple element getter
function getElement(id) {
    const element = document.getElementById(id);
    if (!element) {
        console.error('Element not found:', id);
    }
    return element;
}

// Simple class manipulation
function addClass(element, className) {
    if (element && element.classList) {
        element.classList.add(className);
    }
}

function removeClass(element, className) {
    if (element && element.classList) {
        element.classList.remove(className);
    }
}

function hasClass(element, className) {
    return element && element.classList && element.classList.contains(className);
}

simpleReady(function() {
    // Initialize simple exam creation form
    
    // Get essential elements
    const examForm = getElement('examForm');
    const nextBtn = getElement('nextBtn');
    const prevBtn = getElement('prevBtn');
    const submitBtn = getElement('submitBtn');
    
    // Validate that essential elements exist
    if (!examForm || !nextBtn || !prevBtn || !submitBtn) {
        // Essential elements missing, cannot initialize
        return;
    }
    
    if (!nextBtn || !prevBtn || !submitBtn) {
        console.error('Critical buttons missing!');
        return;
    }
    
    // Get form steps
    const formSteps = document.querySelectorAll('.form-step');
    if (formSteps.length === 0) {
        // No form steps found
        return;
    }
    
    // Current step tracking
    let currentStep = 1;
    const totalSteps = 4;
    
    // Show specific step
    function showStep(step) {
        // Validate step number
        if (step < 1 || step > formSteps.length) return;
        
        // Hide all steps
        formSteps.forEach((stepEl, index) => {
            addClass(stepEl, 'hidden');
        });
        
        // Show current step
        const currentStepEl = getElement('step' + step);
        if (currentStepEl) {
            removeClass(currentStepEl, 'hidden');
        }
        
        // Update buttons
        updateButtons(step);
    }
    
    // Update button visibility
    function updateButtons(step) {
        // Validate step parameter
        if (!step || step < 1) return;
        
        if (step === 1) {
            // First step: show Next, hide Previous and Submit
            removeClass(nextBtn, 'hidden');
            addClass(prevBtn, 'hidden');
            addClass(submitBtn, 'hidden');
        } else if (step === totalSteps) {
            // Last step: show Previous and Submit, hide Next
            addClass(nextBtn, 'hidden');
            removeClass(prevBtn, 'hidden');
            removeClass(submitBtn, 'hidden');
        } else {
            // Middle steps: show Next and Previous, hide Submit
            removeClass(nextBtn, 'hidden');
            removeClass(prevBtn, 'hidden');
            addClass(submitBtn, 'hidden');
        }
        
        // Update button states as needed
    }
    
    // Basic validation
    function validateStep(step) {
        if (step === 1) {
            const title = getElement('title');
            const duration = getElement('duration_minutes');
            
            if (!title || !title.value.trim()) {
                return false;
            }
            
            if (!duration || !duration.value || duration.value < 1) {
                return false;
            }
        }
        
        if (step === 3) {
            const selectedMethod = document.querySelector('input[name="generation_method"]:checked');
            if (!selectedMethod) {
                return false;
            }
        }
        
        return true;
    }
    
    // Next button handler
    if (nextBtn) {
        nextBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Handle next button click
            
            if (validateStep(currentStep)) {
                if (currentStep < totalSteps) {
                    currentStep++;
                    showStep(currentStep);
                }
            }
        });
    }
    
    // Previous button handler
    if (prevBtn) {
        prevBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Handle previous button click
            
            if (currentStep > 1) {
                currentStep--;
                showStep(currentStep);
            }
        });
    }
    
    // Initialize first step
    showStep(currentStep);
    
    // Simple exam creation form initialized
});