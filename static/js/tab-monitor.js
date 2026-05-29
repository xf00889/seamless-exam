

class TabMonitor {
    constructor(attemptId, options = {}) {
        this.attemptId = attemptId;
        this.warningCount = 0;
        this.maxWarnings = options.maxWarnings || 3;
        this.isMonitoring = false;
        this.currentViolationId = null;
        this.storageKey = `tab_monitor_${attemptId}`;
        this.gracePeriod = options.gracePeriod || 1000; // 1 second to detect tab switches quickly
        this.gracePeriodTimer = null;
        this.lastVisibilityChange = Date.now();

        // Split-screen detection
        this.initialWidth = window.innerWidth;
        this.splitScreenThreshold = 0.75; // Flag if window is less than 75% of screen width
        this.splitScreenDetected = false;
        this.splitScreenGraceTimer = null;
        this.blurWithoutHidden = false;
        this.lastWindowWidth = window.innerWidth;
        this.resizeCheckInterval = null;

        // AJAX client for server communication
        this.ajaxClient = new AjaxClient({
            maxRetries: 3,
            retryDelay: 1000
        });

        // Queue for offline violation events
        this.violationQueue = [];
        this.isOnline = navigator.onLine;

        // Bind methods to maintain context
        this.handleVisibilityChange = this.handleVisibilityChange.bind(this);
        this.handleOnline = this.handleOnline.bind(this);
        this.handleOffline = this.handleOffline.bind(this);
        this.handleResize = this.handleResize.bind(this);
        this.handleWindowBlur = this.handleWindowBlur.bind(this);
        this.handleWindowFocus = this.handleWindowFocus.bind(this);

        // Load saved state
        this.loadViolationState();
    }
    
    /**
     * Start monitoring tab visibility
     * Requirements: 2.1, 2.2, 2.3
     */
    startMonitoring() {
        if (this.isMonitoring) {
            console.warn('Tab monitoring already started');
            return;
        }

        // Check if Page Visibility API is supported
        if (typeof document.hidden === 'undefined') {
            console.error('Page Visibility API not supported. Tab monitoring disabled.');
            this.showUnsupportedBrowserNotice();
            return;
        }

        // Add visibility change listener
        document.addEventListener('visibilitychange', this.handleVisibilityChange);

        // Add online/offline listeners for network handling
        window.addEventListener('online', this.handleOnline);
        window.addEventListener('offline', this.handleOffline);

        // Split-screen detection listeners
        window.addEventListener('resize', this.handleResize);
        window.addEventListener('blur', this.handleWindowBlur);
        window.addEventListener('focus', this.handleWindowFocus);

        // Store initial window width for comparison
        this.initialWidth = window.screen.availWidth || window.innerWidth;

        this.isMonitoring = true;

        // Start periodic split-screen check
        this.startSplitScreenCheck();

        // Sync state with server on start
        this.syncWithServer();

        // Update warning display
        this.updateWarningDisplay();
    }
    
    /**
     * Stop monitoring tab visibility
     */
    stopMonitoring() {
        if (!this.isMonitoring) {
            return;
        }

        document.removeEventListener('visibilitychange', this.handleVisibilityChange);
        window.removeEventListener('online', this.handleOnline);
        window.removeEventListener('offline', this.handleOffline);
        window.removeEventListener('resize', this.handleResize);
        window.removeEventListener('blur', this.handleWindowBlur);
        window.removeEventListener('focus', this.handleWindowFocus);

        if (this.gracePeriodTimer) {
            clearTimeout(this.gracePeriodTimer);
        }
        if (this.splitScreenGraceTimer) {
            clearTimeout(this.splitScreenGraceTimer);
        }
        if (this.resizeCheckInterval) {
            clearInterval(this.resizeCheckInterval);
        }

        this.isMonitoring = false;
    }
    
