/**
 * Exam Review
 * Handles the review modal showing all questions and answers
 */

class ExamReview {
    constructor() {
        this.reviewModal = document.getElementById('review-modal');
        this.reviewContent = document.getElementById('review-content');
        this.reviewBtn = document.getElementById('review-exam-btn');
        this.closeReviewBtn = document.getElementById('close-review-btn');
        this.closeReviewFooterBtn = document.getElementById('close-review-footer-btn');
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        if (this.reviewBtn) {
            this.reviewBtn.addEventListener('click', () => this.openReview());
        }
        
        if (this.closeReviewBtn) {
            this.closeReviewBtn.addEventListener('click', () => this.closeReview());
        }
        
        if (this.closeReviewFooterBtn) {
            this.closeReviewFooterBtn.addEventListener('click', () => this.closeReview());
        }
        
        // Close on outside click
        if (this.reviewModal) {
            this.reviewModal.addEventListener('click', (e) => {
                if (e.target === this.reviewModal) {
                    this.closeReview();
                }
            });
        }
        
        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.reviewModal.classList.contains('hidden')) {
                this.closeReview();
            }
        });
    }
    
    openReview() {
        if (!this.reviewModal || !this.reviewContent) return;
        
        this.populateReview();
        this.reviewModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }
    
    closeReview() {
        if (!this.reviewModal) return;
        
        this.reviewModal.classList.add('hidden');
        document.body.style.overflow = ''; // Restore scrolling
    }
    
    populateReview() {
        if (!this.reviewContent) return;
        
        const questionCards = Array.from(document.querySelectorAll('.question-card'));
        let html = '';
        
        questionCards.forEach((card, index) => {
            const questionNumber = index + 1;
            const questionId = card.getAttribute('data-question-id');
            
            // Get question type
            const typeSpan = card.querySelector('span.inline-block.px-2');
            const questionType = typeSpan ? typeSpan.textContent.trim() : 'Question';
            
            // Get question text
            const questionTextEl = card.querySelector('p.text-gray-800, p.text-sm.text-gray-800, p.text-base.text-gray-800');
            const questionText = questionTextEl ? questionTextEl.textContent.trim() : 'No question text available';
            
            // Get points
            const pointsEl = card.querySelector('span.text-gray-500.ml-2');
            const points = pointsEl ? pointsEl.textContent.trim() : '';
            
            // Get answer
            let answerText = 'Not answered';
            let isAnswered = false;
            
            // Check for radio buttons
            const checkedRadio = card.querySelector('input[type="radio"]:checked');
            if (checkedRadio) {
                if (checkedRadio.type === 'radio') {
                    const label = checkedRadio.closest('label');
                    if (label) {
                        answerText = label.textContent.trim();
                        isAnswered = true;
                    }
                }
            }
            
            // Check for text input
            const textInput = card.querySelector('input[type="text"]');
            if (textInput && textInput.value.trim() !== '') {
                answerText = textInput.value.trim();
                isAnswered = true;
            }
            
            // Check for textarea
            const textarea = card.querySelector('textarea');
            if (textarea && textarea.value.trim() !== '') {
                answerText = textarea.value.trim();
                isAnswered = true;
            }
            
            const statusClass = isAnswered ? 'bg-green-100 border-green-500 text-green-700' : 'bg-gray-100 border-gray-300 text-gray-600';
            const statusText = isAnswered ? 'Answered' : 'Not Answered';
            
            html += `
                <div class="bg-white border-2 ${statusClass} rounded-lg p-4 mb-4">
                    <div class="flex justify-between items-start mb-2">
                        <div class="flex-1">
                            <div class="flex items-center gap-2 mb-2">
                                <span class="px-2 py-1 text-xs font-semibold rounded bg-gray-200 text-gray-800">${questionType}</span>
                                <span class="text-sm font-medium text-gray-700">Question ${questionNumber}</span>
                                <span class="text-xs text-gray-500">${points}</span>
                            </div>
                            <p class="text-sm text-gray-800 mb-3">${this.escapeHtml(questionText)}</p>
                            <div class="mb-2">
                                <span class="text-xs font-semibold ${isAnswered ? 'text-green-700' : 'text-gray-600'}">${statusText}:</span>
                                <p class="text-sm text-gray-700 mt-1 ${isAnswered ? '' : 'italic'}">${this.escapeHtml(answerText)}</p>
                            </div>
                        </div>
                    </div>
                    <button type="button" 
                            class="jump-to-question-btn mt-2 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded transition-colors"
                            data-question-number="${questionNumber}">
                        Jump to Question ${questionNumber}
                    </button>
                </div>
            `;
        });
        
        this.reviewContent.innerHTML = html;
        
        // Add event listeners to jump buttons
        const jumpButtons = this.reviewContent.querySelectorAll('.jump-to-question-btn');
        jumpButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const questionNumber = parseInt(btn.getAttribute('data-question-number'));
                this.jumpToQuestion(questionNumber);
            });
        });
    }
    
    jumpToQuestion(questionNumber) {
        this.closeReview();
        
        // Use navigation to jump to question
        if (window.examNavigation) {
            setTimeout(() => {
                window.examNavigation.jumpToQuestion(questionNumber);
            }, 300);
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.examReview = new ExamReview();
});

