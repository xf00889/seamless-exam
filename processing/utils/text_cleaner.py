"""
Text cleaning utility for removing formatting artifacts and normalizing text.
"""
import re


class TextCleaner:
    """
    Utility class for cleaning extracted text from documents.
    Removes formatting artifacts while preserving content.
    """
    
    def __init__(self):
        """Initialize the text cleaner with common patterns."""
        # Patterns for common artifacts
        self.excessive_whitespace_pattern = re.compile(r'\s+')
        self.page_number_pattern = re.compile(r'^\s*\d+\s*$', re.MULTILINE)
        self.header_footer_pattern = re.compile(r'^[-_=]{3,}$', re.MULTILINE)
        
    def clean(self, text: str) -> str:
        """
        Clean text by removing formatting artifacts.
        
        Args:
            text: Raw text extracted from document
            
        Returns:
            Cleaned text with artifacts removed
        """
        if not text:
            return ""
        
        # Remove null bytes and other control characters
        text = self._remove_control_characters(text)
        
        # Remove page numbers (standalone numbers on lines)
        text = self.page_number_pattern.sub('', text)
        
        # Remove header/footer separators
        text = self.header_footer_pattern.sub('', text)
        
        # Normalize whitespace (multiple spaces/tabs to single space)
        text = self.excessive_whitespace_pattern.sub(' ', text)
        
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        
        # Remove empty lines
        lines = [line for line in lines if line]
        
        # Join lines back together
        text = '\n'.join(lines)
        
        return text.strip()
    
    def _remove_control_characters(self, text: str) -> str:
        """
        Remove control characters except newlines and tabs.
        
        Args:
            text: Input text
            
        Returns:
            Text with control characters removed
        """
        # Keep newlines and tabs, remove other control characters
        return ''.join(char for char in text if char == '\n' or char == '\t' or not char.isprintable() is False or ord(char) >= 32)
    
    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized whitespace
        """
        return self.excessive_whitespace_pattern.sub(' ', text).strip()
    
    def remove_extra_newlines(self, text: str, max_consecutive: int = 2) -> str:
        """
        Remove excessive consecutive newlines.
        
        Args:
            text: Input text
            max_consecutive: Maximum number of consecutive newlines to keep
            
        Returns:
            Text with excessive newlines removed
        """
        pattern = re.compile(r'\n{' + str(max_consecutive + 1) + r',}')
        return pattern.sub('\n' * max_consecutive, text)
