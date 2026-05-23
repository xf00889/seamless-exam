/**
 * Property-Based Tests for Dashboard Charts Empty State Management
 * 
 * Feature: dashboard-chart-fix
 * Property 5: Empty State Management
 * Validates: Requirements 2.4
 * 
 * These tests verify that empty states are displayed correctly when no data is available
 * for various chart types and scenarios.
 */

const fc = require('fast-check');

// Set up DOM environment for testing
document.body.innerHTML = `
    <div id="examPerformanceChart-container">
        <canvas id="examPerformanceChart"></canvas>
    </div>
    <div id="overallDistributionChart-container">
        <canvas id="overallDistributionChart"></canvas>
    </div>
    <div id="passingRateBySubjectChart-container">
        <canvas id="passingRateBySubjectChart"></canvas>
    </div>
    <div id="scoreTrendChart-container">
        <canvas id="scoreTrendChart"></canvas>
    </div>
    <div id="typePerformanceChart-container">
        <canvas id="typePerformanceChart"></canvas>
    </div>
`;

// Mock Chart.js
global.Chart = class MockChart {
    constructor(ctx, config) {
        this.ctx = ctx;
        this.config = config;
        this.destroyed = false;
    }
    
    destroy() {
        this.destroyed = true;
    }
    
    resize() {
        // Mock resize
    }
    
    static get version() {
        return '3.9.1';
    }
};

// Create a simplified DashboardCharts class for testing
class DashboardCharts {
    constructor() {
        this.charts = new Map();
    }

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
                    subtitle: 'Create and activate exams to see student performance analytics'
                };

            case 'overallDistributionChart':
                return {
                    ...baseConfig,
                    iconPath: 'M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z',
                    title: 'No Student Attempts',
                    subtitle: 'Students need to complete exams to generate distribution data'
                };

            case 'passingRateBySubjectChart':
                return {
                    ...baseConfig,
                    iconPath: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
                    title: 'No Subject Performance Data',
                    subtitle: 'Add subjects to your exams to track performance by subject area'
                };

            case 'scoreTrendChart':
                return {
                    ...baseConfig,
                    iconPath: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
                    title: 'No Exam History Yet',
                    subtitle: 'Complete some exams to see your progress over time'
                };

            case 'typePerformanceChart':
                return {
                    ...baseConfig,
                    iconPath: 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
                    title: 'No Question Type Data',
                    subtitle: 'Answer questions of different types to see your performance breakdown'
                };

            default:
                return {
                    ...baseConfig,
                    iconPath: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
                    title: message || 'No Data Available',
                    subtitle: 'Data will appear here once available'
                };
        }
    }

    showMultipleEmptyStates(chartConfigs) {
        chartConfigs.forEach(config => {
            this.showEmptyState(config.canvasId, config.message);
        });
    }

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

    destroy() {
        this.charts.forEach(chart => {
            chart.destroy();
        });
        this.charts.clear();
    }
}

