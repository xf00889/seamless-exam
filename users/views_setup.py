"""
First-time setup views for creating the initial superadmin account.
"""

from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from pathlib import Path
import json


class FirstTimeSetupView(View):
    """
    View for first-time setup - creates the initial superadmin account.
    Only accessible when no superuser exists in the system.
    """

    def get(self, request):
        """Display the setup form."""
        if self.is_setup_complete():
            return redirect('home')

        return render(request, 'users/first_time_setup.html', {
            'page_title': 'First Time Setup - Create Admin Account'
        })

    def post(self, request):
        """Process the setup form and create superadmin account."""
        if self.is_setup_complete():
            messages.error(request, 'Setup has already been completed.')
            return redirect('home')

        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        errors = []

        if not username:
            errors.append('Username is required.')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already exists.')

        if not first_name:
            errors.append('First name is required.')

        if not last_name:
            errors.append('Last name is required.')

        if not password:
            errors.append('Password is required.')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters.')

        if password != password_confirm:
            errors.append('Passwords do not match.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'users/first_time_setup.html', {
                'page_title': 'First Time Setup - Create Admin Account',
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
            })

        try:
            with transaction.atomic():
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
                self.mark_setup_complete()

                messages.success(
                    request,
                    f'Superadmin account created successfully! Welcome, {first_name}!'
                )

                return redirect('superadmin_login')

        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'users/first_time_setup.html', {
                'page_title': 'First Time Setup - Create Admin Account',
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
            })

    @staticmethod
    def is_setup_complete():
        """Check if first-time setup has been completed."""
        try:
            if User.objects.filter(is_superuser=True).exists():
                return True
        except Exception:
            return False

        setup_file = Path(__file__).resolve().parent.parent / '.setup_complete'
        if setup_file.exists():
            try:
                with open(setup_file, 'r') as f:
                    data = json.load(f)
                    return data.get('setup_complete', False)
            except Exception:
                pass

        return False

    @staticmethod
    def mark_setup_complete():
        """Mark first-time setup as complete."""
        setup_file = Path(__file__).resolve().parent.parent / '.setup_complete'
        data = {}
        if setup_file.exists():
            try:
                with open(setup_file, 'r') as f:
                    data = json.load(f)
            except Exception:
                pass

        data['setup_complete'] = True

        try:
            with open(setup_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
