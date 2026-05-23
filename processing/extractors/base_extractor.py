"""
Base extractor abstract class for document text extraction.
"""
from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """
    Abstract base class for document extractors.
    Implements the Liskov Substitution Principle - all extractors
    can be used interchangeably through this interface.
    """
    
    def __init__(self):
        """Initialize the base extractor."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def extract(self, file_path: str) -> str:
        """
        Extract text content from a document file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Extracted text content as a string
            
        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file format is invalid
            Exception: For other extraction errors
        """
        pass
    
    def validate_file_exists(self, file_path: str) -> None:
        """
        Validate that the file exists.
        
        Args:
            file_path: Path to the file
            
        Raises:
            FileNotFoundError: If file does not exist
        """
        import os
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
    
    def validate_file_extension(self, file_path: str, expected_extensions: list) -> None:
        """
        Validate that the file has an expected extension.
        
        Args:
            file_path: Path to the file
            expected_extensions: List of valid extensions (e.g., ['.pdf', '.PDF'])
            
        Raises:
            ValueError: If file extension is not in expected list
        """
        import os
        _, ext = os.path.splitext(file_path)
        if ext not in expected_extensions:
            raise ValueError(
                f"Invalid file extension '{ext}'. Expected one of: {expected_extensions}"
            )
    
    def safe_extract(self, file_path: str) -> Optional[str]:
        """
        Safely extract text with error handling.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Extracted text or None if extraction fails
        """
        try:
            return self.extract(file_path)
        except Exception as e:
            self.logger.error(f"Error extracting text from {file_path}: {e}")
            return None
