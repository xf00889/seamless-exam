"""
Repository layer for data access abstraction.
Implements the Repository pattern to separate data access from business logic.
"""
from .base_repository import BaseRepository
from .student_repository import StudentRepository
from .teacher_repository import TeacherRepository
from .exam_repository import ExamRepository
from .question_repository import QuestionRepository
from .upload_repository import UploadedDocumentRepository
from .extracted_content_repository import ExtractedContentRepository
from .attempt_repository import AttemptRepository
from .answer_repository import AnswerRepository
from .class_repository import ClassRepository
from .tab_violation_repository import TabViolationRepository

__all__ = [
    'BaseRepository',
    'StudentRepository',
    'TeacherRepository',
    'ExamRepository',
    'QuestionRepository',
    'UploadedDocumentRepository',
    'ExtractedContentRepository',
    'AttemptRepository',
    'AnswerRepository',
    'ClassRepository',
    'TabViolationRepository',
]
