# Implementation Plan: Template Refactoring

## Overview

This implementation plan systematically refactors Django templates to extract inline CSS and JavaScript into external files. The approach prioritizes maintaining functionality while improving code organization, following the ExamMaker system's architectural patterns.

## Tasks

- [x] 1. Set up external file structure and utilities
  - Create directory structure in `static/css/` and `static/js/`
  - Create utility classes for CSRF handling and data loading
  - Set up base CSS and JavaScript files for common functionality
  - _Requirements: 4.1, 4.2, 4.3_

- [ ]* 1.1 Write property test for file organization structure
  - **Property 5: File Organization Structure**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.5, 10.3**

- [x] 2. Extract and refactor component-level CSS
  - [x] 2.1 Extract modal styles from templates
    - Move modal CSS from `class_list.html`, `exam_list.html` to `static/css/components/modals.css`
    - Convert inline styles to CSS classes
    - _Requirements: 1.1, 1.2, 4.1_

  - [x] 2.2 Extract form styles from templates
    - Move form CSS from `student_account_management.html`, `first_time_setup.html` to `static/css/components/forms.css`
    - Convert password display and validation styles
    - _Requirements: 1.1, 1.2, 4.1_

  - [x] 2.3 Extract chart container styles
    - Move chart height styles from dashboard templates to `static/css/components/charts.css`
    - Create responsive chart container classes
    - _Requirements: 1.1, 1.2, 4.1_

- [ ]* 2.4 Write property test for CSS extraction
  - **Property 1: Inline Code Extraction**
  - **Validates: Requirements 1.1, 1.2**

- [ ]* 2.5 Write property test for visual equivalence
  - **Property 3: Visual Equivalence**
  - **Validates: Requirements 1.3, 3.1**

- [-] 3. Create reusable JavaScript components
  - [x] 3.1 Create modal manager component
    - Extract modal functionality from `class_list.html`, `exam_list.html`
    - Create `static/js/components/modal-manager.js` with reusable modal methods
    - _Requirements: 2.1, 4.2, 4.4_

  - [x] 3.2 Create form validator component
    - Extract form validation from `first_time_setup.html`, `student_account_management.html`
    - Create `static/js/components/form-validator.js` with validation utilities
    - _Requirements: 2.1, 4.2, 4.4_

  - [ ] 3.3 Create CSRF helper utility
    - Extract CSRF token handling patterns
    - Create `static/js/utils/csrf-helper.js` for CSRF management
    - _Requirements: 2.1, 5.3_

- [ ]* 3.4 Write property test for JavaScript extraction
  - **Property 2: JavaScript Extraction**
  - **Validates: Requirements 2.1**

- [ ]* 3.5 Write property test for code reusability
  - **Property 8: Code Reusability**
  - **Validates: Requirements 4.4**

- [x] 4. Refactor complex dashboard charts
  - [x] 4.1 Extract teacher dashboard chart code
    - Move 900+ lines of chart JavaScript from `teacher_dashboard.html`
    - Create `static/js/pages/dashboard-charts.js` with chart management
    - Implement proper data passing through JSON script tags
    - _Requirements: 2.1, 2.3, 5.1_

  - [x] 4.2 Extract student dashboard chart code
    - Move chart initialization from `student_dashboard.html`
    - Integrate with shared dashboard chart utilities
    - _Requirements: 2.1, 2.3, 5.1_

- [ ]* 4.3 Write property test for chart functionality
  - **Property 4: Functional Equivalence (Charts)**
  - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

- [ ]* 4.4 Write property test for template data access
  - **Property 6: Template Data Access**
  - **Validates: Requirements 2.3, 5.1, 5.2, 5.3, 5.4, 5.5**

