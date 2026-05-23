from django.contrib import admin
from .models import Teacher, Student, Class


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    """
    Admin interface for Class model.
    Provides filtering, searching, and display of class information.
    """
    list_display = ('grade_level', 'strand', 'section', 'teacher', 'student_count', 'created_at')
    list_filter = ('grade_level', 'strand', 'created_at')
    search_fields = ('grade_level', 'strand', 'section', 'teacher__user__username', 'teacher__user__first_name', 'teacher__user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('grade_level', 'strand', 'section')
    
    fieldsets = (
        ('Class Information', {
            'fields': ('grade_level', 'strand', 'section', 'teacher')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def student_count(self, obj):
        """Display the number of students in the class."""
        return obj.students.count()
    student_count.short_description = 'Students'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for teacher."""
        queryset = super().get_queryset(request)
        return queryset.select_related('teacher__user')


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    """
    Admin interface for Teacher model.
    """
    list_display = ('get_full_name', 'get_username', 'department', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'department')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_full_name(self, obj):
        """Display teacher's full name."""
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Full Name'
    
    def get_username(self, obj):
        """Display teacher's username."""
        return obj.user.username
    get_username.short_description = 'Username'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """
    Admin interface for Student model.
    """
    list_display = ('school_id', 'first_name', 'last_name', 'class_assigned', 'created_at')
    list_filter = ('class_assigned', 'created_at')
    search_fields = ('school_id', 'first_name', 'last_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Student Information', {
            'fields': ('school_id', 'first_name', 'last_name', 'class_assigned')
        }),
        ('Profile', {
            'fields': ('profile_picture', 'bio')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
