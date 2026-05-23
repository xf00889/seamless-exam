"""
Question Approval Service for teacher review workflow.
Implements business logic for reviewing and approving extracted/generated questions.
"""
import logging
from typing import List, Dict, Optional

from repositories.extracted_content_repository import ExtractedContentRepository
from repositories.exam_repository import ExamRepository
from repositories.question_repository import QuestionRepository
from exams.models import Question, QuestionType

logger = logging.getLogger(__name__)


class QuestionApprovalError(Exception):
    """Custom exception for question approval errors."""
    pass


class QuestionApprovalService:
    """
    Service for managing teacher review and approval of extracted/generated questions.
    Handles conversion of generated questions to exam questions.
    """
    
    def __init__(self):
        """Initialize service with repositories."""
        self.content_repository = ExtractedContentRepository()
        self.exam_repository = ExamRepository()
        self.question_repository = QuestionRepository()
    
    def get_questions_for_review(self, document_id: int) -> List[Dict[str, any]]:
        """
        Get extracted/generated questions for teacher review.
        
        Args:
            document_id: ID of the document
            
        Returns:
            List of question dictionaries
            
        Raises:
            QuestionApprovalError: If content not found
        """
        content = self.content_repository.get_by_document(document_id)
        
        if not content:
            raise QuestionApprovalError(
                f"No extracted content found for document {document_id}"
            )
        
        return content.processed_questions or []
    
    def update_question(
        self,
        document_id: int,
        question_index: int,
        updated_question: Dict[str, any]
    ) -> List[Dict[str, any]]:
        """
        Update a specific question in the extracted content.
        
        Args:
            document_id: ID of the document
            question_index: Index of the question to update
            updated_question: Updated question dictionary
            
        Returns:
            Updated list of all questions
            
        Raises:
            QuestionApprovalError: If update fails
        """
        content = self.content_repository.get_by_document(document_id)
        
        if not content:
            raise QuestionApprovalError(
                f"No extracted content found for document {document_id}"
            )
        
        questions = content.processed_questions or []
        
        if question_index < 0 or question_index >= len(questions):
            raise QuestionApprovalError(
                f"Invalid question index: {question_index}"
            )
        
        # Update the question
        questions[question_index] = updated_question
        
        # Save updated questions
        updated_content = self.content_repository.update(
            content.id,
            processed_questions=questions
        )
        
        logger.info(f"Updated question {question_index} for document {document_id}")
        return updated_content.processed_questions
    
    def delete_question(
        self,
        document_id: int,
        question_index: int
    ) -> List[Dict[str, any]]:
        """
        Delete a question from the extracted content.
        
        Args:
            document_id: ID of the document
            question_index: Index of the question to delete
            
        Returns:
            Updated list of remaining questions
            
        Raises:
            QuestionApprovalError: If deletion fails
        """
        content = self.content_repository.get_by_document(document_id)
        
        if not content:
            raise QuestionApprovalError(
                f"No extracted content found for document {document_id}"
            )
        
        questions = content.processed_questions or []
        
        if question_index < 0 or question_index >= len(questions):
            raise QuestionApprovalError(
                f"Invalid question index: {question_index}"
            )
        
        # Remove the question
        questions.pop(question_index)
        
        # Save updated questions
        updated_content = self.content_repository.update(
            content.id,
            processed_questions=questions
        )
        
        logger.info(f"Deleted question {question_index} from document {document_id}")
        return updated_content.processed_questions
    
    def add_question(
        self,
        document_id: int,
        new_question: Dict[str, any]
    ) -> List[Dict[str, any]]:
        """
        Add a new question to the extracted content.
        
        Args:
            document_id: ID of the document
            new_question: New question dictionary to add
            
        Returns:
            Updated list of all questions
            
        Raises:
            QuestionApprovalError: If addition fails
        """
        content = self.content_repository.get_by_document(document_id)
        
        if not content:
            raise QuestionApprovalError(
                f"No extracted content found for document {document_id}"
            )
        
        questions = content.processed_questions or []
        
        # Add the new question
        questions.append(new_question)
        
        # Save updated questions
        updated_content = self.content_repository.update(
            content.id,
            processed_questions=questions
        )
        
        logger.info(f"Added new question to document {document_id}")
        return updated_content.processed_questions
    
    def approve_questions_to_exam(
        self,
        document_id: int,
        exam_id: int,
        question_indices: Optional[List[int]] = None
    ) -> List[Question]:
        """
        Approve and add questions from extracted content to an exam.
        
        Args:
            document_id: ID of the document
            exam_id: ID of the exam to add questions to
            question_indices: Optional list of question indices to approve
                            (None = approve all questions)
            
        Returns:
            List of created Question instances
            
        Raises:
            QuestionApprovalError: If approval fails
        """
        # Get extracted content
        content = self.content_repository.get_by_document(document_id)
        
        if not content:
            raise QuestionApprovalError(
                f"No extracted content found for document {document_id}"
            )
        
        # Get exam
        exam = self.exam_repository.get_by_id(exam_id)
        
        if not exam:
            raise QuestionApprovalError(f"Exam with ID {exam_id} not found")
        
        questions_to_approve = content.processed_questions or []
        
        if not questions_to_approve:
            raise QuestionApprovalError("No questions available to approve")
        
        # Filter questions if specific indices provided
        if question_indices is not None:
            questions_to_approve = [
                questions_to_approve[i]
                for i in question_indices
                if 0 <= i < len(questions_to_approve)
            ]
        
        # Get current max order index for the exam
        existing_questions = self.question_repository.get_by_exam(exam_id)
        max_order = max([q.order_index for q in existing_questions], default=0)
        
        # Create Question instances
        created_questions = []
        
        for idx, question_data in enumerate(questions_to_approve):
            try:
                question = self._convert_to_question(
                    question_data,
                    exam_id,
                    max_order + idx + 1
                )
                created_questions.append(question)
                
            except Exception as e:
                logger.error(f"Error creating question: {str(e)}")
                # Continue with other questions
                continue
        
        logger.info(
            f"Approved {len(created_questions)} questions from document {document_id} "
            f"to exam {exam_id}"
        )
        
        return created_questions
    
    def _convert_to_question(
        self,
        question_data: Dict[str, any],
        exam_id: int,
        order_index: int
    ) -> Question:
        """
        Convert a question dictionary to a Question model instance.
        
        Args:
            question_data: Question dictionary from generator
            exam_id: ID of the exam
            order_index: Order index for the question
            
        Returns:
            Created Question instance
            
        Raises:
            QuestionApprovalError: If conversion fails
        """
        try:
            # Extract question type
            question_type = question_data.get('type', 'UNKNOWN')
            
            # Validate question type
            if question_type not in [choice[0] for choice in QuestionType.choices]:
                raise QuestionApprovalError(f"Invalid question type: {question_type}")
            
            # Extract question text
            question_text = question_data.get('question', '')
            if not question_text:
                raise QuestionApprovalError("Question text is required")
            
            # Extract options (for MCQ)
            options = question_data.get('options', None)
            
            # Extract correct answer
            correct_answer = question_data.get('correct_answer')
            if correct_answer is None:
                raise QuestionApprovalError("Correct answer is required")
            
            # Extract points
            points = question_data.get('points', 1.0)
            
            # Create question
            question = self.question_repository.create(
                exam_id=exam_id,
                question_type=question_type,
                question_text=question_text,
                options=options,
                correct_answer=correct_answer,
                points=points,
                order_index=order_index
            )
            
            return question
            
        except Exception as e:
            logger.error(f"Error converting question data: {str(e)}")
            raise QuestionApprovalError(f"Failed to convert question: {str(e)}")
    
    def get_approval_summary(self, document_id: int) -> Dict[str, any]:
        """
        Get summary of questions available for approval.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Dictionary with summary information
        """
        content = self.content_repository.get_by_document(document_id)
        
        if not content:
            return {
                'total_questions': 0,
                'by_type': {},
                'has_content': False
            }
        
        questions = content.processed_questions or []
        
        # Count by type
        by_type = {}
        for question in questions:
            q_type = question.get('type', 'UNKNOWN')
            by_type[q_type] = by_type.get(q_type, 0) + 1
        
        return {
            'total_questions': len(questions),
            'by_type': by_type,
            'has_content': bool(content.raw_text)
        }
