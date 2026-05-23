"""
Document Processing Service for orchestrating extraction and question generation.
Implements business logic for processing uploaded documents.
"""
import os
import logging
from typing import List, Dict, Optional
from django.conf import settings

from repositories.upload_repository import UploadedDocumentRepository
from repositories.extracted_content_repository import ExtractedContentRepository
from processing.extractors import PDFExtractor, DOCXExtractor

from uploads.models import UploadedDocument, ExtractedContent

logger = logging.getLogger(__name__)


class DocumentProcessingError(Exception):
    """Custom exception for document processing errors."""
    pass


class DocumentProcessingService:
    """
    Service for orchestrating document extraction and question generation.
    Coordinates extractors and generators to process uploaded documents.
    """
    
    def __init__(self):
        """Initialize service with repositories and processors."""
        self.document_repository = UploadedDocumentRepository()
        self.content_repository = ExtractedContentRepository()
        
        # Initialize extractors
        self.pdf_extractor = PDFExtractor()
        self.docx_extractor = DOCXExtractor()
    
    def process_document(
        self,
        document_id: int
    ) -> ExtractedContent:
        """
        Process a document: extract text only.
        
        Args:
            document_id: ID of the document to process
            
        Returns:
            ExtractedContent instance with processed data
            
        Raises:
            DocumentProcessingError: If processing fails
        """
        # Get document
        document = self.document_repository.get_by_id(document_id)
        if not document:
            raise DocumentProcessingError(f"Document with ID {document_id} not found")
        
        try:
            # Update status to processing
            self.document_repository.update_status(document_id, 'processing')
            
            # Extract text from document
            raw_text = self._extract_text(document)
            
            # Save extracted content (text only)
            extracted_content = self._save_extracted_content(
                document_id,
                raw_text,
                []  # No questions generated
            )
            
            # Update status to completed
            self.document_repository.update_status(document_id, 'completed')
            
            logger.info(f"Successfully processed document {document_id}")
            return extracted_content
            
        except Exception as e:
            # Update status to failed
            self.document_repository.update_status(document_id, 'failed')
            logger.error(f"Error processing document {document_id}: {str(e)}")
            raise DocumentProcessingError(f"Failed to process document: {str(e)}")
    
    def _extract_text(self, document: UploadedDocument) -> str:
        """
        Extract text from document based on file type.
        
        Args:
            document: UploadedDocument instance
            
        Returns:
            Extracted text string
            
        Raises:
            DocumentProcessingError: If extraction fails
        """
        # Get full file path
        file_path = os.path.join(settings.MEDIA_ROOT, document.file_path)
        
        if not os.path.exists(file_path):
            raise DocumentProcessingError(f"File not found: {file_path}")
        
        try:
            # Select appropriate extractor
            if document.file_type == 'PDF':
                raw_text = self.pdf_extractor.extract(file_path)
            elif document.file_type == 'DOCX':
                raw_text = self.docx_extractor.extract(file_path)
            else:
                raise DocumentProcessingError(f"Unsupported file type: {document.file_type}")
            
            if not raw_text or len(raw_text.strip()) < 10:
                raise DocumentProcessingError("Extracted text is empty or too short")
            
            return raw_text
            
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise DocumentProcessingError(f"Text extraction failed: {str(e)}")

    
    def _save_extracted_content(
        self,
        document_id: int,
        raw_text: str,
        processed_questions: List[Dict[str, any]]
    ) -> ExtractedContent:
        """
        Save extracted content to database.
        
        Args:
            document_id: ID of the source document
            raw_text: Extracted raw text
            processed_questions: List of generated questions (empty for manual-only workflow)
            
        Returns:
            Created ExtractedContent instance
        """
        # Check if content already exists
        existing = self.content_repository.get_by_document(document_id)
        
        if existing:
            # Update existing content
            return self.content_repository.update(
                existing.id,
                raw_text=raw_text,
                processed_questions=processed_questions
            )
        else:
            # Create new content
            return self.content_repository.create(
                document_id=document_id,
                raw_text=raw_text,
                processed_questions=processed_questions
            )
    
    def get_extracted_content(self, document_id: int) -> Optional[ExtractedContent]:
        """
        Get extracted content for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            ExtractedContent instance if found, None otherwise
        """
        return self.content_repository.get_by_document(document_id)