- [x] 5. Refactor page-specific functionality
  - [x] 5.1 Refactor student profile page
    - Extract profile picture upload and password change JavaScript from `student_profile.html`
    - Create `static/js/pages/student-profile.js`
    - _Requirements: 2.1, 4.2_

  - [x] 5.2 Refactor exam form functionality
    - Extract navigation and validation from `exam_form_simple.html`
    - Create `static/js/pages/exam-form.js`
    - Remove debug code and test sections
    - _Requirements: 2.1, 8.1, 8.2, 8.4_

  - [x] 5.3 Refactor navbar and message components
    - Extract dropdown functionality from `navbar.html`
    - Extract SweetAlert2 integration from `messages.html`
    - Create shared component files
    - _Requirements: 2.1, 4.4_

- [ ]* 5.4 Write property test for functional equivalence
  - **Property 4: Functional Equivalence (Forms/UI)**
  - **Validates: Requirements 3.2, 3.3, 3.4, 7.1, 7.2, 7.3, 7.4, 7.5**

- [-] 6. Update templates to use external files
  - [x] 6.1 Update template references to CSS files
    - Replace inline styles with `{% static %}` references
    - Add proper CSS file loading in template blocks
    - _Requirements: 1.5, 9.1_

  - [x] 6.2 Update template references to JavaScript files
    - Replace inline scripts with `{% static %}` references
    - Add proper JavaScript file loading in template blocks
    - _Requirements: 2.5, 9.1_

  - [x] 6.3 Implement JSON data passing
    - Add JSON script tags for template variables
    - Update JavaScript to read data from JSON tags
    - _Requirements: 5.1, 5.2_

- [ ]* 6.4 Write property test for static file loading
  - **Property 7: Static File Loading**
  - **Validates: Requirements 1.5, 2.5, 9.1**

- [x] 7. Clean up debug and test code
  - [x] 7.1 Remove debug styles and test sections
    - Remove bright-colored debug styles from `exam_form_simple.html`
    - Remove test sections with placeholder content
    - _Requirements: 8.1, 8.2_

  - [x] 7.2 Remove debug JavaScript code
    - Remove `console.log` statements from production code
    - Remove `alert()` calls used for debugging
    - _Requirements: 8.3, 8.4_

- [ ]* 7.3 Write property test for debug code removal
  - **Property 9: Debug Code Removal**
  - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

- [x] 8. Optimize for performance and standards
  - [x] 8.1 Optimize file organization
    - Ensure reasonable number of files (not too many small files)
    - Group related functionality appropriately
    - _Requirements: 9.5_

  - [x] 8.2 Apply coding standards
    - Format JavaScript according to project conventions
    - Format CSS according to project patterns
    - Add appropriate comments and documentation
    - _Requirements: 10.1, 10.2, 10.4_

- [ ]* 8.3 Write property test for performance optimization
  - **Property 10: Performance Optimization**
  - **Validates: Requirements 9.2, 9.3, 9.5**

- [ ]* 8.4 Write property test for coding standards compliance
  - **Property 11: Coding Standards Compliance**
  - **Validates: Requirements 10.1, 10.2, 10.4, 10.5**

- [x] 9. Test build process compatibility
  - [x] 9.1 Verify static file collection
    - Test that `python manage.py collectstatic` works correctly
    - Verify all external files are collected properly
    - _Requirements: 9.4_

  - [ ] 9.2 Test minification compatibility
    - Verify external files work with existing build process
    - Test that minified files maintain functionality
    - _Requirements: 9.4_

- [ ]* 9.3 Write property test for build process compatibility
  - **Property 12: Build Process Compatibility**
  - **Validates: Requirements 9.4**

- [x] 10. Checkpoint - Comprehensive testing and validation
  - Run all property-based tests to verify correctness properties
  - Perform visual regression testing on key pages
  - Test all interactive functionality (forms, modals, charts)
  - Verify performance improvements and caching behavior
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based tests that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout the refactoring process
- Property tests validate universal correctness properties across all templates
- The refactoring maintains strict functional equivalence while improving code organization