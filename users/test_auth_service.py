from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import cache
from django.test import RequestFactory, TestCase

from services.auth_service import AuthenticationService
from users.models import School, Student, Teacher


class AuthenticationServiceTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.auth_service = AuthenticationService()
        cache.clear()
        self.school = School.objects.create(name='Test School')

    def _build_request(self, path: str):
        request = self.factory.post(path)
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        request.user = AnonymousUser()
        return request

    def test_teacher_login_is_case_insensitive(self):
        user = User.objects.create_user(
            username='TeacherOne',
            password='SecretPass123',
            first_name='Teacher',
            last_name='One',
        )
        Teacher.objects.create(user=user, school=self.school, department='Science')

        request = self._build_request('/users/teacher/login/')
        result = self.auth_service.authenticate_teacher(
            request=request,
            username='teacherone',
            password='SecretPass123',
        )

        self.assertTrue(result.success)
        self.assertEqual(result.user.user_id, user.id)
        self.assertEqual(request.session.get('user_type'), 'teacher')

    def test_teacher_with_staff_flag_can_login(self):
        staff_user = User.objects.create_user(
            username='schooladmin',
            password='SecretPass123',
            is_staff=True,
        )
        Teacher.objects.create(user=staff_user, school=self.school, department='Admin')

        request = self._build_request('/users/teacher/login/')
        result = self.auth_service.authenticate_teacher(
            request=request,
            username='schooladmin',
            password='SecretPass123',
        )

        self.assertTrue(result.success)
        self.assertEqual(request.session.get('user_type'), 'teacher')

    def test_user_without_teacher_profile_cannot_login(self):
        staff_user = User.objects.create_user(
            username='noprofile',
            password='SecretPass123',
            is_staff=True,
        )

        request = self._build_request('/users/teacher/login/')
        result = self.auth_service.authenticate_teacher(
            request=request,
            username='noprofile',
            password='SecretPass123',
        )

        self.assertFalse(result.success)
        self.assertIn('not registered as a teacher', result.error)

    def test_student_login_is_case_insensitive(self):
        student = Student.objects.create(
            school=self.school,
            student_id='STU001',
            first_name='Alice',
            last_name='Smith',
        )
        student.set_password('StudentPass123')
        student.save()

        request = self._build_request('/users/student/login/')
        result = self.auth_service.authenticate_student(
            request=request,
            student_id='stu001',
            password='StudentPass123',
        )

        self.assertTrue(result.success)
        self.assertEqual(result.user.id, student.id)
        self.assertEqual(request.session.get('user_type'), 'student')

    def test_student_legacy_plaintext_password_is_migrated(self):
        student = Student.objects.create(
            school=self.school,
            student_id='LEG001',
            first_name='Legacy',
            last_name='Student',
            password_hash='legacyPass123',
        )

        request = self._build_request('/users/student/login/')
        result = self.auth_service.authenticate_student(
            request=request,
            student_id='LEG001',
            password='legacyPass123',
        )
        student.refresh_from_db()

        self.assertTrue(result.success)
        self.assertNotEqual(student.password_hash, 'legacyPass123')
        self.assertTrue(student.password_hash.startswith('pbkdf2_'))

    def test_teacher_login_is_rate_limited_after_failed_attempts(self):
        user = User.objects.create_user(
            username='RateLimitedTeacher',
            password='SecretPass123',
            first_name='Rate',
            last_name='Limited',
        )
        Teacher.objects.create(user=user, school=self.school, department='Science')

        for _ in range(self.auth_service.rate_limiter.LOGIN_ATTEMPT_LIMIT):
            request = self._build_request('/users/teacher/login/')
            result = self.auth_service.authenticate_teacher(
                request=request,
                username='ratelimitedteacher',
                password='wrong-password',
            )

            self.assertFalse(result.success)

        blocked_request = self._build_request('/users/teacher/login/')
        blocked_result = self.auth_service.authenticate_teacher(
            request=blocked_request,
            username='ratelimitedteacher',
            password='SecretPass123',
        )

        self.assertFalse(blocked_result.success)
        self.assertIn('Too many login attempts', blocked_result.error)

    def test_student_login_resets_rate_limit_after_success(self):
        student = Student.objects.create(
            school=self.school,
            student_id='RESET001',
            first_name='Reset',
            last_name='Student',
        )
        student.set_password('StudentPass123')
        student.save()

        for _ in range(2):
            request = self._build_request('/users/student/login/')
            result = self.auth_service.authenticate_student(
                request=request,
                student_id='RESET001',
                password='wrong-password',
            )

            self.assertFalse(result.success)

        success_request = self._build_request('/users/student/login/')
        success_result = self.auth_service.authenticate_student(
            request=success_request,
            student_id='RESET001',
            password='StudentPass123',
        )

        self.assertTrue(success_result.success)

        followup_request = self._build_request('/users/student/login/')
        followup_result = self.auth_service.authenticate_student(
            request=followup_request,
            student_id='RESET001',
            password='wrong-password',
        )

        self.assertFalse(followup_result.success)
