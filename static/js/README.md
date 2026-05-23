# JavaScript Utilities Documentation

## Overview

The `utils.js` file provides a comprehensive set of utility functions for the Offline Exam System. All utilities are designed to work in external JavaScript files only, following requirements 17.2 and 17.4.

## Table of Contents

1. [Dashboard Charts](#dashboard-charts)
2. [AJAX Utilities](#ajax-utilities)
3. [Cookie Utilities](#cookie-utilities)
4. [Local Storage Utilities](#local-storage-utilities)
5. [Form Utilities](#form-utilities)
6. [DOM Utilities](#dom-utilities)
7. [Notification Manager](#notification-manager)
8. [String Utilities](#string-utilities)
9. [Validation Utilities](#validation-utilities)
10. [Date/Time Utilities](#datetime-utilities)

---

## Dashboard Charts

### DashboardCharts

Chart.js integration for student dashboard visualizations. Provides interactive charts for score trends and question type performance.

**Requirements:** 8.1, 8.2, 8.4, 8.5, 9.4

**Dependencies:**
- Chart.js v4.4.0 (included as `chart.min.js`)

**Methods:**

- `init(data)` - Initialize all dashboard charts
- `initScoreTrendChart(trendData)` - Create line chart for score trends
- `initTypePerformanceChart(typeData)` - Create bar chart for question type performance
- `showEmptyState(canvasId, message)` - Display empty state when no data available

**Data Structure:**

```javascript
const chartData = {
    scoreTrend: [
        {
            exam_name: "Quiz 1",
            date: "2024-01-15T10:00:00",
            percentage: 75.5,
            score: 15.1,
            total_possible: 20
        }
        // ... more exams
    ],
    typePerformance: {
        "Multiple Choice": 85.5,
        "Identification": 78.2,
        "Enumeration": 82.0,
        "Essay": 75.8
    }
};
```

**Example:**

```javascript
// Initialize charts with data from backend
DashboardCharts.init({
    scoreTrend: scoreTrendData,
    typePerformance: typePerformanceData
});
```

**Features:**

- **Score Trend Chart:**
  - Line chart showing performance over time
  - Passing threshold line at 60% (dashed red line)
  - Interactive tooltips with exam name, date, and score
  - Responsive design for mobile devices
  - Smooth curve interpolation

- **Question Type Performance Chart:**
  - Horizontal bar chart showing average scores by type
  - Color-coded bars for each question type
  - Performance indicators in tooltips
  - Responsive layout

**Testing:**

A test page is available at `static/js/test-charts.html` to verify Chart.js integration works correctly.

---

## AJAX Utilities

### AjaxClient

A robust AJAX client with automatic retry logic and error handling.

**Constructor Options:**
```javascript
const client = new AjaxClient({
    maxRetries: 3,        // Maximum number of retry attempts
    retryDelay: 1000,     // Initial retry delay in milliseconds
    timeout: 30000,       // Request timeout in milliseconds
    headers: {}           // Additional headers
});
```

**Methods:**

- `get(url, options)` - Perform GET request
- `post(url, data, options)` - Perform POST request
- `put(url, data, options)` - Perform PUT request
- `delete(url, options)` - Perform DELETE request

**Example:**
```javascript
const client = new AjaxClient({ maxRetries: 3 });

try {
    const response = await client.post('/api/save-answer', {
        question_id: 1,
        answer: 'My answer'
    });
    const data = await response.json();
    console.log('Success:', data);
} catch (error) {
    console.error('Error:', error);
}
```

---

## Cookie Utilities

### CookieUtils

Utilities for managing browser cookies.

**Methods:**

- `getCookie(name)` - Get cookie value by name
- `setCookie(name, value, days, options)` - Set a cookie
- `deleteCookie(name)` - Delete a cookie

**Example:**
```javascript
// Set a cookie
CookieUtils.setCookie('user_preference', 'dark_mode', 7);

// Get a cookie
const preference = CookieUtils.getCookie('user_preference');

// Delete a cookie
CookieUtils.deleteCookie('user_preference');

// Get CSRF token (common use case)
const csrfToken = CookieUtils.getCookie('csrftoken');
```

---

## Local Storage Utilities

### StorageUtils

Utilities for managing browser local storage with automatic JSON serialization.

**Methods:**

- `get(key, defaultValue)` - Get item from storage
- `set(key, value)` - Set item in storage
- `remove(key)` - Remove item from storage
- `clear()` - Clear all items
- `has(key)` - Check if key exists
- `keys()` - Get all keys

**Example:**
```javascript
// Store an object
StorageUtils.set('exam_state', {
    attemptId: 123,
    currentQuestion: 5,
    answers: []
});

// Retrieve the object
const state = StorageUtils.get('exam_state', {});

// Check if exists
if (StorageUtils.has('exam_state')) {
    console.log('State found');
}

// Remove
StorageUtils.remove('exam_state');
```

---

## Form Utilities

### FormUtils

Utilities for working with HTML forms.

**Methods:**

- `serialize(form)` - Serialize form to object
- `serializeJSON(form)` - Serialize form to JSON string
- `serializeQuery(form)` - Serialize form to URL query string
- `populate(form, data)` - Populate form with data
- `reset(form)` - Reset form and clear validation errors
- `disable(form)` - Disable all form inputs
- `enable(form)` - Enable all form inputs

**Example:**
```javascript
const form = document.getElementById('myForm');

// Serialize to object
const data = FormUtils.serialize(form);
console.log(data); // { username: 'john', email: 'john@example.com' }

// Serialize to JSON
const json = FormUtils.serializeJSON(form);

// Populate form
FormUtils.populate(form, {
    username: 'jane',
    email: 'jane@example.com'
});

// Disable during submission
FormUtils.disable(form);
```

---

## DOM Utilities

### DOMUtils

Utilities for DOM manipulation.

**Methods:**

- `createElement(tag, attributes, content)` - Create element with attributes
- `remove(element)` - Remove element from DOM
- `show(element)` - Show element (remove 'hidden' class)
- `hide(element)` - Hide element (add 'hidden' class)
- `toggle(element)` - Toggle element visibility

**Example:**
```javascript
// Create element
const button = DOMUtils.createElement('button', {
    className: 'btn btn-primary',
    dataset: { action: 'submit' }
}, 'Click Me');

// Show/hide elements
DOMUtils.hide('#loading-spinner');
DOMUtils.show('#content');

// Toggle
DOMUtils.toggle('.sidebar');
```

---

## Notification Manager

### NotificationManager

Display toast-style notifications to users.

**Methods:**

- `show(message, type, duration)` - Show notification
- `success(message, duration)` - Show success notification
- `error(message, duration)` - Show error notification
- `warning(message, duration)` - Show warning notification
- `info(message, duration)` - Show info notification

**Example:**
```javascript
// Show success message
NotificationManager.success('Answer saved successfully!');

// Show error with custom duration
NotificationManager.error('Failed to save answer', 10000);

// Show persistent warning (duration = 0)
NotificationManager.warning('Connection lost', 0);

// Generic notification
NotificationManager.show('Processing...', 'info', 3000);
```

---

## String Utilities

### StringUtils

Utilities for string manipulation.

**Methods:**

- `capitalize(str)` - Capitalize first letter
- `titleCase(str)` - Convert to title case
- `truncate(str, length, suffix)` - Truncate string
- `escapeHtml(str)` - Escape HTML special characters
- `stripHtml(html)` - Strip HTML tags

**Example:**
```javascript
// Capitalize
StringUtils.capitalize('hello'); // 'Hello'

// Title case
StringUtils.titleCase('hello world'); // 'Hello World'

// Truncate
StringUtils.truncate('This is a long string', 10); // 'This is...'

// Escape HTML
StringUtils.escapeHtml('<script>alert("xss")</script>');
// '&lt;script&gt;alert("xss")&lt;/script&gt;'
```

---

## Validation Utilities

### ValidationUtils

Utilities for input validation.

**Methods:**

- `isEmail(email)` - Validate email format
- `isUrl(url)` - Validate URL format
- `isNumber(value)` - Check if value is a number
- `isInteger(value)` - Check if value is an integer
- `isEmpty(value)` - Check if value is empty

**Example:**
```javascript
// Validate email
if (ValidationUtils.isEmail('test@example.com')) {
    console.log('Valid email');
}

// Validate URL
if (ValidationUtils.isUrl('https://example.com')) {
    console.log('Valid URL');
}

// Check if empty
if (ValidationUtils.isEmpty(inputValue)) {
    console.log('Input is empty');
}
```

---

## Date/Time Utilities

### DateUtils

Utilities for date and time formatting.

**Methods:**

- `format(date, options)` - Format date to readable string
- `formatTime(date)` - Format time to readable string
- `formatDateTime(date)` - Format date and time
- `relative(date)` - Get relative time string (e.g., "2 hours ago")

**Example:**
```javascript
const now = new Date();

// Format date
DateUtils.format(now); // 'Dec 4, 2025'

// Format time
DateUtils.formatTime(now); // '2:30 PM'

// Format date and time
DateUtils.formatDateTime(now); // 'Dec 4, 2025 2:30 PM'

// Relative time
DateUtils.relative(new Date(Date.now() - 3600000)); // '1 hours ago'
```

---

## Testing

A test page is available at `static/js/utils.test.html` to verify all utility functions work correctly. Open this file in a browser to run interactive tests.

---

## Requirements

This module satisfies the following requirements:

- **Requirement 17.2**: All JavaScript must be in external files
- **Requirement 17.4**: No inline JavaScript in HTML templates

All utilities are exported to the global `window` object for easy access across all JavaScript files in the application.

---

## Legacy Compatibility

For backward compatibility with existing code, the `getCookie` function is also exposed globally:

```javascript
// Both work the same
const token1 = CookieUtils.getCookie('csrftoken');
const token2 = getCookie('csrftoken');
```

---

## Error Handling

All utilities include proper error handling:

- AJAX requests automatically retry on network errors
- Storage operations catch and log errors
- Form operations validate inputs before processing
- Notifications handle missing DOM elements gracefully

---

## Browser Support

These utilities work in all modern browsers that support:
- ES6 (ECMAScript 2015)
- Fetch API
- Local Storage API
- Modern DOM APIs

For older browsers, consider using polyfills.
