"""
Custom error classes for the exam system.
Provides structured error types for different failure scenarios.
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class BaseError:
    """Base class for all application errors."""
    message: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON responses."""
        result = {
            'error': self.message,
            'code': self.code
        }
        if self.details:
            result['details'] = self.details
        return result


@dataclass
class ValidationError(BaseError):
    """Error for validation failures."""
    code: str = "VALIDATION_ERROR"


@dataclass
class AuthenticationError(BaseError):
    """Error for authentication failures."""
    code: str = "AUTHENTICATION_ERROR"


@dataclass
class AuthorizationError(BaseError):
    """Error for authorization failures."""
    code: str = "AUTHORIZATION_ERROR"


@dataclass
class NotFoundError(BaseError):
    """Error when a resource is not found."""
    code: str = "NOT_FOUND"


@dataclass
class DatabaseError(BaseError):
    """Error for database operation failures."""
    code: str = "DATABASE_ERROR"


@dataclass
class FileError(BaseError):
    """Error for file operation failures."""
    code: str = "FILE_ERROR"


@dataclass
class ProcessingError(BaseError):
    """Error for document processing failures."""
    code: str = "PROCESSING_ERROR"


@dataclass
class ExamError(BaseError):
    """Error for exam-related operations."""
    code: str = "EXAM_ERROR"


@dataclass
class GradingError(BaseError):
    """Error for grading operations."""
    code: str = "GRADING_ERROR"


@dataclass
class SystemError(BaseError):
    """Error for unexpected system failures."""
    code: str = "SYSTEM_ERROR"


@dataclass
class ConcurrencyError(BaseError):
    """Error for concurrent operation conflicts."""
    code: str = "CONCURRENCY_ERROR"


@dataclass
class NetworkError(BaseError):
    """Error for network-related failures."""
    code: str = "NETWORK_ERROR"





# Exception classes for backward compatibility
class UploadError(Exception):
    """Custom exception for upload-related errors."""
    pass


class QuestionApprovalError(Exception):
    """Custom exception for question approval errors."""
    pass


class DocumentProcessingError(Exception):
    """Custom exception for document processing errors."""
    pass
