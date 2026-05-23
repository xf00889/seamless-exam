/**
 * Integration Test with Real Django Data
 * Tests the complete data flow from Django context to chart rendering
 * 
 * This test uses actual data from the debug script to verify:
 * - JSON data parsing from script tags
 * - Data validation and accuracy
 * - Chart rendering with production data
 * - Error handling in realistic scenarios
 */

// Load the modules by reading and evaluating them
const fs = require('fs');
const path = require('path');

// Load DashboardCharts
const dashboardChartsPath = path.join(__dirname, '../pages/dashboard-charts.js');
const dashboardChartsCode = fs.readFileSync(dashboardChartsPath, 'utf8');
eval(dashboardChartsCode);

// Load DashboardDataLoader
const dashboardDataLoaderPath = path.join(__dirname, '../utils/dashboard-data-loader.js');
const dashboardDataLoaderCode = fs.readFileSync(dashboardDataLoaderPath, 'utf8');
eval(dashboardDataLoaderCode);

// Real data from debug_charts.py output
const REAL_EXAM_PERFORMANCE_DATA = {
    "test": {"passers": 2, "failers": 1, "total": 3},
    "Science 12 Summative": {"passers": 3, "failers": 1, "total": 4},
    "Science 12": {"passers": 1, "failers": 0, "total": 1}
};

const REAL_DASHBOARD_CONFIG = {
    "total_students": 5,
    "total_exams": 7,
    "total_passers": 6,
    "total_failers": 2
};

const REAL_PASSING_RATE_DATA = {
    "sections": ["Grade 12 A", "Grade 12 B"],
    "subjects": ["Science", "Mathematics", "English"],
    "data": {
        "Science": [75.5, 82.3],
        "Mathematics": [68.2, 71.8],
        "English": [89.1, 85.7]
    }
};

