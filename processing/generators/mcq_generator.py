"""
MCQ Generator for creating multiple choice questions with NLP concept identification.
"""
import random
from typing import List, Dict, Optional
from .base_generator import BaseQuestionGenerator
from processing.utils import NLPProcessor, MCQBuilder, TextCleaner


class MCQGenerator(BaseQuestionGenerator):
    """
    Generator for Multiple Choice Questions using NLP concept identification.
    Generates plausible distractors for MCQ questions.
    """
    
    def __init__(self, nlp_processor: Optional[NLPProcessor] = None):
        """
        Initialize MCQ generator.
        
        Args:
            nlp_processor: NLP processor instance (creates new if None)
        """
        self.nlp_processor = nlp_processor or NLPProcessor()
        self.mcq_builder = MCQBuilder()
        self.text_cleaner = TextCleaner()
    
    def can_generate(self, text: str) -> bool:
        """
        Determine if MCQ can be generated from text.
        Requires NLP processor and sufficient text content.
        
        Args:
            text: Input text to analyze
            
        Returns:
            True if MCQ can be generated, False otherwise
        """
        if not text or len(text.strip()) < 20:
            return False
        
        # Check if NLP processor is available
        if not self.nlp_processor.is_available():
            return False
        
        # Check if we can extract concepts
        concepts = self.nlp_processor.extract_key_concepts(text, max_concepts=3)
        return len(concepts) > 0
    
    def generate(self, text: str, num_questions: int = 5, 
                 num_options: int = 4, **kwargs) -> List[Dict[str, any]]:
        """
        Generate MCQ questions from text using NLP concept identification.
        
        Args:
            text: Input text to generate questions from
            num_questions: Maximum number of questions to generate
            num_options: Number of options per MCQ (default 4)
            **kwargs: Additional parameters
            
        Returns:
            List of MCQ question dictionaries
        """
        if not self.can_generate(text):
            return []
        
        questions = []
        
        # Clean text
        cleaned_text = self.text_cleaner.clean(text)
        
        # Extract definitions (good for MCQ)
        definitions = self.nlp_processor.extract_definitions(cleaned_text)
        
        for definition in definitions[:num_questions]:
            mcq = self._create_mcq_from_definition(
                definition['term'],
                definition['definition'],
                num_options
            )
            
            if mcq and self.validate_question(mcq):
                questions.append(self.set_default_points(mcq, 2.0))
        
        # If we don't have enough questions from definitions, try concept-based
        if len(questions) < num_questions:
            concept_questions = self._generate_concept_based_mcqs(
                cleaned_text,
                num_questions - len(questions),
                num_options
            )
            questions.extend(concept_questions)
        
        return questions[:num_questions]
    
    def _create_mcq_from_definition(self, term: str, definition: str, 
                                   num_options: int) -> Optional[Dict[str, any]]:
        """
        Create an MCQ question from a term and its definition.
        
        Args:
            term: The term being defined
            definition: The definition text
            num_options: Number of options to generate
            
        Returns:
            MCQ question dictionary or None
        """
        # Create question asking for the definition
        question_text = f"What is {term}?"
        
        # Correct answer is the definition
        correct_answer = definition
        
        # Generate distractors
        distractors = self._generate_distractors(definition, num_options - 1)
        
        if len(distractors) < num_options - 1:
            # Not enough distractors, skip this question
            return None
        
        # Build options
        options = [{'key': 'A', 'value': correct_answer}]
        
        for idx, distractor in enumerate(distractors):
            key = chr(ord('B') + idx)
            options.append({'key': key, 'value': distractor})
        
        # Shuffle options (but remember correct answer)
        correct_key = 'A'
        random.shuffle(options)
        
        # Find new position of correct answer
        for opt in options:
            if opt['value'] == correct_answer:
                correct_key = opt['key']
                break
        
        # Re-key options to be sequential
        for idx, opt in enumerate(options):
            old_key = opt['key']
            new_key = chr(ord('A') + idx)
            opt['key'] = new_key
            if old_key == correct_key:
                correct_key = new_key
        
        return {
            'type': 'MCQ',
            'question': question_text,
            'options': options,
            'correct_answer': correct_key,
            'metadata': {
                'source': 'definition',
                'term': term
            }
        }
    
    def _generate_concept_based_mcqs(self, text: str, num_questions: int,
                                    num_options: int) -> List[Dict[str, any]]:
        """
        Generate MCQs based on key concepts in the text.
        
        Args:
            text: Input text
            num_questions: Number of questions to generate
            num_options: Number of options per question
            
        Returns:
            List of MCQ question dictionaries
        """
        questions = []
        
        # Extract key concepts
        concepts = self.nlp_processor.extract_key_concepts(text, max_concepts=num_questions * 2)
        
        # Extract entities for additional context
        entities = self.nlp_processor.extract_entities(text)
        
        # Try to create questions about concepts
        for concept in concepts[:num_questions]:
            # Create a simple "What is X?" question
            question_text = f"What is {concept}?"
            
            # Try to find context for this concept in the text
            sentences = self.nlp_processor.tokenize_sentences(text)
            context_sentence = None
            
            for sentence in sentences:
                if concept.lower() in sentence.lower():
                    context_sentence = sentence
                    break
            
            if not context_sentence:
                continue
            
            # Use the sentence as the correct answer
            correct_answer = context_sentence.strip()
            
            # Generate distractors
            distractors = self._generate_distractors_from_text(
                text, 
                correct_answer, 
                num_options - 1
            )
            
            if len(distractors) < num_options - 1:
                continue
            
            # Build options
            options = [{'key': 'A', 'value': correct_answer}]
            
            for idx, distractor in enumerate(distractors):
                key = chr(ord('B') + idx)
                options.append({'key': key, 'value': distractor})
            
            # Shuffle and re-key
            correct_key = 'A'
            random.shuffle(options)
            
            for opt in options:
                if opt['value'] == correct_answer:
                    correct_key = opt['key']
                    break
            
            for idx, opt in enumerate(options):
                old_key = opt['key']
                new_key = chr(ord('A') + idx)
                opt['key'] = new_key
                if old_key == correct_key:
                    correct_key = new_key
            
            mcq = {
                'type': 'MCQ',
                'question': question_text,
                'options': options,
                'correct_answer': correct_key,
                'metadata': {
                    'source': 'concept',
                    'concept': concept
                }
            }
            
            if self.validate_question(mcq):
                questions.append(self.set_default_points(mcq, 2.0))
        
        return questions
    
    def _generate_distractors(self, correct_answer: str, num_distractors: int) -> List[str]:
        """
        Generate plausible distractors for an MCQ.
        
        Args:
            correct_answer: The correct answer text
            num_distractors: Number of distractors to generate
            
        Returns:
            List of distractor strings
        """
        distractors = []
        
        # Strategy 1: Modify the correct answer slightly
        words = correct_answer.split()
        
        if len(words) > 3:
            # Remove some words
            distractor = ' '.join(words[:len(words)//2])
            if distractor and distractor != correct_answer:
                distractors.append(distractor)
            
            # Rearrange words
            if len(words) > 5:
                shuffled = words.copy()
                random.shuffle(shuffled)
                distractor = ' '.join(shuffled)
                if distractor != correct_answer:
                    distractors.append(distractor)
        
        # Strategy 2: Generic plausible but wrong answers
        generic_distractors = [
            "A process that occurs naturally",
            "A method used in various applications",
            "A concept related to the subject matter",
            "An approach commonly used in practice",
            "A technique applied in specific situations"
        ]
        
        for generic in generic_distractors:
            if len(distractors) >= num_distractors:
                break
            if generic not in distractors and generic != correct_answer:
                distractors.append(generic)
        
        return distractors[:num_distractors]
    
    def _generate_distractors_from_text(self, text: str, correct_answer: str,
                                       num_distractors: int) -> List[str]:
        """
        Generate distractors by extracting other sentences from the text.
        
        Args:
            text: Source text
            correct_answer: The correct answer
            num_distractors: Number of distractors needed
            
        Returns:
            List of distractor strings
        """
        sentences = self.nlp_processor.tokenize_sentences(text)
        distractors = []
        
        for sentence in sentences:
            if len(distractors) >= num_distractors:
                break
            
            # Use sentences that are different from correct answer
            if sentence.strip() != correct_answer.strip() and len(sentence) > 20:
                distractors.append(sentence.strip())
        
        # If not enough, use generic distractors
        if len(distractors) < num_distractors:
            generic = self._generate_distractors(correct_answer, num_distractors - len(distractors))
            distractors.extend(generic)
        
        return distractors[:num_distractors]
