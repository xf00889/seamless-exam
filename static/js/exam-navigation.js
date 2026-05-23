/**
 * Exam Navigation
 * Handles sidebar navigation and question jumping
 */

class ExamNavigation {
    constructor() {
        this.currentQuestionNumber = 1;
        this.totalQuestions = document.querySelectorAll('.question-card').length;
        this.questionCards = Array.from(document.querySelectorAll('.question-card'));
        this.navButtons = Array.from(document.querySelectorAll('.question-nav-btn'));
        
        this.initializeEventListeners();
        this.updateSidebarState();
    }
    
    initializeEventListeners() {
        // Handle question navigation button clicks
        this.navButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const questionNumber = parseInt(btn.getAttribute('data-question-number'));
                this.jumpToQuestion(questionNumber);
            });
        });
    }
    
    jumpToQuestion(questionNumber) {
        if (questionNumber < 1 || questionNumber > this.totalQuestions) {
            return;
        }
        
        this.currentQuestionNumber = questionNumber;
        
        // Find the question card
        const questionCard = this.questionCards[questionNumber - 1];
        if (!questionCard) return;
        
        // Calculate which page this question is on (5 questions per page)
        const targetPage = Math.ceil(questionNumber / 5);
        
        // Trigger pagination to show the correct page
        if (window.examPagination) {
            window.examPagination.goToPage(targetPage);
        }
        
        // Scroll to question after a short delay to allow pagination
        setTimeout(() => {
            questionCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
            // Highlight the question briefly
            questionCard.classList.add('ring-2', 'ring-blue-500');
            setTimeout(() => {
                questionCard.classList.remove('ring-2', 'ring-blue-500');
            }, 2000);
        }, 100);
        
        this.updateSidebarState();
    }
    
    updateSidebarState() {
        this.navButtons.forEach((btn, index) => {
            const questionNumber = index + 1;
            const questionId = btn.getAttribute('data-question-id');
            const isAnswered = this.isQuestionAnswered(questionId);
            const isCurrent = questionNumber === this.currentQuestionNumber;
            
            // Reset classes
            btn.className = 'question-nav-btn w-10 h-10 rounded-md border-2 text-sm font-medium transition-all hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500';
            
            if (isCurrent) {
                // Current question - blue
                btn.classList.add('bg-blue-100', 'border-blue-500', 'text-blue-700', 'font-bold');
            } else if (isAnswered) {
                // Answered - green
                btn.classList.add('bg-green-100', 'border-green-500', 'text-green-700');
                // Add checkmark icon
                if (!btn.querySelector('svg')) {
                    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                    svg.setAttribute('class', 'w-4 h-4 absolute top-0 right-0');
                    svg.setAttribute('fill', 'currentColor');
                    svg.setAttribute('viewBox', '0 0 20 20');
                    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    path.setAttribute('fill-rule', 'evenodd');
                    path.setAttribute('d', 'M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z');
                    path.setAttribute('clip-rule', 'evenodd');
                    svg.appendChild(path);
                    btn.style.position = 'relative';
                    btn.appendChild(svg);
                }
            } else {
                // Unanswered - gray
                btn.classList.add('bg-gray-100', 'border-gray-300', 'text-gray-600');
                // Remove checkmark if exists
                const svg = btn.querySelector('svg');
                if (svg) svg.remove();
            }
        });
    }
    
    isQuestionAnswered(questionId) {
        const questionCard = document.querySelector(`.question-card[data-question-id="${questionId}"]`);
        if (!questionCard) return false;
        
        // Check for radio buttons
        const checkedRadio = questionCard.querySelector('input[type="radio"]:checked');
        if (checkedRadio) return true;
        
        // Check for text inputs
        const textInput = questionCard.querySelector('input[type="text"]');
        if (textInput && textInput.value.trim() !== '') return true;
        
        // Check for textareas
        const textarea = questionCard.querySelector('textarea');
        if (textarea && textarea.value.trim() !== '') return true;
        
        return false;
    }
    
    markQuestionAnswered(questionId) {
        const btn = this.navButtons.find(b => b.getAttribute('data-question-id') === questionId);
        if (btn) {
            btn.setAttribute('data-answered', 'true');
            this.updateSidebarState();
        }
    }
    
    setCurrentQuestion(questionNumber) {
        this.currentQuestionNumber = questionNumber;
        this.updateSidebarState();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.examNavigation = new ExamNavigation();
});

