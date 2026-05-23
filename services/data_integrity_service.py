"""
Data Integrity Service for ensuring reliability and consistency.
Handles database transactions, concurrent operations, and connection recovery.
"""
import logging
from typing import Optional, Dict, Any, List, Callable
from django.db import transaction, connection
from django.db.models import F
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from attempts.models import Attempt, Answer, AttemptStatus
from repositories.attempt_repository import AttemptRepository
from repositories.answer_repository import AnswerRepository

logger = logging.getLogger(__name__)


class DataIntegrityService:
    """
    Service for ensuring data integrity and reliability.
    Implements transaction management, locking, and recovery mechanisms.
    """
    
    def __init__(self):
        """Initialize service with repositories."""
        self.attempt_repository = AttemptRepository()
        self.answer_repository = AnswerRepository()
    
    def execute_with_transaction(
        self,
        operation: Callable,
        *args,
        **kwargs
    ) -> tuple[bool, Any]:
        """
        Execute an operation within a database transaction.
        Ensures atomicity and automatic rollback on failure.
        
        Args:
            operation: Callable to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Tuple of (success: bool, result: Any)
        """
        try:
            with transaction.atomic():
                result = operation(*args, **kwargs)
                return True, result
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            return False, None
    
    def submit_exam_with_locking(
        self,
        attempt_id: int,
        answers_data: List[Dict[str, Any]]
    ) -> tuple[bool, Optional[Attempt]]:
        """
        Submit an exam with proper locking to handle concurrent submissions.
        Uses SELECT FOR UPDATE to prevent race conditions.
        
        Args:
            attempt_id: Primary key of the attempt
            answers_data: List of answer data to save
            
        Returns:
            Tuple of (success: bool, attempt: Optional[Attempt])
        """
        try:
            with transaction.atomic():
                # Lock the attempt row to prevent concurrent modifications
                attempt = Attempt.objects.select_for_update().get(id=attempt_id)
                
                # Check if already submitted (idempotency)
                if attempt.status != AttemptStatus.IN_PROGRESS:
                    logger.warning(
                        f"Attempt {attempt_id} already submitted with status {attempt.status}"
                    )
                    return True, attempt
                
                # Save all answers
                for answer_data in answers_data:
                    question_id = answer_data.get('question_id')
                    answer_text = answer_data.get('answer_text')
                    
                    if question_id and answer_text is not None:
                        # Ensure answer_text is in proper format
                        if not isinstance(answer_text, dict):
                            answer_text = {'value': answer_text}
                        
                        # Create or update answer with locking
                        Answer.objects.update_or_create(
                            attempt_id=attempt_id,
                            question_id=question_id,
                            defaults={'answer_text': answer_text}
                        )
                
                # Update attempt status
                attempt.status = AttemptStatus.SUBMITTED
                attempt.submitted_at = timezone.now()
                attempt.save(update_fields=['status', 'submitted_at'])
                
                logger.info(f"Exam submitted successfully: Attempt {attempt_id}")
                return True, attempt
                
        except ObjectDoesNotExist:
            logger.error(f"Attempt {attempt_id} not found")
            return False, None
        except Exception as e:
            logger.error(f"Error submitting exam with locking: {e}")
            return False, None
    
    def save_answer_with_locking(
        self,
        attempt_id: int,
        question_id: int,
        answer_text: Any
    ) -> tuple[bool, Optional[Answer]]:
        """
        Save an answer with proper locking to handle concurrent saves.
        Uses SELECT FOR UPDATE to prevent race conditions.
        
        Args:
            attempt_id: Primary key of the attempt
            question_id: Primary key of the question
            answer_text: Answer data to save
            
        Returns:
            Tuple of (success: bool, answer: Optional[Answer])
        """
        try:
            with transaction.atomic():
                # Lock the attempt to ensure it's still in progress
                attempt = Attempt.objects.select_for_update().get(id=attempt_id)
                
                if attempt.status != AttemptStatus.IN_PROGRESS:
                    logger.warning(
                        f"Cannot save answer - attempt {attempt_id} is not in progress"
                    )
                    return False, None
                
                # Ensure answer_text is in proper format
                if not isinstance(answer_text, dict):
                    answer_text = {'value': answer_text}
                
                # Create or update answer
                answer, created = Answer.objects.update_or_create(
                    attempt_id=attempt_id,
                    question_id=question_id,
                    defaults={'answer_text': answer_text}
                )
                
                action = "created" if created else "updated"
                logger.debug(
                    f"Answer {action} for attempt {attempt_id}, question {question_id}"
                )
                
                return True, answer
                
        except ObjectDoesNotExist:
            logger.error(f"Attempt {attempt_id} not found")
            return False, None
        except Exception as e:
            logger.error(f"Error saving answer with locking: {e}")
            return False, None
    
    def recover_interrupted_attempt(
        self,
        student_id: int,
        exam_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Recover an interrupted exam attempt for a student.
        Restores the attempt state and all saved answers.
        
        Args:
            student_id: Primary key of the student
            exam_id: Primary key of the exam
            
        Returns:
            Dictionary with attempt and answers data, None if not found
        """
        try:
            # Find in-progress attempt
            attempt = self.attempt_repository.get_in_progress_attempt(
                student_id, exam_id
            )
            
            if not attempt:
                logger.info(
                    f"No interrupted attempt found for student {student_id}, exam {exam_id}"
                )
                return None
            
            # Get all saved answers
            answers = self.answer_repository.get_by_attempt(attempt.id)
            
            # Build answer map for easy lookup
            answer_map = {}
            for answer in answers:
                answer_map[answer.question_id] = {
                    'answer_id': answer.id,
                    'answer_text': answer.answer_text,
                    'question_id': answer.question_id
                }
            
            logger.info(
                f"Recovered interrupted attempt {attempt.id} with {len(answers)} answers"
            )
            
            return {
                'attempt_id': attempt.id,
                'started_at': attempt.started_at,
                'answers': answer_map,
                'status': attempt.status
            }
            
        except Exception as e:
            logger.error(f"Error recovering interrupted attempt: {e}")
            return None
    
    def verify_data_persistence(self) -> Dict[str, Any]:
        """
        Verify that data persists correctly across server restarts.
        Checks database connectivity and data integrity.
        
        Returns:
            Dictionary with verification results
        """
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_connected = cursor.fetchone()[0] == 1
            
            # Count records to verify data persistence
            attempt_count = Attempt.objects.count()
            answer_count = Answer.objects.count()
            
            # Check for orphaned answers (answers without attempts)
            orphaned_answers = Answer.objects.filter(
                attempt__isnull=True
            ).count()
            
            # Check for in-progress attempts
            in_progress_count = Attempt.objects.filter(
                status=AttemptStatus.IN_PROGRESS
            ).count()
            
            logger.info("Data persistence verification completed successfully")
            
            return {
                'database_connected': db_connected,
                'total_attempts': attempt_count,
                'total_answers': answer_count,
                'orphaned_answers': orphaned_answers,
                'in_progress_attempts': in_progress_count,
                'data_integrity_ok': orphaned_answers == 0
            }
            
        except Exception as e:
            logger.error(f"Error verifying data persistence: {e}")
            return {
                'database_connected': False,
                'error': str(e)
            }
    
    def handle_concurrent_submissions(
        self,
        submissions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Handle multiple concurrent exam submissions safely.
        Processes each submission with proper locking.
        
        Args:
            submissions: List of submission data dicts with 'attempt_id' and 'answers_data'
            
        Returns:
            Dictionary with processing results
        """
        results = {
            'total': len(submissions),
            'successful': 0,
            'failed': 0,
            'already_submitted': 0,
            'details': []
        }
        
        for submission in submissions:
            attempt_id = submission.get('attempt_id')
            answers_data = submission.get('answers_data', [])
            
            if not attempt_id:
                results['failed'] += 1
                results['details'].append({
                    'attempt_id': None,
                    'status': 'failed',
                    'reason': 'Missing attempt_id'
                })
                continue
            
            success, attempt = self.submit_exam_with_locking(attempt_id, answers_data)
            
            if success:
                if attempt and attempt.status == AttemptStatus.SUBMITTED:
                    results['successful'] += 1
                    results['details'].append({
                        'attempt_id': attempt_id,
                        'status': 'success'
                    })
                else:
                    results['already_submitted'] += 1
                    results['details'].append({
                        'attempt_id': attempt_id,
                        'status': 'already_submitted'
                    })
            else:
                results['failed'] += 1
                results['details'].append({
                    'attempt_id': attempt_id,
                    'status': 'failed',
                    'reason': 'Submission error'
                })
        
        logger.info(
            f"Concurrent submissions processed: "
            f"{results['successful']} successful, "
            f"{results['failed']} failed, "
            f"{results['already_submitted']} already submitted"
        )
        
        return results
    
    def cleanup_orphaned_data(self) -> Dict[str, int]:
        """
        Clean up orphaned data (answers without attempts, etc.).
        Should be run periodically for maintenance.
        
        Returns:
            Dictionary with cleanup counts
        """
        try:
            with transaction.atomic():
                # Find and delete orphaned answers
                orphaned_answers = Answer.objects.filter(attempt__isnull=True)
                orphaned_count = orphaned_answers.count()
                orphaned_answers.delete()
                
                logger.info(f"Cleaned up {orphaned_count} orphaned answers")
                
                return {
                    'orphaned_answers_deleted': orphaned_count
                }
                
        except Exception as e:
            logger.error(f"Error cleaning up orphaned data: {e}")
            return {
                'orphaned_answers_deleted': 0,
                'error': str(e)
            }
    
    def ensure_answer_preservation(
        self,
        attempt_id: int
    ) -> tuple[bool, int]:
        """
        Ensure all answers for an attempt are properly preserved.
        Verifies data integrity and returns count of preserved answers.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            Tuple of (success: bool, answer_count: int)
        """
        try:
            # Verify attempt exists
            attempt = self.attempt_repository.get_by_id(attempt_id)
            if not attempt:
                logger.error(f"Attempt {attempt_id} not found")
                return False, 0
            
            # Count preserved answers
            answers = self.answer_repository.get_by_attempt(attempt_id)
            answer_count = len(answers)
            
            # Verify each answer has valid data
            for answer in answers:
                if not answer.answer_text:
                    logger.warning(
                        f"Answer {answer.id} has empty answer_text"
                    )
            
            logger.info(
                f"Verified {answer_count} answers preserved for attempt {attempt_id}"
            )
            
            return True, answer_count
            
        except Exception as e:
            logger.error(f"Error ensuring answer preservation: {e}")
            return False, 0
