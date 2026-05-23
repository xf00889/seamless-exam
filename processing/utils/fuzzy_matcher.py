"""
Fuzzy matching wrapper for RapidFuzz operations.
"""
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class FuzzyMatcher:
    """
    Wrapper class for fuzzy string matching using RapidFuzz.
    Provides approximate string comparison for answer validation.
    """
    
    def __init__(self, default_threshold: int = 80):
        """
        Initialize fuzzy matcher.
        
        Args:
            default_threshold: Default similarity threshold (0-100)
        """
        self.default_threshold = default_threshold
        self._initialize_rapidfuzz()
    
    def _initialize_rapidfuzz(self):
        """Initialize RapidFuzz library."""
        try:
            from rapidfuzz import fuzz, process
            self.fuzz = fuzz
            self.process = process
            self.available = True
        except ImportError:
            logger.warning("RapidFuzz not installed. Fuzzy matching will use exact matching.")
            self.fuzz = None
            self.process = None
            self.available = False
    
    def similarity_ratio(self, str1: str, str2: str, case_sensitive: bool = False) -> float:
        """
        Calculate similarity ratio between two strings.
        
        Args:
            str1: First string
            str2: Second string
            case_sensitive: Whether to consider case
            
        Returns:
            Similarity ratio (0-100)
        """
        if not str1 or not str2:
            return 0.0
        
        if not case_sensitive:
            str1 = str1.lower()
            str2 = str2.lower()
        
        if self.available:
            return self.fuzz.ratio(str1, str2)
        else:
            # Fallback to exact matching
            return 100.0 if str1 == str2 else 0.0
    
    def partial_ratio(self, str1: str, str2: str, case_sensitive: bool = False) -> float:
        """
        Calculate partial similarity ratio (best matching substring).
        
        Args:
            str1: First string
            str2: Second string
            case_sensitive: Whether to consider case
            
        Returns:
            Partial similarity ratio (0-100)
        """
        if not str1 or not str2:
            return 0.0
        
        if not case_sensitive:
            str1 = str1.lower()
            str2 = str2.lower()
        
        if self.available:
            return self.fuzz.partial_ratio(str1, str2)
        else:
            # Fallback to substring check
            return 100.0 if str1 in str2 or str2 in str1 else 0.0
    
    def token_sort_ratio(self, str1: str, str2: str, case_sensitive: bool = False) -> float:
        """
        Calculate similarity ratio with token sorting (order-independent).
        
        Args:
            str1: First string
            str2: Second string
            case_sensitive: Whether to consider case
            
        Returns:
            Token sort similarity ratio (0-100)
        """
        if not str1 or not str2:
            return 0.0
        
        if not case_sensitive:
            str1 = str1.lower()
            str2 = str2.lower()
        
        if self.available:
            return self.fuzz.token_sort_ratio(str1, str2)
        else:
            # Fallback to exact matching
            return 100.0 if str1 == str2 else 0.0
    
    def is_match(self, str1: str, str2: str, threshold: Optional[int] = None, 
                 case_sensitive: bool = False) -> bool:
        """
        Check if two strings match within threshold.
        
        Args:
            str1: First string
            str2: Second string
            threshold: Similarity threshold (0-100), uses default if None
            case_sensitive: Whether to consider case
            
        Returns:
            True if strings match within threshold, False otherwise
        """
        if threshold is None:
            threshold = self.default_threshold
        
        ratio = self.similarity_ratio(str1, str2, case_sensitive)
        return ratio >= threshold
    
    def find_best_match(self, query: str, choices: List[str], 
                       threshold: Optional[int] = None,
                       case_sensitive: bool = False) -> Optional[Tuple[str, float]]:
        """
        Find the best matching string from a list of choices.
        
        Args:
            query: Query string
            choices: List of strings to match against
            threshold: Minimum similarity threshold
            case_sensitive: Whether to consider case
            
        Returns:
            Tuple of (best_match, score) or None if no match above threshold
        """
        if not query or not choices:
            return None
        
        if threshold is None:
            threshold = self.default_threshold
        
        if self.available:
            # Use RapidFuzz process.extractOne
            result = self.process.extractOne(
                query if case_sensitive else query.lower(),
                [c if case_sensitive else c.lower() for c in choices],
                scorer=self.fuzz.ratio
            )
            
            if result and result[1] >= threshold:
                # Return original choice (not lowercased)
                original_idx = [c if case_sensitive else c.lower() for c in choices].index(result[0])
                return (choices[original_idx], result[1])
            return None
        else:
            # Fallback to exact matching
            query_cmp = query if case_sensitive else query.lower()
            for choice in choices:
                choice_cmp = choice if case_sensitive else choice.lower()
                if query_cmp == choice_cmp:
                    return (choice, 100.0)
            return None
    
    def find_all_matches(self, query: str, choices: List[str],
                        threshold: Optional[int] = None,
                        case_sensitive: bool = False,
                        limit: Optional[int] = None) -> List[Tuple[str, float]]:
        """
        Find all matching strings from a list of choices above threshold.
        
        Args:
            query: Query string
            choices: List of strings to match against
            threshold: Minimum similarity threshold
            case_sensitive: Whether to consider case
            limit: Maximum number of matches to return
            
        Returns:
            List of (match, score) tuples sorted by score descending
        """
        if not query or not choices:
            return []
        
        if threshold is None:
            threshold = self.default_threshold
        
        if self.available:
            results = self.process.extract(
                query if case_sensitive else query.lower(),
                [c if case_sensitive else c.lower() for c in choices],
                scorer=self.fuzz.ratio,
                limit=limit
            )
            
            # Filter by threshold and return original choices
            matches = []
            for result in results:
                if result[1] >= threshold:
                    original_idx = [c if case_sensitive else c.lower() for c in choices].index(result[0])
                    matches.append((choices[original_idx], result[1]))
            
            return matches
        else:
            # Fallback to exact matching
            query_cmp = query if case_sensitive else query.lower()
            matches = []
            for choice in choices:
                choice_cmp = choice if case_sensitive else choice.lower()
                if query_cmp == choice_cmp:
                    matches.append((choice, 100.0))
            
            return matches[:limit] if limit else matches
    
    def match_any(self, query: str, choices: List[str],
                  threshold: Optional[int] = None,
                  case_sensitive: bool = False) -> bool:
        """
        Check if query matches any of the choices.
        
        Args:
            query: Query string
            choices: List of strings to match against
            threshold: Minimum similarity threshold
            case_sensitive: Whether to consider case
            
        Returns:
            True if query matches any choice, False otherwise
        """
        return self.find_best_match(query, choices, threshold, case_sensitive) is not None
    
    def is_available(self) -> bool:
        """
        Check if fuzzy matching is available.
        
        Returns:
            True if RapidFuzz is available, False otherwise
        """
        return self.available
