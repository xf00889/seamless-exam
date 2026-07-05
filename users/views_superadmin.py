from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Count
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import timedelta
from functools import wraps

from .models import School, SchoolAdmin, Teacher, Student, Class, AdminNotification


def superadmin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('superadmin_login')
        return view_func(request, *args, **kwargs)
    return wrapper


class SuperAdminLoginView(View):
    def get(self, request):
        if request.user.is_authenticated and request.user.is_superuser:
            return redirect('superadmin_dashboard')
        return render(request, 'superadmin/login.html')

    def post(self, request):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user and user.is_superuser:
            login(request, user)
            return redirect('superadmin_dashboard')

        messages.error(request, 'Invalid credentials or insufficient privileges.')
        return render(request, 'superadmin/login.html')


class SuperAdminLogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('superadmin_login')


class SuperAdminCreateView(View):
    def get(self, request):
        has_superadmin = User.objects.filter(is_superuser=True).exists()
        if has_superadmin:
            return redirect('superadmin_login')
        return render(request, 'superadmin/create.html')

    def post(self, request):
        has_superadmin = User.objects.filter(is_superuser=True).exists()
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
            username=username, password=password, email='',
            first_name='Super', last_name='Admin',
        )
        messages.success(request, 'Superadmin account created. Please log in.')
        return redirect('superadmin_login')


class SuperAdminDashboardView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        schools = School.objects.annotate(
            teacher_count=Count('teachers', distinct=True),
            student_count=Count('students', distinct=True),
            class_count=Count('classes', distinct=True),
        ).order_by('name')

        total_schools = schools.count()
        total_teachers = Teacher.objects.count()
        total_students = Student.objects.count()

        return render(request, 'superadmin/dashboard.html', {
            'schools': schools,
            'total_schools': total_schools,
            'total_teachers': total_teachers,
            'total_students': total_students,
        })


class SuperAdminCreateSchoolView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, 'superadmin/create_school.html', {
            'page_title': 'Create School',
        })

    def post(self, request):
        name = request.POST.get('name', '').strip()
        address = request.POST.get('address', '').strip()
        if not name:
            messages.error(request, 'School name is required.')
            return redirect('superadmin_dashboard')
        try:
            School.objects.create(name=name, address=address)
            messages.success(request, f'School "{name}" created.')
        except IntegrityError:
            messages.error(request, f'School "{name}" already exists.')
        return redirect('superadmin_dashboard')


class SuperAdminCreateSchoolAdminView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        schools = School.objects.all().order_by('name')
        return render(request, 'superadmin/create_school_admin.html', {
            'schools': schools,
            'page_title': 'Create School Admin',
        })

    def post(self, request):
        school_id = request.POST.get('school_id')
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        school = get_object_or_404(School, pk=school_id)

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
            return redirect('superadmin_dashboard')

        user = User.objects.create_user(
            username=username, password=password,
            first_name=request.POST.get('first_name', '').strip(),
            last_name=request.POST.get('last_name', '').strip(),
            email=request.POST.get('email', '').strip(),
        )
        SchoolAdmin.objects.create(user=user, school=school)
        messages.success(request, f'School admin "{username}" created for {school.name}.')
        return redirect('superadmin_dashboard')


class SuperAdminEditSchoolView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, school_id):
        school = get_object_or_404(School, pk=school_id)
        name = request.POST.get('name', '').strip()
        address = request.POST.get('address', '').strip()
        if name:
            school.name = name
        school.address = address
        try:
            school.save()
            messages.success(request, f'School updated.')
        except IntegrityError:
            messages.error(request, f'School with this name already exists.')
        return redirect('superadmin_dashboard')


class SuperAdminDeleteSchoolView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, school_id):
        school = get_object_or_404(School, pk=school_id)
        admin_password = request.POST.get('admin_password', '')
        if not request.user.check_password(admin_password):
            messages.error(request, 'Invalid admin password.')
            return redirect('superadmin_dashboard')
        school.delete()
        messages.success(request, f'School "{school.name}" deleted.')
        return redirect('superadmin_dashboard')


