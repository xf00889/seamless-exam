from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.db import models
from datetime import datetime
from services.auth_service import AuthenticationService
from services.profile_service import ProfileService
from services.dashboard_service import DashboardService
from services.class_service import ClassService
from users.decorators import student_required, teacher_required
from users.forms import (
    TeacherLoginForm, 
    StudentLoginForm,
    ProfileEditForm,
    PasswordChangeForm,
    ProfilePictureForm,
    ClassForm,
    StudentClassAssignmentForm,
    BulkStudentAssignmentForm,
    StudentCreationForm
)


class TeacherLoginView(View):
    """
    View for teacher authentication.
    Handles GET (display form) and POST (process login).
    Requirements: 1.2
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
    
    def get(self, request):
        """Display teacher login form."""
        # Redirect if already authenticated
        if self.auth_service.is_authenticated(request):
            if self.auth_service.require_teacher(request):
                return redirect('teacher_dashboard')
        
        form = TeacherLoginForm()
        return render(request, 'users/teacher_login.html', {'form': form})
    
    def post(self, request):
        """Process teacher login with form validation."""
        form = TeacherLoginForm(request.POST)
        
        if not form.is_valid():
            # Display field-specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return render(request, 'users/teacher_login.html', {'form': form})
        
        # Get cleaned data
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        
        # Authenticate
        result = self.auth_service.authenticate_teacher(request, username, password)
        
        if result.success:
            messages.success(request, f'Welcome, {result.user.user.get_full_name() or username}!')
            # Redirect to teacher dashboard
            next_url = request.GET.get('next', 'teacher_dashboard')
            return redirect(next_url)
        else:
            messages.error(request, result.error)
            form.add_error(None, result.error)
            return render(request, 'users/teacher_login.html', {'form': form})


class StudentLoginView(View):
    """
    View for student authentication using School_ID.
    Handles GET (display form) and POST (process login).
    Requirements: 2.2
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
    
    def get(self, request):
        """Display student login form."""
        # Redirect if already authenticated
        if self.auth_service.is_authenticated(request):
            if self.auth_service.require_student(request):
                return redirect('student_exam_list')  # Will be implemented in exam management
        
        form = StudentLoginForm()
        return render(request, 'users/student_login.html', {'form': form})
    
    def post(self, request):
        """Process student login with form validation."""
        form = StudentLoginForm(request.POST)
        
        if not form.is_valid():
            # Display field-specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return render(request, 'users/student_login.html', {'form': form})
        
        # Get cleaned data
        school_id = form.cleaned_data['school_id']
        password = form.cleaned_data['password']
        
        # Authenticate
        result = self.auth_service.authenticate_student(request, school_id, password)
        
        if result.success:
            messages.success(request, f'Welcome, {result.user.get_full_name()}!')
            # Redirect to student exam list
            next_url = request.GET.get('next', 'student_exam_list')
            return redirect(next_url)
        else:
            messages.error(request, result.error)
            form.add_error(None, result.error)
            return render(request, 'users/student_login.html', {'form': form})


class LogoutView(View):
    """
    View for user logout.
    Terminates session and clears authentication tokens.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
    
    def get(self, request):
        """Handle logout via GET request."""
        return self._logout(request)
    
    def post(self, request):
        """Handle logout via POST request (preferred for security)."""
        return self._logout(request)
    
    def _logout(self, request):
        """Perform logout operation."""
        user_type = self.auth_service.get_current_user_type(request)
        
        # Logout user
        self.auth_service.logout_user(request)
        
        # Show success message
        messages.success(request, 'You have been logged out successfully')
        
        # Redirect to appropriate login page
        if user_type == 'teacher':
            return redirect('teacher_login')
        elif user_type == 'student':
            return redirect('student_login')
        else:
            return redirect('home')


@method_decorator(student_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class StudentProfileView(View):
    """
    View for displaying student profile information.
    Shows profile picture, basic information, and recent exam history.
    Requirements: 2.1, 6.1, 13.4
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
        self.profile_service = ProfileService()
        self.dashboard_service = DashboardService()
    
    def get(self, request):
        """Display student profile page."""
        # Get current student (authentication already checked by decorator)
        student = self.auth_service.get_current_student(request)
        if not student:
            messages.error(request, 'Student profile not found')
            return redirect('student_login')
        
        # Get profile data
        profile_result = self.profile_service.get_student_profile(student.id)
        
        if profile_result.is_failure():
            messages.error(request, 'Failed to load profile information')
            return redirect('student_exam_list')
        
        # Get recent exam history (Requirement 6.1)
        recent_activity_result = self.dashboard_service.get_recent_activity(student.id, limit=5)
        recent_exams = []
        
        if recent_activity_result.is_success():
            recent_exams = recent_activity_result.value
        
        # Get class information (Requirements 4.1, 4.2)
        student_data = profile_result.value
        class_info = None
        if student_data.class_assigned:
            class_info = {
                'grade_level': student_data.class_assigned.grade_level,
                'strand': student_data.class_assigned.strand,
                'section': student_data.class_assigned.section,
                'full_name': str(student_data.class_assigned)
            }
        
        context = {
            'student': student_data,
            'page_title': 'My Profile',
            'recent_exams': recent_exams,
            'class_info': class_info
        }
        
        return render(request, 'users/student_profile.html', context)


