# Question Extraction Utilities

This module provides utilities for extracting and structuring questions from document text.

## Components

### 1. PatternMatcher

Detects patterns in text that indicate questions, choices, numbering, and question types.

**Features:**
- Numbered pattern detection (1., 2., etc.)
- Choice pattern detection (A., B., C., etc.)
- Question mark detection
- Keyword-based question type classification

**Usage:**
```python
from processing.utils import PatternMatcher, QuestionType

matcher = PatternMatcher()

# Detect numbered items
text = "1. What is Python?\n2. What is Django?"
items = matcher.detect_numbered_items(text)

# Detect choices
choices_text = "A. Option 1\nB. Option 2"
choices = matcher.detect_choice_items(choices_text)

# Classify question type
question = "Define object-oriented programming."
q_type = matcher.classify_question_type(question)  # Returns QuestionType.IDENTIFICATION

# Check for question mark
has_qmark = matcher.has_question_mark("What is Python?")  # Returns True
```

**Question Types:**
- `MCQ`: Multiple Choice Question
- `IDENTIFICATION`: Short answer questions (Define, What is, etc.)
- `ENUMERATION`: List-based questions (Enumerate, List, etc.)
- `ESSAY`: Long-form questions (Explain, Discuss, etc.)
- `TRUE_FALSE`: True/False questions
- `UNKNOWN`: Cannot determine type

### 2. MCQBuilder

Builds and validates structured MCQ questions from components.

**Features:**
- Build MCQ from question text and choices
- Extract MCQ structure from text blocks
- Validate MCQ completeness
- Add/update correct answers
- Reorder choices

**Usage:**
```python
from processing.utils import MCQBuilder

builder = MCQBuilder()

# Build MCQ from components
question = "What is the capital of France?"
choices = [
    {'key': 'A', 'value': 'London'},
    {'key': 'B', 'value': 'Paris'},
    {'key': 'C', 'value': 'Berlin'}
]
mcq = builder.build_mcq(question, choices, correct_answer='B')

# Extract from text
text = """What is 2 + 2?
A. 3
B. 4
C. 5"""
mcq = builder.extract_mcq_from_text(text)

# Validate MCQ
is_valid = builder.validate_mcq(mcq)

# Add correct answer
mcq = builder.add_correct_answer(mcq, 'B')
```

**MCQ Structure:**
```python
{
    'type': 'MCQ',
    'question': 'Question text',
    'options': [
        {'key': 'A', 'value': 'Option 1'},
        {'key': 'B', 'value': 'Option 2'},
        {'key': 'C', 'value': 'Option 3'}
    ],
    'correct_answer': 'B'  # Optional
}
```

### 3. ListDetector

Detects and extracts list/enumeration patterns from text.

**Features:**
- Numbered list detection (1., 2., 3., etc.)
- Bulleted list detection (-, *, •)
- Lettered list detection (a., b., c., etc.)
- Automatic list type detection
- Extract list items
- Split text into header and list items

**Usage:**
```python
from processing.utils import ListDetector

detector = ListDetector()

# Detect numbered list
text = "1. First item\n2. Second item\n3. Third item"
numbered = detector.detect_numbered_list(text)

# Detect any list type
detected = detector.detect_any_list(text)
# Returns: {'type': 'numbered', 'items': [...]}

# Extract just the items
items = detector.extract_list_items(text)
# Returns: ['First item', 'Second item', 'Third item']

# Check if text is an enumeration
is_enum = detector.is_enumeration_answer(text, min_items=2)

# Split text into header and items
header, items = detector.split_by_list("List features:\n1. Feature 1\n2. Feature 2")
# Returns: ('List features:', ['Feature 1', 'Feature 2'])
```

### 4. TextCleaner

Cleans extracted text by removing formatting artifacts.

**Features:**
- Remove control characters
- Remove page numbers
- Remove header/footer separators
- Normalize whitespace
- Remove excessive newlines

**Usage:**
```python
from processing.utils import TextCleaner

cleaner = TextCleaner()

raw_text = "  Some   text   with    extra    spaces  "
cleaned = cleaner.clean(raw_text)
# Returns: "Some text with extra spaces"
```

### 5. NLPProcessor

Wrapper for spaCy/NLTK natural language processing operations.

### 6. FuzzyMatcher

Wrapper for RapidFuzz approximate string matching operations.

## Integration Example

```python
from processing.utils import PatternMatcher, MCQBuilder, ListDetector

# Initialize utilities
matcher = PatternMatcher()
mcq_builder = MCQBuilder()
list_detector = ListDetector()

# Sample document text
document = """
1. What is Django?
A. A Python web framework
B. A database system
C. A programming language

2. Enumerate three advantages of Django.

3. Explain the MVC pattern.
"""

# Extract numbered questions
questions = matcher.detect_numbered_items(document)

for q in questions:
    # Classify question type
    q_type = matcher.classify_question_type(q['text'])
    
    if q_type == QuestionType.MCQ:
        # Extract MCQ structure
        remaining_text = document[q['end']:]
        choices = matcher.detect_choice_items(remaining_text)
        if choices:
            mcq = mcq_builder.build_mcq(q['text'], choices)
            # Process MCQ...
    
    elif q_type == QuestionType.ENUMERATION:
        # This is an enumeration question
        # Could look for list patterns in answer section
        pass
    
    elif q_type == QuestionType.ESSAY:
        # This is an essay question
        pass
```

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 4.1**: Numbered pattern detection (1., 2., etc.) ✓
- **Requirement 4.2**: Choice pattern detection (A., B., C., etc.) ✓
- **Requirement 4.3**: Keyword-based classification (Define, Enumerate, Explain) ✓
- **Requirement 4.4**: Question mark detection ✓
- **Requirement 20.2**: MCQBuilder for structuring MCQ questions ✓
- **Requirement 20.3**: ListDetector for enumeration patterns ✓

## Testing

Run the demonstration to see all features in action:

```bash
python demo_question_extraction.py
```

This will show examples of:
- Pattern detection
- MCQ building
- List detection
- Integrated workflow
