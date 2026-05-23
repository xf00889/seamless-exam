# Design Document: Exam Tab Monitoring Security

## Overview

This feature implements a comprehensive exam security system that monitors student tab activity during exams. The system detects when students navigate away from the exam page, issues progressive warnings (3 warnings total), automatically submits the exam after the fourth violation, flags the attempt as potential cheating, and provides teachers with detailed activity logs through multiple interfaces.

The implementation follows a client-server architecture where JavaScript monitors tab visibility on the client side, communicates violations to the Django backend via AJAX, and persists all activity data in the database for teacher review.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Side (Browser)                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  TabMonitor (JavaScript)                               │ │
│  │  - Detects tab switches using Page Visibility API     │ │
│  │  - Tracks warning count                               │ │
│  │  - Displays warning modals                            │ │
│  │  - Triggers auto-submission                           │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↕ AJAX                             │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                     Server Side (Django)                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Views Layer                                           │ │
│  │  - record_tab_switch_view()                           │ │
│  │  - get_tab_violations_view()                          │ │
│  │  - view_activity_log_view()                           │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↕                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Service Layer                                         │ │
│  │  - TabMonitoringService                               │ │
│  │  - ActivityLogService                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↕                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Repository Layer                                      │ │
│  │  - TabViolationRepository                             │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↕                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Data Layer (PostgreSQL/MySQL)                        │ │
│  │  - TabViolation model                                 │ │
│  │  - Attempt model (updated with flagged field)        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **Tab Switch Detection**: Browser Page Visibility API detects when student leaves exam tab
2. **Violation Recording**: AJAX request sent to Django backend to record violation
3. **Warning Display**: Server returns current warning count, client displays modal
4. **Auto-Submission**: On 4th violation, client triggers exam submission and server flags attempt
5. **Teacher Review**: Teachers access activity logs through grading list, student history, or class results

## Components and Interfaces

### 1. Database Models

#### TabViolation Model (New)

```python
class TabViolation(models.Model):
    """
    Records each instance of a student switching away from the exam tab.
    """
    attempt = models.ForeignKey(
        Attempt,
        on_delete=models.CASCADE,
        related_name='tab_violations'
    )
    violated_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duration away from exam in seconds"
    )
    warning_number = models.IntegerField(
        help_text="Which warning this violation triggered (1-3)"
    )
    
    class Meta:
        db_table = 'attempts_tab_violation'
        ordering = ['violated_at']
        indexes = [
            models.Index(fields=['attempt', 'violated_at']),
        ]
```

#### Attempt Model (Updated)

```python
class Attempt(models.Model):
    # ... existing fields ...
    
    is_flagged = models.BooleanField(
        default=False,
        help_text="Flagged for potential cheating"
    )
    flag_reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Reason for flagging (e.g., 'Auto-submitted after 4 tab switches')"
    )
    auto_submitted = models.BooleanField(
        default=False,
        help_text="Whether exam was auto-submitted due to violations"
    )
```

### 2. Client-Side Components

#### TabMonitor Class (JavaScript)

```javascript
class TabMonitor {
    constructor(attemptId)
    
    // Core Methods
    startMonitoring()
    stopMonitoring()
    handleVisibilityChange()
    recordViolation()
    showWarning(warningNumber, totalWarnings)
    autoSubmitExam()
    
    // State Management
    loadViolationState()
    saveViolationState()
    
    // API Communication
    async sendViolationToServer(violationData)
    async getCurrentViolationCount()
}
```

**Key Responsibilities:**
- Monitor Page Visibility API events
- Track local violation count
- Display warning modals with appropriate messaging
- Trigger auto-submission on 4th violation
- Persist state across page refreshes
- Communicate with backend via AJAX

### 3. Backend Services

#### TabMonitoringService

