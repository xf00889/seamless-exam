# Template Refactoring - External File Structure

This document describes the new organized structure for CSS and JavaScript files created as part of the template refactoring initiative.

## Directory Structure

```
static/
├── css/
│   ├── components/          # Reusable component styles
│   │   └── base.css        # Base component styles (modals, forms, buttons)
│   ├── pages/              # Page-specific styles
│   └── utilities/          # Utility and helper styles
├── js/
│   ├── components/         # Reusable JavaScript components
│   │   └── base.js        # Base component classes and utilities
│   ├── pages/             # Page-specific JavaScript
│   └── utils/             # Utility and helper JavaScript
│       ├── csrf-helper.js  # CSRF token management
│       ├── data-loader.js  # Template data loading utilities
│       └── ajax-helper.js  # AJAX request utilities
```

## Utility Classes

### CSRFHelper (`static/js/utils/csrf-helper.js`)

Handles Django CSRF tokens for AJAX requests:

```javascript
// Get CSRF token
const token = CSRFHelper.getToken();

// Setup automatic CSRF headers for all AJAX requests
CSRFHelper.setupAjaxHeaders();

// Add CSRF token to a form
CSRFHelper.addTokenToForm(formElement);

// Make CSRF-protected request
const response = await CSRFHelper.request('/api/endpoint/', {
    method: 'POST',
    body: JSON.stringify(data)
});
```

### DataLoader (`static/js/utils/data-loader.js`)

Loads data from Django templates into JavaScript:

```javascript
// Load JSON data from script tag
const chartData = DataLoader.loadJSON('chart-data');

// Load with fallback
const config = DataLoader.loadWithFallback('app-config', {});

// Load form configuration
const formConfig = DataLoader.loadFormConfig();

// Get data attribute from element
const value = DataLoader.getDataAttribute(element, 'config', {});
```

### AjaxHelper (`static/js/utils/ajax-helper.js`)

Convenient AJAX request methods with error handling:

```javascript
// GET request
const response = await AjaxHelper.get('/api/data/');

// POST request with JSON data
const result = await AjaxHelper.post('/api/save/', { name: 'value' });

// Submit form via AJAX
const response = await AjaxHelper.submitForm(formElement);

// Load content into element
await AjaxHelper.loadContent('/api/content/', targetElement);
```

### BaseComponent (`static/js/components/base.js`)

Base class for creating reusable UI components:

```javascript
class MyComponent extends BaseComponent {
    static defaultOptions = {
        autoInit: true,
        debug: false
    };
    
    bindEvents() {
        this.on('click', this.handleClick.bind(this));
    }
    
    handleClick(event) {
        // Handle click event
        this.trigger('component:clicked', { event });
    }
}

// Initialize component
const component = new MyComponent(element, options);
```

## Usage in Templates

### Loading CSS Files

```html
{% load static %}

{% block extra_css %}
    <link rel="stylesheet" href="{% static 'css/components/base.css' %}">
    <link rel="stylesheet" href="{% static 'css/components/modals.css' %}">
{% endblock %}
```

### Loading JavaScript Files

```html
{% load static %}

{% block extra_js %}
    <script src="{% static 'js/utils/csrf-helper.js' %}"></script>
    <script src="{% static 'js/utils/data-loader.js' %}"></script>
    <script src="{% static 'js/components/base.js' %}"></script>
{% endblock %}
```

### Passing Data to JavaScript

```html
<!-- Template data passing -->
{{ chart_data|json_script:"chart-data" }}
{{ form_config|json_script:"form-config" }}

<script>
    // Load data in JavaScript
    const chartData = DataLoader.loadJSON('chart-data');
    const formConfig = DataLoader.loadJSON('form-config');
</script>
```

## Component Registry

Use the ComponentRegistry to manage component instances:

```javascript
// Initialize components from DOM
ComponentRegistry.initFromDOM('.modal', ModalComponent);

// Get component instances
const modals = ComponentRegistry.get('ModalComponent');

// Destroy all components of a type
ComponentRegistry.destroyAll('ModalComponent');
```

## Event Bus

Use the EventBus for component communication:

```javascript
// Subscribe to events
EventBus.on('modal:opened', (data) => {
    console.log('Modal opened:', data);
});

// Emit events
EventBus.emit('modal:opened', { modalId: 'confirm-delete' });
```

## DOM Utilities

Common DOM manipulation utilities:

```javascript
// Wait for DOM ready
DOMUtils.ready(() => {
    // Initialize components
});

// Create elements
const button = DOMUtils.createElement('button', {
    className: 'btn btn-primary',
    dataset: { action: 'save' }
}, 'Save');

// Show/hide elements
DOMUtils.show(element);
DOMUtils.hide(element);
DOMUtils.toggle(element);
```

## Best Practices

1. **File Organization**: Place files in appropriate directories based on their purpose
2. **Naming Conventions**: Use descriptive names following project conventions
3. **Dependencies**: Load utility files before component files
4. **Error Handling**: Use try-catch blocks and proper error logging
5. **Performance**: Minimize file sizes and avoid excessive HTTP requests
6. **Compatibility**: Ensure compatibility with existing ExamMaker patterns

## Migration Notes

When refactoring templates:

1. Extract inline CSS to appropriate component/page files
2. Extract inline JavaScript to external files
3. Use DataLoader for template variable access
4. Use CSRFHelper for AJAX requests
5. Update template references to use `{% static %}` tags
6. Test functionality thoroughly after refactoring

This structure provides a solid foundation for maintaining clean, organized, and reusable code while preserving all existing functionality.