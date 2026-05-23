# Requirements Document

## Introduction

The exam creation form in the ExamMaker system uses a multi-step wizard interface to guide teachers through creating new exams. Users have reported that the "Next" button is not displaying properly, preventing them from proceeding through the form steps. This critical issue blocks the primary exam creation workflow and must be resolved to ensure teachers can create exams successfully.

## Glossary

- **ExamMaker System**: The Django-based exam management application
- **Multi-step Form**: A form divided into sequential steps with navigation controls
- **Next Button**: The navigation button that advances users to the subsequent form step
- **Form Wizard**: The complete multi-step exam creation interface
- **Navigation Controls**: The Previous, Next, and Submit buttons that control form progression

## Requirements

### Requirement 1

**User Story:** As a teacher, I want to see and use the Next button in the exam creation form, so that I can proceed through the multi-step wizard to create an exam.

#### Acceptance Criteria

1. WHEN a teacher loads the exam creation form THEN the system SHALL display a visible and clickable Next button
2. WHEN a teacher clicks the Next button THEN the system SHALL advance to the next form step if validation passes
3. WHEN a teacher is on the first step THEN the system SHALL show only the Next button and hide the Previous button
4. WHEN a teacher is on intermediate steps THEN the system SHALL show both Previous and Next buttons
5. WHEN a teacher is on the final step THEN the system SHALL show the Previous button and Submit button while hiding the Next button

### Requirement 2

**User Story:** As a teacher, I want the form navigation to work consistently across all browsers, so that I can create exams regardless of my browser choice.

#### Acceptance Criteria

1. WHEN a teacher uses Chrome, Firefox, Safari, or Edge THEN the system SHALL display navigation buttons consistently
2. WHEN JavaScript is enabled THEN the system SHALL provide interactive step navigation
3. WHEN the form loads THEN the system SHALL initialize the first step with proper button visibility
4. WHEN validation fails on a step THEN the system SHALL prevent navigation and display error messages
5. WHEN the form state changes THEN the system SHALL update button visibility appropriately

### Requirement 3

**User Story:** As a teacher, I want clear visual feedback about form progression, so that I understand which step I'm on and can navigate effectively.

#### Acceptance Criteria

1. WHEN a teacher is on any form step THEN the system SHALL highlight the current step in the progress indicator
2. WHEN a teacher completes a step THEN the system SHALL mark it as completed in the progress bar
3. WHEN navigation buttons are disabled THEN the system SHALL provide visual indication of the disabled state
4. WHEN form validation occurs THEN the system SHALL display clear error messages for invalid fields
5. WHEN the form is processing THEN the system SHALL show appropriate loading states