    /**
     * Handle visibility change events
     * Requirements: 2.1, 2.2, 2.3, 2.4
     */
    handleVisibilityChange() {
        const now = Date.now();
        const timeSinceLastChange = now - this.lastVisibilityChange;
        
        // Ignore rapid changes (potential false positives)
        if (timeSinceLastChange < 500) {
            return;
        }
        
        this.lastVisibilityChange = now;
        
        if (document.hidden) {
            // Student left the exam tab
            
            // Use grace period to avoid false positives from accidental clicks
            this.gracePeriodTimer = setTimeout(() => {
                this.recordViolation('tab_switch');
            }, this.gracePeriod);
        } else {
            // Student returned to exam tab
            
            // Cancel grace period if student returned quickly
            if (this.gracePeriodTimer) {
                clearTimeout(this.gracePeriodTimer);
                this.gracePeriodTimer = null;
                return;
            }
            
            // Record return time if there's an active violation
            if (this.currentViolationId) {
                this.recordReturn();
            }
        }
    }

    handleResize() {
        const screenWidth = window.screen.availWidth || window.screen.width;
        const windowWidth = window.outerWidth || window.innerWidth;
        const ratio = windowWidth / screenWidth;

        if (ratio < this.splitScreenThreshold && !this.splitScreenDetected) {
            if (this.splitScreenGraceTimer) {
                clearTimeout(this.splitScreenGraceTimer);
            }
            this.splitScreenGraceTimer = setTimeout(() => {
                const currentRatio = (window.outerWidth || window.innerWidth) / screenWidth;
                if (currentRatio < this.splitScreenThreshold) {
                    this.splitScreenDetected = true;
                    this.recordViolation('split_screen');
                }
            }, 1500);
        } else if (ratio >= this.splitScreenThreshold && this.splitScreenDetected) {
            this.splitScreenDetected = false;
            if (this.splitScreenGraceTimer) {
                clearTimeout(this.splitScreenGraceTimer);
                this.splitScreenGraceTimer = null;
            }
        }
    }

    handleWindowBlur() {
        if (!document.hidden) {
            this.blurWithoutHidden = true;
            this.splitScreenGraceTimer = setTimeout(() => {
                if (this.blurWithoutHidden && !document.hidden) {
                    this.recordViolation('window_blur');
                }
            }, 1500);
        }
    }

    handleWindowFocus() {
        this.blurWithoutHidden = false;
        if (this.splitScreenGraceTimer) {
            clearTimeout(this.splitScreenGraceTimer);
            this.splitScreenGraceTimer = null;
        }
    }

    startSplitScreenCheck() {
        this.resizeCheckInterval = setInterval(() => {
            if (!this.isMonitoring) return;

            const screenWidth = window.screen.availWidth || window.screen.width;
            const windowWidth = window.outerWidth || window.innerWidth;
            const ratio = windowWidth / screenWidth;

            if (ratio < this.splitScreenThreshold && !this.splitScreenDetected) {
                this.splitScreenDetected = true;
                this.recordViolation('split_screen');
            } else if (ratio >= this.splitScreenThreshold) {
                this.splitScreenDetected = false;
            }
        }, 5000);
    }

