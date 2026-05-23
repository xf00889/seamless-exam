"""
Manual grading service for essay questions.
Implements teacher-driven grading with feedback and score assignment.
"""
from typing import Optional, Dict, Any, List
from decimal import Decimal
import logging
from django.utils import timezone
from exams.models import QuestionType, Question
from attempts.models import Answer, Attempt
from repositories.answer_repository import AnswerRepository
from repositories.attempt_repository import AttemptRepository

logger = logging.getLogger(__name__)


class ManualGraderService:
    """
    Service class for manual grading of essay questions.
    Handles teacher score assignment, feedback, and score modification.
    """
    
    def __init__(self):
        """Initialize manual grader service."""
        self.answer_repository = AnswerRepository()
        self.attempt_repository = AttemptRepository()
    
    def grade_essay(
        self,
        answer_id: int,
        points_earned: float,
        teacher_feedback: Optional[str] = None
    ) -> Optional[Answer]:
        """
        Grade an essay question with teacher-assigned score and feedback.
        
        Args:
            answer_id: Primary key of the answer to grade
            points_earned: Points to award (0 to question.points)
            teacher_feedback: Optional feedback text from teacher
            
        Returns:
            Updated Answer instance if successful, None otherwise
        """
        try:
            # Get answer with question
            answer = self.answer_repository.get_with_question(answer_id)
            
            if not answer:
                logger.error(f"Answer {answer_id} not found")
                return None
            
            # Verify this is an essay question
            if answer.question.question_type != QuestionType.ESSAY:
                logger.error(f"Answer {answer_id} is not an essay question")
                return None
            
            # Validate points_earned is within valid range
            max_points = float(answer.question.points)
            if points_earned < 0 or points_earned > max_points:
                logger.error(
                    f"Invalid points_earned {points_earned} for answer {answer_id}. "
                    f"Must be between 0 and {max_points}"
                )
                return None
            
            # Update answer with grading information
            # Essay questions are marked as correct if they earn any points
            is_correct = points_earned > 0
            
            updated_answer = self.answer_repository.update_grading(
                answer_id=answer_id,
                is_correct=is_correct,
                points_earned=points_earned,
                teacher_feedback=teacher_feedback
            )
            
            logger.info(
                f"Essay graded: Answer {answer_id}, Points: {points_earned}, "
                f"Feedback: {bool(teacher_feedback)}"
            )
            
            return updated_answer
        except Exception as e:
            logger.error(f"Error grading essay answer {answer_id}: {e}")
            return None
    
    def modify_essay_score(
        self,
        answer_id: int,
        new_points_earned: float,
        new_feedback: Optional[str] = None
    ) -> Optional[Answer]:
        """
        Modify the score and feedback for a previously graded essay.
        
        Args:
            answer_id: Primary key of the answer to modify
            new_points_earned: New points to award
            new_feedback: Optional new feedback text (None keeps existing)
            
        Returns:
            Updated Answer instance if successful, None otherwise
        """
        try:
            # Get answer with question
            answer = self.answer_repository.get_with_question(answer_id)
            
            if not answer:
                logger.error(f"Answer {answer_id} not found")
                return None
            
            # Verify this is an essay question
            if answer.question.question_type != QuestionType.ESSAY:
                logger.error(f"Answer {answer_id} is not an essay question")
                return None
            
            # Validate new points
            max_points = float(answer.question.points)
            if new_points_earned < 0 or new_points_earned > max_points:
                logger.error(
                    f"Invalid new_points_earned {new_points_earned} for answer {answer_id}. "
                    f"Must be between 0 and {max_points}"
                )
                return None
            
            # Update answer with new grading information
            is_correct = new_points_earned > 0
            
            # If new_feedback is None, keep existing feedback
            feedback_to_save = new_feedback if new_feedback is not None else answer.teacher_feedback
            
            updated_answer = self.answer_repository.update_grading(
                answer_id=answer_id,
                is_correct=is_correct,
                points_earned=new_points_earned,
                teacher_feedback=feedback_to_save
            )
            
            logger.info(
                f"Essay score modified: Answer {answer_id}, "
                f"New Points: {new_points_earned}"
            )
            
            return updated_answer
        except Exception as e:
            logger.error(f"Error modifying essay score for answer {answer_id}: {e}")
            return None
    
    def get_ungraded_essays(self, attempt_id: int) -> List[Answer]:
        """
        Get all ungraded essay questions for an attempt.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            List of ungraded essay Answer instances
        """
        try:
            # Get all ungraded answers
            ungraded_answers = self.answer_repository.get_ungraded_answers(attempt_id)
            
            # Filter for essay questions only
            essay_answers = [
                answer for answer in ungraded_answers
                if answer.question.question_type == QuestionType.ESSAY
            ]
            
            return essay_answers
        except Exception as e:
            logger.error(f"Error getting ungraded essays for attempt {attempt_id}: {e}")
            return []
    
    def get_graded_essays(self, attempt_id: int) -> List[Answer]:
        """
        Get all graded essay questions for an attempt.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            List of graded essay Answer instances
        """
        try:
            # Get all graded answers
            graded_answers = self.answer_repository.get_graded_answers(attempt_id)
            
            # Filter for essay questions only
            essay_answers = [
                answer for answer in graded_answers
                if answer.question.question_type == QuestionType.ESSAY
            ]
            
            return essay_answers
        except Exception as e:
            logger.error(f"Error getting graded essays for attempt {attempt_id}: {e}")
            return []
    
    def bulk_grade_essays(
        self,
        grading_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Grade multiple essay questions at once.
        
        Args:
            grading_data: List of dicts with 'answer_id', 'points_earned', 'teacher_feedback'
            
        Returns:
            Dictionary with success count and failed answer IDs
        """
        try:
            success_count = 0
            failed_ids = []
            
            for data in grading_data:
                answer_id = data.get('answer_id')
                points_earned = data.get('points_earned')
                teacher_feedback = data.get('teacher_feedback')
                
                if answer_id is None or points_earned is None:
                    logger.warning(f"Invalid grading data: {data}")
                    failed_ids.append(answer_id)
                    continue
                
                result = self.grade_essay(
                    answer_id=answer_id,
                    points_earned=points_earned,
                    teacher_feedback=teacher_feedback
                )
                
                if result:
                    success_count += 1
                else:
                    failed_ids.append(answer_id)
            
            logger.info(
                f"Bulk grading completed: {success_count} successful, "
                f"{len(failed_ids)} failed"
            )
            
            return {
                'success_count': success_count,
                'failed_ids': failed_ids,
                'total': len(grading_data)
            }
        except Exception as e:
            logger.error(f"Error in bulk grading: {e}")
            return {
                'success_count': 0,
                'failed_ids': [d.get('answer_id') for d in grading_data],
                'total': len(grading_data)
            }
    
    def has_ungraded_essays(self, attempt_id: int) -> bool:
        """
        Check if an attempt has any ungraded essay questions.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            True if there are ungraded essays, False otherwise
        """
        try:
            ungraded_essays = self.get_ungraded_essays(attempt_id)
            return len(ungraded_essays) > 0
        except Exception as e:
            logger.error(f"Error checking for ungraded essays: {e}")
            return False