```python
class TabMonitoringService:
    """
    Business logic for tab monitoring and violation management.
    """
    
    def record_tab_switch(
        self,
        attempt_id: int,
        violated_at: datetime
    ) -> Dict[str, Any]:
        """
        Records a tab switch violation and returns current warning count.
        
        Returns:
            {
                'warning_number': int,
                'total_warnings': int,
                'should_auto_submit': bool
            }
        """
    
    def record_tab_return(
        self,
        attempt_id: int,
        violation_id: int,
        returned_at: datetime
    ) -> bool:
        """
        Records when student returns to exam tab.
        Calculates duration away.
        """
    
    def get_violation_count(self, attempt_id: int) -> int:
        """Returns total number of violations for an attempt."""
    
    def flag_attempt_for_cheating(
        self,
        attempt_id: int,
        reason: str
    ) -> bool:
        """Flags an attempt as potential cheating."""
    
    def get_activity_summary(
        self,
        attempt_id: int
    ) -> Dict[str, Any]:
        """
        Returns comprehensive activity summary.
        
        Returns:
            {
                'total_violations': int,
                'total_time_away': int (seconds),
                'violations': List[TabViolation],
                'is_flagged': bool,
                'flag_reason': str,
                'auto_submitted': bool
            }
        """
```

#### ActivityLogService

```python
class ActivityLogService:
    """
    Service for generating and formatting activity logs for teacher review.
    """
    
    def get_formatted_activity_log(
        self,
        attempt_id: int
    ) -> Dict[str, Any]:
        """
        Returns formatted activity log with all events.
        
        Returns:
            {
                'attempt': Attempt,
                'student': Student,
                'exam': Exam,
                'violations': List[Dict],
                'summary': Dict,
                'timeline': List[Dict]
            }
        """
    
    def generate_timeline_events(
        self,
        attempt: Attempt
    ) -> List[Dict]:
        """
        Generates chronological timeline of all exam events.
        Includes: start, tab switches, warnings, submission.
        """
```

### 4. Repository Layer

#### TabViolationRepository

```python
class TabViolationRepository:
    """
    Data access layer for tab violations.
    """
    
    def create_violation(
        self,
        attempt_id: int,
        warning_number: int
    ) -> TabViolation
    
    def update_return_time(
        self,
        violation_id: int,
        returned_at: datetime
    ) -> TabViolation
    
    def get_attempt_violations(
        self,
        attempt_id: int
    ) -> QuerySet[TabViolation]
    
    def count_violations(self, attempt_id: int) -> int
    
    def get_total_time_away(self, attempt_id: int) -> int
```

### 5. View Layer

#### AJAX Endpoints

```python
@require_http_methods(["POST"])
def record_tab_switch_view(request, attempt_id):
    """
    Records a tab switch violation.
    
    Request Body:
        {
            "violated_at": "ISO datetime string"
        }
    
    Response:
        {
            "success": true,
            "warning_number": 1,
            "total_warnings": 3,
            "should_auto_submit": false
        }
    """

@require_http_methods(["GET"])
def get_tab_violations_view(request, attempt_id):
    """
    Returns current violation count for an attempt.
    Used for state restoration after page refresh.
    
    Response:
        {
            "violation_count": 2,
            "is_flagged": false
        }
    """
```

#### Teacher Views

```python
def view_activity_log_view(request, attempt_id):
    """
    Displays detailed activity log for a specific attempt.
    Accessible from grading list, student history, class results.
    
    Shows:
    - Timeline of all tab switches
    - Warning history
    - Total time away from exam
    - Auto-submission status
    - Flagged status
    """
```

## Data Models

### TabViolation

| Field | Type | Description |
|-------|------|-------------|
| id | Integer (PK) | Primary key |
| attempt | ForeignKey | Reference to Attempt |
| violated_at | DateTime | When student left exam tab |
| returned_at | DateTime (nullable) | When student returned |
| duration_seconds | Integer (nullable) | Time away in seconds |
| warning_number | Integer | Which warning (1-3) |

### Attempt (Updated Fields)

| Field | Type | Description |
|-------|------|-------------|
| is_flagged | Boolean | Flagged for cheating |
| flag_reason | String | Reason for flag |
| auto_submitted | Boolean | Auto-submitted due to violations |

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Warning progression consistency

*For any* exam attempt, the sequence of warnings should always be 1, 2, 3, and the 4th violation should trigger auto-submission without displaying a 4th warning.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 2: Violation persistence across page refresh

*For any* exam attempt with recorded violations, refreshing the page should restore the exact same warning count that existed before the refresh.

**Validates: Requirements 3.4**

### Property 3: Auto-submission triggers flagging

*For any* exam attempt that is auto-submitted due to tab violations, the attempt should be marked as flagged with the reason "Auto-submitted after 4 tab switches".

**Validates: Requirements 1.4, 4.4**

### Property 4: Violation recording completeness