describe('Integration Test: Real Django Data Flow', () => {
    let mockCanvas, mockContext, mockChart;
    let originalChart;

    beforeEach(() => {
        // Setup DOM environment
        document.body.innerHTML = `
            <div id="test-container">
                <!-- Exam Performance Chart -->
                <div class="chart-container">
                    <canvas id="examPerformanceChart"></canvas>
                </div>
                
                <!-- Overall Distribution Chart -->
                <div class="chart-container">
                    <canvas id="overallDistributionChart"></canvas>
                </div>
                
                <!-- Passing Rate Chart -->
                <div class="chart-container">
                    <canvas id="passingRateBySubjectChart"></canvas>
                </div>
                
                <!-- JSON Script Tags (simulating Django template) -->
                <script id="exam-performance-data" type="application/json">
                    ${JSON.stringify(REAL_EXAM_PERFORMANCE_DATA)}
                </script>
                
                <script id="dashboard-config-data" type="application/json">
                    ${JSON.stringify(REAL_DASHBOARD_CONFIG)}
                </script>
                
                <script id="passing-rate-data" type="application/json">
                    ${JSON.stringify(REAL_PASSING_RATE_DATA)}
                </script>
            </div>
        `;

        // Mock Chart.js
        mockContext = {
            getContext: jest.fn().mockReturnValue({}),
            style: {},
            parentElement: document.querySelector('.chart-container')
        };
        
        mockCanvas = {
            getContext: jest.fn().mockReturnValue(mockContext),
            style: {},
            parentElement: document.querySelector('.chart-container')
        };

        mockChart = {
            destroy: jest.fn(),
            resize: jest.fn(),
            update: jest.fn(),
            data: { labels: [], datasets: [] },
            options: {},
            config: { type: 'bar' },
            canvas: mockCanvas
        };

        // Mock Chart.js constructor
        originalChart = global.Chart;
        global.Chart = jest.fn().mockImplementation(() => mockChart);
        global.Chart.version = '3.9.1';
        global.Chart.registry = { controllers: { bar: true, doughnut: true, line: true } };

        // Mock canvas elements
        jest.spyOn(document, 'getElementById').mockImplementation((id) => {
            if (id.includes('Chart')) {
                return mockCanvas;
            }
            return document.querySelector(`#${id}`);
        });

        // Mock window properties
        Object.defineProperty(window, 'innerWidth', { value: 1024, writable: true });
        Object.defineProperty(window, 'innerHeight', { value: 768, writable: true });
        Object.defineProperty(window, 'devicePixelRatio', { value: 1, writable: true });
    });

    afterEach(() => {
        global.Chart = originalChart;
        document.body.innerHTML = '';
        jest.restoreAllMocks();
    });

    describe('Real Data Parsing and Validation', () => {
        test('should parse real exam performance data correctly', () => {
            const parsedData = DashboardDataLoader.parseJsonScript('exam-performance-data');
            
            expect(parsedData).toEqual(REAL_EXAM_PERFORMANCE_DATA);
            expect(parsedData).toHaveProperty('test');
            expect(parsedData).toHaveProperty('Science 12 Summative');
            expect(parsedData).toHaveProperty('Science 12');
            
            // Verify data structure
            Object.values(parsedData).forEach(examData => {
                expect(examData).toHaveProperty('passers');
                expect(examData).toHaveProperty('failers');
                expect(examData).toHaveProperty('total');
                expect(typeof examData.passers).toBe('number');
                expect(typeof examData.failers).toBe('number');
                expect(typeof examData.total).toBe('number');
            });
        });

        test('should parse real dashboard config correctly', () => {
            const parsedConfig = DashboardDataLoader.parseJsonScript('dashboard-config-data');
            
            expect(parsedConfig).toEqual(REAL_DASHBOARD_CONFIG);
            expect(parsedConfig.total_students).toBe(5);
            expect(parsedConfig.total_exams).toBe(7);
            expect(parsedConfig.total_passers).toBe(6);
            expect(parsedConfig.total_failers).toBe(2);
        });

        test('should validate real data accuracy calculations', () => {
            const dashboardCharts = new DashboardCharts();
            const validatedData = dashboardCharts.validateExamPerformanceAccuracy(REAL_EXAM_PERFORMANCE_DATA);
            
            // Verify calculations are accurate
            Object.entries(validatedData).forEach(([examTitle, data]) => {
                const calculatedTotal = data.passers + data.failers;
                expect(data.total).toBe(calculatedTotal);
                
                // Verify passing rate calculation
                const expectedPassingRate = calculatedTotal > 0 ? 
                    Math.round((data.passers / calculatedTotal) * 100 * 10) / 10 : 0;
                expect(data.passingRate).toBe(expectedPassingRate);
            });
        });
    });

    describe('Chart Rendering with Real Data', () => {
        test('should render exam performance chart with real data', () => {
            const dashboardCharts = new DashboardCharts();
            
            // Initialize with real data
            dashboardCharts.createExamPerformanceChart(REAL_EXAM_PERFORMANCE_DATA);
            
            // Verify Chart.js was called with correct data
            expect(global.Chart).toHaveBeenCalledWith(
                expect.any(Object),
                expect.objectContaining({
                    type: 'bar',
                    data: expect.objectContaining({
                        labels: ['test', 'Science 12 Summative', 'Science 12'],
                        datasets: expect.arrayContaining([
                            expect.objectContaining({
                                label: 'Passers (≥60%)',
                                data: [2, 3, 1]
                            }),
                            expect.objectContaining({
                                label: 'Failures (<60%)',
                                data: [1, 1, 0]
                            })
                        ])
                    })
                })
            );
        });

        test('should render overall distribution chart with real data', () => {
            const dashboardCharts = new DashboardCharts();
            
            // Initialize with real data
            dashboardCharts.createOverallDistributionChart(
                REAL_DASHBOARD_CONFIG.total_passers,
                REAL_DASHBOARD_CONFIG.total_failers
            );
            
            // Verify Chart.js was called with correct data
            expect(global.Chart).toHaveBeenCalledWith(
                expect.any(Object),
                expect.objectContaining({
                    type: 'doughnut',
                    data: expect.objectContaining({
                        labels: ['Passers (≥60%)', 'Failures (<60%)'],
                        datasets: expect.arrayContaining([
                            expect.objectContaining({
                                data: [6, 2]
                            })
                        ])
                    })
                })
            );
        });

        test('should render passing rate chart with real data', () => {
            const dashboardCharts = new DashboardCharts();
            
            // Initialize with real data
            dashboardCharts.createPassingRateBySubjectChart(REAL_PASSING_RATE_DATA);
            
            // Verify Chart.js was called with correct structure
            expect(global.Chart).toHaveBeenCalledWith(
                expect.any(Object),
                expect.objectContaining({
                    type: 'bar',
                    data: expect.objectContaining({
                        labels: ['Grade 12 A', 'Grade 12 B'],
                        datasets: expect.arrayContaining([
                            expect.objectContaining({
                                label: 'Science',
                                data: [75.5, 82.3]
                            }),
                            expect.objectContaining({
                                label: 'Mathematics',
                                data: [68.2, 71.8]
                            }),
                            expect.objectContaining({
                                label: 'English',
                                data: [89.1, 85.7]
                            })
                        ])
                    })
                })
            );
        });
    });

    describe('Complete Integration Flow', () => {
        test('should complete full teacher dashboard initialization with real data', () => {
            // Simulate complete initialization flow
            const success = DashboardDataLoader.initDashboardWithEnhancedErrorHandling('teacher', {
                totalStudents: REAL_DASHBOARD_CONFIG.total_students,
                totalExams: REAL_DASHBOARD_CONFIG.total_exams,
                totalPassers: REAL_DASHBOARD_CONFIG.total_passers,
                totalFailers: REAL_DASHBOARD_CONFIG.total_failers
            }, {
                templateName: 'teacher_dashboard.html',
                hasExamPerformanceData: true,
                hasPassingRateData: true,
                hasClassStatistics: true
            });
            
            expect(success).toBe(true);
            
            // Verify all charts were initialized
            expect(global.Chart).toHaveBeenCalledTimes(3); // exam performance, distribution, passing rate
        });

        test('should handle data accuracy requirements correctly', () => {
            const dashboardCharts = new DashboardCharts();
            
            // Test with real data that should maintain accuracy
            const validatedExamData = dashboardCharts.validateExamPerformanceAccuracy(REAL_EXAM_PERFORMANCE_DATA);
            
            // Verify Requirements 2.1, 2.2, 2.3: Chart accuracy
            Object.entries(validatedExamData).forEach(([examTitle, data]) => {
                // Requirement 2.1: Accurate pass/fail counts
                expect(data.passers).toBeGreaterThanOrEqual(0);
                expect(data.failers).toBeGreaterThanOrEqual(0);
                
                // Requirement 2.2: Correct total calculations
                expect(data.total).toBe(data.passers + data.failers);
                
                // Requirement 2.3: Accurate percentage calculations
                const expectedPassingRate = data.total > 0 ? 
                    Math.round((data.passers / data.total) * 100 * 10) / 10 : 0;
                expect(data.passingRate).toBe(expectedPassingRate);
            });
        });

        test('should handle empty data gracefully', () => {
            // Test with empty data to verify empty state handling
            document.getElementById('exam-performance-data').textContent = '{}';
            document.getElementById('dashboard-config-data').textContent = JSON.stringify({
                total_students: 0,
                total_exams: 0,
                total_passers: 0,
                total_failers: 0
            });
            
            const success = DashboardDataLoader.initDashboardWithEnhancedErrorHandling('teacher', {}, {
                templateName: 'teacher_dashboard.html',
                hasExamPerformanceData: false,
                hasPassingRateData: false,
                hasClassStatistics: false
            });
            
            // Should still succeed but show empty states
            expect(success).toBe(true);
        });
    });

    describe('Error Handling with Real Scenarios', () => {
        test('should handle malformed JSON gracefully', () => {
            // Simulate malformed JSON from Django template
            document.getElementById('exam-performance-data').textContent = '{"test": {"passers": 2, "failers": 1, "total": 3}'; // Missing closing brace
            
            const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
            
            const parsedData = DashboardDataLoader.parseJsonScript('exam-performance-data');
            
            expect(parsedData).toBeNull();
            expect(consoleSpy).toHaveBeenCalled();
            
            consoleSpy.mockRestore();
        });

        test('should handle missing script elements', () => {
            // Remove a required script element
            document.getElementById('exam-performance-data').remove();
            
            const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
            
            const parsedData = DashboardDataLoader.parseJsonScript('exam-performance-data');
            
            expect(parsedData).toBeNull();
            expect(consoleSpy).toHaveBeenCalled();
            
            consoleSpy.mockRestore();
        });

        test('should validate data types and handle invalid values', () => {
            // Test with invalid data types
            const invalidData = {
                "test": {"passers": "invalid", "failers": null, "total": undefined},
                "Science 12": {"passers": NaN, "failers": -1, "total": Infinity}
            };
            
            const dashboardCharts = new DashboardCharts();
            const validatedData = dashboardCharts.validateExamPerformanceAccuracy(invalidData);
            
            // Should clean up invalid data
            expect(validatedData.test.passers).toBe(0); // "invalid" -> 0
            expect(validatedData.test.failers).toBe(0); // null -> 0
            expect(validatedData.test.total).toBe(0); // calculated from passers + failers
            
            expect(validatedData["Science 12"].passers).toBe(0); // NaN -> 0
            expect(validatedData["Science 12"].failers).toBe(0); // -1 -> 0 (negative not allowed)
            expect(validatedData["Science 12"].total).toBe(0); // calculated total
        });
    });

    describe('Performance and Responsiveness', () => {
        test('should handle large datasets efficiently', () => {
            // Create a large dataset to test performance
            const largeExamData = {};
            for (let i = 0; i < 100; i++) {
                largeExamData[`Exam ${i}`] = {
                    passers: Math.floor(Math.random() * 50),
                    failers: Math.floor(Math.random() * 20),
                    total: 0 // Will be calculated
                };
                largeExamData[`Exam ${i}`].total = 
                    largeExamData[`Exam ${i}`].passers + largeExamData[`Exam ${i}`].failers;
            }
            
            const startTime = performance.now();
            
            const dashboardCharts = new DashboardCharts();
            const validatedData = dashboardCharts.validateExamPerformanceAccuracy(largeExamData);
            
            const endTime = performance.now();
            const processingTime = endTime - startTime;
            
            // Should process large dataset quickly (under 100ms)
            expect(processingTime).toBeLessThan(100);
            expect(Object.keys(validatedData)).toHaveLength(100);
        });

        test('should adapt to different screen sizes', () => {
            const dashboardCharts = new DashboardCharts();
            
            // Test mobile screen size
            Object.defineProperty(window, 'innerWidth', { value: 480, writable: true });
            Object.defineProperty(window, 'innerHeight', { value: 800, writable: true });
            
            dashboardCharts.createExamPerformanceChart(REAL_EXAM_PERFORMANCE_DATA);
            
            // Verify mobile-specific options were applied
            const chartCall = global.Chart.mock.calls[0];
            const chartOptions = chartCall[1].options;
            
            expect(chartOptions.maintainAspectRatio).toBe(false); // Mobile should allow flexible aspect ratio
            expect(chartOptions.plugins.legend.position).toMatch(/bottom|right/); // Mobile legend positioning
        });
    });
});

