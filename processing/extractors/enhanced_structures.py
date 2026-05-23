"""
Data structures for enhanced DOCX extraction with structure preservation.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class ParagraphType(Enum):
    """Types of paragraphs in a document."""
    NORMAL = "normal"
    HEADING = "heading"
    LIST_ITEM = "list_item"
    TABLE_CELL = "table_cell"


@dataclass
class StyledParagraph:
    """
    Represents a paragraph with style and structure information.
    """
    text: str
    style_name: str = "Normal"
    is_heading: bool = False
    is_list_item: bool = False
    indentation_level: int = 0
    has_numbering: bool = False
    numbering_format: Optional[str] = None
    paragraph_type: ParagraphType = ParagraphType.NORMAL
    line_number: int = 0
    
    # Additional formatting information
    is_bold: bool = False
    is_italic: bool = False
    has_special_chars: bool = False


@dataclass
class TableCell:
    """Represents a cell in a table."""
    text: str
    row_index: int
    col_index: int


@dataclass
class Table:
    """Represents a table with cells."""
    cells: List[TableCell] = field(default_factory=list)
    num_rows: int = 0
    num_cols: int = 0
    
    def get_cell(self, row: int, col: int) -> Optional[TableCell]:
        """Get a specific cell by row and column."""
        for cell in self.cells:
            if cell.row_index == row and cell.col_index == col:
                return cell
        return None
    
    def get_row(self, row: int) -> List[TableCell]:
        """Get all cells in a specific row."""
        return [cell for cell in self.cells if cell.row_index == row]


@dataclass
class Section:
    """Represents a document section."""
    header: str
    start_line: int
    end_line: Optional[int] = None
    paragraphs: List[StyledParagraph] = field(default_factory=list)


@dataclass
class StructuredDocument:
    """
    Represents a complete document with structure preserved.
    """
    paragraphs: List[StyledParagraph] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    sections: List[Section] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_text(self) -> str:
        """Get plain text representation of the document."""
        return '\n'.join(p.text for p in self.paragraphs if p.text.strip())
    
    def get_headings(self) -> List[StyledParagraph]:
        """Get all heading paragraphs."""
        return [p for p in self.paragraphs if p.is_heading]
    
    def get_list_items(self) -> List[StyledParagraph]:
        """Get all list item paragraphs."""
        return [p for p in self.paragraphs if p.is_list_item]
