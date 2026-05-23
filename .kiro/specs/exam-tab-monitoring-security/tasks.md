# Implementation Plan: Exam Tab Monitoring Security

- [x] 1. Create database models and migrations




  - Create TabViolation model with fields: attempt, violated_at, returned_at, duration_seconds, warning_number
  - Add fields to Attempt model: is_flagged, flag_reason, auto_submitted
  - Create database migration file
  - Apply migration to database
  - _Requirements: 3.1, 3.2, 3.3, 3.5_

- [ ]* 1.1 Write property test for violation model
  - **Property 1: Warning progression consistency**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

- [x] 2. Implement repository layer





  - Create TabViolationRepository class with CRUD operations
  - Implement create_violation() method
  - Implement update_return_time() method
  - Implement get_attempt_violations() method
  - Implement count_violations() method
  - Implement get_total_time_away() method
  - _Requirements: 3.1, 3.2, 5.5_

- [ ]* 2.1 Write property test for duration calculation
  - **Property 8: Duration calculation accuracy**
  - **Validates: Requirements 5.5**

- [x] 3. Implement TabMonitoringService





  - Create TabMonitoringService class
  - Implement record_tab_switch() method with warning count logic
  - Implement record_tab_return() method with duration calculation
  - Implement get_violation_count() method
  - Implement flag_attempt_for_cheating() method
  - Implement get_activity_summary() method
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.4, 5.5_

- [ ]* 3.1 Write property test for auto-submission flagging
  - **Property 3: Auto-submission triggers flagging**
  - **Validates: Requirements 1.4, 4.4**

- [ ]* 3.2 Write property test for normal submission not flagged
  - **Property 9: Normal submission not flagged**
  - **Validates: Requirements 8.4**

- [x] 4. Implement ActivityLogService





  - Create ActivityLogService class
  - Implement get_formatted_activity_log() method
  - Implement generate_timeline_events() method
  - Format violation data for display
  - Calculate summary statistics (total violations, time away)
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 4.1 Write property test for activity log ordering
  - **Property 5: Activity log completeness**
  - **Validates: Requirements 5.2, 5.3**

- [x] 5. Create AJAX endpoints for violation recording





  - Create record_tab_switch_view() endpoint
  - Implement authentication check for student
  - Implement attempt ownership verification
  - Call TabMonitoringService to record violation
  - Return warning count and auto-submit flag in JSON response
  - Create get_tab_violations_view() endpoint for state restoration
  - _Requirements: 2.1, 3.1, 3.4_

- [ ]* 5.1 Write property test for violation recording completeness
  - **Property 4: Violation recording completeness**
  - **Validates: Requirements 2.1, 3.1**

- [x] 6. Update exam submission logic





  - Modify submit_exam_view() to accept auto_submit parameter
  - When auto_submit=true, call flag_attempt_for_cheating()
  - Set auto_submitted=True on attempt
  - Ensure auto-submitted exams are properly flagged
  - _Requirements: 1.4, 4.4_

- [x] 7. Implement client-side TabMonitor class





  - Create static/js/tab-monitor.js file
  - Implement TabMonitor class constructor
  - Implement startMonitoring() using Page Visibility API
  - Implement handleVisibilityChange() to detect tab switches
  - Implement recordViolation() to send AJAX to server
  - Implement showWarning() to display warning modals
  - Implement autoSubmitExam() to trigger submission on 4th violation
  - Implement state persistence with localStorage
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.4, 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 7.1 Write property test for violation persistence
  - **Property 2: Violation persistence across page refresh**
  - **Validates: Requirements 3.4**



- [x] 8. Integrate TabMonitor into exam page



  - Update templates/attempts/exam_take.html to include tab-monitor.js
  - Add warning count display to exam header
  - Initialize TabMonitor on page load
  - Pass attempt_id to TabMonitor
  - Add warning modal HTML structure
  - Style warning modals with Tailwind CSS
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 9. Create teacher activity log view





  - Create view_activity_log_view() in attempts/views.py
  - Implement teacher authentication check
  - Call ActivityLogService to get formatted log
  - Create templates/attempts/activity_log.html template
  - Display timeline of violations
  - Display summary statistics
  - Display flagged status prominently
  - Style with Tailwind CSS
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.4_

