"""
Attempt service for business logic operations.
Handles attempt creation, management, and session persistence.
"""
from typing import Optional, Dict, Any, List
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from attempts.models import Attempt, AttemptStatus
from repositories.attempt_repository import AttemptRepository
from repositories.answer_repository import AnswerRepository
from repositories.exam_repository import ExamRepository
from repositories.student_repository import StudentRepository


class AttemptService:
    """
    Service class for attempt-related business logic.
    Handles creating and managing exam attempts with session persistence.
    """
    
    def __init__(self):
        self.attempt_repository = AttemptRepository()
        self.answer_repository = AnswerRepository()
        self.exam_repository = ExamRepository()
        self.student_repository = StudentRepository()
    
    def create_attempt(self, student_id: int, exam_id: int) -> Optional[Attempt]:
        """
        Create a new exam attempt for a student.
        Checks if student and exam exist before creating.
        
        Args:
            student_id: Primary key of the student
            exam_id: Primary key of the exam
            
        Returns:
            Created Attempt instance, None if creation fails
        """
        try:
            # Verify student exists
            student = self.student_repository.get_by_id(student_id)
            if not student:
                print(f"Student with id {student_id} not found")
                return None
            
            # Verify exam exists and is active
            exam = self.exam_repository.get_by_id(exam_id)
            if not exam:
                print(f"Exam with id {exam_id} not found")
                return None
            
            if not exam.is_active:
                print(f"Exam {exam_id} is not active")
                return None
            
            # Check ExamStudentAssignment for individual student access
            from repositories.exam_student_assignment_repository import ExamStudentAssignmentRepository
            assignment_repo = ExamStudentAssignmentRepository()
            
            # If exam has student assignments, verify this student has access
            if assignment_repo.has_any_assignments(exam_id):
                if not assignment_repo.is_student_assigned(exam_id, student_id):
                    print(f"Student {student_id} does not have access to exam {exam_id}")
                    return None
            
            # Check if there's already an in-progress attempt
            existing_attempt = self.attempt_repository.get_in_progress_attempt(
                student_id, exam_id
            )
            if existing_attempt:
                print(f"Student {student_id} already has an in-progress attempt for exam {exam_id}")
                return existing_attempt
            
            # Create new attempt
            attempt = self.attempt_repository.create(
                student_id=student_id,
                exam_id=exam_id,
                status=AttemptStatus.IN_PROGRESS
            )
            return attempt
        except Exception as e:
            print(f"Error creating attempt: {e}")
            return None
    
    def get_attempt(self, attempt_id: int) -> Optional[Attempt]:
        """
        Retrieve an attempt by ID.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            Attempt instance if found, None otherwise
        """
        return self.attempt_repository.get_by_id(attempt_id)
    
    def get_attempt_with_answers(self, attempt_id: int) -> Optional[Attempt]:
        """
        Retrieve an attempt with its answers prefetched.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            Attempt instance with answers, None if not found
        """
        return self.attempt_repository.get_with_answers(attempt_id)
    
    def get_attempt_with_full_data(self, attempt_id: int) -> Optional[Attempt]:
        """
        Retrieve an attempt with answers and questions prefetched.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            Attempt instance with full data, None if not found
        """
        return self.attempt_repository.get_with_answers_and_questions(attempt_id)
    
    def get_student_attempts(self, student_id: int) -> List[Attempt]:
        """
        Retrieve all attempts by a student.
        
        Args:
            student_id: Primary key of the student
            
        Returns:
            List of Attempt instances
        """
        return list(self.attempt_repository.get_by_student(student_id))
    
    def get_exam_attempts(self, exam_id: int) -> List[Attempt]:
        """
        Retrieve all attempts for an exam.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            List of Attempt instances
        """
        return list(self.attempt_repository.get_by_exam(exam_id))
    
    def get_student_exam_attempts(self, student_id: int, exam_id: int) -> List[Attempt]:
        """
        Retrieve all attempts by a student for a specific exam.
        
        Args:
            student_id: Primary key of the student
            exam_id: Primary key of the exam
            
        Returns:
            List of Attempt instances
        """
        return list(self.attempt_repository.get_by_student_and_exam(student_id, exam_id))
    
    def get_in_progress_attempt(self, student_id: int, exam_id: int) -> Optional[Attempt]:
        """
        Retrieve an in-progress attempt for a student and exam.
        Used for session persistence and answer preservation.
        
        Args:
            student_id: Primary key of the student
            exam_id: Primary key of the exam
            
        Returns:
            Attempt instance if found, None otherwise
        """
        return self.attempt_repository.get_in_progress_attempt(student_id, exam_id)
    
    def submit_attempt(self, attempt_id: int, auto_submit: bool = False) -> Optional[Attempt]:
        """
        Submit an attempt, marking it as submitted.
        Sets submitted_at timestamp and updates status.
        Uses database transaction for atomicity.
        
        Args:
            attempt_id: Primary key of the attempt
            auto_submit: Whether this is an automatic submission due to violations
            
        Returns:
            Updated Attempt instance if found, None otherwise
        """
        try:
            with transaction.atomic():
                # Lock the attempt row to prevent concurrent modifications
                attempt = Attempt.objects.select_for_update().get(id=attempt_id)
                
                if attempt.status != AttemptStatus.IN_PROGRESS:
                    print(f"Attempt {attempt_id} is not in progress")
                    return attempt
                
                # Update attempt status and timestamp
                attempt.status = AttemptStatus.SUBMITTED
                attempt.submitted_at = timezone.now()
                
                # Handle auto-submission
                if auto_submit:
                    attempt.auto_submitted = True
                    # Flag the attempt if it's auto-submitted
                    self._flag_attempt_internal(attempt, "Auto-submitted after 4 tab switches")
                
                attempt.save(update_fields=['status', 'submitted_at', 'auto_submitted', 'is_flagged', 'flag_reason'])
                
                return attempt
        except Attempt.DoesNotExist:
            print(f"Attempt {attempt_id} not found")
            return None
        except Exception as e:
            print(f"Error submitting attempt: {e}")
            return None
    
    def update_attempt_score(self, attempt_id: int, total_score: float) -> Optional[Attempt]:
        """
        Update the total score of an attempt.
        
        Args:
            attempt_id: Primary key of the attempt
            total_score: New total score
            
        Returns:
            Updated Attempt instance if found, None otherwise
        """
        return self.attempt_repository.update_score(attempt_id, total_score)
    
    def mark_as_graded(self, attempt_id: int) -> Optional[Attempt]:
        """
        Mark an attempt as graded.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            Updated Attempt instance if found, None otherwise
        """
        return self.attempt_repository.update_status(attempt_id, AttemptStatus.GRADED)
    
    def calculate_total_score(self, attempt_id: int) -> float:
        """
        Calculate the total score for an attempt based on its answers.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            Total score as float
        """
        answers = self.answer_repository.get_by_attempt(attempt_id)
        total_score = sum(float(answer.points_earned) for answer in answers)
        return total_score
    
    def recalculate_and_update_score(self, attempt_id: int) -> Optional[Attempt]:
        """
        Recalculate the total score and update the attempt.
        Used after grading answers.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            Updated Attempt instance if found, None otherwise
        """
        try:
            total_score = self.calculate_total_score(attempt_id)
            return self.update_attempt_score(attempt_id, total_score)
        except Exception as e:
            print(f"Error recalculating score: {e}")
            return None
    
    def preserve_attempt_state(self, attempt_id: int) -> bool:
        """
        Preserve the current state of an attempt.
        This is called on session expiration or connection interruption.
        The answers are already saved individually, so this just ensures
        the attempt record is up to date.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            True if state preserved successfully, False otherwise
        """
        try:
            attempt = self.attempt_repository.get_by_id(attempt_id)
            if not attempt:
                return False
            
            # Ensure the attempt is still in progress
            if attempt.status == AttemptStatus.IN_PROGRESS:
                # The attempt state is preserved by virtue of being in the database
                # Individual answers are saved separately via AnswerService
                return True
            
            return False
        except Exception as e:
            print(f"Error preserving attempt state: {e}")
            return False
    
    def restore_attempt_state(self, student_id: int, exam_id: int) -> Optional[Attempt]:
        """
        Restore an in-progress attempt for a student.
        Used when a student reconnects after interruption.
        
        Args:
            student_id: Primary key of the student
            exam_id: Primary key of the exam
            
        Returns:
            Attempt instance with answers if found, None otherwise
        """
        try:
            attempt = self.get_in_progress_attempt(student_id, exam_id)
            if attempt:
                # Prefetch answers for restoration
                return self.get_attempt_with_answers(attempt.id)
            return None
        except Exception as e:
            print(f"Error restoring attempt state: {e}")
            return None
    
    def flag_attempt(self, attempt_id: int, reason: str) -> Optional[Attempt]:
        """
        Flag an attempt as potential cheating.
        
        Args:
            attempt_id: Primary key of the attempt
            reason: Reason for flagging the attempt
            
        Returns:
            Updated Attempt instance if found, None otherwise
        """
        try:
            with transaction.atomic():
                # Lock the attempt row to prevent concurrent modifications
                attempt = Attempt.objects.select_for_update().get(id=attempt_id)
                
                # Flag the attempt
                self._flag_attempt_internal(attempt, reason)
                attempt.save(update_fields=['is_flagged', 'flag_reason'])
                
                return attempt
        except Attempt.DoesNotExist:
            print(f"Attempt {attempt_id} not found")
            return None
        except Exception as e:
            print(f"Error flagging attempt: {e}")
            return None
    
    def _flag_attempt_internal(self, attempt: Attempt, reason: str) -> None:
        """
        Internal helper method to flag an attempt.
        Does not save the attempt - caller is responsible for saving.
        
        Args:
            attempt: Attempt instance to flag
            reason: Reason for flagging
        """
        attempt.is_flagged = True
        attempt.flag_reason = reason
    
    def is_flagged(self, attempt_id: int) -> bool:
        """
        Check if an attempt is flagged for potential cheating.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            True if attempt is flagged, False otherwise
        """
        try:
            attempt = self.attempt_repository.get_by_id(attempt_id)
            if attempt:
                return attempt.is_flagged
            return False
        except Exception as e:
            print(f"Error checking if attempt is flagged: {e}")
            return False
