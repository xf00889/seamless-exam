from django.contrib import admin
from .models import UploadedDocument, ExtractedContent


@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    """Admin interface for UploadedDocument model."""
    list_display = ['id', 'file_path', 'file_type', 'uploaded_by', 'uploaded_at', 'processing_status']
    list_filter = ['file_type', 'processing_status', 'uploaded_at']
    search_fields = ['file_path', 'uploaded_by__user__username']
    readonly_fields = ['uploaded_at']
    ordering = ['-uploaded_at']


@admin.register(ExtractedContent)
class ExtractedContentAdmin(admin.ModelAdmin):
    """Admin interface for ExtractedContent model."""
    list_display = ['id', 'document', 'extracted_at']
    search_fields = ['document__file_path', 'raw_text']
    readonly_fields = ['extracted_at']
    ordering = ['-extracted_at']