    /**
     * Record a tab switch violation
     * Requirements: 2.1, 3.1, 3.4, 8.1, 8.2, 8.5
     */
    async recordViolation(type = 'tab_switch') {

        const violationData = {
            violated_at: new Date().toISOString(),
            attempt_id: this.attemptId,
            violation_type: type
        };
        
        // If offline, queue the violation
        if (!this.isOnline) {
            this.violationQueue.push(violationData);
            this.warningCount++;
            this.saveViolationState();
            this.showWarning(this.warningCount, this.maxWarnings);
            this.updateWarningDisplay();
            return;
        }
        
        try {
            const response = await this.sendViolationToServer(violationData);
            
            if (response.success) {
                this.warningCount = response.warning_number;
                this.currentViolationId = response.violation_id;
                this.saveViolationState();
                
                // Check if auto-submission is required
                if (response.should_auto_submit) {
                    await this.autoSubmitExam();
                } else {
                    // Show warning modal
                    this.showWarning(this.warningCount, this.maxWarnings);
                    this.updateWarningDisplay();
                }
            }
        } catch (error) {
            console.error('Error recording violation:', error);
            
            // Handle specific error types
            if (error instanceof HttpError) {
                if (error.status === 401) {
                    // Authentication error - redirect to login
                    console.error('Authentication failed. Redirecting to login.');
                    window.location.href = '/users/student/login/';
                    return;
                } else if (error.status === 403) {
                    // Permission denied - attempt ownership issue
                    console.error('Permission denied. This attempt does not belong to you.');
                    this.stopMonitoring();
                    return;
                } else if (error.status === 400) {
                    // Bad request - exam already submitted
                    console.warn('Cannot record violation: exam already submitted');
                    this.stopMonitoring();
                    return;
                } else if (error.status === 404) {
                    // Attempt not found
                    console.error('Attempt not found');
                    this.stopMonitoring();
                    return;
                }
            }
            
            // For network errors or server errors, queue violation for retry
            this.violationQueue.push(violationData);
            this.warningCount++;
            this.saveViolationState();
            
            // Still show warning to student
            this.showWarning(this.warningCount, this.maxWarnings);
            this.updateWarningDisplay();
        }
    }
    
    /**
     * Record when student returns to exam tab
     * Requirements: 2.4
     */
    async recordReturn() {
        if (!this.currentViolationId) {
            return;
        }
        
        const returnData = {
            returned_at: new Date().toISOString()
        };
        
        try {
            // Note: This would require a separate endpoint if we want to track return times
            // For now, we'll just clear the current violation ID
            this.currentViolationId = null;
        } catch (error) {
            console.error('Error recording return:', error);
        }
    }
    
    /**
     * Send violation data to server via AJAX
     * Requirements: 2.1, 3.1, 8.1, 8.2, 8.5
     */
    async sendViolationToServer(violationData) {
        const url = `/attempts/student/attempts/${this.attemptId}/tab-switch/`;
        
        try {
            const response = await this.ajaxClient.post(url, violationData);
            const data = await response.json();
            
            // Validate response structure
            if (!data || typeof data !== 'object') {
                throw new Error('Invalid response format from server');
            }
            
            return data;
        } catch (error) {
            // Log error details for debugging
            console.error('Failed to send violation to server:', {
                url,
                attemptId: this.attemptId,
                error: error.message,
                status: error.status
            });
            
            // Re-throw to be handled by caller
            throw error;
        }
    }
    
    /**
     * Show warning modal to student
     * Requirements: 1.1, 1.2, 1.3, 1.5, 7.1, 7.2, 7.3, 7.4
     */
    showWarning(warningNumber, totalWarnings) {
        if (typeof Swal === 'undefined') {
            return;
        }

        let title, text, icon;

        if (warningNumber === 1) {
            title = '⚠️ Warning: Suspicious Activity Detected';
            text = `A tab switch, split screen, or window change was detected.\n\nThis is warning ${warningNumber} of ${totalWarnings}.\n\nKeep the exam in full screen and do not open other apps or tabs. After ${totalWarnings} warnings, your exam will be automatically submitted and flagged.`;
            icon = 'warning';
        } else if (warningNumber === 2) {
            title = '⚠️ Second Warning: Suspicious Activity';
            text = `Another violation was detected (tab switch, split screen, or app switch).\n\nThis is warning ${warningNumber} of ${totalWarnings}.\n\nOne more violation and your exam will be automatically submitted!`;
            icon = 'warning';
        } else if (warningNumber === 3) {
            title = '🚨 Final Warning!';
            text = `This is your FINAL warning (${warningNumber}/${totalWarnings}).\n\nAny further tab switch, split screen usage, or app switching will result in automatic submission and your exam will be flagged for potential cheating.`;
            icon = 'error';
        } else {
            title = '⚠️ Warning: Suspicious Activity Detected';
            text = `A violation was detected.\n\nWarning ${warningNumber} of ${totalWarnings}.`;
            icon = 'warning';
        }
        
        Swal.fire({
            title: title,
            text: text,
            icon: icon,
            confirmButtonText: 'OK, I Understand',
            confirmButtonColor: warningNumber === 3 ? '#dc2626' : '#f59e0b',
            allowOutsideClick: false,
            allowEscapeKey: false,
            backdrop: true
        });
    }
    
