# TabMonitor Class Documentation

## Overview

The `TabMonitor` class provides client-side exam security by monitoring student tab activity during exams. It detects when students navigate away from the exam page, issues progressive warnings, and automatically submits exams after repeated violations.

## Features

### Core Functionality
- **Tab Switch Detection**: Uses the Page Visibility API to detect when students leave the exam tab
- **Progressive Warnings**: Issues 3 warnings before auto-submission
- **Auto-Submission**: Automatically submits exam on 4th violation
- **State Persistence**: Saves violation state to localStorage to survive page refreshes
- **Server Synchronization**: Syncs violation count with backend

### Error Handling
- **Network Resilience**: Queues violations when offline and syncs when connection restored
- **Retry Logic**: Uses exponential backoff for failed AJAX requests
- **Grace Period**: 2-second delay to avoid false positives from accidental clicks
- **Browser Compatibility**: Checks for Page Visibility API support

### User Experience
- **Clear Warnings**: Progressive warning modals with increasing severity
- **Visual Feedback**: Warning count display updates in real-time
- **Color Coding**: Green → Yellow → Orange → Red based on warning level

## Usage

### Basic Initialization

```javascript
// Initialize TabMonitor with attempt ID
const monitor = new TabMonitor(attemptId);

// Start monitoring
monitor.startMonitoring();
```

### With Options

```javascript
const monitor = new TabMonitor(attemptId, {
    maxWarnings: 3,        // Maximum warnings before auto-submit
    gracePeriod: 2000      // Milliseconds before recording violation
});
```

### Methods

#### `startMonitoring()`
Begins monitoring tab visibility. Adds event listeners and syncs with server.

#### `stopMonitoring()`
Stops monitoring and removes event listeners.

#### `getCurrentViolationCount()`
Returns the current warning count.

#### `isActive()`
Returns whether monitoring is currently active.

### HTML Requirements

The exam page should include a warning count display element:

```html
<div id="warning-count">
    <span class="warning-text">No warnings</span>
    <span class="warning-badge">0/3</span>
</div>
```

### Dependencies

- **AjaxClient**: From `utils.js` for AJAX requests
- **SweetAlert2**: For warning modals
- **Page Visibility API**: Browser support required

## API Endpoints

### Record Tab Switch
- **URL**: `/attempts/student/attempts/{attempt_id}/tab-switch/`
- **Method**: POST
- **Body**: `{ "violated_at": "ISO datetime string" }`
- **Response**: 
  ```json
  {
    "success": true,
    "warning_number": 1,
    "violation_id": 123,
    "should_auto_submit": false
  }
  ```

### Get Violations
- **URL**: `/attempts/student/attempts/{attempt_id}/violations/`
- **Method**: GET
- **Response**:
  ```json
  {
    "violation_count": 2,
    "is_flagged": false
  }
  ```

### Submit Exam
- **URL**: `/attempts/student/attempts/{attempt_id}/submit/`
- **Method**: POST
- **Body**: `{ "auto_submit": true }`
- **Response**:
  ```json
  {
    "success": true,
    "redirect_url": "/attempts/student/attempts/123/submitted/"
  }
  ```

## State Management

### LocalStorage Schema

```javascript
{
    "warningCount": 2,
    "currentViolationId": 456,
    "timestamp": 1701234567890,
    "violationQueue": [
        { "violated_at": "2024-12-07T10:30:00Z", "attempt_id": 123 }
    ]
}
```

### State Lifecycle

1. **Load**: On initialization, loads saved state from localStorage
2. **Validate**: Checks state age (must be < 1 hour old)
3. **Sync**: Syncs with server to get authoritative count
4. **Save**: Saves state after each violation
5. **Clear**: Clears state on exam submission

## Warning Progression

### Warning 1
- **Title**: "⚠️ Warning: Tab Switch Detected"
- **Color**: Yellow
- **Message**: "This is warning 1 of 3"

### Warning 2
- **Title**: "⚠️ Second Warning: Tab Switch Detected"
- **Color**: Yellow
- **Message**: "This is warning 2 of 3. One more violation and your exam will be automatically submitted!"

### Warning 3
- **Title**: "🚨 Final Warning: Tab Switch Detected"
- **Color**: Red
- **Message**: "This is your FINAL warning (3/3). If you switch tabs one more time, your exam will be automatically submitted and flagged for potential cheating."

### Violation 4
- **Action**: Auto-submit exam
- **Modal**: "🚨 Exam Auto-Submitted"
- **Result**: Exam flagged for review

## Error Scenarios

### Network Offline
- Violations queued locally
- Warning still shown to student
- Synced when connection restored

### AJAX Failure
- Retry with exponential backoff (3 attempts)
- Violation queued if all retries fail
- Student still sees warning

### Browser Unsupported
- Warning notification shown
- Monitoring disabled gracefully
- No errors thrown

### State Corruption
- Invalid localStorage data cleared
- Fresh state initialized
- Syncs with server for accurate count

## Testing

A test page is available at `static/js/test-tab-monitor.html` for manual testing:

1. Open the test page
2. Click "Start Monitoring"
3. Switch to another tab
4. Return to see the warning
5. Repeat to test all warning levels

## Requirements Validation

This implementation satisfies the following requirements:

- **2.1**: Records tab switch events with timestamps
- **2.2**: Detects new tabs/windows
- **2.3**: Detects application switches
- **2.4**: Records return events
- **2.5**: No violations when exam page is active
- **3.4**: State persists across page refreshes
- **7.1-7.5**: Warning count display and updates
- **8.5**: Network interruption handling

## Browser Compatibility

- **Chrome**: ✅ Full support
- **Firefox**: ✅ Full support
- **Safari**: ✅ Full support
- **Edge**: ✅ Full support
- **IE11**: ❌ Not supported (Page Visibility API)

## Security Considerations

- All violation logic enforced server-side
- Client cannot manipulate warning count on server
- Server validates all timestamps
- Auto-submission triggered by server response
- Attempt ownership verified on backend
