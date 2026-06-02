"""
Tests for the AI essay grader feature.

Covers the service (`services.ai_essay_grader_service`) and the
`ai_grade_essay_view` endpoint end-to-end (with mocked OpenRouter calls).
"""
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User

from users.models import Student, Teacher, Class as SchoolClass
from exams.models import Exam, Question, QuestionType
from attempts.models import Attempt, Answer, AttemptStatus

from services import ai_essay_grader_service
from services.ai_essay_grader_service import (
    build_essay_grader_prompt,
    grade_essay_with_ai,
    _extract_answer_text,
    _normalize_score,
    _is_blank,
)


def _mock_ai_response(content):
    """Build a MagicMock that mimics a successful OpenRouter chat completion."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        'choices': [{'message': {'content': content}}]
    }
    return mock_resp


def _mock_ai_http_error(status_code):
    """Build a MagicMock that mimics an HTTP error response."""
    from requests.exceptions import HTTPError
    err = HTTPError(f'{status_code} error')
    err.response = MagicMock()
    err.response.status_code = status_code
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = err
    return mock_resp


class AIEssayGraderServiceUnitTests(TestCase):
    """Unit tests for the helper functions and prompt builder."""

    def test_extract_answer_text_handles_dict_value_key(self):
        self.assertEqual(_extract_answer_text({'value': 'hello'}), 'hello')

    def test_extract_answer_text_handles_dict_answer_key(self):
        self.assertEqual(_extract_answer_text({'answer': 'world'}), 'world')

    def test_extract_answer_text_handles_string(self):
        self.assertEqual(_extract_answer_text('plain text'), 'plain text')

    def test_extract_answer_text_handles_empty(self):
        self.assertEqual(_extract_answer_text(None), '')
        self.assertEqual(_extract_answer_text({}), '')
        self.assertEqual(_extract_answer_text(''), '')

    def test_is_blank_detects_whitespace(self):
        self.assertTrue(_is_blank(''))
        self.assertTrue(_is_blank('   '))
        self.assertTrue(_is_blank('\n\t  '))
        self.assertFalse(_is_blank('x'))
        self.assertFalse(_is_blank(' 0 '))  # "0" is a valid answer

    def test_normalize_score_clamps_to_max(self):
        self.assertEqual(_normalize_score(10, 5), 5.0)
        self.assertEqual(_normalize_score(-2, 5), 0.0)
        self.assertEqual(_normalize_score(3.5, 5), 3.5)
        self.assertEqual(_normalize_score('bad', 5), 0.0)
        self.assertEqual(_normalize_score(None, 5), 0.0)

    def test_prompt_includes_question_and_answer(self):
        prompt = build_essay_grader_prompt(
            question_text='What causes the seasons?',
            answer_text='Earth tilts on its axis.',
            max_points=5,
            exam_title='Science 101',
            subject='Science',
            grade_level='Grade 5',
        )
        self.assertIn('What causes the seasons?', prompt)
        self.assertIn('Earth tilts on its axis.', prompt)
        self.assertIn('LENIENT', prompt)
        self.assertIn('BLANK', prompt)
        self.assertIn('OFF-TOPIC', prompt)
        self.assertIn('points_earned', prompt)
        self.assertIn('Science 101', prompt)

    def test_prompt_empty_when_question_missing(self):
        prompt = build_essay_grader_prompt(
            question_text='',
            answer_text='something',
            max_points=5,
        )
        self.assertEqual(prompt, '')

    def test_prompt_empty_when_answer_blank(self):
        prompt = build_essay_grader_prompt(
            question_text='A question',
            answer_text='   ',
            max_points=5,
        )
        self.assertEqual(prompt, '')


class AIEssayGraderServiceIntegrationTests(TestCase):
    """Tests for grade_essay_with_ai() with mocked OpenRouter requests."""

    @patch('services.ai_essay_grader_service.requests.post')
    def test_happy_path_returns_suggestion(self, mock_post):
        mock_post.return_value = _mock_ai_response(
            '{"points_earned": 4, "feedback": "Good effort!", "reasoning": "Mostly on-topic.", '
            '"is_blank": false, "is_off_topic": false, '
            '"breakdown": {"relevance": 8, "correctness": 7, "depth": 6}}'
        )
        result = grade_essay_with_ai(
            question_text='Explain photosynthesis.',
            answer_text='Plants convert sunlight to energy.',
            max_points=5,
        )
        self.assertNotIn('error', result)
        self.assertEqual(result['points_earned'], 4.0)
        self.assertEqual(result['feedback'], 'Good effort!')
        self.assertEqual(result['breakdown']['relevance'], 8)
        mock_post.assert_called_once()

    @patch('services.ai_essay_grader_service.requests.post')
    def test_strips_markdown_fences(self, mock_post):
        mock_post.return_value = _mock_ai_response(
            '```json\n{"points_earned": 3, "feedback": "ok", "reasoning": "ok", '
            '"is_blank": false, "is_off_topic": false, '
            '"breakdown": {"relevance": 5, "correctness": 5, "depth": 5}}\n```'
        )
        result = grade_essay_with_ai(
            question_text='Q',
            answer_text='A',
            max_points=5,
        )
        self.assertNotIn('error', result)
        self.assertEqual(result['points_earned'], 3.0)

    def test_blank_answer_returns_zero_without_ai_call(self):
        result = grade_essay_with_ai(
            question_text='Q',
            answer_text='   ',
            max_points=5,
        )
        self.assertEqual(result['points_earned'], 0)
        self.assertTrue(result['is_blank'])
        self.assertFalse(result['is_off_topic'])

    @patch('services.ai_generation_service.get_ai_config')
    def test_no_api_key_returns_friendly_error(self, mock_config):
        mock_config.return_value = {'api_key': '', 'base_url': 'x', 'model': 'y'}
        result = grade_essay_with_ai(
            question_text='Q',
            answer_text='A',
            max_points=5,
        )
        self.assertEqual(result.get('code'), 'no_api_key')
        self.assertIn('AI service is not configured', result.get('error', ''))

    @patch('services.ai_essay_grader_service.requests.post')
    def test_http_401_returns_auth_error(self, mock_post):
        mock_post.return_value = _mock_ai_http_error(401)
        result = grade_essay_with_ai(
            question_text='Q',
            answer_text='A',
            max_points=5,
        )
        self.assertEqual(result.get('code'), 'auth_failed')

    @patch('services.ai_essay_grader_service.requests.post')
    def test_http_429_returns_rate_limited(self, mock_post):
        mock_post.return_value = _mock_ai_http_error(429)
        result = grade_essay_with_ai(
            question_text='Q',
            answer_text='A',
            max_points=5,
        )
        self.assertEqual(result.get('code'), 'rate_limited')

    @patch('services.ai_essay_grader_service.requests.post')
    def test_bad_json_returns_parse_error(self, mock_post):
        mock_post.return_value = _mock_ai_response('not json at all')
        result = grade_essay_with_ai(
            question_text='Q',
            answer_text='A',
            max_points=5,
        )
        self.assertEqual(result.get('code'), 'parse_failed')

    def test_no_points_returns_error(self):
        result = grade_essay_with_ai(
            question_text='Q',
            answer_text='A',
            max_points=0,
        )
        self.assertEqual(result.get('code'), 'no_points')

    @patch('services.ai_essay_grader_service.requests.post')
    def test_score_above_max_clamped(self, mock_post):
        mock_post.return_value = _mock_ai_response(
            '{"points_earned": 99, "feedback": "x", "reasoning": "x", '
            '"is_blank": false, "is_off_topic": false, '
            '"breakdown": {"relevance": 9, "correctness": 9, "depth": 9}}'
        )
        result = grade_essay_with_ai(
            question_text='Q',
            answer_text='A',
            max_points=5,
        )
        self.assertEqual(result['points_earned'], 5.0)


class AIGradeEssayViewTests(TestCase):
    """End-to-end tests for the ai_grade_essay_view endpoint."""

    def setUp(self):
        self.teacher_user = User.objects.create_user(username='aitest_teacher', password='pass123')
        self.teacher = Teacher.objects.create(user=self.teacher_user, department='Science')

        self.other_user = User.objects.create_user(username='aitest_other', password='pass123')
        self.other_teacher = Teacher.objects.create(user=self.other_user, department='Other')

        self.student = Student.objects.create(school_id='3001', first_name='Bob', last_name='Cruz')

        self.exam = Exam.objects.create(
            title='AI Test Exam',
            duration_minutes=60,
            is_active=True,
            created_by=self.teacher,
        )
        self.essay_question = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.ESSAY,
            question_text='Explain the water cycle.',
            points=5,
            correct_answer={},
        )
        self.mcq_question = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.MCQ,
            question_text='Pick A.',
            options=[{'key': 'A', 'value': 'a'}],
            correct_answer='A',
            points=1,
        )
        self.attempt = Attempt.objects.create(
            student=self.student,
            exam=self.exam,
            status=AttemptStatus.SUBMITTED,
            total_score=0,
            submitted_at=timezone.now(),
        )
        self.essay_answer = Answer.objects.create(
            attempt=self.attempt,
            question=self.essay_question,
            answer_text={'value': 'Water evaporates and condenses.'},
        )
        self.mcq_answer = Answer.objects.create(
            attempt=self.attempt,
            question=self.mcq_question,
            answer_text={'value': 'A'},
        )
        self.url = reverse('ai_grade_essay', args=[self.essay_answer.id])
        self.mcq_url = reverse('ai_grade_essay', args=[self.mcq_answer.id])

    def _login_as(self, user):
        self.client.force_login(user)
        session = self.client.session
        session['user_type'] = 'teacher'
        session['user_id'] = user.id
        session.save()

    def test_unauthenticated_returns_401(self):
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 401)
        self.assertIn('error', resp.json())

    def test_wrong_teacher_returns_403(self):
        self._login_as(self.other_teacher.user)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)
        self.assertIn('error', resp.json())

    def test_non_essay_returns_400(self):
        self._login_as(self.teacher_user)
        resp = self.client.post(self.mcq_url)
        self.assertEqual(resp.status_code, 400)
        self.assertIn('essay', resp.json()['error'].lower())

    def test_get_method_rejected(self):
        self._login_as(self.teacher_user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 405)

    def test_blank_answer_returns_zero_in_json(self):
        self._login_as(self.teacher_user)
        self.essay_answer.answer_text = {'value': '   '}
        self.essay_answer.save()
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['points_earned'], 0)
        self.assertTrue(data['is_blank'])

    @patch('services.ai_essay_grader_service.requests.post')
    def test_happy_path_returns_suggestion(self, mock_post):
        mock_post.return_value = _mock_ai_response(
            '{"points_earned": 4, "feedback": "Great answer.", "reasoning": "On-topic and clear.", '
            '"is_blank": false, "is_off_topic": false, '
            '"breakdown": {"relevance": 8, "correctness": 9, "depth": 7}}'
        )
        self._login_as(self.teacher_user)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['points_earned'], 4.0)
        self.assertEqual(data['max_points'], 5.0)
        self.assertEqual(data['feedback'], 'Great answer.')
        self.assertEqual(data['breakdown']['correctness'], 9)
        self.assertNotEqual(data['model_used'], '')

    @patch('services.ai_essay_grader_service.requests.post')
    def test_no_api_key_returns_503(self, mock_post):
        with patch('services.ai_generation_service.get_ai_config') as mock_cfg:
            mock_cfg.return_value = {'api_key': '', 'base_url': 'x', 'model': 'y'}
            self._login_as(self.teacher_user)
            resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.json()['code'], 'no_api_key')

    @patch('services.ai_essay_grader_service.requests.post')
    def test_view_does_not_save_grade(self, mock_post):
        """The AI endpoint must NOT mutate the answer — teacher still confirms via Save Grade."""
        mock_post.return_value = _mock_ai_response(
            '{"points_earned": 3, "feedback": "x", "reasoning": "x", '
            '"is_blank": false, "is_off_topic": false, '
            '"breakdown": {"relevance": 5, "correctness": 5, "depth": 5}}'
        )
        self._login_as(self.teacher_user)
        self.client.post(self.url)
        self.essay_answer.refresh_from_db()
        # The AI endpoint must NOT mark the answer as graded.
        self.assertIsNone(self.essay_answer.is_correct)
        self.assertIsNone(self.essay_answer.graded_at)
        # teacher_feedback defaults to '' (empty TextField)
        self.assertFalse(self.essay_answer.teacher_feedback)
