"""
Tests for the attempts app.
Tests models, repositories, and services for exam attempts and answers.
"""
from django.test import TestCase
from django.utils import timezone
from users.models import Student, Teacher
from exams.models import Exam, Question, QuestionType
from attempts.models import Attempt, Answer, AttemptStatus
from repositories.attempt_repository import AttemptRepository
from repositories.answer_repository import AnswerRepository
from services.attempt_service import AttemptService
from services.answer_service import AnswerService
from django.contrib.auth.models import User


class AttemptModelTest(TestCase):
    """Test the Attempt model."""
    
    def setUp(self):
        """Set up test data."""
        # Create teacher
        user = User.objects.create_user(username='teacher1', password='pass123')
        self.teacher = Teacher.objects.create(user=user, department='CS')
        
        # Create student
        self.student = Student.objects.create(
            school_id='2024001',
            first_name='John',
            last_name='Doe'
        )
        self.student.set_password('password')
        self.student.save()
        
        # Create exam
        self.exam = Exam.objects.create(
            title='Test Exam',
            duration_minutes=60,
            is_active=True,
            created_by=self.teacher
        )
    
    def test_create_attempt(self):
        """Test creating an attempt."""
        attempt = Attempt.objects.create(
            student=self.student,
            exam=self.exam,
            status=AttemptStatus.IN_PROGRESS
        )
        
        self.assertIsNotNone(attempt.id)
        self.assertEqual(attempt.student, self.student)
        self.assertEqual(attempt.exam, self.exam)
        self.assertEqual(attempt.status, AttemptStatus.IN_PROGRESS)
        self.assertEqual(float(attempt.total_score), 0.0)
        self.assertIsNotNone(attempt.started_at)
        self.assertIsNone(attempt.submitted_at)
    
    def test_attempt_string_representation(self):
        """Test the string representation of an attempt."""
        attempt = Attempt.objects.create(
            student=self.student,
            exam=self.exam
        )
        
        expected = f"{self.student.get_full_name()} - {self.exam.title} ({attempt.status})"
        self.assertEqual(str(attempt), expected)


class AnswerModelTest(TestCase):
    """Test the Answer model."""
    
    def setUp(self):
        """Set up test data."""
        # Create teacher
        user = User.objects.create_user(username='teacher1', password='pass123')
        self.teacher = Teacher.objects.create(user=user, department='CS')
        
        # Create student
        self.student = Student.objects.create(
            school_id='2024001',
            first_name='John',
            last_name='Doe'
        )
        
        # Create exam
        self.exam = Exam.objects.create(
            title='Test Exam',
            duration_minutes=60,
            is_active=True,
            created_by=self.teacher
        )
        
        # Create question
        self.question = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.MCQ,
            question_text='What is 2+2?',
            options=[
                {'key': 'A', 'value': '3'},
                {'key': 'B', 'value': '4'},
                {'key': 'C', 'value': '5'}
            ],
            correct_answer={'value': 'B'},
            points=2.0
        )
        
        # Create attempt
        self.attempt = Attempt.objects.create(
            student=self.student,
            exam=self.exam
        )
    
    def test_create_answer(self):
        """Test creating an answer."""
        answer = Answer.objects.create(
            attempt=self.attempt,
            question=self.question,
            answer_text={'value': 'B'}
        )
        
        self.assertIsNotNone(answer.id)
        self.assertEqual(answer.attempt, self.attempt)
        self.assertEqual(answer.question, self.question)
        self.assertEqual(answer.answer_text, {'value': 'B'})
        self.assertIsNone(answer.is_correct)
        self.assertEqual(float(answer.points_earned), 0.0)
    
    def test_unique_constraint(self):
        """Test that an attempt can only have one answer per question."""
        Answer.objects.create(
            attempt=self.attempt,
            question=self.question,
            answer_text={'value': 'B'}
        )
        
        # Try to create another answer for the same attempt and question
        with self.assertRaises(Exception):
            Answer.objects.create(
                attempt=self.attempt,
                question=self.question,
                answer_text={'value': 'C'}
            )


