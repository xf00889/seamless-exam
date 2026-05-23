"""
MCQ Builder utility for structuring multiple choice questions.
"""
from typing import List, Dict, Optional
import re


class MCQBuilder:
    """
    Utility class for building and structuring MCQ questions from detected patterns.
    """
    
    def __init__(self):
        """Initialize MCQ builder."""
        self.choice_pattern = re.compile(r'^\s*([A-Za-z])[.)]\s+(.+)', re.MULTILINE)
    
    def build_mcq(self, question_text: str, choices: List[Dict[str, str]], 
                  correct_answer: Optional[str] = None) -> Dict[str, any]:
        """
        Build a structured MCQ question from components.
        
        Args:
            question_text: The question text
            choices: List of choice dictionaries with 'key' and 'value'
            correct_answer: The correct answer key (optional)
            
        Returns:
            Dictionary with structured MCQ data
        """
        if not question_text or not choices:
            raise ValueError("Question text and choices are required")
        
        if len(choices) < 2:
            raise ValueError("MCQ must have at least 2 choices")
        
        # Normalize choice keys to uppercase
        normalized_choices = []
        for choice in choices:
            normalized_choices.append({
                'key': choice['key'].upper(),
                'value': choice['value'].strip()
            })
        
        mcq = {
            'type': 'MCQ',
            'question': question_text.strip(),
            'options': normalized_choices,
            'correct_answer': correct_answer.upper() if correct_answer else None
        }
        
        return mcq
    
    def extract_mcq_from_text(self, text: str) -> Optional[Dict[str, any]]:
        """
        Extract MCQ structure from a text block containing question and choices.
        
        Args:
            text: Text block with question and choices
            
        Returns:
            Structured MCQ dictionary or None if not valid MCQ
        """
        lines = text.split('\n')
        
        # Find where choices start
        choice_start_idx = None
        for idx, line in enumerate(lines):
            if self.choice_pattern.match(line.strip()):
                choice_start_idx = idx
                break
        
        if choice_start_idx is None or choice_start_idx == 0:
            # No choices found or choices at the beginning (no question)
            return None
        
        # Split into question and choices
        question_lines = lines[:choice_start_idx]
        choice_lines = lines[choice_start_idx:]
        
        question_text = '\n'.join(question_lines).strip()
        
        if not question_text:
            return None
        
        # Extract choices
        choices = []
        for line in choice_lines:
            match = self.choice_pattern.match(line.strip())
            if match:
                choices.append({
                    'key': match.group(1).upper(),
                    'value': match.group(2).strip()
                })
        
        if len(choices) < 2:
            return None
        
        return self.build_mcq(question_text, choices)
    
    def validate_mcq(self, mcq: Dict[str, any]) -> bool:
        """
        Validate that an MCQ structure is complete and correct.
        
        Args:
            mcq: MCQ dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(mcq, dict):
            return False
        
        # Check required fields
        if 'question' not in mcq or 'options' not in mcq:
            return False
        
        # Check question is not empty
        if not mcq['question'] or not mcq['question'].strip():
            return False
        
        # Check options
        options = mcq['options']
        if not isinstance(options, list) or len(options) < 2:
            return False
        
        # Check each option has key and value
        seen_keys = set()
        for option in options:
            if not isinstance(option, dict):
                return False
            if 'key' not in option or 'value' not in option:
                return False
            if not option['key'] or not option['value']:
                return False
            
            # Check for duplicate keys
            if option['key'] in seen_keys:
                return False
            seen_keys.add(option['key'])
        
        # If correct_answer is provided, validate it exists in options
        if 'correct_answer' in mcq and mcq['correct_answer']:
            if mcq['correct_answer'] not in seen_keys:
                return False
        
        return True
    
    def add_correct_answer(self, mcq: Dict[str, any], correct_key: str) -> Dict[str, any]:
        """
        Add or update the correct answer for an MCQ.
        
        Args:
            mcq: MCQ dictionary
            correct_key: The key of the correct answer
            
        Returns:
            Updated MCQ dictionary
        """
        if not self.validate_mcq(mcq):
            raise ValueError("Invalid MCQ structure")
        
        # Validate correct_key exists in options
        option_keys = {opt['key'] for opt in mcq['options']}
        if correct_key.upper() not in option_keys:
            raise ValueError(f"Correct answer key '{correct_key}' not found in options")
        
        mcq['correct_answer'] = correct_key.upper()
        return mcq
    
    def reorder_choices(self, mcq: Dict[str, any], new_order: List[str]) -> Dict[str, any]:
        """
        Reorder MCQ choices according to specified key order.
        
        Args:
            mcq: MCQ dictionary
            new_order: List of choice keys in desired order
            
        Returns:
            MCQ with reordered choices
        """
        if not self.validate_mcq(mcq):
            raise ValueError("Invalid MCQ structure")
        
        # Create mapping of key to option
        option_map = {opt['key']: opt for opt in mcq['options']}
        
        # Validate all keys in new_order exist
        for key in new_order:
            if key not in option_map:
                raise ValueError(f"Key '{key}' not found in options")
        
        # Reorder
        mcq['options'] = [option_map[key] for key in new_order]
        
        return mcq
