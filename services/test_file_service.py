"""
Unit tests for FileService.
Tests file validation, storage, deletion, and URL generation.
"""
import os
import tempfile
from pathlib import Path
from io import BytesIO
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from services.file_service import FileService
from services.errors import ValidationError, FileError


class FileServiceTest(TestCase):
    """Test cases for FileService."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test media files
        self.test_media_root = tempfile.mkdtemp()
        self.service = FileService()
    
    def tearDown(self):
        """Clean up test files."""
        # Remove test media directory and all contents
        import shutil
        if os.path.exists(self.test_media_root):
            shutil.rmtree(self.test_media_root)
    
    def _create_test_image(self, filename='test.jpg', size=1024, content_type='image/jpeg'):
        """Helper to create a test image file."""
        content = b'x' * size
        return SimpleUploadedFile(filename, content, content_type=content_type)
    
    # Test validate_image method
    
    def test_validate_image_success(self):
        """Test successful image validation."""
        file = self._create_test_image('test.jpg', size=1024, content_type='image/jpeg')
        result = self.service.validate_image(file)
        
        self.assertTrue(result.is_success())
        self.assertTrue(result.value)
    
    def test_validate_image_no_file(self):
        """Test validation fails when no file provided."""
        result = self.service.validate_image(None)
        
        self.assertTrue(result.is_failure())
        self.assertIsInstance(result.error, ValidationError)
        self.assertIn('No file provided', result.error.message)
    
    def test_validate_image_size_exceeds_limit(self):
        """Test validation fails when file size exceeds 5MB."""
        # Create file larger than 5MB
        large_size = 6 * 1024 * 1024  # 6MB
        file = self._create_test_image('large.jpg', size=large_size)
        
        result = self.service.validate_image(file)
        
        self.assertTrue(result.is_failure())
        self.assertIsInstance(result.error, ValidationError)
        self.assertIn('exceeds maximum', result.error.message)
    
    def test_validate_image_invalid_extension(self):
        """Test validation fails for invalid file extension."""
        file = self._create_test_image('test.txt', content_type='text/plain')
        
        result = self.service.validate_image(file)
        
        self.assertTrue(result.is_failure())
        self.assertIsInstance(result.error, ValidationError)
        self.assertIn('not allowed', result.error.message)
    
    def test_validate_image_invalid_mime_type(self):
        """Test validation fails for invalid MIME type."""
        file = self._create_test_image('test.jpg', content_type='application/pdf')
        
        result = self.service.validate_image(file)
        
        self.assertTrue(result.is_failure())
        self.assertIsInstance(result.error, ValidationError)
    
    def test_validate_image_all_allowed_types(self):
        """Test validation succeeds for all allowed image types."""
        allowed_types = [
            ('test.jpg', 'image/jpeg'),
            ('test.jpeg', 'image/jpeg'),
            ('test.png', 'image/png'),
            ('test.gif', 'image/gif'),
        ]
        
        for filename, content_type in allowed_types:
            with self.subTest(filename=filename, content_type=content_type):
                file = self._create_test_image(filename, content_type=content_type)
                result = self.service.validate_image(file)
                self.assertTrue(result.is_success(), f"Failed for {filename}")
    
    # Test _sanitize_filename method
    
    def test_sanitize_filename_removes_unsafe_chars(self):
        """Test filename sanitization removes unsafe characters."""
        unsafe_name = '../../../etc/passwd.jpg'
        sanitized = self.service._sanitize_filename(unsafe_name)
        
        # Should not contain path traversal
        self.assertNotIn('..', sanitized)
        self.assertNotIn('/', sanitized)
        self.assertNotIn('\\', sanitized)
        # Should preserve extension
        self.assertTrue(sanitized.endswith('.jpg'))
    
    def test_sanitize_filename_preserves_safe_chars(self):
        """Test filename sanitization preserves safe characters."""
        safe_name = 'my-profile_picture123.png'
        sanitized = self.service._sanitize_filename(safe_name)
        
        self.assertEqual(sanitized, safe_name)
    
    def test_sanitize_filename_replaces_spaces(self):
        """Test filename sanitization replaces spaces with underscores."""
        name_with_spaces = 'my profile picture.jpg'
        sanitized = self.service._sanitize_filename(name_with_spaces)
        
        self.assertNotIn(' ', sanitized)
        self.assertIn('_', sanitized)
    
    def test_sanitize_filename_limits_length(self):
        """Test filename sanitization limits length."""
        long_name = 'a' * 100 + '.jpg'
        sanitized = self.service._sanitize_filename(long_name)
        
        # Should be limited to 50 chars + extension
        self.assertLessEqual(len(sanitized), 54)  # 50 + '.jpg'
    
    # Test _generate_unique_filename method
    
    def test_generate_unique_filename_includes_student_id(self):
        """Test unique filename includes student ID."""
        filename = self.service._generate_unique_filename('test.jpg', student_id=123)
        
        self.assertIn('student_123', filename)
    
    def test_generate_unique_filename_preserves_extension(self):
        """Test unique filename preserves file extension."""
        filename = self.service._generate_unique_filename('test.png', student_id=123)
        
        self.assertTrue(filename.endswith('.png'))
    
    def test_generate_unique_filename_is_unique(self):
        """Test generated filenames are unique."""
        filename1 = self.service._generate_unique_filename('test.jpg', student_id=123)
        filename2 = self.service._generate_unique_filename('test.jpg', student_id=123)
        
        self.assertNotEqual(filename1, filename2)
    
    # Test save_profile_picture method
    
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_save_profile_picture_success(self):
        """Test successful profile picture save."""
        file = self._create_test_image('profile.jpg', size=1024)
        
        result = self.service.save_profile_picture(file, student_id=123)
        
        self.assertTrue(result.is_success())
        self.assertIsInstance(result.value, str)
        self.assertIn('profile_pictures', result.value)
        self.assertIn('student_123', result.value)
        
        # Clean up
        if result.is_success():
            self.service.delete_file(result.value)
    
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_save_profile_picture_invalid_file(self):
        """Test save fails with invalid file."""
        file = self._create_test_image('test.txt', content_type='text/plain')
        
        result = self.service.save_profile_picture(file, student_id=123)
        
        self.assertTrue(result.is_failure())
        self.assertIsInstance(result.error, FileError)
    
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_save_profile_picture_deletes_old_file(self):
        """Test save deletes old profile picture."""
        # Save first file
        file1 = self._create_test_image('profile1.jpg', size=1024)
        result1 = self.service.save_profile_picture(file1, student_id=123)
        self.assertTrue(result1.is_success())
        old_path = result1.value
        
        # Verify first file exists
        full_path1 = Path(self.service.media_root) / old_path
        self.assertTrue(full_path1.exists())
        
        # Save second file with old_file_path
        file2 = self._create_test_image('profile2.jpg', size=1024)
        result2 = self.service.save_profile_picture(file2, student_id=123, old_file_path=old_path)
        self.assertTrue(result2.is_success())
        
        # Verify old file is deleted
        self.assertFalse(full_path1.exists())
        
        # Clean up new file
        self.service.delete_file(result2.value)
    
    # Test delete_file method
    
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_delete_file_success(self):
        """Test successful file deletion."""
        # Create a file first
        file = self._create_test_image('delete_test.jpg', size=1024)
        save_result = self.service.save_profile_picture(file, student_id=123)
        self.assertTrue(save_result.is_success())
        file_path = save_result.value
        
        # Verify file exists
        full_path = Path(self.service.media_root) / file_path
        self.assertTrue(full_path.exists())
        
        # Delete the file
        delete_result = self.service.delete_file(file_path)
        
        self.assertTrue(delete_result.is_success())
        self.assertFalse(full_path.exists())
    
    def test_delete_file_nonexistent(self):
        """Test deleting nonexistent file succeeds gracefully."""
        result = self.service.delete_file('profile_pictures/nonexistent.jpg')
        
        self.assertTrue(result.is_success())
    
    def test_delete_file_empty_path(self):
        """Test deleting with empty path succeeds gracefully."""
        result = self.service.delete_file('')
        
        self.assertTrue(result.is_success())
    
    def test_delete_file_path_traversal_blocked(self):
        """Test path traversal attack is blocked."""
        result = self.service.delete_file('../../../etc/passwd')
        
        self.assertTrue(result.is_failure())
        self.assertIsInstance(result.error, FileError)
        self.assertIn('Invalid file path', result.error.message)
    
    # Test get_file_url method
    
    def test_get_file_url_success(self):
        """Test URL generation for file."""
        file_path = 'profile_pictures/student_123_abc123_test.jpg'
        url = self.service.get_file_url(file_path)
        
        self.assertIn('/media/', url)
        self.assertIn('profile_pictures', url)
        self.assertIn('student_123', url)
    
    def test_get_file_url_empty_path(self):
        """Test URL generation with empty path."""
        url = self.service.get_file_url('')
        
        self.assertEqual(url, '')
    
    def test_get_file_url_none_path(self):
        """Test URL generation with None path."""
        url = self.service.get_file_url(None)
        
        self.assertEqual(url, '')
    
    def test_get_file_url_normalizes_slashes(self):
        """Test URL generation normalizes backslashes to forward slashes."""
        file_path = 'profile_pictures\\student_123\\test.jpg'
        url = self.service.get_file_url(file_path)
        
        self.assertNotIn('\\', url)
        self.assertIn('/', url)
    
    # Test _compress_image method
    
    def test_compress_image_returns_file_when_pillow_unavailable(self):
        """Test compression returns original file when Pillow is not available."""
        from services import file_service
        original_pillow = file_service.PILLOW_AVAILABLE
        
        try:
            # Temporarily disable Pillow
            file_service.PILLOW_AVAILABLE = False
            
            file = self._create_test_image('test.jpg', size=1024)
            result = self.service._compress_image(file)
            
            self.assertTrue(result.is_success())
            self.assertEqual(result.value, file)
        finally:
            # Restore Pillow availability
            file_service.PILLOW_AVAILABLE = original_pillow
    
    def test_compress_image_handles_compression_failure_gracefully(self):
        """Test compression returns original file on failure."""
        from services import file_service
        
        # Only run if Pillow is available
        if not file_service.PILLOW_AVAILABLE:
            self.skipTest("Pillow not available")
        
        # Create an invalid image file (just random bytes)
        invalid_file = SimpleUploadedFile('test.jpg', b'invalid image data', content_type='image/jpeg')
        
        result = self.service._compress_image(invalid_file)
        
        # Should return success with original file (graceful degradation)
        self.assertTrue(result.is_success())
    
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_save_profile_picture_with_compression(self):
        """Test profile picture save includes compression."""
        from services import file_service
        
        # Only run if Pillow is available
        if not file_service.PILLOW_AVAILABLE:
            self.skipTest("Pillow not available")
        
        # Create a larger test file
        file = self._create_test_image('large_profile.jpg', size=2 * 1024 * 1024)  # 2MB
        
        result = self.service.save_profile_picture(file, student_id=456)
        
        self.assertTrue(result.is_success())
        self.assertIsInstance(result.value, str)
        
        # Verify file was saved
        full_path = Path(self.service.media_root) / result.value
        self.assertTrue(full_path.exists())
        
        # Clean up
        self.service.delete_file(result.value)
