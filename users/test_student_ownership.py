from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from users.forms import BulkStudentAssignmentForm, StudentClassAssignmentForm
from users.models import Class, ClassTeacher, GradeLevel, School, Section, Strand, Student, Teacher


def _login_as_teacher(client, user):
    client.login(username=user.username, password='Pass1234!')
    session = client.session
    session['user_type'] = 'teacher'
    session['user_id'] = user.id
    session.save()


class StudentOwnershipTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school = School.objects.create(name='Test School')
        cls.grade_11 = GradeLevel.objects.create(school=cls.school, name='Grade 11')
        cls.strand_stem = Strand.objects.create(school=cls.school, name='STEM')
        cls.section_a = Section.objects.create(school=cls.school, name='A')
        cls.section_b = Section.objects.create(school=cls.school, name='B')

        cls.teacher_a_user = User.objects.create_user(
            username='teacher_a', password='Pass1234!', first_name='Alice', last_name='A',
        )
        cls.teacher_b_user = User.objects.create_user(
            username='teacher_b', password='Pass1234!', first_name='Bob', last_name='B',
        )
        cls.teacher_a = Teacher.objects.create(user=cls.teacher_a_user, school=cls.school, department='Math')
        cls.teacher_b = Teacher.objects.create(user=cls.teacher_b_user, school=cls.school, department='Science')

        cls.class_a = Class.objects.create(
            school=cls.school, grade_level=cls.grade_11, strand=cls.strand_stem, section=cls.section_a,
        )
        cls.class_b = Class.objects.create(
            school=cls.school, grade_level=cls.grade_11, strand=cls.strand_stem, section=cls.section_b,
        )
        ClassTeacher.objects.create(class_obj=cls.class_a, teacher=cls.teacher_a)
        ClassTeacher.objects.create(class_obj=cls.class_b, teacher=cls.teacher_b)

        cls.student_a = Student.objects.create(
            school=cls.school, student_id='2024-001', first_name='Anna', last_name='A',
        )
        cls.student_a.set_password('pass1234')
        cls.student_a.class_assigned = cls.class_a
        cls.student_a.created_by = cls.teacher_a_user
        cls.student_a.save()

        cls.student_b = Student.objects.create(
            school=cls.school, student_id='2024-002', first_name='Ben', last_name='B',
        )
        cls.student_b.set_password('pass1234')
        cls.student_b.class_assigned = cls.class_b
        cls.student_b.created_by = cls.teacher_b_user
        cls.student_b.save()


class StudentAccountManagementListTests(StudentOwnershipTestBase):
    def test_teacher_a_only_sees_own_class_students(self):
        client = Client()
        _login_as_teacher(client, self.teacher_a_user)
        response = client.get(reverse('student_account_management'))
        self.assertEqual(response.status_code, 200)
        student_ids = [s.id for s in response.context['students']]
        self.assertIn(self.student_a.id, student_ids)
        self.assertNotIn(self.student_b.id, student_ids)

    def test_teacher_b_only_sees_own_class_students(self):
        client = Client()
        _login_as_teacher(client, self.teacher_b_user)
        response = client.get(reverse('student_account_management'))
        self.assertEqual(response.status_code, 200)
        student_ids = [s.id for s in response.context['students']]
        self.assertIn(self.student_b.id, student_ids)
        self.assertNotIn(self.student_a.id, student_ids)


class StudentClassAssignmentFormTests(StudentOwnershipTestBase):
    def test_dropdown_includes_school_students(self):
        form = StudentClassAssignmentForm(school_id=self.school.id)
        student_ids = list(form.fields['student'].queryset.values_list('id', flat=True))
        self.assertIn(self.student_a.id, student_ids)
        self.assertIn(self.student_b.id, student_ids)

    def test_no_school_means_empty_queryset(self):
        form = StudentClassAssignmentForm(school_id=None)
        self.assertEqual(form.fields['student'].queryset.count(), 0)


class BulkStudentAssignmentFormTests(StudentOwnershipTestBase):
    def test_dropdown_includes_school_students(self):
        form = BulkStudentAssignmentForm(school_id=self.school.id)
        student_ids = list(form.fields['students'].queryset.values_list('id', flat=True))
        self.assertIn(self.student_a.id, student_ids)
        self.assertIn(self.student_b.id, student_ids)


class StudentMutationAccessTests(StudentOwnershipTestBase):
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
