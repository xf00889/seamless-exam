"""
Tests for per-teacher student scoping.

Students are private to the teacher who created them. These tests verify:
- Teachers can only see their own students in the account management list.
- The Assign Student dropdown only shows the teacher's own students.
- The Bulk Assign dropdown only shows the teacher's own students.
- DetailView / ResetView / DeleteView reject non-owned students.
- Student creation records the creator as created_by.
"""
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from users.forms import (
    BulkStudentAssignmentForm,
    StudentClassAssignmentForm,
    StudentCreationForm,
)
from users.models import Class, Student, Teacher


def _login_as_teacher(client, user):
    """client.login only sets auth — the views also require session user_type."""
    client.login(username=user.username, password='Pass1234!')
    session = client.session
    session['user_type'] = 'teacher'
    session['user_id'] = user.id
    session.save()


class StudentOwnershipTestBase(TestCase):
    """Two teachers, two classes, two students owned by different teachers."""

    @classmethod
    def setUpTestData(cls):
        cls.teacher_a_user = User.objects.create_user(
            username='teacher_a', password='Pass1234!', first_name='Alice', last_name='A',
        )
        cls.teacher_b_user = User.objects.create_user(
            username='teacher_b', password='Pass1234!', first_name='Bob', last_name='B',
        )
        cls.teacher_a = Teacher.objects.create(user=cls.teacher_a_user, department='Math')
        cls.teacher_b = Teacher.objects.create(user=cls.teacher_b_user, department='Science')

        cls.class_a = Class.objects.create(
            grade_level='Grade 11', strand='STEM', section='A', teacher=cls.teacher_a,
        )
        cls.class_b = Class.objects.create(
            grade_level='Grade 11', strand='STEM', section='B', teacher=cls.teacher_b,
        )

        cls.student_a = Student.objects.create(
            school_id='2024-001', first_name='Anna', last_name='A',
        )
        cls.student_a.set_password('pass1234')
        cls.student_a.created_by = cls.teacher_a
        cls.student_a.save()

        cls.student_b = Student.objects.create(
            school_id='2024-002', first_name='Ben', last_name='B',
        )
        cls.student_b.set_password('pass1234')
        cls.student_b.created_by = cls.teacher_b
        cls.student_b.save()


class StudentAccountManagementListTests(StudentOwnershipTestBase):
    def test_teacher_a_only_sees_own_students(self):
        client = Client()
        _login_as_teacher(client, self.teacher_a_user)
        response = client.get(reverse('student_account_management'))
        self.assertEqual(response.status_code, 200)
        student_ids = [s.id for s in response.context['students']]
        self.assertIn(self.student_a.id, student_ids)
        self.assertNotIn(self.student_b.id, student_ids)

    def test_teacher_b_only_sees_own_students(self):
        client = Client()
        _login_as_teacher(client, self.teacher_b_user)
        response = client.get(reverse('student_account_management'))
        self.assertEqual(response.status_code, 200)
        student_ids = [s.id for s in response.context['students']]
        self.assertIn(self.student_b.id, student_ids)
        self.assertNotIn(self.student_a.id, student_ids)


class StudentCreationFormTests(StudentOwnershipTestBase):
    def test_new_student_is_scoped_to_creator(self):
        client = Client()
        _login_as_teacher(client, self.teacher_a_user)
        response = client.post(
            reverse('student_account_management'),
            {
                'school_id': '2024-100',
                'first_name': 'Carla',
                'last_name': 'C',
            },
        )
        self.assertEqual(response.status_code, 302)
        created = Student.objects.get(school_id='2024-100')
        self.assertEqual(created.created_by, self.teacher_a)


class StudentClassAssignmentFormTests(StudentOwnershipTestBase):
    def test_dropdown_only_includes_own_students(self):
        form = StudentClassAssignmentForm(teacher=self.teacher_a)
        student_ids = list(form.fields['student'].queryset.values_list('id', flat=True))
        self.assertIn(self.student_a.id, student_ids)
        self.assertNotIn(self.student_b.id, student_ids)

    def test_no_teacher_means_empty_queryset(self):
        form = StudentClassAssignmentForm(teacher=None)
        self.assertEqual(form.fields['student'].queryset.count(), 0)


class BulkStudentAssignmentFormTests(StudentOwnershipTestBase):
    def test_dropdown_only_includes_own_students(self):
        form = BulkStudentAssignmentForm(teacher=self.teacher_a)
        student_ids = list(form.fields['students'].queryset.values_list('id', flat=True))
        self.assertIn(self.student_a.id, student_ids)
        self.assertNotIn(self.student_b.id, student_ids)


class StudentMutationOwnershipTests(StudentOwnershipTestBase):
    def test_other_teacher_cannot_view_detail(self):
        client = Client()
        _login_as_teacher(client, self.teacher_b_user)
        response = client.get(reverse('student_detail', args=[self.student_a.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('student_account_management'))

    def test_other_teacher_cannot_reset_password(self):
        client = Client()
        _login_as_teacher(client, self.teacher_b_user)
        response = client.post(reverse('student_reset_password', args=[self.student_a.id]))
        self.assertEqual(response.status_code, 302)
        self.student_a.refresh_from_db()
        self.assertTrue(self.student_a.check_password('pass1234'))

    def test_other_teacher_cannot_delete(self):
        client = Client()
        _login_as_teacher(client, self.teacher_b_user)
        response = client.post(reverse('student_delete', args=[self.student_a.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Student.objects.filter(pk=self.student_a.id).exists())

    def test_owner_can_view_detail(self):
        client = Client()
        _login_as_teacher(client, self.teacher_a_user)
        response = client.get(reverse('student_detail', args=[self.student_a.id]))
        self.assertEqual(response.status_code, 200)


class UnownedStudentTests(TestCase):
    """Students with NULL created_by (legacy data, e.g. unowned) are visible only to superadmin."""

    def test_unowned_student_invisible_to_all_teachers(self):
        teacher_user = User.objects.create_user(username='t1', password='Pass1234!')
        teacher = Teacher.objects.create(user=teacher_user, department='Math')

        student = Student.objects.create(
            school_id='2024-LEGACY', first_name='Legacy', last_name='L',
        )
        student.set_password('pass1234')
        student.save()  # created_by remains NULL

        client = Client()
        _login_as_teacher(client, teacher_user)
        response = client.get(reverse('student_account_management'))
        student_ids = [s.id for s in response.context['students']]
        self.assertNotIn(student.id, student_ids)
