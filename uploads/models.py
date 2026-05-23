from django.db import models
from users.models import Teacher


class UploadedDocument(models.Model):
    """
    Model for storing uploaded PDF and DOCX documents.
    Tracks file metadata and processing status.
    """
    FILE_TYPE_CHOICES = [
        ('PDF', 'PDF Document'),
        ('DOCX', 'Word Document'),
    ]
    
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    file_path = models.CharField(
        max_length=500,
        help_text="Path to the uploaded file"
    )
    file_type = models.CharField(
        max_length=10,
        choices=FILE_TYPE_CHOICES,
        help_text="Type of uploaded document (PDF or DOCX)"
    )
    uploaded_by = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='uploaded_documents',
        help_text="Teacher who uploaded the document"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when document was uploaded"
    )
    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Current processing status of the document"
    )
    
    class Meta:
        db_table = 'uploads_uploadeddocument'
        verbose_name = 'Uploaded Document'
        verbose_name_plural = 'Uploaded Documents'
        indexes = [
            models.Index(fields=['uploaded_by'], name='idx_uploaded_by'),
            models.Index(fields=['processing_status'], name='idx_status'),
            # Composite indexes for performance optimization (Requirement 9.5)
            models.Index(fields=['uploaded_by', 'processing_status'], name='idx_upload_teacher_status'),
            models.Index(fields=['-uploaded_at'], name='idx_upload_date_desc'),
            models.Index(fields=['file_type'], name='idx_upload_file_type'),
        ]
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.file_type} - {self.file_path} ({self.processing_status})"


class ExtractedContent(models.Model):
    """
    Model for storing extracted text and processed questions from documents.
    Links to the source document and stores both raw and processed data.
    """
    document = models.OneToOneField(
        UploadedDocument,
        on_delete=models.CASCADE,
        related_name='extracted_content',
        help_text="Source document for this extracted content"
    )
    raw_text = models.TextField(
        help_text="Raw text extracted from the document"
    )
    processed_questions = models.JSONField(
        default=list,
        help_text="JSON array of extracted/generated questions"
    )
    extracted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when content was extracted"
    )
    
    class Meta:
        db_table = 'uploads_extractedcontent'
        verbose_name = 'Extracted Content'
        verbose_name_plural = 'Extracted Contents'
        indexes = [
            models.Index(fields=['document'], name='idx_document'),
        ]
    
    def __str__(self):
        return f"Extracted content from {self.document.file_path}"
