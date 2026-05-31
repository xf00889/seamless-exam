from django.contrib import admin
from .models import Exam, Question, ExamClassAssignment


@admin.register(ExamClassAssignment)
class ExamClassAssignmentAdmin(admin.ModelAdmin):
    """
    Admin interface for ExamClassAssignment model.
    Displays exam-class relationships and assignment information.
    """
    list_display = ('exam', 'get_class_info', 'get_teacher', 'assigned_at')
    list_filter = ('assigned_at', 'class_assigned__grade_level', 'class_assigned__strand')
    search_fields = (
        'exam__title',
        'class_assigned__grade_level',
        'class_assigned__strand',
        'class_assigned__section',
        'class_assigned__teacher__user__username'
    )
    readonly_fields = ('assigned_at',)
    ordering = ('-assigned_at',)
    
    fieldsets = (
        ('Assignment Information', {
            'fields': ('exam', 'class_assigned')
        }),
        ('Metadata', {
            'fields': ('assigned_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_class_info(self, obj):
        """Display class information in a readable format."""
        return f"{obj.class_assigned.grade_level} - {obj.class_assigned.strand} - {obj.class_assigned.section}"
    get_class_info.short_description = 'Class'
    
    def get_teacher(self, obj):
        """Display the teacher who owns the class."""
        return obj.class_assigned.teacher.user.get_full_name() or obj.class_assigned.teacher.user.username
    get_teacher.short_description = 'Teacher'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for related objects."""
        queryset = super().get_queryset(request)
        return queryset.select_related('exam', 'class_assigned__teacher__user')


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    """
    Admin interface for Exam model.
    """
    list_display = ('title', 'subject', 'quarter', 'is_active', 'duration_minutes', 'created_by', 'created_at')
    list_filter = ('is_active', 'subject', 'quarter', 'created_at')
    search_fields = ('title', 'subject', 'quarter__name', 'description', 'created_by__user__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Exam Information', {
            'fields': ('title', 'subject', 'quarter', 'description', 'duration_minutes', 'is_active', 'created_by')
        }),
        ('File Uploads', {
            'fields': ('questionnaire_file', 'answer_key_file', 'auto_extracted')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """
    Admin interface for Question model.
    """
    list_display = ('get_question_preview', 'exam', 'question_type', 'points', 'order_index')
    list_filter = ('question_type', 'exam')
    search_fields = ('question_text', 'exam__title')
    readonly_fields = ('created_at',)
    ordering = ('exam', 'order_index')
    
    fieldsets = (
        ('Question Information', {
            'fields': ('exam', 'question_type', 'question_text', 'options', 'correct_answer', 'points', 'order_index')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_question_preview(self, obj):
        """Display a preview of the question text."""
        return obj.question_text[:75] + '...' if len(obj.question_text) > 75 else obj.question_text
    get_question_preview.short_description = 'Question'
