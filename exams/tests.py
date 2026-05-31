from io import BytesIO
import html
import json
import re

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from docx import Document

from attempts.models import Attempt, AttemptStatus
from exams.models import Exam, Question, QuestionType
from users.models import Class as SchoolClass, Student, Teacher
from exams.models import ExamClassAssignment


def _container_text(container):
    parts = []
    for paragraph in container.paragraphs:
        if paragraph.text:
            parts.append(paragraph.text)
    for table in container.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text:
                    parts.append(cell.text)
    return "\n".join(parts)


def _document_text(document):
    parts = []
    for paragraph in document.paragraphs:
        if paragraph.text:
            parts.append(paragraph.text)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text:
                    parts.append(cell.text)
    return "\n".join(parts)


def _section_xml(section_part):
    return section_part._element.xml


class ExamEditPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teacher1',
            password='testpass123',
            first_name='Test',
            last_name='Teacher',
        )
        self.teacher = Teacher.objects.create(user=self.user, department='Science')
        self.exam = Exam.objects.create(
            title='Geology Quiz',
            subject='Science',
            duration_minutes=60,
            created_by=self.teacher,
        )
        self.question = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.MCQ,
            question_text='What is the main process of rock formation?',
            options=[
                {'key': 'A', 'value': 'Erosion'},
                {'key': 'B', 'value': 'Weathering'},
            ],
            correct_answer='B',
            points=1,
            order_index=0,
        )

        self.client.force_login(self.user)
        session = self.client.session
        session['user_type'] = 'teacher'
        session.save()

    def test_exam_edit_page_embeds_questions_as_a_json_array(self):
        response = self.client.get(reverse('exam_edit', args=[self.exam.id]))

        self.assertEqual(response.status_code, 200)

        match = re.search(
            r'<script id="questions-data" type="application/json">(.*?)</script>',
            response.content.decode('utf-8'),
            re.DOTALL,
        )
        self.assertIsNotNone(match, 'questions-data JSON script was not rendered')

        questions_payload = json.loads(html.unescape(match.group(1)))

        self.assertIsInstance(questions_payload, list)
        self.assertEqual(len(questions_payload), 1)
        self.assertEqual(questions_payload[0]['id'], self.question.id)
        self.assertEqual(questions_payload[0]['text'], self.question.question_text)


class ExamDetailPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teacher2',
            password='testpass123',
            first_name='Detail',
            last_name='Teacher',
        )
        self.teacher = Teacher.objects.create(user=self.user, department='Mathematics')
        self.exam = Exam.objects.create(
            title='Algebra Quiz',
            subject='Math',
            duration_minutes=45,
            description='Linear equations and factoring.',
            created_by=self.teacher,
        )
        self.school_class = SchoolClass.objects.create(
            grade_level='Grade 10',
            strand='STEM',
            section='A',
            teacher=self.teacher,
        )
        ExamClassAssignment.objects.create(exam=self.exam, class_assigned=self.school_class)
        self.student = Student.objects.create(
            school_id='S-1001',
            first_name='Ana',
            last_name='Lopez',
            password_hash='legacy',
            class_assigned=self.school_class,
        )
        self.question = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.TRUE_FALSE,
            question_text='Linear equations always have one solution.',
            correct_answer=True,
            points=2,
            order_index=0,
        )
        Attempt.objects.create(
            student=self.student,
            exam=self.exam,
            total_score=1.50,
            status=AttemptStatus.SUBMITTED,
            submitted_at=timezone.now(),
        )

        self.client.force_login(self.user)
        session = self.client.session
        session['user_type'] = 'teacher'
        session.save()

    def test_exam_detail_page_shows_exam_overview_and_summary(self):
        response = self.client.get(reverse('exam_detail', args=[self.exam.id]))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        self.assertContains(response, 'Exam Details: Algebra Quiz')
        self.assertContains(response, 'Edit Exam')
        self.assertContains(response, 'Edit Questions')
        self.assertContains(response, 'View Takers')
        self.assertContains(response, 'Export Word')
        self.assertContains(response, 'Class Summary')
        self.assertContains(response, 'Taker Summary')
        self.assertContains(response, self.question.question_text)
        self.assertContains(response, 'Grade 10 - STEM - A')
        self.assertContains(response, 'Ana Lopez')
        self.assertContains(response, 'Questions')
        self.assertContains(response, 'Accessible Students')
        self.assertContains(response, 'Recent Takers')
        self.assertIn('reopenModal', content)


class ExamExportWordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teacher3',
            password='testpass123',
            first_name='Export',
            last_name='Teacher',
        )
        self.teacher = Teacher.objects.create(user=self.user, department='English')
        self.exam = Exam.objects.create(
            title='Literature Quiz',
            subject='English',
            duration_minutes=30,
            description='Poetry and prose.',
            created_by=self.teacher,
        )
        Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.MCQ,
            question_text='Which literary device compares two unlike things using "like" or "as"?',
            options=[
                {'key': 'A', 'value': 'Metaphor'},
                {'key': 'B', 'value': 'Simile'},
            ],
            correct_answer='B',
            points=1,
            order_index=0,
        )

        self.client.force_login(self.user)
        session = self.client.session
        session['user_type'] = 'teacher'
        session.save()

    def test_exam_export_word_contains_header_footer_and_questions(self):
        response = self.client.get(reverse('exam_export_word', args=[self.exam.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        )

        document = Document(BytesIO(response.content))
        header_xml = _section_xml(document.sections[0].header)
        footer_xml = _section_xml(document.sections[0].footer)
        body_text = _document_text(document)

        self.assertIn('School Logo', header_xml)
        self.assertNotIn('EXAMINATION PAPER', header_xml)
        self.assertIn('Literature Quiz', body_text)
        self.assertIn('Generated by: seamless.dpdns.org', footer_xml)
        self.assertIn('Literature Quiz', body_text)
        self.assertIn('Which literary device compares two unlike things using "like" or "as"?', body_text)
        self.assertIn('Metaphor', body_text)
        self.assertIn('Simile', body_text)


class MpsExportWordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teacher4',
            password='testpass123',
            first_name='MPS',
            last_name='Teacher',
        )
        self.teacher = Teacher.objects.create(user=self.user, department='Science')
        self.exam = Exam.objects.create(
            title='Physics Check',
            subject='Science',
            duration_minutes=45,
            created_by=self.teacher,
        )
        self.school_class = SchoolClass.objects.create(
            grade_level='Grade 9',
            strand='STEM',
            section='B',
            teacher=self.teacher,
        )
        ExamClassAssignment.objects.create(exam=self.exam, class_assigned=self.school_class)
        self.student = Student.objects.create(
            school_id='S-2001',
            first_name='Ben',
            last_name='Cruz',
            password_hash='legacy',
            class_assigned=self.school_class,
        )
        self.question = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.TRUE_FALSE,
            question_text='Energy can be created from nothing.',
            correct_answer=False,
            points=1,
            order_index=0,
        )
        self.attempt = Attempt.objects.create(
            student=self.student,
            exam=self.exam,
            total_score=0,
            status=AttemptStatus.GRADED,
            submitted_at=timezone.now(),
        )
        from attempts.models import Answer

        Answer.objects.create(
            attempt=self.attempt,
            question=self.question,
            answer_text={'value': True},
            is_correct=False,
            points_earned=0,
            graded_at=timezone.now(),
        )

        self.client.force_login(self.user)
        session = self.client.session
        session['user_type'] = 'teacher'
        session.save()

    def test_mps_export_word_contains_header_and_footer(self):
        response = self.client.get(reverse('mps_export_word', args=[self.exam.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        )

        document = Document(BytesIO(response.content))
        header_xml = _section_xml(document.sections[0].header)
        footer_xml = _section_xml(document.sections[0].footer)

        self.assertIn('School Logo', header_xml)
        self.assertNotIn('MEAN PERCENTAGE SCORE (MPS) REPORT', header_xml)
        self.assertIn('Generated by: seamless.dpdns.org', footer_xml)
