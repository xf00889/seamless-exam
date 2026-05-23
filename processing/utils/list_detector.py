"""
List Detector utility for identifying enumeration patterns in text.
"""
import re
from typing import List, Dict, Optional, Tuple


class ListDetector:
    """
    Utility class for detecting and extracting list/enumeration patterns from text.
    """
    
    def __init__(self):
        """Initialize list detector with patterns."""
        # Numbered list patterns (1., 2., 1), 2), etc.)
        self.numbered_list_pattern = re.compile(r'^\s*(\d+)[.)]\s+(.+)', re.MULTILINE)
        
        # Bulleted list patterns (-, *, •)
        self.bullet_pattern = re.compile(r'^\s*[-*•]\s+(.+)', re.MULTILINE)
        
        # Lettered list patterns (a., b., a), b), etc.)
        self.lettered_list_pattern = re.compile(r'^\s*([a-z])[.)]\s+(.+)', re.MULTILINE | re.IGNORECASE)
        
        # Roman numeral patterns (i., ii., iii., etc.)
        self.roman_pattern = re.compile(r'^\s*([ivxlcdm]+)[.)]\s+(.+)', re.MULTILINE | re.IGNORECASE)
    
    def detect_numbered_list(self, text: str) -> Optional[List[Dict[str, any]]]:
        """
        Detect numbered list items in text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of dictionaries with 'number' and 'text' keys, or None if no list found
        """
        matches = list(self.numbered_list_pattern.finditer(text))
        
        if not matches:
            return None
        
        items = []
        for match in matches:
            items.append({
                'number': int(match.group(1)),
                'text': match.group(2).strip(),
                'start': match.start(),
                'end': match.end()
            })
        
        # Validate it's a proper sequence
        if self._is_valid_sequence(items):
            return items
        
        return None
    
    def detect_bulleted_list(self, text: str) -> Optional[List[Dict[str, any]]]:
        """
        Detect bulleted list items in text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of dictionaries with 'text' key, or None if no list found
        """
        matches = list(self.bullet_pattern.finditer(text))
        
        if len(matches) < 2:  # Need at least 2 items to be a list
            return None
        
        items = []
        for idx, match in enumerate(matches):
            items.append({
                'index': idx + 1,
                'text': match.group(1).strip(),
                'start': match.start(),
                'end': match.end()
            })
        
        return items
    
    def detect_lettered_list(self, text: str) -> Optional[List[Dict[str, any]]]:
        """
        Detect lettered list items in text (a., b., c., etc.).
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of dictionaries with 'letter' and 'text' keys, or None if no list found
        """
        matches = list(self.lettered_list_pattern.finditer(text))
        
        if not matches:
            return None
        
        items = []
        for match in matches:
            items.append({
                'letter': match.group(1).lower(),
                'text': match.group(2).strip(),
                'start': match.start(),
                'end': match.end()
            })
        
        # Validate it's a proper alphabetical sequence
        if self._is_valid_letter_sequence(items):
            return items
        
        return None
    
    def detect_any_list(self, text: str) -> Optional[Dict[str, any]]:
        """
        Detect any type of list in text and return the most likely one.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with 'type' and 'items' keys, or None if no list found
        """
        # Try numbered list first (most common for enumerations)
        numbered = self.detect_numbered_list(text)
        if numbered:
            return {
                'type': 'numbered',
                'items': numbered
            }
        
        # Try lettered list
        lettered = self.detect_lettered_list(text)
        if lettered:
            return {
                'type': 'lettered',
                'items': lettered
            }
        
        # Try bulleted list
        bulleted = self.detect_bulleted_list(text)
        if bulleted:
            return {
                'type': 'bulleted',
                'items': bulleted
            }
        
        return None
    
    def extract_list_items(self, text: str) -> List[str]:
        """
        Extract just the text content of list items, regardless of list type.
        
        Args:
            text: Input text containing a list
            
        Returns:
            List of item texts
        """
        detected = self.detect_any_list(text)
        
        if not detected:
            return []
        
        items = detected['items']
        return [item['text'] for item in items]
    
    def is_enumeration_answer(self, text: str, min_items: int = 2) -> bool:
        """
        Determine if text contains an enumeration-style answer.
        
        Args:
            text: Input text
            min_items: Minimum number of items to consider it an enumeration
            
        Returns:
            True if text contains enumeration, False otherwise
        """
        detected = self.detect_any_list(text)
        
        if not detected:
            return False
        
        return len(detected['items']) >= min_items
    
    def count_list_items(self, text: str) -> int:
        """
        Count the number of items in a detected list.
        
        Args:
            text: Input text
            
        Returns:
            Number of list items, or 0 if no list detected
        """
        detected = self.detect_any_list(text)
        
        if not detected:
            return 0
        
        return len(detected['items'])
    
    def _is_valid_sequence(self, items: List[Dict[str, any]]) -> bool:
        """
        Check if numbered items form a valid sequence (1, 2, 3, ...).
        
        Args:
            items: List of items with 'number' key
            
        Returns:
            True if valid sequence, False otherwise
        """
        if not items:
            return False
        
        # Check if numbers are sequential starting from 1
        expected = 1
        for item in items:
            if item['number'] != expected:
                # Allow some flexibility - might not start at 1
                if expected == 1 and item['number'] > 1:
                    expected = item['number']
                else:
                    return False
            expected += 1
        
        return True
    
    def _is_valid_letter_sequence(self, items: List[Dict[str, any]]) -> bool:
        """
        Check if lettered items form a valid sequence (a, b, c, ...).
        
        Args:
            items: List of items with 'letter' key
            
        Returns:
            True if valid sequence, False otherwise
        """
        if not items:
            return False
        
        # Check if letters are sequential
        expected_ord = ord(items[0]['letter'])
        for item in items:
            if ord(item['letter']) != expected_ord:
                return False
            expected_ord += 1
        
        return True
    
    def split_by_list(self, text: str) -> Tuple[Optional[str], Optional[List[str]]]:
        """
        Split text into a header/question part and list items.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (header_text, list_items) or (None, None) if no list found
        """
        detected = self.detect_any_list(text)
        
        if not detected:
            return None, None
        
        items = detected['items']
        
        if not items:
            return None, None
        
        # Get the position of the first list item
        first_item_start = items[0]['start']
        
        # Extract header (text before first list item)
        header = text[:first_item_start].strip()
        
        # Extract list items
        list_items = [item['text'] for item in items]
        
        return header if header else None, list_items
