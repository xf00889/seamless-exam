"""
Tab violation repository for data access operations.
Implements the Repository pattern for TabViolation model.
"""
from typing import Optional
from datetime import datetime
from django.db.models import QuerySet, Sum, Q
from attempts.models import TabViolation
from repositories.base_repository import BaseRepository


class TabViolationRepository(BaseRepository):
    """
    Repository for TabViolation model with specialized query methods.
    Handles CRUD operations for tab violation tracking.
    """
    
    def __init__(self):
        super().__init__(TabViolation)
    
    def create_violation(
        self,
        attempt_id: int,
        warning_number: int
    ) -> TabViolation:
        """
        Create a new tab violation record.
        
        Args:
            attempt_id: Primary key of the attempt
            warning_number: Which warning this violation triggered (1-3)
            
        Returns:
            Created TabViolation instance
            
        Requirements: 3.1, 3.2
        """
        return self.create(
            attempt_id=attempt_id,
            warning_number=warning_number
        )
    
    def update_return_time(
        self,
        violation_id: int,
        returned_at: datetime
    ) -> Optional[TabViolation]:
        """
        Update the return time for a violation and calculate duration.
        
        Args:
            violation_id: Primary key of the violation
            returned_at: Timestamp when student returned to exam tab
            
        Returns:
            Updated TabViolation instance if found, None otherwise
            
        Requirements: 3.1, 5.5
        """
        violation = self.get_by_id(violation_id)
        if violation:
            violation.returned_at = returned_at
            # Calculate duration in seconds
            duration = (returned_at - violation.violated_at).total_seconds()
            violation.duration_seconds = int(duration)
            violation.save()
        return violation
    
    def get_attempt_violations(
        self,
        attempt_id: int
    ) -> QuerySet:
        """
        Retrieve all violations for a specific attempt.
        Returns violations ordered by violated_at timestamp.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            QuerySet of TabViolation instances ordered chronologically
            
        Requirements: 3.1, 5.5
        """
        return self.filter(attempt_id=attempt_id).order_by('violated_at')
    
    def count_violations(self, attempt_id: int) -> int:
        """
        Count the total number of violations for an attempt.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            Number of violations for the attempt
            
        Requirements: 3.2
        """
        return self.count(attempt_id=attempt_id)
    
    def get_total_time_away(self, attempt_id: int) -> int:
        """
        Calculate the total time a student was away from the exam tab.
        Sums all duration_seconds for violations with recorded return times.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            Total time away in seconds (0 if no violations or no durations recorded)
            
        Requirements: 5.5
        """
        result = self.filter(
            attempt_id=attempt_id,
            duration_seconds__isnull=False
        ).aggregate(total=Sum('duration_seconds'))
        
        return result['total'] or 0
