"""
Class repository for data access operations.
Implements the Repository pattern for Class model.
"""
from typing import Optional
from django.db.models import QuerySet
from users.models import Class, Student
from repositories.base_repository import BaseRepository


class ClassRepository(BaseRepository):
    """
    Repository for Class model with specialized query methods.
    Provides optimized queries for class-teacher and class-student relationships.
    """
    
    def __init__(self):
        super().__init__(Class)
    
    def get_classes_by_teacher(self, teacher_id: int) -> QuerySet:
        """
        Retrieve all classes created by a specific teacher with optimized queries.
        Uses select_related for teacher to minimize database queries.
        
        Args:
            teacher_id: Primary key of the teacher
            
        Returns:
            QuerySet of Class instances created by the teacher with teacher prefetched
            
        Requirements: 1.3, 6.2
        """
        return self.filter(teacher_id=teacher_id).select_related('teacher')
    
    def get_class_with_students(self, class_id: int) -> Optional[Class]:
        """
        Retrieve a class with its students prefetched.
        Uses prefetch_related for students to optimize query performance.
        
        Args:
            class_id: Primary key of the class
            
        Returns:
            Class instance with students prefetched, None if not found
            
        Requirements: 2.3, 6.3
        """
        try:
            return self.model.objects.prefetch_related('students').get(pk=class_id)
        except self.model.DoesNotExist:
            return None
    
    def get_students_in_class(self, class_id: int) -> QuerySet:
        """
        Retrieve all students assigned to a specific class.
        
        Args:
            class_id: Primary key of the class
            
        Returns:
            QuerySet of Student instances assigned to the class
            
        Requirements: 2.3
        """
        return Student.objects.filter(class_assigned_id=class_id)
    
    def check_duplicate_class(
        self,
        teacher_id: int,
        grade_level: str,
        strand: str,
        section: str,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        Check if a class with the same teacher, grade level, strand, and section exists.
        Used for uniqueness validation during class creation and updates.
        
        Args:
            teacher_id: Primary key of the teacher
            grade_level: Grade level of the class
            strand: Academic strand of the class
            section: Section name of the class
            exclude_id: Optional class ID to exclude from the check (for updates)
            
        Returns:
            True if a duplicate exists, False otherwise
            
        Requirements: 7.1
        """
        queryset = self.filter(
            teacher_id=teacher_id,
            grade_level=grade_level,
            strand=strand,
            section=section
        )
        
        if exclude_id is not None:
            queryset = queryset.exclude(pk=exclude_id)
        
        return queryset.exists()
    
    def get_classes_by_strand(self, strand: str) -> QuerySet:
        """
        Retrieve all classes for a specific strand.
        
        Args:
            strand: Academic strand to filter by
            
        Returns:
            QuerySet of Class instances with the specified strand
            
        Requirements: 6.2
        """
        return self.filter(strand=strand).select_related('teacher')
    
    def get_classes_by_grade(self, grade_level: str) -> QuerySet:
        """
        Retrieve all classes for a specific grade level.
        
        Args:
            grade_level: Grade level to filter by
            
        Returns:
            QuerySet of Class instances with the specified grade level
            
        Requirements: 6.2
        """
        return self.filter(grade_level=grade_level).select_related('teacher')
