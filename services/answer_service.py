"""
Answer service for business logic operations.
Handles saving and retrieving student answers with auto-save functionality.
"""
from typing import Optional, Dict, Any, List
from django.db import transaction
from attempts.models import Answer
from repositories.answer_repository import AnswerRepository
from repositories.attempt_repository import AttemptRepository
from repositories.question_repository import QuestionRepository


class AnswerService:
    """
    Service class for answer-related business logic.
    Handles saving, retrieving, and updating student answers.
    """
    
    def __init__(self):
        self.answer_repository = AnswerRepository()
        self.attempt_repository = AttemptRepository()
        self.question_repository = QuestionRepository()
    
    def save_answer(self, attempt_id: int, question_id: int, answer_text: Any) -> Optional[Answer]:
        """
        Save or update a student's answer to a question.
        Implements auto-save functionality with answer preservation.
        Uses database transaction and locking for concurrent safety.
        
        Args:
            attempt_id: Primary key of the attempt
            question_id: Primary key of the question
            answer_text: Answer data (will be stored as JSON)
            
        Returns:
            Created or updated Answer instance, None if save fails
        """
        try:
            with transaction.atomic():
                # Lock the attempt to ensure it's still in progress
                from attempts.models import Attempt
                attempt = Attempt.objects.select_for_update().get(id=attempt_id)
                
                if attempt.status != 'in_progress':
                    print(f"Attempt {attempt_id} is not in progress")
                    return None
                
                # Verify question exists
                question = self.question_repository.get_by_id(question_id)
                if not question:
                    print(f"Question {question_id} not found")
                    return None
                
                # Ensure answer_text is in proper format for JSON storage
                if not isinstance(answer_text, dict):
                    # Wrap simple values in a dict
                    answer_text = {'value': answer_text}
                
                # Create or update answer
                answer = self.answer_repository.create_or_update_answer(
                    attempt_id=attempt_id,
                    question_id=question_id,
                    answer_text=answer_text
                )
                
                return answer
        except Attempt.DoesNotExist:
            print(f"Attempt {attempt_id} not found")
            return None
        except Exception as e:
            print(f"Error saving answer: {e}")
            return None
    
    def save_multiple_answers(self, attempt_id: int, answers_data: List[Dict[str, Any]]) -> bool:
        """
        Save multiple answers at once.
        Used for batch saving or final submission.
        
        Args:
            attempt_id: Primary key of the attempt
            answers_data: List of dicts with 'question_id' and 'answer_text'
            
        Returns:
            True if all answers saved successfully, False otherwise
        """
        try:
            with transaction.atomic():
                for answer_data in answers_data:
                    question_id = answer_data.get('question_id')
                    answer_text = answer_data.get('answer_text')
                    
                    if question_id and answer_text is not None:
                        result = self.save_answer(attempt_id, question_id, answer_text)
                        if not result:
                            return False
                
                return True
        except Exception as e:
            print(f"Error saving multiple answers: {e}")
            return False
    
    def get_answer(self, answer_id: int) -> Optional[Answer]:
        """
        Retrieve an answer by ID.
        
        Args:
            answer_id: Primary key of the answer
            
        Returns:
            Answer instance if found, None otherwise
        """
        return self.answer_repository.get_by_id(answer_id)
    
    def get_answer_with_question(self, answer_id: int) -> Optional[Answer]:
        """
        Retrieve an answer with its question prefetched.
        
        Args:
            answer_id: Primary key of the answer
            
        Returns:
            Answer instance with question, None if not found
        """
        return self.answer_repository.get_with_question(answer_id)
    
    def get_attempt_answers(self, attempt_id: int) -> List[Answer]:
        """
        Retrieve all answers for an attempt.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            List of Answer instances
        """
        return list(self.answer_repository.get_by_attempt(attempt_id))
    
    def get_question_answers(self, question_id: int) -> List[Answer]:
        """
        Retrieve all answers for a specific question.
        Useful for analytics and grading.
        
        Args:
            question_id: Primary key of the question
            
        Returns:
            List of Answer instances
        """
        return list(self.answer_repository.get_by_question(question_id))
    
    def get_specific_answer(self, attempt_id: int, question_id: int) -> Optional[Answer]:
        """
        Retrieve a specific answer for an attempt and question.
        
        Args:
            attempt_id: Primary key of the attempt
            question_id: Primary key of the question
            
        Returns:
            Answer instance if found, None otherwise
        """
        return self.answer_repository.get_by_attempt_and_question(attempt_id, question_id)
    
    def update_answer(self, answer_id: int, answer_text: Any) -> Optional[Answer]:
        """
        Update an existing answer's text.
        Only allowed for in-progress attempts.
        
        Args:
            answer_id: Primary key of the answer
            answer_text: New answer data
            
        Returns:
            Updated Answer instance if found, None otherwise
        """
        try:
            answer = self.answer_repository.get_by_id(answer_id)
            if not answer:
                print(f"Answer {answer_id} not found")
                return None
            
            # Check if attempt is still in progress
            attempt = self.attempt_repository.get_by_id(answer.attempt_id)
            if not attempt or attempt.status != 'in_progress':
                print(f"Cannot update answer - attempt is not in progress")
                return None
            
            # Ensure answer_text is in proper format
            if not isinstance(answer_text, dict):
                answer_text = {'value': answer_text}
            
            return self.answer_repository.update(answer_id, answer_text=answer_text)
        except Exception as e:
            print(f"Error updating answer: {e}")
            return None
    
    def delete_answer(self, answer_id: int) -> bool:
        """
        Delete an answer.
        Only allowed for in-progress attempts.
        
        Args:
            answer_id: Primary key of the answer
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            answer = self.answer_repository.get_by_id(answer_id)
            if not answer:
                return False
            
            # Check if attempt is still in progress
            attempt = self.attempt_repository.get_by_id(answer.attempt_id)
            if not attempt or attempt.status != 'in_progress':
                print(f"Cannot delete answer - attempt is not in progress")
                return False
            
            return self.answer_repository.delete(answer_id)
        except Exception as e:
            print(f"Error deleting answer: {e}")
            return False
    
    def get_ungraded_answers(self, attempt_id: int) -> List[Answer]:
        """
        Retrieve all ungraded answers for an attempt.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            List of ungraded Answer instances
        """
        return list(self.answer_repository.get_ungraded_answers(attempt_id))
    
    def get_graded_answers(self, attempt_id: int) -> List[Answer]:
        """
        Retrieve all graded answers for an attempt.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            List of graded Answer instances
        """
        return list(self.answer_repository.get_graded_answers(attempt_id))
    
    def update_grading(self, answer_id: int, is_correct: bool, points_earned: float,
                       teacher_feedback: str = None) -> Optional[Answer]:
        """
        Update the grading information for an answer.
        Used by grading services.
        
        Args:
            answer_id: Primary key of the answer
            is_correct: Whether the answer is correct
            points_earned: Points earned for this answer
            teacher_feedback: Optional feedback from teacher
            
        Returns:
            Updated Answer instance if found, None otherwise
        """
        return self.answer_repository.update_grading(
            answer_id, is_correct, points_earned, teacher_feedback
        )
    
    def preserve_answers_on_interruption(self, attempt_id: int) -> bool:
        """
        Ensure all answers for an attempt are preserved.
        Called on connection interruption or session expiration.
        Since answers are saved individually as they're entered,
        this mainly serves as a verification step.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            True if answers are preserved, False otherwise
        """
        try:
            # Verify attempt exists
            attempt = self.attempt_repository.get_by_id(attempt_id)
            if not attempt:
                return False
            
            # Answers are already persisted in the database
            # This method serves as a checkpoint to ensure data integrity
            answers = self.get_attempt_answers(attempt_id)
            
            # Return True if we can retrieve the answers
            return True
        except Exception as e:
            print(f"Error preserving answers: {e}")
            return False
    
    def restore_answers(self, attempt_id: int) -> List[Answer]:
        """
        Restore all answers for an attempt.
        Used when a student reconnects after interruption.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            List of Answer instances
        """
        return self.get_attempt_answers(attempt_id)