@method_decorator(student_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class StudentProfileEditView(View):
    """
    View for editing student profile information.
    Allows updating first name, last name, and bio.
    Requirements: 3.1, 3.4, 13.4
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
        self.profile_service = ProfileService()
    
    def get(self, request):
        """Display profile edit form with current values."""
        # Get current student (authentication already checked by decorator)
        student = self.auth_service.get_current_student(request)
        if not student:
            messages.error(request, 'Student profile not found')
            return redirect('student_login')
        
        # Pre-fill form with current values (Requirement 3.2)
        form = ProfileEditForm(initial={
            'first_name': student.first_name,
            'last_name': student.last_name,
            'bio': student.bio or ''
        })
        
        context = {
            'form': form,
            'student': student,
            'page_title': 'Edit Profile'
        }
        
        return render(request, 'users/student_profile_edit.html', context)
    
    def post(self, request):
        """Process profile update with validation."""
        # Get current student (authentication already checked by decorator)
        student = self.auth_service.get_current_student(request)
        if not student:
            messages.error(request, 'Student profile not found')
            return redirect('student_login')
        
        # Validate form (Requirement 3.4)
        form = ProfileEditForm(request.POST)
        
        if not form.is_valid():
            # Display field-specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            
            context = {
                'form': form,
                'student': student,
                'page_title': 'Edit Profile'
            }
            return render(request, 'users/student_profile_edit.html', context)
        
        # Update profile using service
        update_data = {
            'first_name': form.cleaned_data['first_name'],
            'last_name': form.cleaned_data['last_name'],
            'bio': form.cleaned_data.get('bio', '')
        }
        
        result = self.profile_service.update_profile_info(student.id, update_data)
        
        if result.is_success():
            # Update session with new name
            request.session['student_name'] = result.value.get_full_name()
            messages.success(request, 'Profile updated successfully')
            return redirect('student_profile')
        else:
            # Display error from service
            error_details = result.error.details if hasattr(result.error, 'details') else {}
            for field, error in error_details.items():
                messages.error(request, f'{field}: {error}')
            
            context = {
                'form': form,
                'student': student,
                'page_title': 'Edit Profile'
            }
            return render(request, 'users/student_profile_edit.html', context)


@method_decorator(student_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class ProfilePictureUploadView(View):
    """
    View for uploading and updating profile pictures.
    Handles image validation and secure storage.
    Requirements: 4.1, 4.2, 4.3, 13.1, 13.4
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
        self.profile_service = ProfileService()
    
    def post(self, request):
        """Process profile picture upload."""
        # Get current student (authentication already checked by decorator)
        student = self.auth_service.get_current_student(request)
        if not student:
            return JsonResponse({
                'success': False,
                'error': 'Student profile not found'
            }, status=404)
        
        # Validate form
        form = ProfilePictureForm(request.POST, request.FILES)
        
        if not form.is_valid():
            # Return validation errors
            errors = []
            for field, field_errors in form.errors.items():
                for error in field_errors:
                    errors.append(error)
            
            return JsonResponse({
                'success': False,
                'error': '; '.join(errors)
            }, status=400)
        
        # Upload profile picture using service
        file = form.cleaned_data['profile_picture']
        result = self.profile_service.upload_profile_picture(student.id, file)
        
        if result.is_success():
            return JsonResponse({
                'success': True,
                'message': 'Profile picture updated successfully',
                'url': result.value
            })
        else:
            error_message = str(result.error)
            if hasattr(result.error, 'details'):
                error_details = result.error.details
                if 'error' in error_details:
                    error_message = error_details['error']
            
            return JsonResponse({
                'success': False,
                'error': error_message
            }, status=400)
    
    def delete(self, request):
        """Delete profile picture."""
        # Get current student (authentication already checked by decorator)
        student = self.auth_service.get_current_student(request)
        if not student:
            return JsonResponse({
                'success': False,
                'error': 'Student profile not found'
            }, status=404)
        
        # Delete profile picture using service
        result = self.profile_service.delete_profile_picture(student.id)
        
        if result.is_success():
            return JsonResponse({
                'success': True,
                'message': 'Profile picture deleted successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': str(result.error)
            }, status=400)


@method_decorator(student_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class ChangePasswordView(View):
    """
    View for changing student password.
    Requires current password verification and validates new password.
    Implements rate limiting to prevent abuse.
    Requirements: 5.1, 5.2, 5.4, 13.4
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
        self.profile_service = ProfileService()
    
    def get(self, request):
        """Redirect to profile page where password change form lives."""
        return redirect('student_profile')

    def post(self, request):
        """Process password change with security checks and rate limiting."""
        student = self.auth_service.get_current_student(request)
        if not student:
            messages.error(request, 'Student profile not found')
            return redirect('student_login')

        form = PasswordChangeForm(request.POST)

        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return redirect('student_profile')

        current_password = form.cleaned_data['current_password']
        new_password = form.cleaned_data['new_password']

        result = self.profile_service.change_password(
            student.id,
            current_password,
            new_password
        )

        if result.is_success():
            messages.success(request, 'Password changed successfully')
        else:
            error_message = str(result.error.message) if hasattr(result.error, 'message') else str(result.error)
            messages.error(request, error_message)

        return redirect('student_profile')


@method_decorator(student_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class StudentDashboardView(View):
    """
    View for displaying student dashboard with performance analytics.
    Shows metrics, charts, and recent activity.
    Requirements: 7.1, 8.1, 10.1, 11.1, 13.4
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
        self.dashboard_service = DashboardService()
    
    def get(self, request):
        """Display student dashboard with metrics and charts."""
        # Get current student (authentication already checked by decorator)
        student = self.auth_service.get_current_student(request)
        if not student:
            messages.error(request, 'Student profile not found')
            return redirect('student_login')
        
        student_id = student.id
        
        # Try to get cached metrics (Requirement 11.1 - 5 minute cache)
        cache_key_metrics = f'dashboard_metrics_{student_id}'
        metrics = cache.get(cache_key_metrics)
        
        if metrics is None:
            # Get performance metrics from service
            metrics_result = self.dashboard_service.get_performance_metrics(student_id)
            
            if metrics_result.is_failure():
                messages.error(request, 'Failed to load performance metrics')
                metrics = {
                    'total_exams': 0,
                    'average_score': 0.0,
                    'highest_score': 0.0,
                    'pass_rate': 0.0
                }
            else:
                metrics = metrics_result.value
                # Cache for 5 minutes (300 seconds)
                cache.set(cache_key_metrics, metrics, 300)
        
        # Try to get cached score trend (Requirement 11.1 - 10 minute cache)
        cache_key_trend = f'score_trend_{student_id}'
        score_trend = cache.get(cache_key_trend)
        
        if score_trend is None:
            # Get score trend data for chart
            trend_result = self.dashboard_service.get_score_trend(student_id)
            
            if trend_result.is_failure():
                score_trend = []
            else:
                score_trend = trend_result.value
                # Cache for 10 minutes (600 seconds)
                cache.set(cache_key_trend, score_trend, 600)
        
        # Get performance by question type
        type_performance_result = self.dashboard_service.get_type_performance(student_id)
        
        if type_performance_result.is_failure():
            type_performance = {}
        else:
            type_performance = type_performance_result.value
        
        # Get recent activity (not cached - always fresh)
        recent_activity_result = self.dashboard_service.get_recent_activity(student_id, limit=5)
        
        if recent_activity_result.is_failure():
            recent_activity = []
        else:
            recent_activity = recent_activity_result.value
        
        context = {
            'student': student,
            'metrics': metrics,
            'score_trend': score_trend,
            'type_performance': type_performance,
            'recent_activity': recent_activity,
            'page_title': 'My Dashboard',
            'has_data': metrics['total_exams'] > 0
        }
        
        return render(request, 'users/student_dashboard.html', context)


@method_decorator(student_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class StudentHistoryView(View):
    """
    View for displaying complete exam history with filtering and pagination.
    Shows all exam attempts with optional date and status filters.
    Supports AJAX requests for dynamic filtering without page reload.
    Requirements: 6.1, 13.4, 15.1, 15.2, 15.3, 15.4, 15.5
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
        self.dashboard_service = DashboardService()
    
    def get(self, request):
        """Display exam history with filters and pagination."""
        # Get current student (authentication already checked by decorator)
        student = self.auth_service.get_current_student(request)
        if not student:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Student profile not found'
                }, status=404)
            messages.error(request, 'Student profile not found')
            return redirect('student_login')
        
        student_id = student.id
        
        # Get filter parameters from query string (Requirements 15.1, 15.2)
        filters = {}
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        status_filter = request.GET.get('status')
        
        if date_from:
            try:
                filters['date_from'] = datetime.fromisoformat(date_from)
            except ValueError:
                if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    messages.warning(request, 'Invalid date_from format')
        
        if date_to:
            try:
                # Add end of day to include the entire day
                date_to_obj = datetime.fromisoformat(date_to)
                filters['date_to'] = date_to_obj.replace(hour=23, minute=59, second=59)
            except ValueError:
                if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    messages.warning(request, 'Invalid date_to format')
        
        if status_filter and status_filter in ['graded', 'submitted', 'pending']:
            filters['status'] = status_filter
        
        # Get exam history with filters (Requirement 15.3)
        history_result = self.dashboard_service.get_exam_history(student_id, filters)
        
        if history_result.is_failure():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to load exam history'
                }, status=500)
            messages.error(request, 'Failed to load exam history')
            history_data = []
        else:
            history_data = history_result.value
        
        # Apply sorting if requested
        sort_field = request.GET.get('sort', 'date')
        sort_order = request.GET.get('order', 'desc')
        
        if sort_field == 'title':
            history_data = sorted(
                history_data, 
                key=lambda x: x['exam_title'].lower(),
                reverse=(sort_order == 'desc')
            )
        elif sort_field == 'score':
            history_data = sorted(
                history_data,
                key=lambda x: x['score'] if x['score'] is not None else -1,
                reverse=(sort_order == 'desc')
            )
        elif sort_field == 'date':
            history_data = sorted(
                history_data,
                key=lambda x: x['date'] if x['date'] else '',
                reverse=(sort_order == 'desc')
            )
        
        # Implement pagination (10 items per page - Requirement 6.5, 15.1)
        paginator = Paginator(history_data, 10)
        page = request.GET.get('page', 1)
        
        try:
            history_page = paginator.page(page)
        except PageNotAnInteger:
            history_page = paginator.page(1)
        except EmptyPage:
            history_page = paginator.page(paginator.num_pages)
        
        # Handle AJAX requests (Requirement 15.3)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return JSON response for AJAX requests
            return JsonResponse({
                'success': True,
                'data': {
                    'exams': list(history_page),
                    'pagination': {
                        'current_page': history_page.number,
                        'total_pages': paginator.num_pages,
                        'has_previous': history_page.has_previous(),
                        'has_next': history_page.has_next(),
                        'previous_page': history_page.previous_page_number() if history_page.has_previous() else None,
                        'next_page': history_page.next_page_number() if history_page.has_next() else None,
                        'total_count': paginator.count
                    },
                    'filters': {
                        'date_from': date_from or '',
                        'date_to': date_to or '',
                        'status': status_filter or ''
                    },
                    'sort': {
                        'field': sort_field,
                        'order': sort_order
                    }
                }
            })
        
        # Regular page render
        context = {
            'student': student,
            'history_page': history_page,
            'filters': {
                'date_from': date_from or '',
                'date_to': date_to or '',
                'status': status_filter or ''
            },
            'sort_field': sort_field,
            'sort_order': sort_order,
            'page_title': 'Exam History',
            'has_filters': bool(date_from or date_to or status_filter)
        }
        
        return render(request, 'users/student_history.html', context)


@method_decorator(student_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class ExportHistoryView(View):
    """
    View for exporting exam history as CSV file.
    Generates downloadable CSV with all exam records.
    Requirements: 13.4, 14.1, 14.2, 14.3, 14.4, 14.5
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
        self.dashboard_service = DashboardService()
    
    def get(self, request):
        """Generate and download CSV export of exam history."""
        # Get current student (authentication already checked by decorator)
        student = self.auth_service.get_current_student(request)
        if not student:
            messages.error(request, 'Student profile not found')
            return redirect('student_login')
        
        student_id = student.id
        
        # Export history as CSV
        export_result = self.dashboard_service.export_history_csv(student_id)
        
        if export_result.is_failure():
            messages.error(request, 'Failed to export exam history')
            return redirect('student_history')
        
        csv_content = export_result.value
        
        # Generate descriptive filename with student name and date (Requirement 14.4)
        student_name = student.get_full_name().replace(' ', '_')
        current_date = timezone.now().strftime('%Y%m%d')
        filename = f'exam_history_{student_name}_{current_date}.csv'
        
        # Create HTTP response with CSV content (Requirement 14.5)
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response



# ============================================================================
# TEACHER PROFILE VIEWS
# ============================================================================

@method_decorator(teacher_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class TeacherProfileView(View):
    """
    View for displaying teacher profile information.
    Shows teacher details and recent activity.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
    
    def get(self, request):
        """Display teacher profile page."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        context = {
            'teacher': teacher,
        }
        
        return render(request, 'users/teacher_profile.html', context)


@method_decorator(teacher_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class TeacherProfileEditView(View):
    """
    View for editing teacher profile information.
    Allows updating name and email.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
    
    def get(self, request):
        """Display profile edit form."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        # Pre-fill form with current data
        initial_data = {
            'first_name': teacher.user.first_name,
            'last_name': teacher.user.last_name,
            'email': teacher.user.email,
        }
        
        form = ProfileEditForm(initial=initial_data)
        
        context = {
            'teacher': teacher,
            'form': form,
        }
        
        return render(request, 'users/teacher_profile_edit.html', context)
    
    def post(self, request):
        """Process profile update."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        form = ProfileEditForm(request.POST)
        
        if form.is_valid():
            # Update user information
            user = teacher.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data.get('email', '')
            user.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('teacher_profile')
        else:
            # Display validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        
        context = {
            'teacher': teacher,
            'form': form,
        }
        
        return render(request, 'users/teacher_profile_edit.html', context)


@method_decorator(teacher_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class TeacherChangePasswordView(View):
    """
    View for changing teacher password.
    Requires current password verification.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
    
    def get(self, request):
        """Redirect to profile page where password change form lives."""
        return redirect('teacher_profile')

    def post(self, request):
        """Process password change."""
        teacher = self.auth_service.get_current_teacher(request)

        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')

        form = PasswordChangeForm(request.POST)

        if form.is_valid():
            current_password = form.cleaned_data['current_password']
            new_password = form.cleaned_data['new_password']

            from django.contrib.auth import authenticate
            user = authenticate(
                request,
                username=teacher.user.username,
                password=current_password
            )

            if user is None:
                messages.error(request, 'Current password is incorrect')
            else:
                user.set_password(new_password)
                user.save()

                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)

                messages.success(request, 'Password changed successfully!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

        return redirect('teacher_profile')


@method_decorator(teacher_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class TeacherProfilePictureUploadView(View):
    """
    View for uploading and updating teacher profile pictures.
    Handles image validation and secure storage.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
    
    def post(self, request):
        """Process profile picture upload."""
        teacher = self.auth_service.get_current_teacher(request)
        if not teacher:
            return JsonResponse({
                'success': False,
                'error': 'Teacher profile not found'
            }, status=404)
        
        # Validate form
        form = ProfilePictureForm(request.POST, request.FILES)
        
        if not form.is_valid():
            errors = []
            for field, field_errors in form.errors.items():
                for error in field_errors:
                    errors.append(error)
            
            return JsonResponse({
                'success': False,
                'error': '; '.join(errors)
            }, status=400)
        
        # Get the uploaded file
        file = form.cleaned_data['profile_picture']
        
        # Validate file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'File size must be less than 5MB'
            }, status=400)
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
        if file.content_type not in allowed_types:
            return JsonResponse({
                'success': False,
                'error': 'Only JPG, PNG, and GIF images are allowed'
            }, status=400)
        
        try:
            # Delete old profile picture if exists
            if teacher.profile_picture:
                old_path = teacher.profile_picture.path
                import os
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            # Save new profile picture
            teacher.profile_picture = file
            teacher.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Profile picture updated successfully',
                'url': teacher.profile_picture.url
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to upload picture: {str(e)}'
            }, status=500)
    
    def delete(self, request):
        """Delete profile picture."""
        teacher = self.auth_service.get_current_teacher(request)
        if not teacher:
            return JsonResponse({
                'success': False,
                'error': 'Teacher profile not found'
            }, status=404)
        
        try:
            # Delete the file if exists
            if teacher.profile_picture:
                old_path = teacher.profile_picture.path
                import os
                if os.path.exists(old_path):
                    os.remove(old_path)
                
                # Clear the field
                teacher.profile_picture = None
                teacher.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Profile picture deleted successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to delete picture: {str(e)}'
            }, status=500)



# ============================================================================
# CLASS MANAGEMENT VIEWS
# ============================================================================

@method_decorator(teacher_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class ClassListView(View):
    """
    View for displaying all classes for a logged-in teacher.
    Supports filtering by grade level and strand with pagination.
    Requirements: 1.3
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
        self.class_service = ClassService()
    
    def get(self, request):
        """Display class list with filters and pagination."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        # Get all classes for the teacher
        from repositories.class_repository import ClassRepository
        repository = ClassRepository()
        classes_queryset = repository.get_classes_by_teacher(teacher.pk)
        
        # Apply filters
        grade_filter = request.GET.get('grade_level', '').strip()
        strand_filter = request.GET.get('strand', '').strip()
        
        if grade_filter:
            classes_queryset = classes_queryset.filter(grade_level__icontains=grade_filter)
        
        if strand_filter:
            classes_queryset = classes_queryset.filter(strand__icontains=strand_filter)
        
        # Implement pagination (20 items per page)
        paginator = Paginator(classes_queryset, 20)
        page = request.GET.get('page', 1)
        
        try:
            classes_page = paginator.page(page)
        except PageNotAnInteger:
            classes_page = paginator.page(1)
        except EmptyPage:
            classes_page = paginator.page(paginator.num_pages)
        
        context = {
            'teacher': teacher,
            'classes_page': classes_page,
            'grade_filter': grade_filter,
            'strand_filter': strand_filter,
            'page_title': 'My Classes',
            'has_filters': bool(grade_filter or strand_filter)
        }
        
        return render(request, 'users/class_list.html', context)


@method_decorator(teacher_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class ClassCreateView(View):
    """
    View for creating a new class.
    Uses ClassForm for validation and associates class with logged-in teacher.
    Requirements: 1.1, 1.2, 7.1
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
        self.class_service = ClassService()
    
    def get(self, request):
        """Display class creation form."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        form = ClassForm(teacher=teacher)
        
        context = {
            'teacher': teacher,
            'form': form,
            'page_title': 'Create Class',
            'form_action': 'create'
        }
        
        return render(request, 'users/class_form.html', context)
    
    def post(self, request):
        """Process class creation with validation."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        form = ClassForm(request.POST, teacher=teacher)
        
        if not form.is_valid():
            # Display field-specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            
            context = {
                'teacher': teacher,
                'form': form,
                'page_title': 'Create Class',
                'form_action': 'create'
            }
            return render(request, 'users/class_form.html', context)
        
        # Create class using service
        result = self.class_service.create_class(
            teacher_id=teacher.pk,
            grade_level=form.cleaned_data['grade_level'],
            strand=form.cleaned_data['strand'],
            section=form.cleaned_data['section']
        )
        
        if result.is_success():
            messages.success(request, 'Class created successfully')
            return redirect('class_list')
        else:
            messages.error(request, result.error)
            
            context = {
                'teacher': teacher,
                'form': form,
                'page_title': 'Create Class',
                'form_action': 'create'
            }
            return render(request, 'users/class_form.html', context)


@method_decorator(teacher_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class ClassUpdateView(View):
    """
    View for editing an existing class.
    Verifies teacher owns the class and handles uniqueness validation.
    Requirements: 1.4, 7.3
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
        self.class_service = ClassService()
    
    def get(self, request, class_id):
        """Display class edit form with current values."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        # Get the class
        from repositories.class_repository import ClassRepository
        repository = ClassRepository()
        class_obj = repository.get_by_id(class_id)
        
        if not class_obj:
            messages.error(request, 'Class not found')
            return redirect('class_list')
        
        # Verify teacher owns the class
        if class_obj.teacher_id != teacher.pk:
            messages.error(request, 'You do not have permission to edit this class')
            return redirect('class_list')
        
        # Pre-fill form with current values
        form = ClassForm(
            initial={
                'grade_level': class_obj.grade_level,
                'strand': class_obj.strand,
                'section': class_obj.section
            },
            teacher=teacher,
            class_id=class_id
        )
        
        context = {
            'teacher': teacher,
            'form': form,
            'class_obj': class_obj,
            'page_title': 'Edit Class',
            'form_action': 'update'
        }
        
        return render(request, 'users/class_form.html', context)
    
    def post(self, request, class_id):
        """Process class update with validation."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        # Get the class
        from repositories.class_repository import ClassRepository
        repository = ClassRepository()
        class_obj = repository.get_by_id(class_id)
        
        if not class_obj:
            messages.error(request, 'Class not found')
            return redirect('class_list')
        
        # Verify teacher owns the class
        if class_obj.teacher_id != teacher.pk:
            messages.error(request, 'You do not have permission to edit this class')
            return redirect('class_list')
        
        form = ClassForm(request.POST, teacher=teacher, class_id=class_id)
        
        if not form.is_valid():
            # Display field-specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            
            context = {
                'teacher': teacher,
                'form': form,
                'class_obj': class_obj,
                'page_title': 'Edit Class',
                'form_action': 'update'
            }
            return render(request, 'users/class_form.html', context)
        
        # Update class using service
        result = self.class_service.update_class(
            class_id=class_id,
            grade_level=form.cleaned_data['grade_level'],
            strand=form.cleaned_data['strand'],
            section=form.cleaned_data['section']
        )
        
        if result.is_success():
            messages.success(request, 'Class updated successfully')
            return redirect('class_detail', class_id=class_id)
        else:
            messages.error(request, result.error)
            
            context = {
                'teacher': teacher,
                'form': form,
                'class_obj': class_obj,
                'page_title': 'Edit Class',
                'form_action': 'update'
            }
            return render(request, 'users/class_form.html', context)


@method_decorator(teacher_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class ClassDeleteView(View):
    """
    View for deleting a class with password confirmation.
    Verifies teacher owns the class and handles cascade to students (SET_NULL).
    Requirements: 1.5
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
        self.class_service = ClassService()
    
    def get(self, request, class_id):
        """Redirect GET requests to class list (deletion should only be via POST from modal)."""
        messages.info(request, 'Please use the delete button from the class list to delete a class.')
        return redirect('class_list')
    
    def post(self, request, class_id):
        """Process class deletion with password verification."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        # Get the class
        from repositories.class_repository import ClassRepository
        repository = ClassRepository()
        class_obj = repository.get_by_id(class_id)
        
        if not class_obj:
            messages.error(request, 'Class not found')
            return redirect('class_list')
        
        # Verify teacher owns the class
        if class_obj.teacher_id != teacher.pk:
            messages.error(request, 'You do not have permission to delete this class')
            return redirect('class_list')
        
        # Get password from request
        password = request.POST.get('password', '')
        
        if not password:
            messages.error(request, 'Password is required to delete a class')
            return redirect('class_list')
        
        # Verify password
        from django.contrib.auth import authenticate
        user = authenticate(username=request.user.username, password=password)
        
        if user is None:
            messages.error(
                request,
                'Incorrect password. Class deletion cancelled for security.'
            )
            return redirect('class_list')
        
        # Password verified - proceed with deletion
        class_name = f"{class_obj.grade_level} - {class_obj.strand} {class_obj.section}"
        student_count = class_obj.students.count()
        
        # Delete class using service
        result = self.class_service.delete_class(class_id)
        
        if result.is_success():
            messages.success(
                request, 
                f'Class "{class_name}" has been permanently deleted. '
                f'{student_count} student(s) have been unassigned from this class.'
            )
            return redirect('class_list')
        else:
            messages.error(request, result.error)
            return redirect('class_list')


@method_decorator(teacher_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class ClassDetailView(View):
    """
    View for displaying class details.
    Shows class information, student list, and exam assignments.
    Requirements: 2.3, 3.4
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
        self.class_service = ClassService()
    
    def get(self, request, class_id):
        """Display class detail page."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        # Get the class with students
        from repositories.class_repository import ClassRepository
        repository = ClassRepository()
        class_obj = repository.get_class_with_students(class_id)
        
        if not class_obj:
            messages.error(request, 'Class not found')
            return redirect('class_list')
        
        # Verify teacher owns the class
        if class_obj.teacher_id != teacher.pk:
            messages.error(request, 'You do not have permission to view this class')
            return redirect('class_list')
        
        # Get students in the class
        students = class_obj.students.all().order_by('last_name', 'first_name')
        
        # Get exams assigned to this class
        exams_result = self.class_service.get_exams_for_class(class_id)
        exams = exams_result.value if exams_result.is_success() else []
        
        # Get class statistics
        stats_result = self.class_service.get_class_statistics(class_id)
        statistics = stats_result.value if stats_result.is_success() else {
            'student_count': 0,
            'average_score': 0.0,
            'total_attempts': 0,
            'exams_assigned': 0
        }
        
        context = {
            'teacher': teacher,
            'class_obj': class_obj,
            'students': students,
            'exams': exams,
            'statistics': statistics,
            'page_title': f'{class_obj.grade_level} - {class_obj.strand} - {class_obj.section}'
        }
        
        return render(request, 'users/class_detail.html', context)


@method_decorator(teacher_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class StudentAssignView(View):
    """
    View for assigning individual students to classes.
    Uses StudentClassAssignmentForm and handles single class assignment rule.
    Requirements: 2.1, 2.2
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
        self.class_service = ClassService()
    
    def get(self, request):
        """Display student assignment form."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        form = StudentClassAssignmentForm(teacher=teacher)
        
        context = {
            'teacher': teacher,
            'form': form,
            'page_title': 'Assign Student to Class'
        }
        
        return render(request, 'users/student_assignment.html', context)
    
    def post(self, request):
        """Process student assignment with validation."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        form = StudentClassAssignmentForm(request.POST, teacher=teacher)
        
        if not form.is_valid():
            # Display field-specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            
            context = {
                'teacher': teacher,
                'form': form,
                'page_title': 'Assign Student to Class'
            }
            return render(request, 'users/student_assignment.html', context)
        
        # Get form data
        student = form.cleaned_data['student']
        class_assigned = form.cleaned_data['class_assigned']
        
        # Verify teacher owns the class
        if class_assigned.teacher_id != teacher.pk:
            messages.error(request, 'You do not have permission to assign students to this class')
            context = {
                'teacher': teacher,
                'form': form,
                'page_title': 'Assign Student to Class'
            }
            return render(request, 'users/student_assignment.html', context)
        
        # Assign student using service (handles single class assignment rule)
        result = self.class_service.assign_student_to_class(
            student_id=student.pk,
            class_id=class_assigned.pk
        )
        
        if result.is_success():
            messages.success(
                request,
                f'{student.get_full_name()} has been assigned to {class_assigned}'
            )
            return redirect('class_detail', class_id=class_assigned.pk)
        else:
            messages.error(request, result.error)
            
            context = {
                'teacher': teacher,
                'form': form,
                'page_title': 'Assign Student to Class'
            }
            return render(request, 'users/student_assignment.html', context)


@method_decorator(teacher_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class StudentRemoveView(View):
    """
    View for removing students from their assigned class.
    Sets class assignment to null while preserving attempt history.
    Requirements: 2.4, 2.5
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
        self.class_service = ClassService()
    
    def get(self, request, student_id):
        """Display confirmation page for student removal."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        # Get the student
        from repositories.student_repository import StudentRepository
        repository = StudentRepository()
        student = repository.get_by_id(student_id)
        
        if not student:
            messages.error(request, 'Student not found')
            return redirect('class_list')
        
        # Check if student has a class assignment
        if not student.class_assigned:
            messages.warning(request, f'{student.get_full_name()} is not assigned to any class')
            return redirect('class_list')
        
        # Verify teacher owns the class
        if student.class_assigned.teacher_id != teacher.pk:
            messages.error(request, 'You do not have permission to remove this student from their class')
            return redirect('class_list')
        
        # Get attempt count for display
        from attempts.models import Attempt
        attempt_count = Attempt.objects.filter(student_id=student_id).count()
        
        context = {
            'teacher': teacher,
            'student': student,
            'class_obj': student.class_assigned,
            'attempt_count': attempt_count,
            'page_title': 'Remove Student from Class'
        }
        
        return render(request, 'users/student_remove_confirm.html', context)
    
    def post(self, request, student_id):
        """Process student removal from class."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        # Get the student
        from repositories.student_repository import StudentRepository
        repository = StudentRepository()
        student = repository.get_by_id(student_id)
        
        if not student:
            messages.error(request, 'Student not found')
            return redirect('class_list')
        
        # Check if student has a class assignment
        if not student.class_assigned:
            messages.warning(request, f'{student.get_full_name()} is not assigned to any class')
            return redirect('class_list')
        
        # Verify teacher owns the class
        class_id = student.class_assigned.pk
        if student.class_assigned.teacher_id != teacher.pk:
            messages.error(request, 'You do not have permission to remove this student from their class')
            return redirect('class_list')
        
        # Remove student from class using service (preserves attempt history)
        result = self.class_service.remove_student_from_class(student_id)
        
        if result.is_success():
            messages.success(
                request,
                f'{student.get_full_name()} has been removed from the class. '
                f'Their exam history has been preserved.'
            )
            return redirect('class_detail', class_id=class_id)
        else:
            messages.error(request, result.error)
            return redirect('class_detail', class_id=class_id)


@method_decorator(teacher_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class BulkStudentAssignView(View):
    """
    View for bulk assigning multiple students to a class.
    Uses BulkStudentAssignmentForm with transaction for atomicity.
    Requirements: 8.3, 8.4, 8.5
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
        self.class_service = ClassService()
    
    def get(self, request):
        """Display bulk student assignment form."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        # Get class_id from query parameters for auto-detection
        class_id = request.GET.get('class_id')
        
        form = BulkStudentAssignmentForm(teacher=teacher, initial_class_id=class_id)
        
        # Get class name and object for display if class_id is provided
        selected_class_name = None
        selected_class_obj = None
        class_preselected = False
        
        if class_id:
            try:
                from users.models import Class
                selected_class_obj = Class.objects.get(id=class_id, teacher=teacher)
                selected_class_name = f"{selected_class_obj.grade_level} - {selected_class_obj.strand} ({selected_class_obj.section})"
                class_preselected = True
            except Class.DoesNotExist:
                pass
        
        context = {
            'teacher': teacher,
            'form': form,
            'page_title': 'Assign Students' if class_preselected else 'Bulk Assign Students to Class',
            'selected_class_name': selected_class_name,
            'selected_class': selected_class_obj,
            'class_preselected': class_preselected,
            'class_id': class_id
        }
        
        return render(request, 'users/bulk_student_assignment.html', context)
    
    def post(self, request):
        """Process bulk student assignment with transaction. Supports AJAX requests."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Teacher profile not found'})
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        # Get class_id from query parameters for form initialization
        class_id = request.GET.get('class_id')
        
        form = BulkStudentAssignmentForm(request.POST, teacher=teacher, initial_class_id=class_id)
        
        if not form.is_valid():
            # Handle AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = []
                for field, field_errors in form.errors.items():
                    for error in field_errors:
                        errors.append(str(error))
                return JsonResponse({
                    'success': False,
                    'error': 'Form validation failed',
                    'errors': errors
                })
            
            # Display field-specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            
            context = {
                'teacher': teacher,
                'form': form,
                'page_title': 'Bulk Assign Students to Class'
            }
            return render(request, 'users/bulk_student_assignment.html', context)
        
        # Get form data
        students = form.cleaned_data['students']
        class_assigned = form.cleaned_data['class_assigned']
        
        # Verify teacher owns the class
        if class_assigned.teacher_id != teacher.pk:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'You do not have permission to assign students to this class'
                })
            
            messages.error(request, 'You do not have permission to assign students to this class')
            context = {
                'teacher': teacher,
                'form': form,
                'page_title': 'Bulk Assign Students to Class'
            }
            return render(request, 'users/bulk_student_assignment.html', context)
        
        # Get student IDs
        student_ids = [student.pk for student in students]
        
        # Bulk assign students using service (atomic transaction)
        result = self.class_service.bulk_assign_students(
            student_ids=student_ids,
            class_id=class_assigned.pk
        )
        
        if result.is_success():
            summary = result.value
            
            # Handle AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Bulk assignment completed: {summary["successful"]} successful, '
                              f'{summary["failed"]} failed out of {summary["total"]} students',
                    'summary': summary,
                    'reload': True
                })
            
            # Display success/failure summary
            messages.success(
                request,
                f'Bulk assignment completed: {summary["successful"]} successful, '
                f'{summary["failed"]} failed out of {summary["total"]} students'
            )
            
            # Display any errors
            if summary['errors']:
                for error in summary['errors']:
                    messages.warning(request, error)
            
            # Redirect back to class detail if coming from class detail page
            redirect_class_id = request.GET.get('class_id') or class_assigned.pk
            return redirect('class_detail', class_id=redirect_class_id)
        else:
            # Handle AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': f'Bulk assignment failed: {result.error}. No students were assigned.'
                })
            
            # Transaction failed, all changes rolled back
            messages.error(
                request,
                f'Bulk assignment failed: {result.error}. No students were assigned.'
            )
            
            context = {
                'teacher': teacher,
                'form': form,
                'page_title': 'Bulk Assign Students to Class'
            }
            return render(request, 'users/bulk_student_assignment.html', context)



@method_decorator(teacher_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class StudentAccountManagementView(View):
    """
    View for managing student accounts.
    Allows teachers to manually create student accounts with auto-generated passwords.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
    
    def get(self, request):
        """Display student account management page with creation form and student list."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        # Import here to avoid circular imports
        from users.models import Student
        from users.forms import StudentCreationForm
        
        # Get all students ordered by last name
        students = Student.objects.all().select_related('class_assigned').order_by('last_name', 'first_name')
        
        # Apply search filter if provided
        search_query = request.GET.get('search', '').strip()
        if search_query:
            students = students.filter(
                models.Q(school_id__icontains=search_query) |
                models.Q(first_name__icontains=search_query) |
                models.Q(last_name__icontains=search_query)
            )
        
        # Pagination
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
        paginator = Paginator(students, 20)  # 20 students per page
        page = request.GET.get('page', 1)
        
        try:
            students_page = paginator.page(page)
        except PageNotAnInteger:
            students_page = paginator.page(1)
        except EmptyPage:
            students_page = paginator.page(paginator.num_pages)
        
        # Initialize form
        form = StudentCreationForm(teacher=teacher)
        
        context = {
            'teacher': teacher,
            'form': form,
            'students': students_page,
            'search_query': search_query,
            'page_title': 'Student Account Management',
            'total_students': Student.objects.count()
        }
        
        return render(request, 'users/student_account_management.html', context)
    
    def post(self, request):
        """Process student account creation."""
        teacher = self.auth_service.get_current_teacher(request)
        
        if not teacher:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Teacher profile not found'})
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')
        
        # Import here to avoid circular imports
        from users.models import Student
        from users.forms import StudentCreationForm
        
        form = StudentCreationForm(request.POST, teacher=teacher)
        
        if not form.is_valid():
            # Handle AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = []
                for field, field_errors in form.errors.items():
                    for error in field_errors:
                        errors.append(str(error))
                return JsonResponse({
                    'success': False,
                    'error': 'Form validation failed',
                    'errors': errors
                })
            
            # Display field-specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            
            # Re-render page with form errors
            students = Student.objects.all().select_related('class_assigned').order_by('last_name', 'first_name')
            
            from django.core.paginator import Paginator
            paginator = Paginator(students, 20)
            students_page = paginator.page(1)
            
            context = {
                'teacher': teacher,
                'form': form,
                'students': students_page,
                'search_query': '',
                'page_title': 'Student Account Management',
                'total_students': Student.objects.count()
            }
            return render(request, 'users/student_account_management.html', context)
        
        # Get form data
        school_id = form.cleaned_data['school_id']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        class_assigned = form.cleaned_data.get('class_assigned')
        
        # Generate password
        generated_password = StudentCreationForm.generate_password(school_id, last_name)
        
        # Create student
        try:
            student = Student(
                school_id=school_id,
                first_name=first_name,
                last_name=last_name,
                class_assigned=class_assigned
            )
            student.set_password(generated_password)
            student.save()
            
            # Handle AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Student account created successfully',
                    'student': {
                        'id': student.id,
                        'school_id': student.school_id,
                        'name': student.get_full_name(),
                        'password': generated_password,
                        'class': str(student.class_assigned) if student.class_assigned else 'Not assigned'
                    }
                })
            
            # Display success message with generated password
            messages.success(
                request,
                f'Student account created successfully! '
                f'Student ID: {school_id}, Generated Password: {generated_password}'
            )
            
            return redirect('student_account_management')
            
        except Exception as e:
            # Handle AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': f'Failed to create student account: {str(e)}'
                })
            
            messages.error(request, f'Failed to create student account: {str(e)}')

            # Re-render page with form
            students = Student.objects.all().select_related('class_assigned').order_by('last_name', 'first_name')

            from django.core.paginator import Paginator
            paginator = Paginator(students, 20)
            students_page = paginator.page(1)

            context = {
                'teacher': teacher,
                'form': form,
                'students': students_page,
                'search_query': '',
                'page_title': 'Student Account Management',
                'total_students': Student.objects.count()
            }
            return render(request, 'users/student_account_management.html', context)


