/**
 * Dashboard Data Loader Utility
 * Handles loading and parsing of dashboard chart data from Django templates
 */

class DashboardDataLoader {
    /**
     * Initialize dashboard charts with data from JSON script tags
     * @param {Object} config - Configuration object with chart data element IDs
     */
    static initStudentDashboard(config = {}) {
        try {
            // Parse chart data from Django context with error tracking
            const scoreTrendData = this.parseJsonScript('score-trend-data');
            const typePerformanceData = this.parseJsonScript('type-performance-data');

            // Initialize student dashboard charts
            if (window.DashboardCharts) {
                const chartInstance = DashboardCharts.init({
                    scoreTrend: scoreTrendData,
                    typePerformance: typePerformanceData,
                    ...config
                });
                if (!chartInstance) {
                    throw new Error('Failed to initialize DashboardCharts instance');
                }
            } else {
                const error = new Error('DashboardCharts not loaded');
                this.handleDataError(error, {
                    operation: 'initStudentDashboard',
                    context: 'DashboardCharts class not available',
                    config: config
                });
            }
        } catch (error) {
            this.handleDataError(error, {
                operation: 'initStudentDashboard',
                context: 'Student dashboard initialization failed',
                config: config
            });
        }
    }

    /**
     * Initialize teacher dashboard charts with data from JSON script tags
     * @param {Object} config - Configuration object with additional data
     */
    static initTeacherDashboard(config = {}) {
        try {
            // Parse chart data from Django context with error tracking
            const examPerformanceData = this.parseJsonScript('exam-performance-data');
            const passingRateData = this.parseJsonScript('passing-rate-data');
            const dashboardConfig = this.parseJsonScript('dashboard-config-data');
            
            // Validate and prepare chart data
            const validatedConfig = this.validateChartData({
                examPerformance: examPerformanceData,
                passingRateData: passingRateData,
                totalPassers: dashboardConfig?.total_passers || config.totalPassers || 0,
                totalFailers: dashboardConfig?.total_failers || config.totalFailers || 0,
                ...config
            });
            
            // Initialize teacher dashboard charts
            if (window.DashboardCharts) {
                const chartInstance = DashboardCharts.init(validatedConfig);
                if (!chartInstance) {
                    throw new Error('Failed to initialize DashboardCharts instance');
                }
            } else {
                const error = new Error('DashboardCharts not loaded');
                this.handleDataError(error, {
                    operation: 'initTeacherDashboard',
                    context: 'DashboardCharts class not available',
                    config: validatedConfig
                });
            }
        } catch (error) {
            this.handleDataError(error, {
                operation: 'initTeacherDashboard',
                context: 'Teacher dashboard initialization failed',
                config: config
            });
        }
    }

    /**
     * Parse JSON data from script tag
     * @param {string} elementId - ID of the script element containing JSON data
     * @returns {Object|null} Parsed JSON data or null if not found
     */
    static parseJsonScript(elementId) {
        try {
            const element = document.getElementById(elementId);
            if (!element) {
                const error = new Error(`JSON script element with ID '${elementId}' not found`);
                this.handleDataError(error, {
                    operation: 'parseJsonScript',
                    elementId: elementId,
                    context: 'Element not found in DOM'
                });
                return null;
            }

            const textContent = element.textContent.trim();
            if (!textContent) {
                const error = new Error(`JSON script element '${elementId}' is empty`);
                this.handleDataError(error, {
                    operation: 'parseJsonScript',
                    elementId: elementId,
                    context: 'Element found but content is empty'
                });
                return null;
            }

            try {
                return JSON.parse(textContent);
            } catch (parseError) {
                // Enhanced JSON parsing error with content sample
                const contentSample = textContent.length > 100 ? 
                    textContent.substring(0, 100) + '...' : textContent;
                
                const error = new Error(`JSON parsing failed for element '${elementId}': ${parseError.message}`);
                this.handleDataError(error, {
                    operation: 'parseJsonScript',
                    elementId: elementId,
                    context: 'JSON parsing failed',
                    contentSample: contentSample,
                    originalError: parseError.message
                });
                return null;
            }
        } catch (error) {
            this.handleDataError(error, {
                operation: 'parseJsonScript',
                elementId: elementId,
                context: 'Unexpected error during JSON parsing'
            });
            return null;
        }
    }

