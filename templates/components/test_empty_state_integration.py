"""
Integration tests for empty state component in teacher dashboard
Requirements: 2.1, 2.2, 2.3 - Empty state components
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from users.models import Teacher
from exams.models import Exam
from attempts.models import Attempt

User = get_user_model()


class EmptyStateIntegrationTest(TestCase):
    """Test empty state components display correctly in teacher dashboard."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create teacher user
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            password='testpass123',
            email='teacher@test.com',
            first_name='Test',
            last_name='Teacher'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            department='Science'
        )
    
    def test_empty_state_displays_when_no_attempts(self):
        """Test that empty state displays when there are no exam attempts (Requirement 2.1)."""
        # Login as teacher
        self.client.login(username='teacher1', password='testpass123')
        
        # Access dashboard
        response = self.client.get('/attempts/teacher/dashboard/')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        # Verify empty state is displayed
        self.assertContains(response, 'empty-state')
        self.assertContains(response, 'No exam attempts yet')
        self.assertContains(response, 'Students haven\'t submitted any exams yet')
    
    def test_empty_state_displays_for_no_filter_results(self):
        """Test that empty state displays when filters return no results (Requirement 2.2)."""
        # Login as teacher
        self.client.login(username='teacher1', password='testpass123')
        
        # Access dashboard with filter that returns no results
        response = self.client.get('/attempts/teacher/dashboard/?exam=999')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        # Verify empty state for no filter results is displayed
        self.assertContains(response, 'empty-state')
        self.assertContains(response, 'No results found')
        self.assertContains(response, 'Try adjusting your filters')
    
    def test_empty_state_displays_for_charts_with_no_data(self):
        """Test that empty state displays in charts when no data available (Requirement 2.3)."""
        # Login as teacher
        self.client.login(username='teacher1', password='testpass123')
        
        # Access dashboard
        response = self.client.get('/attempts/teacher/dashboard/')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        # Verify empty state is displayed in chart sections
        self.assertContains(response, 'No exam data available')
        self.assertContains(response, 'No distribution data')
        self.assertContains(response, 'No subject data available')
    
    def test_empty_state_has_action_button(self):
        """Test that empty state includes action button when appropriate."""
        # Login as teacher
        self.client.login(username='teacher1', password='testpass123')
        
        # Access dashboard
        response = self.client.get('/attempts/teacher/dashboard/')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        # Verify action button is present
        self.assertContains(response, 'Create Your First Exam')
        self.assertContains(response, 'empty-state-action')
    
    def test_empty_state_clear_filters_button(self):
        """Test that empty state includes clear filters button when filters are applied."""
        # Login as teacher
        self.client.login(username='teacher1', password='testpass123')
        
        # Access dashboard with filters
        response = self.client.get('/attempts/teacher/dashboard/?status=submitted')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        # Verify clear filters button is present
        self.assertContains(response, 'Clear All Filters')