class StudentDetailView(View):
    """View student account details including default password."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()

    def get(self, request, student_id):
        teacher = self.auth_service.get_current_teacher(request)
        if not teacher:
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')

        from users.models import Student
        from users.forms import StudentCreationForm

        student = get_object_or_404(Student, pk=student_id)
        default_password = StudentCreationForm.generate_password(student.school_id, student.last_name)

        context = {
            'teacher': teacher,
            'student': student,
            'default_password': default_password,
        }
        return render(request, 'users/student_detail.html', context)


class StudentResetPasswordView(View):
    """Reset a student's password to the default."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()

    def post(self, request, student_id):
        teacher = self.auth_service.get_current_teacher(request)
        if not teacher:
            return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)

        from users.models import Student
        from users.forms import StudentCreationForm

        student = get_object_or_404(Student, pk=student_id)
        default_password = StudentCreationForm.generate_password(student.school_id, student.last_name)
        student.set_password(default_password)
        student.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Password reset to default successfully'})

        messages.success(request, f'Password for {student.get_full_name()} has been reset to default.')
        return redirect('student_detail', student_id=student_id)


class StudentDeleteView(View):
    """Permanently delete a student account and all associated data."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()

    def post(self, request, student_id):
        teacher = self.auth_service.get_current_teacher(request)
        if not teacher:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
            messages.error(request, 'Teacher profile not found')
            return redirect('teacher_login')

        from users.models import Student

        student = get_object_or_404(Student, pk=student_id)
        student_name = student.get_full_name()
        student_school_id = student.school_id

        student.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Student "{student_name}" ({student_school_id}) has been permanently deleted.'
            })

        messages.success(request, f'Student "{student_name}" ({student_school_id}) has been permanently deleted.')
        return redirect('student_account_management')


@method_decorator(student_required, name='dispatch')
class StudentActivityLogView(View):
    """View for students to see their exam activity log."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()

    def get(self, request):
        student = self.auth_service.get_current_student(request)
        if not student:
            messages.error(request, 'Student profile not found')
            return redirect('student_login')

        from attempts.models import Attempt, TabViolation

        attempts = Attempt.objects.filter(student=student).select_related('exam').order_by('-started_at')

        activity_log = []
        for attempt in attempts:
            violations = TabViolation.objects.filter(attempt=attempt).order_by('violated_at')
            activity_log.append({
                'attempt': attempt,
                'exam_title': attempt.exam.title,
                'started_at': attempt.started_at,
                'submitted_at': attempt.submitted_at,
                'status': attempt.get_status_display(),
                'is_flagged': attempt.is_flagged,
                'flag_reason': attempt.flag_reason,
                'auto_submitted': attempt.auto_submitted,
                'violation_count': violations.count(),
                'violations': violations,
            })

        context = {
            'student': student,
            'activity_log': activity_log,
            'page_title': 'Activity Log',
        }

        return render(request, 'users/student_activity_log.html', context)
