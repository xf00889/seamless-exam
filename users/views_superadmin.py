"""
Super Admin views for system management.
Superadmin is a Django User with is_superuser=True and NO Teacher profile.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from functools import wraps
from django.utils.decorators import method_decorator

from .models import Teacher, Student, Class
from exams.models import Exam
from attempts.models import Attempt


def superadmin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('superadmin_login')
        if not request.user.is_superuser:
            return redirect('superadmin_login')
        if Teacher.objects.filter(user=request.user).exists():
            messages.error(request, 'Teachers cannot access the superadmin panel.')
            return redirect('teacher_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


class SuperAdminLoginView(View):
    def get(self, request):
        if request.user.is_authenticated and request.user.is_superuser:
            if not Teacher.objects.filter(user=request.user).exists():
                return redirect('superadmin_dashboard')
        return render(request, 'superadmin/login.html')

    def post(self, request):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user and user.is_superuser:
            if Teacher.objects.filter(user=user).exists():
                messages.error(request, 'Teachers cannot access the superadmin panel.')
                return render(request, 'superadmin/login.html')
            login(request, user)
            return redirect('superadmin_dashboard')

        messages.error(request, 'Invalid credentials or insufficient privileges.')
        return render(request, 'superadmin/login.html')


class SuperAdminLogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('superadmin_login')


class SuperAdminDashboardView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)

        total_teachers = Teacher.objects.count()
        total_students = Student.objects.count()
        total_exams = Exam.objects.count()
        total_attempts = Attempt.objects.count()
        total_classes = Class.objects.count()

        recent_attempts = Attempt.objects.filter(
            submitted_at__gte=thirty_days_ago
        ).count()

        recent_students = Student.objects.filter(
            created_at__gte=seven_days_ago
        ).count()

        graded_attempts = Attempt.objects.filter(status='graded')
        avg_score = graded_attempts.aggregate(
            avg=Avg('total_score')
        )['avg'] or 0

        active_exams = Exam.objects.filter(is_active=True).count()

        recent_activity = Attempt.objects.select_related(
            'exam'
        ).order_by('-submitted_at')[:10]

        context = {
            'total_teachers': total_teachers,
            'total_students': total_students,
            'total_exams': total_exams,
            'total_attempts': total_attempts,
            'total_classes': total_classes,
            'recent_attempts': recent_attempts,
            'recent_students': recent_students,
            'avg_score': avg_score,
            'active_exams': active_exams,
            'recent_activity': recent_activity,
        }
        return render(request, 'superadmin/dashboard.html', context)


class SuperAdminTeachersView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        teachers = Teacher.objects.select_related('user').annotate(
            class_count=Count('classes'),
            exam_count=Count('exams', distinct=True),
        ).order_by('-created_at')
        return render(request, 'superadmin/teachers.html', {'teachers': teachers})


class SuperAdminStudentsView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        search = request.GET.get('search', '').strip()
        students = Student.objects.select_related('class_assigned').annotate(
            attempt_count=Count('attempts'),
        )
        if search:
            students = students.filter(
                Q(school_id__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        students = students.order_by('-created_at')

        from django.core.paginator import Paginator
        paginator = Paginator(students, 25)
        page = request.GET.get('page', 1)
        students_page = paginator.get_page(page)

        return render(request, 'superadmin/students.html', {
            'students': students_page,
            'search': search,
        })


class SuperAdminResetPasswordView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        user_type = request.POST.get('user_type')
        user_id = request.POST.get('user_id')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not new_password or len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return redirect(request.META.get('HTTP_REFERER', 'superadmin_dashboard'))

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect(request.META.get('HTTP_REFERER', 'superadmin_dashboard'))

        if user_type == 'teacher':
            teacher = get_object_or_404(Teacher, user_id=user_id)
            teacher.user.set_password(new_password)
            teacher.user.save()
            messages.success(request, f'Password reset for teacher: {teacher.user.get_full_name()}')
            return redirect('superadmin_teachers')

        elif user_type == 'student':
            student = get_object_or_404(Student, id=user_id)
            student.set_password(new_password)
            student.save()
            messages.success(request, f'Password reset for student: {student.get_full_name()}')
            return redirect('superadmin_students')

        messages.error(request, 'Invalid user type.')
        return redirect('superadmin_dashboard')


class SuperAdminDeleteUserView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        user_type = request.POST.get('user_type')
        user_id = request.POST.get('user_id')
        admin_password = request.POST.get('admin_password')

        if not request.user.check_password(admin_password):
            messages.error(request, 'Invalid admin password.')
            return redirect(request.META.get('HTTP_REFERER', 'superadmin_dashboard'))

        if user_type == 'teacher':
            teacher = get_object_or_404(Teacher, user_id=user_id)
            name = teacher.user.get_full_name()
            teacher.user.delete()
            messages.success(request, f'Teacher "{name}" deleted.')
            return redirect('superadmin_teachers')

        elif user_type == 'student':
            student = get_object_or_404(Student, id=user_id)
            name = student.get_full_name()
            student.delete()
            messages.success(request, f'Student "{name}" deleted.')
            return redirect('superadmin_students')

        messages.error(request, 'Invalid user type.')
        return redirect('superadmin_dashboard')


class SuperAdminCreateView(View):
    """Create a superadmin account. Only accessible when no superadmin exists."""

    def get(self, request):
        has_superadmin = User.objects.filter(
            is_superuser=True
        ).exclude(
            teacher_profile__isnull=False
        ).exists()
        if has_superadmin:
            return redirect('superadmin_login')
        return render(request, 'superadmin/create.html')

    def post(self, request):
        has_superadmin = User.objects.filter(
            is_superuser=True
        ).exclude(
            teacher_profile__isnull=False
        ).exists()
        if has_superadmin:
            messages.error(request, 'A superadmin account already exists.')
            return redirect('superadmin_login')

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        if not password or len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != password_confirm:
            errors.append('Passwords do not match.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'superadmin/create.html', {'username': username})

        User.objects.create_superuser(
            username=username,
            password=password,
            email='',
            first_name='Super',
            last_name='Admin',
        )
        messages.success(request, 'Superadmin account created. Please log in.')
        return redirect('superadmin_login')