class AttemptRepositoryTest(TestCase):
    """Test the AttemptRepository."""
    
    def setUp(self):
        """Set up test data."""
        self.repository = AttemptRepository()
        
        # Create teacher
        user = User.objects.create_user(username='teacher1', password='pass123')
        self.teacher = Teacher.objects.create(user=user, department='CS')
        
        # Create student
        self.student = Student.objects.create(
            school_id='2024001',
            first_name='John',
            last_name='Doe'
        )
        
        # Create exam
        self.exam = Exam.objects.create(
            title='Test Exam',
            duration_minutes=60,
            is_active=True,
            created_by=self.teacher
        )
    
    def test_get_by_student(self):
        """Test retrieving attempts by student."""
        attempt1 = Attempt.objects.create(student=self.student, exam=self.exam)
        attempt2 = Attempt.objects.create(student=self.student, exam=self.exam)
        
        attempts = self.repository.get_by_student(self.student.id)
        self.assertEqual(attempts.count(), 2)
    
    def test_get_in_progress_attempt(self):
        """Test retrieving in-progress attempt."""
        attempt = Attempt.objects.create(
            student=self.student,
            exam=self.exam,
            status=AttemptStatus.IN_PROGRESS
        )
        
        found = self.repository.get_in_progress_attempt(self.student.id, self.exam.id)
        self.assertEqual(found.id, attempt.id)


class AttemptServiceTest(TestCase):
    """Test the AttemptService."""
    
    def setUp(self):
        """Set up test data."""
        self.service = AttemptService()
        
        # Create teacher
        user = User.objects.create_user(username='teacher1', password='pass123')
        self.teacher = Teacher.objects.create(user=user, department='CS')
        
        # Create student
        self.student = Student.objects.create(
            school_id='2024001',
            first_name='John',
            last_name='Doe'
        )
        
        # Create exam
        self.exam = Exam.objects.create(
            title='Test Exam',
            duration_minutes=60,
            is_active=True,
            created_by=self.teacher
        )
    
    def test_create_attempt(self):
        """Test creating an attempt through service."""
        attempt = self.service.create_attempt(self.student.id, self.exam.id)
        
        self.assertIsNotNone(attempt)
        self.assertEqual(attempt.student_id, self.student.id)
        self.assertEqual(attempt.exam_id, self.exam.id)
        self.assertEqual(attempt.status, AttemptStatus.IN_PROGRESS)
    
    def test_submit_attempt(self):
        """Test submitting an attempt."""
        attempt = self.service.create_attempt(self.student.id, self.exam.id)
        
        submitted = self.service.submit_attempt(attempt.id)
        
        self.assertIsNotNone(submitted)
        self.assertEqual(submitted.status, AttemptStatus.SUBMITTED)
        self.assertIsNotNone(submitted.submitted_at)
    
    def test_submit_attempt_with_auto_submit(self):
        """Test auto-submitting an attempt flags it correctly."""
        attempt = self.service.create_attempt(self.student.id, self.exam.id)
        
        submitted = self.service.submit_attempt(attempt.id, auto_submit=True)
        
        self.assertIsNotNone(submitted)
        self.assertEqual(submitted.status, AttemptStatus.SUBMITTED)
        self.assertIsNotNone(submitted.submitted_at)
        self.assertTrue(submitted.auto_submitted)
        self.assertTrue(submitted.is_flagged)
        self.assertEqual(submitted.flag_reason, "Auto-submitted after 4 tab switches")
    
    def test_flag_attempt(self):
        """Test flagging an attempt."""
        attempt = self.service.create_attempt(self.student.id, self.exam.id)
        
        flagged = self.service.flag_attempt(attempt.id, "Test reason")
        
        self.assertIsNotNone(flagged)
        self.assertTrue(flagged.is_flagged)
        self.assertEqual(flagged.flag_reason, "Test reason")
    
    def test_is_flagged(self):
        """Test checking if an attempt is flagged."""
        attempt = self.service.create_attempt(self.student.id, self.exam.id)
        
        # Initially not flagged
        self.assertFalse(self.service.is_flagged(attempt.id))
        
        # Flag the attempt
        self.service.flag_attempt(attempt.id, "Test reason")
        
        # Now it should be flagged
        self.assertTrue(self.service.is_flagged(attempt.id))
    
    def test_normal_submit_not_flagged(self):
        """Test that normal submission does not flag the attempt."""
        attempt = self.service.create_attempt(self.student.id, self.exam.id)
        
        submitted = self.service.submit_attempt(attempt.id, auto_submit=False)
        
        self.assertIsNotNone(submitted)
        self.assertEqual(submitted.status, AttemptStatus.SUBMITTED)
        self.assertFalse(submitted.auto_submitted)
        self.assertFalse(submitted.is_flagged)
        self.assertEqual(submitted.flag_reason, "")


