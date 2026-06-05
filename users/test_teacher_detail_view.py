"""
Smoke tests for SuperAdminTeacherDetailView. The view previously crashed
with FieldError because it used Exam.objects.filter(teacher=...) on a
model whose FK is named created_by. These tests guard against regression.
"""
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from users.models import Class, Student, Teacher


class SuperAdminTeacherDetailSmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username='root', password='Pass1234!', email='root@example.com',
        )
        cls.teacher_user = User.objects.create_user(
            username='t1', password='Pass1234!', first_name='Test', last_name='Teacher',
        )
        cls.teacher = Teacher.objects.create(user=cls.teacher_user, department='Math')
        cls.student = Student.objects.create(
            school_id='2024-001', first_name='Anna', last_name='A',
        )
        cls.student.created_by = cls.teacher
        cls.student.save()

    def test_detail_view_renders_for_superadmin(self):
        client = Client()
        client.login(username='root', password='Pass1234!')
        response = client.get(
            reverse('superadmin_teacher_detail', args=[self.teacher.user.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Teacher')
        # Hero avatar must have its color class and initials rendered
        # (this catches missing extra_css blocks in the base layout).
        self.assertContains(response, 'td-avatar ')
        self.assertContains(response, '>TT<')
        # The empty-state wrapper class must be present in the CSS (not just
        # referenced in the template) — if the extra_css block is missing
        # from the base, the styles will not be linked.
        self.assertIn('td-empty-icon', str(response.content))

    def test_detail_view_404_for_missing_teacher(self):
        client = Client()
        client.login(username='root', password='Pass1234!')
        response = client.get(reverse('superadmin_teacher_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)


class SuperAdminTeacherDetailFilterTests(TestCase):
    """The student table on the teacher detail page supports search,
    class filter, and sort. These tests verify each one in isolation."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username='root', password='Pass1234!', email='root@example.com',
        )
        cls.teacher_user = User.objects.create_user(
            username='t1', password='Pass1234!', first_name='Test', last_name='Teacher',
        )
        cls.teacher = Teacher.objects.create(user=cls.teacher_user, department='Math')

        # Two classes
        cls.class_alpha = Class.objects.create(
            grade_level='Grade 11', strand='STEM', section='Alpha', teacher=cls.teacher,
        )
        cls.class_beta = Class.objects.create(
            grade_level='Grade 12', strand='ABM', section='Beta', teacher=cls.teacher,
        )

        # Three students: assigned to alpha, assigned to beta, unassigned
        def _make_student(school_id, first, last, klass):
            s = Student.objects.create(school_id=school_id, first_name=first, last_name=last)
            s.created_by = cls.teacher
            s.class_assigned = klass
            s.save()
            return s

        cls.alpha_student = _make_student('2024-001', 'Alice', 'Anderson', cls.class_alpha)
        cls.beta_student = _make_student('2024-002', 'Bob', 'Brown', cls.class_beta)
        cls.unassigned_student = _make_student('2024-003', 'Carla', 'Carter', None)

    def _get(self, **params):
        client = Client()
        client.login(username='root', password='Pass1234!')
        url = reverse('superadmin_teacher_detail', args=[self.teacher.user.pk])
        if params:
            url = url + '?' + '&'.join(f'{k}={v}' for k, v in params.items())
        return client.get(url)

    def test_filter_by_class_alpha(self):
        response = self._get(**{'class': self.class_alpha.id})
        self.assertEqual(response.status_code, 200)
        ids = [s.id for s in response.context['students']]
        self.assertIn(self.alpha_student.id, ids)
        self.assertNotIn(self.beta_student.id, ids)
        self.assertNotIn(self.unassigned_student.id, ids)

    def test_filter_unassigned(self):
        response = self._get(**{'class': 'unassigned'})
        self.assertEqual(response.status_code, 200)
        ids = [s.id for s in response.context['students']]
        self.assertIn(self.unassigned_student.id, ids)
        self.assertNotIn(self.alpha_student.id, ids)
        self.assertNotIn(self.beta_student.id, ids)

    def test_search_by_name(self):
        response = self._get(search='Alice')
        self.assertEqual(response.status_code, 200)
        ids = [s.id for s in response.context['students']]
        self.assertEqual(ids, [self.alpha_student.id])

    def test_sort_by_name_asc(self):
        response = self._get(sort='name', dir='asc')
        self.assertEqual(response.status_code, 200)
        ordered = list(response.context['students'])
        names = [s.last_name for s in ordered]
        self.assertEqual(names, sorted(names))

    def test_clear_filters_button_present(self):
        response = self._get(search='Bob')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Clear')

    def test_total_attempts_aggregate_is_zero_by_default(self):
        response = self._get()
        self.assertEqual(response.context['total_attempts'], 0)
