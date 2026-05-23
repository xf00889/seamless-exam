"""
Answer repository for data access operations.
Implements the Repository pattern for Answer model.
"""
from typing import Optional, List
from django.db.models import QuerySet
from attempts.models import Answer
from repositories.base_repository import BaseRepository


class AnswerRepository(BaseRepository):
    """
    Repository for Answer model with specialized query methods.
    """
    
    def __init__(self):
        super().__init__(Answer)
    
    def get_by_attempt(self, attempt_id: int) -> QuerySet:
        """
        Retrieve all answers for a specific attempt.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            QuerySet of Answer instances for the attempt
        """
        return self.filter(attempt_id=attempt_id)
    
    def get_by_question(self, question_id: int) -> QuerySet:
        """
        Retrieve all answers for a specific question.
        
        Args:
            question_id: Primary key of the question
            
        Returns:
            QuerySet of Answer instances for the question
        """
        return self.filter(question_id=question_id)
    
    def get_by_attempt_and_question(self, attempt_id: int, question_id: int) -> Optional[Answer]:
        """
        Retrieve a specific answer for an attempt and question.
        
        Args:
            attempt_id: Primary key of the attempt
            question_id: Primary key of the question
            
        Returns:
            Answer instance if found, None otherwise
        """
        try:
            return self.model.objects.get(
                attempt_id=attempt_id,
                question_id=question_id
            )
        except self.model.DoesNotExist:
            return None
    
    def create_or_update_answer(self, attempt_id: int, question_id: int, answer_text: dict) -> Answer:
        """
        Create a new answer or update existing one.
        
        Args:
            attempt_id: Primary key of the attempt
            question_id: Primary key of the question
            answer_text: Answer data in JSON format
            
        Returns:
            Created or updated Answer instance
        """
        answer = self.get_by_attempt_and_question(attempt_id, question_id)
        if answer:
            answer.answer_text = answer_text
            answer.save()
        else:
            answer = self.create(
                attempt_id=attempt_id,
                question_id=question_id,
                answer_text=answer_text
            )
        return answer
    
    def get_ungraded_answers(self, attempt_id: int) -> QuerySet:
        """
        Retrieve all ungraded answers for an attempt.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            QuerySet of ungraded Answer instances
        """
        return self.filter(attempt_id=attempt_id, is_correct__isnull=True)
    
    def get_graded_answers(self, attempt_id: int) -> QuerySet:
        """
        Retrieve all graded answers for an attempt.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            QuerySet of graded Answer instances
        """
        return self.filter(attempt_id=attempt_id, is_correct__isnull=False)
    
    def update_grading(self, answer_id: int, is_correct: bool, points_earned: float, 
                       teacher_feedback: str = None) -> Optional[Answer]:
        """
        Update the grading information for an answer.
        
        Args:
            answer_id: Primary key of the answer
            is_correct: Whether the answer is correct
            points_earned: Points earned for this answer
            teacher_feedback: Optional feedback from teacher
            
        Returns:
            Updated Answer instance if found, None otherwise
        """
        from django.utils import timezone
        update_data = {
            'is_correct': is_correct,
            'points_earned': points_earned,
            'graded_at': timezone.now()
        }
        if teacher_feedback is not None:
            update_data['teacher_feedback'] = teacher_feedback
        
        return self.update(answer_id, **update_data)
    
    def get_with_question(self, answer_id: int) -> Optional[Answer]:
        """
        Retrieve an answer with its question prefetched.
        
        Args:
            answer_id: Primary key of the answer
            
        Returns:
            Answer instance with question prefetched, None if not found
        """
        try:
            return self.model.objects.select_related('question').get(pk=answer_id)
        except self.model.DoesNotExist:
            return None