class AnswerServiceTest(TestCase):
    """Test the AnswerService."""
    
    def setUp(self):
        """Set up test data."""
        self.service = AnswerService()
        
        # Create teacher
        user = User.objects.create_user(username='teacher1', password='pass123')
        self.teacher = Teacher.objects.create(user=user, department='CS')
        
        # Create student
        self.student = Student.objects.create(
            school_id='2024001',
            first_name='John',
            last_name='Doe'
        )
        
        # Create exam
        self.exam = Exam.objects.create(
            title='Test Exam',
            duration_minutes=60,
            is_active=True,
            created_by=self.teacher
        )
        
        # Create question
        self.question = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.MCQ,
            question_text='What is 2+2?',
            options=[
                {'key': 'A', 'value': '3'},
                {'key': 'B', 'value': '4'}
            ],
            correct_answer={'value': 'B'},
            points=2.0
        )
        
        # Create attempt
        self.attempt = Attempt.objects.create(
            student=self.student,
            exam=self.exam,
            status=AttemptStatus.IN_PROGRESS
        )
    
    def test_save_answer(self):
        """Test saving an answer through service."""
        answer = self.service.save_answer(
            self.attempt.id,
            self.question.id,
            {'value': 'B'}
        )
        
        self.assertIsNotNone(answer)
        self.assertEqual(answer.attempt_id, self.attempt.id)
        self.assertEqual(answer.question_id, self.question.id)
        self.assertEqual(answer.answer_text, {'value': 'B'})
    
    def test_update_existing_answer(self):
        """Test updating an existing answer."""
        # Save initial answer
        answer1 = self.service.save_answer(
            self.attempt.id,
            self.question.id,
            {'value': 'A'}
        )
        
        # Update answer
        answer2 = self.service.save_answer(
            self.attempt.id,
            self.question.id,
            {'value': 'B'}
        )
        
        # Should be the same answer object, just updated
        self.assertEqual(answer1.id, answer2.id)
        self.assertEqual(answer2.answer_text, {'value': 'B'})



