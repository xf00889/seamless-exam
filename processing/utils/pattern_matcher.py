"""
Pattern matching utility for detecting numbering, choices, and keywords in text.
"""
import re
from typing import List, Dict, Optional, Tuple
from enum import Enum


class QuestionType(Enum):
    """Enumeration of question types."""
    MCQ = "MCQ"
    IDENTIFICATION = "IDENTIFICATION"
    ENUMERATION = "ENUMERATION"
    ESSAY = "ESSAY"
    TRUE_FALSE = "TRUE_FALSE"
    UNKNOWN = "UNKNOWN"


class PatternMatcher:
    """
    Utility class for detecting patterns in text that indicate questions,
    choices, numbering, and question types.
    """
    
    def __init__(self):
        """Initialize pattern matcher with regex patterns."""
        # Numbered question patterns (1., 2., 1), 2), etc.)
        self.numbered_pattern = re.compile(r'^\s*(\d+)[.)]\s+(.+)', re.MULTILINE)
        
        # Choice patterns (A., B., A), B), etc.)
        self.choice_pattern = re.compile(r'^\s*([A-Za-z])[.)]\s+(.+)', re.MULTILINE)
        
        # Question mark pattern
        self.question_mark_pattern = re.compile(r'\?[\s]*$')
        
        # Keywords for different question types
        self.identification_keywords = [
            'define', 'what is', 'who is', 'when is', 'where is',
            'identify', 'name', 'state', 'give the'
        ]
        
        self.enumeration_keywords = [
            'enumerate', 'list', 'give', 'mention', 'name',
            'state the', 'provide', 'cite'
        ]
        
        self.essay_keywords = [
            'explain', 'discuss', 'describe', 'compare', 'contrast',
            'analyze', 'evaluate', 'justify', 'argue', 'elaborate'
        ]
        
        self.true_false_keywords = [
            'true or false', 't or f', 'true/false', 't/f'
        ]
    
    def detect_numbered_items(self, text: str) -> List[Dict[str, any]]:
        """
        Detect numbered items in text (potential questions).
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of dictionaries with 'number' and 'text' keys
        """
        matches = self.numbered_pattern.finditer(text)
        items = []
        
        for match in matches:
            items.append({
                'number': int(match.group(1)),
                'text': match.group(2).strip(),
                'start': match.start(),
                'end': match.end()
            })
        
        return items
    
    def detect_choice_items(self, text: str) -> List[Dict[str, any]]:
        """
        Detect choice items in text (potential MCQ options).
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of dictionaries with 'key' and 'value' keys
        """
        matches = self.choice_pattern.finditer(text)
        choices = []
        
        for match in matches:
            choices.append({
                'key': match.group(1).upper(),
                'value': match.group(2).strip(),
                'start': match.start(),
                'end': match.end()
            })
        
        return choices
    
    def has_question_mark(self, text: str) -> bool:
        """
        Check if text ends with a question mark.
        
        Args:
            text: Input text
            
        Returns:
            True if text ends with question mark, False otherwise
        """
        return bool(self.question_mark_pattern.search(text))
    
    def classify_question_type(self, text: str) -> QuestionType:
        """
        Classify question type based on keywords and patterns.
        
        Args:
            text: Question text
            
        Returns:
            QuestionType enum value
        """
        text_lower = text.lower()
        
        # Check for True/False
        if any(keyword in text_lower for keyword in self.true_false_keywords):
            return QuestionType.TRUE_FALSE
        
        # Check for Identification
        if any(text_lower.startswith(keyword) for keyword in self.identification_keywords):
            return QuestionType.IDENTIFICATION
        
        # Check for Enumeration
        if any(keyword in text_lower for keyword in self.enumeration_keywords):
            return QuestionType.ENUMERATION
        
        # Check for Essay
        if any(text_lower.startswith(keyword) for keyword in self.essay_keywords):
            return QuestionType.ESSAY
        
        # Check if it has choices (MCQ)
        choices = self.detect_choice_items(text)
        if len(choices) >= 2:
            return QuestionType.MCQ
        
        return QuestionType.UNKNOWN
    
    def extract_question_and_choices(self, text: str) -> Optional[Dict[str, any]]:
        """
        Extract question text and choices from a text block.
        
        Args:
            text: Text block containing question and possibly choices
            
        Returns:
            Dictionary with 'question' and 'choices' keys, or None
        """
        lines = text.split('\n')
        
        # Find where choices start
        choice_start_idx = None
        for idx, line in enumerate(lines):
            if self.choice_pattern.match(line.strip()):
                choice_start_idx = idx
                break
        
        if choice_start_idx is None:
            # No choices found
            return {
                'question': text.strip(),
                'choices': []
            }
        
        # Split into question and choices
        question_lines = lines[:choice_start_idx]
        choice_lines = lines[choice_start_idx:]
        
        question_text = '\n'.join(question_lines).strip()
        
        # Extract choices
        choices = []
        for line in choice_lines:
            match = self.choice_pattern.match(line.strip())
            if match:
                choices.append({
                    'key': match.group(1).upper(),
                    'value': match.group(2).strip()
                })
        
        return {
            'question': question_text,
            'choices': choices
        }
    
    def is_likely_question(self, text: str) -> bool:
        """
        Determine if text is likely a question based on multiple indicators.
        
        Args:
            text: Input text
            
        Returns:
            True if text is likely a question, False otherwise
        """
        if not text or len(text.strip()) < 5:
            return False
        
        # Check for question mark
        if self.has_question_mark(text):
            return True
        
        # Check for question keywords
        text_lower = text.lower()
        all_keywords = (
            self.identification_keywords +
            self.enumeration_keywords +
            self.essay_keywords
        )
        
        if any(text_lower.startswith(keyword) for keyword in all_keywords):
            return True
        
        return False