    /**
     * Validate chart data to prevent NaN errors
     * @param {Object} data - Chart data to validate
     * @returns {Object} Validated chart data
     */
    static validateChartData(data) {
        // Use DashboardCharts validation if available
        if (window.DashboardCharts) {
            const chartInstance = new window.DashboardCharts();
            return chartInstance.validateChartConfig(data);
        }
        
        // Fallback validation
        const validated = { ...data };
        
        // Validate exam performance data
        if (validated.examPerformance && typeof validated.examPerformance === 'object') {
            for (const [examTitle, examData] of Object.entries(validated.examPerformance)) {
                if (examData && typeof examData === 'object') {
                    validated.examPerformance[examTitle] = {
                        passers: this.validateNumericValue(examData.passers, 0),
                        failers: this.validateNumericValue(examData.failers, 0),
                        total: this.validateNumericValue(examData.total, 0)
                    };
                }
            }
        } else {
            validated.examPerformance = {};
        }
        
        // Validate passing rate data
        if (validated.passingRateData && typeof validated.passingRateData === 'object') {
            validated.passingRateData = {
                sections: Array.isArray(validated.passingRateData.sections) ? validated.passingRateData.sections : [],
                subjects: Array.isArray(validated.passingRateData.subjects) ? validated.passingRateData.subjects : [],
                data: validated.passingRateData.data && typeof validated.passingRateData.data === 'object' ? validated.passingRateData.data : {}
            };
            
            // Validate numeric data in passing rate data
            if (validated.passingRateData.data) {
                for (const [subject, values] of Object.entries(validated.passingRateData.data)) {
                    if (Array.isArray(values)) {
                        validated.passingRateData.data[subject] = values.map(val => this.validateNumericValue(val, 0));
                    }
                }
            }
        } else {
            validated.passingRateData = { sections: [], subjects: [], data: {} };
        }
        
        // Validate total counts
        validated.totalPassers = this.validateNumericValue(validated.totalPassers, 0);
        validated.totalFailers = this.validateNumericValue(validated.totalFailers, 0);
        
        return validated;
    }

    /**
     * Validate a numeric value and provide fallback
     * @param {*} value - Value to validate
     * @param {number} fallback - Fallback value if invalid
     * @returns {number} Valid numeric value
     */
    static validateNumericValue(value, fallback = 0) {
        const num = parseFloat(value);
        return isNaN(num) || !isFinite(num) ? fallback : num;
    }

    /**
     * Get fallback data structure for empty or invalid chart data
     * @param {string} dataType - Type of data (examPerformance, passingRateData, etc.)
     * @returns {Object} Fallback data structure
     */
    static getFallbackData(dataType) {
        const fallbacks = {
            examPerformance: {},
            passingRateData: { 
                sections: [], 
                subjects: [], 
                data: {} 
            },
            scoreTrend: [],
            typePerformance: {},
            dashboardConfig: {
                total_students: 0,
                total_exams: 0,
                total_passers: 0,
                total_failers: 0
            }
        };

        return fallbacks[dataType] || null;
    }

    /**
     * Parse JSON data from script tag with fallback support
     * @param {string} elementId - ID of the script element containing JSON data
     * @param {string} dataType - Type of data for fallback (optional)
     * @returns {Object|null} Parsed JSON data, fallback data, or null
     */
    static parseJsonScriptWithFallback(elementId, dataType = null) {
        const data = this.parseJsonScript(elementId);
        
        // If parsing failed and we have a data type, return fallback
        if (data === null && dataType) {
            console.warn(`Using fallback data for '${elementId}' (${dataType})`);
            return this.getFallbackData(dataType);
        }
        
        return data;
    }

    /**
     * Detect Chart.js library availability and version
     * @returns {Object} Library detection result
     */
    static detectChartLibrary() {
        const detection = {
            available: false,
            version: null,
            globalChart: false,
            error: null
        };

        try {
            // Check if Chart is available globally
            if (typeof Chart !== 'undefined') {
                detection.available = true;
                detection.globalChart = true;
                
                // Try to get version
                if (Chart.version) {
                    detection.version = Chart.version;
                } else if (Chart.Chart && Chart.Chart.version) {
                    detection.version = Chart.Chart.version;
                }
            } else {
                detection.error = 'Chart.js not found in global scope';
            }

            // Additional checks for Chart.js functionality
            if (detection.available) {
                try {
                    // Test basic Chart.js functionality
                    const testCanvas = document.createElement('canvas');
                    const testCtx = testCanvas.getContext('2d');
                    
                    // Try to create a minimal chart instance (will be destroyed immediately)
                    const testChart = new Chart(testCtx, {
                        type: 'bar',
                        data: { labels: [], datasets: [] },
                        options: { responsive: false, animation: false }
                    });
                    
                    testChart.destroy();
                    detection.functional = true;
                } catch (functionalError) {
                    detection.available = false;
                    detection.functional = false;
                    detection.error = `Chart.js not functional: ${functionalError.message}`;
                }
            }
        } catch (error) {
            detection.available = false;
            detection.error = `Chart.js detection failed: ${error.message}`;
        }

        return detection;
    }

