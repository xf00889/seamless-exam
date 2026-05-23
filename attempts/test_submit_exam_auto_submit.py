"""
Test for auto-submission functionality in submit_exam_view.
Tests that auto_submit parameter properly flags attempts.
Requirements: 1.4, 4.4
"""
import json
from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import User
from attempts.models import Attempt, AttemptStatus
from attempts.views import submit_exam_view
from users.models import Student, Teacher
from exams.models import Exam
from services.tab_monitoring_service import TabMonitoringService


class SubmitExamAutoSubmitTest(TestCase):
    """Test auto-submission and flagging functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        
        # Create Django user for teacher
        teacher_user = User.objects.create_user(
            username="teacher",
            email="teacher@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Teacher"
        )
        
        # Create teacher
        self.teacher = Teacher.objects.create(
            user=teacher_user,
            department="Test Department"
        )
        
        # Create student
        self.student = Student.objects.create(
            first_name="Test",
            last_name="Student",
            school_id="12345",
            password_hash="dummy_hash"
        )
        
        # Create exam
        self.exam = Exam.objects.create(
            title="Test Exam",
            created_by=self.teacher,
            duration_minutes=60,
            is_active=True
        )
        
        # Create attempt
        self.attempt = Attempt.objects.create(
            student=self.student,
            exam=self.exam,
            status=AttemptStatus.IN_PROGRESS
        )
        
        self.tab_monitoring_service = TabMonitoringService()
    
    def _add_session_to_request(self, request):
        """Add session to request."""
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        request.session['student_id'] = self.student.id
    
    def test_normal_submission_not_flagged(self):
        """Test that normal submission does not flag the attempt."""
        # Create request without auto_submit parameter
        request = self.factory.post(
            f'/attempts/{self.attempt.id}/submit/',
            data=json.dumps({}),
            content_type='application/json'
        )
        self._add_session_to_request(request)
        
        # Submit exam
        response = submit_exam_view(request, self.attempt.id)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify attempt is submitted but not flagged
        self.attempt.refresh_from_db()
        # Status can be SUBMITTED or GRADED (auto-grader marks as GRADED if no essays)
        self.assertIn(self.attempt.status, [AttemptStatus.SUBMITTED, AttemptStatus.GRADED])
        self.assertFalse(self.attempt.is_flagged)
        self.assertFalse(self.attempt.auto_submitted)
        self.assertEqual(self.attempt.flag_reason, '')
    
    def test_auto_submission_flags_attempt(self):
        """Test that auto-submission flags the attempt."""
        # Create request with auto_submit=True
        request = self.factory.post(
            f'/attempts/{self.attempt.id}/submit/',
            data=json.dumps({'auto_submit': True}),
            content_type='application/json'
        )
        self._add_session_to_request(request)
        
        # Submit exam
        response = submit_exam_view(request, self.attempt.id)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify attempt is submitted and flagged
        self.attempt.refresh_from_db()
        # Status can be SUBMITTED or GRADED (auto-grader marks as GRADED if no essays)
        self.assertIn(self.attempt.status, [AttemptStatus.SUBMITTED, AttemptStatus.GRADED])
        self.assertTrue(self.attempt.is_flagged)
        self.assertTrue(self.attempt.auto_submitted)
        self.assertEqual(self.attempt.flag_reason, "Auto-submitted after 4 tab switches")
    
    def test_auto_submission_with_false_parameter(self):
        """Test that auto_submit=False does not flag the attempt."""
        # Create request with auto_submit=False
        request = self.factory.post(
            f'/attempts/{self.attempt.id}/submit/',
            data=json.dumps({'auto_submit': False}),
            content_type='application/json'
        )
        self._add_session_to_request(request)
        
        # Submit exam
        response = submit_exam_view(request, self.attempt.id)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify attempt is submitted but not flagged
        self.attempt.refresh_from_db()
        # Status can be SUBMITTED or GRADED (auto-grader marks as GRADED if no essays)
        self.assertIn(self.attempt.status, [AttemptStatus.SUBMITTED, AttemptStatus.GRADED])
        self.assertFalse(self.attempt.is_flagged)
        self.assertFalse(self.attempt.auto_submitted)
    
    def test_empty_request_body_not_flagged(self):
        """Test that empty request body does not flag the attempt."""
        # Create request with empty body
        request = self.factory.post(
            f'/attempts/{self.attempt.id}/submit/',
            data='',
            content_type='application/json'
        )
        self._add_session_to_request(request)
        
        # Submit exam
        response = submit_exam_view(request, self.attempt.id)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify attempt is submitted but not flagged
        self.attempt.refresh_from_db()
        # Status can be SUBMITTED or GRADED (auto-grader marks as GRADED if no essays)
        self.assertIn(self.attempt.status, [AttemptStatus.SUBMITTED, AttemptStatus.GRADED])
        self.assertFalse(self.attempt.is_flagged)
        self.assertFalse(self.attempt.auto_submitted)
