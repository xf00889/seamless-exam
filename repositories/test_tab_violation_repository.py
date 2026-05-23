"""
Unit tests for TabViolationRepository.
Tests CRUD operations and specialized query methods.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from users.models import Student, User
from exams.models import Exam, Teacher
from attempts.models import Attempt, TabViolation
from repositories.tab_violation_repository import TabViolationRepository


class TabViolationRepositoryTest(TestCase):
    """Test suite for TabViolationRepository."""
    
    def setUp(self):
        """Set up test data."""
        # Create teacher
        teacher_user = User.objects.create_user(
            username='teacher1',
            password='testpass123'
        )
        self.teacher = Teacher.objects.create(
            user=teacher_user,
            department='Science'
        )
        
        # Create student
        self.student = Student.objects.create(
            school_id='S001',
            first_name='John',
            last_name='Doe',
            password_hash='dummy_hash'
        )
        
        # Create exam
        self.exam = Exam.objects.create(
            title='Test Exam',
            created_by=self.teacher,
            duration_minutes=60
        )
        
        # Create attempt
        self.attempt = Attempt.objects.create(
            student=self.student,
            exam=self.exam
        )
        
        self.repository = TabViolationRepository()
    
    def test_create_violation(self):
        """Test creating a new violation."""
        violation = self.repository.create_violation(
            attempt_id=self.attempt.id,
            warning_number=1
        )
        
        self.assertIsNotNone(violation)
        self.assertEqual(violation.attempt_id, self.attempt.id)
        self.assertEqual(violation.warning_number, 1)
        self.assertIsNotNone(violation.violated_at)
        self.assertIsNone(violation.returned_at)
        self.assertIsNone(violation.duration_seconds)
    
    def test_update_return_time(self):
        """Test updating return time and duration calculation."""
        # Create violation
        violation = self.repository.create_violation(
            attempt_id=self.attempt.id,
            warning_number=1
        )
        
        # Update return time (45 seconds later)
        returned_at = violation.violated_at + timedelta(seconds=45)
        updated_violation = self.repository.update_return_time(
            violation_id=violation.id,
            returned_at=returned_at
        )
        
        self.assertIsNotNone(updated_violation)
        self.assertEqual(updated_violation.returned_at, returned_at)
        self.assertEqual(updated_violation.duration_seconds, 45)
    
    def test_get_attempt_violations(self):
        """Test retrieving all violations for an attempt."""
        # Create multiple violations
        violation1 = self.repository.create_violation(
            attempt_id=self.attempt.id,
            warning_number=1
        )
        violation2 = self.repository.create_violation(
            attempt_id=self.attempt.id,
            warning_number=2
        )
        violation3 = self.repository.create_violation(
            attempt_id=self.attempt.id,
            warning_number=3
        )
        
        violations = self.repository.get_attempt_violations(self.attempt.id)
        
        self.assertEqual(violations.count(), 3)
        # Verify chronological ordering
        violation_list = list(violations)
        self.assertEqual(violation_list[0].id, violation1.id)
        self.assertEqual(violation_list[1].id, violation2.id)
        self.assertEqual(violation_list[2].id, violation3.id)
    
    def test_count_violations(self):
        """Test counting violations for an attempt."""
        # Initially no violations
        count = self.repository.count_violations(self.attempt.id)
        self.assertEqual(count, 0)
        
        # Create violations
        self.repository.create_violation(
            attempt_id=self.attempt.id,
            warning_number=1
        )
        self.repository.create_violation(
            attempt_id=self.attempt.id,
            warning_number=2
        )
        
        count = self.repository.count_violations(self.attempt.id)
        self.assertEqual(count, 2)
    
    def test_get_total_time_away(self):
        """Test calculating total time away from exam."""
        # Create violations with durations
        violation1 = self.repository.create_violation(
            attempt_id=self.attempt.id,
            warning_number=1
        )
        self.repository.update_return_time(
            violation_id=violation1.id,
            returned_at=violation1.violated_at + timedelta(seconds=30)
        )
        
        violation2 = self.repository.create_violation(
            attempt_id=self.attempt.id,
            warning_number=2
        )
        self.repository.update_return_time(
            violation_id=violation2.id,
            returned_at=violation2.violated_at + timedelta(seconds=45)
        )
        
        # Create violation without return time (should not be counted)
        self.repository.create_violation(
            attempt_id=self.attempt.id,
            warning_number=3
        )
        
        total_time = self.repository.get_total_time_away(self.attempt.id)
        self.assertEqual(total_time, 75)  # 30 + 45
    
    def test_get_total_time_away_no_violations(self):
        """Test total time away when no violations exist."""
        total_time = self.repository.get_total_time_away(self.attempt.id)
        self.assertEqual(total_time, 0)
    
    def test_update_return_time_invalid_id(self):
        """Test updating return time with invalid violation ID."""
        returned_at = timezone.now()
        result = self.repository.update_return_time(
            violation_id=99999,
            returned_at=returned_at
        )
        
        self.assertIsNone(result)