    /**
     * Initialize dashboard with Chart.js library detection and fallback
     * @param {string} dashboardType - Type of dashboard ('teacher' or 'student')
     * @param {Object} config - Configuration object
     */
    static initDashboardWithFallback(dashboardType, config = {}) {
        try {
            // Detect Chart.js library
            const libraryDetection = this.detectChartLibrary();
            
            if (!libraryDetection.available) {
                const error = new Error(libraryDetection.error || 'Chart.js library not available');
                this.handleDataError(error, {
                    operation: 'libraryDetection',
                    context: 'Chart.js library check failed',
                    dashboardType: dashboardType,
                    detection: libraryDetection
                });
                
                // Show library fallback UI
                this.showLibraryFallback(dashboardType);
                return false;
            }

            // Log successful detection
            console.log(`Chart.js detected: version ${libraryDetection.version || 'unknown'}`);

            // Initialize appropriate dashboard
            if (dashboardType === 'teacher') {
                this.initTeacherDashboardWithFallback(config);
            } else if (dashboardType === 'student') {
                this.initStudentDashboardWithFallback(config);
            } else {
                throw new Error(`Unknown dashboard type: ${dashboardType}`);
            }

            return true;
        } catch (error) {
            this.handleDataError(error, {
                operation: 'initDashboardWithFallback',
                context: 'Dashboard initialization with fallback failed',
                dashboardType: dashboardType,
                config: config
            });
            return false;
        }
    }

    /**
     * Initialize teacher dashboard with fallback data support
     * @param {Object} config - Configuration object with additional data
     */
    static initTeacherDashboardWithFallback(config = {}) {
        try {
            // Parse chart data with fallback support
            const examPerformanceData = this.parseJsonScriptWithFallback('exam-performance-data', 'examPerformance');
            const passingRateData = this.parseJsonScriptWithFallback('passing-rate-data', 'passingRateData');
            const dashboardConfig = this.parseJsonScriptWithFallback('dashboard-config-data', 'dashboardConfig');
            
            // Validate and prepare chart data with fallbacks
            const validatedConfig = this.validateChartDataWithFallback({
                examPerformance: examPerformanceData,
                passingRateData: passingRateData,
                totalPassers: dashboardConfig?.total_passers || config.totalPassers || 0,
                totalFailers: dashboardConfig?.total_failers || config.totalFailers || 0,
                ...config
            });
            
            // Initialize teacher dashboard charts
            if (window.DashboardCharts) {
                const chartInstance = DashboardCharts.init(validatedConfig);
                if (!chartInstance) {
                    throw new Error('Failed to initialize DashboardCharts instance');
                }
                return chartInstance;
            } else {
                throw new Error('DashboardCharts class not available');
            }
        } catch (error) {
            this.handleDataError(error, {
                operation: 'initTeacherDashboardWithFallback',
                context: 'Teacher dashboard initialization with fallback failed',
                config: config
            });
            
            // Show fallback UI for teacher dashboard
            this.showDashboardFallback('teacher');
            return null;
        }
    }

    /**
     * Initialize student dashboard with fallback data support
     * @param {Object} config - Configuration object with chart data element IDs
     */
    static initStudentDashboardWithFallback(config = {}) {
        try {
            // Parse chart data with fallback support
            const scoreTrendData = this.parseJsonScriptWithFallback('score-trend-data', 'scoreTrend');
            const typePerformanceData = this.parseJsonScriptWithFallback('type-performance-data', 'typePerformance');

            // Initialize student dashboard charts
            if (window.DashboardCharts) {
                const chartInstance = DashboardCharts.init({
                    scoreTrend: scoreTrendData,
                    typePerformance: typePerformanceData,
                    ...config
                });
                if (!chartInstance) {
                    throw new Error('Failed to initialize DashboardCharts instance');
                }
                return chartInstance;
            } else {
                throw new Error('DashboardCharts class not available');
            }
        } catch (error) {
            this.handleDataError(error, {
                operation: 'initStudentDashboardWithFallback',
                context: 'Student dashboard initialization with fallback failed',
                config: config
            });
            
            // Show fallback UI for student dashboard
            this.showDashboardFallback('student');
            return null;
        }
    }

