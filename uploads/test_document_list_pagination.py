"""
Tests for document_list pagination functionality.
Validates Requirements: 5.4
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import Teacher
from uploads.models import UploadedDocument
from datetime import datetime

User = get_user_model()


class DocumentListPaginationTest(TestCase):
    """Test pagination in document_list view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create a teacher user
        self.user = User.objects.create_user(
            username='teacher1',
            password='testpass123',
            email='teacher1@test.com',
            first_name='Test',
            last_name='Teacher'
        )
        
        self.teacher = Teacher.objects.create(
            user=self.user,
            department='Science'
        )
        
        # Create 25 documents to test pagination (20 per page)
        self.documents = []
        for i in range(25):
            doc = UploadedDocument.objects.create(
                file_path=f'media/test_doc_{i}.pdf',
                file_type='PDF',
                uploaded_by=self.teacher,
                processing_status='pending'
            )
            self.documents.append(doc)
        
        # Login
        self.client.login(username='teacher1', password='testpass123')
    
    def test_pagination_displays_20_items_per_page(self):
        """Test that first page shows 20 documents."""
        response = self.client.get(reverse('uploads:document_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj), 20)
        self.assertEqual(page_obj.paginator.count, 25)
        self.assertEqual(page_obj.paginator.num_pages, 2)
    
    def test_pagination_second_page_shows_remaining_items(self):
        """Test that second page shows remaining 5 documents."""
        response = self.client.get(reverse('uploads:document_list') + '?page=2')
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        self.assertEqual(len(page_obj), 5)
        self.assertEqual(page_obj.number, 2)
    
    def test_pagination_invalid_page_defaults_to_first(self):
        """Test that invalid page number defaults to page 1."""
        response = self.client.get(reverse('uploads:document_list') + '?page=invalid')
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        self.assertEqual(page_obj.number, 1)
        self.assertEqual(len(page_obj), 20)
    
    def test_pagination_out_of_range_shows_last_page(self):
        """Test that out of range page number shows last page."""
        response = self.client.get(reverse('uploads:document_list') + '?page=999')
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        self.assertEqual(page_obj.number, 2)  # Last page
        self.assertEqual(len(page_obj), 5)
    
    def test_pagination_hidden_with_few_documents(self):
        """Test that pagination is hidden when only one page exists."""
        # Delete documents to have only 10
        UploadedDocument.objects.filter(
            id__in=[doc.id for doc in self.documents[10:]]
        ).delete()
        
        response = self.client.get(reverse('uploads:document_list'))
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        # Should have only 1 page
        self.assertEqual(page_obj.paginator.num_pages, 1)
        self.assertFalse(page_obj.has_other_pages())
    
    def test_pagination_component_receives_page_obj(self):
        """Test that template receives page_obj for pagination component."""
        response = self.client.get(reverse('uploads:document_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        
        # Verify page_obj has required attributes
        page_obj = response.context['page_obj']
        self.assertTrue(hasattr(page_obj, 'number'))
        self.assertTrue(hasattr(page_obj, 'paginator'))
        self.assertTrue(hasattr(page_obj, 'has_previous'))
        self.assertTrue(hasattr(page_obj, 'has_next'))
    
    def test_total_count_displayed(self):
        """Test that total document count is displayed."""
        response = self.client.get(reverse('uploads:document_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 25)
    
    def test_empty_state_when_no_documents(self):
        """Test empty state when teacher has no documents."""
        # Delete all documents
        UploadedDocument.objects.all().delete()
        
        response = self.client.get(reverse('uploads:document_list'))
        
        self.assertEqual(response.status_code, 200)
        # Should not have page_obj or it should be empty
        page_obj = response.context.get('page_obj')
        if page_obj:
            self.assertEqual(len(page_obj), 0)
    
    def test_documents_ordered_by_upload_date_desc(self):
        """Test that documents are ordered by upload date (newest first)."""
        response = self.client.get(reverse('uploads:document_list'))
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        # Get the documents from page
        docs = list(page_obj)
        
        # Verify they are in descending order by uploaded_at
        for i in range(len(docs) - 1):
            self.assertGreaterEqual(docs[i].uploaded_at, docs[i + 1].uploaded_at)
    
    def test_teacher_only_sees_own_documents(self):
        """Test that teacher only sees their own documents."""
        # Create another teacher with documents
        other_user = User.objects.create_user(
            username='teacher2',
            password='testpass123',
            email='teacher2@test.com',
            first_name='Other',
            last_name='Teacher'
        )
        
        other_teacher = Teacher.objects.create(
            user=other_user,
            department='Math'
        )
        
        # Create documents for other teacher
        for i in range(5):
            UploadedDocument.objects.create(
                file_path=f'media/other_doc_{i}.pdf',
                file_type='PDF',
                uploaded_by=other_teacher,
                processing_status='pending'
            )
        
        response = self.client.get(reverse('uploads:document_list'))
        
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        
        # Should still only see 25 documents (not 30)
        self.assertEqual(page_obj.paginator.count, 25)
        
        # Verify all documents belong to the logged-in teacher
        for doc in page_obj:
            self.assertEqual(doc.uploaded_by_id, self.teacher.pk)
