"""
Tab monitoring service for business logic operations.
Handles tab violation tracking, warning management, and attempt flagging.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from django.db import transaction
from django.utils import timezone
from attempts.models import Attempt, AttemptStatus
from repositories.tab_violation_repository import TabViolationRepository
from repositories.attempt_repository import AttemptRepository

logger = logging.getLogger(__name__)


class TabMonitoringService:
    """
    Service class for tab monitoring and violation management.
    Handles recording violations, issuing warnings, and flagging attempts.
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.4, 5.5
    """
    
    # Constants for warning thresholds
    MAX_WARNINGS = 3
    AUTO_SUBMIT_THRESHOLD = 4
    
    def __init__(self):
        """Initialize tab monitoring service with required repositories."""
        self.violation_repository = TabViolationRepository()
        self.attempt_repository = AttemptRepository()
    
    def record_tab_switch(
        self,
        attempt_id: int,
        violated_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Records a tab switch violation and returns current warning count.
        Implements progressive warning logic (1, 2, 3 warnings).
        Uses database transactions to handle concurrent violation recording.
        
        Args:
            attempt_id: Primary key of the attempt
            violated_at: Timestamp when violation occurred (defaults to now)
            
        Returns:
            Dictionary containing:
                - warning_number: Current warning number (1-3)
                - total_warnings: Maximum warnings allowed (3)
                - should_auto_submit: Whether exam should be auto-submitted (4th violation)
                - violation_id: ID of created violation record
                
        Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 3.1, 3.2, 8.1, 8.2, 8.5
        """
        try:
            # Validate attempt_id
            if not isinstance(attempt_id, int) or attempt_id <= 0:
                raise ValueError(f"Invalid attempt_id: {attempt_id}")
            
            # Use current time if not provided
            if violated_at is None:
                violated_at = timezone.now()
            
            # Validate timestamp
            if not isinstance(violated_at, datetime):
                raise ValueError(f"Invalid violated_at timestamp: {violated_at}")
            
            # Use transaction to handle concurrent violation recording
            with transaction.atomic():
                # Lock the attempt row to prevent race conditions
                attempt = Attempt.objects.select_for_update().get(id=attempt_id)
                
                # Verify attempt is still in progress
                if attempt.status != AttemptStatus.IN_PROGRESS:
                    logger.warning(
                        f"Cannot record violation for attempt {attempt_id}: "
                        f"Status is {attempt.status}"
                    )
                    raise ValueError("Cannot record violations for submitted exams")
                
                # Get current violation count (within transaction)
                current_count = self.violation_repository.count_violations(attempt_id)
                
                # Calculate warning number (1-based)
                warning_number = current_count + 1
                
                # Determine if this should trigger auto-submission
                should_auto_submit = warning_number >= self.AUTO_SUBMIT_THRESHOLD
                
                # Create violation record (only if warning_number <= 3)
                # The 4th violation triggers auto-submit but doesn't create a warning
                violation_id = None
                if warning_number <= self.MAX_WARNINGS:
                    violation = self.violation_repository.create_violation(
                        attempt_id=attempt_id,
                        warning_number=warning_number
                    )
                    violation_id = violation.id if violation else None
                    
                    if not violation_id:
                        logger.error(f"Failed to create violation record for attempt {attempt_id}")
                        raise Exception("Failed to create violation record")
            
            logger.info(
                f"Tab switch recorded for attempt {attempt_id}: "
                f"Warning {warning_number}, Auto-submit: {should_auto_submit}"
            )
            
            return {
                'warning_number': warning_number,
                'total_warnings': self.MAX_WARNINGS,
                'should_auto_submit': should_auto_submit,
                'violation_id': violation_id
            }
        except Attempt.DoesNotExist:
            logger.error(f"Attempt {attempt_id} not found")
            raise ValueError(f"Attempt {attempt_id} not found")
        except ValueError as e:
            logger.error(f"Validation error recording tab switch for attempt {attempt_id}: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error recording tab switch for attempt {attempt_id}: {e}",
                exc_info=True
            )
            raise
    
    def record_tab_return(
        self,
        attempt_id: int,
        violation_id: int,
        returned_at: Optional[datetime] = None
    ) -> bool:
        """
        Records when student returns to exam tab.
        Calculates and stores duration away from exam.
        
        Args:
            attempt_id: Primary key of the attempt
            violation_id: Primary key of the violation to update
            returned_at: Timestamp when student returned (defaults to now)
            
        Returns:
            True if return time recorded successfully, False otherwise
            
        Requirements: 2.4, 5.5
        """
        try:
            # Use current time if not provided
            if returned_at is None:
                returned_at = timezone.now()
            
            # Update violation with return time (duration calculated in repository)
            violation = self.violation_repository.update_return_time(
                violation_id=violation_id,
                returned_at=returned_at
            )
            
            if violation:
                logger.info(
                    f"Tab return recorded for attempt {attempt_id}, "
                    f"violation {violation_id}: Duration {violation.duration_seconds}s"
                )
                return True
            else:
                logger.warning(
                    f"Failed to record tab return: Violation {violation_id} not found"
                )
                return False
        except Exception as e:
            logger.error(
                f"Error recording tab return for attempt {attempt_id}, "
                f"violation {violation_id}: {e}"
            )
            return False
    
    def get_violation_count(self, attempt_id: int) -> int:
        """
        Returns total number of violations for an attempt.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            Number of violations for the attempt
            
        Requirements: 3.2, 7.1, 7.2, 7.3, 7.4
        """
        try:
            return self.violation_repository.count_violations(attempt_id)
        except Exception as e:
            logger.error(f"Error getting violation count for attempt {attempt_id}: {e}")
            return 0
    
    def flag_attempt_for_cheating(
        self,
        attempt_id: int,
        reason: str
    ) -> bool:
        """
        Flags an attempt as potential cheating.
        Sets is_flagged=True, stores reason, and marks as auto_submitted.
        Uses database transactions to prevent concurrent modification issues.
        
        Args:
            attempt_id: Primary key of the attempt
            reason: Reason for flagging (e.g., "Auto-submitted after 4 tab switches")
            
        Returns:
            True if flagging successful, False otherwise
            
        Requirements: 1.4, 4.4, 8.1, 8.2, 8.5
        """
        try:
            # Validate inputs
            if not isinstance(attempt_id, int) or attempt_id <= 0:
                logger.error(f"Invalid attempt_id for flagging: {attempt_id}")
                return False
            
            if not reason or not isinstance(reason, str):
                logger.error(f"Invalid reason for flagging attempt {attempt_id}: {reason}")
                return False
            
            # Truncate reason if too long (database field limit)
            if len(reason) > 255:
                reason = reason[:252] + '...'
            
            with transaction.atomic():
                # Lock the attempt row to prevent concurrent modifications
                attempt = Attempt.objects.select_for_update().get(id=attempt_id)
                
                # Check if already flagged
                if attempt.is_flagged:
                    logger.info(
                        f"Attempt {attempt_id} already flagged: {attempt.flag_reason}"
                    )
                    return True  # Already flagged, consider it success
                
                # Update flagging fields
                attempt.is_flagged = True
                attempt.flag_reason = reason
                attempt.auto_submitted = True
                
                attempt.save(update_fields=['is_flagged', 'flag_reason', 'auto_submitted'])
                
                logger.info(
                    f"Attempt {attempt_id} flagged for cheating: {reason}"
                )
                
                return True
        except Attempt.DoesNotExist:
            logger.error(f"Cannot flag attempt {attempt_id}: Attempt not found")
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error flagging attempt {attempt_id}: {e}",
                exc_info=True
            )
            return False
    
    def get_activity_summary(
        self,
        attempt_id: int
    ) -> Dict[str, Any]:
        """
        Returns comprehensive activity summary for an attempt.
        Includes violations, time away, and flagging status.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            Dictionary containing:
                - found: Whether attempt was found
                - total_violations: Total number of violations
                - total_time_away: Total time away in seconds
                - violations: List of TabViolation objects
                - is_flagged: Whether attempt is flagged
                - flag_reason: Reason for flagging (if flagged)
                - auto_submitted: Whether exam was auto-submitted
                - attempt: Attempt object
                - error: Error message (if found=False)
                
        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 8.1, 8.2
        """
        try:
            # Validate attempt_id
            if not isinstance(attempt_id, int) or attempt_id <= 0:
                logger.error(f"Invalid attempt_id: {attempt_id}")
                return {
                    'found': False,
                    'error': 'Invalid attempt ID'
                }
            
            # Get attempt with error handling
            attempt = self.attempt_repository.get_by_id(attempt_id)
            
            if not attempt:
                logger.error(f"Attempt {attempt_id} not found")
                return {
                    'found': False,
                    'error': 'Attempt not found'
                }
            
            # Get all violations with error handling
            try:
                violations = list(self.violation_repository.get_attempt_violations(attempt_id))
            except Exception as e:
                logger.error(f"Error retrieving violations for attempt {attempt_id}: {e}")
                violations = []
            
            # Get total time away with error handling
            try:
                total_time_away = self.violation_repository.get_total_time_away(attempt_id)
                # Validate total_time_away is a valid number
                if not isinstance(total_time_away, (int, float)) or total_time_away < 0:
                    logger.warning(f"Invalid total_time_away for attempt {attempt_id}: {total_time_away}")
                    total_time_away = 0
            except Exception as e:
                logger.error(f"Error calculating total time away for attempt {attempt_id}: {e}")
                total_time_away = 0
            
            # Count violations
            total_violations = len(violations)
            
            logger.info(
                f"Activity summary for attempt {attempt_id}: "
                f"{total_violations} violations, {total_time_away}s away"
            )
            
            return {
                'found': True,
                'attempt_id': attempt_id,
                'total_violations': total_violations,
                'total_time_away': total_time_away,
                'violations': violations,
                'is_flagged': bool(attempt.is_flagged),
                'flag_reason': attempt.flag_reason or '',
                'auto_submitted': bool(attempt.auto_submitted),
                'attempt': attempt
            }
        except Exception as e:
            logger.error(
                f"Unexpected error getting activity summary for attempt {attempt_id}: {e}",
                exc_info=True
            )
            return {
                'found': False,
                'error': 'Internal server error'
            }
