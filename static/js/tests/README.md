# Dashboard Charts Property-Based Tests

This directory contains property-based tests for the dashboard charts functionality, specifically testing the empty state management feature.

## Overview

The tests validate **Property 5: Empty State Management** which ensures that appropriate empty state messages are displayed when no data is available for various chart types.

## Test Coverage

### Property Tests Included:

1. **Empty State Display**: Verifies empty states are shown for any valid chart canvas ID
2. **Configuration Consistency**: Ensures empty state configurations are consistent across chart types
3. **Empty State Cleanup**: Tests that empty states can be properly cleared and canvases restored
4. **Multiple Empty States**: Validates handling of multiple empty states without interference
5. **Invalid Canvas Handling**: Ensures graceful handling of invalid canvas IDs
6. **Message Customization**: Tests empty state behavior with custom messages
7. **DOM Structure Integrity**: Validates the generated DOM structure is valid and secure

## Requirements Validated

- **Requirement 2.4**: Empty state handling for missing data scenarios

## Setup and Installation

1. Navigate to the tests directory:
   ```bash
   cd static/js/tests
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Running Tests

### Run all tests:
```bash
npm test
```

### Run tests in watch mode:
```bash
npm run test:watch
```

### Run only property-based tests:
```bash
npm run test:pbt
```

### Run tests with coverage:
```bash
npm run test:coverage
```

## Test Configuration

- **Test Framework**: Jest
- **Property-Based Testing**: fast-check
- **DOM Environment**: JSDOM
- **Test Iterations**: 100 iterations per property test (configurable)
- **Timeout**: 30 seconds for property-based tests

## Test Structure

Each property test follows this pattern:

```javascript
test('should [behavior] for any [input type]', () => {
    fc.assert(fc.property(
        fc.[generator](),
        (input) => {
            // Arrange
            // Act  
            // Assert
        }
    ), { numRuns: 100 });
});
```

## Mocks and Setup

The tests include comprehensive mocks for:
- Chart.js library
- DOM environment (JSDOM)
- Window properties (innerWidth, innerHeight, devicePixelRatio)
- Browser APIs (ResizeObserver, requestAnimationFrame)

## Coverage

The tests provide coverage for:
- Empty state display logic
- Configuration generation
- DOM manipulation
- Error handling
- Accessibility attributes
- Security (no script injection)

## Integration with CI/CD

These tests can be integrated into continuous integration pipelines:

```yaml
# Example GitHub Actions step
- name: Run Dashboard Charts Tests
  run: |
    cd static/js/tests
    npm install
    npm test
```

## Debugging

To debug failing tests:

1. Run tests with verbose output:
   ```bash
   npm test -- --verbose
   ```

2. Run a specific test:
   ```bash
   npm test -- --testNamePattern="empty state display"
   ```

3. Enable console output in tests by modifying `jest.setup.js`

## Property-Based Testing Benefits

Property-based tests provide several advantages:

1. **Comprehensive Coverage**: Tests many input combinations automatically
2. **Edge Case Discovery**: Finds edge cases that manual tests might miss
3. **Regression Prevention**: Ensures properties hold across code changes
4. **Documentation**: Properties serve as executable specifications

## Maintenance

When modifying the dashboard charts code:

1. Run the property tests to ensure no regressions
2. Update test generators if new chart types are added
3. Add new properties for new functionality
4. Maintain the 100+ iteration count for thorough testing

## Troubleshooting

### Common Issues:

1. **JSDOM errors**: Ensure DOM setup is correct in test files
2. **Timeout errors**: Increase Jest timeout for complex property tests
3. **Mock issues**: Verify Chart.js mocks match actual API usage
4. **Path issues**: Ensure relative paths to source files are correct

### Performance:

- Property tests run 100 iterations by default
- Reduce `numRuns` for faster development cycles
- Use `--maxWorkers=1` for debugging race conditions