# CSS Coding Standards

This document outlines the CSS coding standards applied to the ExamMaker stylesheet organization.

## File Organization

### Directory Structure
```
static/css/
├── components/          # Component-specific styles
│   ├── modals.css      # Modal dialog styles
│   ├── forms.css       # Form element styles
│   ├── charts.css      # Chart container styles
│   └── base.css        # Base component styles
├── pages/              # Page-specific styles
│   └── exam-list.css   # Exam list page styles
├── utilities/          # Utility classes (currently empty)
├── main.css            # Core application styles
└── profile.css         # Profile and dashboard styles
```

### Component Guidelines
- **Components**: Reusable styles that can be used across multiple pages
- **Pages**: Styles specific to individual pages or views
- **Utilities**: Helper classes and utility styles

## Code Style Guidelines

### 1. File Headers
All CSS files must include a proper header:

```css
/**
 * [Component/Page Name] CSS
 * [Brief description of styles contained]
 * 
 * @author ExamMaker Development Team
 * @version 1.0.0
 * @since 2024
 * 
 * Requirements: [Requirement numbers] - [Brief description]
 */
```

### 2. CSS Organization
Organize CSS rules in logical sections with clear comments:

```css
/* ==========================================================================
   Component Name
   ========================================================================== */

/* Base Styles */
.component-base {
    /* Base properties */
}

/* Variants */
.component-variant {
    /* Variant-specific properties */
}

/* States */
.component-base:hover,
.component-base:focus {
    /* Interactive states */
}

/* Responsive */
@media (max-width: 768px) {
    .component-base {
        /* Mobile styles */
    }
}
```

### 3. Naming Conventions
- Use kebab-case for class names
- Use descriptive, semantic names
- Follow BEM methodology when appropriate
- Prefix component classes consistently

```css
/* Good Examples */
.modal-overlay { }
.modal-container { }
.modal-container-wide { }
.form-error-message { }
.chart-container-sm { }

/* Bad Examples */
.modal1 { }
.redButton { }
.container_wide { }
```

### 4. Property Organization
Order CSS properties logically:

```css
.example-class {
    /* Positioning */
    position: relative;
    top: 0;
    left: 0;
    z-index: 10;
    
    /* Box Model */
    display: flex;
    width: 100%;
    height: auto;
    margin: 1rem;
    padding: 0.5rem;
    border: 1px solid #ccc;
    
    /* Typography */
    font-family: inherit;
    font-size: 1rem;
    line-height: 1.5;
    color: #333;
    
    /* Visual */
    background-color: #fff;
    border-radius: 0.375rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    
    /* Animation */
    transition: all 0.2s ease;
}
```

### 5. Color and Spacing Standards
Use consistent color palette and spacing:

```css
/* Color Palette */
:root {
    --primary-blue: #3b82f6;
    --primary-blue-dark: #2563eb;
    --success-green: #16a34a;
    --danger-red: #dc2626;
    --warning-amber: #f59e0b;
    --gray-100: #f3f4f6;
    --gray-300: #d1d5db;
    --gray-600: #4b5563;
    --gray-900: #111827;
}

/* Spacing Scale */
.spacing-xs { margin: 0.25rem; }    /* 4px */
.spacing-sm { margin: 0.5rem; }     /* 8px */
.spacing-md { margin: 1rem; }       /* 16px */
.spacing-lg { margin: 1.5rem; }     /* 24px */
.spacing-xl { margin: 2rem; }       /* 32px */
```

### 6. Responsive Design
Use mobile-first approach:

```css
/* Mobile First (default) */
.component {
    width: 100%;
    padding: 1rem;
}

/* Tablet and up */
@media (min-width: 768px) {
    .component {
        width: 50%;
        padding: 1.5rem;
    }
}

/* Desktop and up */
@media (min-width: 1024px) {
    .component {
        width: 33.333%;
        padding: 2rem;
    }
}
```

## Component-Specific Standards

### 1. Modal Components
```css
/* Modal Base */
.modal-overlay {
    position: fixed;
    inset: 0;
    background-color: rgba(75, 85, 99, 0.5);
    z-index: 50;
}

.modal-container {
    position: relative;
    margin: 0 auto;
    padding: 1.25rem;
    background-color: white;
    border-radius: 0.375rem;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}
```

### 2. Form Components
```css
/* Form Base Styles */
.form-input {
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    font-size: 0.875rem;
}

.form-input:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-error {
    border-color: #dc2626;
}
```

### 3. Button Components
```css
/* Button Base */
.btn {
    display: inline-flex;
    align-items: center;
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
}

/* Button Variants */
.btn-primary {
    background-color: #3b82f6;
    color: white;
}

.btn-primary:hover {
    background-color: #2563eb;
}
```

## Performance Guidelines

### 1. Efficient Selectors
- Avoid overly specific selectors
- Use classes instead of IDs for styling
- Minimize nesting depth

```css
/* Good */
.modal-title { }
.form-error-message { }

/* Avoid */
#modal div.container h2.title { }
```

### 2. Minimize Reflows
- Use `transform` and `opacity` for animations
- Avoid changing layout properties in animations

```css
/* Good - GPU accelerated */
.fade-in {
    opacity: 0;
    transform: translateY(10px);
    transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-in.active {
    opacity: 1;
    transform: translateY(0);
}

/* Avoid - causes reflows */
.slide-down {
    height: 0;
    transition: height 0.3s ease;
}
```

### 3. File Size Optimization
- Remove unused styles
- Combine related styles
- Use shorthand properties when appropriate

## Browser Compatibility

### Supported Features
- CSS Grid and Flexbox
- CSS Custom Properties (variables)
- Modern pseudo-selectors
- CSS transforms and transitions

### Fallbacks
Provide fallbacks for older browsers when necessary:

```css
/* Fallback for older browsers */
.grid-container {
    display: block; /* Fallback */
    display: grid;  /* Modern browsers */
}
```

## Code Review Checklist

Before committing CSS code, ensure:

- [ ] File has proper header with author and version info
- [ ] Styles are organized logically with clear comments
- [ ] Class names follow naming conventions
- [ ] Properties are ordered consistently
- [ ] Responsive design is implemented
- [ ] Colors use consistent palette
- [ ] No unused or duplicate styles
- [ ] File is in the correct directory
- [ ] Performance considerations are addressed

## Migration Notes

When refactoring existing CSS:

1. Add proper file headers
2. Organize styles into logical sections
3. Update class names to follow conventions
4. Remove unused styles
5. Add responsive design where needed
6. Use consistent color palette
7. Optimize for performance
8. Move files to appropriate directories

This ensures all CSS code follows ExamMaker coding standards and requirements 10.1, 10.2, and 10.4.