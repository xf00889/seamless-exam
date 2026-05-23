"""
Profile service for managing student profile operations.
Handles profile information updates, password changes, and profile picture management.
"""
from typing import Optional, Dict, Any
from django.core.files.uploadedfile import UploadedFile
from repositories.student_repository import StudentRepository
from services.file_service import FileService
from services.rate_limiter import RateLimiter
from services.sanitizer import InputSanitizer
from services.result import Result
from services.errors import (
    ValidationError,
    NotFoundError,
    AuthenticationError,
    DatabaseError
)
from users.models import Student
import logging

logger = logging.getLogger('services')


class ProfileService:
    """
    Service for managing student profile operations.
    Provides methods for viewing, updating profile information, changing passwords,
    and managing profile pictures.
    """
    
    def __init__(self):
        """Initialize with required repositories and services."""
        self.student_repo = StudentRepository()
        self.file_service = FileService()
        self.rate_limiter = RateLimiter()
        self.sanitizer = InputSanitizer()
    
    def get_student_profile(self, student_id: int) -> Result[Student, NotFoundError]:
        """
        Retrieve a student's profile by ID.
        
        Args:
            student_id: Student's database ID
            
        Returns:
            Result[Student, NotFoundError]: Success with Student instance or Failure with error
            
        Requirements: 2.1
        """
        try:
            student = self.student_repo.get_by_id(student_id)
            
            if student is None:
                logger.warning(f"Student profile not found: {student_id}")
                return Result.failure(NotFoundError(
                    message=f"Student with ID {student_id} not found",
                    details={'student_id': student_id}
                ))
            
            logger.info(f"Retrieved profile for student {student_id}")
            return Result.success(student)
            
        except Exception as e:
            logger.error(f"Error retrieving student profile {student_id}: {str(e)}")
            return Result.failure(NotFoundError(
                message="Failed to retrieve student profile",
                details={'student_id': student_id, 'error': str(e)}
            ))

    def update_profile_info(
        self, 
        student_id: int, 
        data: Dict[str, Any]
    ) -> Result[Student, ValidationError]:
        """
        Update a student's profile information with validation and sanitization.
        
        Validates input data and updates allowed fields (first_name, last_name, bio).
        Does not allow modification of school_id or created_at.
        Sanitizes all inputs to prevent XSS attacks.
        
        Args:
            student_id: Student's database ID
            data: Dictionary containing fields to update
                  Allowed keys: 'first_name', 'last_name', 'bio'
            
        Returns:
            Result[Student, ValidationError]: Success with updated Student or Failure with error
            
        Requirements: 3.1, 3.4, 13.5
        """
        # Get the student first
        student_result = self.get_student_profile(student_id)
        if student_result.is_failure():
            return Result.failure(ValidationError(
                message="Student not found",
                details={'student_id': student_id}
            ))
        
        student = student_result.value
        
        # Sanitize inputs (Requirement 13.5)
        sanitized_data = {}
        if 'first_name' in data:
            sanitized_data['first_name'] = self.sanitizer.sanitize_text(data['first_name'], max_length=100)
        if 'last_name' in data:
            sanitized_data['last_name'] = self.sanitizer.sanitize_text(data['last_name'], max_length=100)
        if 'bio' in data:
            sanitized_data['bio'] = self.sanitizer.sanitize_html(data['bio'])
            # Truncate bio to max length after sanitization
            if sanitized_data['bio'] and len(sanitized_data['bio']) > 500:
                sanitized_data['bio'] = sanitized_data['bio'][:500]
        
        # Validate input data
        validation_errors = {}
        
        # Allowed fields for update
        allowed_fields = {'first_name', 'last_name', 'bio'}
        
        # Check for invalid fields
        invalid_fields = set(data.keys()) - allowed_fields
        if invalid_fields:
            validation_errors['invalid_fields'] = list(invalid_fields)
        
        # Validate first_name if provided
        if 'first_name' in sanitized_data:
            first_name = sanitized_data['first_name']
            if not first_name or not isinstance(first_name, str):
                validation_errors['first_name'] = 'First name is required and must be a string'
            elif len(first_name.strip()) == 0:
                validation_errors['first_name'] = 'First name cannot be empty'
            elif len(first_name) > 100:
                validation_errors['first_name'] = 'First name cannot exceed 100 characters'
        
        # Validate last_name if provided
        if 'last_name' in sanitized_data:
            last_name = sanitized_data['last_name']
            if not last_name or not isinstance(last_name, str):
                validation_errors['last_name'] = 'Last name is required and must be a string'
            elif len(last_name.strip()) == 0:
                validation_errors['last_name'] = 'Last name cannot be empty'
            elif len(last_name) > 100:
                validation_errors['last_name'] = 'Last name cannot exceed 100 characters'
        
        # Validate bio if provided
        if 'bio' in sanitized_data:
            bio = sanitized_data['bio']
            if bio is not None:
                if not isinstance(bio, str):
                    validation_errors['bio'] = 'Bio must be a string'
                elif len(bio) > 500:
                    validation_errors['bio'] = 'Bio cannot exceed 500 characters'
        
        # Return validation errors if any
        if validation_errors:
            logger.warning(f"Profile update validation failed for student {student_id}: {validation_errors}")
            return Result.failure(ValidationError(
                message="Profile update validation failed",
                details=validation_errors
            ))
        
        # Update the student fields
        try:
            if 'first_name' in sanitized_data:
                student.first_name = sanitized_data['first_name'].strip()
            
            if 'last_name' in sanitized_data:
                student.last_name = sanitized_data['last_name'].strip()
            
            if 'bio' in sanitized_data:
                student.bio = sanitized_data['bio']
            
            # Save the updated student
            student.save()
            
            logger.info(f"Profile updated successfully for student {student_id}")
            return Result.success(student)
            
        except Exception as e:
            logger.error(f"Failed to update profile for student {student_id}: {str(e)}")
            return Result.failure(ValidationError(
                message="Failed to update profile",
                details={'student_id': student_id, 'error': str(e)}
            ))

    def upload_profile_picture(
        self, 
        student_id: int, 
        file: UploadedFile
    ) -> Result[str, ValidationError]:
        """
        Upload and save a profile picture for a student.
        
        Uses FileService for validation and secure storage.
        Deletes the old profile picture if one exists.
        
        Args:
            student_id: Student's database ID
            file: Uploaded image file
            
        Returns:
            Result[str, ValidationError]: Success with file URL or Failure with error
            
        Requirements: 4.1, 4.2, 4.3, 4.4
        """
        # Get the student first
        student_result = self.get_student_profile(student_id)
        if student_result.is_failure():
            return Result.failure(ValidationError(
                message="Student not found",
                details={'student_id': student_id}
            ))
        
        student = student_result.value
        
        # Get old profile picture path for cleanup
        old_file_path = student.profile_picture.name if student.profile_picture else None
        
        # Save the profile picture using FileService
        save_result = self.file_service.save_profile_picture(
            file=file,
            student_id=student_id,
            old_file_path=old_file_path
        )
        
        if save_result.is_failure():
            logger.warning(f"Failed to save profile picture for student {student_id}: {save_result.error}")
            return Result.failure(ValidationError(
                message="Failed to upload profile picture",
                details={'error': str(save_result.error)}
            ))
        
        # Update student's profile_picture field
        try:
            file_path = save_result.value
            student.profile_picture = file_path
            student.save()
            
            # Get the URL for the uploaded file
            file_url = self.file_service.get_file_url(file_path)
            
            logger.info(f"Profile picture uploaded successfully for student {student_id}")
            return Result.success(file_url)
            
        except Exception as e:
            logger.error(f"Failed to update student profile picture field for {student_id}: {str(e)}")
            # Try to clean up the uploaded file
            self.file_service.delete_file(save_result.value)
            return Result.failure(ValidationError(
                message="Failed to update profile picture",
                details={'student_id': student_id, 'error': str(e)}
            ))

    def change_password(
        self, 
        student_id: int, 
        current_password: str, 
        new_password: str
    ) -> Result[bool, AuthenticationError]:
        """
        Change a student's password with security checks and rate limiting.
        
        Verifies the current password before allowing the change.
        Validates new password meets security requirements.
        Uses Django's secure password hashing (PBKDF2).
        Implements rate limiting to prevent abuse.
        
        Args:
            student_id: Student's database ID
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            Result[bool, AuthenticationError]: Success(True) or Failure with error
            
        Requirements: 5.1, 5.2, 5.4, 13.3, 13.4
        """
        # Check rate limit (Requirement 13.4)
        is_allowed, remaining = self.rate_limiter.check_password_change_limit(student_id)
        if not is_allowed:
            logger.warning(f"Password change rate limit exceeded for student {student_id}")
            return Result.failure(AuthenticationError(
                message="Too many password change attempts. Please try again later.",
                details={'rate_limit': 'exceeded', 'retry_after': '1 hour'}
            ))
        
        # Get the student first
        student_result = self.get_student_profile(student_id)
        if student_result.is_failure():
            return Result.failure(AuthenticationError(
                message="Student not found",
                details={'student_id': student_id}
            ))
        
        student = student_result.value
        
        # Record the attempt (Requirement 13.4)
        self.rate_limiter.record_password_change_attempt(student_id)
        
        # Verify current password (Requirement 5.2)
        if not student.check_password(current_password):
            logger.warning(f"Password change failed for student {student_id}: incorrect current password")
            return Result.failure(AuthenticationError(
                message="Current password is incorrect",
                details={'field': 'current_password'}
            ))
        
        # Validate new password (Requirement 5.4)
        validation_errors = self._validate_password(new_password)
        if validation_errors:
            logger.warning(f"Password change validation failed for student {student_id}: {validation_errors}")
            return Result.failure(AuthenticationError(
                message="New password does not meet security requirements",
                details=validation_errors
            ))
        
        # Check that new password is different from current
        if current_password == new_password:
            return Result.failure(AuthenticationError(
                message="New password must be different from current password",
                details={'field': 'new_password'}
            ))
        
        # Update password using secure hashing (Requirement 13.3)
        try:
            student.set_password(new_password)
            student.save()
            
            # Reset rate limit on successful password change
            self.rate_limiter.reset_password_change_limit(student_id)
            
            logger.info(f"Password changed successfully for student {student_id}")
            return Result.success(True)
            
        except Exception as e:
            logger.error(f"Failed to change password for student {student_id}: {str(e)}")
            return Result.failure(AuthenticationError(
                message="Failed to change password",
                details={'student_id': student_id, 'error': str(e)}
            ))
    
    def _validate_password(self, password: str) -> Dict[str, str]:
        """
        Validate password meets security requirements.
        
        Requirements (Requirement 5.4):
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        
        Args:
            password: Password to validate
            
        Returns:
            Dictionary of validation errors (empty if valid)
        """
        errors = {}
        
        if not password or not isinstance(password, str):
            errors['password'] = 'Password is required'
            return errors
        
        # Minimum length check
        if len(password) < 8:
            errors['length'] = 'Password must be at least 8 characters long'
        
        # Check for uppercase letter
        if not any(c.isupper() for c in password):
            errors['uppercase'] = 'Password must contain at least one uppercase letter'
        
        # Check for lowercase letter
        if not any(c.islower() for c in password):
            errors['lowercase'] = 'Password must contain at least one lowercase letter'
        
        # Check for digit
        if not any(c.isdigit() for c in password):
            errors['digit'] = 'Password must contain at least one digit'
        
        return errors

    def delete_profile_picture(self, student_id: int) -> Result[bool, ValidationError]:
        """
        Delete a student's profile picture.
        
        Removes the profile picture file from storage and clears the database field.
        
        Args:
            student_id: Student's database ID
            
        Returns:
            Result[bool, ValidationError]: Success(True) or Failure with error
            
        Requirements: 4.4
        """
        # Get the student first
        student_result = self.get_student_profile(student_id)
        if student_result.is_failure():
            return Result.failure(ValidationError(
                message="Student not found",
                details={'student_id': student_id}
            ))
        
        student = student_result.value
        
        # Check if student has a profile picture
        if not student.profile_picture:
            logger.info(f"No profile picture to delete for student {student_id}")
            return Result.success(True)
        
        # Get the file path
        file_path = student.profile_picture.name
        
        # Delete the file using FileService
        delete_result = self.file_service.delete_file(file_path)
        
        if delete_result.is_failure():
            logger.warning(f"Failed to delete profile picture file for student {student_id}: {delete_result.error}")
            # Continue to clear the database field even if file deletion fails
        
        # Clear the profile_picture field
        try:
            student.profile_picture = None
            student.save()
            
            logger.info(f"Profile picture deleted successfully for student {student_id}")
            return Result.success(True)
            
        except Exception as e:
            logger.error(f"Failed to clear profile picture field for student {student_id}: {str(e)}")
            return Result.failure(ValidationError(
                message="Failed to delete profile picture",
                details={'student_id': student_id, 'error': str(e)}
            ))