    /**
     * Validate chart data with fallback support
     * @param {Object} data - Chart data to validate
     * @returns {Object} Validated chart data with fallbacks applied
     */
    static validateChartDataWithFallback(data) {
        try {
            // Use DashboardCharts validation if available
            if (window.DashboardCharts) {
                const chartInstance = new window.DashboardCharts();
                return chartInstance.validateChartConfig(data);
            }
            
            // Fallback validation with enhanced error recovery
            return this.validateChartDataFallback(data);
        } catch (error) {
            console.warn('Chart data validation failed, using fallback data:', error);
            return this.getDefaultChartConfig();
        }
    }

    /**
     * Fallback chart data validation when DashboardCharts is not available
     * @param {Object} data - Chart data to validate
     * @returns {Object} Validated chart data
     */
    static validateChartDataFallback(data) {
        const validated = { ...data };
        
        // Validate exam performance data with fallback
        if (validated.examPerformance && typeof validated.examPerformance === 'object') {
            for (const [examTitle, examData] of Object.entries(validated.examPerformance)) {
                if (examData && typeof examData === 'object') {
                    validated.examPerformance[examTitle] = {
                        passers: this.validateNumericValue(examData.passers, 0),
                        failers: this.validateNumericValue(examData.failers, 0),
                        total: this.validateNumericValue(examData.total, 0)
                    };
                } else {
                    // Remove invalid exam data
                    delete validated.examPerformance[examTitle];
                }
            }
        } else {
            validated.examPerformance = this.getFallbackData('examPerformance');
        }
        
        // Validate passing rate data with fallback
        if (validated.passingRateData && typeof validated.passingRateData === 'object') {
            validated.passingRateData = {
                sections: Array.isArray(validated.passingRateData.sections) ? 
                    validated.passingRateData.sections : [],
                subjects: Array.isArray(validated.passingRateData.subjects) ? 
                    validated.passingRateData.subjects : [],
                data: validated.passingRateData.data && typeof validated.passingRateData.data === 'object' ? 
                    validated.passingRateData.data : {}
            };
            
            // Validate numeric data in passing rate data
            if (validated.passingRateData.data) {
                for (const [subject, values] of Object.entries(validated.passingRateData.data)) {
                    if (Array.isArray(values)) {
                        validated.passingRateData.data[subject] = values.map(val => 
                            this.validateNumericValue(val, 0));
                    } else {
                        // Remove invalid subject data
                        delete validated.passingRateData.data[subject];
                    }
                }
            }
        } else {
            validated.passingRateData = this.getFallbackData('passingRateData');
        }
        
        // Validate score trend data with fallback
        if (Array.isArray(validated.scoreTrend)) {
            validated.scoreTrend = validated.scoreTrend.filter(item => 
                item && typeof item === 'object' && typeof item.percentage === 'number');
        } else {
            validated.scoreTrend = this.getFallbackData('scoreTrend');
        }
        
        // Validate type performance data with fallback
        if (validated.typePerformance && typeof validated.typePerformance === 'object') {
            for (const [type, score] of Object.entries(validated.typePerformance)) {
                if (typeof score !== 'number' || isNaN(score)) {
                    delete validated.typePerformance[type];
                }
            }
        } else {
            validated.typePerformance = this.getFallbackData('typePerformance');
        }
        
        // Validate total counts with fallback
        validated.totalPassers = this.validateNumericValue(validated.totalPassers, 0);
        validated.totalFailers = this.validateNumericValue(validated.totalFailers, 0);
        
        return validated;
    }

    /**
     * Get default chart configuration with fallback data
     * @returns {Object} Default configuration object
     */
    static getDefaultChartConfig() {
        return {
            examPerformance: this.getFallbackData('examPerformance'),
            totalPassers: 0,
            totalFailers: 0,
            passingRateData: this.getFallbackData('passingRateData'),
            scoreTrend: this.getFallbackData('scoreTrend'),
            typePerformance: this.getFallbackData('typePerformance')
        };
    }

