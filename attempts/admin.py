from django.contrib import admin
from .models import Attempt, Answer, TabViolation


@admin.register(TabViolation)
class TabViolationAdmin(admin.ModelAdmin):
    """
    Admin interface for TabViolation model.
    Read-only to prevent manual editing of violation records.
    """
    list_display = [
        'id',
        'get_student_name',
        'get_exam_title',
        'warning_number',
        'violated_at',
        'returned_at',
        'duration_seconds',
    ]
    
    list_filter = [
        'warning_number',
        'violated_at',
        ('attempt', admin.RelatedOnlyFieldListFilter),
    ]
    
    search_fields = [
        'attempt__student__user__first_name',
        'attempt__student__user__last_name',
        'attempt__student__student_id',
        'attempt__exam__title',
    ]
    
    readonly_fields = [
        'attempt',
        'violated_at',
        'returned_at',
        'duration_seconds',
        'warning_number',
    ]
    
    ordering = ['-violated_at']
    
    date_hierarchy = 'violated_at'
    
    def get_student_name(self, obj):
        """Display student name in list view."""
        return obj.attempt.student.get_full_name()
    get_student_name.short_description = 'Student'
    get_student_name.admin_order_field = 'attempt__student__user__last_name'
    
    def get_exam_title(self, obj):
        """Display exam title in list view."""
        return obj.attempt.exam.title
    get_exam_title.short_description = 'Exam'
    get_exam_title.admin_order_field = 'attempt__exam__title'
    
    def has_add_permission(self, request):
        """Prevent manual creation of violations."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of violation records."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of violation records."""
        return False
