"""
Question Generator orchestrator that coordinates multiple generator types.
"""
from typing import List, Dict, Optional
from .base_generator import BaseQuestionGenerator
from .mcq_generator import MCQGenerator
from .identification_generator import IdentificationGenerator
from .enumeration_generator import EnumerationGenerator
from processing.utils import NLPProcessor, TextCleaner


class QuestionGenerator:
    """
    Main orchestrator for question generation.
    Coordinates multiple generator types and produces diverse questions.
    """
    
    def __init__(self, nlp_processor: Optional[NLPProcessor] = None):
        """
        Initialize question generator with all sub-generators.
        
        Args:
            nlp_processor: Shared NLP processor instance (creates new if None)
        """
        self.nlp_processor = nlp_processor or NLPProcessor()
        self.text_cleaner = TextCleaner()
        
        # Initialize all generators
        self.generators: List[BaseQuestionGenerator] = [
            MCQGenerator(self.nlp_processor),
            IdentificationGenerator(self.nlp_processor),
            EnumerationGenerator(self.nlp_processor),
        ]
    
    def generate_questions(self, text: str, num_questions: int = 10,
                          question_types: Optional[List[str]] = None) -> List[Dict[str, any]]:
        """
        Generate questions from text using all available generators.
        
        Args:
            text: Input text to generate questions from
            num_questions: Total number of questions to generate
            question_types: List of question types to generate (None = all types)
                          Options: ['MCQ', 'IDENTIFICATION', 'ENUMERATION']
            
        Returns:
            List of question dictionaries from various generators
        """
        if not text or len(text.strip()) < 20:
            return []
        
        # Clean text
        cleaned_text = self.text_cleaner.clean(text)
        
        all_questions = []
        
        # Determine how many questions per type
        active_generators = self._get_active_generators(cleaned_text, question_types)
        
        if not active_generators:
            return []
        
        questions_per_type = max(1, num_questions // len(active_generators))
        
        # Generate questions from each generator
        for generator in active_generators:
            questions = generator.generate(
                cleaned_text,
                num_questions=questions_per_type
            )
            all_questions.extend(questions)
        
        # If we don't have enough questions, try to generate more
        if len(all_questions) < num_questions:
            for generator in active_generators:
                if len(all_questions) >= num_questions:
                    break
                
                additional = generator.generate(
                    cleaned_text,
                    num_questions=num_questions - len(all_questions)
                )
                all_questions.extend(additional)
        
        return all_questions[:num_questions]
    
    def generate_by_type(self, text: str, question_type: str,
                        num_questions: int = 5) -> List[Dict[str, any]]:
        """
        Generate questions of a specific type.
        
        Args:
            text: Input text to generate questions from
            question_type: Type of questions to generate
                          ('MCQ', 'IDENTIFICATION', 'ENUMERATION')
            num_questions: Number of questions to generate
            
        Returns:
            List of question dictionaries of the specified type
        """
        if not text or len(text.strip()) < 20:
            return []
        
        # Clean text
        cleaned_text = self.text_cleaner.clean(text)
        
        # Find the appropriate generator
        generator = self._get_generator_for_type(question_type)
        
        if not generator:
            return []
        
        if not generator.can_generate(cleaned_text):
            return []
        
        return generator.generate(cleaned_text, num_questions=num_questions)
    
    def can_generate_from_text(self, text: str) -> Dict[str, bool]:
        """
        Check which question types can be generated from the text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary mapping question types to boolean availability
        """
        if not text or len(text.strip()) < 20:
            return {
                'MCQ': False,
                'IDENTIFICATION': False,
                'ENUMERATION': False
            }
        
        cleaned_text = self.text_cleaner.clean(text)
        
        return {
            'MCQ': self._get_generator_for_type('MCQ').can_generate(cleaned_text),
            'IDENTIFICATION': self._get_generator_for_type('IDENTIFICATION').can_generate(cleaned_text),
            'ENUMERATION': self._get_generator_for_type('ENUMERATION').can_generate(cleaned_text),
        }
    
    def _get_active_generators(self, text: str,
                              question_types: Optional[List[str]] = None) -> List[BaseQuestionGenerator]:
        """
        Get list of generators that can produce questions from the text.
        
        Args:
            text: Input text
            question_types: Optional filter for specific question types
            
        Returns:
            List of active generators
        """
        active = []
        
        for generator in self.generators:
            # Check if this generator type is requested
            if question_types:
                # Determine generator type
                generator_type = self._get_generator_type(generator)
                if generator_type not in question_types:
                    continue
            
            # Check if generator can produce questions from this text
            if generator.can_generate(text):
                active.append(generator)
        
        return active
    
    def _get_generator_for_type(self, question_type: str) -> Optional[BaseQuestionGenerator]:
        """
        Get the generator for a specific question type.
        
        Args:
            question_type: Type of question ('MCQ', 'IDENTIFICATION', 'ENUMERATION')
            
        Returns:
            Generator instance or None
        """
        for generator in self.generators:
            if self._get_generator_type(generator) == question_type:
                return generator
        
        return None
    
    def _get_generator_type(self, generator: BaseQuestionGenerator) -> str:
        """
        Determine the question type produced by a generator.
        
        Args:
            generator: Generator instance
            
        Returns:
            Question type string
        """
        if isinstance(generator, MCQGenerator):
            return 'MCQ'
        elif isinstance(generator, IdentificationGenerator):
            return 'IDENTIFICATION'
        elif isinstance(generator, EnumerationGenerator):
            return 'ENUMERATION'
        else:
            return 'UNKNOWN'
    
    def add_generator(self, generator: BaseQuestionGenerator):
        """
        Add a custom generator to the orchestrator.
        
        Args:
            generator: Generator instance to add
        """
        if generator not in self.generators:
            self.generators.append(generator)
    
    def remove_generator(self, generator_type: str):
        """
        Remove a generator by type.
        
        Args:
            generator_type: Type of generator to remove
        """
        self.generators = [
            g for g in self.generators
            if self._get_generator_type(g) != generator_type
        ]
