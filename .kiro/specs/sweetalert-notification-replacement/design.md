# Design Document: SweetAlert2 Notification Replacement

## Overview

This design document describes the architecture and implementation approach for replacing the current custom toast notification system with SweetAlert2. The solution will maintain backward compatibility with existing code while providing enhanced notification capabilities through SweetAlert2's rich feature set.

The implementation will follow a wrapper pattern, where the existing NotificationManager API is preserved but internally uses SweetAlert2 for rendering notifications. This approach minimizes code changes across the application while providing immediate benefits from SweetAlert2's features including better accessibility, animations, and cross-browser compatibility.

## Architecture

### Component Structure

```
┌─────────────────────────────────────────┐
│         Application Code                │
│  (grading.js, exam-timer.js, etc.)     │
└──────────────┬──────────────────────────┘
               │ calls
               ▼
┌─────────────────────────────────────────┐
│      NotificationManager Wrapper        │
│         (utils.js)                      │
│  - Maintains existing API               │
│  - Translates to SweetAlert2 calls      │
└──────────────┬──────────────────────────┘
               │ uses
               ▼
┌─────────────────────────────────────────┐
│         SweetAlert2 Library             │
│  - Renders notifications                │
│  - Handles animations                   │
│  - Manages accessibility                │
└─────────────────────────────────────────┘
```

### Integration Points

1. **Base Template (templates/base.html)**
   - Add SweetAlert2 CSS and JS files
   - Load before custom scripts to ensure availability

2. **Utility Module (static/js/utils.js)**
   - Replace NotificationManager implementation
   - Maintain existing method signatures
   - Add SweetAlert2 configuration

3. **Individual JavaScript Files**
   - student-history-filters.js: Replace custom showError function
   - grading.js: No changes needed (uses NotificationManager)
   - exam-timer.js: No changes needed (uses NotificationManager)
   - answer-saver.js: No changes needed (uses NotificationManager)
   - main.js: No changes needed (uses NotificationManager)

## Components and Interfaces

### SweetAlert2 Configuration

```javascript
// Default SweetAlert2 toast configuration
const SWAL_TOAST_CONFIG = {
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 5000,
    timerProgressBar: true,
    didOpen: (toast) => {
        toast.addEventListener('mouseenter', Swal.stopTimer);
        toast.addEventListener('mouseleave', Swal.resumeTimer);
    }
};
```

### NotificationManager Interface

The NotificationManager will maintain its existing public API:

```javascript
const NotificationManager = {
    /**
     * Show notification message
     * @param {string} message - Message text
     * @param {string} type - Message type (success, error, warning, info)
     * @param {number} duration - Duration in milliseconds (0 for persistent)
     * @returns {Promise} - SweetAlert2 promise
     */
    show(message, type = 'info', duration = 5000): Promise

    /**
     * Show success notification
     * @param {string} message - Message text
     * @param {number} duration - Duration in milliseconds
     * @returns {Promise} - SweetAlert2 promise
     */
    success(message, duration = 5000): Promise

    /**
     * Show error notification
     * @param {string} message - Message text
     * @param {number} duration - Duration in milliseconds
     * @returns {Promise} - SweetAlert2 promise
     */
    error(message, duration = 5000): Promise

    /**
     * Show warning notification
     * @param {string} message - Message text
     * @param {number} duration - Duration in milliseconds
     * @returns {Promise} - SweetAlert2 promise
     */
    warning(message, duration = 5000): Promise

    /**
     * Show info notification
     * @param {string} message - Message text
     * @param {number} duration - Duration in milliseconds
     * @returns {Promise} - SweetAlert2 promise
     */
    info(message, duration = 5000): Promise
}
```

### SweetAlert2 Type Mapping

| NotificationManager Type | SweetAlert2 Icon | Color Theme |
|-------------------------|------------------|-------------|
| success                 | success          | Green       |
| error                   | error            | Red         |
| warning                 | warning          | Yellow      |
| info                    | info             | Blue        |

## Data Models

### Notification Configuration Object

