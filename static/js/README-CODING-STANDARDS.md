# JavaScript Coding Standards

This document outlines the coding standards applied to the ExamMaker JavaScript codebase.

## File Organization

### Directory Structure
```
static/js/
├── components/          # Reusable UI components
├── pages/              # Page-specific functionality
├── utils/              # Utility functions and helpers
├── main.js             # Core application JavaScript
└── utils.js            # Legacy utilities (being phased out)
```

### Component Guidelines
- **Components**: Reusable functionality that can be used across multiple pages
- **Pages**: Specific to individual pages or views
- **Utils**: Helper functions and utilities

## Code Style Guidelines

### 1. File Headers
All JavaScript files must include a proper header:

```javascript
/**
 * [Component/Page/Utility Name]
 * [Brief description of functionality]
 * 
 * @author ExamMaker Development Team
 * @version 1.0.0
 * @since 2024
 * 
 * Requirements: [Requirement numbers] - [Brief description]
 */
```

### 2. JSDoc Comments
All functions must include JSDoc comments:

```javascript
/**
 * Brief description of the function
 * @param {type} paramName - Description of parameter
 * @param {type} [optionalParam] - Description of optional parameter
 * @returns {type} Description of return value
 * @throws {Error} Description of when errors are thrown
 */
function exampleFunction(paramName, optionalParam) {
    // Implementation
}
```

### 3. Class Documentation
Classes must include comprehensive documentation:

```javascript
/**
 * Class description
 * @class
 */
class ExampleClass {
    /**
     * Constructor description
     * @param {Object} options - Configuration options
     */
    constructor(options = {}) {
        // Implementation
    }
    
    /**
     * Method description
     * @param {string} param - Parameter description
     * @returns {boolean} Return value description
     */
    exampleMethod(param) {
        // Implementation
    }
}
```

### 4. Error Handling
- Use proper error handling with try-catch blocks
- Provide meaningful error messages
- Log errors appropriately (not using console.log in production)

```javascript
try {
    // Risky operation
} catch (error) {
    // Handle error appropriately
    this.handleError('Operation failed', error);
}
```

### 5. Variable Naming
- Use camelCase for variables and functions
- Use PascalCase for classes and constructors
- Use UPPER_CASE for constants
- Use descriptive names

```javascript
const MAX_RETRY_ATTEMPTS = 3;
const userName = 'john_doe';
const isValidEmail = true;

class UserManager {
    constructor() {
        this.activeUsers = new Map();
    }
}
```

### 6. Function Guidelines
- Keep functions small and focused
- Use pure functions when possible
- Avoid side effects when not necessary
- Return early to reduce nesting

```javascript
function validateEmail(email) {
    if (!email) {
        return false;
    }
    
    if (typeof email !== 'string') {
        return false;
    }
    
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
```

## Production Code Standards

### 1. No Debug Code
- Remove all `console.log()` statements from production code
- Remove all `alert()` calls used for debugging
- Remove test code and debug sections

### 2. Performance Considerations
- Minimize DOM queries by caching elements
- Use event delegation for dynamic content
- Avoid memory leaks by properly removing event listeners

### 3. Browser Compatibility
- Use modern JavaScript features (ES6+)
- Provide fallbacks for older browsers when necessary
- Test across different browsers

### 4. Security
- Sanitize user input
- Use proper CSRF token handling
- Validate data on both client and server side

## Code Review Checklist

Before committing JavaScript code, ensure:

- [ ] File has proper header with author and version info
- [ ] All functions have JSDoc comments
- [ ] No console.log or debug statements remain
- [ ] Error handling is implemented
- [ ] Variable names are descriptive
- [ ] Code follows ExamMaker conventions
- [ ] File is in the correct directory (components/pages/utils)
- [ ] Dependencies are properly managed
- [ ] Code is tested and functional

## Examples

### Good Example
```javascript
/**
 * Modal Manager Component
 * Provides reusable modal functionality for the ExamMaker system
 * 
 * @author ExamMaker Development Team
 * @version 1.0.0
 * @since 2024
 */

class ModalManager {
    /**
     * Open a modal with specified configuration
     * @param {string} modalId - The ID of the modal element
     * @param {Object} config - Modal configuration options
     * @param {string} [config.title] - Modal title
     * @param {string} [config.content] - Modal content
     * @returns {boolean} True if modal was opened successfully
     */
    static openModal(modalId, config = {}) {
        const modal = document.getElementById(modalId);
        
        if (!modal) {
            this.handleError(`Modal with ID '${modalId}' not found`);
            return false;
        }
        
        // Apply configuration
        this.applyConfiguration(modal, config);
        
        // Show modal
        modal.classList.remove('hidden');
        
        return true;
    }
    
    /**
     * Handle errors appropriately
     * @private
     * @param {string} message - Error message
     */
    static handleError(message) {
        // Log error for debugging (not console.log in production)
        // Show user-friendly message if needed
    }
}
```

### Bad Example
```javascript
// Bad: No header, no documentation, debug code
function openModal(id, config) {
    console.log('Opening modal:', id); // Debug code - remove!
    var modal = document.getElementById(id); // Use const/let
    if (!modal) {
        alert('Modal not found!'); // Debug code - remove!
        return;
    }
    modal.style.display = 'block'; // Inconsistent with CSS classes
}
```

## Migration Notes

When refactoring existing code:

1. Add proper file headers
2. Add JSDoc comments to all functions
3. Remove debug code (console.log, alert)
4. Move files to appropriate directories
5. Update variable declarations (var → const/let)
6. Improve error handling
7. Add proper documentation

This ensures all JavaScript code follows ExamMaker coding standards and requirements 10.1, 10.2, and 10.4.