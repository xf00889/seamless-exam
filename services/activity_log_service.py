"""
Activity log service for formatting and displaying exam activity data.
Handles generation of detailed activity logs for teacher review.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from django.utils import timezone
from attempts.models import Attempt
from repositories.tab_violation_repository import TabViolationRepository
from repositories.attempt_repository import AttemptRepository

logger = logging.getLogger(__name__)


class ActivityLogService:
    """
    Service for generating and formatting activity logs for teacher review.
    Provides detailed timeline of exam events including tab violations.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    
    def __init__(self):
        """Initialize activity log service with required repositories."""
        self.violation_repository = TabViolationRepository()
        self.attempt_repository = AttemptRepository()
    
    def get_formatted_activity_log(
        self,
        attempt_id: int
    ) -> Dict[str, Any]:
        """
        Returns formatted activity log with all events for an attempt.
        Includes student info, exam info, violations, summary, and timeline.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            Dictionary containing:
                - found: Whether attempt was found
                - attempt: Attempt object
                - student: Student object
                - exam: Exam object
                - violations: List of formatted violation dictionaries
                - summary: Summary statistics dictionary
                - timeline: Chronological list of all events
                - error: Error message if not found
                
        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
        """
        try:
            # Get attempt with related data
            attempt = self.attempt_repository.get_by_id(attempt_id)
            
            if not attempt:
                logger.error(f"Attempt {attempt_id} not found")
                return {
                    'found': False,
                    'error': 'Attempt not found'
                }
            
            # Get all violations
            violations = list(self.violation_repository.get_attempt_violations(attempt_id))
            
            # Format violations for display
            formatted_violations = self._format_violations(violations)
            
            # Calculate summary statistics
            summary = self._calculate_summary(attempt, violations)
            
            # Generate timeline events
            timeline = self.generate_timeline_events(attempt)
            
            logger.info(
                f"Generated activity log for attempt {attempt_id}: "
                f"{len(violations)} violations, {summary['total_time_away']}s away"
            )
            
            return {
                'found': True,
                'attempt': attempt,
                'student': attempt.student,
                'exam': attempt.exam,
                'violations': formatted_violations,
                'summary': summary,
                'timeline': timeline
            }
        except Exception as e:
            logger.error(f"Error generating activity log for attempt {attempt_id}: {e}")
            return {
                'found': False,
                'error': str(e)
            }
    
    def generate_timeline_events(
        self,
        attempt: Attempt
    ) -> List[Dict[str, Any]]:
        """
        Generates chronological timeline of all exam events.
        Includes: exam start, tab switches, warnings, returns, and submission.
        
        Args:
            attempt: Attempt instance
            
        Returns:
            List of event dictionaries, each containing:
                - timestamp: DateTime of event
                - event_type: Type of event (start, violation, return, submit)
                - description: Human-readable description
                - warning_number: Warning number (for violations)
                - duration: Duration away (for returns)
                - is_critical: Whether event is critical (auto-submit, flagged)
                
        Requirements: 5.2, 5.3, 5.4
        """
        try:
            timeline = []
            
            # Add exam start event
            timeline.append({
                'timestamp': attempt.started_at,
                'event_type': 'start',
                'description': 'Exam started',
                'is_critical': False
            })
            
            # Get all violations
            violations = list(self.violation_repository.get_attempt_violations(attempt.id))
            
            # Add violation and return events
            for violation in violations:
                # Add violation event
                timeline.append({
                    'timestamp': violation.violated_at,
                    'event_type': 'violation',
                    'description': f'Tab switch detected (Warning {violation.warning_number} of 3)',
                    'warning_number': violation.warning_number,
                    'is_critical': violation.warning_number == 3  # Last warning is critical
                })
                
                # Add return event if student returned
                if violation.returned_at:
                    duration_str = self._format_duration(violation.duration_seconds)
                    timeline.append({
                        'timestamp': violation.returned_at,
                        'event_type': 'return',
                        'description': f'Returned to exam (Away for {duration_str})',
                        'duration': violation.duration_seconds,
                        'duration_formatted': duration_str,
                        'is_critical': False
                    })
            
            # Add submission event
            if attempt.submitted_at:
                submission_type = 'Auto-submitted' if attempt.auto_submitted else 'Submitted'
                timeline.append({
                    'timestamp': attempt.submitted_at,
                    'event_type': 'submit',
                    'description': f'{submission_type} by {"system" if attempt.auto_submitted else "student"}',
                    'is_critical': attempt.auto_submitted,
                    'auto_submitted': attempt.auto_submitted
                })
            
            # Sort timeline by timestamp
            timeline.sort(key=lambda x: x['timestamp'])
            
            logger.info(f"Generated timeline with {len(timeline)} events for attempt {attempt.id}")
            
            return timeline
        except Exception as e:
            logger.error(f"Error generating timeline for attempt {attempt.id}: {e}")
            return []
    
    def _format_violations(
        self,
        violations: List
    ) -> List[Dict[str, Any]]:
        """
        Format violation objects for display.
        
        Args:
            violations: List of TabViolation objects
            
        Returns:
            List of formatted violation dictionaries
        """
        formatted = []
        
        for violation in violations:
            formatted.append({
                'id': violation.id,
                'violated_at': violation.violated_at,
                'returned_at': violation.returned_at,
                'duration_seconds': violation.duration_seconds,
                'duration_formatted': self._format_duration(violation.duration_seconds) if violation.duration_seconds else 'Still away',
                'warning_number': violation.warning_number
            })
        
        return formatted
    
    def _calculate_summary(
        self,
        attempt: Attempt,
        violations: List
    ) -> Dict[str, Any]:
        """
        Calculate summary statistics for an attempt.
        
        Args:
            attempt: Attempt instance
            violations: List of TabViolation objects
            
        Returns:
            Dictionary containing summary statistics:
                - total_violations: Total number of violations
                - total_time_away: Total time away in seconds
                - total_time_away_formatted: Formatted time away string
                - is_flagged: Whether attempt is flagged
                - flag_reason: Reason for flagging
                - auto_submitted: Whether exam was auto-submitted
                - exam_duration: Total exam duration in seconds
                - exam_duration_formatted: Formatted exam duration
                
        Requirements: 5.5
        """
        # Count violations
        total_violations = len(violations)
        
        # Calculate total time away
        total_time_away = self.violation_repository.get_total_time_away(attempt.id)
        
        # Calculate exam duration
        exam_duration = None
        exam_duration_formatted = 'In progress'
        if attempt.submitted_at:
            duration_delta = attempt.submitted_at - attempt.started_at
            exam_duration = int(duration_delta.total_seconds())
            exam_duration_formatted = self._format_duration(exam_duration)
        
        return {
            'total_violations': total_violations,
            'total_time_away': total_time_away,
            'total_time_away_formatted': self._format_duration(total_time_away),
            'is_flagged': attempt.is_flagged,
            'flag_reason': attempt.flag_reason,
            'auto_submitted': attempt.auto_submitted,
            'exam_duration': exam_duration,
            'exam_duration_formatted': exam_duration_formatted
        }
    
    def _format_duration(self, seconds: Optional[int]) -> str:
        """
        Format duration in seconds to human-readable string.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted string (e.g., "2m 30s", "1h 15m 45s")
        """
        if seconds is None or seconds == 0:
            return "0s"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or not parts:  # Always show seconds if no other parts
            parts.append(f"{secs}s")
        
        return " ".join(parts)
