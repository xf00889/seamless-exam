"""
Unit tests for DashboardService caching functionality.
Tests cache behavior, invalidation, and warming.
"""
from django.test import TestCase
from django.core.cache import cache
from django.conf import settings
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

from users.models import Student, Teacher
from exams.models import Exam, Question, QuestionType
from attempts.models import Attempt, AttemptStatus, Answer
from services.dashboard_service import DashboardService
from services.result import Result


class DashboardCachingTest(TestCase):
    """Test cases for DashboardService caching functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = DashboardService()
        
        # Clear cache before each test
        cache.clear()
        
        # Create a test teacher (Teacher uses Django User model)
        from django.contrib.auth.models import User
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            password='password123',
            first_name='John',
            last_name='Doe'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user
        )
        
        # Create a test student
        self.student = Student.objects.create(
            school_id='2024001',
            first_name='Jane',
            last_name='Smith',
            password_hash='hashed_password'
        )
        
        # Create a test exam
        self.exam = Exam.objects.create(
            title='Test Exam',
            description='Test Description',
            created_by=self.teacher,
            duration_minutes=60,
            is_active=True
        )
        
        # Create test questions
        self.question = Question.objects.create(
            exam=self.exam,
            question_text='What is 2+2?',
            question_type=QuestionType.MCQ,
            points=Decimal('10.0'),
            correct_answer={'answer': 'A'},
            order_index=1
        )
    
    def test_performance_metrics_caching(self):
        """Test that performance metrics are cached correctly."""
        # First call should miss cache and compute
        result1 = self.service.get_performance_metrics(self.student.id)
        self.assertTrue(result1.is_success())
        
        # Check that data is now in cache
        cache_key = self.service._get_cache_key(
            settings.CACHE_KEY_DASHBOARD_METRICS,
            self.student.id
        )
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data, result1.value)
        
        # Second call should hit cache (verify by checking it returns same object)
        result2 = self.service.get_performance_metrics(self.student.id)
        self.assertTrue(result2.is_success())
        self.assertEqual(result2.value, result1.value)
    
    def test_score_trend_caching(self):
        """Test that score trend data is cached correctly."""
        # Create a graded attempt
        attempt = Attempt.objects.create(
            student=self.student,
            exam=self.exam,
            status=AttemptStatus.GRADED,
            total_score=Decimal('8.0'),
            submitted_at=timezone.now()
        )
        
        # First call should miss cache and compute
        result1 = self.service.get_score_trend(self.student.id)
        self.assertTrue(result1.is_success())
        
        # Check that data is now in cache
        cache_key = self.service._get_cache_key(
            settings.CACHE_KEY_SCORE_TREND,
            self.student.id
        )
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
        self.assertEqual(len(cached_data), 1)
        
        # Second call should hit cache
        result2 = self.service.get_score_trend(self.student.id)
        self.assertTrue(result2.is_success())
        self.assertEqual(result2.value, result1.value)
    
    def test_type_performance_caching(self):
        """Test that type performance data is cached correctly."""
        # Create a graded attempt with answer
        attempt = Attempt.objects.create(
            student=self.student,
            exam=self.exam,
            status=AttemptStatus.GRADED,
            total_score=Decimal('8.0'),
            submitted_at=timezone.now()
        )
        
        Answer.objects.create(
            attempt=attempt,
            question=self.question,
            answer_text={'value': 'A'},
            points_earned=Decimal('8.0'),
            is_correct=True
        )
        
        # First call should miss cache and compute
        result1 = self.service.get_type_performance(self.student.id)
        self.assertTrue(result1.is_success())
        
        # Check that data is now in cache
        cache_key = self.service._get_cache_key(
            settings.CACHE_KEY_TYPE_PERFORMANCE,
            self.student.id
        )
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
        
        # Second call should hit cache
        result2 = self.service.get_type_performance(self.student.id)
        self.assertTrue(result2.is_success())
        self.assertEqual(result2.value, result1.value)
    
    def test_cache_invalidation(self):
        """Test that cache is properly invalidated."""
        # Create initial data and cache it
        result1 = self.service.get_performance_metrics(self.student.id)
        self.assertTrue(result1.is_success())
        
        # Verify cache exists
        cache_key = self.service._get_cache_key(
            settings.CACHE_KEY_DASHBOARD_METRICS,
            self.student.id
        )
        self.assertIsNotNone(cache.get(cache_key))
        
        # Invalidate cache
        DashboardService.invalidate_student_cache(self.student.id)
        
        # Verify cache is cleared
        self.assertIsNone(cache.get(cache_key))
    
    def test_cache_invalidation_all_keys(self):
        """Test that all cache keys are invalidated together."""
        # Create graded attempt for all data types
        attempt = Attempt.objects.create(
            student=self.student,
            exam=self.exam,
            status=AttemptStatus.GRADED,
            total_score=Decimal('8.0'),
            submitted_at=timezone.now()
        )
        
        Answer.objects.create(
            attempt=attempt,
            question=self.question,
            answer_text={'value': 'A'},
            points_earned=Decimal('8.0'),
            is_correct=True
        )
        
        # Cache all data types
        self.service.get_performance_metrics(self.student.id)
        self.service.get_score_trend(self.student.id)
        self.service.get_type_performance(self.student.id)
        
        # Verify all caches exist
        metrics_key = self.service._get_cache_key(
            settings.CACHE_KEY_DASHBOARD_METRICS,
            self.student.id
        )
        trend_key = self.service._get_cache_key(
            settings.CACHE_KEY_SCORE_TREND,
            self.student.id
        )
        performance_key = self.service._get_cache_key(
            settings.CACHE_KEY_TYPE_PERFORMANCE,
            self.student.id
        )
        
        self.assertIsNotNone(cache.get(metrics_key))
        self.assertIsNotNone(cache.get(trend_key))
        self.assertIsNotNone(cache.get(performance_key))
        
        # Invalidate all caches
        DashboardService.invalidate_student_cache(self.student.id)
        
        # Verify all caches are cleared
        self.assertIsNone(cache.get(metrics_key))
        self.assertIsNone(cache.get(trend_key))
        self.assertIsNone(cache.get(performance_key))
    
    def test_cache_warming(self):
        """Test that cache warming pre-populates cache."""
        # Create graded attempt
        attempt = Attempt.objects.create(
            student=self.student,
            exam=self.exam,
            status=AttemptStatus.GRADED,
            total_score=Decimal('8.0'),
            submitted_at=timezone.now()
        )
        
        Answer.objects.create(
            attempt=attempt,
            question=self.question,
            answer_text={'value': 'A'},
            points_earned=Decimal('8.0'),
            is_correct=True
        )
        
        # Verify cache is empty
        metrics_key = self.service._get_cache_key(
            settings.CACHE_KEY_DASHBOARD_METRICS,
            self.student.id
        )
        self.assertIsNone(cache.get(metrics_key))
        
        # Warm cache
        DashboardService.warm_cache(self.student.id)
        
        # Verify all caches are populated
        self.assertIsNotNone(cache.get(metrics_key))
        
        trend_key = self.service._get_cache_key(
            settings.CACHE_KEY_SCORE_TREND,
            self.student.id
        )
        self.assertIsNotNone(cache.get(trend_key))
        
        performance_key = self.service._get_cache_key(
            settings.CACHE_KEY_TYPE_PERFORMANCE,
            self.student.id
        )
        self.assertIsNotNone(cache.get(performance_key))
    
    def test_cache_timeout_configuration(self):
        """Test that cache timeouts are configured correctly."""
        # Verify timeout settings exist
        self.assertTrue(hasattr(settings, 'CACHE_TIMEOUT_DASHBOARD_METRICS'))
        self.assertTrue(hasattr(settings, 'CACHE_TIMEOUT_SCORE_TREND'))
        self.assertTrue(hasattr(settings, 'CACHE_TIMEOUT_TYPE_PERFORMANCE'))
        
        # Verify timeout values
        self.assertEqual(settings.CACHE_TIMEOUT_DASHBOARD_METRICS, 300)  # 5 minutes
        self.assertEqual(settings.CACHE_TIMEOUT_SCORE_TREND, 600)  # 10 minutes
        self.assertEqual(settings.CACHE_TIMEOUT_TYPE_PERFORMANCE, 300)  # 5 minutes
    
    def test_cache_with_no_data(self):
        """Test that empty results are also cached."""
        # Get metrics for student with no exams
        result = self.service.get_performance_metrics(self.student.id)
        self.assertTrue(result.is_success())
        self.assertEqual(result.value['total_exams'], 0)
        
        # Verify empty result is cached
        cache_key = self.service._get_cache_key(
            settings.CACHE_KEY_DASHBOARD_METRICS,
            self.student.id
        )
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data['total_exams'], 0)
    
    def test_cache_isolation_between_students(self):
        """Test that cache is isolated between different students."""
        # Create another student
        student2 = Student.objects.create(
            school_id='2024002',
            first_name='John',
            last_name='Doe',
            password_hash='hashed_password'
        )
        
        # Create different data for each student
        attempt1 = Attempt.objects.create(
            student=self.student,
            exam=self.exam,
            status=AttemptStatus.GRADED,
            total_score=Decimal('8.0'),
            submitted_at=timezone.now()
        )
        
        attempt2 = Attempt.objects.create(
            student=student2,
            exam=self.exam,
            status=AttemptStatus.GRADED,
            total_score=Decimal('10.0'),
            submitted_at=timezone.now()
        )
        
        # Cache data for both students
        result1 = self.service.get_performance_metrics(self.student.id)
        result2 = self.service.get_performance_metrics(student2.id)
        
        # Verify different data is cached
        self.assertNotEqual(result1.value['highest_score'], result2.value['highest_score'])
        
        # Invalidate cache for student1
        DashboardService.invalidate_student_cache(self.student.id)
        
        # Verify student1 cache is cleared but student2 cache remains
        cache_key1 = self.service._get_cache_key(
            settings.CACHE_KEY_DASHBOARD_METRICS,
            self.student.id
        )
        cache_key2 = self.service._get_cache_key(
            settings.CACHE_KEY_DASHBOARD_METRICS,
            student2.id
        )
        
        self.assertIsNone(cache.get(cache_key1))
        self.assertIsNotNone(cache.get(cache_key2))
