import html
import json
import re

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from exams.models import Exam, Question, QuestionType
from users.models import Teacher


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
