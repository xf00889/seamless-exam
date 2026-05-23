"""
Public view for teacher access requests.
"""

from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from .models import AdminNotification


class RequestAccessView(View):
    def get(self, request):
        return render(request, 'users/request_access.html')

    def post(self, request):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()

        errors = []
        if not name or len(name) < 2:
            errors.append('Name is required (at least 2 characters).')
        if not message or len(message) < 10:
            errors.append('Please provide a message (at least 10 characters).')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'users/request_access.html', {
                'name': name,
                'email': email,
                'message_text': message,
            })

        AdminNotification.objects.create(
            name=name,
            email=email,
            message=message,
        )
        messages.success(request, 'Your request has been sent to the administrator.')
        return redirect('teacher_login')
