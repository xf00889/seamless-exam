/**
 * Jest setup file for dashboard charts tests
 * Configures the testing environment and global mocks
 */

// Configure Jest timeout for property-based tests
jest.setTimeout(30000);

// Global test configuration
global.console = {
    ...console,
    // Suppress console.warn and console.info during tests unless needed
    warn: jest.fn(),
    info: jest.fn(),
    error: console.error, // Keep errors visible
    log: console.log // Keep logs visible for debugging
};

// Mock window.devicePixelRatio
Object.defineProperty(window, 'devicePixelRatio', {
    value: 1,
    writable: true
});

// Mock window.innerWidth and innerHeight for responsive tests
Object.defineProperty(window, 'innerWidth', {
    value: 1024,
    writable: true
});

Object.defineProperty(window, 'innerHeight', {
    value: 768,
    writable: true
});

// Mock ResizeObserver if needed
global.ResizeObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn()
}));

// Mock requestAnimationFrame
global.requestAnimationFrame = jest.fn(cb => setTimeout(cb, 0));
global.cancelAnimationFrame = jest.fn(id => clearTimeout(id));

// Setup for property-based testing
beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
    
    // Reset console mocks
    global.console.warn.mockClear();
    global.console.info.mockClear();
});

afterEach(() => {
    // Clean up any timers
    jest.clearAllTimers();
});