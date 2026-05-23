"""
Question service for business logic operations.
Handles question CRUD operations.
"""
from typing import Optional, Dict, Any, List
from exams.models import Question
from repositories.question_repository import QuestionRepository


class QuestionService:
    """
    Service class for question-related business logic.
    Handles question creation, updates, and deletion.
    """
    
    def __init__(self):
        self.question_repository = QuestionRepository()
    
    def create_question(self, question_data: Dict[str, Any]) -> Optional[Question]:
        """
        Create a new question.
        
        Args:
            question_data: Dictionary containing question fields
                - exam: Exam instance or exam_id
                - question_type: str (from QuestionType enum)
                - question_text: str
                - options: dict/list (optional, for MCQ)
                - correct_answer: dict/list/str
                - points: float (optional, default 1.0)
                - order_index: int (optional, auto-calculated if not provided)
                
        Returns:
            Created Question instance, None if creation fails
        """
        try:
            # Handle exam if it's an ID
            if 'exam' in question_data and isinstance(question_data['exam'], int):
                exam_id = question_data.pop('exam')
                question_data['exam_id'] = exam_id
            else:
                exam_id = question_data.get('exam').id if 'exam' in question_data else None
            
            # Auto-calculate order_index if not provided
            if 'order_index' not in question_data and exam_id:
                question_data['order_index'] = self.question_repository.get_next_order_index(exam_id)
            
            question = self.question_repository.create(**question_data)
            return question
        except Exception as e:
            print(f"Error creating question: {e}")
            return None
    
    def get_question(self, question_id: int) -> Optional[Question]:
        """
        Retrieve a question by ID.
        
        Args:
            question_id: Primary key of the question
            
        Returns:
            Question instance if found, None otherwise
        """
        return self.question_repository.get_by_id(question_id)
    
    def get_questions_by_exam(self, exam_id: int) -> List[Question]:
        """
        Retrieve all questions for a specific exam.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            List of Question instances ordered by order_index
        """
        return list(self.question_repository.get_questions_by_exam(exam_id))
    
    def get_questions_by_type(self, exam_id: int, question_type: str) -> List[Question]:
        """
        Retrieve questions of a specific type for an exam.
        
        Args:
            exam_id: Primary key of the exam
            question_type: Type of question (from QuestionType enum)
            
        Returns:
            List of Question instances
        """
        return list(self.question_repository.get_questions_by_type(exam_id, question_type))
    
    def update_question(self, question_id: int, question_data: Dict[str, Any]) -> Optional[Question]:
        """
        Update an existing question.
        
        Args:
            question_id: Primary key of the question
            question_data: Dictionary containing fields to update
            
        Returns:
            Updated Question instance if found, None otherwise
        """
        try:
            return self.question_repository.update(question_id, **question_data)
        except Exception as e:
            print(f"Error updating question: {e}")
            return None
    
    def delete_question(self, question_id: int) -> bool:
        """
        Delete a question.
        
        Args:
            question_id: Primary key of the question
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            return self.question_repository.delete(question_id)
        except Exception as e:
            print(f"Error deleting question: {e}")
            return False
    
    def reorder_questions(self, exam_id: int, question_ids: List[int]) -> bool:
        """
        Reorder questions in an exam.
        
        Args:
            exam_id: Primary key of the exam
            question_ids: List of question IDs in desired order
            
        Returns:
            True if reordering successful, False otherwise
        """
        return self.question_repository.reorder_questions(exam_id, question_ids)