    /**
     * Show library fallback UI when Chart.js is not available
     * @param {string} dashboardType - Type of dashboard ('teacher' or 'student')
     */
    static showLibraryFallback(dashboardType) {
        const chartContainers = dashboardType === 'teacher' ? 
            ['examPerformanceChart', 'overallDistributionChart', 'passingRateBySubjectChart'] :
            ['scoreTrendChart', 'typePerformanceChart'];
        
        chartContainers.forEach(canvasId => {
            const canvas = document.getElementById(canvasId);
            if (canvas && canvas.parentElement) {
                const container = canvas.parentElement;
                canvas.style.display = 'none';
                
                const fallbackMessage = document.createElement('div');
                fallbackMessage.className = 'chart-library-fallback p-6 text-center text-amber-600 bg-amber-50 rounded-lg border border-amber-200';
                fallbackMessage.innerHTML = `
                    <div class="text-sm">
                        <svg class="mx-auto h-10 w-10 text-amber-500 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <p class="font-medium text-amber-800 mb-2">Chart library unavailable</p>
                        <p class="text-xs text-amber-700 mb-3">Charts cannot be displayed at this time</p>
                        <button class="text-xs bg-amber-100 hover:bg-amber-200 text-amber-800 px-3 py-1 rounded border border-amber-300 transition-colors duration-200" 
                                onclick="window.location.reload()">
                            Reload Page
                        </button>
                    </div>
                `;
                container.appendChild(fallbackMessage);
            }
        });
    }

    /**
     * Show dashboard fallback UI when initialization fails
     * @param {string} dashboardType - Type of dashboard ('teacher' or 'student')
     */
    static showDashboardFallback(dashboardType) {
        const message = dashboardType === 'teacher' ? 
            'Teacher dashboard temporarily unavailable' :
            'Student dashboard temporarily unavailable';
        
        const chartContainers = dashboardType === 'teacher' ? 
            ['examPerformanceChart', 'overallDistributionChart', 'passingRateBySubjectChart'] :
            ['scoreTrendChart', 'typePerformanceChart'];
        
        chartContainers.forEach(canvasId => {
            const canvas = document.getElementById(canvasId);
            if (canvas && canvas.parentElement) {
                const container = canvas.parentElement;
                canvas.style.display = 'none';
                
                const fallbackMessage = document.createElement('div');
                fallbackMessage.className = 'chart-dashboard-fallback p-6 text-center text-blue-600 bg-blue-50 rounded-lg border border-blue-200';
                fallbackMessage.innerHTML = `
                    <div class="text-sm">
                        <svg class="mx-auto h-10 w-10 text-blue-500 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <p class="font-medium text-blue-800 mb-2">${message}</p>
                        <p class="text-xs text-blue-700 mb-3">Please try refreshing the page</p>
                        <button class="text-xs bg-blue-100 hover:bg-blue-200 text-blue-800 px-3 py-1 rounded border border-blue-300 transition-colors duration-200" 
                                onclick="window.location.reload()">
                            Refresh Page
                        </button>
                    </div>
                `;
                container.appendChild(fallbackMessage);
            }
        });
    }

    /**
     * Handle data loading errors with detailed logging and context tracking
     * @param {Error} error - The error that occurred
     * @param {Object} context - Additional context information
     */
    static handleDataError(error, context = {}) {
        // Use DashboardCharts centralized error handler if available
        if (window.DashboardCharts && typeof window.DashboardCharts.handleChartError === 'function') {
            return window.DashboardCharts.handleChartError(error, {
                ...context,
                component: 'DashboardDataLoader'
            });
        }

        // Fallback error handling if DashboardCharts is not available
        const errorInfo = {
            timestamp: new Date().toISOString(),
            message: error.message,
            stack: error.stack,
            context: {
                ...context,
                component: 'DashboardDataLoader',
                userAgent: navigator.userAgent,
                url: window.location.href
            }
        };
        
        console.error('Dashboard Data Loading Error:', errorInfo);
        
        // Show user-friendly fallback if possible
        if (context.elementId && context.elementId.includes('chart')) {
            this.showDataErrorFallback(context.elementId);
        }
        
        // Optional: Send to error tracking service
        if (window.errorTracker) {
            try {
                window.errorTracker.log(errorInfo);
            } catch (trackingError) {
                console.warn('Failed to send error to tracking service:', trackingError);
            }
        }

        return errorInfo;
    }

