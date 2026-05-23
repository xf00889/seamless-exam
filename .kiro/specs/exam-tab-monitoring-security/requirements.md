# Requirements Document

## Introduction

This document specifies requirements for an exam security system that monitors student tab activity during exams. The system detects when students switch tabs or open new tabs, issues progressive warnings, automatically submits exams after repeated violations, flags suspicious behavior, and provides teachers with detailed activity reports.

## Glossary

- **Exam System**: The web-based examination platform where students take exams
- **Tab Switch Event**: When a student navigates away from the exam page to another browser tab or window
- **Warning System**: The progressive notification mechanism that alerts students about tab switching violations
- **Auto-Submission**: The automatic submission of an exam when violation thresholds are exceeded
- **Activity Log**: A record of all tab switch events and warnings for a specific exam attempt
- **Flagged Attempt**: An exam attempt marked as potentially involving cheating behavior
- **Teacher Dashboard**: The interface where teachers view student exam attempts and activity

## Requirements

### Requirement 1

**User Story:** As a student taking an exam, I want to receive clear warnings when I switch tabs, so that I understand the consequences before my exam is auto-submitted.

#### Acceptance Criteria

1. WHEN a student switches away from the exam tab for the first time THEN the system SHALL display a warning message indicating this is warning 1 of 3
2. WHEN a student switches away from the exam tab for the second time THEN the system SHALL display a warning message indicating this is warning 2 of 3
3. WHEN a student switches away from the exam tab for the third time THEN the system SHALL display a final warning message indicating this is the last warning
4. WHEN a student switches away from the exam tab for the fourth time THEN the system SHALL automatically submit the exam and flag the attempt as potential cheating
5. WHEN a warning is displayed THEN the system SHALL include the current warning count and total allowed warnings

### Requirement 2

**User Story:** As a student, I want the system to accurately detect when I leave the exam page, so that I am only warned for actual violations.

#### Acceptance Criteria

1. WHEN a student's browser tab loses focus THEN the system SHALL record a tab switch event with timestamp
2. WHEN a student opens a new browser tab or window THEN the system SHALL detect this as a tab switch event
3. WHEN a student switches to another application THEN the system SHALL detect this as a tab switch event
4. WHEN a student returns to the exam tab THEN the system SHALL record the return event with timestamp
5. WHEN the exam page is the active tab THEN the system SHALL not record any violations

### Requirement 3

**User Story:** As the exam system, I want to persist tab switch violations to the database, so that the data survives page refreshes and is available for teacher review.

#### Acceptance Criteria

1. WHEN a tab switch event occurs THEN the system SHALL store the event timestamp in the database
2. WHEN a warning is issued THEN the system SHALL store the warning number and timestamp in the database
3. WHEN an exam is auto-submitted due to violations THEN the system SHALL store the auto-submission reason in the database
4. WHEN a student refreshes the exam page THEN the system SHALL retrieve and display the current warning count
5. WHEN storing violation data THEN the system SHALL associate it with the specific exam attempt

### Requirement 4

**User Story:** As a teacher, I want to view which students have been flagged for potential cheating, so that I can review their exam attempts carefully.

#### Acceptance Criteria

1. WHEN viewing the grading list THEN the system SHALL display a visual indicator for flagged attempts
2. WHEN viewing student exam history THEN the system SHALL display a visual indicator for flagged attempts
3. WHEN viewing class exam results THEN the system SHALL display a visual indicator for flagged attempts
4. WHEN a flagged attempt is displayed THEN the system SHALL show the reason for flagging
5. WHEN multiple attempts exist for a student THEN the system SHALL clearly distinguish flagged from non-flagged attempts

### Requirement 5

**User Story:** As a teacher, I want to view detailed activity logs for each student's exam attempt, so that I can understand what happened during the exam.

#### Acceptance Criteria

1. WHEN a teacher clicks a "View Activity" button for an attempt THEN the system SHALL display a detailed activity log
2. WHEN displaying the activity log THEN the system SHALL show all tab switch events with timestamps
3. WHEN displaying the activity log THEN the system SHALL show all warnings issued with timestamps
4. WHEN displaying the activity log THEN the system SHALL show whether the exam was auto-submitted
5. WHEN displaying the activity log THEN the system SHALL show the total duration the student was away from the exam tab

### Requirement 6

**User Story:** As a teacher, I want to access student activity reports from multiple locations, so that I can review behavior whenever I'm viewing student data.

#### Acceptance Criteria

1. WHEN viewing the grading list THEN the system SHALL provide a "View Activity" action button for each attempt
2. WHEN viewing individual student exam history THEN the system SHALL provide a "View Activity" action button for each attempt
3. WHEN viewing class exam results THEN the system SHALL provide a "View Activity" action button for each attempt
4. WHEN viewing an individual attempt detail page THEN the system SHALL display the activity log inline
5. WHEN clicking "View Activity" THEN the system SHALL display the activity log in a modal or dedicated page

### Requirement 7

**User Story:** As a student, I want to see my remaining warnings during the exam, so that I know how many violations I have left.

#### Acceptance Criteria

1. WHEN a student is taking an exam THEN the system SHALL display the current warning count on the exam page
2. WHEN a student has no warnings THEN the system SHALL display "No warnings" or "0/3 warnings"
3. WHEN a student has warnings THEN the system SHALL display the count in a prominent location
4. WHEN a student receives a new warning THEN the system SHALL update the displayed count immediately
5. WHEN the warning count reaches 3 THEN the system SHALL display a critical warning indicator

### Requirement 8

**User Story:** As the exam system, I want to handle edge cases gracefully, so that legitimate student actions don't trigger false violations.

#### Acceptance Criteria

1. WHEN a student's browser crashes and they reload the page THEN the system SHALL preserve their warning count
2. WHEN a student accidentally triggers a browser dialog THEN the system SHALL not count this as a violation
3. WHEN a student's exam time expires naturally THEN the system SHALL not flag the attempt as cheating
4. WHEN a student submits the exam normally THEN the system SHALL not flag the attempt as cheating
5. WHEN network connectivity is lost temporarily THEN the system SHALL queue violation events and sync when reconnected
