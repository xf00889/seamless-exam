"""
Identification Generator for creating identification/definition questions.
"""
from typing import List, Dict, Optional
from .base_generator import BaseQuestionGenerator
from processing.utils import NLPProcessor, TextCleaner


class IdentificationGenerator(BaseQuestionGenerator):
    """
    Generator for Identification questions based on definitions and key terms.
    """
    
    def __init__(self, nlp_processor: Optional[NLPProcessor] = None):
        """
        Initialize identification generator.
        
        Args:
            nlp_processor: NLP processor instance (creates new if None)
        """
        self.nlp_processor = nlp_processor or NLPProcessor()
        self.text_cleaner = TextCleaner()
    
    def can_generate(self, text: str) -> bool:
        """
        Determine if identification questions can be generated from text.
        Requires definitions or key terms.
        
        Args:
            text: Input text to analyze
            
        Returns:
            True if identification questions can be generated, False otherwise
        """
        if not text or len(text.strip()) < 20:
            return False
        
        # Check if NLP processor is available
        if not self.nlp_processor.is_available():
            return False
        
        # Check if we can extract definitions or concepts
        definitions = self.nlp_processor.extract_definitions(text)
        concepts = self.nlp_processor.extract_key_concepts(text, max_concepts=3)
        
        return len(definitions) > 0 or len(concepts) > 0
    
    def generate(self, text: str, num_questions: int = 5, **kwargs) -> List[Dict[str, any]]:
        """
        Generate identification questions from text.
        
        Args:
            text: Input text to generate questions from
            num_questions: Maximum number of questions to generate
            **kwargs: Additional parameters
            
        Returns:
            List of identification question dictionaries
        """
        if not self.can_generate(text):
            return []
        
        questions = []
        
        # Clean text
        cleaned_text = self.text_cleaner.clean(text)
        
        # Extract definitions
        definitions = self.nlp_processor.extract_definitions(cleaned_text)
        
        # Create questions from definitions
        for definition in definitions[:num_questions]:
            question = self._create_question_from_definition(
                definition['term'],
                definition['definition']
            )
            
            if question and self.validate_question(question):
                questions.append(self.set_default_points(question, 1.0))
        
        # If we need more questions, create from entities
        if len(questions) < num_questions:
            entity_questions = self._create_questions_from_entities(
                cleaned_text,
                num_questions - len(questions)
            )
            questions.extend(entity_questions)
        
        # If still need more, create from key concepts
        if len(questions) < num_questions:
            concept_questions = self._create_questions_from_concepts(
                cleaned_text,
                num_questions - len(questions)
            )
            questions.extend(concept_questions)
        
        return questions[:num_questions]
    
    def _create_question_from_definition(self, term: str, definition: str) -> Optional[Dict[str, any]]:
        """
        Create an identification question from a term and definition.
        
        Args:
            term: The term to ask about
            definition: The definition of the term
            
        Returns:
            Identification question dictionary or None
        """
        # Create question asking to define the term
        question_text = f"Define {term}."
        
        # The correct answer is the term itself or the definition
        # We'll accept both the term and variations of the definition
        correct_answers = [term.lower(), definition.lower()]
        
        # Also accept just the key words from the definition
        key_words = [word.lower() for word in definition.split() 
                    if len(word) > 4 and word.isalpha()]
        
        return {
            'type': 'IDENTIFICATION',
            'question': question_text,
            'correct_answer': correct_answers,
            'metadata': {
                'source': 'definition',
                'term': term,
                'full_definition': definition,
                'key_words': key_words
            }
        }
    
    def _create_questions_from_entities(self, text: str, num_questions: int) -> List[Dict[str, any]]:
        """
        Create identification questions from named entities.
        
        Args:
            text: Input text
            num_questions: Number of questions to generate
            
        Returns:
            List of identification question dictionaries
        """
        questions = []
        
        # Extract entities
        entities = self.nlp_processor.extract_entities(text)
        
        for entity in entities[:num_questions]:
            entity_text = entity['text']
            entity_label = entity['label']
            
            # Create question based on entity type
            if entity_label == 'PERSON':
                question_text = f"Who is {entity_text}?"
            elif entity_label == 'DATE':
                question_text = f"When did this occur: {entity_text}?"
            elif entity_label == 'GPE':  # Geo-political entity
                question_text = f"Where is {entity_text}?"
            elif entity_label == 'ORG':  # Organization
                question_text = f"What is {entity_text}?"
            else:
                question_text = f"Identify {entity_text}."
            
            # Try to find context for this entity
            sentences = self.nlp_processor.tokenize_sentences(text)
            context = None
            
            for sentence in sentences:
                if entity_text in sentence:
                    context = sentence
                    break
            
            correct_answers = [entity_text.lower()]
            if context:
                correct_answers.append(context.lower())
            
            question = {
                'type': 'IDENTIFICATION',
                'question': question_text,
                'correct_answer': correct_answers,
                'metadata': {
                    'source': 'entity',
                    'entity_type': entity_label,
                    'entity_text': entity_text
                }
            }
            
            if self.validate_question(question):
                questions.append(self.set_default_points(question, 1.0))
        
        return questions
    
    def _create_questions_from_concepts(self, text: str, num_questions: int) -> List[Dict[str, any]]:
        """
        Create identification questions from key concepts.
        
        Args:
            text: Input text
            num_questions: Number of questions to generate
            
        Returns:
            List of identification question dictionaries
        """
        questions = []
        
        # Extract key concepts
        concepts = self.nlp_processor.extract_key_concepts(text, max_concepts=num_questions * 2)
        
        for concept in concepts[:num_questions]:
            # Create "What is X?" question
            question_text = f"What is {concept}?"
            
            # Try to find a sentence that describes this concept
            sentences = self.nlp_processor.tokenize_sentences(text)
            description = None
            
            for sentence in sentences:
                if concept.lower() in sentence.lower():
                    description = sentence
                    break
            
            if not description:
                continue
            
            correct_answers = [concept.lower()]
            if description:
                correct_answers.append(description.lower())
            
            question = {
                'type': 'IDENTIFICATION',
                'question': question_text,
                'correct_answer': correct_answers,
                'metadata': {
                    'source': 'concept',
                    'concept': concept,
                    'description': description
                }
            }
            
            if self.validate_question(question):
                questions.append(self.set_default_points(question, 1.0))
        
        return questions
