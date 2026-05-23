"""
Student repository for data access operations.
Provides specialized methods for student-related queries.
"""
from typing import Optional
from .base_repository import BaseRepository
from users.models import Student


class StudentRepository(BaseRepository):
    """
    Repository for Student model data access.
    Extends BaseRepository with student-specific operations.
    """
    
    def __init__(self):
        """Initialize with Student model."""
        super().__init__(Student)
    
    def get_by_school_id(self, school_id: str) -> Optional[Student]:
        """
        Retrieve a student by their School_ID.
        
        Args:
            school_id: Unique school identifier
            
        Returns:
            Student instance if found, None otherwise
        """
        normalized_school_id = (school_id or '').strip()
        if not normalized_school_id:
            return None

        try:
            return self.model.objects.get(school_id=normalized_school_id)
        except self.model.DoesNotExist:
            # Backward-compatible lookup for IDs entered with different casing.
            matches = list(self.model.objects.filter(
                school_id__iexact=normalized_school_id
            )[:2])
            return matches[0] if len(matches) == 1 else None
    
    def create_student(self, school_id: str, first_name: str, last_name: str, password: str) -> Student:
        """
        Create a new student with hashed password.
        
        Args:
            school_id: Unique school identifier
            first_name: Student's first name
            last_name: Student's last name
            password: Raw password (will be hashed)
            
        Returns:
            Created Student instance
        """
        student = Student(
            school_id=school_id,
            first_name=first_name,
            last_name=last_name
        )
        student.set_password(password)
        student.save()
        return student
    
    def update_password(self, school_id: str, new_password: str) -> Optional[Student]:
        """
        Update a student's password.
        
        Args:
            school_id: Student's school ID
            new_password: New raw password (will be hashed)
            
        Returns:
            Updated Student instance if found, None otherwise
        """
        student = self.get_by_school_id(school_id)
        if student:
            student.set_password(new_password)
            student.save()
        return student
    
    def school_id_exists(self, school_id: str) -> bool:
        """
        Check if a School_ID already exists.
        
        Args:
            school_id: School ID to check
            
        Returns:
            True if exists, False otherwise
        """
        return self.exists(school_id=school_id)
