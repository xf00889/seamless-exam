from django.db import models
from users.models import Student
from exams.models import Exam, Question


class AttemptStatus(models.TextChoices):
    """
    Enum for attempt status.
    """
    IN_PROGRESS = 'in_progress', 'In Progress'
    SUBMITTED = 'submitted', 'Submitted'
    GRADED = 'graded', 'Graded'


class Attempt(models.Model):
    """
    Attempt model representing a student's exam submission.
    Tracks student, exam, timestamps, score, and status.
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attempts',
        db_index=True
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='attempts',
        db_index=True
    )
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    total_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    status = models.CharField(
        max_length=20,
        choices=AttemptStatus.choices,
        default=AttemptStatus.IN_PROGRESS,
        db_index=True
    )
    is_flagged = models.BooleanField(
        default=False,
        help_text="Flagged for potential cheating"
    )
    flag_reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Reason for flagging (e.g., 'Auto-submitted after 4 tab switches')"
    )
    auto_submitted = models.BooleanField(
        default=False,
        help_text="Whether exam was auto-submitted due to violations"
    )
    
    class Meta:
        db_table = 'attempts_attempt'
        verbose_name = 'Attempt'
        verbose_name_plural = 'Attempts'
        indexes = [
            models.Index(fields=['student'], name='idx_attempt_student'),
            models.Index(fields=['exam'], name='idx_attempt_exam'),
            models.Index(fields=['status'], name='idx_attempt_status'),
            # Composite indexes for performance optimization (Requirement 9.5, 11.2)
            models.Index(fields=['student', 'exam'], name='idx_attempt_student_exam'),
            models.Index(fields=['status', '-submitted_at'], name='idx_attempt_status_submit'),
            models.Index(fields=['-submitted_at'], name='idx_attempt_submit_desc'),
            models.Index(fields=['student', 'submitted_at'], name='idx_attempt_student_submit'),
        ]
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.exam.title} ({self.status})"


class Answer(models.Model):
    """
    Answer model representing a student's response to a question.
    Stores answer text in JSON format, correctness, points earned, and teacher feedback.
    """
    attempt = models.ForeignKey(
        Attempt,
        on_delete=models.CASCADE,
        related_name='answers',
        db_index=True
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        db_index=True
    )
    answer_text = models.JSONField(
        help_text="JSON field for answer data. Format varies by question type."
    )
    is_correct = models.BooleanField(null=True, blank=True)
    points_earned = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    teacher_feedback = models.TextField(blank=True, null=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'attempts_answer'
        verbose_name = 'Answer'
        verbose_name_plural = 'Answers'
        indexes = [
            models.Index(fields=['attempt'], name='idx_answer_attempt'),
            models.Index(fields=['question'], name='idx_answer_question'),
            # Composite index for performance optimization (Requirement 9.5)
            models.Index(fields=['attempt', 'question'], name='idx_answer_attempt_quest'),
            models.Index(fields=['graded_at'], name='idx_answer_graded_at'),
        ]
        unique_together = [['attempt', 'question']]
    
    def __str__(self):
        return f"Answer to {self.question.question_text[:30]}... ({self.points_earned} pts)"


class TabViolation(models.Model):
    """
    Records each instance of a student switching away from the exam tab.
    Tracks violations for exam security monitoring.
    """
    attempt = models.ForeignKey(
        Attempt,
        on_delete=models.CASCADE,
        related_name='tab_violations'
    )
    violated_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duration away from exam in seconds"
    )
    warning_number = models.IntegerField(
        help_text="Which warning this violation triggered (1-3)"
    )
    
    class Meta:
        db_table = 'attempts_tab_violation'
        verbose_name = 'Tab Violation'
        verbose_name_plural = 'Tab Violations'
        ordering = ['violated_at']
        indexes = [
            models.Index(fields=['attempt', 'violated_at'], name='idx_tabviol_attempt_time'),
        ]
    
    def __str__(self):
        return f"Violation #{self.warning_number} - {self.attempt.student.get_full_name()} ({self.violated_at})"
