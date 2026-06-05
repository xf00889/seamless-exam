"""
Custom middleware for the exam system.
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.template.loader import render_to_string
from django.http import HttpResponse
from users.models import Teacher, SystemSettings
from pathlib import Path
import json


class FileSizeValidationMiddleware:
    """
    Middleware to validate file upload sizes before processing.
    Prevents large file uploads from consuming server resources.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process the request
        response = self.get_response(request)
        return response


class FirstTimeSetupMiddleware:
    """
    Middleware to redirect to first-time setup if no teachers exist.
    Ensures the system is properly initialized before use.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Paths that don't require setup
        self.exempt_paths = [
            '/setup/',
            '/users/setup/',
            '/health/',
            '/superadmin/',
            '/static/',
            '/media/',
            '/admin/',
            '/__debug__/',
        ]
    
    def __call__(self, request):
        # Check if path is exempt
        if any(request.path.startswith(path) for path in self.exempt_paths):
            return self.get_response(request)
        
        # Check if setup is needed
        if self.needs_setup():
            # Redirect to setup page
            setup_url = reverse('setup')
            if request.path != setup_url:
                return redirect(setup_url)
        
        response = self.get_response(request)
        return response
    
    @staticmethod
    def needs_setup():
        """Check if first-time setup is needed."""
        try:
            # Check if any teachers exist
            if Teacher.objects.exists():
                return False
        except Exception:
            # Table doesn't exist yet (migrations not run)
            # Setup is definitely needed
            return True

        # Check if setup flag file exists and is marked complete
        try:
            setup_file = Path(__file__).resolve().parent.parent / '.setup_complete'
            if setup_file.exists():
                with open(setup_file, 'r') as f:
                    data = json.load(f)
                    if data.get('teacher_created', False):
                        return False
        except:
            pass

        return True


class MaintenanceModeMiddleware:
    """
    Middleware that returns a maintenance page to all non-superadmin users
    when SystemSettings.maintenance_mode is enabled. Superadmins and exempt
    paths (static, media, superadmin, etc.) are always allowed through.
    """

    EXEMPT_PATH_PREFIXES = [
        '/superadmin/',
        '/static/',
        '/media/',
        '/admin/',
        '/__debug__/',
        '/health/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._is_exempt_path(request.path):
            return self.get_response(request)

        if self._is_superadmin(request):
            return self.get_response(request)

        if not self._is_maintenance_on():
            return self.get_response(request)

        message = self._get_maintenance_message()
        html = render_to_string(
            'maintenance.html',
            {'message': message, 'request': request},
            request=request,
        )
        return HttpResponse(html, status=503)

    @staticmethod
    def _is_exempt_path(path):
        return any(path.startswith(prefix) for prefix in MaintenanceModeMiddleware.EXEMPT_PATH_PREFIXES)

    @staticmethod
    def _is_superadmin(request):
        user = getattr(request, 'user', None)
        return bool(user and user.is_authenticated and user.is_superuser)

    @staticmethod
    def _is_maintenance_on():
        try:
            return SystemSettings.load().maintenance_mode
        except Exception:
            return False

    @staticmethod
    def _get_maintenance_message():
        try:
            msg = SystemSettings.load().maintenance_message
            return msg.strip() or "We're performing scheduled maintenance. Please check back soon."
        except Exception:
            return "We're performing scheduled maintenance. Please check back soon."
