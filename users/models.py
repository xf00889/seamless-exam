from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password


class School(models.Model):
    name = models.CharField(max_length=200, unique=True)
    address = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_school'
        verbose_name = 'School'
        verbose_name_plural = 'Schools'

    def __str__(self):
        return self.name


class SchoolAdmin(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='school_admin_profile',
        primary_key=True,
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='admins',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_school_admin'
        verbose_name = 'School Admin'
        verbose_name_plural = 'School Admins'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.school.name})"


class Teacher(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        primary_key=True,
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='teachers',
    )
    department = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/teachers/',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_teacher'
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'
        indexes = [
            models.Index(fields=['school'], name='idx_teacher_school'),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} (Teacher)"


class GradeLevel(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='grade_levels',
    )
    name = models.CharField(max_length=50)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_grade_level'
        ordering = ['order', 'name']
        unique_together = ['school', 'name']

    def __str__(self):
        return self.name


class Strand(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='strands',
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_strand'
        ordering = ['name']
        unique_together = ['school', 'name']

    def __str__(self):
        return self.name


class Section(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='sections',
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_section'
        ordering = ['name']
        unique_together = ['school', 'name']

    def __str__(self):
        return self.name


class Subject(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='subjects',
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_subject'
        ordering = ['name']
        unique_together = ['school', 'name']

    def __str__(self):
        return self.name


class Quarter(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='quarters',
    )
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_quarter'
        ordering = ['order', 'name']
        unique_together = ['school', 'name']

    def __str__(self):
        return self.name


class Class(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='classes',
    )
    grade_level = models.ForeignKey(
        GradeLevel,
        on_delete=models.CASCADE,
        related_name='classes',
    )
    strand = models.ForeignKey(
        Strand,
        on_delete=models.CASCADE,
        related_name='classes',
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='classes',
    )
    teachers = models.ManyToManyField(
        Teacher,
        through='ClassTeacher',
        related_name='classes',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_class'
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'
        unique_together = [['school', 'grade_level', 'strand', 'section']]
        ordering = ['grade_level__order', 'grade_level__name', 'strand__name', 'section__name']
        indexes = [
            models.Index(fields=['school'], name='idx_class_school'),
        ]

    def __str__(self):
        return f"{self.grade_level.name} - {self.strand.name} - {self.section.name}"


class ClassTeacher(models.Model):
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='class_teachers',
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='class_teachers',
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_class_teacher'
        verbose_name = 'Class Teacher'
        verbose_name_plural = 'Class Teachers'
        unique_together = [['class_obj', 'teacher']]

    def __str__(self):
        return f"{self.teacher} → {self.class_obj}"


class Student(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='students',
    )
    student_id = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Unique identifier for student authentication",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    password_hash = models.CharField(
        max_length=255,
        help_text="Hashed password using Django's password hashing",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_students',
        help_text="User who created this student account (audit trail).",
    )
    class_assigned = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        related_name='students',
        help_text="Class to which the student is assigned",
    )
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
    )
    bio = models.TextField(
        blank=True,
        null=True,
        max_length=500,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_student'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        unique_together = [['school', 'student_id']]
        indexes = [
            models.Index(fields=['school'], name='idx_student_school'),
            models.Index(fields=['student_id'], name='idx_student_sid'),
            models.Index(fields=['class_assigned'], name='idx_student_class'),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class AdminNotification(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    message = models.TextField(max_length=500)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_admin_notification'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {'Read' if self.is_read else 'Unread'}"


class SystemSettings(models.Model):
    ai_api_key = models.CharField(max_length=500, blank=True, default='')
    ai_base_url = models.CharField(max_length=255, blank=True, default='https://openrouter.ai/api/v1')
    ai_model = models.CharField(max_length=255, blank=True, default='meta-llama/llama-3.1-8b-instruct:free')
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(
        blank=True,
        default="We're performing scheduled maintenance. The system will be back online shortly. Thank you for your patience.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_settings'
        verbose_name_plural = 'System Settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "System Settings"
