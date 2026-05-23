"""
Unit tests for DashboardService.
Tests dashboard analytics operations including metrics, trends, and history.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from users.models import Student, Teacher
from exams.models import Exam, Question, QuestionType
from attempts.models import Attempt, AttemptStatus, Answer
from services.dashboard_service import DashboardService
from services.result import Result


class DashboardServiceTest(TestCase):
    """Test cases for DashboardService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = DashboardService()
        
        # Create a test teacher (Teacher uses Django User model)
        teacher_user = User.objects.create_user(
            username='teacher001',
            password='TestPass123',
            first_name='Test',
            last_name='Teacher'
        )
        self.teacher = Teacher.objects.create(
            user=teacher_user,
            department='Mathematics'
        )
        
        # Create a test student
        self.student = Student.objects.create(
            school_id='TEST001',
            first_name='John',
            last_name='Doe'
        )
        self.student.set_password('TestPass123')
        self.student.save()
        
        # Create test exams
        self.exam1 = Exam.objects.create(
            title='Math Exam 1',
            description='First math exam',
            duration_minutes=60,
            is_active=True,
            created_by=self.teacher
        )
        
        self.exam2 = Exam.objects.create(
            title='Math Exam 2',
            description='Second math exam',
            duration_minutes=60,
            is_active=True,
            created_by=self.teacher
        )
        
        # Create questions for exam1
        self.q1_exam1 = Question.objects.create(
            exam=self.exam1,
            question_type=QuestionType.MCQ,
            question_text='What is 2+2?',
            options=[{'key': 'A', 'value': '3'}, {'key': 'B', 'value': '4'}],
            correct_answer={'answer': 'B'},
            points=Decimal('10.00'),
            order_index=1
        )
        
        self.q2_exam1 = Question.objects.create(
            exam=self.exam1,
            question_type=QuestionType.ESSAY,
            question_text='Explain calculus',
            correct_answer={'keywords': ['derivative', 'integral']},
            points=Decimal('20.00'),
            order_index=2
        )
        
        # Create questions for exam2
        self.q1_exam2 = Question.objects.create(
            exam=self.exam2,
            question_type=QuestionType.IDENTIFICATION,
            question_text='Name the capital',
            correct_answer={'answer': 'Paris'},
            points=Decimal('15.00'),
            order_index=1
        )
    
    def test_get_performance_metrics_no_exams(self):
        """Test metrics for student with no graded exams."""
        result = self.service.get_performance_metrics(self.student.id)
        
        self.assertTrue(result.is_success())
        metrics = result.value
        self.assertEqual(metrics['total_exams'], 0)
        self.assertEqual(metrics['average_score'], 0.0)
        self.assertEqual(metrics['highest_score'], 0.0)
        self.assertEqual(metrics['pass_rate'], 0.0)
    
    def test_get_performance_metrics_with_graded_exams(self):
        """Test metrics calculation with graded exams."""
        # Create graded attempts
        attempt1 = Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.GRADED,
            submitted_at=timezone.now(),
            total_score=Decimal('25.00')  # 25/30 = 83.33%
        )
        
        attempt2 = Attempt.objects.create(
            student=self.student,
            exam=self.exam2,
            status=AttemptStatus.GRADED,
            submitted_at=timezone.now(),
            total_score=Decimal('10.00')  # 10/15 = 66.67%
        )
        
        result = self.service.get_performance_metrics(self.student.id)
        
        self.assertTrue(result.is_success())
        metrics = result.value
        self.assertEqual(metrics['total_exams'], 2)
        self.assertEqual(metrics['average_score'], 17.5)  # (25 + 10) / 2
        self.assertEqual(metrics['highest_score'], 25.0)
        self.assertEqual(metrics['pass_rate'], 100.0)  # Both above 60%
    
    def test_get_performance_metrics_with_failing_exam(self):
        """Test pass rate calculation with failing exam."""
        # Create one passing and one failing attempt
        Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.GRADED,
            submitted_at=timezone.now(),
            total_score=Decimal('25.00')  # 25/30 = 83.33% (pass)
        )
        
        Attempt.objects.create(
            student=self.student,
            exam=self.exam2,
            status=AttemptStatus.GRADED,
            submitted_at=timezone.now(),
            total_score=Decimal('5.00')  # 5/15 = 33.33% (fail)
        )
        
        result = self.service.get_performance_metrics(self.student.id)
        
        self.assertTrue(result.is_success())
        metrics = result.value
        self.assertEqual(metrics['total_exams'], 2)
        self.assertEqual(metrics['pass_rate'], 50.0)  # 1 out of 2 passed
    
    def test_get_performance_metrics_ignores_submitted(self):
        """Test that submitted but not graded attempts are ignored."""
        # Create graded attempt
        Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.GRADED,
            submitted_at=timezone.now(),
            total_score=Decimal('25.00')
        )
        
        # Create submitted but not graded attempt
        Attempt.objects.create(
            student=self.student,
            exam=self.exam2,
            status=AttemptStatus.SUBMITTED,
            submitted_at=timezone.now(),
            total_score=Decimal('0.00')
        )
        
        result = self.service.get_performance_metrics(self.student.id)
        
        self.assertTrue(result.is_success())
        metrics = result.value
        self.assertEqual(metrics['total_exams'], 1)  # Only graded counted
    
    def test_get_performance_metrics_student_not_found(self):
        """Test metrics for non-existent student."""
        result = self.service.get_performance_metrics(99999)
        
        self.assertTrue(result.is_failure())
        self.assertIn('not found', result.error.message.lower())
    
    def test_get_score_trend_empty(self):
        """Test score trend for student with no graded exams."""
        result = self.service.get_score_trend(self.student.id)
        
        self.assertTrue(result.is_success())
        self.assertEqual(len(result.value), 0)
    
    def test_get_score_trend_chronological_order(self):
        """Test that score trend is in chronological order."""
        # Create attempts at different times
        now = timezone.now()
        
        attempt1 = Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.GRADED,
            submitted_at=now - timedelta(days=2),
            total_score=Decimal('20.00')
        )
        
        attempt2 = Attempt.objects.create(
            student=self.student,
            exam=self.exam2,
            status=AttemptStatus.GRADED,
            submitted_at=now - timedelta(days=1),
            total_score=Decimal('12.00')
        )
        
        result = self.service.get_score_trend(self.student.id)
        
        self.assertTrue(result.is_success())
        trend_data = result.value
        self.assertEqual(len(trend_data), 2)
        
        # Verify chronological order (oldest first)
        self.assertEqual(trend_data[0]['exam_name'], 'Math Exam 1')
        self.assertEqual(trend_data[1]['exam_name'], 'Math Exam 2')
        
        # Verify data structure
        self.assertIn('date', trend_data[0])
        self.assertIn('score', trend_data[0])
        self.assertIn('percentage', trend_data[0])
        self.assertIn('total_possible', trend_data[0])
    
    def test_get_score_trend_percentage_calculation(self):
        """Test that percentages are calculated correctly."""
        Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.GRADED,
            submitted_at=timezone.now(),
            total_score=Decimal('15.00')  # 15/30 = 50%
        )
        
        result = self.service.get_score_trend(self.student.id)
        
        self.assertTrue(result.is_success())
        trend_data = result.value
        self.assertEqual(len(trend_data), 1)
        self.assertEqual(trend_data[0]['percentage'], 50.0)
        self.assertEqual(trend_data[0]['score'], 15.0)
        self.assertEqual(trend_data[0]['total_possible'], 30.0)
    
    def test_get_type_performance_empty(self):
        """Test type performance for student with no graded exams."""
        result = self.service.get_type_performance(self.student.id)
        
        self.assertTrue(result.is_success())
        self.assertEqual(len(result.value), 0)
    
    def test_get_type_performance_multiple_types(self):
        """Test type performance calculation across different question types."""
        # Create attempt
        attempt = Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.GRADED,
            submitted_at=timezone.now(),
            total_score=Decimal('25.00')
        )
        
        # Create answers for different question types
        Answer.objects.create(
            attempt=attempt,
            question=self.q1_exam1,  # MCQ, 10 points
            answer_text={'answer': 'B'},
            is_correct=True,
            points_earned=Decimal('10.00')
        )
        
        Answer.objects.create(
            attempt=attempt,
            question=self.q2_exam1,  # Essay, 20 points
            answer_text={'text': 'Calculus is...'},
            is_correct=True,
            points_earned=Decimal('15.00')
        )
        
        result = self.service.get_type_performance(self.student.id)
        
        self.assertTrue(result.is_success())
        type_perf = result.value
        
        # MCQ: 10/10 = 100%
        self.assertEqual(type_perf['Multiple Choice Question'], 100.0)
        
        # Essay: 15/20 = 75%
        self.assertEqual(type_perf['Essay'], 75.0)
    
    def test_get_type_performance_averages_across_exams(self):
        """Test that type performance averages across multiple exams."""
        # Create two attempts
        attempt1 = Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.GRADED,
            submitted_at=timezone.now(),
            total_score=Decimal('10.00')
        )
        
        attempt2 = Attempt.objects.create(
            student=self.student,
            exam=self.exam2,
            status=AttemptStatus.GRADED,
            submitted_at=timezone.now(),
            total_score=Decimal('15.00')
        )
        
        # MCQ answer in exam1: 10/10 = 100%
        Answer.objects.create(
            attempt=attempt1,
            question=self.q1_exam1,
            answer_text={'answer': 'B'},
            is_correct=True,
            points_earned=Decimal('10.00')
        )
        
        # Identification answer in exam2: 10/15 = 66.67%
        Answer.objects.create(
            attempt=attempt2,
            question=self.q1_exam2,
            answer_text={'answer': 'Paris'},
            is_correct=True,
            points_earned=Decimal('10.00')
        )
        
        result = self.service.get_type_performance(self.student.id)
        
        self.assertTrue(result.is_success())
        type_perf = result.value
        
        self.assertEqual(type_perf['Multiple Choice Question'], 100.0)
        self.assertAlmostEqual(type_perf['Identification'], 66.67, places=2)
    
    def test_get_recent_activity_empty(self):
        """Test recent activity for student with no attempts."""
        result = self.service.get_recent_activity(self.student.id)
        
        self.assertTrue(result.is_success())
        self.assertEqual(len(result.value), 0)
    
    def test_get_recent_activity_limit(self):
        """Test that recent activity respects the limit parameter."""
        # Create 7 attempts
        for i in range(7):
            Attempt.objects.create(
                student=self.student,
                exam=self.exam1,
                status=AttemptStatus.GRADED,
                submitted_at=timezone.now() - timedelta(days=i),
                total_score=Decimal('20.00')
            )
        
        # Default limit is 5
        result = self.service.get_recent_activity(self.student.id)
        
        self.assertTrue(result.is_success())
        self.assertEqual(len(result.value), 5)
        
        # Test custom limit
        result = self.service.get_recent_activity(self.student.id, limit=3)
        
        self.assertTrue(result.is_success())
        self.assertEqual(len(result.value), 3)
    
    def test_get_recent_activity_includes_pending(self):
        """Test that recent activity includes submitted but not graded attempts."""
        # Create graded attempt
        Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.GRADED,
            submitted_at=timezone.now() - timedelta(days=1),
            total_score=Decimal('25.00')
        )
        
        # Create submitted attempt
        Attempt.objects.create(
            student=self.student,
            exam=self.exam2,
            status=AttemptStatus.SUBMITTED,
            submitted_at=timezone.now(),
            total_score=Decimal('0.00')
        )
        
        result = self.service.get_recent_activity(self.student.id)
        
        self.assertTrue(result.is_success())
        activity = result.value
        self.assertEqual(len(activity), 2)
        
        # Most recent should be submitted
        self.assertEqual(activity[0]['status'], AttemptStatus.SUBMITTED)
        self.assertIsNone(activity[0]['score'])  # Not graded yet
        
        # Second should be graded
        self.assertEqual(activity[1]['status'], AttemptStatus.GRADED)
        self.assertEqual(activity[1]['score'], 25.0)
    
    def test_get_recent_activity_most_recent_first(self):
        """Test that recent activity is ordered by most recent first."""
        now = timezone.now()
        
        Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.GRADED,
            submitted_at=now - timedelta(days=2),
            total_score=Decimal('20.00')
        )
        
        Attempt.objects.create(
            student=self.student,
            exam=self.exam2,
            status=AttemptStatus.GRADED,
            submitted_at=now - timedelta(days=1),
            total_score=Decimal('15.00')
        )
        
        result = self.service.get_recent_activity(self.student.id)
        
        self.assertTrue(result.is_success())
        activity = result.value
        
        # Most recent first
        self.assertEqual(activity[0]['exam_title'], 'Math Exam 2')
        self.assertEqual(activity[1]['exam_title'], 'Math Exam 1')
    
    def test_get_exam_history_empty(self):
        """Test exam history for student with no attempts."""
        result = self.service.get_exam_history(self.student.id)
        
        self.assertTrue(result.is_success())
        self.assertEqual(len(result.value), 0)
    
    def test_get_exam_history_all_attempts(self):
        """Test that exam history returns all graded and submitted attempts."""
        # Create various attempts
        Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.GRADED,
            submitted_at=timezone.now(),
            total_score=Decimal('25.00')
        )
        
        Attempt.objects.create(
            student=self.student,
            exam=self.exam2,
            status=AttemptStatus.SUBMITTED,
            submitted_at=timezone.now(),
            total_score=Decimal('0.00')
        )
        
        # In progress should not be included
        Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.IN_PROGRESS,
            total_score=Decimal('0.00')
        )
        
        result = self.service.get_exam_history(self.student.id)
        
        self.assertTrue(result.is_success())
        history = result.value
        self.assertEqual(len(history), 2)  # Only graded and submitted
    
    def test_get_exam_history_date_filter(self):
        """Test exam history filtering by date range."""
        now = timezone.now()
        
        # Create attempts at different times
        Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.GRADED,
            submitted_at=now - timedelta(days=10),
            total_score=Decimal('20.00')
        )
        
        Attempt.objects.create(
            student=self.student,
            exam=self.exam2,
            status=AttemptStatus.GRADED,
            submitted_at=now - timedelta(days=5),
            total_score=Decimal('15.00')
        )
        
        Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.GRADED,
            submitted_at=now - timedelta(days=1),
            total_score=Decimal('25.00')
        )
        
        # Filter for last 7 days
        filters = {
            'date_from': (now - timedelta(days=7)).isoformat()
        }
        
        result = self.service.get_exam_history(self.student.id, filters)
        
        self.assertTrue(result.is_success())
        history = result.value
        self.assertEqual(len(history), 2)  # Only last 2 attempts
    
    def test_get_exam_history_status_filter(self):
        """Test exam history filtering by status."""
        # Create graded and submitted attempts
        Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.GRADED,
            submitted_at=timezone.now(),
            total_score=Decimal('25.00')
        )
        
        Attempt.objects.create(
            student=self.student,
            exam=self.exam2,
            status=AttemptStatus.SUBMITTED,
            submitted_at=timezone.now(),
            total_score=Decimal('0.00')
        )
        
        # Filter for graded only
        filters = {'status': AttemptStatus.GRADED}
        
        result = self.service.get_exam_history(self.student.id, filters)
        
        self.assertTrue(result.is_success())
        history = result.value
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['status'], AttemptStatus.GRADED)
    
    def test_export_history_csv_empty(self):
        """Test CSV export for student with no history."""
        result = self.service.export_history_csv(self.student.id)
        
        self.assertTrue(result.is_success())
        csv_content = result.value.decode('utf-8')
        
        # Should have header row
        lines = csv_content.strip().split('\n')
        self.assertEqual(len(lines), 1)  # Only header
        self.assertIn('Exam Title', lines[0])
        # Verify class columns are in header (Requirement 5.4)
        self.assertIn('Grade Level', lines[0])
        self.assertIn('Strand', lines[0])
        self.assertIn('Section', lines[0])
    
    def test_export_history_csv_with_data(self):
        """Test CSV export with exam history data."""
        # Create attempts
        Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.GRADED,
            submitted_at=timezone.now(),
            total_score=Decimal('25.00')
        )
        
        Attempt.objects.create(
            student=self.student,
            exam=self.exam2,
            status=AttemptStatus.SUBMITTED,
            submitted_at=timezone.now(),
            total_score=Decimal('0.00')
        )
        
        result = self.service.export_history_csv(self.student.id)
        
        self.assertTrue(result.is_success())
        csv_content = result.value.decode('utf-8')
        
        # Should have header + 2 data rows
        lines = csv_content.strip().split('\n')
        self.assertEqual(len(lines), 3)
        
        # Verify header
        self.assertIn('Exam Title', lines[0])
        self.assertIn('Date Taken', lines[0])
        self.assertIn('Score', lines[0])
        self.assertIn('Status', lines[0])
        # Verify class columns are in header (Requirement 5.4)
        self.assertIn('Grade Level', lines[0])
        self.assertIn('Strand', lines[0])
        self.assertIn('Section', lines[0])
        
        # Verify data rows contain exam titles
        self.assertIn('Math Exam', csv_content)
    
    def test_export_history_csv_formats_correctly(self):
        """Test that CSV export formats data correctly."""
        Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.GRADED,
            submitted_at=timezone.now(),
            total_score=Decimal('25.00')
        )
        
        result = self.service.export_history_csv(self.student.id)
        
        self.assertTrue(result.is_success())
        csv_content = result.value.decode('utf-8')
        
        # Check for formatted score
        self.assertIn('25.00', csv_content)
        
        # Check for status
        self.assertIn('Graded', csv_content)
        
        # Check for percentage
        self.assertIn('%', csv_content)
    

    def test_export_history_csv_includes_class_information(self):
        """Test that CSV export includes class information when student has class assignment (Requirement 5.4)."""
        from users.models import Class
        
        # Create a class
        test_class = Class.objects.create(
            grade_level='Grade 12',
            strand='HUMSS',
            section='A',
            teacher=self.teacher
        )
        
        # Assign student to class
        self.student.class_assigned = test_class
        self.student.save()
        
        # Create an attempt
        Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.GRADED,
            submitted_at=timezone.now(),
            total_score=Decimal('25.00')
        )
        
        result = self.service.export_history_csv(self.student.id)
        
        self.assertTrue(result.is_success())
        csv_content = result.value.decode('utf-8')
        
        # Verify class information is in the CSV
        self.assertIn('Grade 12', csv_content)
        self.assertIn('HUMSS', csv_content)
        self.assertIn('A', csv_content)
        
        # Verify header includes class columns
        lines = csv_content.strip().split('\n')
        header = lines[0]
        self.assertIn('Grade Level', header)
        self.assertIn('Strand', header)
        self.assertIn('Section', header)
    
    def test_export_history_csv_handles_null_class_assignment(self):
        """Test that CSV export handles null class assignments gracefully (Requirement 5.4)."""
        # Ensure student has no class assignment
        self.student.class_assigned = None
        self.student.save()
        
        # Create an attempt
        Attempt.objects.create(
            student=self.student,
            exam=self.exam1,
            status=AttemptStatus.GRADED,
            submitted_at=timezone.now(),
            total_score=Decimal('25.00')
        )
        
        result = self.service.export_history_csv(self.student.id)
        
        self.assertTrue(result.is_success())
        csv_content = result.value.decode('utf-8')
        
        # Verify header includes class columns
        lines = csv_content.strip().split('\n')
        header = lines[0]
        self.assertIn('Grade Level', header)
        self.assertIn('Strand', header)
        self.assertIn('Section', header)
        
        # Verify data row exists (should have empty class fields)
        self.assertEqual(len(lines), 2)  # Header + 1 data row
        
        # Verify exam title is present
        self.assertIn('Math Exam', csv_content)
