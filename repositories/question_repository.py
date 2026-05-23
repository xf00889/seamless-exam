"""
Question repository for data access operations.
Implements the Repository pattern for Question model.
"""
from typing import Optional, List
from django.db.models import QuerySet
from exams.models import Question
from repositories.base_repository import BaseRepository


class QuestionRepository(BaseRepository):
    """
    Repository for Question model with specialized query methods.
    """
    
    def __init__(self):
        super().__init__(Question)
    
    def get_questions_by_exam(self, exam_id: int) -> QuerySet:
        """
        Retrieve all questions for a specific exam, ordered by order_index.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            QuerySet of Question instances for the exam
        """
        return self.filter(exam_id=exam_id).order_by('order_index', 'id')
    
    def get_questions_by_type(self, exam_id: int, question_type: str) -> QuerySet:
        """
        Retrieve questions of a specific type for an exam.
        
        Args:
            exam_id: Primary key of the exam
            question_type: Type of question (from QuestionType enum)
            
        Returns:
            QuerySet of Question instances matching the type
        """
        return self.filter(exam_id=exam_id, question_type=question_type)
    
    def get_next_order_index(self, exam_id: int) -> int:
        """
        Get the next order_index value for a new question in an exam.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            Next available order_index value
        """
        questions = self.filter(exam_id=exam_id)
        if questions.exists():
            max_order = questions.order_by('-order_index').first().order_index
            return max_order + 1
        return 0
    
    def reorder_questions(self, exam_id: int, question_ids: List[int]) -> bool:
        """
        Reorder questions in an exam based on provided list of question IDs.
        
        Args:
            exam_id: Primary key of the exam
            question_ids: List of question IDs in desired order
            
        Returns:
            True if reordering successful, False otherwise
        """
        try:
            for index, question_id in enumerate(question_ids):
                question = self.get_by_id(question_id)
                if question and question.exam_id == exam_id:
                    question.order_index = index
                    question.save()
            return True
        except Exception:
            return False
    
    def delete_questions_by_exam(self, exam_id: int) -> int:
        """
        Delete all questions for a specific exam.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            Number of questions deleted
        """
        questions = self.filter(exam_id=exam_id)
        count = questions.count()
        questions.delete()
        return count
