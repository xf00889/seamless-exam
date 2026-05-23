"""
Base abstract class for question generators.
Follows Open/Closed principle for extensibility.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseQuestionGenerator(ABC):
    """
    Abstract base class for question generators.
    All specific question generators must inherit from this class.
    """
    
    @abstractmethod
    def generate(self, text: str, **kwargs) -> List[Dict[str, any]]:
        """
        Generate questions from the provided text.
        
        Args:
            text: Input text to generate questions from
            **kwargs: Additional parameters specific to generator type
            
        Returns:
            List of question dictionaries with structure:
            {
                'type': str,  # Question type (MCQ, IDENTIFICATION, etc.)
                'question': str,  # Question text
                'options': List[Dict],  # For MCQ (optional)
                'correct_answer': any,  # Correct answer(s)
                'points': float,  # Default points
                'metadata': Dict  # Additional metadata (optional)
            }
        """
        pass
    
    @abstractmethod
    def can_generate(self, text: str) -> bool:
        """
        Determine if this generator can produce questions from the given text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            True if generator can produce questions, False otherwise
        """
        pass
    
    def validate_question(self, question: Dict[str, any]) -> bool:
        """
        Validate that a generated question has the required structure.
        
        Args:
            question: Question dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(question, dict):
            return False
        
        # Check required fields
        required_fields = ['type', 'question', 'correct_answer']
        for field in required_fields:
            if field not in question:
                return False
        
        # Check question text is not empty
        if not question['question'] or not question['question'].strip():
            return False
        
        return True
    
    def set_default_points(self, question: Dict[str, any], points: float = 1.0) -> Dict[str, any]:
        """
        Set default points for a question if not already set.
        
        Args:
            question: Question dictionary
            points: Default points value
            
        Returns:
            Question dictionary with points set
        """
        if 'points' not in question:
            question['points'] = points
        
        return question