- [x] 10. Add flagged indicators to grading list






  - Update templates/attempts/grading_list.html
  - Add visual flag indicator (🚩 emoji or icon) for flagged attempts
  - Display flag_reason on hover or in tooltip
  - Add "View Activity" button for each attempt
  - Link button to activity log view
  - Style flagged rows with subtle background color
  - _Requirements: 4.1, 4.4, 6.1_

- [ ]* 10.1 Write property test for flagged indicator visibility
  - **Property 6: Flagged indicator visibility**
  - **Validates: Requirements 4.1, 4.2, 4.3**

- [x] 11. Add flagged indicators to student exam history





  - Update templates/users/student_profile.html or student history template
  - Add visual flag indicator for flagged attempts
  - Display flag_reason
  - Add "View Activity" button
  - Link to activity log view
  - _Requirements: 4.2, 4.4, 6.2_

- [x] 12. Add flagged indicators to class results





  - Update templates/exams/class_results.html or relevant template
  - Add visual flag indicator for flagged attempts
  - Display flag_reason
  - Add "View Activity" button
  - Link to activity log view
  - _Requirements: 4.3, 4.4, 6.3_

- [ ]* 12.1 Write property test for activity log accessibility
  - **Property 10: Activity log accessibility**
  - **Validates: Requirements 6.1, 6.2, 6.3**

- [x] 13. Add URL routes




  - Add route for record_tab_switch_view()
  - Add route for get_tab_violations_view()
  - Add route for view_activity_log_view()
  - Update attempts/urls.py
  - _Requirements: All_

- [x] 14. Implement error handling





  - Add try-catch blocks in TabMonitor for network failures
  - Implement retry logic with exponential backoff
  - Add error handling in views for invalid data
  - Handle concurrent violation recording with transactions
  - Add validation for attempt ownership
  - Log all errors appropriately
  - _Requirements: 8.1, 8.2, 8.5_

- [ ]* 14.1 Write unit tests for error handling
  - Test network failure scenarios
  - Test invalid attempt ID
  - Test concurrent violation recording
  - Test attempt already submitted
  - _Requirements: 8.1, 8.2, 8.5_

- [x] 15. Add warning count display to exam page





  - Update exam_take.html to show current warning count
  - Display "0/3 warnings" when no violations
  - Update display dynamically when warnings occur
  - Style with appropriate colors (green → yellow → red)
  - Position prominently near timer
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 15.1 Write property test for warning count display accuracy
  - **Property 7: Warning count display accuracy**
  - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

- [x] 16. Update AttemptService for flagging





  - Add method to flag attempt: flag_attempt()
  - Add method to check if attempt is flagged: is_flagged()
  - Update submit_attempt() to handle auto_submit parameter
  - Ensure flagged attempts are properly marked
  - _Requirements: 1.4, 4.4_

- [x] 17. Add admin interface for TabViolation




  - Register TabViolation model in admin.py
  - Configure list display fields
  - Add filters for attempt and warning_number
  - Add search by attempt
  - Make read-only (violations should not be manually edited)
  - _Requirements: 3.1, 3.2_

- [ ] 18. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 19. Test cross-browser compatibility
  - Test on Chrome, Firefox, Safari, Edge
  - Verify Page Visibility API works consistently
  - Test on mobile browsers (iOS Safari, Chrome Mobile)
  - Document any browser-specific issues
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 20. Test edge cases
  - Test browser crash and recovery
  - Test network interruption during violation
  - Test multiple tabs open simultaneously
  - Test rapid tab switching
  - Test page refresh with violations
  - Test auto-submission flow end-to-end
  - _Requirements: 8.1, 8.2, 8.3, 8.5_

- [ ] 21. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
