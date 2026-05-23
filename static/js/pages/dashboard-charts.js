/**
 * Dashboard Charts Module
 * Handles chart initialization and management for teacher and student dashboards
 * Extracted from teacher_dashboard.html and student_dashboard.html templates
 * 
 * @author ExamMaker Development Team
 * @version 1.0.0
 * @since 2024
 * 
 * Requirements: 10.1, 10.2, 10.4 - Coding standards compliance
 */

class DashboardCharts {
    constructor() {
        this.charts = new Map();
        this.resizeTimeout = null;
        this.setupResizeHandler();
    }

    /**
     * Initialize dashboard charts based on provided configuration
     * @param {Object} config - Chart configuration object
     */
    static init(config = {}) {
        try {
            // Enhanced Chart.js library detection
            const libraryDetection = this.detectAndValidateChartLibrary();
            
            if (!libraryDetection.available || !libraryDetection.functional) {
                const error = new Error(libraryDetection.error || 'Chart.js library not available or functional');
                this.handleChartError(error, {
                    operation: 'libraryLoading',
                    component: 'DashboardCharts',
                    data: config,
                    detection: libraryDetection
                });
                this.showLibraryError();
                return null;
            }

            // Log successful library detection
            console.log(`Chart.js initialized successfully: v${libraryDetection.version || 'unknown'}`);
            
            const instance = new DashboardCharts();
            
            // Initialize teacher dashboard charts if data is available
            if (config.examPerformance || config.totalPassers !== undefined || config.passingRateData) {
                try {
                    instance.initTeacherCharts(config);
                } catch (error) {
                    this.handleChartError(error, {
                        operation: 'teacherChartInitialization',
                        component: 'DashboardCharts',
                        data: config
                    });
                }
            }
            
            // Initialize student dashboard charts if data is available
            if (config.scoreTrend || config.typePerformance) {
                try {
                    instance.initStudentCharts(config);
                } catch (error) {
                    this.handleChartError(error, {
                        operation: 'studentChartInitialization',
                        component: 'DashboardCharts',
                        data: config
                    });
                }
            }
            
            return instance;
        } catch (error) {
            this.handleChartError(error, {
                operation: 'dashboardInitialization',
                component: 'DashboardCharts',
                data: config
            });
            return null;
        }
    }

    /**
     * Enhanced Chart.js library detection and fallback handling
     * @returns {Object} Detection result with detailed information
     */
    static detectAndValidateChartLibrary() {
        const detection = {
            available: false,
            version: null,
            functional: false,
            error: null,
            capabilities: {
                canCreateChart: false,
                hasRequiredTypes: false,
                hasPlugins: false
            }
        };

        try {
            // Check if Chart is available globally
            if (typeof Chart === 'undefined') {
                detection.error = 'Chart.js not found in global scope';
                return detection;
            }

            detection.available = true;

            // Get version information
            try {
                if (Chart.version) {
                    detection.version = Chart.version;
                } else if (Chart.Chart && Chart.Chart.version) {
                    detection.version = Chart.Chart.version;
                }
            } catch (versionError) {
                console.warn('Could not determine Chart.js version:', versionError);
            }

            // Test Chart.js functionality
            try {
                // Create a temporary canvas for testing
                const testCanvas = document.createElement('canvas');
                testCanvas.width = 100;
                testCanvas.height = 100;
                const testCtx = testCanvas.getContext('2d');
                
                if (!testCtx) {
                    detection.error = 'Canvas context not available';
                    return detection;
                }

                // Test basic chart creation
                const testChart = new Chart(testCtx, {
                    type: 'bar',
                    data: { 
                        labels: ['Test'], 
                        datasets: [{ 
                            label: 'Test', 
                            data: [1],
                            backgroundColor: 'rgba(0,0,0,0.1)'
                        }] 
                    },
                    options: { 
                        responsive: false, 
                        animation: false,
                        plugins: { legend: { display: false } },
                        scales: { x: { display: false }, y: { display: false } }
                    }
                });
                
                detection.capabilities.canCreateChart = true;
                
                // Test chart destruction
                testChart.destroy();
                
                detection.functional = true;
            } catch (functionalError) {
                detection.error = `Chart.js functionality test failed: ${functionalError.message}`;
                return detection;
            }

            // Test required chart types
            try {
                const requiredTypes = ['bar', 'doughnut', 'line'];
                const availableTypes = Chart.registry ? 
                    Object.keys(Chart.registry.controllers) : 
                    ['bar', 'doughnut', 'line']; // Assume basic types are available

                detection.capabilities.hasRequiredTypes = requiredTypes.every(type => 
                    availableTypes.includes(type) || Chart.controllers[type]);
                
                if (!detection.capabilities.hasRequiredTypes) {
                    detection.error = 'Required chart types not available';
                }
            } catch (typeError) {
                console.warn('Could not verify chart types:', typeError);
                detection.capabilities.hasRequiredTypes = true; // Assume they're available
            }

            // Test plugin system
            try {
                detection.capabilities.hasPlugins = !!(Chart.plugins || Chart.pluginService);
            } catch (pluginError) {
                console.warn('Could not verify plugin system:', pluginError);
                detection.capabilities.hasPlugins = false;
            }

        } catch (error) {
            detection.error = `Chart.js detection failed: ${error.message}`;
        }

        return detection;
    }

    /**
     * Show enhanced library error with detailed information
     */
    static showLibraryError() {
        const detection = this.detectAndValidateChartLibrary();
        
        const chartContainers = [
            'examPerformanceChart',
            'overallDistributionChart', 
            'passingRateBySubjectChart',
            'scoreTrendChart',
            'typePerformanceChart'
        ];
        
        chartContainers.forEach(canvasId => {
            const canvas = document.getElementById(canvasId);
            if (canvas && canvas.parentElement) {
                const container = canvas.parentElement;
                canvas.style.display = 'none';
                
                // Determine error message based on detection results
                let errorTitle = 'Chart library not loaded';
                let errorDetails = 'Please refresh the page or contact support';
                let errorClass = 'text-red-500 bg-red-50 border-red-200';
                
                if (detection.available && !detection.functional) {
                    errorTitle = 'Chart library not functional';
                    errorDetails = `Chart.js v${detection.version || 'unknown'} loaded but not working properly`;
                } else if (detection.available && detection.functional && !detection.capabilities.hasRequiredTypes) {
                    errorTitle = 'Chart types unavailable';
                    errorDetails = 'Required chart types are not available in this Chart.js version';
                    errorClass = 'text-amber-500 bg-amber-50 border-amber-200';
                }
                
                const errorMessage = document.createElement('div');
                errorMessage.className = `chart-library-error p-4 text-center ${errorClass} rounded-lg border`;
                errorMessage.innerHTML = `
                    <div class="text-sm">
                        <svg class="mx-auto h-8 w-8 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <p class="font-medium mb-1">${errorTitle}</p>
                        <p class="text-xs mb-3">${errorDetails}</p>
                        ${detection.error ? `<p class="text-xs mb-3 font-mono">${detection.error}</p>` : ''}
                        <button class="chart-error-retry-btn text-xs px-3 py-1 rounded border transition-colors duration-200" 
                                onclick="window.location.reload()">
                            Refresh Page
                        </button>
                    </div>
                `;
                container.appendChild(errorMessage);
            }
        });

        // Log detailed detection information for debugging
        console.group('Chart.js Library Detection Results');
        console.log('Available:', detection.available);
        console.log('Version:', detection.version);
        console.log('Functional:', detection.functional);
        console.log('Capabilities:', detection.capabilities);
        if (detection.error) {
            console.error('Error:', detection.error);
        }
        console.groupEnd();
    }

    /**
     * Initialize teacher dashboard charts
     * @param {Object} config - Configuration object containing chart data
     */
    initTeacherCharts(config) {
        // Validate the entire configuration first
        const validatedConfig = this.validateChartConfig(config);
        const { examPerformance, totalPassers, totalFailers, passingRateData } = validatedConfig;
        
        // Initialize Pass/Fail by Exam Chart
        if (examPerformance && Object.keys(examPerformance).length > 0) {
            this.createExamPerformanceChart(examPerformance);
        } else {
            this.showEmptyState('examPerformanceChart');
        }
        
        // Initialize Overall Distribution Chart
        if (totalPassers !== null && totalFailers !== null && (totalPassers > 0 || totalFailers > 0)) {
            this.createOverallDistributionChart(totalPassers, totalFailers);
        } else {
            this.showEmptyState('overallDistributionChart');
        }
        
        // Initialize Passing Rate by Subject Chart
        if (passingRateData && passingRateData.subjects && passingRateData.subjects.length > 0) {
            this.createPassingRateBySubjectChart(passingRateData);
        } else {
            this.showEmptyState('passingRateBySubjectChart');
        }
    }

