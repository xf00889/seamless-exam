"""
PDF text extraction using pdfminer.six and PyPDF2.
"""
from typing import Optional
import logging
from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class PDFExtractor(BaseExtractor):
    """
    Extractor for PDF documents using pdfminer.six as primary
    and PyPDF2 as fallback.
    """
    
    def __init__(self):
        """Initialize PDF extractor."""
        super().__init__()
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required libraries are available."""
        try:
            import pdfminer
            self.pdfminer_available = True
        except ImportError:
            self.logger.warning("pdfminer.six not available")
            self.pdfminer_available = False
        
        try:
            import PyPDF2
            self.pypdf2_available = True
        except ImportError:
            self.logger.warning("PyPDF2 not available")
            self.pypdf2_available = False
        
        if not self.pdfminer_available and not self.pypdf2_available:
            raise ImportError("Neither pdfminer.six nor PyPDF2 is available")
    
    def extract(self, file_path: str) -> str:
        """
        Extract text from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text from all pages
            
        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file is not a PDF
            Exception: For extraction errors
        """
        self.validate_file_exists(file_path)
        self.validate_file_extension(file_path, ['.pdf', '.PDF'])
        
        # Try pdfminer.six first (better quality)
        if self.pdfminer_available:
            try:
                text = self._extract_with_pdfminer(file_path)
                if text and text.strip():
                    return text
            except Exception as e:
                self.logger.warning(f"pdfminer.six extraction failed: {e}")
        
        # Fallback to PyPDF2
        if self.pypdf2_available:
            try:
                text = self._extract_with_pypdf2(file_path)
                if text and text.strip():
                    return text
            except Exception as e:
                self.logger.error(f"PyPDF2 extraction failed: {e}")
                raise
        
        raise Exception("Failed to extract text from PDF with all available methods")
    
    def _extract_with_pdfminer(self, file_path: str) -> str:
        """
        Extract text using pdfminer.six.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        from pdfminer.high_level import extract_text
        
        try:
            text = extract_text(file_path)
            return text
        except Exception as e:
            self.logger.error(f"pdfminer.six extraction error: {e}")
            raise
    
    def _extract_with_pypdf2(self, file_path: str) -> str:
        """
        Extract text using PyPDF2.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text from all pages
        """
        import PyPDF2
        
        text_parts = []
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from all pages
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    
                    if page_text:
                        text_parts.append(page_text)
            
            return '\n'.join(text_parts)
        
        except Exception as e:
            self.logger.error(f"PyPDF2 extraction error: {e}")
            raise
    
    def extract_page(self, file_path: str, page_number: int) -> str:
        """
        Extract text from a specific page.
        
        Args:
            file_path: Path to PDF file
            page_number: Page number (0-indexed)
            
        Returns:
            Extracted text from the specified page
        """
        self.validate_file_exists(file_path)
        self.validate_file_extension(file_path, ['.pdf', '.PDF'])
        
        if self.pypdf2_available:
            import PyPDF2
            
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    if page_number < 0 or page_number >= len(pdf_reader.pages):
                        raise ValueError(f"Invalid page number: {page_number}")
                    
                    page = pdf_reader.pages[page_number]
                    return page.extract_text()
            
            except Exception as e:
                self.logger.error(f"Error extracting page {page_number}: {e}")
                raise
        else:
            raise NotImplementedError("Page extraction requires PyPDF2")
    
    def get_page_count(self, file_path: str) -> int:
        """
        Get the number of pages in a PDF.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Number of pages
        """
        self.validate_file_exists(file_path)
        self.validate_file_extension(file_path, ['.pdf', '.PDF'])
        
        if self.pypdf2_available:
            import PyPDF2
            
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    return len(pdf_reader.pages)
            except Exception as e:
                self.logger.error(f"Error getting page count: {e}")
                raise
        else:
            raise NotImplementedError("Page count requires PyPDF2")
