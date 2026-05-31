"""
Exam repository for data access operations.
Implements the Repository pattern for Exam model.
"""
from typing import Optional, List
from django.db.models import QuerySet
from exams.models import Exam, ExamClassAssignment
from repositories.base_repository import BaseRepository


class ExamRepository(BaseRepository):
    """
    Repository for Exam model with specialized query methods.
    """
    
    def __init__(self):
        super().__init__(Exam)
    
    def get_active_exams(self) -> QuerySet:
        """
        Retrieve all active exams with optimized queries.
        Uses select_related for created_by and prefetch_related for questions.
        
        Returns:
            QuerySet of active Exam instances with related data prefetched
            
        Requirements: 9.5
        """
        return self.filter(is_active=True).select_related('created_by', 'quarter').prefetch_related('questions')
    
    def get_exams_by_teacher(self, teacher_id: int) -> QuerySet:
        """
        Retrieve all exams created by a specific teacher with optimized queries.
        Uses select_related for created_by and prefetch_related for questions.
        
        Args:
            teacher_id: Primary key of the teacher
            
        Returns:
            QuerySet of Exam instances created by the teacher with related data prefetched
            
        Requirements: 9.5
        """
        return self.filter(created_by_id=teacher_id).select_related('created_by', 'quarter').prefetch_related('questions')
    
    def get_active_exams_by_teacher(self, teacher_id: int) -> QuerySet:
        """
        Retrieve active exams created by a specific teacher.
        
        Args:
            teacher_id: Primary key of the teacher
            
        Returns:
            QuerySet of active Exam instances created by the teacher
        """
        return self.filter(created_by_id=teacher_id, is_active=True)
    
    def activate_exam(self, exam_id: int) -> Optional[Exam]:
        """
        Activate an exam by setting is_active to True.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            Updated Exam instance if found, None otherwise
        """
        return self.update(exam_id, is_active=True)
    
    def deactivate_exam(self, exam_id: int) -> Optional[Exam]:
        """
        Deactivate an exam by setting is_active to False.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            Updated Exam instance if found, None otherwise
        """
        return self.update(exam_id, is_active=False)
    
    def get_with_questions(self, exam_id: int) -> Optional[Exam]:
        """
        Retrieve an exam with its questions prefetched.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            Exam instance with questions prefetched, None if not found
        """
        try:
            return self.model.objects.select_related('created_by', 'quarter').prefetch_related('questions').get(pk=exam_id)
        except self.model.DoesNotExist:
            return None
    
    def get_exams_for_class(self, class_id: int) -> QuerySet:
        """
        Retrieve all exams assigned to a specific class.
        Uses prefetch_related for class_assignments to optimize query performance.
        
        Args:
            class_id: Primary key of the class
            
        Returns:
            QuerySet of Exam instances assigned to the class
            
        Requirements: 3.4, 6.4
        """
        return self.model.objects.filter(
            class_assignments__class_assigned_id=class_id
        ).select_related('created_by', 'quarter').prefetch_related('class_assignments')
    
    def get_classes_for_exam(self, exam_id: int) -> QuerySet:
        """
        Retrieve all classes assigned to a specific exam.
        Uses prefetch_related for class_assignments to optimize query performance.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            QuerySet of Class instances (via ExamClassAssignment) assigned to the exam
            
        Requirements: 3.4, 6.4
        """
        from users.models import Class
        return Class.objects.filter(
            exam_assignments__exam_id=exam_id
        ).prefetch_related('exam_assignments')
