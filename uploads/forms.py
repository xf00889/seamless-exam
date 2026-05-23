"""
Django forms for document upload.
Provides server-side validation for file uploads.
Requirements: 3.4
"""

from django import forms
from django.core.exceptions import ValidationError
from uploads.models import UploadedDocument
import os


class DocumentUploadForm(forms.Form):
    """
    Form for uploading PDF and DOCX documents.
    Validates file type and size.
    Requirement 3.4: File type validation
    """
    document = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none',
            'accept': '.pdf,.docx',
            'data-field-name': 'Document',
            'data-max-size': str(50 * 1024 * 1024)  # 50MB
        }),
        error_messages={
            'required': 'Please select a file to upload'
        }
    )
    
    def clean_document(self):
        """
        Validate uploaded document.
        Checks file type and size.
        """
        document = self.cleaned_data.get('document')
        
        if not document:
            raise ValidationError('No file selected')
        
        # Get file extension
        file_name = document.name
        file_extension = os.path.splitext(file_name)[1].lower()
        
        # Validate file type (Requirement 3.4)
        allowed_extensions = ['.pdf', '.docx']
        if file_extension not in allowed_extensions:
            raise ValidationError(
                f'Invalid file type. Only PDF and DOCX files are allowed. '
                f'You uploaded: {file_extension}'
            )
        
        # Validate file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB in bytes
        if document.size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            actual_size_mb = document.size / (1024 * 1024)
            raise ValidationError(
                f'File size exceeds maximum allowed size of {max_size_mb:.0f}MB. '
                f'Your file is {actual_size_mb:.2f}MB'
            )
        
        # Validate file is not empty
        if document.size == 0:
            raise ValidationError('Uploaded file is empty')
        
        # Additional validation: check file name
        if len(file_name) > 255:
            raise ValidationError('File name is too long (maximum 255 characters)')
        
        # Check for potentially dangerous characters in filename
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        for char in dangerous_chars:
            if char in file_name:
                raise ValidationError(
                    f'File name contains invalid character: {char}'
                )
        
        return document

