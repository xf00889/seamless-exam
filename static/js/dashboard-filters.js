/**
 * Dashboard Filters JavaScript
 * Handles filtering functionality for the teacher dashboard
 */

(function() {
    'use strict';

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initializeFilters();
    });

    /**
     * Initialize filter functionality
     */
    function initializeFilters() {
        const filterForm = document.getElementById('filter-form');
        const examFilter = document.getElementById('exam-filter');
        const studentFilter = document.getElementById('student-filter');
        const statusFilter = document.getElementById('status-filter');

        if (!filterForm) {
            return;
        }

        // Auto-submit form when filters change
        if (examFilter) {
            examFilter.addEventListener('change', function() {
                filterForm.submit();
            });
        }

        if (studentFilter) {
            studentFilter.addEventListener('change', function() {
                filterForm.submit();
            });
        }

        if (statusFilter) {
            statusFilter.addEventListener('change', function() {
                filterForm.submit();
            });
        }

        // Add loading state during filter submission
        filterForm.addEventListener('submit', function() {
            const submitButton = filterForm.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = 'Loading...';
            }
        });
    }

    /**
     * Get URL parameter by name
     * @param {string} name - Parameter name
     * @returns {string|null} Parameter value or null
     */
    function getUrlParameter(name) {
        name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
        const regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
        const results = regex.exec(location.search);
        return results === null ? null : decodeURIComponent(results[1].replace(/\+/g, ' '));
    }

    /**
     * Update URL with new filter parameters
     * @param {Object} params - Filter parameters
     */
    function updateUrlWithFilters(params) {
        const url = new URL(window.location.href);
        
        // Clear existing filter parameters
        url.searchParams.delete('exam');
        url.searchParams.delete('student');
        url.searchParams.delete('status');
        
        // Add new parameters
        Object.keys(params).forEach(key => {
            if (params[key]) {
                url.searchParams.set(key, params[key]);
            }
        });
        
        // Update URL without page reload
        window.history.pushState({}, '', url);
    }

    /**
     * Clear all filters
     */
    function clearFilters() {
        const url = new URL(window.location.href);
        url.searchParams.delete('exam');
        url.searchParams.delete('student');
        url.searchParams.delete('status');
        window.location.href = url.toString();
    }

    /**
     * Export statistics data for external use
     * @returns {Object} Statistics data
     */
    function getStatistics() {
        const statsCards = document.querySelectorAll('.grid .bg-white');
        const stats = {};
        
        statsCards.forEach(card => {
            const label = card.querySelector('.text-gray-500');
            const value = card.querySelector('.text-3xl');
            
            if (label && value) {
                const key = label.textContent.trim().toLowerCase().replace(/\s+/g, '_');
                stats[key] = value.textContent.trim();
            }
        });
        
        return stats;
    }

    // Expose public API
    window.DashboardFilters = {
        clearFilters: clearFilters,
        getStatistics: getStatistics,
        updateUrlWithFilters: updateUrlWithFilters
    };
})();