    /**
     * Auto-submit exam after 4th violation
     * Requirements: 1.4, 2.5, 8.1, 8.2, 8.5
     */
    async autoSubmitExam() {
        
        // Stop monitoring to prevent additional violations
        this.stopMonitoring();
        
        // Show auto-submission modal
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: '🚨 Exam Auto-Submitted',
                text: 'You have switched tabs too many times. Your exam has been automatically submitted and flagged for review by your teacher.',
                icon: 'error',
                showConfirmButton: false,
                allowOutsideClick: false,
                allowEscapeKey: false,
                backdrop: true,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
        }
        
        try {
            // Submit exam with auto_submit flag
            const url = `/attempts/student/attempts/${this.attemptId}/submit/`;
            const response = await this.ajaxClient.post(url, {
                auto_submit: true
            });
            
            const data = await response.json();
            
            // Validate response
            if (!data || typeof data !== 'object') {
                throw new Error('Invalid response format from server');
            }
            
            if (data.success) {
                // Clear saved state
                this.clearViolationState();
                
                // Redirect to submission confirmation page
                const redirectUrl = data.redirect_url || `/attempts/student/attempts/${this.attemptId}/submitted/`;
                window.location.href = redirectUrl;
            } else {
                throw new Error(data.error || 'Failed to auto-submit exam');
            }
        } catch (error) {
            console.error('Error auto-submitting exam:', error);
            
            // Log detailed error information
            console.error('Auto-submit error details:', {
                attemptId: this.attemptId,
                error: error.message,
                status: error.status,
                type: error.name
            });
            
            // Handle specific error types
            let errorMessage = 'Failed to submit your exam automatically. Please submit manually or contact your teacher.';
            
            if (error instanceof HttpError) {
                if (error.status === 401) {
                    errorMessage = 'Your session has expired. Please log in again.';
                    // Redirect to login after showing error
                    setTimeout(() => {
                        window.location.href = '/users/student/login/';
                    }, 3000);
                } else if (error.status === 403) {
                    errorMessage = 'Permission denied. Please contact your teacher.';
                } else if (error.status === 404) {
                    errorMessage = 'Exam attempt not found. Please contact your teacher.';
                } else if (error.status >= 500) {
                    errorMessage = 'Server error occurred. Please try submitting manually or contact your teacher.';
                }
            } else if (error.name === 'AbortError') {
                errorMessage = 'Request timed out. Please check your internet connection and try submitting manually.';
            }
            
            // Show error message
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: 'Submission Error',
                    text: errorMessage,
                    icon: 'error',
                    confirmButtonText: 'OK',
                    confirmButtonColor: '#dc2626'
                });
            }
        }
    }
    
    /**
     * Update warning count display on exam page
     * Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
     */
    updateWarningDisplay() {
        const warningBadge = document.getElementById('warning-count-badge');
        if (!warningBadge) {
            console.warn('Warning count badge element not found');
            return;
        }
        
        // Update badge text and styling based on warning count
        if (this.warningCount === 0) {
            warningBadge.textContent = `0/${this.maxWarnings}`;
            warningBadge.className = 'px-2 py-1 rounded text-sm font-semibold bg-green-100 text-green-800';
        } else if (this.warningCount === 1) {
            warningBadge.textContent = `${this.warningCount}/${this.maxWarnings}`;
            warningBadge.className = 'px-2 py-1 rounded text-sm font-semibold bg-yellow-100 text-yellow-800';
        } else if (this.warningCount === 2) {
            warningBadge.textContent = `${this.warningCount}/${this.maxWarnings}`;
            warningBadge.className = 'px-2 py-1 rounded text-sm font-semibold bg-orange-100 text-orange-800';
        } else if (this.warningCount >= 3) {
            warningBadge.textContent = `${this.warningCount}/${this.maxWarnings}`;
            warningBadge.className = 'px-2 py-1 rounded text-sm font-semibold bg-red-100 text-red-800 animate-pulse';
        }
    }
    
    /**
     * Save violation state to localStorage
     * Requirements: 3.4, 8.1, 8.2
     */
    saveViolationState() {
        const state = {
            warningCount: this.warningCount,
            currentViolationId: this.currentViolationId,
            timestamp: Date.now(),
            violationQueue: this.violationQueue
        };
        
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(state));
        } catch (error) {
            console.error('Error saving violation state:', error);
            
            // Handle specific localStorage errors
            if (error.name === 'QuotaExceededError') {
                console.error('localStorage quota exceeded. Clearing old data.');
                // Try to clear old tab monitor data
                try {
                    const keys = Object.keys(localStorage);
                    for (const key of keys) {
                        if (key.startsWith('tab_monitor_') && key !== this.storageKey) {
                            localStorage.removeItem(key);
                        }
                    }
                    // Try saving again
                    localStorage.setItem(this.storageKey, JSON.stringify(state));
                } catch (retryError) {
                    console.error('Failed to save state even after cleanup:', retryError);
                }
            } else if (error.name === 'SecurityError') {
                console.error('localStorage access denied (private browsing mode?)');
            }
        }
    }
    
    /**
     * Load violation state from localStorage
     * Requirements: 3.4, 8.1, 8.2
     */
    loadViolationState() {
        try {
            const savedState = localStorage.getItem(this.storageKey);
            if (savedState) {
                const state = JSON.parse(savedState);
                
                // Validate state structure
                if (!state || typeof state !== 'object') {
                    console.warn('Invalid state structure, clearing');
                    this.clearViolationState();
                    return;
                }
                
                // Validate state is recent (within last hour)
                const age = Date.now() - (state.timestamp || 0);
                if (age < 3600000) { // 1 hour
                    // Validate and sanitize state values
                    this.warningCount = typeof state.warningCount === 'number' ? state.warningCount : 0;
                    this.currentViolationId = state.currentViolationId || null;
                    this.violationQueue = Array.isArray(state.violationQueue) ? state.violationQueue : [];
                    
                    // Ensure warning count is within valid range
                    if (this.warningCount < 0 || this.warningCount > this.maxWarnings + 1) {
                        console.warn('Invalid warning count in saved state, resetting to 0');
                        this.warningCount = 0;
                    }
                } else {
                    // Saved state too old, clearing
                    this.clearViolationState();
                }
            }
        } catch (error) {
            console.error('Error loading violation state:', error);
            
            // Handle specific errors
            if (error instanceof SyntaxError) {
                console.error('Corrupted state data, clearing');
            } else if (error.name === 'SecurityError') {
                console.error('localStorage access denied');
            }
            
            // Clear corrupted state
            this.clearViolationState();
        }
    }
    
    /**
     * Clear violation state from localStorage
     */
    clearViolationState() {
        try {
            localStorage.removeItem(this.storageKey);
        } catch (error) {
            console.error('Error clearing violation state:', error);
        }
    }
    
    /**
     * Sync state with server
     * Requirements: 3.4, 8.1, 8.2, 8.5
     */
    async syncWithServer() {
        try {
            const url = `/attempts/student/attempts/${this.attemptId}/violations/`;
            const response = await this.ajaxClient.get(url);
            const data = await response.json();
            
            // Validate response structure
            if (!data || typeof data !== 'object') {
                console.warn('Invalid response format from server during sync');
                return;
            }
            
            if (data.violation_count !== undefined) {
                // Update local state to match server
                this.warningCount = data.violation_count;
                this.saveViolationState();
                this.updateWarningDisplay();
                
                // Check if already flagged (exam was auto-submitted)
                if (data.is_flagged) {
                    this.stopMonitoring();
                }
            }
        } catch (error) {
            console.error('Error syncing with server:', error);
            
            // Handle specific error types
            if (error instanceof HttpError) {
                if (error.status === 401) {
                    console.warn('Authentication failed during sync. User may need to log in again.');
                } else if (error.status === 403) {
                    console.warn('Permission denied during sync. Stopping monitoring.');
                    this.stopMonitoring();
                } else if (error.status === 404) {
                    console.warn('Attempt not found during sync. Stopping monitoring.');
                    this.stopMonitoring();
                }
            }
            
            // Continue with local state if sync fails
        }
    }
    
    /**
     * Handle online event - sync queued violations
     * Requirements: 8.5
     */
    async handleOnline() {
        this.isOnline = true;
        
        // Sync queued violations with error handling
        if (this.violationQueue.length > 0) {
            
            const queue = [...this.violationQueue];
            this.violationQueue = [];
            
            let syncedCount = 0;
            let failedCount = 0;
            
            for (const violation of queue) {
                try {
                    await this.sendViolationToServer(violation);
                    syncedCount++;
                } catch (error) {
                    console.error('Error syncing queued violation:', error);
                    failedCount++;
                    
                    // Re-queue if sync fails (unless it's a client error)
                    if (!(error instanceof HttpError) || error.status >= 500) {
                        this.violationQueue.push(violation);
                    } else {
                        // Don't re-queue client errors (4xx)
                        console.warn('Discarding queued violation due to client error:', error.status);
                    }
                }
            }
            
            this.saveViolationState();
        }
        
        // Sync with server to get accurate count
        try {
            await this.syncWithServer();
        } catch (error) {
            console.error('Error syncing with server after reconnection:', error);
            // Continue even if sync fails
        }
    }
    
    /**
     * Handle offline event
     * Requirements: 8.5
     */
    handleOffline() {
        this.isOnline = false;
    }
    
    /**
     * Show notice for unsupported browsers
     */
    showUnsupportedBrowserNotice() {
        if (typeof NotificationManager !== 'undefined') {
            NotificationManager.warning(
                'Your browser does not support tab monitoring. Please use a modern browser.',
                0 // Persistent
            );
        } else {
            console.warn('Browser does not support Page Visibility API');
        }
    }
    
    /**
     * Get current violation count
     * @returns {number} Current warning count
     */
    getCurrentViolationCount() {
        return this.warningCount;
    }
    
    /**
     * Check if monitoring is active
     * @returns {boolean} True if monitoring
     */
    isActive() {
        return this.isMonitoring;
    }
}

// Export to global scope
window.TabMonitor = TabMonitor;

// Initialize TabMonitor when page loads
document.addEventListener('DOMContentLoaded', function() {
    const timerElement = document.getElementById('timer');
    if (timerElement) {
        const attemptId = parseInt(timerElement.getAttribute('data-attempt-id'));
        
        if (attemptId) {
            const tabMonitor = new TabMonitor(attemptId);
            tabMonitor.startMonitoring();
            
            // Store reference globally for debugging
            window.tabMonitor = tabMonitor;
            
            // Stop monitoring when exam is submitted
            const submitButton = document.getElementById('confirm-submit-btn');
            if (submitButton) {
                submitButton.addEventListener('click', function() {
                    tabMonitor.stopMonitoring();
                });
            }
        }
    }
});
