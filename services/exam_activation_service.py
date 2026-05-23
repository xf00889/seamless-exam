"""
Exam activation service for managing exam visibility.
Handles activation and deactivation of exams.
"""
from typing import Optional
from django.db import transaction
from exams.models import Exam
from repositories.exam_repository import ExamRepository


class ExamActivationService:
    """
    Service class for exam activation/deactivation logic.
    Controls exam visibility to students.
    """
    
    def __init__(self):
        self.exam_repository = ExamRepository()
    
    def activate_exam(self, exam_id: int) -> Optional[Exam]:
        """
        Activate an exam, making it visible to students.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            Updated Exam instance if successful, None otherwise
        """
        try:
            exam = self.exam_repository.activate_exam(exam_id)
            if exam:
                print(f"Exam '{exam.title}' (ID: {exam_id}) activated successfully")
            return exam
        except Exception as e:
            print(f"Error activating exam: {e}")
            return None
    
    def deactivate_exam(self, exam_id: int) -> Optional[Exam]:
        """
        Deactivate an exam, hiding it from students.
        Note: Current student progress is preserved by the attempt system.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            Updated Exam instance if successful, None otherwise
        """
        try:
            exam = self.exam_repository.deactivate_exam(exam_id)
            if exam:
                print(f"Exam '{exam.title}' (ID: {exam_id}) deactivated successfully")
            return exam
        except Exception as e:
            print(f"Error deactivating exam: {e}")
            return None
    
    def toggle_activation(self, exam_id: int) -> Optional[Exam]:
        """
        Toggle the activation status of an exam.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            Updated Exam instance if successful, None otherwise
        """
        exam = self.exam_repository.get_by_id(exam_id)
        if not exam:
            return None
        
        if exam.is_active:
            return self.deactivate_exam(exam_id)
        else:
            return self.activate_exam(exam_id)
    
    def is_exam_active(self, exam_id: int) -> bool:
        """
        Check if an exam is currently active.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            True if exam is active, False otherwise
        """
        exam = self.exam_repository.get_by_id(exam_id)
        return exam.is_active if exam else False
    
    def get_active_exams_count(self) -> int:
        """
        Get the count of currently active exams.
        
        Returns:
            Number of active exams
        """
        return self.exam_repository.count(is_active=True)
