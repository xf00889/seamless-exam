"""
Exam service for business logic operations.
Handles exam CRUD operations and JSON serialization.
"""
from typing import Optional, Dict, Any, List
from django.db import transaction
from exams.models import Exam
from repositories.exam_repository import ExamRepository
from repositories.question_repository import QuestionRepository
import json


class ExamService:
    """
    Service class for exam-related business logic.
    Handles exam creation, updates, and JSON serialization.
    """
    
    def __init__(self):
        self.exam_repository = ExamRepository()
        self.question_repository = QuestionRepository()
    
    def create_exam(self, exam_data: Dict[str, Any]) -> Optional[Exam]:
        """
        Create a new exam.
        
        Args:
            exam_data: Dictionary containing exam fields
                - title: str
                - description: str (optional)
                - duration_minutes: int
                - created_by: Teacher instance or teacher_id
                
        Returns:
            Created Exam instance, None if creation fails
        """
        try:
            # Handle created_by if it's an ID
            if 'created_by' in exam_data and isinstance(exam_data['created_by'], int):
                exam_data['created_by_id'] = exam_data.pop('created_by')
            
            exam = self.exam_repository.create(**exam_data)
            return exam
        except Exception as e:
            print(f"Error creating exam: {e}")
            return None
    
    def get_exam(self, exam_id: int) -> Optional[Exam]:
        """
        Retrieve an exam by ID.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            Exam instance if found, None otherwise
        """
        return self.exam_repository.get_by_id(exam_id)
    
    def get_exam_with_questions(self, exam_id: int) -> Optional[Exam]:
        """
        Retrieve an exam with its questions prefetched.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            Exam instance with questions, None if not found
        """
        return self.exam_repository.get_with_questions(exam_id)
    
    def get_all_exams(self) -> List[Exam]:
        """
        Retrieve all exams.
        
        Returns:
            List of all Exam instances
        """
        return list(self.exam_repository.get_all())
    
    def get_exams_by_teacher(self, teacher_id: int) -> List[Exam]:
        """
        Retrieve all exams created by a specific teacher.
        
        Args:
            teacher_id: Primary key of the teacher
            
        Returns:
            List of Exam instances
        """
        return list(self.exam_repository.get_exams_by_teacher(teacher_id))
    
    def get_active_exams(self) -> List[Exam]:
        """
        Retrieve all active exams with optimized queries.
        Prefetches questions to avoid N+1 queries.
        
        Returns:
            List of active Exam instances with questions prefetched
            
        Requirements: 9.5
        """
        return list(self.exam_repository.get_active_exams())
    
    def update_exam(self, exam_id: int, exam_data: Dict[str, Any]) -> Optional[Exam]:
        """
        Update an existing exam.
        
        Args:
            exam_id: Primary key of the exam
            exam_data: Dictionary containing fields to update
            
        Returns:
            Updated Exam instance if found, None otherwise
        """
        try:
            return self.exam_repository.update(exam_id, **exam_data)
        except Exception as e:
            print(f"Error updating exam: {e}")
            return None
    
    def delete_exam(self, exam_id: int) -> bool:
        """
        Delete an exam and all its questions.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            with transaction.atomic():
                # Questions will be deleted automatically due to CASCADE
                return self.exam_repository.delete(exam_id)
        except Exception as e:
            print(f"Error deleting exam: {e}")
            return False
    
    def serialize_exam(self, exam_id: int) -> Optional[Dict[str, Any]]:
        """
        Serialize an exam to JSON format.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            Dictionary representation of the exam with questions
        """
        exam = self.get_exam_with_questions(exam_id)
        if not exam:
            return None
        
        questions_data = []
        for question in exam.questions.all():
            questions_data.append({
                'id': question.id,
                'type': question.question_type,
                'text': question.question_text,
                'options': question.options,
                'correct_answer': question.correct_answer,
                'points': float(question.points),
                'order_index': question.order_index
            })
        
        return {
            'exam_id': exam.id,
            'title': exam.title,
            'description': exam.description,
            'duration_minutes': exam.duration_minutes,
            'is_active': exam.is_active,
            'questions': questions_data
        }
    
    def deserialize_exam(self, json_data: Dict[str, Any], teacher_id: int) -> Optional[Exam]:
        """
        Deserialize JSON data to create an exam with questions.
        
        Args:
            json_data: Dictionary containing exam and questions data
            teacher_id: ID of the teacher creating the exam
            
        Returns:
            Created Exam instance, None if creation fails
        """
        try:
            with transaction.atomic():
                # Create exam
                exam_data = {
                    'title': json_data['title'],
                    'description': json_data.get('description', ''),
                    'duration_minutes': json_data['duration_minutes'],
                    'is_active': json_data.get('is_active', False),
                    'created_by_id': teacher_id
                }
                exam = self.exam_repository.create(**exam_data)
                
                # Create questions
                for question_data in json_data.get('questions', []):
                    self.question_repository.create(
                        exam=exam,
                        question_type=question_data['type'],
                        question_text=question_data['text'],
                        options=question_data.get('options'),
                        correct_answer=question_data['correct_answer'],
                        points=question_data.get('points', 1.0),
                        order_index=question_data.get('order_index', 0)
                    )
                
                return exam
        except Exception as e:
            print(f"Error deserializing exam: {e}")
            return None
