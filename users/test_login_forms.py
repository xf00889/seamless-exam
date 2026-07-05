from django.test import SimpleTestCase

from users.forms import StudentLoginForm, TeacherLoginForm


class LoginFormsTests(SimpleTestCase):
    def test_teacher_login_allows_short_password_and_extended_username_chars(self):
        form = TeacherLoginForm(data={
            'username': 'teacher+one@example.com',
            'password': '1234',
        })

        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_student_login_allows_short_password_and_flexible_school_id(self):
        form = StudentLoginForm(data={
            'student_id': '2026.001/A',
            'password': '1234',
        })

        self.assertTrue(form.is_valid(), form.errors.as_json())
