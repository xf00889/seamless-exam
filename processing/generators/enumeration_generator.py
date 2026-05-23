"""
Enumeration Generator for creating enumeration/list questions.
"""
from typing import List, Dict, Optional
from .base_generator import BaseQuestionGenerator
from processing.utils import ListDetector, NLPProcessor, TextCleaner


class EnumerationGenerator(BaseQuestionGenerator):
    """
    Generator for Enumeration questions based on lists and sequences in text.
    """
    
    def __init__(self, nlp_processor: Optional[NLPProcessor] = None):
        """
        Initialize enumeration generator.
        
        Args:
            nlp_processor: NLP processor instance (creates new if None)
        """
        self.nlp_processor = nlp_processor or NLPProcessor()
        self.list_detector = ListDetector()
        self.text_cleaner = TextCleaner()
    
    def can_generate(self, text: str) -> bool:
        """
        Determine if enumeration questions can be generated from text.
        Requires detectable lists or sequences.
        
        Args:
            text: Input text to analyze
            
        Returns:
            True if enumeration questions can be generated, False otherwise
        """
        if not text or len(text.strip()) < 20:
            return False
        
        # Check if we can detect any lists
        detected_list = self.list_detector.detect_any_list(text)
        
        return detected_list is not None and len(detected_list['items']) >= 2
    
    def generate(self, text: str, num_questions: int = 5, **kwargs) -> List[Dict[str, any]]:
        """
        Generate enumeration questions from text.
        
        Args:
            text: Input text to generate questions from
            num_questions: Maximum number of questions to generate
            **kwargs: Additional parameters
            
        Returns:
            List of enumeration question dictionaries
        """
        if not self.can_generate(text):
            return []
        
        questions = []
        
        # Clean text
        cleaned_text = self.text_cleaner.clean(text)
        
        # Split text into paragraphs or sections
        sections = self._split_into_sections(cleaned_text)
        
        for section in sections:
            if len(questions) >= num_questions:
                break
            
            # Try to detect a list in this section
            detected_list = self.list_detector.detect_any_list(section)
            
            if detected_list and len(detected_list['items']) >= 2:
                question = self._create_question_from_list(section, detected_list)
                
                if question and self.validate_question(question):
                    questions.append(self.set_default_points(question, 3.0))
        
        return questions[:num_questions]
    
    def _split_into_sections(self, text: str) -> List[str]:
        """
        Split text into sections (paragraphs or logical blocks).
        
        Args:
            text: Input text
            
        Returns:
            List of text sections
        """
        # Split by double newlines (paragraphs)
        sections = text.split('\n\n')
        
        # Filter out very short sections
        sections = [s.strip() for s in sections if len(s.strip()) > 50]
        
        return sections
    
    def _create_question_from_list(self, section: str, detected_list: Dict[str, any]) -> Optional[Dict[str, any]]:
        """
        Create an enumeration question from a detected list.
        
        Args:
            section: Text section containing the list
            detected_list: Detected list information
            
        Returns:
            Enumeration question dictionary or None
        """
        items = detected_list['items']
        
        if len(items) < 2:
            return None
        
        # Extract the header/question part
        header, list_items = self.list_detector.split_by_list(section)
        
        if not list_items:
            return None
        
        # Create question text
        if header and len(header) > 10:
            # Use the header as the question
            question_text = header
            
            # If header doesn't end with question mark or colon, add instruction
            if not question_text.endswith('?') and not question_text.endswith(':'):
                question_text = f"List the items: {question_text}"
        else:
            # Generate a generic question
            question_text = f"Enumerate the items in the following list."
        
        # Ensure question asks for enumeration
        if not any(keyword in question_text.lower() for keyword in ['list', 'enumerate', 'name', 'give', 'mention']):
            question_text = f"List: {question_text}"
        
        # The correct answer is all the list items
        correct_answer = [item.lower().strip() for item in list_items]
        
        # Determine minimum required items (at least half)
        min_required = max(2, len(correct_answer) // 2)
        
        return {
            'type': 'ENUMERATION',
            'question': question_text,
            'correct_answer': correct_answer,
            'metadata': {
                'source': 'detected_list',
                'list_type': detected_list['type'],
                'total_items': len(correct_answer),
                'min_required': min_required
            }
        }
    
    def _extract_list_from_concepts(self, text: str) -> Optional[List[str]]:
        """
        Extract a list of related concepts from text using NLP.
        
        Args:
            text: Input text
            
        Returns:
            List of concepts or None
        """
        if not self.nlp_processor.is_available():
            return None
        
        # Extract key concepts
        concepts = self.nlp_processor.extract_key_concepts(text, max_concepts=10)
        
        if len(concepts) < 3:
            return None
        
        return concepts
    
    def validate_question(self, question: Dict[str, any]) -> bool:
        """
        Validate enumeration question structure.
        
        Args:
            question: Question dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not super().validate_question(question):
            return False
        
        # Check that correct_answer is a list
        if not isinstance(question['correct_answer'], list):
            return False
        
        # Check that we have at least 2 items
        if len(question['correct_answer']) < 2:
            return False
        
        return True