describe('Integration Test: Production Environment Simulation', () => {
    test('should work with actual Django template structure', () => {
        // Simulate the exact structure from teacher_dashboard.html
        document.body.innerHTML = `
            <div class="container mx-auto px-4 py-0">
                <!-- Charts Section -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-6 sm:mb-8">
                    <!-- Pass/Fail by Exam Chart -->
                    <div class="bg-white rounded-lg shadow-md overflow-hidden">
                        <div class="p-4 sm:p-6">
                            <div class="chart-container chart-container-md">
                                <canvas id="examPerformanceChart"></canvas>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Overall Pass/Fail Distribution -->
                    <div class="bg-white rounded-lg shadow-md overflow-hidden">
                        <div class="p-4 sm:p-6">
                            <div class="chart-container chart-container-md">
                                <canvas id="overallDistributionChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Passing Rate by Subject per Section Chart -->
                <div class="bg-white rounded-lg shadow-md overflow-hidden mb-6 sm:mb-8">
                    <div class="p-4 sm:p-6">
                        <div class="chart-container chart-container-lg">
                            <canvas id="passingRateBySubjectChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Chart Data from Django Context -->
            <script id="exam-performance-data" type="application/json">
                ${JSON.stringify(REAL_EXAM_PERFORMANCE_DATA)}
            </script>
            <script id="passing-rate-data" type="application/json">
                ${JSON.stringify(REAL_PASSING_RATE_DATA)}
            </script>
            <script id="dashboard-config-data" type="application/json">
                ${JSON.stringify(REAL_DASHBOARD_CONFIG)}
            </script>
        `;

        // Mock Chart.js and canvas elements
        const mockChart = { destroy: jest.fn(), resize: jest.fn(), update: jest.fn() };
        global.Chart = jest.fn().mockReturnValue(mockChart);
        global.Chart.version = '3.9.1';

        const mockCanvas = {
            getContext: jest.fn().mockReturnValue({}),
            style: {},
            parentElement: document.querySelector('.chart-container')
        };

        jest.spyOn(document, 'getElementById').mockImplementation((id) => {
            if (id.includes('Chart')) return mockCanvas;
            return document.querySelector(`#${id}`);
        });

        // Test the complete initialization as it would happen in production
        const success = DashboardDataLoader.initDashboardWithEnhancedErrorHandling('teacher', {
            totalStudents: REAL_DASHBOARD_CONFIG.total_students,
            totalExams: REAL_DASHBOARD_CONFIG.total_exams,
            totalPassers: REAL_DASHBOARD_CONFIG.total_passers,
            totalFailers: REAL_DASHBOARD_CONFIG.total_failers
        }, {
            templateName: 'teacher_dashboard.html',
            hasExamPerformanceData: true,
            hasPassingRateData: true,
            hasClassStatistics: true
        });

        expect(success).toBe(true);
        expect(global.Chart).toHaveBeenCalledTimes(3);
    });
});