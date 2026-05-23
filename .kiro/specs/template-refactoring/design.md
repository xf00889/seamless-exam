# Design Document

## Overview

This design outlines the systematic refactoring of Django templates in the ExamMaker system to extract inline CSS and JavaScript into external files. The refactoring will improve code maintainability, enable better caching, and follow Django best practices for static file organization.

The refactoring affects 15+ templates containing significant inline styles and scripts, including complex dashboard charts, form validation, modal dialogs, and UI interactions. All functionality and visual appearance will be preserved while improving code organization.

## Architecture

### Static File Organization

The refactored code will follow Django's static file conventions with logical organization:

```
static/
├── css/
│   ├── components/
│   │   ├── modals.css           # Shared modal styles
│   │   ├── forms.css            # Form-specific styles
│   │   ├── charts.css           # Chart container styles
│   │   └── messages.css         # Message display styles
│   ├── pages/
│   │   ├── dashboard.css        # Dashboard-specific styles
│   │   ├── profile.css          # Profile page styles
│   │   └── exam-form.css        # Exam form styles
│   └── utilities/
│       └── debug.css            # Debug styles (removed in production)
├── js/
│   ├── components/
│   │   ├── modal-manager.js     # Reusable modal functionality
│   │   ├── form-validator.js    # Enhanced form validation
│   │   ├── password-toggle.js   # Password visibility toggle
│   │   └── file-upload.js       # File upload handling
│   ├── pages/
│   │   ├── dashboard-charts.js  # Chart initialization and management
│   │   ├── student-profile.js   # Profile page interactions
│   │   └── exam-form.js         # Exam form navigation
│   └── utils/
│       ├── csrf-helper.js       # CSRF token management
│       ├── data-loader.js       # Template data loading utilities
│       └── ajax-helper.js       # AJAX request utilities
```

### Template Block Strategy

Templates will use Django's block system for including external files:

```html
<!-- Base template structure -->
{% block extra_css %}
  <link rel="stylesheet" href="{% static 'css/components/modals.css' %}">
{% endblock %}

{% block extra_js %}
  <script src="{% static 'js/components/modal-manager.js' %}"></script>
{% endblock %}
```

### Data Passing Mechanism

JavaScript will access Django template data through JSON script tags:

```html
<!-- Template data passing -->
{{ chart_data|json_script:"chart-data" }}
{{ form_config|json_script:"form-config" }}

<script>
  const chartData = JSON.parse(document.getElementById('chart-data').textContent);
  const formConfig = JSON.parse(document.getElementById('form-config').textContent);
</script>
```

## Components and Interfaces

### CSS Component Structure

#### Modal Component (`static/css/components/modals.css`)
- Delete confirmation modal styles
- Reopen exam modal styles
- Password confirmation modal styles
- Responsive modal behavior

#### Form Component (`static/css/components/forms.css`)
- Password display styles
- File upload styling
- Form validation states
- Input field enhancements

#### Chart Component (`static/css/components/charts.css`)
- Chart container dimensions
- Responsive chart behavior
- Chart loading states

### JavaScript Component Structure

#### Modal Manager (`static/js/components/modal-manager.js`)
```javascript
class ModalManager {
  static openModal(modalId, config = {}) { /* ... */ }
  static closeModal(modalId) { /* ... */ }
  static confirmAction(config) { /* ... */ }
}
```

#### Form Validator (`static/js/components/form-validator.js`)
```javascript
class FormValidator {
  static validatePassword(password, confirmPassword) { /* ... */ }
  static validateRequired(fields) { /* ... */ }
  static showError(field, message) { /* ... */ }
}
```

#### Chart Manager (`static/js/pages/dashboard-charts.js`)
```javascript
class DashboardCharts {
  static init(config) { /* ... */ }
  static createExamPerformanceChart(data) { /* ... */ }
  static createDistributionChart(data) { /* ... */ }
  static handleResize() { /* ... */ }
}
```

#### CSRF Helper (`static/js/utils/csrf-helper.js`)
```javascript
class CSRFHelper {
  static getToken() { /* ... */ }
  static setupAjaxHeaders() { /* ... */ }
  static addTokenToForm(form) { /* ... */ }
}
```

## Data Models

### Template Data Structure

Templates will pass structured data to JavaScript:

```javascript
// Chart data structure
{
  examPerformance: {
    labels: ["Exam 1", "Exam 2"],
    passers: [15, 20],
    failers: [5, 3]
  },
  passingRateData: {
    subjects: ["Math", "Science"],
    sections: ["A", "B"],
    data: { "Math": [85, 90], "Science": [78, 82] }
  }
}

// Form configuration structure
{
  validation: {
    passwordMinLength: 8,
    requiredFields: ["first_name", "last_name"],
    patterns: {
      email: "^[\\w\\.-]+@[\\w\\.-]+\\.[a-zA-Z]{2,}$"
    }
  },
  urls: {
    submit: "/api/form/submit/",
    validate: "/api/form/validate/"
  }
}

// Modal configuration structure
{
  title: "Delete Confirmation",
  message: "Are you sure you want to delete this item?",
  confirmText: "Delete",
  cancelText: "Cancel",
  confirmClass: "btn-danger",
  onConfirm: "handleDelete",
  requirePassword: true
}
```

