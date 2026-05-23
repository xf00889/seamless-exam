/**
 * Exam Pagination
 * Handles pagination of questions (5 per page)
 */

class ExamPagination {
    constructor() {
        this.questionsPerPage = 5;
        this.currentPage = 1;
        this.questionCards = Array.from(document.querySelectorAll('.question-card'));
        this.totalQuestions = this.questionCards.length;
        this.totalPages = Math.ceil(this.totalQuestions / this.questionsPerPage);
        
        this.prevBtn = document.getElementById('prev-page-btn');
        this.nextBtn = document.getElementById('next-page-btn');
        this.pageIndicator = document.getElementById('page-indicator');
        
        // Initialize from URL hash if present
        const hash = window.location.hash;
        if (hash) {
            const pageMatch = hash.match(/page-(\d+)/);
            if (pageMatch) {
                this.currentPage = parseInt(pageMatch[1]);
            }
        }
        
        this.initializeEventListeners();
        this.showPage(this.currentPage);
    }
    
    initializeEventListeners() {
        if (this.prevBtn) {
            this.prevBtn.addEventListener('click', () => this.previousPage());
        }
        
        if (this.nextBtn) {
            this.nextBtn.addEventListener('click', () => this.nextPage());
        }
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) return; // Don't interfere with browser shortcuts
            
            if (e.key === 'ArrowLeft' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
                this.previousPage();
            } else if (e.key === 'ArrowRight' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
                this.nextPage();
            }
        });
    }
    
    showPage(page) {
        if (page < 1) page = 1;
        if (page > this.totalPages) page = this.totalPages;
        
        this.currentPage = page;
        
        // Calculate question range for this page
        const startIndex = (page - 1) * this.questionsPerPage;
        const endIndex = Math.min(startIndex + this.questionsPerPage, this.totalQuestions);
        
        // Hide all questions first
        this.questionCards.forEach((card, index) => {
            if (index >= startIndex && index < endIndex) {
                card.classList.remove('hidden');
                card.classList.add('question-page-item');
            } else {
                card.classList.add('hidden');
                card.classList.remove('question-page-item');
            }
        });
        
        // Update navigation buttons
        if (this.prevBtn) {
            this.prevBtn.disabled = page === 1;
        }
        if (this.nextBtn) {
            this.nextBtn.disabled = page === this.totalPages;
        }
        
        // Update page indicator
        if (this.pageIndicator) {
            this.pageIndicator.textContent = `Page ${page} of ${this.totalPages}`;
        }
        
        // Update URL hash
        window.location.hash = `page-${page}`;
        
        // Update current question in navigation
        if (window.examNavigation) {
            const firstQuestionOnPage = startIndex + 1;
            window.examNavigation.setCurrentQuestion(firstQuestionOnPage);
        }
        
        // Scroll to top of questions container
        const container = document.getElementById('questions-container');
        if (container) {
            container.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
    
    previousPage() {
        if (this.currentPage > 1) {
            this.showPage(this.currentPage - 1);
        }
    }
    
    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.showPage(this.currentPage + 1);
        }
    }
    
    goToPage(page) {
        this.showPage(page);
    }
    
    getCurrentPage() {
        return this.currentPage;
    }
    
    getTotalPages() {
        return this.totalPages;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.examPagination = new ExamPagination();
});

