from secrets import compare_digest
from typing import Optional, Dict, Any
from dataclasses import dataclass
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpRequest
from repositories.student_repository import StudentRepository
from repositories.teacher_repository import TeacherRepository
from services.rate_limiter import RateLimiter
from users.models import Teacher, Student, SchoolAdmin


@dataclass
class AuthResult:
    success: bool
    user: Optional[Any] = None
    error: Optional[str] = None
    user_type: Optional[str] = None


class AuthenticationService:
    def __init__(self):
        self.student_repo = StudentRepository()
        self.teacher_repo = TeacherRepository()
        self.rate_limiter = RateLimiter()

    @staticmethod
    def _resolve_username_case_insensitive(username: str) -> str:
        normalized = (username or '').strip()
        if not normalized:
            return normalized
        matches = list(User.objects.filter(username__iexact=normalized)
                       .values_list('username', flat=True)[:2])
        return matches[0] if len(matches) == 1 else normalized

    def authenticate_teacher(self, request: HttpRequest, username: str, password: str) -> AuthResult:
        canonical_username = self._resolve_username_case_insensitive(username)
        is_allowed, _ = self.rate_limiter.check_login_attempt_limit(
            f'teacher:{canonical_username.lower()}'
        )
        if not is_allowed:
            return AuthResult(
                success=False,
                error='Too many login attempts. Please try again later.',
            )

        user = authenticate(request, username=canonical_username, password=password)
        if user is not None:
            self.rate_limiter.record_login_attempt(
                f'teacher:{canonical_username.lower()}', success=True
            )
            teacher = Teacher.objects.filter(user=user).first()
            if teacher is None:
                return AuthResult(
                    success=False,
                    error='User account exists but is not registered as a teacher',
                )
            login(request, user)
            request.session['user_type'] = 'teacher'
            request.session['user_id'] = user.id
            return AuthResult(success=True, user=teacher, user_type='teacher')
        else:
            self.rate_limiter.record_login_attempt(
                f'teacher:{canonical_username.lower()}', success=False
            )
            return AuthResult(success=False, error='Invalid username or password')

    def authenticate_student(self, request: HttpRequest, student_id: str, password: str) -> AuthResult:
        normalized_id = (student_id or '').strip()
        rate_limit_key = f'student:{normalized_id.lower()}'
        is_allowed, _ = self.rate_limiter.check_login_attempt_limit(rate_limit_key)
        if not is_allowed:
            return AuthResult(
                success=False,
                error='Too many login attempts. Please try again later.',
            )

        student = self.student_repo.get_by_school_id(normalized_id)
        if student is None:
            self.rate_limiter.record_login_attempt(rate_limit_key, success=False)
            return AuthResult(success=False, error='Invalid School ID or password')

        password_is_valid = student.check_password(password)
        if not password_is_valid and student.password_hash:
            password_is_valid = compare_digest(student.password_hash, password)
            if password_is_valid:
                student.set_password(password)
                student.save(update_fields=['password_hash'])

        if not password_is_valid:
            self.rate_limiter.record_login_attempt(rate_limit_key, success=False)
            return AuthResult(success=False, error='Invalid School ID or password')

        request.session['user_type'] = 'student'
        request.session['student_id'] = student.id
        request.session['student_id_str'] = student.student_id
        request.session['student_name'] = student.get_full_name()
        request.session.modified = True
        self.rate_limiter.record_login_attempt(rate_limit_key, success=True)
        return AuthResult(success=True, user=student, user_type='student')

    def authenticate_unified(self, request: HttpRequest, username: str, password: str) -> AuthResult:
        """Authenticate and detect role: superadmin, school_admin, or teacher."""
        canonical_username = self._resolve_username_case_insensitive(username)
        user = authenticate(request, username=canonical_username, password=password)
        if user is None:
            return AuthResult(success=False, error='Invalid username or password')

        if user.is_superuser:
            login(request, user)
            request.session['user_type'] = 'superadmin'
            return AuthResult(success=True, user=user, user_type='superadmin')

        try:
            school_admin = SchoolAdmin.objects.get(user=user)
            login(request, user)
            request.session['user_type'] = 'school_admin'
            request.session['school_id'] = school_admin.school_id
            return AuthResult(success=True, user=school_admin, user_type='school_admin')
        except SchoolAdmin.DoesNotExist:
            pass

        teacher = Teacher.objects.filter(user=user).first()
        if teacher is not None:
            login(request, user)
            request.session['user_type'] = 'teacher'
            request.session['user_id'] = user.id
            request.session['school_id'] = teacher.school_id
            return AuthResult(success=True, user=teacher, user_type='teacher')

        return AuthResult(
            success=False,
            error='User account exists but has no assigned role',
        )

    def logout_user(self, request: HttpRequest) -> bool:
        user_type = request.session.get('user_type')
        if user_type in ('superadmin', 'school_admin', 'teacher'):
            logout(request)
        request.session.flush()
        return True

    def is_authenticated(self, request: HttpRequest) -> bool:
        user_type = request.session.get('user_type')
        if user_type in ('superadmin', 'school_admin', 'teacher'):
            return request.user.is_authenticated
        elif user_type == 'student':
            return 'student_id' in request.session
        return False

    def get_current_user_type(self, request: HttpRequest) -> Optional[str]:
        return request.session.get('user_type')

    def get_current_school_id(self, request: HttpRequest) -> Optional[int]:
        return request.session.get('school_id')

    def get_current_student(self, request: HttpRequest) -> Optional[Student]:
        if request.session.get('user_type') == 'student':
            student_id = request.session.get('student_id')
            if student_id:
                return self.student_repo.get_by_id(student_id)
        return None

    def get_current_teacher(self, request: HttpRequest) -> Optional[Teacher]:
        if request.session.get('user_type') == 'teacher' and request.user.is_authenticated:
            try:
                return Teacher.objects.get(user=request.user)
            except Teacher.DoesNotExist:
                return None
        return None

    def require_teacher(self, request: HttpRequest) -> bool:
        return (request.session.get('user_type') == 'teacher'
                and request.user.is_authenticated)

    def require_student(self, request: HttpRequest) -> bool:
        return (request.session.get('user_type') == 'student'
                and 'student_id' in request.session)