*For any* tab switch event detected by the client, a corresponding TabViolation record should exist in the database with the correct timestamp and warning number.

**Validates: Requirements 2.1, 3.1**

### Property 5: Activity log completeness

*For any* exam attempt with violations, the activity log should contain all tab switch events in chronological order with accurate timestamps.

**Validates: Requirements 5.2, 5.3**

### Property 6: Flagged indicator visibility

*For any* flagged attempt, when displayed in the grading list, student history, or class results, a visual indicator should be present.

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 7: Warning count display accuracy

*For any* student taking an exam, the displayed warning count on the exam page should always match the number of violations recorded in the database.

**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

### Property 8: Duration calculation accuracy

*For any* violation where both violated_at and returned_at are recorded, the duration_seconds should equal the difference between these timestamps.

**Validates: Requirements 5.5**

### Property 9: Normal submission not flagged

*For any* exam attempt that is submitted normally by the student (not auto-submitted), the attempt should not be flagged as cheating regardless of warning count.

**Validates: Requirements 8.4**

### Property 10: Activity log accessibility

*For any* exam attempt, teachers should be able to access the activity log from at least three different locations: grading list, student history, and class results.

**Validates: Requirements 6.1, 6.2, 6.3**

## Error Handling

### Client-Side Error Handling

1. **Network Failures**
   - Queue violation events locally if server unreachable
   - Retry with exponential backoff
   - Sync queued events when connection restored

2. **Page Visibility API Unavailable**
   - Gracefully degrade (no monitoring)
   - Log warning to console
   - Display notice to teacher in admin panel

3. **State Corruption**
   - Validate localStorage data before use
   - Fall back to server state if local state invalid
   - Clear corrupted state and start fresh

### Server-Side Error Handling

1. **Concurrent Violation Recording**
   - Use database transactions
   - Handle race conditions with proper locking
   - Ensure warning numbers are sequential

2. **Invalid Attempt ID**
   - Return 404 with clear error message
   - Log suspicious activity

3. **Attempt Already Submitted**
   - Reject violation recording
   - Return appropriate error code
   - Prevent post-submission manipulation

4. **Database Failures**
   - Log errors comprehensively
   - Return user-friendly error messages
   - Implement retry logic for transient failures

## Testing Strategy

### Unit Testing

**Client-Side (JavaScript)**
- Test TabMonitor class methods in isolation
- Mock Page Visibility API events
- Verify warning modal display logic
- Test state persistence to localStorage
- Verify AJAX request formatting

**Server-Side (Python)**
- Test TabMonitoringService methods
- Test ActivityLogService formatting
- Test TabViolationRepository CRUD operations
- Test view authentication and authorization
- Test edge cases (concurrent requests, invalid data)

### Property-Based Testing

We will use Hypothesis (Python) for property-based testing of the backend logic.

**Property Tests:**

1. **Warning Sequence Property**
   - Generate random sequences of tab switches
   - Verify warning numbers are always 1, 2, 3
   - Verify 4th switch triggers auto-submission

2. **Duration Calculation Property**
   - Generate random violated_at and returned_at timestamps
   - Verify duration_seconds calculation is always correct

3. **State Restoration Property**
   - Generate random violation counts
   - Simulate page refresh
   - Verify restored count matches original

4. **Flagging Consistency Property**
   - Generate random attempts with various violation counts
   - Verify only auto-submitted attempts are flagged
   - Verify flag_reason is always set correctly

5. **Activity Log Ordering Property**
   - Generate random violation sequences
   - Verify activity log is always chronologically ordered

### Integration Testing

1. **End-to-End Tab Monitoring Flow**
   - Start exam
   - Trigger tab switches
   - Verify warnings displayed
   - Verify auto-submission on 4th violation
   - Verify flagging in database

2. **Teacher Activity Log Access**
   - Create flagged attempt
   - Access from grading list
   - Access from student history
   - Access from class results
   - Verify all show same data

3. **State Persistence**
   - Start exam
   - Trigger violations
   - Refresh page
   - Verify warning count restored
   - Continue exam
   - Verify violations accumulate correctly

### Manual Testing

1. **Cross-Browser Compatibility**
   - Test on Chrome, Firefox, Safari, Edge
   - Verify Page Visibility API works consistently
   - Test on mobile browsers

2. **User Experience**
   - Verify warning modals are clear and not intrusive
   - Test warning display timing
   - Verify auto-submission is smooth
   - Test teacher activity log readability

