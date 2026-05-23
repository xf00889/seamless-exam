"""
Upload service for handling file uploads and validation.
Implements business logic for document upload operations.
Includes comprehensive security checks (Requirement 1.4, 3.4).
"""
import os
import re
from typing import Optional, Tuple, List
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
from repositories.upload_repository import UploadedDocumentRepository
from uploads.models import UploadedDocument


class UploadError(Exception):
    """Custom exception for upload-related errors."""
    pass


class UploadService:
    """
    Service for handling document uploads and validation.
    Implements file type validation and error handling.
    
    Security Features (Requirement 1.4):
    - File extension validation
    - MIME type validation
    - File size limits
    - Filename sanitization
    - Path traversal prevention
    - Magic number validation
    """
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.pdf', '.docx'}
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/octet-stream',  # Some browsers send this for DOCX
    }
    
    # Maximum file size (50 MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    # File magic numbers (first bytes) for validation
    PDF_MAGIC = b'%PDF'
    DOCX_MAGIC = b'PK\x03\x04'  # DOCX is a ZIP file
    
    def __init__(self):
        """Initialize service with repository."""
        self.repository = UploadedDocumentRepository()
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and other attacks.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path components (prevent directory traversal)
        filename = os.path.basename(filename)
        
        # Remove any non-alphanumeric characters except dots, hyphens, and underscores
        filename = re.sub(r'[^\w\s\-\.]', '', filename)
        
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        
        # Limit filename length
        name, ext = os.path.splitext(filename)
        if len(name) > 100:
            name = name[:100]
        
        return name + ext
    
    def _validate_magic_number(self, uploaded_file: UploadedFile, file_ext: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file content by checking magic numbers (file signatures).
        This prevents file extension spoofing attacks.
        
        Args:
            uploaded_file: Django UploadedFile instance
            file_ext: Expected file extension
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Read first few bytes
            uploaded_file.seek(0)
            header = uploaded_file.read(4)
            uploaded_file.seek(0)  # Reset file pointer
            
            # Validate based on extension
            if file_ext == '.pdf':
                if not header.startswith(self.PDF_MAGIC):
                    return False, "File content does not match PDF format"
            elif file_ext == '.docx':
                if not header.startswith(self.DOCX_MAGIC):
                    return False, "File content does not match DOCX format"
            
            return True, None
            
        except Exception as e:
            return False, f"Error validating file content: {str(e)}"
    
    def validate_file(self, uploaded_file: UploadedFile) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive file validation with security checks.
        
        Security checks (Requirement 1.4):
        1. File existence check
        2. File size validation (prevent DoS)
        3. Extension validation (whitelist approach)
        4. MIME type validation
        5. Filename sanitization (prevent path traversal)
        6. Magic number validation (prevent extension spoofing)
        
        Args:
            uploaded_file: Django UploadedFile instance
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if file exists
        if not uploaded_file:
            return False, "No file provided"
        
        # Check for empty file
        if uploaded_file.size == 0:
            return False, "File is empty"
        
        # Check file size (prevent DoS attacks)
        if uploaded_file.size > self.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum allowed size of {self.MAX_FILE_SIZE / (1024 * 1024):.0f} MB"
        
        # Sanitize and validate filename
        original_name = uploaded_file.name
        if not original_name:
            return False, "Invalid filename"
        
        # Check for path traversal attempts
        if '..' in original_name or '/' in original_name or '\\' in original_name:
            return False, "Invalid filename: path traversal detected"
        
        # Check file extension (whitelist approach)
        file_name = original_name.lower()
        file_ext = os.path.splitext(file_name)[1]
        
        if file_ext not in self.ALLOWED_EXTENSIONS:
            return False, f"Invalid file type. Only PDF and DOCX files are allowed"
        
        # Check MIME type if available
        if hasattr(uploaded_file, 'content_type') and uploaded_file.content_type:
            if uploaded_file.content_type not in self.ALLOWED_MIME_TYPES:
                return False, f"Invalid file format. Only PDF and DOCX files are allowed"
        
        # Validate file content by magic number (prevent extension spoofing)
        is_valid, error_msg = self._validate_magic_number(uploaded_file, file_ext)
        if not is_valid:
            return False, error_msg
        
        return True, None
    
    def get_file_type(self, file_name: str) -> str:
        """
        Determine file type from file name.
        
        Args:
            file_name: Name of the file
            
        Returns:
            File type string ('PDF' or 'DOCX')
        """
        file_ext = os.path.splitext(file_name.lower())[1]
        if file_ext == '.pdf':
            return 'PDF'
        elif file_ext == '.docx':
            return 'DOCX'
        else:
            raise UploadError(f"Unsupported file extension: {file_ext}")
    
    def save_uploaded_file(
        self,
        uploaded_file: UploadedFile,
        teacher_id: int
    ) -> UploadedDocument:
        """
        Save uploaded file to disk and create database record.
        
        Args:
            uploaded_file: Django UploadedFile instance
            teacher_id: ID of the teacher uploading the file
            
        Returns:
            Created UploadedDocument instance
            
        Raises:
            UploadError: If validation fails or file cannot be saved
        """
        # Validate file
        is_valid, error_message = self.validate_file(uploaded_file)
        if not is_valid:
            raise UploadError(error_message)
        
        try:
            # Determine file type
            file_type = self.get_file_type(uploaded_file.name)
            
            # Sanitize filename (security: prevent path traversal)
            sanitized_name = self._sanitize_filename(uploaded_file.name)
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'documents')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Set secure directory permissions if configured
            if hasattr(settings, 'FILE_UPLOAD_DIRECTORY_PERMISSIONS'):
                try:
                    os.chmod(upload_dir, settings.FILE_UPLOAD_DIRECTORY_PERMISSIONS)
                except:
                    pass  # Permissions may not be changeable on all systems
            
            # Generate unique file name to avoid conflicts
            base_name = os.path.splitext(sanitized_name)[0]
            file_ext = os.path.splitext(sanitized_name)[1]
            file_name = f"{base_name}_{teacher_id}_{uploaded_file.size}{file_ext}"
            file_path = os.path.join(upload_dir, file_name)
            
            # Security: Ensure file path is within upload directory (prevent path traversal)
            real_upload_dir = os.path.realpath(upload_dir)
            real_file_path = os.path.realpath(file_path)
            if not real_file_path.startswith(real_upload_dir):
                raise UploadError("Invalid file path detected")
            
            # Handle duplicate file names
            counter = 1
            while os.path.exists(file_path):
                file_name = f"{base_name}_{teacher_id}_{uploaded_file.size}_{counter}{file_ext}"
                file_path = os.path.join(upload_dir, file_name)
                counter += 1
            
            # Save file to disk with secure permissions
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # Set secure file permissions if configured
            if hasattr(settings, 'FILE_UPLOAD_PERMISSIONS'):
                try:
                    os.chmod(file_path, settings.FILE_UPLOAD_PERMISSIONS)
                except:
                    pass  # Permissions may not be changeable on all systems
            
            # Create database record
            relative_path = os.path.join('uploads', 'documents', file_name)
            document = self.repository.create(
                file_path=relative_path,
                file_type=file_type,
                uploaded_by_id=teacher_id,
                processing_status='pending'
            )
            
            return document
            
        except Exception as e:
            # Clean up file if database operation fails
            if 'file_path' in locals() and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            
            raise UploadError(f"Failed to save uploaded file: {str(e)}")
    
    def get_teacher_documents(self, teacher_id: int) -> List[UploadedDocument]:
        """
        Get all documents uploaded by a teacher.
        
        Args:
            teacher_id: ID of the teacher
            
        Returns:
            List of UploadedDocument instances
        """
        return list(self.repository.get_by_teacher(teacher_id))
    
    def get_document_by_id(self, document_id: int) -> Optional[UploadedDocument]:
        """
        Get a document by its ID.
        
        Args:
            document_id: ID of the document
            
        Returns:
            UploadedDocument instance if found, None otherwise
        """
        return self.repository.get_by_id(document_id)
    
    def update_processing_status(
        self,
        document_id: int,
        status: str
    ) -> Optional[UploadedDocument]:
        """
        Update the processing status of a document.
        
        Args:
            document_id: ID of the document
            status: New processing status
            
        Returns:
            Updated UploadedDocument instance if found, None otherwise
        """
        return self.repository.update_status(document_id, status)
    
    def delete_document(self, document_id: int) -> bool:
        """
        Delete a document and its associated file.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        document = self.repository.get_by_id(document_id)
        if not document:
            return False
        
        # Delete file from disk
        file_path = os.path.join(settings.MEDIA_ROOT, document.file_path)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                # Log error but continue with database deletion
                print(f"Error deleting file: {e}")
        
        # Delete database record
        return self.repository.delete(document_id)