class AutoGraderServiceTest(TestCase):
    """Test the AutoGraderService."""
    
    def setUp(self):
        """Set up test data."""
        from services.auto_grader_service import AutoGraderService
        self.service = AutoGraderService()
        
        # Create teacher
        user = User.objects.create_user(username='teacher1', password='pass123')
        self.teacher = Teacher.objects.create(user=user, department='CS')
        
        # Create student
        self.student = Student.objects.create(
            school_id='2024001',
            first_name='John',
            last_name='Doe'
        )
        
        # Create exam
        self.exam = Exam.objects.create(
            title='Test Exam',
            duration_minutes=60,
            is_active=True,
            created_by=self.teacher
        )
        
        # Create attempt
        self.attempt = Attempt.objects.create(
            student=self.student,
            exam=self.exam,
            status=AttemptStatus.SUBMITTED
        )
    
    def test_grade_mcq_correct(self):
        """Test grading a correct MCQ answer."""
        question = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.MCQ,
            question_text='What is 2+2?',
            options=[
                {'key': 'A', 'value': '3'},
                {'key': 'B', 'value': '4'},
                {'key': 'C', 'value': '5'}
            ],
            correct_answer='B',
            points=2.0
        )
        
        answer = Answer.objects.create(
            attempt=self.attempt,
            question=question,
            answer_text={'answer': 'B'}
        )
        
        result = self.service.grade_mcq(answer, question)
        
        self.assertTrue(result['is_correct'])
        self.assertEqual(float(result['points_earned']), 2.0)
    
    def test_grade_mcq_incorrect(self):
        """Test grading an incorrect MCQ answer."""
        question = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.MCQ,
            question_text='What is 2+2?',
            options=[
                {'key': 'A', 'value': '3'},
                {'key': 'B', 'value': '4'},
                {'key': 'C', 'value': '5'}
            ],
            correct_answer='B',
            points=2.0
        )
        
        answer = Answer.objects.create(
            attempt=self.attempt,
            question=question,
            answer_text={'answer': 'A'}
        )
        
        result = self.service.grade_mcq(answer, question)
        
        self.assertFalse(result['is_correct'])
        self.assertEqual(float(result['points_earned']), 0.0)
    
    def test_grade_identification_exact_match(self):
        """Test grading an identification question with exact match."""
        question = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.IDENTIFICATION,
            question_text='What keyword is used to define a function in Python?',
            correct_answer=['def', 'define'],
            points=1.0
        )
        
        answer = Answer.objects.create(
            attempt=self.attempt,
            question=question,
            answer_text={'answer': 'def'}
        )
        
        result = self.service.grade_identification(answer, question)
        
        self.assertTrue(result['is_correct'])
        self.assertEqual(float(result['points_earned']), 1.0)
    
    def test_grade_identification_fuzzy_match(self):
        """Test grading an identification question with fuzzy match."""
        question = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.IDENTIFICATION,
            question_text='What is the capital of France?',
            correct_answer=['Paris'],
            points=1.0
        )
        
        # Test with slight variation
        answer = Answer.objects.create(
            attempt=self.attempt,
            question=question,
            answer_text={'answer': 'paris'}  # lowercase
        )
        
        result = self.service.grade_identification(answer, question)
        
        self.assertTrue(result['is_correct'])
        self.assertEqual(float(result['points_earned']), 1.0)
    
    def test_grade_true_false_correct(self):
        """Test grading a correct True/False answer."""
        question = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.TRUE_FALSE,
            question_text='Python is a programming language.',
            correct_answer='True',
            points=1.0
        )
        
        answer = Answer.objects.create(
            attempt=self.attempt,
            question=question,
            answer_text={'answer': 'True'}
        )
        
        result = self.service.grade_true_false(answer, question)
        
        self.assertTrue(result['is_correct'])
        self.assertEqual(float(result['points_earned']), 1.0)
    
    def test_grade_true_false_boolean_values(self):
        """Test grading True/False with boolean values."""
        question = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.TRUE_FALSE,
            question_text='The sky is blue.',
            correct_answer=True,
            points=1.0
        )
        
        answer = Answer.objects.create(
            attempt=self.attempt,
            question=question,
            answer_text={'answer': True}
        )
        
        result = self.service.grade_true_false(answer, question)
        
        self.assertTrue(result['is_correct'])
        self.assertEqual(float(result['points_earned']), 1.0)
    
    def test_grade_enumeration_all_correct(self):
        """Test grading an enumeration question with all correct items."""
        question = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.ENUMERATION,
            question_text='List three built-in data types in Python.',
            correct_answer={
                'answers': ['int', 'str', 'list', 'dict', 'tuple', 'set'],
                'min_required': 3
            },
            points=3.0
        )
        
        answer = Answer.objects.create(
            attempt=self.attempt,
            question=question,
            answer_text={'answer': ['int', 'str', 'list']}
        )
        
        result = self.service.grade_enumeration(answer, question)
        
        self.assertTrue(result['is_correct'])
        self.assertEqual(float(result['points_earned']), 3.0)
    
    def test_grade_enumeration_partial_credit(self):
        """Test grading an enumeration question with partial credit."""
        question = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.ENUMERATION,
            question_text='List three built-in data types in Python.',
            correct_answer={
                'answers': ['int', 'str', 'list', 'dict', 'tuple', 'set'],
                'min_required': 3
            },
            points=3.0
        )
        
        # Student provides only 2 correct items
        answer = Answer.objects.create(
            attempt=self.attempt,
            question=question,
            answer_text={'answer': ['int', 'str']}
        )
        
        result = self.service.grade_enumeration(answer, question)
        
        self.assertFalse(result['is_correct'])  # Less than min_required
        # Should get partial credit: 2/3 * 3.0 = 2.0
        self.assertGreater(float(result['points_earned']), 0.0)
    
    def test_grade_attempt_calculates_total_score(self):
        """Test that grading an attempt calculates the total score correctly."""
        # Create multiple questions
        q1 = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.MCQ,
            question_text='What is 2+2?',
            correct_answer='B',
            points=2.0
        )
        
        q2 = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.IDENTIFICATION,
            question_text='What is the capital of France?',
            correct_answer=['Paris'],
            points=1.0
        )
        
        # Create answers
        Answer.objects.create(
            attempt=self.attempt,
            question=q1,
            answer_text={'answer': 'B'}  # Correct
        )
        
        Answer.objects.create(
            attempt=self.attempt,
            question=q2,
            answer_text={'answer': 'Paris'}  # Correct
        )
        
        # Grade the attempt
        success = self.service.grade_attempt(self.attempt.id)
        
        self.assertTrue(success)
        
        # Refresh attempt from database
        self.attempt.refresh_from_db()
        
        # Total score should be 2.0 + 1.0 = 3.0
        self.assertEqual(float(self.attempt.total_score), 3.0)
    
    def test_calculate_total_score(self):
        """Test calculating total score from graded answers."""
        # Create questions and answers
        q1 = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.MCQ,
            question_text='Question 1',
            correct_answer='A',
            points=2.0
        )
        
        q2 = Question.objects.create(
            exam=self.exam,
            question_type=QuestionType.MCQ,
            question_text='Question 2',
            correct_answer='B',
            points=3.0
        )
        
        # Create graded answers
        Answer.objects.create(
            attempt=self.attempt,
            question=q1,
            answer_text={'answer': 'A'},
            is_correct=True,
            points_earned=2.0
        )
        
        Answer.objects.create(
            attempt=self.attempt,
            question=q2,
            answer_text={'answer': 'C'},
            is_correct=False,
            points_earned=0.0
        )
        
        total = self.service.calculate_total_score(self.attempt.id)
        
        self.assertEqual(float(total), 2.0)