    /**
     * Validate numeric data to prevent NaN errors
     * @param {*} value - Value to validate
     * @param {string} fieldName - Name of the field for error reporting
     * @param {Object} options - Validation options
     * @param {boolean} options.allowNegative - Whether to allow negative values (default: false)
     * @param {number} options.min - Minimum allowed value
     * @param {number} options.max - Maximum allowed value
     * @param {number} options.fallback - Fallback value for invalid data (default: null)
     * @returns {number|null} Valid number or null if invalid
     */
    validateNumericData(value, fieldName, options = {}) {
        const { allowNegative = false, min, max, fallback = null } = options;
        
        // Check for null/undefined
        if (value === null || value === undefined) {
            console.warn(`Chart data field '${fieldName}' is null or undefined`);
            return fallback;
        }
        
        // Check for empty string or whitespace
        if (typeof value === 'string' && value.trim() === '') {
            console.warn(`Chart data field '${fieldName}' is empty string`);
            return fallback;
        }
        
        // Convert to number
        const num = parseFloat(value);
        
        // Check for NaN or infinite values
        if (isNaN(num) || !isFinite(num)) {
            console.warn(`Chart data field '${fieldName}' contains invalid numeric value:`, value);
            return fallback;
        }
        
        // Check negative values
        if (!allowNegative && num < 0) {
            console.warn(`Chart data field '${fieldName}' contains negative value:`, num);
            return fallback !== null ? fallback : 0;
        }
        
        // Check minimum value
        if (min !== undefined && num < min) {
            console.warn(`Chart data field '${fieldName}' is below minimum (${min}):`, num);
            return fallback !== null ? fallback : min;
        }
        
        // Check maximum value
        if (max !== undefined && num > max) {
            console.warn(`Chart data field '${fieldName}' exceeds maximum (${max}):`, num);
            return fallback !== null ? fallback : max;
        }
        
        return num;
    }

    /**
     * Validate chart configuration object structure and data types
     * @param {Object} config - Chart configuration object to validate
     * @returns {Object} Validated configuration object with sanitized data
     */
    validateChartConfig(config) {
        if (!config || typeof config !== 'object') {
            console.error('Chart config is not a valid object:', config);
            return this.getDefaultChartConfig();
        }

        const validatedConfig = {};

        // Validate exam performance data
        if (config.examPerformance) {
            validatedConfig.examPerformance = this.validateExamPerformanceData(config.examPerformance);
        }

        // Validate total counts
        validatedConfig.totalPassers = this.validateNumericData(
            config.totalPassers, 
            'totalPassers', 
            { min: 0, fallback: 0 }
        );
        
        validatedConfig.totalFailers = this.validateNumericData(
            config.totalFailers, 
            'totalFailers', 
            { min: 0, fallback: 0 }
        );

        // Validate passing rate data
        if (config.passingRateData) {
            validatedConfig.passingRateData = this.validatePassingRateData(config.passingRateData);
        }

        // Validate student dashboard data
        if (config.scoreTrend) {
            validatedConfig.scoreTrend = this.validateScoreTrendData(config.scoreTrend);
        }

        if (config.typePerformance) {
            validatedConfig.typePerformance = this.validateTypePerformanceData(config.typePerformance);
        }

        return validatedConfig;
    }

    /**
     * Validate exam performance data structure
     * @param {Object} examPerformance - Exam performance data object
     * @returns {Object} Validated exam performance data
     */
    validateExamPerformanceData(examPerformance) {
        // Use schema validation first
        return this.validateExamPerformanceSchema(examPerformance);
    }

    /**
     * Validate passing rate data structure
     * @param {Object} passingRateData - Passing rate data object
     * @returns {Object} Validated passing rate data
     */
    validatePassingRateData(passingRateData) {
        // Use schema validation first
        return this.validatePassingRateSchema(passingRateData);
    }

    /**
     * Validate score trend data structure
     * @param {Array} scoreTrendData - Score trend data array
     * @returns {Array} Validated score trend data
     */
    validateScoreTrendData(scoreTrendData) {
        // Use schema validation first
        return this.validateScoreTrendSchema(scoreTrendData);
    }

    /**
     * Validate type performance data structure
     * @param {Object} typePerformanceData - Type performance data object
     * @returns {Object} Validated type performance data
     */
    validateTypePerformanceData(typePerformanceData) {
        // Use schema validation first
        return this.validateTypePerformanceSchema(typePerformanceData);
    }

    /**
     * Get default chart configuration
     * @returns {Object} Default configuration object
     */
    getDefaultChartConfig() {
        return {
            examPerformance: {},
            totalPassers: 0,
            totalFailers: 0,
            passingRateData: { sections: [], subjects: [], data: {} },
            scoreTrend: [],
            typePerformance: {}
        };
    }

    /**
     * Define schema for chart data validation
     * @returns {Object} Schema definitions for different data types
     */
    getChartDataSchemas() {
        return {
            examPerformance: {
                type: 'object',
                properties: {
                    '*': {
                        type: 'object',
                        required: ['passers', 'failers', 'total'],
                        properties: {
                            passers: { type: 'number', minimum: 0 },
                            failers: { type: 'number', minimum: 0 },
                            total: { type: 'number', minimum: 0 }
                        }
                    }
                }
            },
            dashboardConfig: {
                type: 'object',
                required: ['total_students', 'total_exams', 'total_passers', 'total_failers'],
                properties: {
                    total_students: { type: 'number', minimum: 0 },
                    total_exams: { type: 'number', minimum: 0 },
                    total_passers: { type: 'number', minimum: 0 },
                    total_failers: { type: 'number', minimum: 0 }
                }
            },
            passingRateData: {
                type: 'object',
                required: ['sections', 'subjects', 'data'],
                properties: {
                    sections: { type: 'array', items: { type: 'string' } },
                    subjects: { type: 'array', items: { type: 'string' } },
                    data: {
                        type: 'object',
                        properties: {
                            '*': {
                                type: 'array',
                                items: { type: 'number', minimum: 0, maximum: 100 }
                            }
                        }
                    }
                }
            },
            scoreTrend: {
                type: 'array',
                items: {
                    type: 'object',
                    required: ['percentage'],
                    properties: {
                        percentage: { type: 'number', minimum: 0, maximum: 100 },
                        date: { type: 'string' },
                        exam_title: { type: 'string' },
                        exam_name: { type: 'string' }
                    }
                }
            },
            typePerformance: {
                type: 'object',
                properties: {
                    '*': { type: 'number', minimum: 0, maximum: 100 }
                }
            }
        };
    }

    /**
     * Validate data against schema
     * @param {*} data - Data to validate
     * @param {Object} schema - Schema definition
     * @param {string} path - Current path for error reporting
     * @returns {Object} Validation result with isValid flag and errors array
     */
    validateAgainstSchema(data, schema, path = 'root') {
        const errors = [];

        // Check type
        if (schema.type) {
            const actualType = Array.isArray(data) ? 'array' : typeof data;
            if (actualType !== schema.type) {
                errors.push(`${path}: Expected ${schema.type}, got ${actualType}`);
                return { isValid: false, errors };
            }
        }

        // Check required properties for objects
        if (schema.type === 'object' && schema.required && data) {
            for (const requiredProp of schema.required) {
                if (!(requiredProp in data)) {
                    errors.push(`${path}: Missing required property '${requiredProp}'`);
                }
            }
        }

        // Check properties for objects
        if (schema.type === 'object' && schema.properties && data) {
            for (const [propName, propSchema] of Object.entries(schema.properties)) {
                if (propName === '*') {
                    // Wildcard property - validate all properties
                    for (const [key, value] of Object.entries(data)) {
                        const result = this.validateAgainstSchema(value, propSchema, `${path}.${key}`);
                        errors.push(...result.errors);
                    }
                } else if (propName in data) {
                    const result = this.validateAgainstSchema(data[propName], propSchema, `${path}.${propName}`);
                    errors.push(...result.errors);
                }
            }
        }

        // Check array items
        if (schema.type === 'array' && schema.items && Array.isArray(data)) {
            data.forEach((item, index) => {
                const result = this.validateAgainstSchema(item, schema.items, `${path}[${index}]`);
                errors.push(...result.errors);
            });
        }

        // Check numeric constraints
        if (schema.type === 'number' && typeof data === 'number') {
            if (schema.minimum !== undefined && data < schema.minimum) {
                errors.push(`${path}: Value ${data} is below minimum ${schema.minimum}`);
            }
            if (schema.maximum !== undefined && data > schema.maximum) {
                errors.push(`${path}: Value ${data} exceeds maximum ${schema.maximum}`);
            }
        }

        return { isValid: errors.length === 0, errors };
    }

    /**
     * Validate exam performance data against schema
     * @param {Object} examPerformanceData - Exam performance data to validate
     * @returns {Object} Validation result with sanitized data
     */
    validateExamPerformanceSchema(examPerformanceData) {
        const schema = this.getChartDataSchemas().examPerformance;
        const result = this.validateAgainstSchema(examPerformanceData, schema, 'examPerformance');
        
        if (!result.isValid) {
            console.warn('Exam performance data validation errors:', result.errors);
            // Return empty object for invalid data
            return {};
        }

        // Additional business logic validation with enhanced accuracy checks
        const validated = {};
        for (const [examTitle, data] of Object.entries(examPerformanceData)) {
            if (data && typeof data === 'object') {
                // Ensure all values are valid numbers
                const passers = this.validateNumericData(data.passers, `${examTitle}.passers`, { min: 0, fallback: 0 });
                const failers = this.validateNumericData(data.failers, `${examTitle}.failers`, { min: 0, fallback: 0 });
                const total = this.validateNumericData(data.total, `${examTitle}.total`, { min: 0, fallback: 0 });

                // Calculate the correct total from passers + failers
                const calculatedTotal = passers + failers;
                
                // Ensure total matches passers + failers exactly
                if (total !== calculatedTotal && calculatedTotal > 0) {
                    console.warn(`Total mismatch for '${examTitle}': provided total=${total}, calculated total=${calculatedTotal}. Using calculated total.`);
                }

                // Use calculated total to ensure accuracy
                const finalTotal = calculatedTotal;
                
                // Validate that passers and failers don't exceed total
                const adjustedPassers = Math.min(passers, finalTotal);
                const adjustedFailers = Math.min(failers, finalTotal);
                
                // Ensure the sum still equals total after adjustments
                if (adjustedPassers + adjustedFailers !== finalTotal) {
                    console.warn(`Adjustment needed for '${examTitle}': passers=${adjustedPassers}, failers=${adjustedFailers}, total=${finalTotal}`);
                }

                validated[examTitle] = {
                    passers: adjustedPassers,
                    failers: adjustedFailers,
                    total: finalTotal
                };
            }
        }

        return validated;
    }

