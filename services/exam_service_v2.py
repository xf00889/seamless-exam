"""
Exam service with Result pattern for error handling.
Demonstrates improved error handling with explicit success/failure cases.
"""
from typing import Dict, Any, List
import logging
from django.db import transaction, DatabaseError as DjangoDatabaseError
from exams.models import Exam
from repositories.exam_repository import ExamRepository
from repositories.question_repository import QuestionRepository
from services.result import Result, Success, Failure
from services.errors import (
    ValidationError,
    NotFoundError,
    DatabaseError,
    SystemError
)


logger = logging.getLogger('services.exam')


class ExamServiceV2:
    """
    Enhanced exam service with Result pattern for error handling.
    All methods return Result[T, Error] for explicit error handling.
    """
    
    def __init__(self):
        self.exam_repository = ExamRepository()
        self.question_repository = QuestionRepository()
    
    def create_exam(self, exam_data: Dict[str, Any]) -> Result[Exam, Any]:
        """
        Create a new exam with explicit error handling.
        
        Args:
            exam_data: Dictionary containing exam fields
                - title: str (required)
                - description: str (optional)
                - duration_minutes: int (required)
                - created_by: Teacher instance or teacher_id (required)
                
        Returns:
            Result[Exam, Error]: Success with Exam or Failure with error
        """
        try:
            # Validate required fields
            if not exam_data.get('title'):
                logger.warning("Exam creation failed: missing title")
                return Failure(ValidationError(
                    "Title is required",
                    details={'field': 'title'}
                ))
            
            if not exam_data.get('duration_minutes'):
                logger.warning("Exam creation failed: missing duration")
                return Failure(ValidationError(
                    "Duration is required",
                    details={'field': 'duration_minutes'}
                ))
            
            if not exam_data.get('created_by') and not exam_data.get('created_by_id'):
                logger.warning("Exam creation failed: missing creator")
                return Failure(ValidationError(
                    "Creator is required",
                    details={'field': 'created_by'}
                ))
            
            # Validate duration is positive
            duration = exam_data.get('duration_minutes')
            if not isinstance(duration, int) or duration <= 0:
                logger.warning(f"Exam creation failed: invalid duration {duration}")
                return Failure(ValidationError(
                    "Duration must be a positive integer",
                    details={'field': 'duration_minutes', 'value': duration}
                ))
            
            # Handle created_by if it's an ID
            if 'created_by' in exam_data and isinstance(exam_data['created_by'], int):
                exam_data['created_by_id'] = exam_data.pop('created_by')
            
            # Create exam
            exam = self.exam_repository.create(**exam_data)
            
            logger.info(f"Exam created successfully: {exam.id} - {exam.title}")
            return Success(exam)
            
        except DjangoDatabaseError as e:
            logger.error(f"Database error creating exam: {e}", exc_info=True)
            return Failure(DatabaseError(
                "Failed to create exam due to database error",
                details={'original_error': str(e)}
            ))
        except Exception as e:
            logger.exception(f"Unexpected error creating exam: {e}")
            return Failure(SystemError(
                "An unexpected error occurred while creating exam",
                details={'original_error': str(e)}
            ))
    
    def get_exam(self, exam_id: int) -> Result[Exam, Any]:
        """
        Retrieve an exam by ID with error handling.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            Result[Exam, Error]: Success with Exam or Failure with error
        """
        try:
            exam = self.exam_repository.get_by_id(exam_id)
            
            if exam is None:
                logger.warning(f"Exam not found: {exam_id}")
                return Failure(NotFoundError(
                    f"Exam with ID {exam_id} not found",
                    details={'exam_id': exam_id}
                ))
            
            logger.debug(f"Exam retrieved: {exam_id}")
            return Success(exam)
            
        except DjangoDatabaseError as e:
            logger.error(f"Database error retrieving exam {exam_id}: {e}", exc_info=True)
            return Failure(DatabaseError(
                "Failed to retrieve exam due to database error",
                details={'exam_id': exam_id, 'original_error': str(e)}
            ))
        except Exception as e:
            logger.exception(f"Unexpected error retrieving exam {exam_id}: {e}")
            return Failure(SystemError(
                "An unexpected error occurred while retrieving exam",
                details={'exam_id': exam_id, 'original_error': str(e)}
            ))
    
    def get_exam_with_questions(self, exam_id: int) -> Result[Exam, Any]:
        """
        Retrieve an exam with its questions prefetched.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            Result[Exam, Error]: Success with Exam or Failure with error
        """
        try:
            exam = self.exam_repository.get_with_questions(exam_id)
            
            if exam is None:
                logger.warning(f"Exam not found: {exam_id}")
                return Failure(NotFoundError(
                    f"Exam with ID {exam_id} not found",
                    details={'exam_id': exam_id}
                ))
            
            logger.debug(f"Exam with questions retrieved: {exam_id}")
            return Success(exam)
            
        except DjangoDatabaseError as e:
            logger.error(f"Database error retrieving exam {exam_id}: {e}", exc_info=True)
            return Failure(DatabaseError(
                "Failed to retrieve exam due to database error",
                details={'exam_id': exam_id, 'original_error': str(e)}
            ))
        except Exception as e:
            logger.exception(f"Unexpected error retrieving exam {exam_id}: {e}")
            return Failure(SystemError(
                "An unexpected error occurred while retrieving exam",
                details={'exam_id': exam_id, 'original_error': str(e)}
            ))
    
    def get_all_exams(self) -> Result[List[Exam], Any]:
        """
        Retrieve all exams with error handling.
        
        Returns:
            Result[List[Exam], Error]: Success with exam list or Failure with error
        """
        try:
            exams = list(self.exam_repository.get_all())
            logger.debug(f"Retrieved {len(exams)} exams")
            return Success(exams)
            
        except DjangoDatabaseError as e:
            logger.error(f"Database error retrieving exams: {e}", exc_info=True)
            return Failure(DatabaseError(
                "Failed to retrieve exams due to database error",
                details={'original_error': str(e)}
            ))
        except Exception as e:
            logger.exception(f"Unexpected error retrieving exams: {e}")
            return Failure(SystemError(
                "An unexpected error occurred while retrieving exams",
                details={'original_error': str(e)}
            ))
    
    def update_exam(self, exam_id: int, exam_data: Dict[str, Any]) -> Result[Exam, Any]:
        """
        Update an existing exam with error handling.
        
        Args:
            exam_id: Primary key of the exam
            exam_data: Dictionary containing fields to update
            
        Returns:
            Result[Exam, Error]: Success with updated Exam or Failure with error
        """
        try:
            # Check if exam exists
            exam = self.exam_repository.get_by_id(exam_id)
            if exam is None:
                logger.warning(f"Cannot update: exam not found {exam_id}")
                return Failure(NotFoundError(
                    f"Exam with ID {exam_id} not found",
                    details={'exam_id': exam_id}
                ))
            
            # Validate duration if provided
            if 'duration_minutes' in exam_data:
                duration = exam_data['duration_minutes']
                if not isinstance(duration, int) or duration <= 0:
                    logger.warning(f"Exam update failed: invalid duration {duration}")
                    return Failure(ValidationError(
                        "Duration must be a positive integer",
                        details={'field': 'duration_minutes', 'value': duration}
                    ))
            
            # Update exam
            updated_exam = self.exam_repository.update(exam_id, **exam_data)
            
            if updated_exam is None:
                logger.error(f"Exam update returned None: {exam_id}")
                return Failure(DatabaseError(
                    "Failed to update exam",
                    details={'exam_id': exam_id}
                ))
            
            logger.info(f"Exam updated successfully: {exam_id}")
            return Success(updated_exam)
            
        except DjangoDatabaseError as e:
            logger.error(f"Database error updating exam {exam_id}: {e}", exc_info=True)
            return Failure(DatabaseError(
                "Failed to update exam due to database error",
                details={'exam_id': exam_id, 'original_error': str(e)}
            ))
        except Exception as e:
            logger.exception(f"Unexpected error updating exam {exam_id}: {e}")
            return Failure(SystemError(
                "An unexpected error occurred while updating exam",
                details={'exam_id': exam_id, 'original_error': str(e)}
            ))
    
    def delete_exam(self, exam_id: int) -> Result[bool, Any]:
        """
        Delete an exam and all its questions with error handling.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            Result[bool, Error]: Success with True or Failure with error
        """
        try:
            # Check if exam exists
            exam = self.exam_repository.get_by_id(exam_id)
            if exam is None:
                logger.warning(f"Cannot delete: exam not found {exam_id}")
                return Failure(NotFoundError(
                    f"Exam with ID {exam_id} not found",
                    details={'exam_id': exam_id}
                ))
            
            # Delete exam (questions will be deleted automatically due to CASCADE)
            with transaction.atomic():
                success = self.exam_repository.delete(exam_id)
                
                if not success:
                    logger.error(f"Exam deletion failed: {exam_id}")
                    return Failure(DatabaseError(
                        "Failed to delete exam",
                        details={'exam_id': exam_id}
                    ))
                
                logger.info(f"Exam deleted successfully: {exam_id}")
                return Success(True)
                
        except DjangoDatabaseError as e:
            logger.error(f"Database error deleting exam {exam_id}: {e}", exc_info=True)
            return Failure(DatabaseError(
                "Failed to delete exam due to database error",
                details={'exam_id': exam_id, 'original_error': str(e)}
            ))
        except Exception as e:
            logger.exception(f"Unexpected error deleting exam {exam_id}: {e}")
            return Failure(SystemError(
                "An unexpected error occurred while deleting exam",
                details={'exam_id': exam_id, 'original_error': str(e)}
            ))
    
    def serialize_exam(self, exam_id: int) -> Result[Dict[str, Any], Any]:
        """
        Serialize an exam to JSON format with error handling.
        
        Args:
            exam_id: Primary key of the exam
            
        Returns:
            Result[Dict, Error]: Success with exam dict or Failure with error
        """
        # Get exam with questions
        result = self.get_exam_with_questions(exam_id)
        
        if result.is_failure():
            return result
        
        try:
            exam = result.value
            
            questions_data = []
            for question in exam.questions.all():
                questions_data.append({
                    'id': question.id,
                    'type': question.question_type,
                    'text': question.question_text,
                    'options': question.options,
                    'correct_answer': question.correct_answer,
                    'points': float(question.points),
                    'order_index': question.order_index
                })
            
            exam_dict = {
                'exam_id': exam.id,
                'title': exam.title,
                'description': exam.description,
                'duration_minutes': exam.duration_minutes,
                'is_active': exam.is_active,
                'questions': questions_data
            }
            
            logger.debug(f"Exam serialized: {exam_id}")
            return Success(exam_dict)
            
        except Exception as e:
            logger.exception(f"Error serializing exam {exam_id}: {e}")
            return Failure(SystemError(
                "Failed to serialize exam",
                details={'exam_id': exam_id, 'original_error': str(e)}
            ))
