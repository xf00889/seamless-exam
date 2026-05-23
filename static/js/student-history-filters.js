/**
 * Student History Filters JavaScript
 * Handles AJAX filtering and pagination for student exam history
 */

(function() {
    'use strict';

    // State management
    let isLoading = false;
    let currentFilters = {
        date_from: '',
        date_to: '',
        status: '',
        sort: 'date',
        order: 'desc',
        page: 1
    };

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initializeFilters();
        initializePagination();
        initializeSorting();
        initializeKeyboardShortcuts();
        loadInitialFilters();
    });

    /**
     * Load initial filter values from URL parameters
     */
    function loadInitialFilters() {
        const urlParams = new URLSearchParams(window.location.search);
        currentFilters.date_from = urlParams.get('date_from') || '';
        currentFilters.date_to = urlParams.get('date_to') || '';
        currentFilters.status = urlParams.get('status') || '';
        currentFilters.sort = urlParams.get('sort') || 'date';
        currentFilters.order = urlParams.get('order') || 'desc';
        currentFilters.page = parseInt(urlParams.get('page')) || 1;
    }

    /**
     * Initialize filter functionality with AJAX support
     * Requirement: 15.3 - AJAX for filter updates without page reload
     */
    function initializeFilters() {
        const filterForm = document.getElementById('filter-form');
        if (!filterForm) return;

        const dateFromInput = document.getElementById('date_from');
        const dateToInput = document.getElementById('date_to');
        const statusSelect = document.getElementById('status');
        const applyButton = filterForm.querySelector('button[type="submit"]');
        const clearButton = filterForm.querySelector('a[href*="student_history"]');

        // Prevent default form submission
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            applyFilters();
        });

        // Clear filters button
        if (clearButton) {
            clearButton.addEventListener('click', function(e) {
                e.preventDefault();
                clearFilters();
            });
        }

        // Optional: Auto-apply on change (can be enabled/disabled)
        // dateFromInput?.addEventListener('change', () => applyFilters());
        // dateToInput?.addEventListener('change', () => applyFilters());
        // statusSelect?.addEventListener('change', () => applyFilters());
    }

    /**
     * Apply filters and fetch filtered data via AJAX
     * Requirement: 15.3 - Update results without page reload
     */
    function applyFilters() {
        if (isLoading) return;

        const dateFromInput = document.getElementById('date_from');
        const dateToInput = document.getElementById('date_to');
        const statusSelect = document.getElementById('status');

        // Update current filters
        currentFilters.date_from = dateFromInput?.value || '';
        currentFilters.date_to = dateToInput?.value || '';
        currentFilters.status = statusSelect?.value || '';
        currentFilters.page = 1; // Reset to first page when filtering

        // Validate date range
        if (currentFilters.date_from && currentFilters.date_to) {
            const fromDate = new Date(currentFilters.date_from);
            const toDate = new Date(currentFilters.date_to);
            
            if (fromDate > toDate) {
                NotificationManager.error('Start date must be before end date');
                return;
            }
        }

        fetchHistory();
    }

    /**
     * Clear all filters and reload data
     * Requirement: 15.5 - Clear filters functionality
     */
    function clearFilters() {
        // Reset filter inputs
        const dateFromInput = document.getElementById('date_from');
        const dateToInput = document.getElementById('date_to');
        const statusSelect = document.getElementById('status');

        if (dateFromInput) dateFromInput.value = '';
        if (dateToInput) dateToInput.value = '';
        if (statusSelect) statusSelect.value = '';

        // Reset current filters
        currentFilters.date_from = '';
        currentFilters.date_to = '';
        currentFilters.status = '';
        currentFilters.page = 1;

        // Fetch unfiltered data
        fetchHistory();
    }

    /**
     * Initialize pagination click handlers
     * Requirement: 15.1 - Pagination with 10 items per page
     */
    function initializePagination() {
        document.addEventListener('click', function(e) {
            // Handle pagination links
            if (e.target.matches('.pagination-link') || e.target.closest('.pagination-link')) {
                e.preventDefault();
                const link = e.target.matches('.pagination-link') ? e.target : e.target.closest('.pagination-link');
                const page = parseInt(link.dataset.page);
                
                if (page && !isNaN(page)) {
                    currentFilters.page = page;
                    fetchHistory();
                }
            }
        });
    }

    /**
     * Initialize sorting functionality
     */
    function initializeSorting() {
        document.addEventListener('click', function(e) {
            const sortLink = e.target.closest('a[href*="sort="]');
            if (sortLink) {
                e.preventDefault();
                const url = new URL(sortLink.href);
                currentFilters.sort = url.searchParams.get('sort') || 'date';
                currentFilters.order = url.searchParams.get('order') || 'desc';
                currentFilters.page = 1; // Reset to first page when sorting
                fetchHistory();
            }
        });
    }

    /**
     * Fetch history data via AJAX
     * Requirement: 15.3 - AJAX for filter updates
     */
    function fetchHistory() {
        if (isLoading) return;

        isLoading = true;
        showLoadingState();

        // Build query parameters
        const params = new URLSearchParams();
        if (currentFilters.date_from) params.append('date_from', currentFilters.date_from);
        if (currentFilters.date_to) params.append('date_to', currentFilters.date_to);
        if (currentFilters.status) params.append('status', currentFilters.status);
        params.append('sort', currentFilters.sort);
        params.append('order', currentFilters.order);
        params.append('page', currentFilters.page);

        // Make AJAX request
        fetch(`/users/student/history/?${params.toString()}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                updateHistoryTable(data.data);
                updatePagination(data.data.pagination);
                updateActiveFilters(data.data.filters);
                updateURL(params);
            } else {
                NotificationManager.error(data.error || 'Failed to load exam history');
            }
        })
        .catch(error => {
            console.error('Error fetching history:', error);
            NotificationManager.error('Failed to load exam history. Please try again.');
        })
        .finally(() => {
            isLoading = false;
            hideLoadingState();
        });
    }

    /**
     * Update the history table with new data
     */
    function updateHistoryTable(data) {
        const desktopTable = document.querySelector('.hidden.md\\:block tbody');
        const mobileCards = document.querySelector('.md\\:hidden');

        if (!data.exams || data.exams.length === 0) {
            showEmptyState();
            return;
        }

        // Update desktop table
        if (desktopTable) {
            desktopTable.innerHTML = data.exams.map(exam => createTableRow(exam)).join('');
        }

        // Update mobile cards
        if (mobileCards) {
            mobileCards.innerHTML = data.exams.map(exam => createMobileCard(exam)).join('');
        }
    }

    /**
     * Create table row HTML for desktop view
     */
    function createTableRow(exam) {
        const date = exam.date ? new Date(exam.date) : null;
        const dateStr = date ? date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '-';
        const timeStr = date ? date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }) : '';
        
        const isGraded = exam.status === 'graded';
        const isPassed = exam.percentage >= 60;
        
        let statusBadge = '';
        if (isGraded) {
            statusBadge = isPassed 
                ? '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Passed</span>'
                : '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">Failed</span>';
        } else {
            statusBadge = '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">Pending</span>';
        }

        const scoreDisplay = isGraded 
            ? `<div class="text-sm font-medium text-gray-900">${exam.score.toFixed(1)}/${exam.total_possible.toFixed(1)}</div>`
            : '<div class="text-sm text-gray-500">-</div>';

        const percentageDisplay = isGraded
            ? `<div class="text-sm font-semibold ${isPassed ? 'text-green-600' : 'text-red-600'}">${exam.percentage.toFixed(1)}%</div>`
            : '<div class="text-sm text-gray-500">-</div>';

        const actionDisplay = isGraded
            ? `<a href="/attempts/results/${exam.attempt_id}/" class="text-blue-600 hover:text-blue-900 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1">View Results</a>`
            : '<span class="text-gray-400">Awaiting Grading</span>';

        return `
            <tr class="hover:bg-gray-50 transition-colors duration-150">
                <td class="px-6 py-4">
                    <div class="text-sm font-medium text-gray-900">${escapeHtml(exam.exam_title)}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${dateStr}</div>
                    <div class="text-xs text-gray-500">${timeStr}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">${scoreDisplay}</td>
                <td class="px-6 py-4 whitespace-nowrap">${percentageDisplay}</td>
                <td class="px-6 py-4 whitespace-nowrap">${statusBadge}</td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">${actionDisplay}</td>
            </tr>
        `;
    }

    /**
     * Create mobile card HTML
     */
    function createMobileCard(exam) {
        const date = exam.date ? new Date(exam.date) : null;
        const dateStr = date ? date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '-';
        const timeStr = date ? date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }) : '';
        
        const isGraded = exam.status === 'graded';
        const isPassed = exam.percentage >= 60;
        
        let statusBadge = '';
        if (isGraded) {
            statusBadge = isPassed 
                ? '<span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Passed</span>'
                : '<span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">Failed</span>';
        } else {
            statusBadge = '<span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">Pending</span>';
        }

        const scoreSection = isGraded ? `
            <div class="grid grid-cols-2 gap-4 mb-4">
                <div>
                    <dt class="text-xs font-medium text-gray-500 uppercase">Score</dt>
                    <dd class="mt-1 text-sm font-semibold text-gray-900">${exam.score.toFixed(1)}/${exam.total_possible.toFixed(1)}</dd>
                </div>
                <div>
                    <dt class="text-xs font-medium text-gray-500 uppercase">Percentage</dt>
                    <dd class="mt-1 text-sm font-semibold ${isPassed ? 'text-green-600' : 'text-red-600'}">${exam.percentage.toFixed(1)}%</dd>
                </div>
            </div>
            <div class="mt-4">
                <a href="/attempts/results/${exam.attempt_id}/" class="block w-full text-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-200">
                    View Results
                </a>
            </div>
        ` : `
            <div class="mt-4 text-center py-2 text-sm text-gray-500">
                Awaiting grading from teacher
            </div>
        `;

        return `
            <div class="p-6 hover:bg-gray-50 transition-colors duration-150 border-b border-gray-200">
                <div class="flex justify-between items-start mb-3">
                    <div class="flex-1 min-w-0">
                        <h3 class="text-base font-semibold text-gray-900 truncate">${escapeHtml(exam.exam_title)}</h3>
                        <p class="text-sm text-gray-500 mt-1">${dateStr} at ${timeStr}</p>
                    </div>
                    <div class="ml-4">${statusBadge}</div>
                </div>
                ${scoreSection}
            </div>
        `;
    }

    /**
     * Update pagination controls
     * Requirement: 15.1 - Pagination with 10 items per page
     */
    function updatePagination(pagination) {
        const paginationContainer = document.querySelector('.border-t.border-gray-200');
        if (!paginationContainer) return;

        if (pagination.total_pages <= 1) {
            paginationContainer.style.display = 'none';
            return;
        }

        paginationContainer.style.display = 'block';

        // Generate pagination HTML
        let paginationHTML = '<div class="px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">';
        
        // Mobile view
        paginationHTML += '<div class="flex-1 flex justify-between sm:hidden">';
        if (pagination.has_previous) {
            paginationHTML += `<a href="#" class="pagination-link relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50" data-page="${pagination.previous_page}">Previous</a>`;
        } else {
            paginationHTML += '<span class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-400 bg-gray-100 cursor-not-allowed">Previous</span>';
        }
        if (pagination.has_next) {
            paginationHTML += `<a href="#" class="pagination-link ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50" data-page="${pagination.next_page}">Next</a>`;
        } else {
            paginationHTML += '<span class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-400 bg-gray-100 cursor-not-allowed">Next</span>';
        }
        paginationHTML += '</div>';

        // Desktop view
        paginationHTML += '<div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">';
        paginationHTML += `<div><p class="text-sm text-gray-700">Showing page <span class="font-medium">${pagination.current_page}</span> of <span class="font-medium">${pagination.total_pages}</span> (${pagination.total_count} total exams)</p></div>`;
        paginationHTML += '<div><nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">';
        
        // Previous button
        if (pagination.has_previous) {
            paginationHTML += `<a href="#" class="pagination-link relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50" data-page="${pagination.previous_page}">
                <span class="sr-only">Previous</span>
                <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
            </a>`;
        }

        // Page numbers
        const maxPages = 7;
        let startPage = Math.max(1, pagination.current_page - Math.floor(maxPages / 2));
        let endPage = Math.min(pagination.total_pages, startPage + maxPages - 1);
        
        if (endPage - startPage < maxPages - 1) {
            startPage = Math.max(1, endPage - maxPages + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            if (i === pagination.current_page) {
                paginationHTML += `<span class="z-10 bg-blue-50 border-blue-500 text-blue-600 relative inline-flex items-center px-4 py-2 border text-sm font-medium">${i}</span>`;
            } else {
                paginationHTML += `<a href="#" class="pagination-link bg-white border-gray-300 text-gray-500 hover:bg-gray-50 relative inline-flex items-center px-4 py-2 border text-sm font-medium" data-page="${i}">${i}</a>`;
            }
        }

        // Next button
        if (pagination.has_next) {
            paginationHTML += `<a href="#" class="pagination-link relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50" data-page="${pagination.next_page}">
                <span class="sr-only">Next</span>
                <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/></svg>
            </a>`;
        }

        paginationHTML += '</nav></div></div></div>';
        
        paginationContainer.innerHTML = paginationHTML;
    }

    /**
     * Update active filters display
     * Requirement: 15.4 - Display active filters
     */
    function updateActiveFilters(filters) {
        const activeFiltersContainer = document.querySelector('.mt-4.pt-4.border-t.border-gray-200');
        if (!activeFiltersContainer) return;

        const hasFilters = filters.date_from || filters.date_to || filters.status;

        if (!hasFilters) {
            activeFiltersContainer.style.display = 'none';
            return;
        }

        activeFiltersContainer.style.display = 'block';

        let filtersHTML = '<div class="flex flex-wrap items-center gap-2">';
        filtersHTML += '<span class="text-sm font-medium text-gray-700">Active filters:</span>';

        if (filters.date_from) {
            filtersHTML += `<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">From: ${filters.date_from}</span>`;
        }
        if (filters.date_to) {
            filtersHTML += `<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">To: ${filters.date_to}</span>`;
        }
        if (filters.status) {
            const statusLabel = filters.status.charAt(0).toUpperCase() + filters.status.slice(1);
            filtersHTML += `<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">Status: ${statusLabel}</span>`;
        }

        filtersHTML += '</div>';
        activeFiltersContainer.innerHTML = filtersHTML;
    }

    /**
     * Update browser URL without page reload
     */
    function updateURL(params) {
        const newURL = `${window.location.pathname}?${params.toString()}`;
        window.history.pushState({ path: newURL }, '', newURL);
    }

    /**
     * Show empty state when no results
     */
    function showEmptyState() {
        const resultsSection = document.querySelector('.bg-white.shadow-md.rounded-lg.overflow-hidden');
        if (!resultsSection) return;

        const hasFilters = currentFilters.date_from || currentFilters.date_to || currentFilters.status;

        const emptyHTML = `
            <div class="p-12 text-center">
                <svg class="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                ${hasFilters ? `
                    <h3 class="mt-4 text-lg font-medium text-gray-900">No exams found</h3>
                    <p class="mt-2 text-sm text-gray-500">No exams match your current filters. Try adjusting your filter criteria.</p>
                    <div class="mt-6">
                        <button onclick="window.studentHistoryFilters.clearFilters()" class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                            Clear All Filters
                        </button>
                    </div>
                ` : `
                    <h3 class="mt-4 text-lg font-medium text-gray-900">No exam history yet</h3>
                    <p class="mt-2 text-sm text-gray-500">You haven't taken any exams yet. Start taking exams to see your history here.</p>
                    <div class="mt-6">
                        <a href="/attempts/exams/" class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                            Browse Available Exams
                        </a>
                    </div>
                `}
            </div>
        `;

        resultsSection.innerHTML = emptyHTML;
    }

    /**
     * Show loading state
     */
    function showLoadingState() {
        const resultsSection = document.querySelector('.bg-white.shadow-md.rounded-lg.overflow-hidden');
        if (resultsSection) {
            resultsSection.style.opacity = '0.6';
            resultsSection.style.pointerEvents = 'none';
        }
    }

    /**
     * Hide loading state
     */
    function hideLoadingState() {
        const resultsSection = document.querySelector('.bg-white.shadow-md.rounded-lg.overflow-hidden');
        if (resultsSection) {
            resultsSection.style.opacity = '1';
            resultsSection.style.pointerEvents = 'auto';
        }
    }



    /**
     * Initialize keyboard shortcuts
     */
    function initializeKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + E to export
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                const exportBtn = document.querySelector('a[href*="export_history"]');
                if (exportBtn) {
                    exportBtn.click();
                }
            }
            
            // Ctrl/Cmd + K to focus filter
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const dateFromInput = document.getElementById('date_from');
                if (dateFromInput) {
                    dateFromInput.focus();
                }
            }
        });
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Expose public API
    window.studentHistoryFilters = {
        applyFilters,
        clearFilters,
        fetchHistory
    };

})();