    /**
     * Validate dashboard configuration data against schema
     * @param {Object} dashboardConfigData - Dashboard configuration data to validate
     * @returns {Object} Validation result with sanitized data
     */
    validateDashboardConfigSchema(dashboardConfigData) {
        const schema = this.getChartDataSchemas().dashboardConfig;
        const result = this.validateAgainstSchema(dashboardConfigData, schema, 'dashboardConfig');
        
        if (!result.isValid) {
            console.warn('Dashboard config data validation errors:', result.errors);
            // Return default values for invalid data
            return {
                total_students: 0,
                total_exams: 0,
                total_passers: 0,
                total_failers: 0
            };
        }

        // Ensure consistency between totals
        const { total_students, total_passers, total_failers } = dashboardConfigData;
        const calculatedTotal = (total_passers || 0) + (total_failers || 0);
        
        if (total_students && calculatedTotal > total_students) {
            console.warn(`Student count inconsistency: passers(${total_passers}) + failers(${total_failers}) > total_students(${total_students})`);
        }

        return {
            total_students: total_students || 0,
            total_exams: dashboardConfigData.total_exams || 0,
            total_passers: total_passers || 0,
            total_failers: total_failers || 0
        };
    }

    /**
     * Validate passing rate data against schema
     * @param {Object} passingRateData - Passing rate data to validate
     * @returns {Object} Validation result with sanitized data
     */
    validatePassingRateSchema(passingRateData) {
        const schema = this.getChartDataSchemas().passingRateData;
        const result = this.validateAgainstSchema(passingRateData, schema, 'passingRateData');
        
        if (!result.isValid) {
            console.warn('Passing rate data validation errors:', result.errors);
            return { sections: [], subjects: [], data: {} };
        }

        // Ensure data consistency
        const { sections, subjects, data } = passingRateData;
        const validated = {
            sections: sections || [],
            subjects: subjects || [],
            data: {}
        };

        // Validate that each subject has data for each section
        if (data && typeof data === 'object') {
            for (const subject of subjects) {
                if (data[subject] && Array.isArray(data[subject])) {
                    if (data[subject].length !== sections.length) {
                        console.warn(`Data length mismatch for subject '${subject}': expected ${sections.length}, got ${data[subject].length}`);
                    }
                    validated.data[subject] = data[subject].slice(0, sections.length);
                } else {
                    console.warn(`Missing or invalid data for subject '${subject}'`);
                    validated.data[subject] = new Array(sections.length).fill(0);
                }
            }
        }

        return validated;
    }

    /**
     * Validate score trend data against schema
     * @param {Array} scoreTrendData - Score trend data to validate
     * @returns {Array} Validation result with sanitized data
     */
    validateScoreTrendSchema(scoreTrendData) {
        const schema = this.getChartDataSchemas().scoreTrend;
        const result = this.validateAgainstSchema(scoreTrendData, schema, 'scoreTrend');
        
        if (!result.isValid) {
            console.warn('Score trend data validation errors:', result.errors);
            return [];
        }

        // Filter out invalid items and ensure required fields
        return scoreTrendData.filter((item, index) => {
            if (!item || typeof item !== 'object') {
                console.warn(`Invalid score trend item at index ${index}:`, item);
                return false;
            }

            if (typeof item.percentage !== 'number' || item.percentage < 0 || item.percentage > 100) {
                console.warn(`Invalid percentage in score trend item at index ${index}:`, item.percentage);
                return false;
            }

            return true;
        });
    }

    /**
     * Validate type performance data against schema
     * @param {Object} typePerformanceData - Type performance data to validate
     * @returns {Object} Validation result with sanitized data
     */
    validateTypePerformanceSchema(typePerformanceData) {
        const schema = this.getChartDataSchemas().typePerformance;
        const result = this.validateAgainstSchema(typePerformanceData, schema, 'typePerformance');
        
        if (!result.isValid) {
            console.warn('Type performance data validation errors:', result.errors);
            return {};
        }

        // Filter out invalid values
        const validated = {};
        for (const [type, score] of Object.entries(typePerformanceData)) {
            if (typeof score === 'number' && score >= 0 && score <= 100) {
                validated[type] = score;
            } else {
                console.warn(`Invalid score for type '${type}':`, score);
            }
        }

        return validated;
    }

    /**
     * Initialize student dashboard charts
     * @param {Object} config - Configuration object containing chart data
     */
    initStudentCharts(config) {
        // Validate the entire configuration first
        const validatedConfig = this.validateChartConfig(config);
        const { scoreTrend, typePerformance } = validatedConfig;
        
        // Initialize Score Trend Chart
        if (scoreTrend && scoreTrend.length > 0) {
            this.createScoreTrendChart(scoreTrend);
        } else {
            this.showEmptyState('scoreTrendChart');
        }
        
        // Initialize Type Performance Chart
        if (typePerformance && Object.keys(typePerformance).length > 0) {
            this.createTypePerformanceChart(typePerformance);
        } else {
            this.showEmptyState('typePerformanceChart');
        }
    }