## Correctness Properties

Now I'll analyze the acceptance criteria for testability using the prework tool:

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, several properties can be consolidated to eliminate redundancy:

- Properties about file organization (4.1, 4.2, 4.3, 4.5, 10.3) can be combined into comprehensive file organization properties
- Properties about functionality preservation (3.1, 3.2, 6.1, 6.2, 7.1, 7.2) can be grouped into functional equivalence properties
- Properties about debug code removal (8.1, 8.2, 8.3, 8.4, 8.5) can be combined into a single debug cleanup property
- Properties about static file handling (1.5, 2.5, 9.1) can be consolidated into proper Django static file usage

### Core Properties

**Property 1: Inline Code Extraction**
*For any* template containing inline `<style>` tags or `style=` attributes, after refactoring the template should contain no inline CSS and equivalent styles should exist in external CSS files
**Validates: Requirements 1.1, 1.2**

**Property 2: JavaScript Extraction**
*For any* template containing inline `<script>` tags with JavaScript code, after refactoring the template should contain no inline JavaScript and equivalent functionality should exist in external JS files
**Validates: Requirements 2.1**

**Property 3: Visual Equivalence**
*For any* template before and after refactoring, the computed CSS styles for all elements should be identical when rendered in the browser
**Validates: Requirements 1.3, 3.1**

**Property 4: Functional Equivalence**
*For any* interactive element (forms, modals, charts, dropdowns) before and after refactoring, the behavior and functionality should be identical when tested
**Validates: Requirements 2.2, 3.2, 3.3, 3.4, 3.5, 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5**

**Property 5: File Organization Structure**
*For any* extracted CSS or JavaScript file, it should be placed in the correct directory (`static/css/` or `static/js/`) with a descriptive name following project conventions
**Validates: Requirements 4.1, 4.2, 4.3, 4.5, 10.3**

**Property 6: Template Data Access**
*For any* JavaScript code that needs template variables, it should access them through JSON script tags or other proper Django mechanisms, not through inline code
**Validates: Requirements 2.3, 5.1, 5.2, 5.3, 5.4, 5.5**

**Property 7: Static File Loading**
*For any* template referencing external CSS or JavaScript files, it should use Django's `{% static %}` template tag with proper versioning
**Validates: Requirements 1.5, 2.5, 9.1**

**Property 8: Code Reusability**
*For any* functionality that appears in multiple templates, it should be extracted to shared external files rather than duplicated
**Validates: Requirements 4.4**

**Property 9: Debug Code Removal**
*For any* refactored template or external file, it should contain no debug code including bright-colored styles, test sections, console.log statements, or alert() calls
**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

**Property 10: Performance Optimization**
*For any* external CSS or JavaScript file, it should be structured to support browser caching and not create excessive numbers of small files
**Validates: Requirements 9.2, 9.3, 9.5**

**Property 11: Coding Standards Compliance**
*For any* extracted CSS or JavaScript code, it should follow the project's coding conventions, documentation standards, and organizational patterns
**Validates: Requirements 10.1, 10.2, 10.4, 10.5**

**Property 12: Build Process Compatibility**
*For any* external CSS or JavaScript file, it should work correctly with the existing Django static file collection and minification processes
**Validates: Requirements 9.4**

## Error Handling

### Template Loading Errors
- **Missing Static Files**: If external CSS/JS files are missing, templates should gracefully degrade
- **Invalid JSON Data**: JavaScript should handle malformed JSON data from template variables
- **CSRF Token Issues**: JavaScript should handle missing or invalid CSRF tokens appropriately

### JavaScript Runtime Errors
- **Chart Initialization**: Charts should handle missing or invalid data gracefully
- **Modal Operations**: Modals should handle DOM manipulation errors
- **Form Validation**: Form validators should handle edge cases and invalid input

### CSS Loading Issues
- **Missing Stylesheets**: Pages should remain functional with basic styling if CSS fails to load
- **Responsive Breakpoints**: Styles should work across all device sizes and orientations

## Testing Strategy

### Dual Testing Approach
The refactoring will use both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests** will verify:
- Specific examples of template rendering
- Individual JavaScript function behavior
- CSS class application and styling
- Form submission and validation flows
- Modal opening and closing operations

**Property-Based Tests** will verify:
- Universal properties across all templates
- Functional equivalence before and after refactoring
- File organization patterns
- Static file loading mechanisms
- Code extraction completeness

### Property-Based Testing Configuration
- **Testing Framework**: Django's TestCase with Hypothesis for property-based testing
- **Minimum Iterations**: 100 iterations per property test
- **Test Tags**: Each property test will be tagged with format: **Feature: template-refactoring, Property {number}: {property_text}**

### Visual Regression Testing
- **Screenshot Comparison**: Before/after screenshots of key pages
- **Computed Style Verification**: Comparison of computed CSS styles
- **Interactive Element Testing**: Verification of all interactive behaviors

### Integration Testing
- **End-to-End Workflows**: Complete user workflows through refactored templates
- **Cross-Browser Testing**: Verification across different browsers
- **Performance Testing**: Load time and caching behavior verification

The testing strategy ensures that all refactored code maintains identical functionality while improving maintainability and performance.