```javascript
{
    message: string,        // The notification message text
    type: string,          // Notification type: 'success', 'error', 'warning', 'info'
    duration: number,      // Auto-dismiss duration in milliseconds (0 = persistent)
    position: string,      // Position on screen (default: 'top-end')
    showConfirmButton: boolean,  // Show confirmation button (default: false for toast)
    timer: number,         // Auto-close timer in milliseconds
    timerProgressBar: boolean    // Show progress bar (default: true)
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: API Method Compatibility

*For any* valid message string and notification type (success, error, warning, info), calling the corresponding NotificationManager method should execute without throwing errors and should call SweetAlert2's fire method with appropriate parameters.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 3.1**

### Property 2: Duration Auto-Dismiss

*For any* notification with a duration value greater than zero, the notification should auto-dismiss after approximately that duration (within a tolerance of ±200ms for timing variations).

**Validates: Requirements 2.6**

### Property 3: Type-Icon Mapping

*For any* notification type from the set {success, error, warning, info}, the displayed SweetAlert2 notification should use the corresponding icon type consistently.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 4.5**

### Property 4: Message Preservation

*For any* non-empty message string (including strings with special characters, HTML entities, or Unicode), the displayed notification should contain that exact message text without modification.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

### Property 5: Position Consistency

*For any* notification displayed through NotificationManager, the SweetAlert2 configuration should specify position as 'top-end' (top-right corner).

**Validates: Requirements 4.1**

## Error Handling

### SweetAlert2 Loading Failure

**Scenario**: SweetAlert2 library fails to load from local files

**Handling**:
- Implement a fallback check in NotificationManager
- If Swal object is not available, log error to console
- Optionally fall back to browser's native alert() for critical messages
- Display console warning to developers

```javascript
if (typeof Swal === 'undefined') {
    console.error('SweetAlert2 not loaded. Notifications will not work.');
    // Fallback to console logging
    console.log(`[${type.toUpperCase()}] ${message}`);
    return Promise.resolve();
}
```

### Invalid Parameters

**Scenario**: NotificationManager methods called with invalid parameters

**Handling**:
- Validate message parameter (must be non-empty string)
- Validate type parameter (must be one of: success, error, warning, info)
- Validate duration parameter (must be non-negative number)
- Use sensible defaults for invalid values
- Log warnings for invalid parameters

```javascript
if (!message || typeof message !== 'string') {
    console.warn('Invalid message parameter for notification');
    return Promise.resolve();
}

if (!['success', 'error', 'warning', 'info'].includes(type)) {
    console.warn(`Invalid notification type: ${type}. Using 'info' as default.`);
    type = 'info';
}

if (typeof duration !== 'number' || duration < 0) {
    console.warn(`Invalid duration: ${duration}. Using default 5000ms.`);
    duration = 5000;
}
```

### Multiple Simultaneous Notifications

**Scenario**: Multiple notifications triggered in rapid succession

**Handling**:
- SweetAlert2 handles stacking automatically
- Configure queue behavior if needed
- Ensure notifications don't overlap visually
- Maintain readability with proper spacing

## Testing Strategy

### Unit Testing

Unit tests will verify specific notification behaviors:

1. **API Method Tests**
   - Test each NotificationManager method (show, success, error, warning, info)
   - Verify correct SweetAlert2 configuration is generated
   - Test with various parameter combinations

2. **Parameter Validation Tests**
   - Test with invalid message types (null, undefined, empty string)
   - Test with invalid duration values (negative, non-numeric)
   - Test with invalid notification types
   - Verify appropriate defaults are applied

3. **Configuration Tests**
   - Test toast configuration is correctly applied
   - Test position setting
   - Test timer configuration
   - Test progress bar visibility

### Property-Based Testing

Property-based tests will use a JavaScript PBT library (fast-check) to verify universal properties:

1. **Property Test: API Compatibility**
   - Generate random valid notification parameters
   - Call NotificationManager methods
   - Verify no errors are thrown
   - Verify Swal.fire is called with correct parameters

2. **Property Test: Duration Handling**
   - Generate random duration values (100ms to 10000ms)
   - Create notifications with those durations
   - Verify notifications auto-dismiss within tolerance

3. **Property Test: Message Preservation**
   - Generate random message strings (including special characters, HTML, long text)
   - Display notifications with those messages
   - Verify message content is preserved exactly

4. **Property Test: Type Mapping**
   - Generate random notification types from valid set
   - Create notifications with each type
   - Verify correct icon and color scheme are applied

### Integration Testing

Integration tests will verify the notification system works with existing code:

1. **Student History Filter Integration**
   - Trigger filter errors
   - Verify SweetAlert2 error notifications appear
   - Verify notifications auto-dismiss

2. **Grading System Integration**
   - Save grades successfully
   - Verify success notifications appear
   - Trigger grading errors
   - Verify error notifications appear

3. **Exam Timer Integration**
   - Trigger timer warnings
   - Verify warning notifications appear
   - Test time-up notification
   - Verify persistent notification behavior

4. **Answer Saver Integration**
   - Test connection status changes
   - Verify appropriate notifications appear
   - Test offline/online transitions

### Manual Testing Checklist

- [ ] Verify SweetAlert2 loads from local files (check Network tab)
- [ ] Test each notification type visually
- [ ] Verify notifications appear in top-right corner
- [ ] Test notification stacking with multiple simultaneous notifications
- [ ] Verify auto-dismiss timing is accurate
- [ ] Test persistent notifications (duration = 0)
- [ ] Verify notifications are keyboard accessible
- [ ] Test with screen reader for accessibility
- [ ] Verify notifications work in all supported browsers
- [ ] Test responsive behavior on mobile devices
- [ ] Verify no console errors when notifications are displayed
- [ ] Test notification appearance with long messages
- [ ] Verify hover behavior (pause timer on hover)

### Browser Compatibility Testing

Test in the following browsers:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

### Accessibility Testing

- Test with NVDA/JAWS screen readers
- Verify keyboard navigation
- Check color contrast ratios
- Test with browser zoom at 200%
- Verify focus management
