"""
Exam Student Assignment repository for data access operations.
Implements the Repository pattern for ExamStudentAssignment model.
"""
from typing import Optional, List, Set
from django.db.models import QuerySet
from exams.models import ExamStudentAssignment
from repositories.base_repository import BaseRepository


class ExamStudentAssignmentRepository(BaseRepository):
    """
    Repository for ExamStudentAssignment model with specialized query methods.
    """
    
    def __init__(self):
        super().__init__(ExamStudentAssignment)
    
    def get_students_for_exam(self, exam_id: int) -> QuerySet:
        """
        Retrieve all students assigned to a specific exam.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            QuerySet of ExamStudentAssignment instances for the exam
        """
        return self.filter(exam_id=exam_id).select_related('student')
    
    def get_student_ids_for_exam(self, exam_id: int) -> Set[int]:
        """
        Get set of student IDs assigned to an exam.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            Set of student IDs
        """
        return set(
            self.filter(exam_id=exam_id).values_list('student_id', flat=True)
        )
    
    def assign_students_to_exam(self, exam_id: int, student_ids: List[int]) -> List[ExamStudentAssignment]:
        """
        Assign multiple students to an exam.
        Creates ExamStudentAssignment records for each student.
        
        Args:
            exam_id: Primary key of the exam
            student_ids: List of student IDs to assign
            
        Returns:
            List of created ExamStudentAssignment instances
        """
        assignments = []
        for student_id in student_ids:
            # Use get_or_create to avoid duplicates
            assignment, created = self.model.objects.get_or_create(
                exam_id=exam_id,
                student_id=student_id
            )
            assignments.append(assignment)
        return assignments
    
    def clear_assignments_for_exam(self, exam_id: int) -> int:
        """
        Remove all student assignments for an exam.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            Number of assignments deleted
        """
        count, _ = self.filter(exam_id=exam_id).delete()
        return count
    
    def is_student_assigned(self, exam_id: int, student_id: int) -> bool:
        """
        Check if a specific student is assigned to an exam.
        
        Args:
            exam_id: Primary key of the exam
            student_id: Primary key of the student
            
        Returns:
            True if student is assigned, False otherwise
        """
        return self.exists(exam_id=exam_id, student_id=student_id)
    
    def has_any_assignments(self, exam_id: int) -> bool:
        """
        Check if an exam has any student assignments.
        Used to determine if access is restricted to specific students.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            True if exam has student assignments, False otherwise
        """
        return self.exists(exam_id=exam_id)
    
    def get_exams_for_student(self, student_id: int) -> QuerySet:
        """
        Retrieve all exams assigned to a specific student.
        
        Args:
            student_id: Primary key of the student
            
        Returns:
            QuerySet of ExamStudentAssignment instances for the student
        """
        return self.filter(student_id=student_id).select_related('exam')