class SuperAdminDeleteSchoolAdminView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, admin_id):
        school_admin = get_object_or_404(
            SchoolAdmin.objects.select_related('user', 'school'),
            pk=admin_id,
        )
        admin_password = request.POST.get('admin_password', '')
        if not request.user.check_password(admin_password):
            messages.error(request, 'Invalid admin password.')
            return redirect('superadmin_manage')
        username = school_admin.user.username
        school_name = school_admin.school.name
        school_admin.user.delete()
        messages.success(request, f'School admin "{username}" for "{school_name}" deleted.')
        return redirect('superadmin_manage')


class SuperAdminManageView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        schools = School.objects.annotate(
            teacher_count=Count('teachers', distinct=True),
            student_count=Count('students', distinct=True),
            class_count=Count('classes', distinct=True),
        ).order_by('name')

        school_admins = SchoolAdmin.objects.select_related(
            'user', 'school'
        ).order_by('school__name', 'user__username')

        total_classes = Class.objects.count()
        total_students = Student.objects.count()

        return render(request, 'superadmin/manage.html', {
            'schools': schools,
            'school_admins': school_admins,
            'total_classes': total_classes,
            'total_students': total_students,
        })


class SuperAdminSchoolAdminDetailView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, admin_id):
        school_admin = get_object_or_404(
            SchoolAdmin.objects.select_related('user', 'school'),
            pk=admin_id,
        )
        school = school_admin.school
        school_data = School.objects.annotate(
            teacher_count=Count('teachers', distinct=True),
            student_count=Count('students', distinct=True),
            class_count=Count('classes', distinct=True),
        ).get(pk=school.pk)

        return render(request, 'superadmin/school_admin_detail.html', {
            'sa': school_admin,
            'school': school_data,
        })


class SuperAdminSessionsView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        now = timezone.now()
        raw_sessions = Session.objects.filter(expire_date__gt=now).order_by('-expire_date')

        rows = []
        for session in raw_sessions:
            data = session.get_decoded()
            row = {'session_key': session.session_key, 'expires': session.expire_date, 'is_self': False, 'kind': 'Unknown', 'name': '', 'detail': ''}
            user_id = data.get('_auth_user_id')
            student_id = data.get('student_id')
            if user_id:
                try:
                    user = User.objects.get(pk=int(user_id))
                    if hasattr(user, 'school_admin_profile'):
                        row['kind'] = 'School Admin'
                        row['detail'] = user.school_admin_profile.school.name
                    elif hasattr(user, 'teacher_profile'):
                        row['kind'] = 'Teacher'
                        row['detail'] = user.teacher_profile.school.name
                    elif user.is_superuser:
                        row['kind'] = 'Superadmin'
                    else:
                        row['kind'] = 'Staff'
                    row['name'] = user.get_full_name() or user.username
                    row['is_self'] = (user.id == request.user.id)
                except (User.DoesNotExist, ValueError, TypeError):
                    pass
            elif student_id:
                try:
                    from .models import Student
                    student = Student.objects.get(pk=int(student_id))
                    row['kind'] = 'Student'
                    row['name'] = student.get_full_name()
                    row['detail'] = student.student_id
                except (Student.DoesNotExist, ValueError, TypeError):
                    pass
            rows.append(row)

        return render(request, 'superadmin/sessions.html', {'rows': rows, 'total': len(rows)})

    def post(self, request):
        action = request.POST.get('action')
        if action == 'kick':
            session_key = request.POST.get('session_key', '').strip()
            try:
                session = Session.objects.get(pk=session_key)
            except Session.DoesNotExist:
                messages.error(request, 'Session not found.')
                return redirect('superadmin_sessions')
            session.delete()
            messages.success(request, 'Session ended.')
            return redirect('superadmin_sessions')
        if action == 'kick_all':
            now = timezone.now()
            killed = 0
            for session in Session.objects.filter(expire_date__gt=now):
                session.delete()
                killed += 1
            messages.success(request, f'Ended {killed} session{"s" if killed != 1 else ""}.')
            return redirect('superadmin_sessions')
        messages.error(request, 'Unknown action.')
        return redirect('superadmin_sessions')


class SuperAdminNotificationsView(View):
    @method_decorator(superadmin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        notifications = AdminNotification.objects.all()
        unread_count = notifications.filter(is_read=False).count()
        return render(request, 'superadmin/notifications.html', {
            'notifications': notifications, 'unread_count': unread_count,
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
