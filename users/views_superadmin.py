"""
Super Admin views for system management.
Superadmin is a Django User with is_superuser=True and NO Teacher profile.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib import messages
from django.http import JsonResponse
from django.db import IntegrityError
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from functools import wraps
from django.utils.decorators import method_decorator
import json

from .models import (
    Teacher, Student, Class, AdminNotification,
    GradeLevel, Strand, Section, Subject, Quarter,
)
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

        # Daily attempts for chart (last 7 days)
        daily_attempts = []
        daily_labels = []
        for i in range(6, -1, -1):
            day = (now - timedelta(days=i)).date()
            count = Attempt.objects.filter(
                submitted_at__date=day
            ).count()
            daily_labels.append(day.strftime('%b %d'))
            daily_attempts.append(count)

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
            'daily_labels': json.dumps(daily_labels),
            'daily_attempts': json.dumps(daily_attempts),
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


class SuperAdminEditTeacherView(View):
    """Edit a teacher's profile fields (name, email, department). Username is immutable."""

    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, teacher_id):
        teacher = get_object_or_404(Teacher.objects.select_related('user'), user_id=teacher_id)

        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        department = request.POST.get('department', '').strip()

        errors = []
        if not first_name:
            errors.append('First name is required.')
        if email and User.objects.filter(email=email).exclude(pk=teacher.user_id).exists():
            errors.append('Another user already uses this email.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('superadmin_teachers')

        teacher.user.first_name = first_name
        teacher.user.last_name = last_name
        teacher.user.email = email
        teacher.user.save(update_fields=['first_name', 'last_name', 'email'])

        teacher.department = department or None
        teacher.save(update_fields=['department', 'updated_at'])

        messages.success(request, f'Teacher "{teacher.user.get_full_name() or teacher.user.username}" updated.')
        return redirect('superadmin_teachers')


class SuperAdminTeacherDetailView(View):
    """
    Detail view for a single teacher: profile, classes, exams, and the
    student accounts they have created. Students are scoped to the teacher
    who created them; this view is the superadmin's window into that
    private scope.
    """

    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, teacher_id):
        teacher = get_object_or_404(
            Teacher.objects.select_related('user'),
            user_id=teacher_id,
        )

        # Avatar: first letter of first name + first letter of last name.
        # Falls back to first 2 chars of username, then "?".
        first = (teacher.user.first_name or '').strip()
        last = (teacher.user.last_name or '').strip()
        if first or last:
            initials = (first[:1] + last[:1]).upper() or '?'
        else:
            initials = (teacher.user.username[:2] or '?').upper()
        # Pick a stable color class based on the first letter (a-h).
        avatar_letter = (first[:1] or teacher.user.username[:1] or 'a').lower()
        if avatar_letter not in 'abcdefgh':
            avatar_letter = 'a'
        avatar_class = f'td-avatar-{avatar_letter}'

        search = request.GET.get('search', '').strip()
        class_filter = request.GET.get('class', '').strip()
        sort = request.GET.get('sort', 'created')
        direction = request.GET.get('dir', 'desc')

        # Classes owned by this teacher (for the class filter dropdown + summary card)
        all_classes = list(
            Class.objects
            .filter(teacher=teacher)
            .order_by('grade_level', 'strand', 'section')
        )
        classes_qs = (
            Class.objects
            .filter(teacher=teacher)
            .annotate(student_count=Count('students', distinct=True))
            .order_by('grade_level', 'strand', 'section')
        )
        class_total = classes_qs.count()

        # Exams authored by this teacher
        exams = (
            Exam.objects
            .filter(created_by=teacher)
            .annotate(attempt_count=Count('attempts', distinct=True))
            .order_by('-created_at')[:8]
        )
        exam_total = Exam.objects.filter(created_by=teacher).count()

        # Students CREATED by this teacher (the private scope)
        from django.db.models import Max
        students_qs = (
            Student.objects
            .filter(created_by=teacher)
            .select_related('class_assigned')
            .annotate(
                attempt_count=Count('attempts', distinct=True),
                last_activity=Max('attempts__started_at'),
            )
        )

        if search:
            students_qs = students_qs.filter(
                Q(school_id__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        if class_filter:
            if class_filter == 'unassigned':
                students_qs = students_qs.filter(class_assigned__isnull=True)
            elif class_filter.isdigit():
                students_qs = students_qs.filter(class_assigned_id=int(class_filter))

        # Sorting
        sort_options = {
            'name': ('last_name', 'first_name'),
            'created': ('-created_at',),
            'attempts': ('-attempt_count', '-created_at'),
            'last_activity': ('-last_activity', '-created_at'),
            'class': ('class_assigned__grade_level', 'class_assigned__strand', 'class_assigned__section'),
        }
        order_by = sort_options.get(sort, sort_options['created'])
        if sort == 'name' and direction == 'desc':
            order_by = ('-last_name', '-first_name')
        elif sort == 'created' and direction == 'asc':
            order_by = ('created_at',)
        elif sort == 'attempts' and direction == 'asc':
            order_by = ('attempt_count', '-created_at')
        elif sort == 'last_activity' and direction == 'asc':
            order_by = ('last_activity', '-created_at')
        students_qs = students_qs.order_by(*order_by)

        from django.core.paginator import Paginator
        paginator = Paginator(students_qs, 20)
        page = request.GET.get('page', 1)
        students_page = paginator.get_page(page)

        # Total attempts across this teacher's students (for the stats tile)
        from attempts.models import Attempt
        total_attempts = Attempt.objects.filter(student__created_by=teacher).count()

        return render(request, 'superadmin/teacher_detail.html', {
            'teacher': teacher,
            'initials': initials,
            'avatar_class': avatar_class,
            'classes': classes_qs,
            'all_classes': all_classes,
            'exams': exams,
            'students': students_page,
            'search': search,
            'class_filter': class_filter,
            'sort': sort,
            'direction': direction,
            'student_total': paginator.count,
            'class_total': class_total,
            'exam_total': exam_total,
            'total_attempts': total_attempts,
        })


class SuperAdminToggleTeacherActiveView(View):
    """Enable or disable a teacher account. Disabling also kills any active sessions."""

    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, teacher_id):
        teacher = get_object_or_404(Teacher.objects.select_related('user'), user_id=teacher_id)

        if teacher.user_id == request.user.id:
            messages.error(request, 'You cannot disable your own account.')
            return redirect('superadmin_teachers')

        teacher.user.is_active = not teacher.user.is_active
        teacher.user.save(update_fields=['is_active'])

        kicked = 0
        if not teacher.user.is_active:
            kicked = _kill_user_sessions(teacher.user_id)

        state = 'enabled' if teacher.user.is_active else 'disabled'
        suffix = f' ({kicked} active session{"s" if kicked != 1 else ""} ended)' if kicked else ''
        messages.success(
            request,
            f'Teacher "{teacher.user.get_full_name() or teacher.user.username}" {state}{suffix}.'
        )
        return redirect('superadmin_teachers')


class SuperAdminStudentsView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        search = request.GET.get('search', '').strip()
        students = (
            Student.objects
            .select_related('class_assigned', 'created_by__user')
            .annotate(attempt_count=Count('attempts'))
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


class SuperAdminNotificationsView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        notifications = AdminNotification.objects.all()
        unread_count = notifications.filter(is_read=False).count()
        return render(request, 'superadmin/notifications.html', {
            'notifications': notifications,
            'unread_count': unread_count,
        })

    def post(self, request):
        action = request.POST.get('action')
        notif_id = request.POST.get('notification_id')

        if action == 'mark_read' and notif_id:
            notif = get_object_or_404(AdminNotification, id=notif_id)
            notif.is_read = True
            notif.save()
        elif action == 'mark_all_read':
            AdminNotification.objects.filter(is_read=False).update(is_read=True)
        elif action == 'delete' and notif_id:
            notif = get_object_or_404(AdminNotification, id=notif_id)
            notif.delete()
            messages.success(request, 'Notification deleted.')

        return redirect('superadmin_notifications')


class SuperAdminCreateTeacherView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        notif_id = request.POST.get('notification_id')

        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        if not email:
            errors.append('Email is required.')
        if User.objects.filter(email=email).exists():
            errors.append('A user with this email already exists.')
        if not password or len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != password_confirm:
            errors.append('Passwords do not match.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('superadmin_notifications')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        Teacher.objects.create(user=user)

        if notif_id:
            AdminNotification.objects.filter(id=notif_id).update(is_read=True)

        messages.success(request, f'Teacher account created for {first_name} {last_name} ({username}).')
        return redirect('superadmin_notifications')


# ---------------------------------------------------------------------------
# Active sessions
# ---------------------------------------------------------------------------

def _decode_session(session):
    """Return the decoded session dict or {} if it cannot be decoded."""
    try:
        return session.get_decoded()
    except Exception:
        return {}


def _kill_user_sessions(user_id):
    """Delete all active Django auth sessions for a given user id. Returns count."""
    now = timezone.now()
    killed = 0
    for session in Session.objects.filter(expire_date__gt=now):
        data = _decode_session(session)
        if str(data.get('_auth_user_id') or '') == str(user_id):
            session.delete()
            killed += 1
    return killed


def _kill_student_sessions(student_id):
    """Delete all active sessions for a given student id. Returns count."""
    now = timezone.now()
    killed = 0
    for session in Session.objects.filter(expire_date__gt=now):
        data = _decode_session(session)
        if str(data.get('student_id') or '') == str(student_id):
            session.delete()
            killed += 1
    return killed


class SuperAdminSessionsView(View):
    """List active sessions across teachers, students, and the superadmin, with force-logout."""

    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        now = timezone.now()
        raw_sessions = Session.objects.filter(expire_date__gt=now).order_by('-expire_date')

        # Pre-fetch users and students referenced by sessions in batches to avoid N+1.
        decoded_rows = []
        user_ids = set()
        student_ids = set()
        for session in raw_sessions:
            data = _decode_session(session)
            decoded_rows.append((session, data))
            if data.get('_auth_user_id'):
                try:
                    user_ids.add(int(data['_auth_user_id']))
                except (TypeError, ValueError):
                    pass
            if data.get('student_id'):
                try:
                    student_ids.add(int(data['student_id']))
                except (TypeError, ValueError):
                    pass

        users_by_id = {u.id: u for u in User.objects.filter(id__in=user_ids).select_related('teacher_profile')}
        students_by_id = {s.id: s for s in Student.objects.filter(id__in=student_ids)}

        rows = []
        for session, data in decoded_rows:
            row = {
                'session_key': session.session_key,
                'expires': session.expire_date,
                'is_self': False,
                'kind': 'Unknown',
                'name': '(unidentified session)',
                'detail': '',
            }

            user_id = data.get('_auth_user_id')
            student_id = data.get('student_id')

            if user_id:
                try:
                    user_id_int = int(user_id)
                except (TypeError, ValueError):
                    user_id_int = None
                user = users_by_id.get(user_id_int) if user_id_int is not None else None
                if user is not None:
                    if user.is_superuser and not hasattr(user, 'teacher_profile'):
                        row['kind'] = 'Superadmin'
                    elif hasattr(user, 'teacher_profile'):
                        row['kind'] = 'Teacher'
                    else:
                        row['kind'] = 'Staff'
                    row['name'] = user.get_full_name() or user.username
                    row['detail'] = user.username
                    row['is_self'] = (user.id == request.user.id)
            elif student_id:
                try:
                    student_id_int = int(student_id)
                except (TypeError, ValueError):
                    student_id_int = None
                student = students_by_id.get(student_id_int) if student_id_int is not None else None
                if student is not None:
                    row['kind'] = 'Student'
                    row['name'] = student.get_full_name()
                    row['detail'] = student.school_id

            rows.append(row)

        return render(request, 'superadmin/sessions.html', {
            'rows': rows,
            'total': len(rows),
        })

    def post(self, request):
        action = request.POST.get('action')

        if action == 'kick':
            session_key = request.POST.get('session_key', '').strip()
            if not session_key:
                messages.error(request, 'Missing session identifier.')
                return redirect('superadmin_sessions')

            try:
                session = Session.objects.get(pk=session_key)
            except Session.DoesNotExist:
                messages.error(request, 'Session already expired or not found.')
                return redirect('superadmin_sessions')

            data = _decode_session(session)
            try:
                user_id_in_session = int(data.get('_auth_user_id') or 0)
            except (TypeError, ValueError):
                user_id_in_session = 0

            if user_id_in_session == request.user.id:
                messages.error(request, 'You cannot end your own session here. Use Logout instead.')
                return redirect('superadmin_sessions')

            session.delete()
            messages.success(request, 'Session ended.')
            return redirect('superadmin_sessions')

        if action == 'kick_all':
            now = timezone.now()
            killed = 0
            for session in Session.objects.filter(expire_date__gt=now):
                data = _decode_session(session)
                try:
                    user_id_in_session = int(data.get('_auth_user_id') or 0)
                except (TypeError, ValueError):
                    user_id_in_session = 0
                if user_id_in_session == request.user.id:
                    continue
                session.delete()
                killed += 1
            messages.success(request, f'Ended {killed} session{"s" if killed != 1 else ""}.')
            return redirect('superadmin_sessions')

        messages.error(request, 'Unknown action.')
        return redirect('superadmin_sessions')


# ---------------------------------------------------------------------------
# Lookup data CRUD (Grade Levels, Strands, Sections, Subjects, Quarters)
# ---------------------------------------------------------------------------

LOOKUP_MODELS = {
    'grade_level': {
        'model': GradeLevel,
        'label': 'Grade Levels',
        'has_order': True,
        'usage': lambda name: Class.objects.filter(grade_level=name).count(),
        'usage_label': 'classes',
    },
    'strand': {
        'model': Strand,
        'label': 'Strands',
        'has_order': False,
        'usage': lambda name: Class.objects.filter(strand=name).count(),
        'usage_label': 'classes',
    },
    'section': {
        'model': Section,
        'label': 'Sections',
        'has_order': False,
        'usage': lambda name: Class.objects.filter(section=name).count(),
        'usage_label': 'classes',
    },
    'subject': {
        'model': Subject,
        'label': 'Subjects',
        'has_order': False,
        'usage': lambda name: Exam.objects.filter(subject=name).count(),
        'usage_label': 'exams',
    },
    'quarter': {
        'model': Quarter,
        'label': 'Quarters',
        'has_order': True,
        'usage': lambda name: Exam.objects.filter(quarter__name=name).count(),
        'usage_label': 'exams',
    },
}


class SuperAdminLookupsView(View):
    """Create, rename, and delete entries in lookup tables used across the system."""

    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        groups = []
        for key, meta in LOOKUP_MODELS.items():
            items = list(meta['model'].objects.all())
            groups.append({
                'key': key,
                'label': meta['label'],
                'has_order': meta['has_order'],
                'items': items,
            })
        return render(request, 'superadmin/lookups.html', {'groups': groups})

    def post(self, request):
        kind = request.POST.get('kind', '').strip()
        action = request.POST.get('action', '').strip()
        meta = LOOKUP_MODELS.get(kind)
        if not meta:
            messages.error(request, 'Unknown lookup type.')
            return redirect('superadmin_lookups')

        Model = meta['model']

        if action == 'create':
            name = request.POST.get('name', '').strip()
            order_raw = request.POST.get('order', '').strip()
            if not name:
                messages.error(request, 'Name is required.')
                return redirect('superadmin_lookups')

            fields = {'name': name}
            if meta['has_order']:
                try:
                    fields['order'] = int(order_raw) if order_raw else 0
                except ValueError:
                    fields['order'] = 0

            try:
                Model.objects.create(**fields)
                messages.success(request, f'{meta["label"][:-1]} "{name}" added.')
            except IntegrityError:
                messages.error(request, f'"{name}" already exists.')
            return redirect('superadmin_lookups')

        if action == 'edit':
            item_id = request.POST.get('item_id')
            name = request.POST.get('name', '').strip()
            order_raw = request.POST.get('order', '').strip()
            if not name:
                messages.error(request, 'Name is required.')
                return redirect('superadmin_lookups')

            item = get_object_or_404(Model, pk=item_id)
            old_name = item.name
            item.name = name
            update_fields = ['name']
            if meta['has_order']:
                try:
                    item.order = int(order_raw) if order_raw else 0
                    update_fields.append('order')
                except ValueError:
                    pass

            try:
                item.save(update_fields=update_fields)
            except IntegrityError:
                messages.error(request, f'"{name}" already exists.')
                return redirect('superadmin_lookups')

            # If the name changed and this lookup is referenced by string in other
            # tables, propagate the rename so existing data stays consistent.
            if old_name != name and kind in ('grade_level', 'strand', 'section'):
                Class.objects.filter(**{kind: old_name}).update(**{kind: name})
            elif old_name != name and kind == 'subject':
                Exam.objects.filter(subject=old_name).update(subject=name)

            messages.success(request, f'{meta["label"][:-1]} renamed to "{name}".')
            return redirect('superadmin_lookups')

        if action == 'delete':
            item_id = request.POST.get('item_id')
            item = get_object_or_404(Model, pk=item_id)
            usage_count = meta['usage'](item.name)
            if usage_count > 0:
                messages.error(
                    request,
                    f'Cannot delete "{item.name}": still used by {usage_count} {meta["usage_label"]}.'
                )
                return redirect('superadmin_lookups')

            item.delete()
            messages.success(request, f'{meta["label"][:-1]} "{item.name}" deleted.')
            return redirect('superadmin_lookups')

        messages.error(request, 'Unknown action.')
        return redirect('superadmin_lookups')
