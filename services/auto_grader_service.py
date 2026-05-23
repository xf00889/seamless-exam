"""
Auto-grading service for objective questions.
Implements automatic grading for MCQ, Identification, True/False, and Enumeration questions.
"""
from typing import Optional, Dict, Any, List
from decimal import Decimal
import logging
from exams.models import QuestionType, Question
from attempts.models import Answer, Attempt, AttemptStatus
from repositories.answer_repository import AnswerRepository
from repositories.attempt_repository import AttemptRepository
from processing.utils.fuzzy_matcher import FuzzyMatcher

logger = logging.getLogger(__name__)


class AutoGraderService:
    """
    Service class for automatic grading of objective questions.
    Handles MCQ, Identification, True/False, and Enumeration questions.
    """
    
    def __init__(self, fuzzy_threshold: int = 80):
        """
        Initialize auto-grader service.
        
        Args:
            fuzzy_threshold: Similarity threshold for fuzzy matching (0-100)
        """
        self.answer_repository = AnswerRepository()
        self.attempt_repository = AttemptRepository()
        self.fuzzy_matcher = FuzzyMatcher(default_threshold=fuzzy_threshold)
    
    def grade_mcq(self, answer: Answer, question: Question) -> Dict[str, Any]:
        """
        Grade a multiple choice question using exact matching.
        
        Args:
            answer: Answer instance to grade
            question: Question instance with correct answer
            
        Returns:
            Dictionary with grading results: {is_correct, points_earned}
        """
        try:
            # Extract student's answer (check both 'value' and 'answer' keys for compatibility)
            student_answer = answer.answer_text.get('value', answer.answer_text.get('answer', ''))
            
            # Extract correct answer from question
            correct_answer = question.correct_answer
            
            # Handle different correct_answer formats
            if isinstance(correct_answer, dict):
                correct_answer = correct_answer.get('answer', correct_answer.get('value', ''))
            elif isinstance(correct_answer, list):
                correct_answer = correct_answer[0] if correct_answer else ''
            
            # Exact match comparison (case-insensitive)
            is_correct = str(student_answer).strip().upper() == str(correct_answer).strip().upper()
            
            points_earned = Decimal(str(question.points)) if is_correct else Decimal('0.00')
            
            logger.info(f"MCQ grading: Answer {answer.id}, Correct: {is_correct}, Points: {points_earned}")
            
            return {
                'is_correct': is_correct,
                'points_earned': points_earned
            }
        except Exception as e:
            logger.error(f"Error grading MCQ answer {answer.id}: {e}")
            return {
                'is_correct': False,
                'points_earned': Decimal('0.00')
            }
    
    def grade_identification(self, answer: Answer, question: Question) -> Dict[str, Any]:
        """
        Grade an identification question using fuzzy matching.
        
        Args:
            answer: Answer instance to grade
            question: Question instance with correct answer(s)
            
        Returns:
            Dictionary with grading results: {is_correct, points_earned}
        """
        try:
            # Extract student's answer (check both 'value' and 'answer' keys for compatibility)
            student_answer = answer.answer_text.get('value', answer.answer_text.get('answer', ''))
            
            if not student_answer or not str(student_answer).strip():
                return {
                    'is_correct': False,
                    'points_earned': Decimal('0.00')
                }
            
            # Extract correct answer(s) from question
            correct_answers = question.correct_answer
            
            # Normalize to list format
            if isinstance(correct_answers, str):
                correct_answers = [correct_answers]
            elif isinstance(correct_answers, dict):
                correct_answers = [correct_answers.get('answer', '')]
            elif not isinstance(correct_answers, list):
                correct_answers = [str(correct_answers)]
            
            # Clean and filter empty answers
            correct_answers = [str(ans).strip() for ans in correct_answers if ans]
            
            if not correct_answers:
                return {
                    'is_correct': False,
                    'points_earned': Decimal('0.00')
                }
            
            # Use fuzzy matching to check if student answer matches any correct answer
            student_answer_str = str(student_answer).strip()
            is_correct = self.fuzzy_matcher.match_any(
                student_answer_str,
                correct_answers,
                case_sensitive=False
            )
            
            points_earned = Decimal(str(question.points)) if is_correct else Decimal('0.00')
            
            logger.info(f"Identification grading: Answer {answer.id}, Correct: {is_correct}, Points: {points_earned}")
            
            return {
                'is_correct': is_correct,
                'points_earned': points_earned
            }
        except Exception as e:
            logger.error(f"Error grading Identification answer {answer.id}: {e}")
            return {
                'is_correct': False,
                'points_earned': Decimal('0.00')
            }
    
    def grade_true_false(self, answer: Answer, question: Question) -> Dict[str, Any]:
        """
        Grade a True/False question using boolean comparison.
        
        Args:
            answer: Answer instance to grade
            question: Question instance with correct answer
            
        Returns:
            Dictionary with grading results: {is_correct, points_earned}
        """
        try:
            # Extract student's answer (check both 'value' and 'answer' keys for compatibility)
            student_answer = answer.answer_text.get('value', answer.answer_text.get('answer', ''))
            
            # Extract correct answer from question
            correct_answer = question.correct_answer
            
            # Handle different correct_answer formats
            if isinstance(correct_answer, dict):
                correct_answer = correct_answer.get('answer', correct_answer.get('value', ''))
            elif isinstance(correct_answer, list):
                correct_answer = correct_answer[0] if correct_answer else ''
            
            # Normalize to boolean values
            def normalize_boolean(value) -> Optional[bool]:
                """Convert various boolean representations to bool."""
                if isinstance(value, bool):
                    return value
                
                value_str = str(value).strip().lower()
                
                if value_str in ['true', 't', '1', 'yes', 'y']:
                    return True
                elif value_str in ['false', 'f', '0', 'no', 'n']:
                    return False
                
                return None
            
            student_bool = normalize_boolean(student_answer)
            correct_bool = normalize_boolean(correct_answer)
            
            # Check if both are valid booleans and match
            is_correct = (student_bool is not None and 
                         correct_bool is not None and 
                         student_bool == correct_bool)
            
            points_earned = Decimal(str(question.points)) if is_correct else Decimal('0.00')
            
            logger.info(f"True/False grading: Answer {answer.id}, Correct: {is_correct}, Points: {points_earned}")
            
            return {
                'is_correct': is_correct,
                'points_earned': points_earned
            }
        except Exception as e:
            logger.error(f"Error grading True/False answer {answer.id}: {e}")
            return {
                'is_correct': False,
                'points_earned': Decimal('0.00')
            }
    
    def grade_enumeration(self, answer: Answer, question: Question) -> Dict[str, Any]:
        """
        Grade an enumeration question using fuzzy matching for items.
        
        Args:
            answer: Answer instance to grade
            question: Question instance with correct answer(s)
            
        Returns:
            Dictionary with grading results: {is_correct, points_earned}
        """
        try:
            # Extract student's answers (check both 'value' and 'answer' keys for compatibility)
            student_answers = answer.answer_text.get('value', answer.answer_text.get('answer', []))
            
            # Normalize to list
            if isinstance(student_answers, str):
                # Split by common delimiters if it's a string
                student_answers = [item.strip() for item in student_answers.split(',')]
            elif not isinstance(student_answers, list):
                student_answers = [str(student_answers)]
            
            # Filter empty answers
            student_answers = [str(ans).strip() for ans in student_answers if ans and str(ans).strip()]
            
            if not student_answers:
                return {
                    'is_correct': False,
                    'points_earned': Decimal('0.00')
                }
            
            # Extract correct answers from question
            correct_answers = question.correct_answer
            
            # Normalize to list format
            if isinstance(correct_answers, str):
                correct_answers = [correct_answers]
            elif isinstance(correct_answers, dict):
                # Check for 'answers' or 'answer' key
                if 'answers' in correct_answers:
                    correct_answers = correct_answers['answers']
                elif 'answer' in correct_answers:
                    correct_answers = correct_answers['answer']
                else:
                    correct_answers = []
                
                if not isinstance(correct_answers, list):
                    correct_answers = [correct_answers]
            elif not isinstance(correct_answers, list):
                correct_answers = [str(correct_answers)]
            
            # Clean correct answers
            correct_answers = [str(ans).strip() for ans in correct_answers if ans]
            
            if not correct_answers:
                return {
                    'is_correct': False,
                    'points_earned': Decimal('0.00')
                }
            
            # Get minimum required items (default to all if not specified)
            min_required = question.correct_answer.get('min_required', len(correct_answers)) \
                          if isinstance(question.correct_answer, dict) else len(correct_answers)
            
            # Count how many student answers match correct answers using fuzzy matching
            matched_count = 0
            for student_ans in student_answers:
                if self.fuzzy_matcher.match_any(student_ans, correct_answers, case_sensitive=False):
                    matched_count += 1
            
            # Check if student provided at least the minimum required correct items
            is_correct = matched_count >= min_required
            
            # Calculate partial credit based on matched items
            if matched_count > 0:
                # Award partial credit proportional to correct items
                credit_ratio = min(matched_count / min_required, 1.0)
                points_earned = Decimal(str(question.points)) * Decimal(str(credit_ratio))
            else:
                points_earned = Decimal('0.00')
            
            logger.info(f"Enumeration grading: Answer {answer.id}, Matched: {matched_count}/{min_required}, Points: {points_earned}")
            
            return {
                'is_correct': is_correct,
                'points_earned': points_earned
            }
        except Exception as e:
            logger.error(f"Error grading Enumeration answer {answer.id}: {e}")
            return {
                'is_correct': False,
                'points_earned': Decimal('0.00')
            }
    
    def grade_answer(self, answer: Answer) -> bool:
        """
        Grade a single answer based on its question type.
        
        Args:
            answer: Answer instance to grade
            
        Returns:
            True if grading successful, False otherwise
        """
        try:
            question = answer.question
            
            # Skip essay questions (require manual grading)
            if question.question_type == QuestionType.ESSAY:
                logger.info(f"Skipping essay question {question.id} - requires manual grading")
                return False
            
            # Grade based on question type
            if question.question_type == QuestionType.MCQ:
                result = self.grade_mcq(answer, question)
            elif question.question_type == QuestionType.IDENTIFICATION:
                result = self.grade_identification(answer, question)
            elif question.question_type == QuestionType.TRUE_FALSE:
                result = self.grade_true_false(answer, question)
            elif question.question_type == QuestionType.ENUMERATION:
                result = self.grade_enumeration(answer, question)
            else:
                logger.warning(f"Unknown question type: {question.question_type}")
                return False
            
            # Update answer with grading results
            self.answer_repository.update_grading(
                answer.id,
                is_correct=result['is_correct'],
                points_earned=float(result['points_earned'])
            )
            
            return True
        except Exception as e:
            logger.error(f"Error grading answer {answer.id}: {e}")
            return False
    
    def grade_attempt(self, attempt_id: int) -> bool:
        """
        Grade all objective questions in an attempt and calculate total score.
        
        Args:
            attempt_id: Primary key of the attempt to grade
            
        Returns:
            True if grading successful, False otherwise
        """
        try:
            # Get attempt with answers and questions
            attempt = self.attempt_repository.get_with_answers_and_questions(attempt_id)
            
            if not attempt:
                logger.error(f"Attempt {attempt_id} not found")
                return False
            
            # Grade each answer
            graded_count = 0
            for answer in attempt.answers.all():
                if self.grade_answer(answer):
                    graded_count += 1
            
            logger.info(f"Graded {graded_count} answers for attempt {attempt_id}")
            
            # Calculate total score
            total_score = self.calculate_total_score(attempt_id)
            
            # Update attempt with total score
            self.attempt_repository.update_score(attempt_id, float(total_score))
            
            # Update status to graded if all objective questions are graded
            # (essays may still need manual grading)
            has_ungraded_essays = any(
                answer.question.question_type == QuestionType.ESSAY and answer.is_correct is None
                for answer in attempt.answers.all()
            )
            
            if not has_ungraded_essays:
                self.attempt_repository.update_status(attempt_id, AttemptStatus.GRADED)
            
            logger.info(f"Attempt {attempt_id} total score: {total_score}")
            
            return True
        except Exception as e:
            logger.error(f"Error grading attempt {attempt_id}: {e}")
            return False
    
    def calculate_total_score(self, attempt_id: int) -> Decimal:
        """
        Calculate the total score for an attempt by summing points earned.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            Total score as Decimal
        """
        try:
            answers = self.answer_repository.get_by_attempt(attempt_id)
            
            total = Decimal('0.00')
            for answer in answers:
                if answer.points_earned is not None:
                    total += Decimal(str(answer.points_earned))
            
            return total
        except Exception as e:
            logger.error(f"Error calculating total score for attempt {attempt_id}: {e}")
            return Decimal('0.00')
    
    def regrade_attempt(self, attempt_id: int) -> bool:
        """
        Regrade an attempt (useful after manual essay grading).
        Recalculates total score from all graded answers.
        
        Args:
            attempt_id: Primary key of the attempt
            
        Returns:
            True if regrading successful, False otherwise
        """
        try:
            # Recalculate total score
            total_score = self.calculate_total_score(attempt_id)
            
            # Update attempt with new total score
            self.attempt_repository.update_score(attempt_id, float(total_score))
            
            # Check if all questions are now graded
            attempt = self.attempt_repository.get_with_answers_and_questions(attempt_id)
            if attempt:
                all_graded = all(
                    answer.is_correct is not None
                    for answer in attempt.answers.all()
                )
                
                if all_graded:
                    self.attempt_repository.update_status(attempt_id, AttemptStatus.GRADED)
            
            logger.info(f"Regraded attempt {attempt_id}, new total score: {total_score}")
            
            return True
        except Exception as e:
            logger.error(f"Error regrading attempt {attempt_id}: {e}")
            return False
