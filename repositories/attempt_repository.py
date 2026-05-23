"""
Attempt repository for data access operations.
Implements the Repository pattern for Attempt model.
"""
from typing import Optional, List
from django.db.models import QuerySet
from attempts.models import Attempt, AttemptStatus
from repositories.base_repository import BaseRepository


class AttemptRepository(BaseRepository):
    """
    Repository for Attempt model with specialized query methods.
    """
    
    def __init__(self):
        super().__init__(Attempt)
    
    def get_by_student(self, student_id: int) -> QuerySet:
        """
        Retrieve all attempts by a specific student with optimized queries.
        Uses select_related for student and exam foreign keys.
        
        Args:
            student_id: Primary key of the student
            
        Returns:
            QuerySet of Attempt instances for the student with related data prefetched
            
        Requirements: 9.5
        """
        return self.filter(student_id=student_id).select_related('student', 'exam')
    
    def get_by_exam(self, exam_id: int) -> QuerySet:
        """
        Retrieve all attempts for a specific exam with optimized queries.
        Uses select_related for student and exam foreign keys.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            QuerySet of Attempt instances for the exam with related data prefetched
            
        Requirements: 9.5
        """
        return self.filter(exam_id=exam_id).select_related('student', 'exam')
    
    def get_by_student_and_exam(self, student_id: int, exam_id: int) -> QuerySet:
        """
        Retrieve attempts by a student for a specific exam.
        
        Args:
            student_id: Primary key of the student
            exam_id: Primary key of the exam
            
        Returns:
            QuerySet of Attempt instances
        """
        return self.filter(student_id=student_id, exam_id=exam_id)
    
    def get_in_progress_attempt(self, student_id: int, exam_id: int) -> Optional[Attempt]:
        """
        Retrieve an in-progress attempt for a student and exam.
        
        Args:
            student_id: Primary key of the student
            exam_id: Primary key of the exam
            
        Returns:
            Attempt instance if found, None otherwise
        """
        try:
            return self.model.objects.get(
                student_id=student_id,
                exam_id=exam_id,
                status=AttemptStatus.IN_PROGRESS
            )
        except self.model.DoesNotExist:
            return None
    
    def get_with_answers(self, attempt_id: int) -> Optional[Attempt]:
        """
        Retrieve an attempt with its answers prefetched.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            Attempt instance with answers prefetched, None if not found
        """
        try:
            return self.model.objects.prefetch_related('answers').get(pk=attempt_id)
        except self.model.DoesNotExist:
            return None
    
    def get_with_answers_and_questions(self, attempt_id: int) -> Optional[Attempt]:
        """
        Retrieve an attempt with answers and questions prefetched.
        Uses select_related for student and exam, and prefetch_related for answers and questions.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            Attempt instance with answers and questions prefetched, None if not found
            
        Requirements: 9.5
        """
        try:
            return self.model.objects.select_related(
                'student',
                'exam'
            ).prefetch_related(
                'answers',
                'answers__question'
            ).get(pk=attempt_id)
        except self.model.DoesNotExist:
            return None
    
    def get_submitted_attempts(self) -> QuerySet:
        """
        Retrieve all submitted attempts with optimized queries.
        Uses select_related for student and exam foreign keys.
        
        Returns:
            QuerySet of submitted Attempt instances with related data prefetched
            
        Requirements: 9.5
        """
        return self.filter(status=AttemptStatus.SUBMITTED).select_related('student', 'exam')
    
    def get_graded_attempts(self) -> QuerySet:
        """
        Retrieve all graded attempts with optimized queries.
        Uses select_related for student and exam foreign keys.
        
        Returns:
            QuerySet of graded Attempt instances with related data prefetched
            
        Requirements: 9.5
        """
        return self.filter(status=AttemptStatus.GRADED).select_related('student', 'exam')
    
    def update_status(self, attempt_id: int, status: str) -> Optional[Attempt]:
        """
        Update the status of an attempt.
        
        Args:
            attempt_id: Primary key of the attempt
            status: New status value
            
        Returns:
            Updated Attempt instance if found, None otherwise
        """
        return self.update(attempt_id, status=status)
    
    def update_score(self, attempt_id: int, total_score: float) -> Optional[Attempt]:
        """
        Update the total score of an attempt.
        
        Args:
            attempt_id: Primary key of the attempt
            total_score: New total score
            
        Returns:
            Updated Attempt instance if found, None otherwise
        """
        return self.update(attempt_id, total_score=total_score)