    /**
     * Show fallback UI for data loading errors
     * @param {string} elementId - ID of the element that failed to load
     */
    static showDataErrorFallback(elementId) {
        const element = document.getElementById(elementId);
        if (element && element.parentElement) {
            const container = element.parentElement;
            const errorMessage = document.createElement('div');
            errorMessage.className = 'chart-error-state p-4 text-center text-gray-500';
            errorMessage.innerHTML = `
                <div class="text-sm">
                    <svg class="mx-auto h-8 w-8 text-gray-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                    <p>Unable to load chart data</p>
                    <p class="text-xs mt-1">Please refresh the page or contact support</p>
                </div>
            `;
            container.appendChild(errorMessage);
        }
    }

    /**
     * Set up data attributes for URL passing to JavaScript
     * @param {Object} urlMappings - Object mapping element IDs to URL data attributes
     */
    static setupUrlDataAttributes(urlMappings) {
        Object.entries(urlMappings).forEach(([elementId, urls]) => {
            const element = document.getElementById(elementId);
            if (element) {
                Object.entries(urls).forEach(([key, url]) => {
                    element.dataset[key] = url;
                });
            }
        });
    }

    /**
     * Parse and apply configuration data to components
     * @param {string} configElementId - ID of the script element containing configuration JSON
     * @param {Function} applyFunction - Function to apply the configuration
     */
    static applyConfiguration(configElementId, applyFunction) {
        try {
            const config = this.parseJsonScript(configElementId);
            if (config && typeof applyFunction === 'function') {
                applyFunction(config);
            }
        } catch (error) {
            console.error(`Error applying configuration from '${configElementId}':`, error);
        }
    }

    /**
     * Generic data loader for any JSON script tag
     * @param {string} elementId - ID of the script element containing JSON data
     * @param {Function} callback - Callback function to handle the parsed data
     */
    static loadJsonData(elementId, callback) {
        try {
            const data = this.parseJsonScript(elementId);
            if (data && typeof callback === 'function') {
                callback(data);
            }
        } catch (error) {
            console.error(`Error loading JSON data from '${elementId}':`, error);
        }
    }

    /**
     * Initialize dashboard with enhanced error handling and validation
     * @param {string} dashboardType - Type of dashboard ('teacher' or 'student')
     * @param {Object} config - Configuration object
     * @param {Object} templateContext - Template-specific context for debugging
     */
    static initDashboardWithEnhancedErrorHandling(dashboardType, config = {}, templateContext = {}) {
        try {
            // Validate dashboard type
            if (!['teacher', 'student'].includes(dashboardType)) {
                throw new Error(`Invalid dashboard type: ${dashboardType}`);
            }

            // Validate required data elements exist in DOM
            const requiredElements = dashboardType === 'teacher' 
                ? ['exam-performance-data', 'passing-rate-data', 'dashboard-config-data']
                : ['score-trend-data', 'type-performance-data'];
            
            const missingElements = requiredElements.filter(id => !document.getElementById(id));
            
            if (missingElements.length > 0) {
                console.warn(`Missing required data elements for ${dashboardType} dashboard:`, missingElements);
            }

            // Enhanced error context for debugging
            const errorContext = {
                timestamp: new Date().toISOString(),
                dashboardType: dashboardType,
                userAgent: navigator.userAgent,
                url: window.location.href,
                availableElements: requiredElements.map(id => ({ 
                    id, 
                    exists: !!document.getElementById(id),
                    hasContent: document.getElementById(id)?.textContent?.trim().length > 0
                })),
                libraryStatus: {
                    chartLibraryAvailable: typeof Chart !== 'undefined',
                    dashboardDataLoaderAvailable: typeof DashboardDataLoader !== 'undefined',
                    dashboardChartsAvailable: typeof DashboardCharts !== 'undefined'
                },
                templateContext: templateContext,
                config: config
            };

            // Attempt primary initialization
            const success = this.initDashboardWithFallback(dashboardType, config);
            
            if (!success) {
                console.warn(`${dashboardType} dashboard initialization failed, attempting fallback methods`);
                
                // Attempt alternative initialization methods
                const fallbackMethod = dashboardType === 'teacher' 
                    ? 'initTeacherDashboard' 
                    : 'initStudentDashboard';
                
                if (window.DashboardDataLoader && typeof DashboardDataLoader[fallbackMethod] === 'function') {
                    console.log(`Attempting fallback initialization method: ${fallbackMethod}`);
                    try {
                        DashboardDataLoader[fallbackMethod](config);
                        console.log(`Fallback initialization successful for ${dashboardType} dashboard`);
                        return true;
                    } catch (fallbackError) {
                        console.error(`Fallback initialization failed for ${dashboardType} dashboard:`, fallbackError);
                        this.handleTemplateInitializationError(new Error(`Both primary and fallback initialization failed: ${fallbackError.message}`), errorContext);
                        return false;
                    }
                } else {
                    this.handleTemplateInitializationError(new Error('No fallback initialization method available'), errorContext);
                    return false;
                }
            } else {
                console.log(`${dashboardType} dashboard initialized successfully`);
                return true;
            }
        } catch (error) {
            const errorContext = {
                timestamp: new Date().toISOString(),
                dashboardType: dashboardType,
                userAgent: navigator.userAgent,
                url: window.location.href,
                libraryStatus: {
                    chartLibraryAvailable: typeof Chart !== 'undefined',
                    dashboardDataLoaderAvailable: typeof DashboardDataLoader !== 'undefined',
                    dashboardChartsAvailable: typeof DashboardCharts !== 'undefined'
                },
                templateContext: templateContext,
                config: config
            };
            
            this.handleTemplateInitializationError(error, errorContext);
            return false;
        }
    }

