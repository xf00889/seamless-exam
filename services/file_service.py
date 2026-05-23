"""
File service for handling image uploads and file operations.
Provides secure file validation, storage, and retrieval for profile pictures.
"""
import os
import uuid
import mimetypes
from pathlib import Path
from typing import Optional
from io import BytesIO
from django.core.files.uploadedfile import UploadedFile, InMemoryUploadedFile
from django.conf import settings
from services.result import Result
from services.errors import FileError, ValidationError
import logging

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    logging.warning("Pillow not available - image compression will be disabled")

logger = logging.getLogger('services')


class FileService:
    """
    Service for handling file operations with security and validation.
    Manages profile picture uploads, validation, storage, and cleanup.
    """
    
    # Allowed image MIME types (Requirement 4.2, 13.1)
    ALLOWED_IMAGE_TYPES = {
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/gif',
    }
    
    # Allowed file extensions (Requirement 4.2, 13.1)
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif'}
    
    # Maximum file size: 5MB (Requirement 4.3)
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
    
    # Profile pictures subdirectory
    PROFILE_PICTURES_DIR = 'profile_pictures'
    
    # Image compression settings
    MAX_IMAGE_WIDTH = 800  # Maximum width for profile pictures
    MAX_IMAGE_HEIGHT = 800  # Maximum height for profile pictures
    JPEG_QUALITY = 85  # JPEG compression quality (0-100)
    
    def __init__(self):
        """Initialize the file service."""
        self.media_root = Path(settings.MEDIA_ROOT)
        self.media_url = settings.MEDIA_URL
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """
        Ensure required directories exist with proper permissions.
        Creates profile_pictures directory if it doesn't exist.
        """
        profile_dir = self.media_root / self.PROFILE_PICTURES_DIR
        if not profile_dir.exists():
            profile_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created profile pictures directory: {profile_dir}")
    
    def validate_image(self, file: UploadedFile) -> Result[bool, ValidationError]:
        """
        Validate an uploaded image file for type and size.
        
        Validates:
        - File size does not exceed MAX_FILE_SIZE (5MB)
        - File extension is in ALLOWED_EXTENSIONS
        - MIME type is in ALLOWED_IMAGE_TYPES
        
        Args:
            file: Django UploadedFile instance
            
        Returns:
            Result[bool, ValidationError]: Success(True) if valid, Failure with error details
            
        Requirements: 4.2, 4.3, 13.1
        """
        # Check if file exists
        if not file:
            return Result.failure(ValidationError(
                message="No file provided",
                details={'field': 'file'}
            ))
        
        # Validate file size (Requirement 4.3)
        if file.size > self.MAX_FILE_SIZE:
            size_mb = file.size / (1024 * 1024)
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            return Result.failure(ValidationError(
                message=f"File size ({size_mb:.2f}MB) exceeds maximum allowed size ({max_mb}MB)",
                details={
                    'field': 'file',
                    'size': file.size,
                    'max_size': self.MAX_FILE_SIZE
                }
            ))
        
        # Validate file extension (Requirement 4.2, 13.1)
        file_ext = Path(file.name).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            return Result.failure(ValidationError(
                message=f"File type '{file_ext}' is not allowed. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}",
                details={
                    'field': 'file',
                    'extension': file_ext,
                    'allowed_extensions': list(self.ALLOWED_EXTENSIONS)
                }
            ))
        
        # Validate MIME type (Requirement 4.2, 13.1)
        # Check content_type from upload - must match allowed types
        content_type = file.content_type
        
        # Verify content type matches allowed types
        if content_type not in self.ALLOWED_IMAGE_TYPES:
            return Result.failure(ValidationError(
                message=f"File MIME type '{content_type}' is not allowed. Must be an image file.",
                details={
                    'field': 'file',
                    'mime_type': content_type,
                    'allowed_types': list(self.ALLOWED_IMAGE_TYPES)
                }
            ))
        
        logger.info(f"File validation successful: {file.name} ({file.size} bytes, {content_type})")
        return Result.success(True)
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and other security issues.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem storage
            
        Requirements: 13.1
        """
        # Get the file extension
        ext = Path(filename).suffix.lower()
        
        # Remove any path components (prevent directory traversal)
        filename = os.path.basename(filename)
        
        # Remove extension temporarily
        name_without_ext = filename[:-len(ext)] if ext else filename
        
        # Remove or replace unsafe characters
        # Keep only alphanumeric, dash, underscore
        safe_chars = []
        for char in name_without_ext:
            if char.isalnum() or char in ('-', '_'):
                safe_chars.append(char)
            elif char in (' ', '.'):
                safe_chars.append('_')
        
        sanitized = ''.join(safe_chars)
        
        # Ensure filename is not empty
        if not sanitized:
            sanitized = 'file'
        
        # Limit length
        if len(sanitized) > 50:
            sanitized = sanitized[:50]
        
        return sanitized + ext
    
    def _generate_unique_filename(self, original_filename: str, student_id: int) -> str:
        """
        Generate a unique filename for storage.
        
        Combines student ID, UUID, and sanitized original filename
        to ensure uniqueness and prevent overwrites.
        
        Args:
            original_filename: Original uploaded filename
            student_id: Student ID for namespacing
            
        Returns:
            Unique filename
            
        Requirements: 13.1
        """
        # Sanitize the original filename
        sanitized = self._sanitize_filename(original_filename)
        
        # Get extension
        ext = Path(sanitized).suffix
        
        # Generate unique identifier
        unique_id = uuid.uuid4().hex[:12]
        
        # Combine: student_id_uniqueid_sanitizedname.ext
        unique_filename = f"student_{student_id}_{unique_id}_{sanitized}"
        
        return unique_filename
    
    def _compress_image(self, file: UploadedFile) -> Result[UploadedFile, FileError]:
        """
        Compress and resize an image to reduce file size.
        
        Resizes images larger than MAX_IMAGE_WIDTH x MAX_IMAGE_HEIGHT
        and applies JPEG compression to reduce file size while maintaining quality.
        
        Args:
            file: Django UploadedFile instance
            
        Returns:
            Result[UploadedFile, FileError]: Compressed file or original if compression not available
            
        Requirements: 4.3, 4.4
        """
        # If Pillow is not available, return original file
        if not PILLOW_AVAILABLE:
            logger.warning("Image compression skipped - Pillow not installed")
            return Result.success(file)
        
        try:
            # Open the image
            image = Image.open(file)
            
            # Convert RGBA to RGB if necessary (for JPEG compatibility)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create a white background
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get original dimensions
            original_width, original_height = image.size
            
            # Calculate new dimensions if image is too large
            if original_width > self.MAX_IMAGE_WIDTH or original_height > self.MAX_IMAGE_HEIGHT:
                # Calculate aspect ratio
                aspect_ratio = original_width / original_height
                
                if original_width > original_height:
                    new_width = self.MAX_IMAGE_WIDTH
                    new_height = int(new_width / aspect_ratio)
                else:
                    new_height = self.MAX_IMAGE_HEIGHT
                    new_width = int(new_height * aspect_ratio)
                
                # Resize image with high-quality resampling
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"Image resized from {original_width}x{original_height} to {new_width}x{new_height}")
            
            # Save compressed image to BytesIO
            output = BytesIO()
            image.save(output, format='JPEG', quality=self.JPEG_QUALITY, optimize=True)
            output.seek(0)
            
            # Get original filename and change extension to .jpg
            original_name = Path(file.name).stem + '.jpg'
            
            # Create new InMemoryUploadedFile
            compressed_file = InMemoryUploadedFile(
                output,
                'ImageField',
                original_name,
                'image/jpeg',
                output.getbuffer().nbytes,
                None
            )
            
            original_size = file.size
            compressed_size = compressed_file.size
            reduction = ((original_size - compressed_size) / original_size) * 100
            
            logger.info(
                f"Image compressed: {original_size} bytes -> {compressed_size} bytes "
                f"({reduction:.1f}% reduction)"
            )
            
            return Result.success(compressed_file)
            
        except Exception as e:
            logger.error(f"Image compression failed: {str(e)}")
            # Return original file if compression fails
            logger.warning("Returning original file due to compression failure")
            file.seek(0)  # Reset file pointer
            return Result.success(file)
    
    def save_profile_picture(
        self, 
        file: UploadedFile, 
        student_id: int,
        old_file_path: Optional[str] = None
    ) -> Result[str, FileError]:
        """
        Save a profile picture with secure storage.
        
        Validates the file, compresses it, generates a unique filename, saves to disk,
        and optionally deletes the old profile picture.
        
        Args:
            file: Django UploadedFile instance
            student_id: Student ID for namespacing
            old_file_path: Optional path to old profile picture to delete
            
        Returns:
            Result[str, FileError]: Success with relative file path, or Failure with error
            
        Requirements: 4.2, 4.3, 4.4, 13.1
        """
        # Validate the image first
        validation_result = self.validate_image(file)
        if validation_result.is_failure():
            return Result.failure(FileError(
                message="File validation failed",
                details={'validation_error': str(validation_result.error)}
            ))
        
        # Compress the image
        compression_result = self._compress_image(file)
        if compression_result.is_failure():
            return Result.failure(FileError(
                message="Image compression failed",
                details={'compression_error': str(compression_result.error)}
            ))
        
        # Use compressed file for saving
        file_to_save = compression_result.value
        
        try:
            # Generate unique filename (use compressed file name if available)
            unique_filename = self._generate_unique_filename(file_to_save.name, student_id)
            
            # Construct full path
            relative_path = os.path.join(self.PROFILE_PICTURES_DIR, unique_filename)
            full_path = self.media_root / relative_path
            
            # Ensure directory exists with proper permissions
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Set directory permissions (Requirement 13.2)
            try:
                os.chmod(full_path.parent, 0o755)  # Full access for owner, read/execute for others
            except OSError as e:
                logger.warning(f"Could not set directory permissions: {str(e)}")
            
            # Write file to disk in chunks (memory efficient)
            with open(full_path, 'wb') as destination:
                for chunk in file_to_save.chunks():
                    destination.write(chunk)
            
            # Set file permissions (Requirement 13.2)
            os.chmod(full_path, 0o644)  # Read/write for owner, read for others
            
            logger.info(f"Profile picture saved successfully: {relative_path} for student {student_id}")
            
            # Delete old file if provided
            if old_file_path:
                self.delete_file(old_file_path)
            
            return Result.success(relative_path)
            
        except OSError as e:
            logger.error(f"Failed to save profile picture: {str(e)}")
            return Result.failure(FileError(
                message="Failed to save file to disk",
                details={'error': str(e), 'student_id': student_id}
            ))
        except Exception as e:
            logger.error(f"Unexpected error saving profile picture: {str(e)}")
            return Result.failure(FileError(
                message="Unexpected error during file save",
                details={'error': str(e), 'student_id': student_id}
            ))
    
    def delete_file(self, file_path: str) -> Result[bool, FileError]:
        """
        Delete a file from storage.
        
        Safely removes a file from the filesystem with error handling.
        
        Args:
            file_path: Relative path to file (e.g., 'profile_pictures/image.jpg')
            
        Returns:
            Result[bool, FileError]: Success(True) if deleted, Failure with error
            
        Requirements: 4.4
        """
        if not file_path:
            return Result.success(True)  # Nothing to delete
        
        try:
            # Construct full path
            full_path = self.media_root / file_path
            
            # Verify file is within media root (security check) - do this BEFORE checking existence
            try:
                full_path.resolve().relative_to(self.media_root.resolve())
            except ValueError:
                logger.error(f"Attempted to delete file outside media root: {file_path}")
                return Result.failure(FileError(
                    message="Invalid file path",
                    details={'path': file_path}
                ))
            
            # Check if file exists
            if not full_path.exists():
                logger.warning(f"File does not exist, skipping deletion: {file_path}")
                return Result.success(True)  # Already deleted or never existed
            
            # Delete the file
            full_path.unlink()
            logger.info(f"File deleted successfully: {file_path}")
            
            return Result.success(True)
            
        except OSError as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return Result.failure(FileError(
                message="Failed to delete file",
                details={'error': str(e), 'path': file_path}
            ))
        except Exception as e:
            logger.error(f"Unexpected error deleting file {file_path}: {str(e)}")
            return Result.failure(FileError(
                message="Unexpected error during file deletion",
                details={'error': str(e), 'path': file_path}
            ))
    
    def get_file_url(self, file_path: Optional[str]) -> str:
        """
        Get the URL for serving a file.
        
        Converts a relative file path to a full URL for serving via Django.
        
        Args:
            file_path: Relative path to file (e.g., 'profile_pictures/image.jpg')
            
        Returns:
            Full URL for the file, or empty string if no path provided
            
        Requirements: 4.4
        """
        if not file_path:
            return ''
        
        # Ensure path uses forward slashes for URLs
        normalized_path = file_path.replace('\\', '/')
        
        # Construct URL
        url = f"{self.media_url.rstrip('/')}/{normalized_path.lstrip('/')}"
        
        return url