    /**
     * Create Pass/Fail by Exam Chart (Teacher Dashboard)
     * @param {Object} examPerformance - Validated exam performance data
     */
    createExamPerformanceChart(examPerformance) {
        try {
            const ctx = document.getElementById('examPerformanceChart');
            if (!ctx) {
                const error = new Error('Canvas element examPerformanceChart not found');
                DashboardCharts.handleChartError(error, {
                    operation: 'chartInitialization',
                    chartType: 'examPerformance',
                    canvasId: 'examPerformanceChart',
                    component: 'DashboardCharts'
                });
                return;
            }

            // Data is already validated, so we can use it directly
            const examLabels = Object.keys(examPerformance);
            const passersData = examLabels.map(title => examPerformance[title].passers);
            const failersData = examLabels.map(title => examPerformance[title].failers);

            // Check if we have valid data
            if (examLabels.length === 0) {
                this.showEmptyState('examPerformanceChart');
                return;
            }

            // Determine responsive settings with enhanced mobile optimization
            const isMobile = window.innerWidth < 640;
            const isTablet = window.innerWidth >= 640 && window.innerWidth < 1024;
            const isLandscape = window.innerWidth > window.innerHeight;
            const containerWidth = ctx.parentElement ? ctx.parentElement.clientWidth : window.innerWidth;

            const chart = new Chart(ctx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: examLabels,
                    datasets: [
                        {
                            label: 'Passers (≥60%)',
                            data: passersData,
                            backgroundColor: 'rgba(16, 185, 129, 0.85)',
                            borderColor: 'rgb(16, 185, 129)',
                            borderWidth: 2,
                            borderRadius: 6,
                        },
                        {
                            label: 'Failures (<60%)',
                            data: failersData,
                            backgroundColor: 'rgba(239, 68, 68, 0.85)',
                            borderColor: 'rgb(239, 68, 68)',
                            borderWidth: 2,
                            borderRadius: 6,
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: !isMobile, // Allow flexible aspect ratio on mobile
                    devicePixelRatio: window.devicePixelRatio || 1,
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    // Enhanced responsive behavior
                    onResize: (chart, size) => {
                        const newIsMobile = size.width < 640;
                        const newIsTablet = size.width >= 640 && size.width < 1024;
                        
                        // Update options based on new size
                        if (newIsMobile !== isMobile) {
                            this.updateChartResponsiveOptions(chart, {
                                isMobile: newIsMobile,
                                isTablet: newIsTablet,
                                isLandscape: size.width > size.height,
                                width: size.width,
                                height: size.height
                            });
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: isMobile ? (isLandscape ? 'right' : 'bottom') : 'top',
                            align: 'center',
                            labels: {
                                usePointStyle: true,
                                padding: isMobile ? (isLandscape ? 8 : 10) : 15,
                                font: {
                                    size: isMobile ? (isLandscape ? 10 : 11) : 12,
                                    family: "'Space Grotesk', sans-serif"
                                },
                                boxWidth: isMobile ? 8 : 10,
                                boxHeight: isMobile ? 8 : 10
                            },
                            // Limit legend height on mobile
                            maxHeight: isMobile ? 60 : undefined
                        },
                        tooltip: {
                            enabled: true,
                            backgroundColor: 'rgba(0, 0, 0, 0.9)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: 'rgba(255, 255, 255, 0.3)',
                            borderWidth: 1,
                            padding: isMobile ? 8 : 14,
                            displayColors: true,
                            titleFont: {
                                size: isMobile ? 12 : 14,
                                weight: 'bold'
                            },
                            bodyFont: {
                                size: isMobile ? 11 : 13
                            },
                            // Enhanced mobile tooltip positioning
                            position: isMobile ? 'nearest' : 'average',
                            caretPadding: isMobile ? 4 : 6,
                            cornerRadius: isMobile ? 4 : 6,
                            callbacks: {
                                title: function(context) {
                                    return context[0].label;
                                },
                                label: function(context) {
                                    const label = context.dataset.label || '';
                                    const value = context.parsed.y;
                                    const examIndex = context.dataIndex;
                                    const total = passersData[examIndex] + failersData[examIndex];
                                    // Ensure accurate percentage calculation with proper rounding
                                    const percentage = total > 0 ? Math.round((value / total) * 100 * 10) / 10 : 0;
                                    return `${label}: ${value} students (${percentage}%)`;
                                },
                                afterBody: function(context) {
                                    const examIndex = context[0].dataIndex;
                                    const total = passersData[examIndex] + failersData[examIndex];
                                    return `\nTotal Attempts: ${total}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            display: true,
                            grid: {
                                display: false,
                                drawBorder: true
                            },
                            ticks: {
                                font: {
                                    size: isMobile ? 9 : (isTablet ? 10 : 11)
                                },
                                autoSkip: true,
                                maxTicksLimit: isMobile ? (isLandscape ? 5 : 3) : (isTablet ? 4 : 6),
                                maxRotation: isMobile ? (isLandscape ? 30 : 45) : 30,
                                minRotation: isMobile ? (isLandscape ? 0 : 45) : 0,
                                callback: function(value, index) {
                                    const label = this.getLabelForValue(value);
                                    // Enhanced label truncation based on container width
                                    const maxLength = containerWidth < 300 ? 8 : (isMobile ? 12 : 20);
                                    if (label.length > maxLength) {
                                        return label.substring(0, maxLength - 3) + '...';
                                    }
                                    return label;
                                }
                            }
                        },
                        y: {
                            display: true,
                            title: {
                                display: !isMobile || isLandscape,
                                text: 'Number of Students',
                                font: {
                                    size: isMobile ? 10 : 12,
                                    weight: 'bold'
                                }
                            },
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1,
                                precision: 0,
                                font: {
                                    size: isMobile ? 9 : 11
                                },
                                // Reduce number of ticks on mobile
                                maxTicksLimit: isMobile ? 5 : 8
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.06)',
                                drawBorder: true
                            }
                        }
                    }
                }
            });

            this.charts.set('examPerformance', chart);
        } catch (error) {
            DashboardCharts.handleChartError(error, {
                operation: 'chartCreation',
                chartType: 'examPerformance',
                canvasId: 'examPerformanceChart',
                component: 'DashboardCharts',
                data: examPerformance
            });
        }
    }

    /**
     * Create Overall Distribution Chart (Teacher Dashboard)
     * @param {number} totalPassers - Validated number of students who passed
     * @param {number} totalFailers - Validated number of students who failed
     */
    createOverallDistributionChart(totalPassers, totalFailers) {
        const ctx = document.getElementById('overallDistributionChart');
        if (!ctx) {
            console.warn('Canvas element overallDistributionChart not found');
            return;
        }

        // Ensure accurate calculations by validating inputs
        const validatedPassers = this.validateNumericData(totalPassers, 'totalPassers', { min: 0, fallback: 0 });
        const validatedFailers = this.validateNumericData(totalFailers, 'totalFailers', { min: 0, fallback: 0 });
        const total = validatedPassers + validatedFailers;
        
        // Check if we have any data
        if (total === 0) {
            this.showEmptyState('overallDistributionChart');
            return;
        }

        const isMobile = window.innerWidth < 640;
        const isTablet = window.innerWidth >= 640 && window.innerWidth < 1024;
        const isLandscape = window.innerWidth > window.innerHeight;
        const containerWidth = ctx.parentElement ? ctx.parentElement.clientWidth : window.innerWidth;
        const isSmallContainer = containerWidth < 300;

        const chart = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Passers (≥60%)', 'Failures (<60%)'],
                datasets: [{
                    data: [validatedPassers, validatedFailers],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.85)',
                        'rgba(239, 68, 68, 0.85)'
                    ],
                    borderColor: [
                        'rgb(16, 185, 129)',
                        'rgb(239, 68, 68)'
                    ],
                    borderWidth: 2,
                    hoverOffset: 8,
                    hoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: !isMobile, // Allow flexible aspect ratio on mobile
                devicePixelRatio: window.devicePixelRatio || 1,
                cutout: isMobile ? (isSmallContainer ? '50%' : '55%') : '60%',
                // Enhanced responsive behavior
                onResize: (chart, size) => {
                    const newIsMobile = size.width < 640;
                    const newIsTablet = size.width >= 640 && size.width < 1024;
                    
                    // Update cutout based on new size
                    chart.options.cutout = newIsMobile ? '55%' : '60%';
                    
                    // Update options based on new size
                    if (newIsMobile !== isMobile) {
                        this.updateChartResponsiveOptions(chart, {
                            isMobile: newIsMobile,
                            isTablet: newIsTablet,
                            isLandscape: size.width > size.height,
                            width: size.width,
                            height: size.height
                        });
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom', // Always bottom for doughnut charts
                        align: 'center',
                        labels: {
                            usePointStyle: true,
                            padding: isMobile ? (isSmallContainer ? 8 : 10) : 15,
                            font: {
                                size: isMobile ? (isSmallContainer ? 10 : 11) : 12,
                                family: "'Space Grotesk', sans-serif"
                            },
                            boxWidth: isMobile ? (isSmallContainer ? 8 : 10) : 12,
                            boxHeight: isMobile ? (isSmallContainer ? 8 : 10) : 12,
                            // Enhanced responsive legend generation
                            generateLabels: function(chart) {
                                const data = chart.data;
                                if (data.labels.length && data.datasets.length) {
                                    return data.labels.map((label, i) => {
                                        const value = data.datasets[0].data[i];
                                        // Ensure accurate percentage calculation with proper rounding
                                        const percentage = total > 0 ? Math.round((value / total) * 100 * 10) / 10 : 0;
                                        
                                        // Truncate labels on very small containers
                                        let displayLabel = label;
                                        if (isSmallContainer && label.length > 15) {
                                            displayLabel = label.substring(0, 12) + '...';
                                        }
                                        
                                        return {
                                            text: `${displayLabel} (${percentage}%)`,
                                            fillStyle: data.datasets[0].backgroundColor[i],
                                            strokeStyle: data.datasets[0].borderColor[i],
                                            lineWidth: 2,
                                            hidden: false,
                                            index: i
                                        };
                                    });
                                }
                                return [];
                            }
                        },
                        // Limit legend height on mobile
                        maxHeight: isMobile ? (isSmallContainer ? 50 : 70) : undefined
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                        borderWidth: 1,
                        padding: isMobile ? (isSmallContainer ? 6 : 8) : 14,
                        displayColors: true,
                        titleFont: {
                            size: isMobile ? (isSmallContainer ? 11 : 12) : 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: isMobile ? (isSmallContainer ? 10 : 11) : 13
                        },
                        // Enhanced tooltip positioning for better visibility
                        position: 'nearest',
                        caretPadding: isMobile ? 4 : 6,
                        cornerRadius: isMobile ? 4 : 6,
                        // Ensure tooltips stay within viewport
                        filter: function(tooltipItem, chart) {
                            // Always show tooltips for doughnut charts
                            return true;
                        },
                        // Enhanced positioning logic
                        external: function(context) {
                            const tooltip = context.tooltip;
                            if (!tooltip || tooltip.opacity === 0) return;

                            const chart = context.chart;
                            const canvas = chart.canvas;
                            const rect = canvas.getBoundingClientRect();
                            
                            // Get tooltip element
                            let tooltipEl = document.getElementById('chartjs-tooltip');
                            if (!tooltipEl) {
                                tooltipEl = document.createElement('div');
                                tooltipEl.id = 'chartjs-tooltip';
                                tooltipEl.style.position = 'absolute';
                                tooltipEl.style.pointerEvents = 'none';
                                tooltipEl.style.zIndex = '1000';
                                document.body.appendChild(tooltipEl);
                            }

                            // Calculate position to keep tooltip in viewport
                            let left = rect.left + tooltip.caretX;
                            let top = rect.top + tooltip.caretY;
                            
                            // Adjust for viewport boundaries
                            const tooltipWidth = 200; // Estimated tooltip width
                            const tooltipHeight = 100; // Estimated tooltip height
                            
                            if (left + tooltipWidth > window.innerWidth) {
                                left = window.innerWidth - tooltipWidth - 10;
                            }
                            if (left < 10) {
                                left = 10;
                            }
                            if (top + tooltipHeight > window.innerHeight) {
                                top = rect.top + tooltip.caretY - tooltipHeight - 10;
                            }
                            if (top < 10) {
                                top = 10;
                            }

                            tooltipEl.style.left = left + 'px';
                            tooltipEl.style.top = top + 'px';
                        },
                        callbacks: {
                            title: function(context) {
                                return context[0].label;
                            },
                            label: function(context) {
                                const value = context.parsed;
                                return `Count: ${value} students`;
                            },
                            afterLabel: function(context) {
                                const value = context.parsed;
                                // Ensure accurate percentage calculation with proper rounding
                                const percentage = total > 0 ? Math.round((value / total) * 100 * 10) / 10 : 0;
                                return `Percentage: ${percentage}%`;
                            },
                            afterBody: function(context) {
                                return `\nTotal Attempts: ${total}`;
                            }
                        }
                    }
                }
            }
        });

        this.charts.set('overallDistribution', chart);
    }

    /**
     * Create Passing Rate by Subject Chart (Teacher Dashboard)
     * @param {Object} passingRateData - Passing rate data by subject and section
     */
    createPassingRateBySubjectChart(passingRateData) {
        const ctx = document.getElementById('passingRateBySubjectChart');
        if (!ctx) return;

        const isMobile = window.innerWidth < 640;
        const isTablet = window.innerWidth >= 640 && window.innerWidth < 1024;
        const isLandscape = window.innerWidth > window.innerHeight;
        const containerWidth = ctx.parentElement ? ctx.parentElement.clientWidth : window.innerWidth;
        const isSmallContainer = containerWidth < 400;

        // Generate distinct colors for each subject
        const subjectColors = [
            { bg: 'rgba(59, 130, 246, 0.85)', border: 'rgb(59, 130, 246)' },      // Blue
            { bg: 'rgba(16, 185, 129, 0.85)', border: 'rgb(16, 185, 129)' },      // Green
            { bg: 'rgba(245, 158, 11, 0.85)', border: 'rgb(245, 158, 11)' },      // Amber
            { bg: 'rgba(139, 92, 246, 0.85)', border: 'rgb(139, 92, 246)' },      // Purple
            { bg: 'rgba(236, 72, 153, 0.85)', border: 'rgb(236, 72, 153)' },      // Pink
            { bg: 'rgba(20, 184, 166, 0.85)', border: 'rgb(20, 184, 166)' },      // Teal
            { bg: 'rgba(251, 146, 60, 0.85)', border: 'rgb(251, 146, 60)' },      // Orange
            { bg: 'rgba(99, 102, 241, 0.85)', border: 'rgb(99, 102, 241)' },      // Indigo
            { bg: 'rgba(244, 63, 94, 0.85)', border: 'rgb(244, 63, 94)' },        // Rose
            { bg: 'rgba(14, 165, 233, 0.85)', border: 'rgb(14, 165, 233)' },      // Sky
        ];

        // Prepare datasets for each subject
        const datasets = passingRateData.subjects.map((subject, index) => {
            const colorIndex = index % subjectColors.length;
            return {
                label: subject,
                data: passingRateData.data[subject],
                backgroundColor: subjectColors[colorIndex].bg,
                borderColor: subjectColors[colorIndex].border,
                borderWidth: 2,
                borderRadius: 6,
            };
        });

        const chart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: passingRateData.sections,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: !isMobile, // Allow flexible aspect ratio on mobile
                devicePixelRatio: window.devicePixelRatio || 1,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                // Enhanced responsive behavior
                onResize: (chart, size) => {
                    const newIsMobile = size.width < 640;
                    const newIsTablet = size.width >= 640 && size.width < 1024;
                    
                    // Update options based on new size
                    if (newIsMobile !== isMobile) {
                        this.updateChartResponsiveOptions(chart, {
                            isMobile: newIsMobile,
                            isTablet: newIsTablet,
                            isLandscape: size.width > size.height,
                            width: size.width,
                            height: size.height
                        });
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: isMobile ? (isLandscape ? 'right' : 'bottom') : 'top',
                        align: 'center',
                        labels: {
                            usePointStyle: true,
                            padding: isMobile ? (isSmallContainer ? 6 : 8) : 12,
                            font: {
                                size: isMobile ? (isSmallContainer ? 9 : 10) : 11,
                                family: "'Space Grotesk', sans-serif"
                            },
                            boxWidth: isMobile ? (isSmallContainer ? 6 : 8) : 10,
                            boxHeight: isMobile ? (isSmallContainer ? 6 : 8) : 10
                        },
                        maxHeight: isMobile ? (isSmallContainer ? 60 : 80) : undefined
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                        borderWidth: 1,
                        padding: isMobile ? (isSmallContainer ? 6 : 8) : 14,
                        displayColors: true,
                        titleFont: {
                            size: isMobile ? (isSmallContainer ? 11 : 12) : 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: isMobile ? (isSmallContainer ? 10 : 11) : 13
                        },
                        // Enhanced tooltip positioning for better visibility
                        position: isMobile ? 'nearest' : 'average',
                        caretPadding: isMobile ? 4 : 6,
                        cornerRadius: isMobile ? 4 : 6,
                        // Ensure tooltips stay within viewport on mobile
                        filter: function(tooltipItem, chart) {
                            // Show all tooltips but limit on very small screens
                            if (isSmallContainer && chart.data.datasets.length > 3) {
                                // Only show tooltip for the first 3 datasets on small screens
                                return tooltipItem.datasetIndex < 3;
                            }
                            return true;
                        },
                        callbacks: {
                            title: function(context) {
                                return `Section: ${context[0].label}`;
                            },
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y;
                                return `${label}: ${value.toFixed(1)}%`;
                            },
                            afterLabel: function(context) {
                                const value = context.parsed.y;
                                if (value >= 90) return 'Excellent performance! 🌟';
                                if (value >= 75) return 'Strong performance 👍';
                                if (value >= 60) return 'Good performance ✓';
                                if (value >= 40) return 'Needs improvement 📚';
                                return 'Requires attention ⚠️';
                            },
                            footer: function(context) {
                                // Calculate average for this section
                                let sum = 0;
                                context.forEach(item => {
                                    sum += item.parsed.y;
                                });
                                const avg = (sum / context.length).toFixed(1);
                                return `\nSection Average: ${avg}%`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false,
                            drawBorder: true
                        },
                        ticks: {
                            font: {
                                size: isMobile ? (isSmallContainer ? 8 : 9) : (isTablet ? 10 : 11)
                            },
                            autoSkip: true,
                            maxTicksLimit: isMobile ? (isSmallContainer ? 2 : (isLandscape ? 4 : 3)) : (isTablet ? 5 : 8),
                            maxRotation: isMobile ? (isLandscape ? 30 : 45) : (isTablet ? 30 : 20),
                            minRotation: isMobile ? (isLandscape ? 0 : 45) : 0,
                            callback: function(value, index) {
                                const label = this.getLabelForValue(value);
                                // Enhanced label truncation based on container size
                                const maxLength = isSmallContainer ? 6 : (isMobile ? 10 : 15);
                                if (label.length > maxLength) {
                                    return label.substring(0, maxLength - 3) + '...';
                                }
                                return label;
                            }
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: !isMobile || isLandscape,
                            text: 'Passing Rate (%)',
                            font: {
                                size: isMobile ? 10 : 12,
                                weight: 'bold'
                            }
                        },
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: isMobile ? (isSmallContainer ? 50 : 25) : 20,
                            font: {
                                size: isMobile ? (isSmallContainer ? 8 : 9) : 11
                            },
                            callback: function(value) {
                                return value + '%';
                            },
                            // Reduce number of ticks on mobile
                            maxTicksLimit: isMobile ? (isSmallContainer ? 3 : 5) : 6
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.06)',
                            drawBorder: true
                        }
                    }
                }
            }
        });

        this.charts.set('passingRateBySubject', chart);
    }

    /**
     * Create Score Trend Chart (Student Dashboard)
     * @param {Array} scoreTrendData - Array of score data over time
     */
    createScoreTrendChart(scoreTrendData) {
        const ctx = document.getElementById('scoreTrendChart');
        if (!ctx || !scoreTrendData || scoreTrendData.length === 0) {
            this.showEmptyState('scoreTrendChart');
            return;
        }

        const isMobile = window.innerWidth < 640;

        // Prepare data for Chart.js
        const labels = scoreTrendData.map(item => {
            if (item.date) {
                const date = new Date(item.date);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }
            return item.exam_title || item.exam_name;
        });

        const scores = scoreTrendData.map(item => item.percentage);
        const examNames = scoreTrendData.map(item => item.exam_title || item.exam_name);

        // Create passing threshold line (60%)
        const passingThreshold = Array(scoreTrendData.length).fill(60);

        const chart = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Your Score',
                        data: scores,
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: isMobile ? 4 : 6,
                        pointHoverRadius: isMobile ? 6 : 8,
                        pointBackgroundColor: 'rgb(59, 130, 246)',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                    },
                    {
                        label: 'Passing Threshold (60%)',
                        data: passingThreshold,
                        borderColor: 'rgb(239, 68, 68)',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        pointRadius: 0,
                        pointHoverRadius: 0,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                devicePixelRatio: window.devicePixelRatio || 1,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: isMobile ? 10 : 15,
                            font: {
                                size: isMobile ? 11 : 12,
                                family: "'Space Grotesk', sans-serif"
                            }
                        }
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                        borderWidth: 1,
                        padding: isMobile ? 10 : 14,
                        displayColors: true,
                        titleFont: {
                            size: isMobile ? 13 : 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: isMobile ? 12 : 13
                        },
                        callbacks: {
                            title: function(context) {
                                const index = context[0].dataIndex;
                                return examNames[index];
                            },
                            label: function(context) {
                                if (context.datasetIndex === 0) {
                                    const score = context.parsed.y;
                                    const status = score >= 60 ? ' ✓' : ' (Below Threshold)';
                                    return `Score: ${score.toFixed(1)}%${status}`;
                                }
                                return null; // Don't show tooltip for threshold line
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: !isMobile,
                            text: 'Exam Date',
                            font: {
                                size: 12,
                                weight: 'bold'
                            }
                        },
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: isMobile ? 9 : 11
                            },
                            maxRotation: isMobile ? 45 : 0,
                            autoSkip: true,
                            maxTicksLimit: isMobile ? 5 : 10,
                            callback: function(value, index) {
                                const label = this.getLabelForValue(value);
                                if (isMobile && label.length > 15) {
                                    return label.substring(0, 12) + '...';
                                }
                                return label;
                            }
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: !isMobile,
                            text: 'Score (%)',
                            font: {
                                size: 12,
                                weight: 'bold'
                            }
                        },
                        min: 0,
                        max: 100,
                        ticks: {
                            stepSize: 10,
                            font: {
                                size: isMobile ? 10 : 11
                            },
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.06)'
                        }
                    }
                }
            }
        });

        this.charts.set('scoreTrend', chart);
    }

    /**
     * Create Type Performance Chart (Student Dashboard)
     * @param {Object} typePerformanceData - Performance data by question type
     */
    createTypePerformanceChart(typePerformanceData) {
        const ctx = document.getElementById('typePerformanceChart');
        if (!ctx || !typePerformanceData) {
            this.showEmptyState('typePerformanceChart');
            return;
        }

        const isMobile = window.innerWidth < 640;

        // Define colors for each question type
        const colors = [
            'rgba(16, 185, 129, 0.85)',   // Green
            'rgba(59, 130, 246, 0.85)',   // Blue
            'rgba(245, 158, 11, 0.85)',   // Amber
            'rgba(139, 92, 246, 0.85)',   // Purple
            'rgba(236, 72, 153, 0.85)',   // Pink
        ];

        const borderColors = [
            'rgb(16, 185, 129)',
            'rgb(59, 130, 246)',
            'rgb(245, 158, 11)',
            'rgb(139, 92, 246)',
            'rgb(236, 72, 153)',
        ];

        const labels = Object.keys(typePerformanceData);
        const scores = Object.values(typePerformanceData);

        const chart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Average Score (%)',
                    data: scores,
                    backgroundColor: colors.slice(0, labels.length),
                    borderColor: borderColors.slice(0, labels.length),
                    borderWidth: 2,
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                devicePixelRatio: window.devicePixelRatio || 1,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                        borderWidth: 1,
                        padding: isMobile ? 10 : 14,
                        displayColors: false,
                        titleFont: {
                            size: isMobile ? 13 : 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: isMobile ? 12 : 13
                        },
                        callbacks: {
                            title: function(context) {
                                return context[0].label;
                            },
                            label: function(context) {
                                return `Average: ${context.parsed.y.toFixed(1)}%`;
                            },
                            afterLabel: function(context) {
                                const score = context.parsed.y;
                                if (score >= 90) return 'Excellent! 🌟';
                                if (score >= 80) return 'Great! 👍';
                                if (score >= 70) return 'Good 👌';
                                if (score >= 60) return 'Passing ✓';
                                return 'Needs improvement 📚';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: isMobile ? 9 : 11
                            },
                            maxRotation: isMobile ? 45 : 0,
                            autoSkip: true,
                            maxTicksLimit: isMobile ? 3 : 5,
                            callback: function(value, index) {
                                const label = this.getLabelForValue(value);
                                if (isMobile && label.length > 12) {
                                    return label.substring(0, 10) + '...';
                                }
                                return label;
                            }
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: !isMobile,
                            text: 'Average Score (%)',
                            font: {
                                size: 12,
                                weight: 'bold'
                            }
                        },
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 10,
                            font: {
                                size: isMobile ? 10 : 11
                            },
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.06)'
                        }
                    }
                }
            }
        });

        this.charts.set('typePerformance', chart);
    }

    /**
     * Setup enhanced window resize handler for responsive charts
     * Handles window changes, orientation changes, and container size changes
     */
    setupResizeHandler() {
        let lastWidth = window.innerWidth;
        let lastHeight = window.innerHeight;
        let lastOrientation = window.orientation || 0;

        const handleResize = () => {
            const currentWidth = window.innerWidth;
            const currentHeight = window.innerHeight;
            const currentOrientation = window.orientation || 0;

            // Check if this is a significant resize (not just scrollbar changes)
            const widthChange = Math.abs(currentWidth - lastWidth);
            const heightChange = Math.abs(currentHeight - lastHeight);
            const orientationChange = currentOrientation !== lastOrientation;

            if (widthChange > 10 || heightChange > 10 || orientationChange) {
                clearTimeout(this.resizeTimeout);
                this.resizeTimeout = setTimeout(() => {
                    this.handleResponsiveResize(currentWidth, currentHeight, orientationChange);
                    lastWidth = currentWidth;
                    lastHeight = currentHeight;
                    lastOrientation = currentOrientation;
                }, 150); // Reduced debounce time for better responsiveness
            }
        };

        // Listen to multiple resize events for comprehensive coverage
        window.addEventListener('resize', handleResize, { passive: true });
        window.addEventListener('orientationchange', () => {
            // Orientation change needs a longer delay to get accurate dimensions
            setTimeout(handleResize, 300);
        }, { passive: true });

        // Also listen for container resize using ResizeObserver if available
        if (window.ResizeObserver) {
            this.setupContainerResizeObserver();
        }
    }

    /**
     * Setup ResizeObserver for individual chart containers
     * Provides more accurate resize detection than window events
     */
    setupContainerResizeObserver() {
        if (!window.ResizeObserver) return;

        this.containerObserver = new ResizeObserver((entries) => {
            clearTimeout(this.containerResizeTimeout);
            this.containerResizeTimeout = setTimeout(() => {
                entries.forEach(entry => {
                    const canvasId = entry.target.querySelector('canvas')?.id;
                    if (canvasId && this.charts.has(this.getChartKeyFromCanvasId(canvasId))) {
                        const chart = this.charts.get(this.getChartKeyFromCanvasId(canvasId));
                        if (chart) {
                            this.updateChartForContainer(chart, entry.contentRect);
                        }
                    }
                });
            }, 100);
        });

        // Observe all chart containers
        const chartContainers = [
            'examPerformanceChart',
            'overallDistributionChart',
            'passingRateBySubjectChart',
            'scoreTrendChart',
            'typePerformanceChart'
        ];

        chartContainers.forEach(canvasId => {
            const canvas = document.getElementById(canvasId);
            if (canvas && canvas.parentElement) {
                this.containerObserver.observe(canvas.parentElement);
            }
        });
    }

    /**
     * Handle responsive resize with enhanced mobile optimization
     * @param {number} width - Current window width
     * @param {number} height - Current window height
     * @param {boolean} orientationChanged - Whether orientation changed
     */
    handleResponsiveResize(width, height, orientationChanged) {
        const isMobile = width < 640;
        const isTablet = width >= 640 && width < 1024;
        const isLandscape = width > height;

        console.log(`Responsive resize: ${width}x${height}, mobile: ${isMobile}, tablet: ${isTablet}, landscape: ${isLandscape}`);

        this.charts.forEach((chart, chartKey) => {
            try {
                // Update chart options for new screen size
                this.updateChartResponsiveOptions(chart, {
                    isMobile,
                    isTablet,
                    isLandscape,
                    width,
                    height,
                    orientationChanged
                });

                // Resize the chart
                chart.resize();

                // Force update if orientation changed (fixes rendering issues)
                if (orientationChanged) {
                    setTimeout(() => {
                        chart.update('none'); // Update without animation for immediate response
                    }, 50);
                }
            } catch (error) {
                console.error(`Error resizing chart ${chartKey}:`, error);
            }
        });
    }

    /**
     * Update chart options for responsive behavior
     * @param {Chart} chart - Chart.js instance
     * @param {Object} screenInfo - Screen size and orientation information
     */
    updateChartResponsiveOptions(chart, screenInfo) {
        const { isMobile, isTablet, isLandscape, width, height } = screenInfo;

        // Update legend positioning
        if (chart.options.plugins && chart.options.plugins.legend) {
            const legend = chart.options.plugins.legend;
            
            // Adjust legend position based on screen size and chart type
            if (chart.config.type === 'doughnut') {
                legend.position = 'bottom';
            } else if (isMobile) {
                legend.position = isLandscape ? 'right' : 'bottom';
                legend.labels.padding = 8;
                legend.labels.font.size = 10;
            } else if (isTablet) {
                legend.position = 'top';
                legend.labels.padding = 12;
                legend.labels.font.size = 11;
            } else {
                legend.position = 'top';
                legend.labels.padding = 15;
                legend.labels.font.size = 12;
            }
        }

        // Update tooltip settings
        if (chart.options.plugins && chart.options.plugins.tooltip) {
            const tooltip = chart.options.plugins.tooltip;
            tooltip.padding = isMobile ? 8 : 14;
            tooltip.titleFont.size = isMobile ? 12 : 14;
            tooltip.bodyFont.size = isMobile ? 11 : 13;
        }

        // Update scale settings
        if (chart.options.scales) {
            // X-axis adjustments
            if (chart.options.scales.x) {
                const xScale = chart.options.scales.x;
                if (xScale.ticks) {
                    xScale.ticks.font.size = isMobile ? 9 : (isTablet ? 10 : 11);
                    xScale.ticks.maxRotation = isMobile ? 45 : (isTablet ? 30 : 20);
                    xScale.ticks.minRotation = isMobile ? 45 : 0;
                    xScale.ticks.maxTicksLimit = isMobile ? (isLandscape ? 5 : 3) : (isTablet ? 6 : 8);
                }
                if (xScale.title) {
                    xScale.title.display = !isMobile || isLandscape;
                }
            }

            // Y-axis adjustments
            if (chart.options.scales.y) {
                const yScale = chart.options.scales.y;
                if (yScale.ticks) {
                    yScale.ticks.font.size = isMobile ? 9 : 11;
                    if (chart.config.type === 'bar' && isMobile) {
                        yScale.ticks.stepSize = Math.max(1, Math.ceil(chart.data.datasets[0].data.length / 4));
                    }
                }
                if (yScale.title) {
                    yScale.title.display = !isMobile || isLandscape;
                    yScale.title.font.size = isMobile ? 10 : 12;
                }
            }
        }

        // Update aspect ratio and sizing
        if (isMobile) {
            chart.options.maintainAspectRatio = false;
            // Set minimum height for mobile charts
            const canvas = chart.canvas;
            if (canvas && canvas.parentElement) {
                const container = canvas.parentElement;
                const minHeight = isLandscape ? '200px' : '250px';
                if (container.style.height !== minHeight) {
                    container.style.height = minHeight;
                }
            }
        } else {
            chart.options.maintainAspectRatio = true;
        }

        // Update device pixel ratio for crisp rendering
        chart.options.devicePixelRatio = window.devicePixelRatio || 1;
    }

    /**
     * Update chart for specific container resize
     * @param {Chart} chart - Chart.js instance
     * @param {DOMRectReadOnly} containerRect - Container dimensions
     */
    updateChartForContainer(chart, containerRect) {
        const { width, height } = containerRect;
        const isMobile = width < 400; // Container-based mobile detection
        const aspectRatio = width / height;

        // Adjust chart based on container dimensions
        if (chart.options.plugins && chart.options.plugins.legend) {
            const legend = chart.options.plugins.legend;
            
            // Switch legend position based on container aspect ratio
            if (aspectRatio < 1.2) { // Tall container
                legend.position = 'bottom';
            } else if (aspectRatio > 2) { // Wide container
                legend.position = 'right';
            } else {
                legend.position = 'top';
            }
        }

        chart.resize();
    }

    /**
     * Get chart key from canvas ID
     * @param {string} canvasId - Canvas element ID
     * @returns {string} Chart key for the charts Map
     */
    getChartKeyFromCanvasId(canvasId) {
        const keyMap = {
            'examPerformanceChart': 'examPerformance',
            'overallDistributionChart': 'overallDistribution',
            'passingRateBySubjectChart': 'passingRateBySubject',
            'scoreTrendChart': 'scoreTrend',
            'typePerformanceChart': 'typePerformance'
        };
        return keyMap[canvasId] || canvasId;
    }

    /**
     * Enhanced tooltip positioning to ensure visibility within viewport
     * @param {Object} context - Chart.js tooltip context
     * @param {string} tooltipId - Unique ID for the tooltip element
     */
    static positionTooltipInViewport(context, tooltipId = 'chartjs-tooltip') {
        const tooltip = context.tooltip;
        if (!tooltip || tooltip.opacity === 0) return;

        const chart = context.chart;
        const canvas = chart.canvas;
        const rect = canvas.getBoundingClientRect();
        
        // Get or create tooltip element
        let tooltipEl = document.getElementById(tooltipId);
        if (!tooltipEl) {
            tooltipEl = document.createElement('div');
            tooltipEl.id = tooltipId;
            tooltipEl.style.position = 'absolute';
            tooltipEl.style.pointerEvents = 'none';
            tooltipEl.style.zIndex = '1000';
            tooltipEl.style.transition = 'all 0.1s ease';
            document.body.appendChild(tooltipEl);
        }

        // Calculate initial position
        let left = rect.left + window.scrollX + tooltip.caretX;
        let top = rect.top + window.scrollY + tooltip.caretY;
        
        // Estimate tooltip dimensions (will be refined after rendering)
        const estimatedWidth = Math.min(300, window.innerWidth * 0.8);
        const estimatedHeight = Math.min(150, window.innerHeight * 0.3);
        
        // Adjust for viewport boundaries with padding
        const padding = 10;
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // Horizontal positioning
        if (left + estimatedWidth > viewportWidth - padding) {
            left = viewportWidth - estimatedWidth - padding;
        }
        if (left < padding) {
            left = padding;
        }
        
        // Vertical positioning
        if (top + estimatedHeight > viewportHeight - padding) {
            // Position above the point instead
            top = rect.top + window.scrollY + tooltip.caretY - estimatedHeight - 10;
        }
        if (top < padding) {
            top = padding;
        }

        // Apply positioning
        tooltipEl.style.left = left + 'px';
        tooltipEl.style.top = top + 'px';
        tooltipEl.style.maxWidth = estimatedWidth + 'px';
        tooltipEl.style.maxHeight = estimatedHeight + 'px';
        
        return { left, top, maxWidth: estimatedWidth, maxHeight: estimatedHeight };
    }

    /**
     * Create responsive breakpoint configuration
     * @param {number} width - Current width
     * @param {number} height - Current height
     * @returns {Object} Breakpoint configuration
     */
    static getResponsiveBreakpoints(width, height) {
        return {
            isXSmall: width < 480,
            isSmall: width >= 480 && width < 640,
            isMobile: width < 640,
            isTablet: width >= 640 && width < 1024,
            isDesktop: width >= 1024,
            isLandscape: width > height,
            isPortrait: height >= width,
            containerSize: {
                isNarrow: width < 300,
                isWide: width > 800,
                isTall: height > 600,
                isShort: height < 400
            }
        };
    }

    /**
     * Destroy all charts and cleanup
     */
    destroy() {
        this.charts.forEach(chart => {
            chart.destroy();
        });
        this.charts.clear();
        
        if (this.resizeTimeout) {
            clearTimeout(this.resizeTimeout);
        }

        if (this.containerResizeTimeout) {
            clearTimeout(this.containerResizeTimeout);
        }

        if (this.containerObserver) {
            this.containerObserver.disconnect();
            this.containerObserver = null;
        }
    }

    /**
     * Get a specific chart instance
     * @param {string} chartName - Name of the chart
     * @returns {Chart|undefined} Chart instance or undefined if not found
     */
    getChart(chartName) {
        return this.charts.get(chartName);
    }

    /**
     * Get all chart instances
     * @returns {Map} Map of all chart instances
     */
    getAllCharts() {
        return this.charts;
    }

    /**
     * Centralized error handling function with detailed logging and context tracking
     * @param {Error} error - The error that occurred
     * @param {Object} context - Additional context information for debugging
     * @param {string} context.operation - The operation that failed (e.g., 'chartInitialization', 'dataValidation')
     * @param {string} context.chartType - Type of chart being processed (e.g., 'examPerformance', 'overallDistribution')
     * @param {string} context.canvasId - ID of the canvas element
     * @param {*} context.data - The data that caused the error (will be sanitized for logging)
     * @param {string} context.component - Component name where error occurred
     */
    static handleChartError(error, context = {}) {
        // Create comprehensive error information
        const errorInfo = {
            timestamp: new Date().toISOString(),
            message: error.message,
            stack: error.stack,
            name: error.name,
            context: {
                operation: context.operation || 'unknown',
                chartType: context.chartType || 'unknown',
                canvasId: context.canvasId || 'unknown',
                component: context.component || 'DashboardCharts',
                userAgent: navigator.userAgent,
                url: window.location.href,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                }
            }
        };

        // Sanitize data for logging (remove sensitive information, limit size)
        if (context.data) {
            try {
                const dataString = JSON.stringify(context.data);
                if (dataString.length > 1000) {
                    errorInfo.context.dataSample = dataString.substring(0, 1000) + '... [truncated]';
                } else {
                    errorInfo.context.dataSample = dataString;
                }
            } catch (serializationError) {
                errorInfo.context.dataSample = '[Unable to serialize data]';
            }
        }

        // Log error with full context
        console.error('Dashboard Chart Error:', errorInfo);

        // Log additional debug information
        console.group('Chart Error Debug Information');
        console.log('Error Type:', error.constructor.name);
        console.log('Operation:', context.operation);
        console.log('Chart Type:', context.chartType);
        console.log('Canvas ID:', context.canvasId);
        if (context.data) {
            console.log('Data Type:', typeof context.data);
            console.log('Data Keys:', context.data && typeof context.data === 'object' ? Object.keys(context.data) : 'N/A');
        }
        console.groupEnd();

        // Show user-friendly fallback based on error type and context
        if (context.canvasId) {
            this.showChartErrorState(context.canvasId, error, context);
        }

        // Send to error tracking service if available
        if (window.errorTracker && typeof window.errorTracker.log === 'function') {
            try {
                window.errorTracker.log(errorInfo);
            } catch (trackingError) {
                console.warn('Failed to send error to tracking service:', trackingError);
            }
        }

        // Send to external monitoring if configured
        if (window.chartErrorReporter && typeof window.chartErrorReporter === 'function') {
            try {
                window.chartErrorReporter(errorInfo);
            } catch (reportingError) {
                console.warn('Failed to report error to external service:', reportingError);
            }
        }

        return errorInfo;
    }

    /**
     * Show appropriate error state UI based on error type and context
     * @param {string} canvasId - ID of the canvas element
     * @param {Error} error - The error that occurred
     * @param {Object} context - Error context information
     */
    static showChartErrorState(canvasId, error, context = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !canvas.parentElement) {
            console.warn(`Cannot show error state: canvas '${canvasId}' not found`);
            return;
        }

        const container = canvas.parentElement;
        
        // Hide canvas
        canvas.style.display = 'none';

        // Remove any existing error states
        const existingError = container.querySelector('.chart-error-state');
        if (existingError) {
            existingError.remove();
        }

        // Determine error message based on error type and context
        let errorMessage = 'Unable to load chart';
        let errorDetails = 'Please refresh the page or contact support';
        let errorIcon = 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'; // Warning icon

        if (error.name === 'SyntaxError' || context.operation === 'dataValidation') {
            errorMessage = 'Invalid chart data';
            errorDetails = 'The chart data format is incorrect';
            errorIcon = 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z';
        } else if (error.message.includes('Chart') || context.operation === 'chartInitialization') {
            errorMessage = 'Chart initialization failed';
            errorDetails = 'Unable to create the chart visualization';
        } else if (error.name === 'TypeError' && error.message.includes('undefined')) {
            errorMessage = 'Missing chart data';
            errorDetails = 'Required data is not available';
        } else if (context.operation === 'libraryLoading') {
            errorMessage = 'Chart library not loaded';
            errorDetails = 'Please refresh the page to reload chart components';
            errorIcon = 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z';
        }

        // Create error state UI
        const errorState = document.createElement('div');
        errorState.className = 'chart-error-state p-6 text-center text-red-500 bg-red-50 rounded-lg border border-red-200';
        errorState.innerHTML = `
            <div class="text-sm">
                <svg class="mx-auto h-10 w-10 text-red-400 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${errorIcon}" />
                </svg>
                <p class="font-medium text-red-800 mb-1">${errorMessage}</p>
                <p class="text-xs text-red-600 mb-3">${errorDetails}</p>
                <button class="chart-error-retry-btn text-xs bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1 rounded border border-red-300 transition-colors duration-200" 
                        onclick="window.location.reload()">
                    Refresh Page
                </button>
            </div>
        `;
        
        container.appendChild(errorState);

        // Add error state to canvas for accessibility
        canvas.setAttribute('aria-label', `Chart error: ${errorMessage}`);
        canvas.setAttribute('role', 'img');
    }

    /**
     * Validate and ensure accurate calculations for chart data
     * @param {Object} chartData - Chart data to validate
     * @param {string} chartType - Type of chart (examPerformance, distribution, etc.)
     * @returns {Object} Validated chart data with accurate calculations
     */
    ensureCalculationAccuracy(chartData, chartType) {
        switch (chartType) {
            case 'examPerformance':
                return this.validateExamPerformanceAccuracy(chartData);
            case 'distribution':
                return this.validateDistributionAccuracy(chartData);
            case 'passingRate':
                return this.validatePassingRateAccuracy(chartData);
            default:
                console.warn(`Unknown chart type for accuracy validation: ${chartType}`);
                return chartData;
        }
    }

    /**
     * Validate accuracy of exam performance calculations
     * @param {Object} examData - Exam performance data
     * @returns {Object} Validated exam data with accurate calculations
     */
    validateExamPerformanceAccuracy(examData) {
        const validated = {};
        
        for (const [examTitle, data] of Object.entries(examData)) {
            if (data && typeof data === 'object') {
                const passers = Math.max(0, Math.floor(Number(data.passers) || 0));
                const failers = Math.max(0, Math.floor(Number(data.failers) || 0));
                
                // Calculate total from components to ensure accuracy
                const calculatedTotal = passers + failers;
                
                validated[examTitle] = {
                    passers: passers,
                    failers: failers,
                    total: calculatedTotal,
                    // Add percentage calculations for reference
                    passingRate: calculatedTotal > 0 ? Math.round((passers / calculatedTotal) * 100 * 10) / 10 : 0
                };
            }
        }
        
        return validated;
    }

    /**
     * Validate accuracy of distribution calculations
     * @param {Object} distributionData - Distribution data
     * @returns {Object} Validated distribution data with accurate calculations
     */
    validateDistributionAccuracy(distributionData) {
        const passers = Math.max(0, Math.floor(Number(distributionData.totalPassers) || 0));
        const failers = Math.max(0, Math.floor(Number(distributionData.totalFailers) || 0));
        const total = passers + failers;
        
        return {
            totalPassers: passers,
            totalFailers: failers,
            total: total,
            passingRate: total > 0 ? Math.round((passers / total) * 100 * 10) / 10 : 0,
            failureRate: total > 0 ? Math.round((failers / total) * 100 * 10) / 10 : 0
        };
    }

    /**
     * Validate accuracy of passing rate calculations
     * @param {Object} passingRateData - Passing rate data
     * @returns {Object} Validated passing rate data with accurate calculations
     */
    validatePassingRateAccuracy(passingRateData) {
        if (!passingRateData || !passingRateData.data) {
            return { sections: [], subjects: [], data: {} };
        }

        const validated = {
            sections: passingRateData.sections || [],
            subjects: passingRateData.subjects || [],
            data: {}
        };

        // Validate each subject's data
        for (const subject of validated.subjects) {
            if (passingRateData.data[subject] && Array.isArray(passingRateData.data[subject])) {
                validated.data[subject] = passingRateData.data[subject].map(rate => {
                    const numRate = Number(rate);
                    if (isNaN(numRate)) return 0;
                    // Ensure rate is between 0 and 100 and properly rounded
                    return Math.round(Math.max(0, Math.min(100, numRate)) * 10) / 10;
                });
            } else {
                validated.data[subject] = new Array(validated.sections.length).fill(0);
            }
        }

        return validated;
    }

    /**
     * Show empty state message when no data is available
     * @param {string} canvasId - ID of the canvas element
     * @param {string} message - Message to display
     */
    showEmptyState(canvasId, message) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.warn(`Canvas element '${canvasId}' not found for empty state display`);
            return;
        }

        const container = canvas.parentElement;
        if (!container) {
            console.warn(`Container for canvas '${canvasId}' not found`);
            return;
        }

        // Hide canvas
        canvas.style.display = 'none';

        // Remove any existing empty state or error state
        const existingState = container.querySelector('.chart-empty-state, .chart-error-state');
        if (existingState) {
            existingState.remove();
        }

        // Determine appropriate icon and styling based on chart type
        const emptyStateConfig = this.getEmptyStateConfig(canvasId, message);

        // Create enhanced empty state message
        const emptyState = document.createElement('div');
        emptyState.className = `chart-empty-state ${emptyStateConfig.containerClass}`;
        emptyState.innerHTML = `
            <div class="text-center">
                <svg class="mx-auto ${emptyStateConfig.iconClass}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${emptyStateConfig.iconPath}" />
                </svg>
                <p class="${emptyStateConfig.titleClass}">${emptyStateConfig.title}</p>
                <p class="${emptyStateConfig.subtitleClass}">${emptyStateConfig.subtitle}</p>
                ${emptyStateConfig.actionHtml}
            </div>
        `;
        
        container.appendChild(emptyState);

        // Add accessibility attributes
        canvas.setAttribute('aria-label', `Empty chart: ${emptyStateConfig.title}`);
        canvas.setAttribute('role', 'img');
        
        // Log empty state for debugging
        console.info(`Empty state displayed for ${canvasId}: ${emptyStateConfig.title}`);
    }

    /**
     * Get configuration for empty state based on chart type and context
     * @param {string} canvasId - ID of the canvas element
     * @param {string} message - Original message
     * @returns {Object} Configuration object for empty state
     */
    getEmptyStateConfig(canvasId, message) {
        const baseConfig = {
            containerClass: 'p-8 text-center text-gray-500 bg-gray-50 rounded-lg border border-gray-200 min-h-[200px] flex items-center justify-center',
            iconClass: 'h-12 w-12 text-gray-400 mb-4',
            titleClass: 'text-sm font-medium text-gray-700 mb-2',
            subtitleClass: 'text-xs text-gray-500 mb-4',
            actionHtml: ''
        };

        // Customize based on chart type
        switch (canvasId) {
            case 'examPerformanceChart':
                return {
                    ...baseConfig,
                    iconPath: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
                    title: 'No Exam Performance Data',
                    subtitle: 'Create and activate exams to see student performance analytics',
                    actionHtml: `
                        <div class="mt-4">
                            <button class="text-xs bg-blue-100 hover:bg-blue-200 text-blue-700 px-4 py-2 rounded-md border border-blue-300 transition-colors duration-200" 
                                    onclick="window.location.href='/exams/create/'">
                                Create First Exam
                            </button>
                        </div>
                    `
                };

            case 'overallDistributionChart':
                return {
                    ...baseConfig,
                    iconPath: 'M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z',
                    title: 'No Student Attempts',
                    subtitle: 'Students need to complete exams to generate distribution data',
                    actionHtml: `
                        <div class="mt-4 text-xs text-gray-600">
                            <p>💡 Tip: Share exam links with students to get started</p>
                        </div>
                    `
                };

            case 'passingRateBySubjectChart':
                return {
                    ...baseConfig,
                    iconPath: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
                    title: 'No Subject Performance Data',
                    subtitle: 'Add subjects to your exams to track performance by subject area',
                    actionHtml: `
                        <div class="mt-4 text-xs text-gray-600">
                            <p>📚 Organize questions by subject for detailed analytics</p>
                        </div>
                    `
                };

            case 'scoreTrendChart':
                return {
                    ...baseConfig,
                    iconPath: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
                    title: 'No Exam History Yet',
                    subtitle: 'Complete some exams to see your progress over time',
                    actionHtml: `
                        <div class="mt-4">
                            <button class="text-xs bg-green-100 hover:bg-green-200 text-green-700 px-4 py-2 rounded-md border border-green-300 transition-colors duration-200" 
                                    onclick="window.location.href='/exams/'">
                                Browse Available Exams
                            </button>
                        </div>
                    `
                };

            case 'typePerformanceChart':
                return {
                    ...baseConfig,
                    iconPath: 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
                    title: 'No Question Type Data',
                    subtitle: 'Answer questions of different types to see your performance breakdown',
                    actionHtml: `
                        <div class="mt-4 text-xs text-gray-600">
                            <p>🎯 Try multiple choice, essay, and identification questions</p>
                        </div>
                    `
                };

            default:
                // Generic empty state
                return {
                    ...baseConfig,
                    iconPath: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
                    title: message || 'No Data Available',
                    subtitle: 'Data will appear here once available',
                    actionHtml: ''
                };
        }
    }

    /**
     * Show empty state for multiple charts at once
     * @param {Array} chartConfigs - Array of {canvasId, message} objects
     */
    showMultipleEmptyStates(chartConfigs) {
        chartConfigs.forEach(config => {
            this.showEmptyState(config.canvasId, config.message);
        });
    }

    /**
     * Clear empty state and restore canvas
     * @param {string} canvasId - ID of the canvas element
     */
    clearEmptyState(canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        const container = canvas.parentElement;
        if (!container) return;

        // Remove empty state
        const emptyState = container.querySelector('.chart-empty-state');
        if (emptyState) {
            emptyState.remove();
        }

        // Show canvas
        canvas.style.display = 'block';

        // Remove accessibility attributes
        canvas.removeAttribute('aria-label');
        canvas.removeAttribute('role');
    }
}

// Export for use in other modules
window.DashboardCharts = DashboardCharts;