    /**
     * Handle template initialization errors with comprehensive fallback UI
     * @param {Error} error - The error that occurred
     * @param {Object} errorContext - Detailed error context
     */
    static handleTemplateInitializationError(error, errorContext) {
        console.error(`Dashboard initialization error for ${errorContext.dashboardType}:`, error);
        console.error('Error context:', errorContext);
        
        // Show appropriate fallback UI based on available methods
        if (window.DashboardDataLoader) {
            if (typeof DashboardDataLoader.showDashboardFallback === 'function') {
                DashboardDataLoader.showDashboardFallback(errorContext.dashboardType);
            } else if (typeof DashboardDataLoader.showLibraryFallback === 'function') {
                DashboardDataLoader.showLibraryFallback(errorContext.dashboardType);
            } else {
                this.showBasicErrorFallback(errorContext.dashboardType);
            }
        } else {
            this.showBasicErrorFallback(errorContext.dashboardType);
        }
        
        // Send error to tracking service if available
        if (window.errorTracker && typeof window.errorTracker.log === 'function') {
            try {
                window.errorTracker.log({
                    error: error.message,
                    stack: error.stack,
                    context: errorContext,
                    component: 'DashboardTemplateInitialization'
                });
            } catch (trackingError) {
                console.warn('Failed to send error to tracking service:', trackingError);
            }
        }
    }

    /**
     * Show basic error fallback UI when other methods are not available
     * @param {string} dashboardType - Type of dashboard ('teacher' or 'student')
     */
    static showBasicErrorFallback(dashboardType) {
        const chartContainers = dashboardType === 'teacher' 
            ? ['examPerformanceChart', 'overallDistributionChart', 'passingRateBySubjectChart']
            : ['scoreTrendChart', 'typePerformanceChart'];
        
        chartContainers.forEach(canvasId => {
            const canvas = document.getElementById(canvasId);
            if (canvas && canvas.parentElement) {
                const container = canvas.parentElement;
                canvas.style.display = 'none';
                
                // Check if error message already exists
                if (container.querySelector('.chart-initialization-error')) {
                    return;
                }
                
                const errorDiv = document.createElement('div');
                errorDiv.className = 'chart-initialization-error p-6 text-center text-red-600 bg-red-50 rounded-lg border border-red-200';
                errorDiv.innerHTML = `
                    <div class="text-sm">
                        <svg class="mx-auto h-10 w-10 text-red-500 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <p class="font-medium text-red-800 mb-2">Chart initialization failed</p>
                        <p class="text-xs text-red-700 mb-3">Unable to load ${dashboardType} dashboard charts</p>
                        <button class="text-xs bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded border border-red-300 transition-colors duration-200" 
                                onclick="window.location.reload()">
                            Reload Page
                        </button>
                    </div>
                `;
                container.appendChild(errorDiv);
            }
        });
    }
}

// Make available globally
window.DashboardDataLoader = DashboardDataLoader;