"""
Grading service orchestrator.
Coordinates auto-grading and manual grading, handles score recalculation.
"""
from typing import Optional, Dict, Any, List
from decimal import Decimal
import logging
from django.db import transaction
from exams.models import QuestionType
from attempts.models import Attempt, AttemptStatus
from repositories.attempt_repository import AttemptRepository
from repositories.answer_repository import AnswerRepository
from services.auto_grader_service import AutoGraderService
from services.manual_grader_service import ManualGraderService

logger = logging.getLogger(__name__)


class GradingService:
    """
    Orchestrator service for grading operations.
    Coordinates auto-grading and manual grading, manages score recalculation.
    """
    
    def __init__(self):
        """Initialize grading service with auto and manual graders."""
        self.attempt_repository = AttemptRepository()
        self.answer_repository = AnswerRepository()
        self.auto_grader = AutoGraderService()
        self.manual_grader = ManualGraderService()
    
    def grade_attempt(self, attempt_id: int) -> bool:
        """
        Grade an attempt by auto-grading objective questions.
        Essay questions are left for manual grading.
        
        Args:
            attempt_id: Primary key of the attempt to grade
            
        Returns:
            True if grading successful, False otherwise
        """
        try:
            # Use auto-grader to grade objective questions
            result = self.auto_grader.grade_attempt(attempt_id)
            
            if result:
                logger.info(f"Attempt {attempt_id} auto-graded successfully")
            else:
                logger.error(f"Failed to auto-grade attempt {attempt_id}")
            
            return result
        except Exception as e:
            logger.error(f"Error grading attempt {attempt_id}: {e}")
            return False
    
    def grade_essay(
        self,
        answer_id: int,
        points_earned: float,
        teacher_feedback: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Grade an essay question and recalculate attempt score.
        
        Args:
            answer_id: Primary key of the answer to grade
            points_earned: Points to award
            teacher_feedback: Optional feedback text
            
        Returns:
            Dictionary with updated answer and attempt, None if failed
        """
        try:
            with transaction.atomic():
                # Grade the essay
                answer = self.manual_grader.grade_essay(
                    answer_id=answer_id,
                    points_earned=points_earned,
                    teacher_feedback=teacher_feedback
                )
                
                if not answer:
                    logger.error(f"Failed to grade essay answer {answer_id}")
                    return None
                
                # Recalculate total score for the attempt
                attempt = self.recalculate_attempt_score(answer.attempt_id)
                
                if not attempt:
                    logger.error(f"Failed to recalculate score for attempt {answer.attempt_id}")
                    return None
                
                logger.info(
                    f"Essay graded and score recalculated: "
                    f"Answer {answer_id}, Attempt {answer.attempt_id}"
                )
                
                return {
                    'answer': answer,
                    'attempt': attempt
                }
        except Exception as e:
            logger.error(f"Error grading essay and recalculating score: {e}")
            return None
    
    def modify_essay_score(
        self,
        answer_id: int,
        new_points_earned: float,
        new_feedback: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Modify an essay score and recalculate attempt score.
        
        Args:
            answer_id: Primary key of the answer to modify
            new_points_earned: New points to award
            new_feedback: Optional new feedback text
            
        Returns:
            Dictionary with updated answer and attempt, None if failed
        """
        try:
            with transaction.atomic():
                # Modify the essay score
                answer = self.manual_grader.modify_essay_score(
                    answer_id=answer_id,
                    new_points_earned=new_points_earned,
                    new_feedback=new_feedback
                )
                
                if not answer:
                    logger.error(f"Failed to modify essay score for answer {answer_id}")
                    return None
                
                # Recalculate total score for the attempt
                attempt = self.recalculate_attempt_score(answer.attempt_id)
                
                if not attempt:
                    logger.error(f"Failed to recalculate score for attempt {answer.attempt_id}")
                    return None
                
                logger.info(
                    f"Essay score modified and recalculated: "
                    f"Answer {answer_id}, Attempt {answer.attempt_id}"
                )
                
                return {
                    'answer': answer,
                    'attempt': attempt
                }
        except Exception as e:
            logger.error(f"Error modifying essay score and recalculating: {e}")
            return None
    
    def recalculate_attempt_score(self, attempt_id: int) -> Optional[Attempt]:
        """
        Recalculate the total score for an attempt after essay grading.
        Updates the attempt status to GRADED if all questions are graded.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            Updated Attempt instance if successful, None otherwise
        """
        try:
            # Calculate total score from all answers
            total_score = self.auto_grader.calculate_total_score(attempt_id)
            
            # Update attempt with new total score
            attempt = self.attempt_repository.update_score(attempt_id, float(total_score))
            
            if not attempt:
                logger.error(f"Failed to update score for attempt {attempt_id}")
                return None
            
            # Check if all questions are now graded
            attempt_with_answers = self.attempt_repository.get_with_answers_and_questions(attempt_id)
            
            if attempt_with_answers:
                all_graded = all(
                    answer.is_correct is not None
                    for answer in attempt_with_answers.answers.all()
                )
                
                # Update status to GRADED if all questions are graded
                if all_graded and attempt.status != AttemptStatus.GRADED:
                    attempt = self.attempt_repository.update_status(
                        attempt_id,
                        AttemptStatus.GRADED
                    )
                    logger.info(f"Attempt {attempt_id} marked as fully graded")
            
            logger.info(f"Recalculated score for attempt {attempt_id}: {total_score}")
            
            return attempt
        except Exception as e:
            logger.error(f"Error recalculating score for attempt {attempt_id}: {e}")
            return None
    
    def bulk_grade_essays(
        self,
        attempt_id: int,
        grading_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Grade multiple essays for an attempt and recalculate score once.
        More efficient than grading individually.
        
        Args:
            attempt_id: Primary key of the attempt
            grading_data: List of dicts with 'answer_id', 'points_earned', 'teacher_feedback'
            
        Returns:
            Dictionary with grading results and updated attempt
        """
        try:
            with transaction.atomic():
                # Grade all essays
                result = self.manual_grader.bulk_grade_essays(grading_data)
                
                # Recalculate score once after all essays are graded
                attempt = self.recalculate_attempt_score(attempt_id)
                
                result['attempt'] = attempt
                
                logger.info(
                    f"Bulk graded {result['success_count']} essays for attempt {attempt_id}"
                )
                
                return result
        except Exception as e:
            logger.error(f"Error in bulk grading for attempt {attempt_id}: {e}")
            return {
                'success_count': 0,
                'failed_ids': [d.get('answer_id') for d in grading_data],
                'total': len(grading_data),
                'attempt': None
            }
    
    def get_grading_status(self, attempt_id: int) -> Dict[str, Any]:
        """
        Get the grading status for an attempt.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            Dictionary with grading status information
        """
        try:
            attempt = self.attempt_repository.get_with_answers_and_questions(attempt_id)
            
            if not attempt:
                logger.error(f"Attempt {attempt_id} not found")
                return {
                    'found': False
                }
            
            # Count graded and ungraded questions by type
            total_questions = 0
            graded_questions = 0
            ungraded_essays = 0
            graded_essays = 0
            objective_questions = 0
            
            for answer in attempt.answers.all():
                total_questions += 1
                
                if answer.question.question_type == QuestionType.ESSAY:
                    if answer.is_correct is not None:
                        graded_essays += 1
                        graded_questions += 1
                    else:
                        ungraded_essays += 1
                else:
                    objective_questions += 1
                    if answer.is_correct is not None:
                        graded_questions += 1
            
            all_graded = graded_questions == total_questions
            
            return {
                'found': True,
                'attempt_id': attempt_id,
                'status': attempt.status,
                'total_questions': total_questions,
                'graded_questions': graded_questions,
                'ungraded_questions': total_questions - graded_questions,
                'objective_questions': objective_questions,
                'graded_essays': graded_essays,
                'ungraded_essays': ungraded_essays,
                'all_graded': all_graded,
                'total_score': float(attempt.total_score)
            }
        except Exception as e:
            logger.error(f"Error getting grading status for attempt {attempt_id}: {e}")
            return {
                'found': False,
                'error': str(e)
            }
    
    def get_ungraded_essays_for_attempt(self, attempt_id: int) -> List[Dict[str, Any]]:
        """
        Get all ungraded essays for an attempt with question details.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            List of dictionaries with essay answer and question information
        """
        try:
            ungraded_essays = self.manual_grader.get_ungraded_essays(attempt_id)
            
            result = []
            for answer in ungraded_essays:
                result.append({
                    'answer_id': answer.id,
                    'question_id': answer.question.id,
                    'question_text': answer.question.question_text,
                    'max_points': float(answer.question.points),
                    'student_answer': answer.answer_text,
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting ungraded essays for attempt {attempt_id}: {e}")
            return []
    
    def regrade_attempt(self, attempt_id: int) -> bool:
        """
        Regrade an entire attempt (useful after modifying essay scores).
        Recalculates total score and updates status.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            True if regrading successful, False otherwise
        """
        try:
            # Use auto-grader's regrade method which recalculates total score
            result = self.auto_grader.regrade_attempt(attempt_id)
            
            if result:
                logger.info(f"Attempt {attempt_id} regraded successfully")
            else:
                logger.error(f"Failed to regrade attempt {attempt_id}")
            
            return result
        except Exception as e:
            logger.error(f"Error regrading attempt {attempt_id}: {e}")
            return False
