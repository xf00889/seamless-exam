"""
Tests for exam_takers view pagination.
Validates Requirements 5.4 - pagination for exam_takers.html
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from users.models import Teacher, Student
from exams.models import Exam, Question, QuestionType
from attempts.models import Attempt, AttemptStatus
from decimal import Decimal


class ExamTakersPaginationTest(TestCase):
    """Test pagination functionality for exam takers view."""
    
    def setUp(self):
        """Set up test data."""
        # Create teacher user
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            password='testpass123',
            first_name='Test',
            last_name='Teacher'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            department='Mathematics'
        )
        
        # Create exam
        self.exam = Exam.objects.create(
            title='Test Exam',
            description='Test Description',
            duration_minutes=60,
            created_by=self.teacher,
            is_active=True
        )
        
        # Create a question for the exam
        self.question = Question.objects.create(
            exam=self.exam,
            question_text='Test Question',
            question_type=QuestionType.MCQ,
            correct_answer={'answer': 'A'},
            points=Decimal('10.00'),
            order_index=1
        )
        
        # Create 25 students with attempts (to test pagination with 20 per page)
        self.students = []
        self.attempts = []
        for i in range(25):
            student = Student.objects.create(
                school_id=f'S{i:03d}',
                first_name=f'Student{i}',
                last_name='Test'
            )
            student.set_password('testpass123')
            student.save()
            self.students.append(student)
            
            # Create submitted attempt
            attempt = Attempt.objects.create(
                student=student,
                exam=self.exam,
                status=AttemptStatus.SUBMITTED,
                total_score=Decimal('8.00')
            )
            self.attempts.append(attempt)
        
        self.client = Client()
        self.client.login(username='teacher1', password='testpass123')
        self.url = reverse('exam_takers', kwargs={'exam_id': self.exam.id})
    
    def test_pagination_exists_with_many_takers(self):
        """Test that pagination controls appear when there are more than 20 takers."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertTrue(response.context['page_obj'].has_other_pages())
        self.assertEqual(response.context['page_obj'].paginator.num_pages, 2)
    
    def test_first_page_shows_20_items(self):
        """Test that the first page shows exactly 20 items."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['takers_data']), 20)
        self.assertEqual(response.context['page_obj'].number, 1)
    
    def test_second_page_shows_remaining_items(self):
        """Test that the second page shows the remaining 5 items."""
        response = self.client.get(self.url + '?page=2')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['takers_data']), 5)
        self.assertEqual(response.context['page_obj'].number, 2)
    
    def test_invalid_page_number_defaults_to_first_page(self):
        """Test that invalid page numbers default to page 1."""
        response = self.client.get(self.url + '?page=invalid')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].number, 1)
    
    def test_out_of_range_page_shows_last_page(self):
        """Test that out of range page numbers show the last page."""
        response = self.client.get(self.url + '?page=999')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].number, 2)
    
    def test_total_takers_count_accurate(self):
        """Test that total_takers reflects all takers, not just current page."""
        response = self.client.get(self.url + '?page=2')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_takers'], 25)
    
    def test_no_pagination_with_few_takers(self):
        """Test that pagination is hidden when there are 20 or fewer takers."""
        # Delete some attempts to get under 20
        Attempt.objects.filter(student__in=self.students[15:]).delete()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['page_obj'].has_other_pages())
    
    def test_pagination_preserves_exam_context(self):
        """Test that exam details are preserved across pages."""
        response = self.client.get(self.url + '?page=2')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['exam'].id, self.exam.id)
        self.assertEqual(response.context['total_possible_points'], 10.0)
        self.assertEqual(response.context['question_count'], 1)
    
    def test_takers_data_structure_maintained(self):
        """Test that takers_data maintains correct structure with pagination."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        takers_data = response.context['takers_data']
        
        # Check first item has correct structure
        self.assertIn('attempt', takers_data[0])
        self.assertIn('student', takers_data[0])
        self.assertIn('percentage', takers_data[0])
        self.assertIn('total_possible', takers_data[0])
    
    def test_only_submitted_and_graded_attempts_shown(self):
        """Test that only submitted and graded attempts appear in the list."""
        # Create an in-progress attempt
        in_progress_student = Student.objects.create(
            school_id='S999',
            first_name='InProgress',
            last_name='Student'
        )
        in_progress_student.set_password('testpass123')
        in_progress_student.save()
        
        Attempt.objects.create(
            student=in_progress_student,
            exam=self.exam,
            status=AttemptStatus.IN_PROGRESS,
            total_score=Decimal('0.00')
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        # Should still be 25 (not 26)
        self.assertEqual(response.context['total_takers'], 25)
