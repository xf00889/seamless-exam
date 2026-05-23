"""
Tests for document upload forms.
Validates form validation logic.
Requirements: 3.4
"""

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from uploads.forms import DocumentUploadForm


class DocumentUploadFormTest(TestCase):
    """Test cases for DocumentUploadForm validation."""
    
    def test_valid_pdf_upload(self):
        """Test form with valid PDF file."""
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            b"PDF content here",
            content_type="application/pdf"
        )
        form = DocumentUploadForm(files={'document': pdf_file})
        self.assertTrue(form.is_valid())
    
    def test_valid_docx_upload(self):
        """Test form with valid DOCX file."""
        docx_file = SimpleUploadedFile(
            "test.docx",
            b"DOCX content here",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        form = DocumentUploadForm(files={'document': docx_file})
        self.assertTrue(form.is_valid())
    
    def test_no_file_uploaded(self):
        """Test form with no file uploaded."""
        form = DocumentUploadForm(files={})
        self.assertFalse(form.is_valid())
        self.assertIn('document', form.errors)
    
    def test_invalid_file_type(self):
        """Test form with invalid file type (Requirement 3.4)."""
        txt_file = SimpleUploadedFile(
            "test.txt",
            b"Text content here",
            content_type="text/plain"
        )
        form = DocumentUploadForm(files={'document': txt_file})
        self.assertFalse(form.is_valid())
        self.assertIn('document', form.errors)
    
    def test_empty_file(self):
        """Test form with empty file."""
        empty_file = SimpleUploadedFile(
            "test.pdf",
            b"",
            content_type="application/pdf"
        )
        form = DocumentUploadForm(files={'document': empty_file})
        self.assertFalse(form.is_valid())
        self.assertIn('document', form.errors)


