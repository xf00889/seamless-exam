"""
Test pagination functionality for teacher dashboard
Requirement: 3.4
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from users.models import Teacher, Student, Class
from exams.models import Exam, Question, QuestionType
from attempts.models import Attempt, AttemptStatus, Answer
from decimal import Decimal


class TeacherDashboardPaginationTest(TestCase):
    """Test pagination in teacher dashboard"""
    
    def setUp(self):
        """Set up test data"""
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
            department='Mathematics'
        )
        
        # Create class
        self.test_class = Class.objects.create(
            grade_level='Grade 12',
            strand='STEM',
            section='A',
            teacher=self.teacher
        )
        
        # Create students
        self.students = []
        for i in range(15):  # Create 15 students to test pagination
            student = Student.objects.create(
                first_name=f'Student{i}',
                last_name=f'Test{i}',
                school_id=f'S{i:03d}',
                password_hash='pbkdf2_sha256$260000$test$test',  # Dummy hash
                class_assigned=self.test_class
            )
            self.students.append(student)
        
        # Create exam
        self.exam = Exam.objects.create(
            title='Test Exam',
            description='Test Description',
            duration_minutes=60,
            is_active=True,
            created_by=self.teacher
        )
        
        # Create question
        self.question = Question.objects.create(
            exam=self.exam,
            question_text='Test Question',
            question_type=QuestionType.MCQ,
            points=Decimal('10.00'),
            correct_answer='A'
        )
        
        # Create attempts for all students
        for student in self.students:
            attempt = Attempt.objects.create(
                student=student,
                exam=self.exam,
                status=AttemptStatus.SUBMITTED,
                total_score=Decimal('8.00')
            )
            # Create answer
            Answer.objects.create(
                attempt=attempt,
                question=self.question,
                answer_text='A',
                is_correct=True,
                points_earned=Decimal('8.00')
            )
        
        self.client = Client()
    
    def test_pagination_exists(self):
        """Test that pagination is present when there are many attempts"""
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse('teacher_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        
        # Check that pagination object has correct properties
        page_obj = response.context['page_obj']
        self.assertTrue(page_obj.has_other_pages())
        self.assertEqual(page_obj.paginator.count, 15)
        self.assertEqual(page_obj.paginator.num_pages, 2)  # 15 items / 10 per page = 2 pages
    
    def test_first_page_shows_correct_items(self):
        """Test that first page shows correct number of items"""
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse('teacher_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        # First page should have 10 items
        self.assertEqual(len(page_obj.object_list), 10)
        self.assertEqual(page_obj.number, 1)
        self.assertTrue(page_obj.has_next())
        self.assertFalse(page_obj.has_previous())
    
    def test_second_page_shows_remaining_items(self):
        """Test that second page shows remaining items"""
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse('teacher_dashboard'), {'page': 2})
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        # Second page should have 5 items (15 total - 10 on first page)
        self.assertEqual(len(page_obj.object_list), 5)
        self.assertEqual(page_obj.number, 2)
        self.assertFalse(page_obj.has_next())
        self.assertTrue(page_obj.has_previous())
    
    def test_pagination_with_filters(self):
        """Test that pagination works with filters applied"""
        self.client.force_login(self.teacher_user)
        response = self.client.get(
            reverse('teacher_dashboard'),
            {'exam': self.exam.id, 'page': 1}
        )
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        # Should still have pagination with filters
        self.assertTrue(page_obj.has_other_pages())
        self.assertEqual(page_obj.paginator.count, 15)
    
    def test_invalid_page_number_defaults_to_first(self):
        """Test that invalid page number defaults to first page"""
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse('teacher_dashboard'), {'page': 'invalid'})
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        # Should default to page 1
        self.assertEqual(page_obj.number, 1)
    
    def test_page_number_too_high_shows_last_page(self):
        """Test that page number beyond range shows last page"""
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse('teacher_dashboard'), {'page': 999})
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        # Should show last page
        self.assertEqual(page_obj.number, page_obj.paginator.num_pages)
    
    def test_pagination_info_display(self):
        """Test that pagination info is correctly calculated"""
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse('teacher_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        # Check pagination info
        self.assertEqual(page_obj.start_index(), 1)
        self.assertEqual(page_obj.end_index(), 10)
        self.assertEqual(page_obj.paginator.count, 15)
    
    def test_no_pagination_with_few_items(self):
        """Test that pagination is not shown when items fit on one page"""
        # Delete some attempts to have less than 10
        attempts_to_delete = list(Attempt.objects.all()[:10].values_list('id', flat=True))
        Attempt.objects.filter(id__in=attempts_to_delete).delete()
        
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse('teacher_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        # Should not have other pages
        self.assertFalse(page_obj.has_other_pages())
        self.assertEqual(page_obj.paginator.num_pages, 1)
