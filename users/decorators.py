"""
Authentication and authorization decorators for views.
Provides reusable decorators for securing views with authentication and authorization checks.
Requirements: 13.4
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from services.auth_service import AuthenticationService


def student_required(view_func):
    """
    Decorator to require student authentication for a view.
    
    Checks if the user is authenticated as a student.
    Redirects to login page if not authenticated.
    Returns JSON error for AJAX requests.
    
    Requirements: 13.4
    
    Usage:
        @student_required
        def my_view(request):
            # View code here
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_service = AuthenticationService()
        
        # Check if user is authenticated as student
        if not auth_service.require_student(request):
            # Handle AJAX requests differently
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Authentication required',
                    'redirect': '/users/student/login/'
                }, status=401)
            
            # Regular request - redirect to login
            messages.error(request, 'Please log in to access this page')
            return redirect('student_login')
        
        # User is authenticated, proceed with view
        return view_func(request, *args, **kwargs)
    
    return wrapper


def teacher_required(view_func):
    """
    Decorator to require teacher authentication for a view.
    
    Checks if the user is authenticated as a teacher.
    Redirects to login page if not authenticated.
    Returns JSON error for AJAX requests.
    
    Requirements: 13.4
    
    Usage:
        @teacher_required
        def my_view(request):
            # View code here
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_service = AuthenticationService()
        
        # Check if user is authenticated as teacher
        if not auth_service.require_teacher(request):
            # Handle AJAX requests differently
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Authentication required',
                    'redirect': '/users/teacher/login/'
                }, status=401)
            
            # Regular request - redirect to login
            messages.error(request, 'Please log in to access this page')
            return redirect('teacher_login')
        
        # User is authenticated, proceed with view
        return view_func(request, *args, **kwargs)
    
    return wrapper


def student_owns_resource(resource_id_param='student_id'):
    """
    Decorator to ensure a student can only access their own resources.
    
    Checks that the authenticated student's ID matches the resource owner ID.
    Prevents students from accessing other students' data.
    
    Requirements: 13.4
    
    Args:
        resource_id_param: Name of the parameter containing the student ID to check
                          Can be a URL parameter or request parameter
    
    Usage:
        @student_required
        @student_owns_resource('student_id')
        def my_view(request, student_id):
            # View code here - student_id is guaranteed to match authenticated student
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            auth_service = AuthenticationService()
            
            # Get the authenticated student
            student = auth_service.get_current_student(request)
            if not student:
                # Should not happen if student_required is used first
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Authentication required'
                    }, status=401)
                messages.error(request, 'Authentication required')
                return redirect('student_login')
            
            # Get the resource owner ID from URL parameters or kwargs
            resource_owner_id = kwargs.get(resource_id_param)
            
            # If not in kwargs, try to get from request parameters
            if resource_owner_id is None:
                resource_owner_id = request.GET.get(resource_id_param) or request.POST.get(resource_id_param)
            
            # Convert to int if it's a string
            if resource_owner_id is not None:
                try:
                    resource_owner_id = int(resource_owner_id)
                except (ValueError, TypeError):
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': 'Invalid resource ID'
                        }, status=400)
                    messages.error(request, 'Invalid resource ID')
                    return redirect('student_profile')
            
            # Check authorization - student can only access their own resources
            if resource_owner_id is not None and student.id != resource_owner_id:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'You are not authorized to access this resource'
                    }, status=403)
                messages.error(request, 'You are not authorized to access this resource')
                return redirect('student_profile')
            
            # Authorization passed, proceed with view
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator
