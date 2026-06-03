"""
Input sanitization service for security.
Provides utilities to sanitize user inputs and prevent XSS attacks.
Requirements: 13.5
"""
import re
import html
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger('services')


class InputSanitizer:
    """
    Service for sanitizing user inputs to prevent security vulnerabilities.
    Provides methods to clean and validate various types of user input.
    """
    
    # Patterns for validation
    ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_]+$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    SCHOOL_ID_PATTERN = re.compile(r'^[a-zA-Z0-9\-_]+$')
    
    # Dangerous HTML tags to strip
    DANGEROUS_TAGS = [
        'script', 'iframe', 'object', 'embed', 'applet',
        'meta', 'link', 'style', 'base', 'form'
    ]
    
    # Dangerous HTML attributes to strip
    DANGEROUS_ATTRIBUTES = [
        'onclick', 'onload', 'onerror', 'onmouseover', 'onmouseout',
        'onfocus', 'onblur', 'onchange', 'onsubmit', 'javascript:'
    ]
    
    @staticmethod
    def sanitize_html(text: Optional[str]) -> str:
        """
        Sanitize HTML content to prevent XSS attacks.
         
        Escapes HTML special characters and removes dangerous tags/attributes.
        Use this for user-generated content that will be displayed in HTML.
        
        Args:
            text: Raw text input from user
            
        Returns:
            Sanitized text safe for HTML display
            
        Requirements: 13.5
        """
        if not text:
            return ''
        
        # Convert to string if not already
        text = str(text)
        
        # Escape HTML special characters
        sanitized = html.escape(text)
        
        return sanitized
    
    @staticmethod
    def sanitize_text(text: Optional[str], max_length: Optional[int] = None) -> str:
        """
        Sanitize plain text input.
        
        Strips leading/trailing whitespace and optionally truncates to max length.
        Use this for text fields like names, titles, etc.
        
        Args:
            text: Raw text input from user
            max_length: Optional maximum length to truncate to
            
        Returns:
            Sanitized text
            
        Requirements: 13.5
        """
        if not text:
            return ''
        
        # Convert to string and strip whitespace
        sanitized = str(text).strip()
        
        # Remove null bytes (security risk)
        sanitized = sanitized.replace('\x00', '')
        
        # Truncate if max_length specified
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def sanitize_filename(filename: Optional[str]) -> str:
        """
        Sanitize a filename to prevent path traversal and other attacks.
        
        Removes path separators and dangerous characters.
        Use this for uploaded file names.
        
        Args:
            filename: Original filename from upload
            
        Returns:
            Sanitized filename safe for filesystem storage
            
        Requirements: 13.1, 13.5
        """
        if not filename:
            return 'file'
        
        # Convert to string
        filename = str(filename)
        
        # Remove path separators (prevent directory traversal)
        filename = filename.replace('/', '_').replace('\\', '_')
        
        # Remove null bytes
        filename = filename.replace('\x00', '')
        
        # Remove or replace dangerous characters
        # Keep only alphanumeric, dash, underscore, dot
        safe_chars = []
        for char in filename:
            if char.isalnum() or char in ('-', '_', '.'):
                safe_chars.append(char)
            elif char == ' ':
                safe_chars.append('_')
        
        sanitized = ''.join(safe_chars)
        
        # Ensure filename is not empty
        if not sanitized or sanitized == '.':
            sanitized = 'file'
        
        # Limit length
        if len(sanitized) > 255:
            # Preserve extension if present
            parts = sanitized.rsplit('.', 1)
            if len(parts) == 2:
                name, ext = parts
                max_name_length = 255 - len(ext) - 1
                sanitized = name[:max_name_length] + '.' + ext
            else:
                sanitized = sanitized[:255]
        
        return sanitized
    
    @staticmethod
    def sanitize_school_id(school_id: Optional[str]) -> str:
        """
        Sanitize school ID input.
        
        Ensures school ID contains only allowed characters.
        
        Args:
            school_id: Raw school ID input
            
        Returns:
            Sanitized school ID
            
        Requirements: 13.5
        """
        if not school_id:
            return ''
        
        # Convert to string and strip whitespace
        sanitized = str(school_id).strip()
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Keep only alphanumeric, dash, underscore
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c in ('-', '_'))
        
        return sanitized
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any], text_fields: list = None, html_fields: list = None) -> Dict[str, Any]:
        """
        Sanitize a dictionary of user inputs.
        
        Applies appropriate sanitization to each field based on its type.
        
        Args:
            data: Dictionary of user inputs
            text_fields: List of field names to sanitize as plain text
            html_fields: List of field names to sanitize as HTML
            
        Returns:
            Dictionary with sanitized values
            
        Requirements: 13.5
        """
        if not data:
            return {}
        
        text_fields = text_fields or []
        html_fields = html_fields or []
        
        sanitized = {}
        
        for key, value in data.items():
            if value is None:
                sanitized[key] = None
            elif key in html_fields:
                # Sanitize as HTML
                sanitized[key] = InputSanitizer.sanitize_html(value)
            elif key in text_fields or isinstance(value, str):
                # Sanitize as plain text
                sanitized[key] = InputSanitizer.sanitize_text(value)
            else:
                # Keep other types as-is (numbers, booleans, etc.)
                sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    def validate_no_sql_injection(text: Optional[str]) -> bool:
        """
        Check if text contains potential SQL injection patterns.
        
        This is a basic check - Django's ORM provides primary SQL injection protection.
        Use this as an additional layer of defense for raw queries.
        
        Args:
            text: Text to check
            
        Returns:
            True if text appears safe, False if suspicious patterns detected
            
        Requirements: 13.5
        """
        if not text:
            return True
        
        text_lower = str(text).lower()
        
        # Common SQL injection patterns
        suspicious_patterns = [
            'union select',
            'drop table',
            'delete from',
            'insert into',
            'update set',
            '--',
            '/*',
            '*/',
            'xp_',
            'sp_',
            'exec(',
            'execute(',
            'script>',
            '<script',
        ]
        
        for pattern in suspicious_patterns:
            if pattern in text_lower:
                logger.warning(f"Potential SQL injection pattern detected: {pattern}")
                return False
        
        return True
    
    @staticmethod
    def validate_no_xss(text: Optional[str]) -> bool:
        """
        Check if text contains potential XSS attack patterns.
        
        This is a basic check - use sanitize_html() for actual sanitization.
        Use this for validation and logging suspicious inputs.
        
        Args:
            text: Text to check
            
        Returns:
            True if text appears safe, False if suspicious patterns detected
            
        Requirements: 13.5
        """
        if not text:
            return True
        
        text_lower = str(text).lower()
        
        # Common XSS patterns
        suspicious_patterns = [
            '<script',
            'javascript:',
            'onerror=',
            'onload=',
            'onclick=',
            'onmouseover=',
            '<iframe',
            '<object',
            '<embed',
            'eval(',
            'expression(',
        ]
        
        for pattern in suspicious_patterns:
            if pattern in text_lower:
                logger.warning(f"Potential XSS pattern detected: {pattern}")
                return False
        
        return True