class TabMonitoringViewsTest(TestCase):
    """Test the tab monitoring AJAX endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create teacher
        user = User.objects.create_user(username='teacher1', password='pass123')
        self.teacher = Teacher.objects.create(user=user, department='CS')
        
        # Create student
        self.student = Student.objects.create(
            school_id='2024001',
            first_name='John',
            last_name='Doe'
        )
        self.student.set_password('password')
        self.student.save()
        
        # Create exam
        self.exam = Exam.objects.create(
            title='Test Exam',
            duration_minutes=60,
            is_active=True,
            created_by=self.teacher
        )
        
        # Create attempt
        self.attempt = Attempt.objects.create(
            student=self.student,
            exam=self.exam,
            status=AttemptStatus.IN_PROGRESS
        )
        
        # Set up session to simulate logged-in student
        session = self.client.session
        session['student_id'] = self.student.id
        session.save()
    
    def test_record_tab_switch_success(self):
        """Test recording a tab switch violation successfully."""
        response = self.client.post(
            f'/attempts/student/attempts/{self.attempt.id}/tab-switch/',
            data={'violated_at': timezone.now().isoformat()},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['warning_number'], 1)
        self.assertEqual(data['total_warnings'], 3)
        self.assertFalse(data['should_auto_submit'])
    
    def test_record_tab_switch_unauthenticated(self):
        """Test recording tab switch without authentication."""
        # Clear session
        self.client.session.flush()
        
        response = self.client.post(
            f'/attempts/student/attempts/{self.attempt.id}/tab-switch/',
            data={},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_record_tab_switch_wrong_student(self):
        """Test recording tab switch for another student's attempt."""
        # Create another student
        other_student = Student.objects.create(
            school_id='2024002',
            first_name='Jane',
            last_name='Smith'
        )
        
        # Set session to other student
        session = self.client.session
        session['student_id'] = other_student.id
        session.save()
        
        response = self.client.post(
            f'/attempts/student/attempts/{self.attempt.id}/tab-switch/',
            data={},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
    
    def test_record_tab_switch_submitted_attempt(self):
        """Test recording tab switch for already submitted attempt."""
        # Submit the attempt
        self.attempt.status = AttemptStatus.SUBMITTED
        self.attempt.submitted_at = timezone.now()
        self.attempt.save()
        
        response = self.client.post(
            f'/attempts/student/attempts/{self.attempt.id}/tab-switch/',
            data={},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_record_multiple_tab_switches(self):
        """Test recording multiple tab switches and warning progression."""
        # First violation
        response1 = self.client.post(
            f'/attempts/student/attempts/{self.attempt.id}/tab-switch/',
            data={},
            content_type='application/json'
        )
        data1 = response1.json()
        self.assertEqual(data1['warning_number'], 1)
        self.assertFalse(data1['should_auto_submit'])
        
        # Second violation
        response2 = self.client.post(
            f'/attempts/student/attempts/{self.attempt.id}/tab-switch/',
            data={},
            content_type='application/json'
        )
        data2 = response2.json()
        self.assertEqual(data2['warning_number'], 2)
        self.assertFalse(data2['should_auto_submit'])
        
        # Third violation
        response3 = self.client.post(
            f'/attempts/student/attempts/{self.attempt.id}/tab-switch/',
            data={},
            content_type='application/json'
        )
        data3 = response3.json()
        self.assertEqual(data3['warning_number'], 3)
        self.assertFalse(data3['should_auto_submit'])
        
        # Fourth violation - should trigger auto-submit
        response4 = self.client.post(
            f'/attempts/student/attempts/{self.attempt.id}/tab-switch/',
            data={},
            content_type='application/json'
        )
        data4 = response4.json()
        self.assertEqual(data4['warning_number'], 4)
        self.assertTrue(data4['should_auto_submit'])
        
        # Verify attempt is flagged
        self.attempt.refresh_from_db()
        self.assertTrue(self.attempt.is_flagged)
        self.assertEqual(self.attempt.flag_reason, "Auto-submitted after 4 tab switches")
    
    def test_get_tab_violations_success(self):
        """Test retrieving violation count successfully."""
        # Create some violations first
        from attempts.models import TabViolation
        TabViolation.objects.create(
            attempt=self.attempt,
            warning_number=1
        )
        TabViolation.objects.create(
            attempt=self.attempt,
            warning_number=2
        )
        
        response = self.client.get(
            f'/attempts/student/attempts/{self.attempt.id}/violations/'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['violation_count'], 2)
        self.assertFalse(data['is_flagged'])
    
    def test_get_tab_violations_unauthenticated(self):
        """Test retrieving violations without authentication."""
        # Clear session
        self.client.session.flush()
        
        response = self.client.get(
            f'/attempts/student/attempts/{self.attempt.id}/violations/'
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_get_tab_violations_wrong_student(self):
        """Test retrieving violations for another student's attempt."""
        # Create another student
        other_student = Student.objects.create(
            school_id='2024002',
            first_name='Jane',
            last_name='Smith'
        )
        
        # Set session to other student
        session = self.client.session
        session['student_id'] = other_student.id
        session.save()
        
        response = self.client.get(
            f'/attempts/student/attempts/{self.attempt.id}/violations/'
        )
        
        self.assertEqual(response.status_code, 403)
    
    def test_get_tab_violations_flagged_attempt(self):
        """Test retrieving violations for a flagged attempt."""
        # Flag the attempt
        self.attempt.is_flagged = True
        self.attempt.flag_reason = "Auto-submitted after 4 tab switches"
        self.attempt.save()
        
        response = self.client.get(
            f'/attempts/student/attempts/{self.attempt.id}/violations/'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_flagged'])
        self.assertEqual(data['flag_reason'], "Auto-submitted after 4 tab switches")
