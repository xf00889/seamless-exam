"""
Repository for ExtractedContent model.
Provides data access methods for extracted content operations.
"""
from typing import Optional, List, Dict, Any
from django.db.models import QuerySet
from uploads.models import ExtractedContent
from .base_repository import BaseRepository


class ExtractedContentRepository(BaseRepository):
    """
    Repository for ExtractedContent data access.
    Extends BaseRepository with extracted content-specific queries.
    """
    
    def __init__(self):
        """Initialize repository with ExtractedContent model."""
        super().__init__(ExtractedContent)
    
    def get_by_document(self, document_id: int) -> Optional[ExtractedContent]:
        """
        Get extracted content for a specific document.
        
        Args:
            document_id: ID of the uploaded document
            
        Returns:
            ExtractedContent instance if found, None otherwise
        """
        try:
            return self.model.objects.get(document_id=document_id)
        except self.model.DoesNotExist:
            return None
    
    def create_from_document(
        self,
        document_id: int,
        raw_text: str,
        processed_questions: List[Dict[str, Any]] = None
    ) -> ExtractedContent:
        """
        Create extracted content for a document.
        
        Args:
            document_id: ID of the source document
            raw_text: Raw extracted text
            processed_questions: Optional list of processed questions
            
        Returns:
            Created ExtractedContent instance
        """
        if processed_questions is None:
            processed_questions = []
        
        return self.create(
            document_id=document_id,
            raw_text=raw_text,
            processed_questions=processed_questions
        )
    
    def update_questions(
        self,
        content_id: int,
        questions: List[Dict[str, Any]]
    ) -> Optional[ExtractedContent]:
        """
        Update the processed questions for extracted content.
        
        Args:
            content_id: ID of the extracted content
            questions: List of processed questions
            
        Returns:
            Updated ExtractedContent instance if found, None otherwise
        """
        return self.update(content_id, processed_questions=questions)
    
    def get_with_document(self, content_id: int) -> Optional[ExtractedContent]:
        """
        Get extracted content with related document data.
        Uses select_related for optimized query.
        
        Args:
            content_id: ID of the extracted content
            
        Returns:
            ExtractedContent instance with document if found, None otherwise
        """
        try:
            return self.model.objects.select_related('document').get(pk=content_id)
        except self.model.DoesNotExist:
            return None
