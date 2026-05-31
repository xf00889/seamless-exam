"""
Authentication service for teacher and student login/logout.
Handles session management and secure authentication.
"""
from secrets import compare_digest
from typing import Optional, Dict, Any
from dataclasses import dataclass
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpRequest
from repositories.student_repository import StudentRepository
from repositories.teacher_repository import TeacherRepository
from services.rate_limiter import RateLimiter
from users.models import Teacher, Student


@dataclass
class AuthResult:
    """Result of an authentication attempt."""
    success: bool
    user: Optional[Any] = None
    error: Optional[str] = None
    user_type: Optional[str] = None  # 'teacher' or 'student'


class AuthenticationService:
    """
    Service for handling authentication operations.
    Manages login, logout, and session management for both teachers and students.
    """
    
    def __init__(self):
        """Initialize with repositories."""
        self.student_repo = StudentRepository()
        self.teacher_repo = TeacherRepository()
        self.rate_limiter = RateLimiter()

    @staticmethod
    def _resolve_username_case_insensitive(username: str) -> str:
        """
        Resolve username to its canonical casing for more forgiving login.

        Returns the original value when no exact match can be safely determined.
        """
        normalized_username = (username or '').strip()
        if not normalized_username:
            return normalized_username

        matches = list(User.objects.filter(username__iexact=normalized_username)
                       .values_list('username', flat=True)[:2])
        return matches[0] if len(matches) == 1 else normalized_username
    
    def authenticate_teacher(self, request: HttpRequest, username: str, password: str) -> AuthResult:
        """
        Authenticate a teacher using Django's authentication system.
        
        Args:
            request: Django HTTP request object
            username: Teacher's username
            password: Raw password
            
        Returns:
            AuthResult with success status and teacher or error message
        """
        canonical_username = self._resolve_username_case_insensitive(username)

        is_allowed, _ = self.rate_limiter.check_login_attempt_limit(f'teacher:{canonical_username.lower()}')
        if not is_allowed:
            return AuthResult(
                success=False,
                error='Too many login attempts. Please try again later.'
            )

        # Use Django's built-in authentication
        user = authenticate(request, username=canonical_username, password=password)
        
        if user is not None:
            self.rate_limiter.record_login_attempt(f'teacher:{canonical_username.lower()}', success=True)

            # Check if user has a teacher profile
            teacher = Teacher.objects.filter(user=user).first()
            if teacher is None and (user.is_staff or user.is_superuser):
                # Allow legacy/admin users to access teacher portal.
                teacher = Teacher.objects.create(user=user)

            if teacher is None:
                return AuthResult(
                    success=False,
                    error='User account exists but is not registered as a teacher'
                )

            # Create session
            login(request, user)
            
            # Store user type in session for authorization checks
            request.session['user_type'] = 'teacher'
            request.session['user_id'] = user.id
            
            return AuthResult(
                success=True,
                user=teacher,
                user_type='teacher'
            )
        else:
            self.rate_limiter.record_login_attempt(f'teacher:{canonical_username.lower()}', success=False)
            return AuthResult(
                success=False,
                error='Invalid username or password'
            )
    
    def authenticate_student(self, request: HttpRequest, school_id: str, password: str) -> AuthResult:
        """
        Authenticate a student using School_ID and password.
        
        Args:
            request: Django HTTP request object
            school_id: Student's unique school identifier
            password: Raw password
            
        Returns:
            AuthResult with success status and student or error message
        """
        normalized_school_id = (school_id or '').strip()
        rate_limit_key = f'student:{normalized_school_id.lower()}'

        is_allowed, _ = self.rate_limiter.check_login_attempt_limit(rate_limit_key)
        if not is_allowed:
            return AuthResult(
                success=False,
                error='Too many login attempts. Please try again later.'
            )

        student = self.student_repo.get_by_school_id(normalized_school_id)
        
        if student is None:
            self.rate_limiter.record_login_attempt(rate_limit_key, success=False)
            return AuthResult(
                success=False,
                error='Invalid School ID or password'
            )
        
        # Verify password using secure hash comparison.
        # If legacy plaintext credentials exist, migrate to hashed on successful login.
        password_is_valid = student.check_password(password)
        if not password_is_valid and student.password_hash:
            password_is_valid = compare_digest(student.password_hash, password)
            if password_is_valid:
                student.set_password(password)
                student.save(update_fields=['password_hash'])

        if not password_is_valid:
            self.rate_limiter.record_login_attempt(rate_limit_key, success=False)
            return AuthResult(
                success=False,
                error='Invalid School ID or password'
            )
        
        # Create session for student
        # Note: Students don't use Django's User model, so we manage sessions manually
        request.session['user_type'] = 'student'
        request.session['student_id'] = student.id
        request.session['school_id'] = student.school_id
        request.session['student_name'] = student.get_full_name()
        
        # Mark session as modified to ensure it's saved
        request.session.modified = True
        self.rate_limiter.record_login_attempt(rate_limit_key, success=True)
        
        return AuthResult(
            success=True,
            user=student,
            user_type='student'
        )
    
    def logout_user(self, request: HttpRequest) -> bool:
        """
        Logout the current user and terminate their session.
        Clears all session data and authentication tokens.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            True if logout successful
        """
        user_type = request.session.get('user_type')
        
        if user_type == 'teacher':
            # Use Django's logout for teachers
            logout(request)
        
        # Clear all session data for both teacher and student
        request.session.flush()
        
        return True
    
    def is_authenticated(self, request: HttpRequest) -> bool:
        """
        Check if the current request has an authenticated user.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            True if user is authenticated, False otherwise
        """
        user_type = request.session.get('user_type')
        
        if user_type == 'teacher':
            return request.user.is_authenticated
        elif user_type == 'student':
            return 'student_id' in request.session
        
        return False
    
    def get_current_user_type(self, request: HttpRequest) -> Optional[str]:
        """
        Get the type of the currently authenticated user.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            'teacher', 'student', or None if not authenticated
        """
        return request.session.get('user_type')
    
    def get_current_student(self, request: HttpRequest) -> Optional[Student]:
        """
        Get the currently authenticated student.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            Student instance if authenticated as student, None otherwise
        """
        if request.session.get('user_type') == 'student':
            student_id = request.session.get('student_id')
            if student_id:
                return self.student_repo.get_by_id(student_id)
        return None
    
    def get_current_teacher(self, request: HttpRequest) -> Optional[Teacher]:
        """
        Get the currently authenticated teacher.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            Teacher instance if authenticated as teacher, None otherwise
        """
        if request.session.get('user_type') == 'teacher' and request.user.is_authenticated:
            try:
                return Teacher.objects.get(user=request.user)
            except Teacher.DoesNotExist:
                return None
        return None
    
    def require_teacher(self, request: HttpRequest) -> bool:
        """
        Check if the current user is an authenticated teacher.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            True if authenticated as teacher, False otherwise
        """
        return (request.session.get('user_type') == 'teacher' and 
                request.user.is_authenticated)
    
    def require_student(self, request: HttpRequest) -> bool:
        """
        Check if the current user is an authenticated student.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            True if authenticated as student, False otherwise
        """
        return (request.session.get('user_type') == 'student' and 
                'student_id' in request.session)
