"""
Service for managing exam metadata.

This module provides functions for managing exam metadata and information.
"""
import logging
from typing import Dict, Any

from exams.models import Exam


logger = logging.getLogger('services.exam_metadata')


def get_exam_basic_info(exam: Exam) -> Dict[str, Any]:
    """
    Retrieve basic information from an exam.
    
    Args:
        exam: The Exam instance to query
    
    Returns:
        Dictionary containing basic exam information
    """
    return {
        'id': exam.id,
        'title': exam.title,
        'subject': exam.subject,
        'created_at': exam.created_at,
        'updated_at': exam.updated_at,
        'is_active': exam.is_active,
        'teacher': exam.created_by.user.username if exam.created_by else None,
    }
