from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from users.models import Teacher
from uploads.models import UploadedDocument, ExtractedContent
from services.upload_service import UploadService, UploadError
from repositories.upload_repository import UploadedDocumentRepository
from repositories.extracted_content_repository import ExtractedContentRepository


class UploadedDocumentModelTest(TestCase):
    """Test cases for UploadedDocument model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testteacher', password='testpass')
        self.teacher = Teacher.objects.create(user=self.user)
    
    def test_create_uploaded_document(self):
        """Test creating an UploadedDocument instance."""
        document = UploadedDocument.objects.create(
            file_path='uploads/documents/test.pdf',
            file_type='PDF',
            uploaded_by=self.teacher,
            processing_status='pending'
        )
        
        self.assertEqual(document.file_type, 'PDF')
        self.assertEqual(document.processing_status, 'pending')
        self.assertEqual(document.uploaded_by, self.teacher)
        self.assertIsNotNone(document.uploaded_at)
    
    def test_document_string_representation(self):
        """Test __str__ method of UploadedDocument."""
        document = UploadedDocument.objects.create(
            file_path='uploads/documents/test.pdf',
            file_type='PDF',
            uploaded_by=self.teacher
        )
        
        expected = "PDF - uploads/documents/test.pdf (pending)"
        self.assertEqual(str(document), expected)


class ExtractedContentModelTest(TestCase):
    """Test cases for ExtractedContent model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testteacher', password='testpass')
        self.teacher = Teacher.objects.create(user=self.user)
        self.document = UploadedDocument.objects.create(
            file_path='uploads/documents/test.pdf',
            file_type='PDF',
            uploaded_by=self.teacher
        )
    
    def test_create_extracted_content(self):
        """Test creating an ExtractedContent instance."""
        content = ExtractedContent.objects.create(
            document=self.document,
            raw_text='Sample extracted text',
            processed_questions=[{'question': 'What is 2+2?', 'answer': '4'}]
        )
        
        self.assertEqual(content.document, self.document)
        self.assertEqual(content.raw_text, 'Sample extracted text')
        self.assertEqual(len(content.processed_questions), 1)
        self.assertIsNotNone(content.extracted_at)


class UploadServiceTest(TestCase):
    """Test cases for UploadService."""
    
    def setUp(self):
        """Set up test data."""
        self.service = UploadService()
        self.user = User.objects.create_user(username='testteacher', password='testpass')
        self.teacher = Teacher.objects.create(user=self.user)
    
    def test_validate_file_pdf(self):
        """Test file validation for PDF files."""
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            b"PDF content",
            content_type="application/pdf"
        )
        
        is_valid, error = self.service.validate_file(pdf_file)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_file_docx(self):
        """Test file validation for DOCX files."""
        docx_file = SimpleUploadedFile(
            "test.docx",
            b"DOCX content",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        is_valid, error = self.service.validate_file(docx_file)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_file_invalid_extension(self):
        """Test file validation rejects invalid extensions."""
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"Text content",
            content_type="text/plain"
        )
        
        is_valid, error = self.service.validate_file(invalid_file)
        self.assertFalse(is_valid)
        self.assertIn("Invalid file type", error)
    
    def test_validate_file_too_large(self):
        """Test file validation rejects files that are too large."""
        # Create a file larger than 50 MB
        large_file = SimpleUploadedFile(
            "large.pdf",
            b"x" * (51 * 1024 * 1024),  # 51 MB
            content_type="application/pdf"
        )
        
        is_valid, error = self.service.validate_file(large_file)
        self.assertFalse(is_valid)
        self.assertIn("exceeds maximum", error)
    
    def test_get_file_type_pdf(self):
        """Test getting file type for PDF."""
        file_type = self.service.get_file_type("document.pdf")
        self.assertEqual(file_type, "PDF")
    
    def test_get_file_type_docx(self):
        """Test getting file type for DOCX."""
        file_type = self.service.get_file_type("document.docx")
        self.assertEqual(file_type, "DOCX")
    
    def test_get_file_type_invalid(self):
        """Test getting file type for invalid extension."""
        with self.assertRaises(UploadError):
            self.service.get_file_type("document.txt")


class UploadRepositoryTest(TestCase):
    """Test cases for UploadedDocumentRepository."""
    
    def setUp(self):
        """Set up test data."""
        self.repository = UploadedDocumentRepository()
        self.user = User.objects.create_user(username='testteacher', password='testpass')
        self.teacher = Teacher.objects.create(user=self.user)
    
    def test_get_by_teacher(self):
        """Test getting documents by teacher."""
        doc1 = UploadedDocument.objects.create(
            file_path='test1.pdf',
            file_type='PDF',
            uploaded_by=self.teacher
        )
        doc2 = UploadedDocument.objects.create(
            file_path='test2.pdf',
            file_type='PDF',
            uploaded_by=self.teacher
        )
        
        documents = self.repository.get_by_teacher(self.teacher.pk)
        self.assertEqual(documents.count(), 2)
    
    def test_get_by_status(self):
        """Test getting documents by status."""
        UploadedDocument.objects.create(
            file_path='test1.pdf',
            file_type='PDF',
            uploaded_by=self.teacher,
            processing_status='pending'
        )
        UploadedDocument.objects.create(
            file_path='test2.pdf',
            file_type='PDF',
            uploaded_by=self.teacher,
            processing_status='completed'
        )
        
        pending = self.repository.get_by_status('pending')
        self.assertEqual(pending.count(), 1)
    
    def test_update_status(self):
        """Test updating document status."""
        document = UploadedDocument.objects.create(
            file_path='test.pdf',
            file_type='PDF',
            uploaded_by=self.teacher,
            processing_status='pending'
        )
        
        updated = self.repository.update_status(document.id, 'completed')
        self.assertEqual(updated.processing_status, 'completed')


class ExtractedContentRepositoryTest(TestCase):
    """Test cases for ExtractedContentRepository."""
    
    def setUp(self):
        """Set up test data."""
        self.repository = ExtractedContentRepository()
        self.user = User.objects.create_user(username='testteacher', password='testpass')
        self.teacher = Teacher.objects.create(user=self.user)
        self.document = UploadedDocument.objects.create(
            file_path='test.pdf',
            file_type='PDF',
            uploaded_by=self.teacher
        )
    
    def test_get_by_document(self):
        """Test getting extracted content by document."""
        content = ExtractedContent.objects.create(
            document=self.document,
            raw_text='Test text'
        )
        
        retrieved = self.repository.get_by_document(self.document.id)
        self.assertEqual(retrieved, content)
    
    def test_create_from_document(self):
        """Test creating extracted content from document."""
        questions = [{'question': 'What is 2+2?', 'answer': '4'}]
        content = self.repository.create_from_document(
            self.document.id,
            'Test text',
            questions
        )
        
        self.assertEqual(content.document, self.document)
        self.assertEqual(content.raw_text, 'Test text')
        self.assertEqual(len(content.processed_questions), 1)
    
    def test_update_questions(self):
        """Test updating processed questions."""
        content = ExtractedContent.objects.create(
            document=self.document,
            raw_text='Test text',
            processed_questions=[]
        )
        
        new_questions = [{'question': 'What is 2+2?', 'answer': '4'}]
        updated = self.repository.update_questions(content.id, new_questions)
        
        self.assertEqual(len(updated.processed_questions), 1)