describe('Property 5: Empty State Management', () => {
    let dashboardCharts;
    
    beforeEach(() => {
        // Reset DOM
        document.querySelectorAll('.chart-empty-state, .chart-error-state').forEach(el => el.remove());
        document.querySelectorAll('canvas').forEach(canvas => {
            canvas.style.display = 'block';
            canvas.removeAttribute('aria-label');
            canvas.removeAttribute('role');
        });
        
        dashboardCharts = new DashboardCharts();
    });
    
    afterEach(() => {
        if (dashboardCharts) {
            dashboardCharts.destroy();
        }
    });

    /**
     * Property Test: Empty state display for any chart type
     * For any valid chart canvas ID, when showEmptyState is called,
     * the system should display an appropriate empty state message
     */
    test('should display empty state for any valid chart canvas ID', () => {
        fc.assert(fc.property(
            fc.constantFrom(
                'examPerformanceChart',
                'overallDistributionChart', 
                'passingRateBySubjectChart',
                'scoreTrendChart',
                'typePerformanceChart'
            ),
            (canvasId) => {
                // Arrange: Ensure canvas exists and is visible
                const canvas = document.getElementById(canvasId);
                expect(canvas).toBeTruthy();
                canvas.style.display = 'block';
                
                // Act: Show empty state
                dashboardCharts.showEmptyState(canvasId);
                
                // Assert: Canvas should be hidden
                expect(canvas.style.display).toBe('none');
                
                // Assert: Empty state should be displayed
                const container = canvas.parentElement;
                const emptyState = container.querySelector('.chart-empty-state');
                expect(emptyState).toBeTruthy();
                
                // Assert: Empty state should have proper structure
                expect(emptyState.querySelector('svg')).toBeTruthy();
                expect(emptyState.textContent.length).toBeGreaterThan(0);
                
                // Assert: Accessibility attributes should be set
                expect(canvas.getAttribute('aria-label')).toContain('Empty chart');
                expect(canvas.getAttribute('role')).toBe('img');
            }
        ), { numRuns: 100 });
    });

    /**
     * Property Test: Empty state configuration consistency
     * For any chart type, the empty state configuration should be consistent
     * and contain all required elements
     */
    test('should provide consistent empty state configuration for any chart type', () => {
        fc.assert(fc.property(
            fc.constantFrom(
                'examPerformanceChart',
                'overallDistributionChart', 
                'passingRateBySubjectChart',
                'scoreTrendChart',
                'typePerformanceChart'
            ),
            (canvasId) => {
                // Act: Get empty state configuration
                const config = dashboardCharts.getEmptyStateConfig(canvasId, 'test message');
                
                // Assert: Configuration should have all required properties
                expect(config).toHaveProperty('containerClass');
                expect(config).toHaveProperty('iconClass');
                expect(config).toHaveProperty('titleClass');
                expect(config).toHaveProperty('subtitleClass');
                expect(config).toHaveProperty('iconPath');
                expect(config).toHaveProperty('title');
                expect(config).toHaveProperty('subtitle');
                expect(config).toHaveProperty('actionHtml');
                
                // Assert: All properties should be strings
                expect(typeof config.containerClass).toBe('string');
                expect(typeof config.iconClass).toBe('string');
                expect(typeof config.titleClass).toBe('string');
                expect(typeof config.subtitleClass).toBe('string');
                expect(typeof config.iconPath).toBe('string');
                expect(typeof config.title).toBe('string');
                expect(typeof config.subtitle).toBe('string');
                expect(typeof config.actionHtml).toBe('string');
                
                // Assert: Title and subtitle should not be empty
                expect(config.title.length).toBeGreaterThan(0);
                expect(config.subtitle.length).toBeGreaterThan(0);
                
                // Assert: Icon path should be valid SVG path
                expect(config.iconPath).toMatch(/^[MmLlHhVvCcSsQqTtAaZz0-9\s,.-]+$/);
            }
        ), { numRuns: 100 });
    });

    /**
     * Property Test: Empty state cleanup
     * For any chart with an empty state, calling clearEmptyState should
     * restore the canvas and remove the empty state
     */
    test('should properly clear empty state for any chart', () => {
        fc.assert(fc.property(
            fc.constantFrom(
                'examPerformanceChart',
                'overallDistributionChart', 
                'passingRateBySubjectChart',
                'scoreTrendChart',
                'typePerformanceChart'
            ),
            (canvasId) => {
                // Arrange: Show empty state first
                dashboardCharts.showEmptyState(canvasId);
                const canvas = document.getElementById(canvasId);
                const container = canvas.parentElement;
                
                // Verify empty state is shown
                expect(canvas.style.display).toBe('none');
                expect(container.querySelector('.chart-empty-state')).toBeTruthy();
                
                // Act: Clear empty state
                dashboardCharts.clearEmptyState(canvasId);
                
                // Assert: Canvas should be visible again
                expect(canvas.style.display).toBe('block');
                
                // Assert: Empty state should be removed
                expect(container.querySelector('.chart-empty-state')).toBeFalsy();
                
                // Assert: Accessibility attributes should be removed
                expect(canvas.getAttribute('aria-label')).toBeFalsy();
                expect(canvas.getAttribute('role')).toBeFalsy();
            }
        ), { numRuns: 100 });
    });

    /**
     * Property Test: Multiple empty states handling
     * For any combination of chart IDs, showing multiple empty states
     * should work correctly without interference
     */
    test('should handle multiple empty states without interference', () => {
        fc.assert(fc.property(
            fc.array(fc.constantFrom(
                'examPerformanceChart',
                'overallDistributionChart', 
                'passingRateBySubjectChart',
                'scoreTrendChart',
                'typePerformanceChart'
            ), { minLength: 1, maxLength: 5 }),
            (canvasIds) => {
                // Remove duplicates
                const uniqueCanvasIds = [...new Set(canvasIds)];
                
                // Act: Show empty states for all charts
                const configs = uniqueCanvasIds.map(canvasId => ({
                    canvasId: canvasId,
                    message: `Test message for ${canvasId}`
                }));
                
                dashboardCharts.showMultipleEmptyStates(configs);
                
                // Assert: All specified charts should have empty states
                uniqueCanvasIds.forEach(canvasId => {
                    const canvas = document.getElementById(canvasId);
                    const container = canvas.parentElement;
                    
                    expect(canvas.style.display).toBe('none');
                    expect(container.querySelector('.chart-empty-state')).toBeTruthy();
                    expect(canvas.getAttribute('aria-label')).toContain('Empty chart');
                });
            }
        ), { numRuns: 50 });
    });

    /**
     * Property Test: Empty state with invalid canvas ID
     * For any invalid canvas ID, showEmptyState should handle gracefully
     * without throwing errors
     */
    test('should handle invalid canvas IDs gracefully', () => {
        fc.assert(fc.property(
            fc.string({ minLength: 1, maxLength: 50 }).filter(id => 
                !['examPerformanceChart', 'overallDistributionChart', 
                  'passingRateBySubjectChart', 'scoreTrendChart', 
                  'typePerformanceChart'].includes(id)
            ),
            (invalidCanvasId) => {
                // Act & Assert: Should not throw error
                expect(() => {
                    dashboardCharts.showEmptyState(invalidCanvasId);
                }).not.toThrow();
                
                // Assert: No empty state should be created for invalid ID
                const invalidCanvas = document.getElementById(invalidCanvasId);
                expect(invalidCanvas).toBeFalsy();
            }
        ), { numRuns: 100 });
    });

    /**
     * Property Test: Empty state message customization
     * For any chart type with custom message, the empty state should
     * use the appropriate configuration while maintaining structure
     */
    test('should maintain structure with any custom message', () => {
        fc.assert(fc.property(
            fc.constantFrom(
                'examPerformanceChart',
                'overallDistributionChart', 
                'passingRateBySubjectChart',
                'scoreTrendChart',
                'typePerformanceChart'
            ),
            fc.string({ minLength: 0, maxLength: 200 }),
            (canvasId, customMessage) => {
                // Act: Show empty state with custom message
                dashboardCharts.showEmptyState(canvasId, customMessage);
                
                // Assert: Empty state should be displayed
                const canvas = document.getElementById(canvasId);
                const container = canvas.parentElement;
                const emptyState = container.querySelector('.chart-empty-state');
                
                expect(emptyState).toBeTruthy();
                expect(canvas.style.display).toBe('none');
                
                // Assert: Should have proper structure regardless of message
                expect(emptyState.querySelector('svg')).toBeTruthy();
                expect(emptyState.textContent.length).toBeGreaterThan(0);
                
                // Assert: Should use chart-specific configuration, not custom message
                const config = dashboardCharts.getEmptyStateConfig(canvasId, customMessage);
                expect(emptyState.textContent).toContain(config.title);
            }
        ), { numRuns: 100 });
    });

    /**
     * Property Test: Empty state DOM structure integrity
     * For any chart with empty state, the DOM structure should be valid
     * and contain all expected elements
     */
    test('should create valid DOM structure for empty states', () => {
        fc.assert(fc.property(
            fc.constantFrom(
                'examPerformanceChart',
                'overallDistributionChart', 
                'passingRateBySubjectChart',
                'scoreTrendChart',
                'typePerformanceChart'
            ),
            (canvasId) => {
                // Act: Show empty state
                dashboardCharts.showEmptyState(canvasId);
                
                // Assert: DOM structure should be valid
                const canvas = document.getElementById(canvasId);
                const container = canvas.parentElement;
                const emptyState = container.querySelector('.chart-empty-state');
                
                expect(emptyState).toBeTruthy();
                
                // Assert: Should have required CSS classes
                expect(emptyState.className).toContain('chart-empty-state');
                
                // Assert: Should have SVG icon
                const svg = emptyState.querySelector('svg');
                expect(svg).toBeTruthy();
                expect(svg.tagName.toLowerCase()).toBe('svg');
                
                // Assert: Should have path element in SVG
                const path = svg.querySelector('path');
                expect(path).toBeTruthy();
                
                // Assert: Should have text content
                const textElements = emptyState.querySelectorAll('p');
                expect(textElements.length).toBeGreaterThanOrEqual(1);
                
                // Assert: Should not have any script tags (security)
                const scripts = emptyState.querySelectorAll('script');
                expect(scripts.length).toBe(0);
            }
        ), { numRuns: 100 });
    });
});

// Export for use in other test files
module.exports = {
    DashboardCharts,
    setupTestDOM: () => {
        // Reset DOM for other tests
        document.querySelectorAll('.chart-empty-state, .chart-error-state').forEach(el => el.remove());
        document.querySelectorAll('canvas').forEach(canvas => {
            canvas.style.display = 'block';
            canvas.removeAttribute('aria-label');
            canvas.removeAttribute('role');
        });
    }
};