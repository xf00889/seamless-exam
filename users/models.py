from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password


class Teacher(models.Model):
    """
    Teacher model extending Django User with teacher-specific fields.
    Uses Django's built-in User model for authentication.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        primary_key=True
    )
    department = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/teachers/',
        null=True,
        blank=True,
        help_text="Teacher profile picture"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_teacher'
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} (Teacher)"


class Class(models.Model):
    """
    Class model representing a grouping of students by grade level, strand, and section.
    Each class is owned by a teacher and can have multiple students assigned.
    """
    grade_level = models.CharField(
        max_length=20,
        db_index=True,
        help_text="Grade level (e.g., Grade 11, Grade 12)"
    )
    strand = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Academic strand (e.g., HUMSS, GAS, ABM, Cookery, SMAW)"
    )
    section = models.CharField(
        max_length=50,
        help_text="Section name (e.g., A, B, Einstein, Newton)"
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='classes',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_class'
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'
        unique_together = [['teacher', 'grade_level', 'strand', 'section']]
        indexes = [
            models.Index(fields=['teacher'], name='idx_class_teacher'),
            models.Index(fields=['grade_level'], name='idx_class_grade'),
            models.Index(fields=['strand'], name='idx_class_strand'),
            models.Index(fields=['grade_level', 'strand', 'section'], 
                        name='idx_class_grade_strand_sec'),
        ]
        ordering = ['grade_level', 'strand', 'section']
    
    def __str__(self):
        return f"{self.grade_level} - {self.strand} - {self.section}"


class Student(models.Model):
    """
    Student model with School_ID authentication.
    Stores password hash for secure authentication.
    """
    school_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique identifier for student authentication"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    password_hash = models.CharField(
        max_length=255,
        help_text="Hashed password using Django's password hashing"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Class assignment (Requirements 2.1, 2.2)
    class_assigned = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        related_name='students',
        null=True,
        blank=True,
        db_index=True,
        help_text="Class to which the student is assigned"
    )
    
    # Profile fields (Requirements 2.4, 4.4, 13.2)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        help_text="Student profile picture"
    )
    bio = models.TextField(
        blank=True,
        null=True,
        max_length=500,
        help_text="Optional student bio"
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_student'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        indexes = [
            models.Index(fields=['school_id'], name='idx_school_id'),
            models.Index(fields=['created_at'], name='idx_student_created_at'),
            models.Index(fields=['class_assigned'], name='idx_student_class'),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.school_id})"
    
    def set_password(self, raw_password):
        """
        Hash and set the password using Django's secure password hashing.
        Uses PBKDF2 with SHA256 by default.
        """
        self.password_hash = make_password(raw_password)
    
    def check_password(self, raw_password):
        """
        Verify a raw password against the stored hash.
        Returns True if password matches, False otherwise.
        """
        return check_password(raw_password, self.password_hash)
    
    def get_full_name(self):
        """Return the student's full name."""
        return f"{self.first_name} {self.last_name}"
