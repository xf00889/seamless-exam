"""
Audit logging service for system operations.

This module provides structured audit logging for tracking system
activities and operations.
"""
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime


logger = logging.getLogger('services.audit')


class AuditLogger:
    """
    Centralized audit logging for system operations.
    
    This class provides structured logging methods for system activities.
    """
    
    @staticmethod
    def log_database_operation(
        operation: str,
        entity_type: str,
        entity_id: int,
        success: bool,
        error: Optional[Exception] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ):
        """
        Log database operations.
        
        Args:
            operation: Type of operation (create, update, delete)
            entity_type: Type of entity (exam, question, etc.)
            entity_id: ID of the entity
            success: Whether operation succeeded
            error: Optional exception if operation failed
            additional_context: Additional context information
        """
        log_data = {
            'event': 'database_operation',
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'success': success,
        }
        
        if additional_context:
            log_data['additional_context'] = additional_context
        
        if error:
            log_data['error'] = {
                'message': str(error),
                'exception_class': error.__class__.__name__,
            }
        
        if success:
            logger.info(
                f"Database operation completed: {json.dumps(log_data)}"
            )
        else:
            logger.error(
                f"Database operation failed: {json.dumps(log_data)}",
                exc_info=True
            )
