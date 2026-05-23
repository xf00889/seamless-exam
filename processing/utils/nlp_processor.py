"""
NLP processing wrapper for spaCy and NLTK operations.
"""
from typing import List, Set, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class NLPProcessor:
    """
    Wrapper class for NLP operations using spaCy and NLTK.
    Provides text analysis, entity extraction, and concept identification.
    """
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize NLP processor with spaCy model.
        
        Args:
            model_name: Name of spaCy model to load
        """
        self.nlp = None
        self.model_name = model_name
        self._initialize_spacy()
        self._initialize_nltk()
    
    def _initialize_spacy(self):
        """Initialize spaCy model."""
        try:
            import spacy
            try:
                self.nlp = spacy.load(self.model_name)
            except OSError:
                logger.warning(f"spaCy model '{self.model_name}' not found. NLP features will be limited.")
                self.nlp = None
        except ImportError:
            logger.warning("spaCy not installed. NLP features will be limited.")
            self.nlp = None
    
    def _initialize_nltk(self):
        """Initialize NLTK resources."""
        try:
            import nltk
            # Try to use punkt tokenizer
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                logger.warning("NLTK punkt tokenizer not found. Some features may be limited.")
        except ImportError:
            logger.warning("NLTK not installed. Some features will be limited.")
    
    def extract_key_concepts(self, text: str, max_concepts: int = 10) -> List[str]:
        """
        Extract key concepts from text using NLP.
        
        Args:
            text: Input text
            max_concepts: Maximum number of concepts to extract
            
        Returns:
            List of key concepts (nouns and noun phrases)
        """
        if not self.nlp or not text:
            return []
        
        doc = self.nlp(text)
        concepts = []
        
        # Extract noun chunks (noun phrases)
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 3:  # Limit to 3-word phrases
                concepts.append(chunk.text.lower())
        
        # Extract important nouns
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop:
                concepts.append(token.text.lower())
        
        # Remove duplicates and limit
        concepts = list(dict.fromkeys(concepts))  # Preserve order
        return concepts[:max_concepts]
    
    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """
        Extract named entities from text.
        
        Args:
            text: Input text
            
        Returns:
            List of dictionaries with 'text' and 'label' keys
        """
        if not self.nlp or not text:
            return []
        
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_
            })
        
        return entities
    
    def tokenize_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        if self.nlp:
            doc = self.nlp(text)
            return [sent.text.strip() for sent in doc.sents]
        else:
            # Fallback to simple splitting
            try:
                from nltk.tokenize import sent_tokenize
                return sent_tokenize(text)
            except:
                # Simple fallback
                import re
                sentences = re.split(r'[.!?]+', text)
                return [s.strip() for s in sentences if s.strip()]
    
    def tokenize_words(self, text: str) -> List[str]:
        """
        Split text into words/tokens.
        
        Args:
            text: Input text
            
        Returns:
            List of words
        """
        if self.nlp:
            doc = self.nlp(text)
            return [token.text for token in doc if not token.is_space]
        else:
            # Fallback to simple splitting
            try:
                from nltk.tokenize import word_tokenize
                return word_tokenize(text)
            except:
                # Simple fallback
                return text.split()
    
    def extract_definitions(self, text: str) -> List[Dict[str, str]]:
        """
        Extract potential definitions from text.
        Looks for patterns like "X is Y" or "X: Y".
        
        Args:
            text: Input text
            
        Returns:
            List of dictionaries with 'term' and 'definition' keys
        """
        definitions = []
        
        # Pattern: "Term is definition"
        import re
        is_pattern = re.compile(r'([A-Z][a-zA-Z\s]+)\s+is\s+([^.!?]+[.!?])')
        
        for match in is_pattern.finditer(text):
            definitions.append({
                'term': match.group(1).strip(),
                'definition': match.group(2).strip()
            })
        
        # Pattern: "Term: definition"
        colon_pattern = re.compile(r'([A-Z][a-zA-Z\s]+):\s+([^.!?]+[.!?])')
        
        for match in colon_pattern.finditer(text):
            definitions.append({
                'term': match.group(1).strip(),
                'definition': match.group(2).strip()
            })
        
        return definitions
    
    def get_pos_tags(self, text: str) -> List[tuple]:
        """
        Get part-of-speech tags for text.
        
        Args:
            text: Input text
            
        Returns:
            List of (word, pos_tag) tuples
        """
        if self.nlp:
            doc = self.nlp(text)
            return [(token.text, token.pos_) for token in doc]
        else:
            try:
                from nltk import pos_tag, word_tokenize
                tokens = word_tokenize(text)
                return pos_tag(tokens)
            except:
                return []
    
    def is_available(self) -> bool:
        """
        Check if NLP processor is available and functional.
        
        Returns:
            True if NLP features are available, False otherwise
        """
        return self.nlp is not None
