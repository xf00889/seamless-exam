"""
Teacher repository for data access operations.
Provides specialized methods for teacher-related queries.
"""
from typing import Optional
from django.contrib.auth.models import User
from .base_repository import BaseRepository
from users.models import Teacher


class TeacherRepository(BaseRepository):
    """
    Repository for Teacher model data access.
    Extends BaseRepository with teacher-specific operations.
    """
    
    def __init__(self):
        """Initialize with Teacher model."""
        super().__init__(Teacher)
    
    def get_by_user_id(self, user_id: int) -> Optional[Teacher]:
        """
        Retrieve a teacher by their User ID.
        
        Args:
            user_id: Django User primary key
            
        Returns:
            Teacher instance if found, None otherwise
        """
        try:
            return self.model.objects.get(user_id=user_id)
        except self.model.DoesNotExist:
            return None
    
    def get_by_username(self, username: str) -> Optional[Teacher]:
        """
        Retrieve a teacher by their username.
        
        Args:
            username: Django User username
            
        Returns:
            Teacher instance if found, None otherwise
        """
        try:
            user = User.objects.get(username=username)
            return self.model.objects.get(user=user)
        except (User.DoesNotExist, self.model.DoesNotExist):
            return None
    
    def create_teacher(self, username: str, password: str, email: str = '', 
                      first_name: str = '', last_name: str = '', 
                      department: str = '') -> Teacher:
        """
        Create a new teacher with associated User account.
        
        Args:
            username: Django User username
            password: Raw password (will be hashed by Django)
            email: Teacher's email address
            first_name: Teacher's first name
            last_name: Teacher's last name
            department: Teacher's department
            
        Returns:
            Created Teacher instance
        """
        # Create Django User with hashed password
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create Teacher profile
        teacher = Teacher.objects.create(
            user=user,
            department=department
        )
        
        return teacher
    
    def update_teacher(self, user_id: int, **kwargs) -> Optional[Teacher]:
        """
        Update teacher information.
        
        Args:
            user_id: Django User primary key
            **kwargs: Fields to update (can include user fields and department)
            
        Returns:
            Updated Teacher instance if found, None otherwise
        """
        teacher = self.get_by_user_id(user_id)
        if not teacher:
            return None
        
        # Separate user fields from teacher fields
        user_fields = {'email', 'first_name', 'last_name'}
        teacher_updates = {}
        user_updates = {}
        
        for key, value in kwargs.items():
            if key in user_fields:
                user_updates[key] = value
            else:
                teacher_updates[key] = value
        
        # Update User fields
        if user_updates:
            for key, value in user_updates.items():
                setattr(teacher.user, key, value)
            teacher.user.save()
        
        # Update Teacher fields
        if teacher_updates:
            for key, value in teacher_updates.items():
                setattr(teacher, key, value)
            teacher.save()
        
        return teacher
    
    def username_exists(self, username: str) -> bool:
        """
        Check if a username already exists.
        
        Args:
            username: Username to check
            
        Returns:
            True if exists, False otherwise
        """
        return User.objects.filter(username=username).exists()
