"""
View helper functions for error handling and UI components.
Provides utilities for converting Result types to HTTP responses and building UI components.
"""
import logging
from typing import Any, List, Dict, Union, Tuple
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.shortcuts import redirect
from services.result import Result
from services.errors import (
    BaseError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    DatabaseError,
    SystemError
)


logger = logging.getLogger('services.views')


def handle_result_json(result: Result, success_status: int = 200) -> JsonResponse:
    """
    Convert a Result to a JSON response.
    
    Args:
        result: Result object from service layer
        success_status: HTTP status code for success (default 200)
        
    Returns:
        JsonResponse with appropriate status code
    """
    if result.is_success():
        # Handle different value types
        value = result.value
        
        if hasattr(value, 'to_dict'):
            # Model with to_dict method
            data = value.to_dict()
        elif isinstance(value, dict):
            # Already a dictionary
            data = value
        elif isinstance(value, (list, tuple)):
            # List of items
            data = {'items': [item.to_dict() if hasattr(item, 'to_dict') else str(item) for item in value]}
        elif isinstance(value, bool):
            # Boolean result
            data = {'success': value}
        else:
            # Other types - convert to string
            data = {'result': str(value)}
        
        return JsonResponse(data, status=success_status)
    else:
        # Handle error
        error = result.error
        
        if isinstance(error, BaseError):
            status_code = get_http_status_for_error(error)
            return JsonResponse(error.to_dict(), status=status_code)
        else:
            # Generic error
            logger.error(f"Unhandled error type: {type(error)}")
            return JsonResponse({
                'error': str(error),
                'code': 'UNKNOWN_ERROR'
            }, status=500)


def handle_result_redirect(
    result: Result,
    request,
    success_url: str,
    error_url: str = None,
    success_message: str = None,
    error_message: str = None
):
    """
    Convert a Result to a redirect with flash messages.
    
    Args:
        result: Result object from service layer
        request: Django request object
        success_url: URL to redirect to on success
        error_url: URL to redirect to on error (defaults to referer or success_url)
        success_message: Message to display on success
        error_message: Message to display on error (defaults to error message)
        
    Returns:
        HttpResponse redirect
    """
    if result.is_success():
        if success_message:
            messages.success(request, success_message)
        return redirect(success_url)
    else:
        error = result.error
        
        # Determine error message
        if error_message:
            msg = error_message
        elif isinstance(error, BaseError):
            msg = error.message
        else:
            msg = str(error)
        
        messages.error(request, msg)
        
        # Determine redirect URL
        if error_url:
            return redirect(error_url)
        else:
            # Try to go back to referer
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(referer)
            else:
                return redirect(success_url)


def get_http_status_for_error(error: BaseError) -> int:
    """
    Map error types to HTTP status codes.
    
    Args:
        error: Error object
        
    Returns:
        HTTP status code
    """
    if isinstance(error, ValidationError):
        return 400  # Bad Request
    elif isinstance(error, AuthenticationError):
        return 401  # Unauthorized
    elif isinstance(error, AuthorizationError):
        return 403  # Forbidden
    elif isinstance(error, NotFoundError):
        return 404  # Not Found
    elif isinstance(error, DatabaseError):
        return 500  # Internal Server Error
    elif isinstance(error, SystemError):
        return 500  # Internal Server Error
    else:
        return 500  # Default to Internal Server Error


def log_error(error: Any, context: str = ""):
    """
    Log an error with appropriate level and context.
    
    Args:
        error: Error object or exception
        context: Additional context about where the error occurred
    """
    if isinstance(error, BaseError):
        if isinstance(error, (ValidationError, NotFoundError)):
            # User errors - log as warning
            logger.warning(f"{context}: {error}")
        else:
            # System errors - log as error
            logger.error(f"{context}: {error}", extra={'details': error.details})
    else:
        # Unknown error - log as error
        logger.error(f"{context}: {error}", exc_info=True)


def extract_validation_errors(error: BaseError) -> dict:
    """
    Extract field-level validation errors from an error object.
    
    Args:
        error: Error object
        
    Returns:
        Dictionary mapping field names to error messages
    """
    if not isinstance(error, ValidationError):
        return {}
    
    if error.details and 'field' in error.details:
        return {error.details['field']: error.message}
    
    return {}


def build_breadcrumbs(*items: Union[Tuple[str, str], str]) -> List[Dict[str, str]]:
    """
    Helper function to build breadcrumb list for navigation components.
    
    This function simplifies the creation of breadcrumb navigation data by accepting
    variable arguments of either tuples (label, url) for clickable links or plain
    strings for the current page (non-clickable).
    
    Args:
        *items: Variable arguments where each item is either:
            - A tuple of (label, url) for clickable breadcrumb links
            - A string label for the current page (non-clickable)
    
    Returns:
        List of breadcrumb dictionaries with 'label' and optional 'url' keys.
        Each dictionary has the structure:
        - {'label': str, 'url': str} for clickable items
        - {'label': str} for the current page
    
    Examples:
        >>> # Simple breadcrumb trail
        >>> breadcrumbs = build_breadcrumbs(
        ...     ('Home', '/'),
        ...     ('Exams', '/exams/'),
        ...     'Create Exam'
        ... )
        >>> # Result: [
        >>> #     {'label': 'Home', 'url': '/'},
        >>> #     {'label': 'Exams', 'url': '/exams/'},
        >>> #     {'label': 'Create Exam'}
        >>> # ]
        
        >>> # Using Django reverse for URLs
        >>> from django.urls import reverse
        >>> breadcrumbs = build_breadcrumbs(
        ...     ('Home', reverse('teacher_dashboard')),
        ...     ('Exams', reverse('exam_list')),
        ...     ('Physics Exam', reverse('exam_detail', args=[exam_id])),
        ...     'Edit'
        ... )
        
        >>> # Single item (just current page)
        >>> breadcrumbs = build_breadcrumbs('Dashboard')
        >>> # Result: [{'label': 'Dashboard'}]
        
        >>> # All clickable items (no current page)
        >>> breadcrumbs = build_breadcrumbs(
        ...     ('Home', '/'),
        ...     ('Settings', '/settings/')
        ... )
    
    Usage in Views:
        def exam_edit_view(request, exam_id):
            exam = get_object_or_404(Exam, id=exam_id)
            
            breadcrumbs = build_breadcrumbs(
                ('Home', reverse('teacher_dashboard')),
                ('Exams', reverse('exam_list')),
                (exam.title, reverse('exam_detail', args=[exam_id])),
                'Edit'
            )
            
            return render(request, 'exams/exam_edit.html', {
                'exam': exam,
                'breadcrumbs': breadcrumbs
            })
    
    Usage in Templates:
        {% include 'components/breadcrumb.html' with breadcrumbs=breadcrumbs %}
    """
    breadcrumbs = []
    
    for item in items:
        if isinstance(item, tuple):
            # Tuple format: (label, url)
            if len(item) == 2:
                label, url = item
                breadcrumbs.append({'label': label, 'url': url})
            else:
                # Invalid tuple length - log warning and skip
                logger.warning(f"Invalid breadcrumb tuple: {item}. Expected (label, url).")
        elif isinstance(item, str):
            # String format: just the label (current page, no URL)
            breadcrumbs.append({'label': item})
        else:
            # Invalid type - log warning and skip
            logger.warning(f"Invalid breadcrumb item type: {type(item)}. Expected tuple or string.")
    
    return breadcrumbs
