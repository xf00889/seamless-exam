from django.db import models
from django.contrib.auth.models import User
from users.models import Teacher


class QuestionType(models.TextChoices):
    """
    Enum for question types supported by the system.
    """
    MCQ = 'MCQ', 'Multiple Choice Question'
    IDENTIFICATION = 'IDENTIFICATION', 'Identification'
    ENUMERATION = 'ENUMERATION', 'Enumeration'
    ESSAY = 'ESSAY', 'Essay'
    TRUE_FALSE = 'TRUE_FALSE', 'True/False'


class Exam(models.Model):
    """
    Exam model representing an examination with metadata.
    Contains title, duration, activation status, and creator information.
    """
    title = models.CharField(max_length=255)
    subject = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Subject of the exam (e.g., English, Physical Science, Filipino)"
    )
    description = models.TextField(blank=True, null=True)
    duration_minutes = models.IntegerField(
        help_text="Duration of the exam in minutes"
    )
    is_active = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the exam is visible to students"
    )
    
    # File uploads for automatic question extraction
    questionnaire_file = models.FileField(
        upload_to='exam_questionnaires/',
        blank=True,
        null=True,
        help_text="Upload test questionnaire document (PDF, DOCX) for automatic question extraction"
    )
    answer_key_file = models.FileField(
        upload_to='exam_answer_keys/',
        blank=True,
        null=True,
        help_text="Upload answer key document (PDF, DOCX, TXT) for automatic answer extraction"
    )
    auto_extracted = models.BooleanField(
        default=False,
        help_text="Whether questions were automatically extracted from uploaded files"
    )
    

    
    created_by = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='exams'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'exams_exam'
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'
        indexes = [
            models.Index(fields=['is_active'], name='idx_exam_active'),
            models.Index(fields=['created_by'], name='idx_exam_created_by'),
            # Composite indexes for performance optimization (Requirement 9.5)
            models.Index(fields=['is_active', 'created_by'], name='idx_exam_active_teacher'),
            models.Index(fields=['-created_at'], name='idx_exam_created_desc'),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({'Active' if self.is_active else 'Inactive'})"


class Question(models.Model):
    """
    Question model representing an individual test item.
    Supports multiple question types with JSON storage for options and answers.
    """
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        db_index=True
    )
    question_text = models.TextField()
    options = models.JSONField(
        blank=True,
        null=True,
        help_text="JSON field for MCQ options: [{'key': 'A', 'value': 'Option text'}]"
    )
    correct_answer = models.JSONField(
        help_text="JSON field for correct answer(s). Format varies by question type."
    )
    points = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00
    )
    order_index = models.IntegerField(
        default=0,
        help_text="Order of the question in the exam"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'exams_question'
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        indexes = [
            models.Index(fields=['exam'], name='idx_question_exam'),
            models.Index(fields=['question_type'], name='idx_question_type'),
            # Composite index for performance optimization (Requirement 9.5)
            models.Index(fields=['exam', 'order_index'], name='idx_question_exam_order'),
        ]
        ordering = ['order_index', 'id']
    
    def __str__(self):
        return f"{self.get_question_type_display()}: {self.question_text[:50]}..."


class ExamClassAssignment(models.Model):
    """
    ExamClassAssignment model representing the many-to-many relationship
    between exams and classes. Tracks which classes have access to which exams.
    """
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='class_assignments'
    )
    class_assigned = models.ForeignKey(
        'users.Class',
        on_delete=models.CASCADE,
        related_name='exam_assignments'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'exams_class_assignment'
        verbose_name = 'Exam Class Assignment'
        verbose_name_plural = 'Exam Class Assignments'
        unique_together = [['exam', 'class_assigned']]
        indexes = [
            models.Index(fields=['exam'], name='idx_exam_class_exam'),
            models.Index(fields=['class_assigned'], name='idx_exam_class_class'),
        ]
    
    def __str__(self):
        return f"{self.exam.title} → {self.class_assigned}"


class ExamStudentAssignment(models.Model):
    """
    ExamStudentAssignment model representing individual student access to exams.
    Tracks which specific students can access a reopened exam.
    If no records exist for an exam, all students in assigned classes can access it.
    """
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='student_assignments'
    )
    student = models.ForeignKey(
        'users.Student',
        on_delete=models.CASCADE,
        related_name='exam_assignments'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'exams_student_assignment'
        verbose_name = 'Exam Student Assignment'
        verbose_name_plural = 'Exam Student Assignments'
        unique_together = [['exam', 'student']]
        indexes = [
            models.Index(fields=['exam'], name='idx_exam_student_exam'),
            models.Index(fields=['student'], name='idx_exam_student_student'),
            models.Index(fields=['exam', 'student'], name='idx_exam_student_composite'),
        ]
    
    def __str__(self):
        return f"{self.exam.title} → {self.student.get_full_name()}"