3. **Edge Cases**
   - Browser crash and recovery
   - Network interruption during violation
   - Multiple tabs open simultaneously
   - Rapid tab switching

## Security Considerations

1. **Client-Side Bypass Prevention**
   - All violation logic enforced server-side
   - Client cannot manipulate warning count
   - Server validates all violation timestamps
   - Auto-submission triggered by server, not client

2. **Authentication & Authorization**
   - Verify student owns attempt before recording violations
   - Verify teacher authentication before showing activity logs
   - Prevent students from viewing other students' violations

3. **Data Integrity**
   - Use database transactions for violation recording
   - Prevent tampering with violation records
   - Audit log for all flagging actions

4. **Privacy**
   - Only store necessary violation data
   - Limit access to activity logs to authorized teachers
   - Clear violation data according to retention policy

## Performance Considerations

1. **Database Optimization**
   - Index on (attempt_id, violated_at) for fast queries
   - Use select_related/prefetch_related for activity logs
   - Cache violation counts for frequently accessed attempts

2. **Client-Side Optimization**
   - Debounce rapid visibility changes
   - Use localStorage for state persistence
   - Minimize AJAX requests

3. **Scalability**
   - Violation recording should handle concurrent exams
   - Activity log generation should be efficient for large datasets
   - Consider pagination for attempts with many violations

## UI/UX Design

### Warning Modal Design

```
┌─────────────────────────────────────────┐
│  ⚠️  Warning: Tab Switch Detected       │
│                                         │
│  You have switched away from the exam.  │
│                                         │
│  Warning 1 of 3                         │
│                                         │
│  After 3 warnings, your exam will be    │
│  automatically submitted and flagged.   │
│                                         │
│  [OK, I Understand]                     │
└─────────────────────────────────────────┘
```

### Warning Count Display (Exam Page)

```
┌─────────────────────────────────────────┐
│  Exam: Physics Final                    │
│  Time Remaining: 45:23                  │
│  Warnings: 2/3 ⚠️                       │
└─────────────────────────────────────────┘
```

### Flagged Indicator (Grading List)

```
┌─────────────────────────────────────────────────────────┐
│ Student Name    │ Exam         │ Score │ Status │ Actions│
├─────────────────┼──────────────┼───────┼────────┼────────┤
│ John Doe 🚩     │ Physics Final│ 85%   │ Graded │ [View] │
│                 │              │       │        │ [Activity]│
└─────────────────────────────────────────────────────────┘
```

### Activity Log View

```
┌─────────────────────────────────────────────────────────┐
│  Activity Log: John Doe - Physics Final                │
│                                                         │
│  Status: 🚩 Flagged (Auto-submitted after 4 tab switches)│
│  Total Violations: 4                                    │
│  Total Time Away: 3 minutes 45 seconds                  │
│                                                         │
│  Timeline:                                              │
│  ├─ 10:00:00 - Exam started                            │
│  ├─ 10:15:23 - Tab switch (Warning 1) - Away 45s       │
│  ├─ 10:28:10 - Tab switch (Warning 2) - Away 1m 20s    │
│  ├─ 10:35:45 - Tab switch (Warning 3) - Away 30s       │
│  ├─ 10:42:18 - Tab switch (4th) - Auto-submitted       │
│  └─ 10:42:18 - Exam submitted (Auto)                   │
└─────────────────────────────────────────────────────────┘
```

## Implementation Notes

1. **Page Visibility API**: Use `document.visibilityState` and `visibilitychange` event
2. **Warning Threshold**: Configurable via Django settings (default: 3 warnings)
3. **Violation Grace Period**: Consider 2-second grace period to avoid false positives from accidental clicks
4. **Mobile Considerations**: Page Visibility API behaves differently on mobile; test thoroughly
5. **Accessibility**: Ensure warning modals are screen-reader friendly
6. **Internationalization**: All warning messages should support i18n

## Future Enhancements

1. **Configurable Warning Thresholds**: Allow teachers to set warning limits per exam
2. **Violation Analytics**: Dashboard showing violation trends across exams
3. **Video Proctoring Integration**: Combine tab monitoring with webcam monitoring
4. **Machine Learning**: Detect suspicious patterns beyond simple tab switches
5. **Student Appeals**: Allow students to contest flagged attempts with explanations
