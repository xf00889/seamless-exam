from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from services.auth_service import AuthenticationService
from users.models import Student, Teacher


class AuthenticationServiceTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.auth_service = AuthenticationService()

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
        Teacher.objects.create(user=user, department='Science')

        request = self._build_request('/users/teacher/login/')
        result = self.auth_service.authenticate_teacher(
            request=request,
            username='teacherone',
            password='SecretPass123',
        )

        self.assertTrue(result.success)
        self.assertEqual(result.user.user_id, user.id)
        self.assertEqual(request.session.get('user_type'), 'teacher')

    def test_staff_user_without_teacher_profile_can_login(self):
        staff_user = User.objects.create_user(
            username='schooladmin',
            password='SecretPass123',
            is_staff=True,
        )

        request = self._build_request('/users/teacher/login/')
        result = self.auth_service.authenticate_teacher(
            request=request,
            username='schooladmin',
            password='SecretPass123',
        )

        self.assertTrue(result.success)
        self.assertTrue(Teacher.objects.filter(user=staff_user).exists())
        self.assertEqual(request.session.get('user_type'), 'teacher')

    def test_student_login_is_case_insensitive(self):
        student = Student.objects.create(
            school_id='STU001',
            first_name='Alice',
            last_name='Smith',
        )
        student.set_password('StudentPass123')
        student.save()

        request = self._build_request('/users/student/login/')
        result = self.auth_service.authenticate_student(
            request=request,
            school_id='stu001',
            password='StudentPass123',
        )

        self.assertTrue(result.success)
        self.assertEqual(result.user.id, student.id)
        self.assertEqual(request.session.get('user_type'), 'student')

    def test_student_legacy_plaintext_password_is_migrated(self):
        student = Student.objects.create(
            school_id='LEG001',
            first_name='Legacy',
            last_name='Student',
            password_hash='legacyPass123',
        )

        request = self._build_request('/users/student/login/')
        result = self.auth_service.authenticate_student(
            request=request,
            school_id='LEG001',
            password='legacyPass123',
        )
        student.refresh_from_db()

        self.assertTrue(result.success)
        self.assertNotEqual(student.password_hash, 'legacyPass123')
        self.assertTrue(student.password_hash.startswith('pbkdf2_'))
