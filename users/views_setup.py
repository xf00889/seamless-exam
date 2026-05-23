"""
First-time setup views for creating initial teacher account.
"""

from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from .models import Teacher
from pathlib import Path
import json


class FirstTimeSetupView(View):
    """
    View for first-time setup - creates the initial teacher account.
    Only accessible when no teachers exist in the system.
    """
    
    def get(self, request):
        """Display the setup form."""
        # Check if setup is already complete
        if self.is_setup_complete():
            return redirect('home')
        
        return render(request, 'users/first_time_setup.html', {
            'page_title': 'First Time Setup - Create Teacher Account'
        })
    
    def post(self, request):
        """Process the setup form and create teacher account."""
        # Check if setup is already complete
        if self.is_setup_complete():
            messages.error(request, 'Setup has already been completed.')
            return redirect('home')
        
        # Get form data
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        department = request.POST.get('department', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        
        # Validation
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
        
        # If there are errors, show them
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'users/first_time_setup.html', {
                'page_title': 'First Time Setup - Create Teacher Account',
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'department': department,
            })
        
        # Create the teacher account
        try:
            with transaction.atomic():
                # Create Django user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=True,  # Allow access to admin panel
                    is_superuser=True  # Make them a superuser
                )
                
                # Create teacher profile
                teacher = Teacher.objects.create(
                    user=user,
                    department=department
                )
                
                # Mark setup as complete
                self.mark_setup_complete()
                
                messages.success(
                    request,
                    f'Teacher account created successfully! Welcome, {first_name}!'
                )
                
                # Redirect to teacher login
                return redirect('teacher_login')
                
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'users/first_time_setup.html', {
                'page_title': 'First Time Setup - Create Teacher Account',
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'department': department,
            })
    
    @staticmethod
    def is_setup_complete():
        """Check if first-time setup has been completed."""
        try:
            # Check if any teachers exist
            if Teacher.objects.exists():
                return True
        except Exception:
            # Table doesn't exist yet, setup not complete
            return False
        
        # Check if setup flag file exists
        setup_file = Path(__file__).resolve().parent.parent / '.setup_complete'
        if setup_file.exists():
            try:
                with open(setup_file, 'r') as f:
                    data = json.load(f)
                    return data.get('teacher_created', False)
            except:
                pass
        
        return False
    
    @staticmethod
    def mark_setup_complete():
        """Mark first-time setup as complete."""
        setup_file = Path(__file__).resolve().parent.parent / '.setup_complete'
        
        # Load existing data or create new
        data = {}
        if setup_file.exists():
            try:
                with open(setup_file, 'r') as f:
                    data = json.load(f)
            except:
                pass
        
        # Update data
        data['teacher_created'] = True
        
        # Save
        try:
            with open(setup_file, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass
