"""
Unit tests for ProfileService.
Tests profile management operations including updates, password changes, and picture uploads.
"""
import os
import tempfile
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from users.models import Student
from services.profile_service import ProfileService
from services.result import Result


class ProfileServiceTest(TestCase):
    """Test cases for ProfileService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = ProfileService()
        
        # Create a test student
        self.student = Student.objects.create(
            school_id='TEST001',
            first_name='John',
            last_name='Doe'
        )
        self.student.set_password('TestPass123')
        self.student.save()
    
    def tearDown(self):
        """Clean up after tests."""
        # Clean up any uploaded files
        if self.student.profile_picture:
            file_path = self.student.profile_picture.name
            self.service.file_service.delete_file(file_path)
    
    def test_get_student_profile_success(self):
        """Test retrieving an existing student profile."""
        result = self.service.get_student_profile(self.student.id)
        
        self.assertTrue(result.is_success())
        self.assertEqual(result.value.id, self.student.id)
        self.assertEqual(result.value.school_id, 'TEST001')
    
    def test_get_student_profile_not_found(self):
        """Test retrieving a non-existent student profile."""
        result = self.service.get_student_profile(99999)
        
        self.assertTrue(result.is_failure())
        self.assertIn('not found', result.error.message.lower())
    
    def test_update_profile_info_success(self):
        """Test updating profile information with valid data."""
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'bio': 'Test bio'
        }
        
        result = self.service.update_profile_info(self.student.id, data)
        
        self.assertTrue(result.is_success())
        self.assertEqual(result.value.first_name, 'Jane')
        self.assertEqual(result.value.last_name, 'Smith')
        self.assertEqual(result.value.bio, 'Test bio')
    
    def test_update_profile_info_partial_update(self):
        """Test updating only some profile fields."""
        data = {'first_name': 'Jane'}
        
        result = self.service.update_profile_info(self.student.id, data)
        
        self.assertTrue(result.is_success())
        self.assertEqual(result.value.first_name, 'Jane')
        self.assertEqual(result.value.last_name, 'Doe')  # Unchanged
    
    def test_update_profile_info_empty_name(self):
        """Test that empty names are rejected."""
        data = {'first_name': '   '}
        
        result = self.service.update_profile_info(self.student.id, data)
        
        self.assertTrue(result.is_failure())
        self.assertIn('first_name', result.error.details)
    
    def test_update_profile_info_name_too_long(self):
        """Test that names exceeding max length are rejected."""
        data = {'first_name': 'A' * 101}
        
        result = self.service.update_profile_info(self.student.id, data)
        
        self.assertTrue(result.is_failure())
        self.assertIn('first_name', result.error.details)
    
    def test_update_profile_info_bio_too_long(self):
        """Test that bio exceeding max length is rejected."""
        data = {'bio': 'A' * 501}
        
        result = self.service.update_profile_info(self.student.id, data)
        
        self.assertTrue(result.is_failure())
        self.assertIn('bio', result.error.details)
    
    def test_update_profile_info_invalid_fields(self):
        """Test that invalid fields are rejected."""
        data = {'school_id': 'HACKED', 'first_name': 'Jane'}
        
        result = self.service.update_profile_info(self.student.id, data)
        
        self.assertTrue(result.is_failure())
        self.assertIn('invalid_fields', result.error.details)
    
    def test_change_password_success(self):
        """Test changing password with valid credentials."""
        result = self.service.change_password(
            self.student.id,
            'TestPass123',
            'NewPass456'
        )
        
        self.assertTrue(result.is_success())
        
        # Verify new password works
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('NewPass456'))
        self.assertFalse(self.student.check_password('TestPass123'))
    
    def test_change_password_wrong_current(self):
        """Test that wrong current password is rejected."""
        result = self.service.change_password(
            self.student.id,
            'WrongPass',
            'NewPass456'
        )
        
        self.assertTrue(result.is_failure())
        self.assertIn('incorrect', result.error.message.lower())
    
    def test_change_password_too_short(self):
        """Test that short passwords are rejected."""
        result = self.service.change_password(
            self.student.id,
            'TestPass123',
            'Short1'
        )
        
        self.assertTrue(result.is_failure())
        self.assertIn('length', result.error.details)
    
    def test_change_password_no_uppercase(self):
        """Test that passwords without uppercase are rejected."""
        result = self.service.change_password(
            self.student.id,
            'TestPass123',
            'newpass123'
        )
        
        self.assertTrue(result.is_failure())
        self.assertIn('uppercase', result.error.details)
    
    def test_change_password_no_lowercase(self):
        """Test that passwords without lowercase are rejected."""
        result = self.service.change_password(
            self.student.id,
            'TestPass123',
            'NEWPASS123'
        )
        
        self.assertTrue(result.is_failure())
        self.assertIn('lowercase', result.error.details)
    
    def test_change_password_no_digit(self):
        """Test that passwords without digits are rejected."""
        result = self.service.change_password(
            self.student.id,
            'TestPass123',
            'NewPassword'
        )
        
        self.assertTrue(result.is_failure())
        self.assertIn('digit', result.error.details)
    
    def test_change_password_same_as_current(self):
        """Test that new password must be different from current."""
        result = self.service.change_password(
            self.student.id,
            'TestPass123',
            'TestPass123'
        )
        
        self.assertTrue(result.is_failure())
        self.assertIn('different', result.error.message.lower())
    
    def test_upload_profile_picture_success(self):
        """Test uploading a valid profile picture."""
        # Create a simple test image file
        image_content = b'GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;'
        image_file = SimpleUploadedFile(
            'test_image.gif',
            image_content,
            content_type='image/gif'
        )
        
        result = self.service.upload_profile_picture(self.student.id, image_file)
        
        self.assertTrue(result.is_success())
        self.assertIsNotNone(result.value)
        
        # Verify student has profile picture
        self.student.refresh_from_db()
        self.assertIsNotNone(self.student.profile_picture)
    
    def test_upload_profile_picture_invalid_type(self):
        """Test that non-image files are rejected."""
        text_file = SimpleUploadedFile(
            'test.txt',
            b'Not an image',
            content_type='text/plain'
        )
        
        result = self.service.upload_profile_picture(self.student.id, text_file)
        
        self.assertTrue(result.is_failure())
    
    def test_upload_profile_picture_replaces_old(self):
        """Test that uploading a new picture replaces the old one."""
        # Upload first picture
        image1 = SimpleUploadedFile(
            'image1.gif',
            b'GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;',
            content_type='image/gif'
        )
        result1 = self.service.upload_profile_picture(self.student.id, image1)
        self.assertTrue(result1.is_success())
        
        old_path = self.student.profile_picture.name
        
        # Upload second picture
        image2 = SimpleUploadedFile(
            'image2.gif',
            b'GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;',
            content_type='image/gif'
        )
        result2 = self.service.upload_profile_picture(self.student.id, image2)
        self.assertTrue(result2.is_success())
        
        # Verify new picture is different
        self.student.refresh_from_db()
        self.assertNotEqual(self.student.profile_picture.name, old_path)
    
    def test_delete_profile_picture_success(self):
        """Test deleting an existing profile picture."""
        # First upload a picture
        image_file = SimpleUploadedFile(
            'test_image.gif',
            b'GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;',
            content_type='image/gif'
        )
        self.service.upload_profile_picture(self.student.id, image_file)
        
        # Now delete it
        result = self.service.delete_profile_picture(self.student.id)
        
        self.assertTrue(result.is_success())
        
        # Verify picture is removed
        self.student.refresh_from_db()
        self.assertFalse(self.student.profile_picture)
    
    def test_delete_profile_picture_when_none(self):
        """Test deleting profile picture when student has none."""
        result = self.service.delete_profile_picture(self.student.id)
        
        self.assertTrue(result.is_success())
