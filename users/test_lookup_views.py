import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from attempts.models import Attempt, AttemptStatus
from exams.models import Exam, ExamClassAssignment, Question, QuestionType
from users.models import Class as SchoolClass
from users.models import Student, Teacher, Quarter


class QuarterLookupViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teacher_lookup',
            password='testpass123',
            first_name='Lookup',
            last_name='Teacher',
        )
        self.teacher = Teacher.objects.create(user=self.user, department='Science')
        self.client.force_login(self.user)
        session = self.client.session
        session['user_type'] = 'teacher'
        session.save()

    def test_create_quarter_view_creates_quarter(self):
        response = self.client.post(
            reverse('create_quarter'),
            data=json.dumps({'name': '1st Quarter'}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Quarter.objects.filter(name='1st Quarter').exists())

    def test_update_quarter_view_renames_quarter(self):
        quarter = Quarter.objects.create(name='1st Quarter')

        response = self.client.post(
            reverse('update_quarter'),
            data=json.dumps({'id': quarter.id, 'name': 'Quarter 1'}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        quarter.refresh_from_db()
        self.assertEqual(quarter.name, 'Quarter 1')


class ClassDetailActionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teacher_class_detail',
            password='testpass123',
            first_name='Class',
            last_name='Teacher',
        )
        self.teacher = Teacher.objects.create(user=self.user, department='Science')
        self.school_class = SchoolClass.objects.create(
            grade_level='Grade 10',
            strand='STEM',
            section='A',
            teacher=self.teacher,
        )
        self.student = Student.objects.create(
            school_id='S-2001',
            first_name='Mia',
            last_name='Santos',
            class_assigned=self.school_class,
        )
        self.exam = Exam.objects.create(
            title='Quarter Test',
            duration_minutes=60,
            is_active=True,
            created_by=self.teacher,
        )
        Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.MCQ,
            question_text='What is 1 + 1?',
            options=[{'key': 'A', 'value': '1'}, {'key': 'B', 'value': '2'}],
            correct_answer='B',
            points=1,
        )
        ExamClassAssignment.objects.create(exam=self.exam, class_assigned=self.school_class)
        Attempt.objects.create(
            student=self.student,
            exam=self.exam,
            status=AttemptStatus.GRADED,
            total_score=1,
        )

        self.client.force_login(self.user)
        session = self.client.session
        session['user_type'] = 'teacher'
        session.save()

    def test_class_detail_links_student_and_exam_actions(self):
        response = self.client.get(reverse('class_detail', args=[self.school_class.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('student_detail', args=[self.student.id]))
        self.assertContains(response, reverse('exam_detail', args=[self.exam.id]))
        self.assertContains(response, 'title="View Student"')
        self.assertContains(response, 'title="View Exam"')
