from django.contrib import admin
from .models import School, SchoolAdmin, Teacher, Student, Class, GradeLevel, Strand, Section, Subject, Quarter


@admin.register(School)
class SchoolModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'created_at')
    search_fields = ('name',)


@admin.register(SchoolAdmin)
class SchoolAdminModelAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'school', 'created_at')
    search_fields = ('user__username', 'school__name')

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('school', 'grade_level', 'strand', 'section', 'teacher_names', 'student_count', 'created_at')
    list_filter = ('school', 'grade_level', 'strand', 'created_at')
    search_fields = ('school__name', 'grade_level__name', 'strand__name', 'section__name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('school', 'grade_level__order', 'grade_level__name', 'strand__name', 'section__name')

    fieldsets = (
        ('Class Information', {
            'fields': ('school', 'grade_level', 'strand', 'section')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def teacher_names(self, obj):
        return ", ".join(
            t.user.get_full_name() or t.user.username
            for t in obj.teachers.all()
        ) or "—"
    teacher_names.short_description = 'Teachers'

    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = 'Students'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('teachers__user')


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'get_username', 'school', 'department', 'created_at')
    list_filter = ('school',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'department', 'school__name')
    readonly_fields = ('created_at', 'updated_at')

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Full Name'

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'first_name', 'last_name', 'school', 'class_assigned', 'created_at')
    list_filter = ('school', 'class_assigned', 'created_at')
    search_fields = ('student_id', 'first_name', 'last_name', 'school__name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Student Information', {
            'fields': ('student_id', 'first_name', 'last_name', 'school', 'class_assigned')
        }),
        ('Profile', {
            'fields': ('profile_picture', 'bio')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
