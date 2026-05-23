"""
Repository for UploadedDocument model.
Provides data access methods for document upload operations.
"""
from typing import Optional, List
from django.db.models import QuerySet
from uploads.models import UploadedDocument
from .base_repository import BaseRepository


class UploadedDocumentRepository(BaseRepository):
    """
    Repository for UploadedDocument data access.
    Extends BaseRepository with document-specific queries.
    """
    
    def __init__(self):
        """Initialize repository with UploadedDocument model."""
        super().__init__(UploadedDocument)
    
    def get_by_teacher(self, teacher_id: int) -> QuerySet:
        """
        Get all documents uploaded by a specific teacher with optimized queries.
        Uses select_related for uploaded_by foreign key.
        
        Args:
            teacher_id: ID of the teacher
            
        Returns:
            QuerySet of UploadedDocument instances with related data prefetched
            
        Requirements: 9.5
        """
        return self.filter(uploaded_by_id=teacher_id).select_related('uploaded_by')
    
    def get_by_status(self, status: str) -> QuerySet:
        """
        Get all documents with a specific processing status.
        
        Args:
            status: Processing status (pending, processing, completed, failed)
            
        Returns:
            QuerySet of UploadedDocument instances
        """
        return self.filter(processing_status=status)
    
    def get_pending_documents(self) -> QuerySet:
        """
        Get all documents pending processing.
        
        Returns:
            QuerySet of pending UploadedDocument instances
        """
        return self.get_by_status('pending')
    
    def update_status(self, document_id: int, status: str) -> Optional[UploadedDocument]:
        """
        Update the processing status of a document.
        
        Args:
            document_id: ID of the document
            status: New processing status
            
        Returns:
            Updated UploadedDocument instance if found, None otherwise
        """
        return self.update(document_id, processing_status=status)
    
    def get_by_file_type(self, file_type: str, teacher_id: Optional[int] = None) -> QuerySet:
        """
        Get documents by file type, optionally filtered by teacher.
        
        Args:
            file_type: File type (PDF or DOCX)
            teacher_id: Optional teacher ID to filter by
            
        Returns:
            QuerySet of UploadedDocument instances
        """
        queryset = self.filter(file_type=file_type)
        if teacher_id:
            queryset = queryset.filter(uploaded_by_id=teacher_id)
        return queryset
