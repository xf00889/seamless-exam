"""
Tests for exam list pagination functionality.
Requirements: 1.1, 2.1, 2.2, 2.5, 8.1
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from exams.models import Exam
from users.models import Teacher


class ExamListPaginationTest(TestCase):
    """Test pagination in exam list view."""
    
    def setUp(self):
        """Set up test data."""
        # Create a teacher user
        self.user = User.objects.create_user(
            username='testteacher',
            password='testpass123',
            email='teacher@test.com',
            first_name='Test',
            last_name='Teacher'
        )
        
        # Create teacher profile
        self.teacher = Teacher.objects.create(
            user=self.user,
            department='Mathematics'
        )
        
        # Create 25 exams to test pagination (20 per page)
        self.exams = []
        for i in range(25):
            exam = Exam.objects.create(
                title=f'Test Exam {i+1}',
                subject='Test Subject',
                description=f'Description for exam {i+1}',
                duration_minutes=60,
                created_by=self.teacher
            )
            self.exams.append(exam)
        
        self.client = Client()
        self.url = reverse('exam_list')
        
        # Login and set session for teacher authentication
        self.client.login(username='testteacher', password='testpass123')
        session = self.client.session
        session['user_type'] = 'teacher'
        session.save()
    
    def test_pagination_displays_20_items_per_page(self):
        """Test that pagination displays 20 items per page (Requirement 2.5)."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        
        # First page should have 20 items
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj), 20)
        self.assertEqual(page_obj.paginator.count, 25)
        self.assertEqual(page_obj.paginator.num_pages, 2)
    
    def test_pagination_second_page(self):
        """Test that second page displays remaining items (Requirement 2.5)."""
        response = self.client.get(self.url, {'page': 2})
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        # Second page should have 5 items (25 total - 20 on first page)
        self.assertEqual(len(page_obj), 5)
        self.assertEqual(page_obj.number, 2)
    
    def test_pagination_invalid_page_number(self):
        """Test that invalid page number defaults to page 1 (Requirement 8.1)."""
        response = self.client.get(self.url, {'page': 'invalid'})
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        # Should default to page 1
        self.assertEqual(page_obj.number, 1)
    
    def test_pagination_out_of_range_page(self):
        """Test that out of range page number shows last page (Requirement 8.1)."""
        response = self.client.get(self.url, {'page': 999})
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        # Should show last page (page 2)
        self.assertEqual(page_obj.number, 2)
    
    def test_pagination_component_included(self):
        """Test that pagination component is included in template (Requirement 1.1, 2.1)."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check that pagination HTML is present
        self.assertContains(response, 'pagination-container')
        self.assertContains(response, 'Showing')
        self.assertContains(response, 'results')
    
    def test_no_pagination_with_few_exams(self):
        """Test that pagination is hidden when only one page exists (Requirement 1.5)."""
        # Delete most exams, keep only 5
        Exam.objects.filter(id__in=[e.id for e in self.exams[5:]]).delete()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        # Should have only 1 page
        self.assertEqual(page_obj.paginator.num_pages, 1)
        
        # Pagination component should not be visible (has_other_pages is False)
        self.assertFalse(page_obj.has_other_pages())
    
    def test_empty_exam_list(self):
        """Test that empty state is shown when no exams exist (Requirement 2.2)."""
        # Delete all exams
        Exam.objects.all().delete()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check for empty state message
        self.assertContains(response, "You haven't created any exams yet")
