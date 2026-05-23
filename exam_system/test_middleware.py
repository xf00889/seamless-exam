"""
Unit tests for custom middleware.
Tests file size validation middleware.
"""
from django.test import TestCase, RequestFactory, override_settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.files.uploadedfile import SimpleUploadedFile
from exam_system.middleware import FileSizeValidationMiddleware


class FileSizeValidationMiddlewareTest(TestCase):
    """Test cases for FileSizeValidationMiddleware."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.get_response = lambda request: JsonResponse({'success': True})
        self.middleware = FileSizeValidationMiddleware(self.get_response)
    
    def _create_test_file(self, filename='test.jpg', size=1024, content_type='image/jpeg'):
        """Helper to create a test file."""
        content = b'x' * size
        return SimpleUploadedFile(filename, content, content_type=content_type)
    
    def test_middleware_allows_get_requests(self):
        """Test middleware allows GET requests without files."""
        request = self.factory.get('/test/')
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_middleware_allows_post_without_files(self):
        """Test middleware allows POST requests without files."""
        request = self.factory.post('/test/', data={'field': 'value'})
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_middleware_allows_small_files(self):
        """Test middleware allows files within size limit."""
        small_file = self._create_test_file('small.jpg', size=1024)  # 1KB
        request = self.factory.post('/test/', data={'file': small_file})
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_middleware_rejects_large_files(self):
        """Test middleware rejects files exceeding size limit."""
        # Create middleware with small max size for testing
        middleware = FileSizeValidationMiddleware(self.get_response)
        middleware.max_size = 1024  # 1KB limit
        
        large_file = self._create_test_file('large.jpg', size=2048)  # 2KB
        request = self.factory.post('/test/', data={'file': large_file})
        
        response = middleware(request)
        
        self.assertEqual(response.status_code, 400)
        self.assertIsInstance(response, HttpResponseBadRequest)
    
    def test_middleware_returns_json_for_ajax(self):
        """Test middleware returns JSON error for AJAX requests."""
        # Create middleware with small max size for testing
        middleware = FileSizeValidationMiddleware(self.get_response)
        middleware.max_size = 1024  # 1KB limit
        
        large_file = self._create_test_file('large.jpg', size=2048)  # 2KB
        request = self.factory.post(
            '/test/',
            data={'file': large_file},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        response = middleware(request)
        
        self.assertEqual(response.status_code, 400)
        self.assertIsInstance(response, JsonResponse)
        
        # Parse JSON response
        import json
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertIn('exceeds maximum', data['error'])
    
    def test_middleware_checks_all_uploaded_files(self):
        """Test middleware validates all files in request."""
        small_file = self._create_test_file('small.jpg', size=512)
        request = self.factory.post('/test/', data={
            'file1': small_file,
            'file2': small_file,
        })
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_middleware_rejects_if_any_file_too_large(self):
        """Test middleware rejects request if any file exceeds limit."""
        # Create middleware with small max size for testing
        middleware = FileSizeValidationMiddleware(self.get_response)
        middleware.max_size = 1024  # 1KB limit
        
        small_file = self._create_test_file('small.jpg', size=512)
        large_file = self._create_test_file('large.jpg', size=2048)
        
        request = self.factory.post('/test/', data={
            'file1': small_file,
            'file2': large_file,
        })
        
        response = middleware(request)
        
        self.assertEqual(response.status_code, 400)
    
    def test_middleware_uses_default_size_limit(self):
        """Test middleware uses default size limit when not configured."""
        # Create middleware without explicit setting
        middleware = FileSizeValidationMiddleware(self.get_response)
        
        # Default is 50MB
        self.assertEqual(middleware.max_size, 52428800)
    
    def test_middleware_logs_rejection(self):
        """Test middleware logs file rejection."""
        import logging
        from unittest.mock import patch
        
        with patch('exam_system.middleware.logger') as mock_logger:
            large_file = self._create_test_file('large.jpg', size=100 * 1024 * 1024)  # 100MB
            request = self.factory.post('/test/', data={'file': large_file})
            
            response = self.middleware(request)
            
            # Verify logging was called
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            self.assertIn('File upload rejected', call_args)
