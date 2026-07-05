from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Count, Avg, Q
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import timedelta
from functools import wraps
import json

from .models import (
    Teacher, Student, Class, School, SchoolAdmin,
    GradeLevel, Strand, Section, Subject, Quarter,
)
from exams.models import Exam
from attempts.models import Attempt


def school_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        try:
            school_admin = SchoolAdmin.objects.get(user=request.user)
            request.current_school = school_admin.school
            request.current_school_admin = school_admin
        except SchoolAdmin.DoesNotExist:
            messages.error(request, 'Access denied.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


class SchoolAdminDashboardView(View):
    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        school = request.current_school
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        total_teachers = Teacher.objects.filter(school=school).count()
        total_students = Student.objects.filter(school=school).count()
        total_exams = Exam.objects.filter(created_by__school=school).count()
        total_attempts = Attempt.objects.filter(student__school=school).count()
        total_classes = Class.objects.filter(school=school).count()

        recent_attempts = Attempt.objects.filter(
            student__school=school, submitted_at__gte=thirty_days_ago
        ).count()

        recent_students = Student.objects.filter(
            school=school, created_at__gte=now - timedelta(days=7)
        ).count()

        active_exams = Exam.objects.filter(
            created_by__school=school, is_active=True
        ).count()

        context = {
            'school': school,
            'total_teachers': total_teachers,
            'total_students': total_students,
            'total_exams': total_exams,
            'total_attempts': total_attempts,
            'total_classes': total_classes,
            'recent_attempts': recent_attempts,
            'recent_students': recent_students,
            'active_exams': active_exams,
        }
        return render(request, 'school_admin/dashboard.html', context)


class SchoolAdminTeachersView(View):
    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        school = request.current_school
        teachers = Teacher.objects.filter(school=school).select_related('user').annotate(
            class_count=Count('classes', distinct=True),
            exam_count=Count('exams', distinct=True),
        ).order_by('-created_at')
        return render(request, 'school_admin/teachers.html', {'teachers': teachers, 'school': school})


class SchoolAdminCreateTeacherView(View):
    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, 'school_admin/create_teacher.html', {
            'school': request.current_school,
        })

    def post(self, request):
        school = request.current_school
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        if not email:
            errors.append('Email is required.')
        if not password or len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != password_confirm:
            errors.append('Passwords do not match.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'school_admin/create_teacher.html', {
                'school': school, 'username': username, 'email': email,
                'first_name': first_name, 'last_name': last_name,
            })

        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name,
        )
        Teacher.objects.create(user=user, school=school)
        messages.success(request, f'Teacher account created for {first_name} {last_name} ({username}).')
        return redirect('school_admin_teachers')


class SchoolAdminEditTeacherView(View):
    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, teacher_id):
        school = request.current_school
        teacher = get_object_or_404(
            Teacher.objects.select_related('user'), user_id=teacher_id, school=school
        )
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
            return redirect('school_admin_teachers')

        teacher.user.first_name = first_name
        teacher.user.last_name = last_name
        teacher.user.email = email
        teacher.user.save(update_fields=['first_name', 'last_name', 'email'])
        teacher.department = department or None
        teacher.save(update_fields=['department', 'updated_at'])

        messages.success(request, f'Teacher "{teacher.user.get_full_name() or teacher.user.username}" updated.')
        return redirect('school_admin_teachers')


class SchoolAdminTeacherDetailView(View):
    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, teacher_id):
        school = request.current_school
        teacher = get_object_or_404(
            Teacher.objects.select_related('user'), user_id=teacher_id, school=school
        )
        classes = Class.objects.filter(school=school, teachers=teacher).annotate(
            student_count=Count('students', distinct=True)
        ).order_by('grade_level__name', 'strand__name', 'section__name')
        exams = Exam.objects.filter(created_by=teacher).annotate(
            attempt_count=Count('attempts', distinct=True)
        ).order_by('-created_at')[:8]

        return render(request, 'school_admin/teacher_detail.html', {
            'teacher': teacher, 'classes': classes, 'exams': exams, 'school': school,
        })


class SchoolAdminToggleTeacherActiveView(View):
    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, teacher_id):
        school = request.current_school
        teacher = get_object_or_404(
            Teacher.objects.select_related('user'), user_id=teacher_id, school=school
        )
        if teacher.user_id == request.user.id:
            messages.error(request, 'You cannot disable your own account.')
            return redirect('school_admin_teachers')
        teacher.user.is_active = not teacher.user.is_active
        teacher.user.save(update_fields=['is_active'])
        state = 'enabled' if teacher.user.is_active else 'disabled'
        messages.success(request, f'Teacher "{teacher.user.get_full_name() or teacher.user.username}" {state}.')
        return redirect('school_admin_teachers')


class SchoolAdminStudentsView(View):
    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        school = request.current_school
        search = request.GET.get('search', '').strip()
        students = Student.objects.filter(school=school).select_related(
            'class_assigned', 'created_by'
        ).annotate(attempt_count=Count('attempts'))
        if search:
            students = students.filter(
                Q(student_id__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        students = students.order_by('-created_at')
        from django.core.paginator import Paginator
        paginator = Paginator(students, 25)
        page = request.GET.get('page', 1)
        students_page = paginator.get_page(page)
        return render(request, 'school_admin/students.html', {
            'students': students_page, 'school': school,
        })


class SchoolAdminStudentDetailView(View):
    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, student_id):
        school = request.current_school
        student = get_object_or_404(
            Student.objects.select_related('class_assigned', 'created_by'),
            id=student_id, school=school,
        )
        attempts = Attempt.objects.filter(student=student).select_related('exam').order_by('-started_at')[:20]
        return render(request, 'school_admin/student_detail.html', {
            'student': student, 'attempts': attempts, 'school': school,
        })


class SchoolAdminResetPasswordView(View):
    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        school = request.current_school
        user_type = request.POST.get('user_type')
        user_id = request.POST.get('user_id')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not new_password or len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return redirect(request.META.get('HTTP_REFERER', 'school_admin_dashboard'))
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect(request.META.get('HTTP_REFERER', 'school_admin_dashboard'))

        if user_type == 'teacher':
            teacher = get_object_or_404(Teacher, user_id=user_id, school=school)
            teacher.user.set_password(new_password)
            teacher.user.save()
            messages.success(request, f'Password reset for teacher: {teacher.user.get_full_name()}')
            return redirect('school_admin_teachers')
        elif user_type == 'student':
            student = get_object_or_404(Student, id=user_id, school=school)
            student.set_password(new_password)
            student.save()
            messages.success(request, f'Password reset for student: {student.get_full_name()}')
            return redirect('school_admin_students')
        messages.error(request, 'Invalid user type.')
        return redirect('school_admin_dashboard')


class SchoolAdminDeleteUserView(View):
    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        school = request.current_school
        user_type = request.POST.get('user_type')
        user_id = request.POST.get('user_id')
        admin_password = request.POST.get('admin_password')

        if not request.user.check_password(admin_password):
            messages.error(request, 'Invalid admin password.')
            return redirect(request.META.get('HTTP_REFERER', 'school_admin_dashboard'))

        if user_type == 'teacher':
            teacher = get_object_or_404(Teacher, user_id=user_id, school=school)
            name = teacher.user.get_full_name()
            teacher.user.delete()
            messages.success(request, f'Teacher "{name}" deleted.')
            return redirect('school_admin_teachers')
        elif user_type == 'student':
            student = get_object_or_404(Student, id=user_id, school=school)
            name = student.get_full_name()
            student.delete()
            messages.success(request, f'Student "{name}" deleted.')
            return redirect('school_admin_students')
        messages.error(request, 'Invalid user type.')
        return redirect('school_admin_dashboard')


class SchoolAdminClassesView(View):
    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        school = request.current_school
        classes = Class.objects.filter(school=school).select_related(
            'grade_level', 'strand', 'section'
        ).prefetch_related('teachers__user').annotate(
            student_count=Count('students', distinct=True)
        ).order_by('grade_level__order', 'grade_level__name', 'strand__name', 'section__name')
        return render(request, 'school_admin/classes.html', {
            'classes': classes, 'school': school,
        })


class SchoolAdminCreateClassView(View):
    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        school = request.current_school
        grade_levels = GradeLevel.objects.filter(school=school).order_by('order', 'name')
        strands = Strand.objects.filter(school=school).order_by('name')
        sections = Section.objects.filter(school=school).order_by('name')
        teachers = Teacher.objects.filter(school=school).select_related('user')
        return render(request, 'school_admin/create_class.html', {
            'school': school, 'grade_levels': grade_levels,
            'strands': strands, 'sections': sections, 'teachers': teachers,
        })

    def post(self, request):
        school = request.current_school
        grade_level_id = request.POST.get('grade_level')
        strand_id = request.POST.get('strand')
        section_id = request.POST.get('section')
        teacher_ids = request.POST.getlist('teachers')

        errors = []
        if not grade_level_id:
            errors.append('Grade level is required.')
        if not strand_id:
            errors.append('Strand is required.')
        if not section_id:
            errors.append('Section is required.')

        if not errors:
            from repositories.class_repository import ClassRepository
            repo = ClassRepository()
            if repo.check_duplicate_class(
                school_id=school.id,
                grade_level_id=int(grade_level_id),
                strand_id=int(strand_id),
                section_id=int(section_id),
            ):
                errors.append('A class with these details already exists.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('school_admin_create_class')

        from django.db import transaction
        with transaction.atomic():
            class_obj = Class.objects.create(
                school=school,
                grade_level_id=int(grade_level_id),
                strand_id=int(strand_id),
                section_id=int(section_id),
            )
            if teacher_ids:
                teachers = Teacher.objects.filter(
                    pk__in=teacher_ids, school=school
                )
                class_obj.teachers.add(*teachers)

        messages.success(request, 'Class created successfully.')
        return redirect('school_admin_classes')


class SchoolAdminEditClassView(View):
    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, class_id):
        school = request.current_school
        class_obj = get_object_or_404(Class, id=class_id, school=school)
        grade_level_id = request.POST.get('grade_level')
        strand_id = request.POST.get('strand')
        section_id = request.POST.get('section')
        teacher_ids = request.POST.getlist('teachers')

        errors = []
        if not grade_level_id:
            errors.append('Grade level is required.')
        if not strand_id:
            errors.append('Strand is required.')
        if not section_id:
            errors.append('Section is required.')

        if not errors:
            from repositories.class_repository import ClassRepository
            repo = ClassRepository()
            if repo.check_duplicate_class(
                school_id=school.id,
                grade_level_id=int(grade_level_id),
                strand_id=int(strand_id),
                section_id=int(section_id),
                exclude_id=class_id,
            ):
                errors.append('A class with these details already exists.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('school_admin_classes')

        from django.db import transaction
        with transaction.atomic():
            class_obj.grade_level_id = int(grade_level_id)
            class_obj.strand_id = int(strand_id)
            class_obj.section_id = int(section_id)
            class_obj.save()
            class_obj.teachers.clear()
            if teacher_ids:
                teachers = Teacher.objects.filter(
                    pk__in=teacher_ids, school=school
                )
                class_obj.teachers.add(*teachers)

        messages.success(request, 'Class updated successfully.')
        return redirect('school_admin_classes')


class SchoolAdminDeleteClassView(View):
    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, class_id):
        school = request.current_school
        class_obj = get_object_or_404(Class, id=class_id, school=school)
        class_obj.delete()
        messages.success(request, 'Class deleted successfully.')
        return redirect('school_admin_classes')


class SchoolAdminClassDetailView(View):
    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, class_id):
        school = request.current_school
        class_obj = get_object_or_404(
            Class.objects.select_related('grade_level', 'strand', 'section')
            .prefetch_related('teachers__user'),
            id=class_id, school=school,
        )
        students = Student.objects.filter(
            school=school, class_assigned=class_obj
        ).order_by('last_name', 'first_name')

        grade_levels = GradeLevel.objects.filter(school=school).order_by('order', 'name')
        strands = Strand.objects.filter(school=school).order_by('name')
        sections = Section.objects.filter(school=school).order_by('name')
        teachers = Teacher.objects.filter(school=school).select_related('user')

        return render(request, 'school_admin/class_detail.html', {
            'class_obj': class_obj, 'students': students,
            'grade_levels': grade_levels, 'strands': strands,
            'sections': sections, 'teachers': teachers, 'school': school,
        })


class SchoolAdminLookupsView(View):
    LOOKUP_MODELS = {
        'grade_level': {
            'model': GradeLevel, 'label': 'Grade Levels', 'has_order': True,
            'usage': lambda name, school: Class.objects.filter(school=school, grade_level__name=name).count(),
            'usage_label': 'classes',
        },
        'strand': {
            'model': Strand, 'label': 'Strands', 'has_order': False,
            'usage': lambda name, school: Class.objects.filter(school=school, strand__name=name).count(),
            'usage_label': 'classes',
        },
        'section': {
            'model': Section, 'label': 'Sections', 'has_order': False,
            'usage': lambda name, school: Class.objects.filter(school=school, section__name=name).count(),
            'usage_label': 'classes',
        },
        'subject': {
            'model': Subject, 'label': 'Subjects', 'has_order': False,
            'usage': lambda name, school: Exam.objects.filter(created_by__school=school, subject=name).count(),
            'usage_label': 'exams',
        },
        'quarter': {
            'model': Quarter, 'label': 'Quarters', 'has_order': True,
            'usage': lambda name, school: Exam.objects.filter(created_by__school=school, quarter__name=name).count(),
            'usage_label': 'exams',
        },
    }

    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        school = request.current_school
        groups = []
        for key, meta in self.LOOKUP_MODELS.items():
            items = list(meta['model'].objects.filter(school=school))
            groups.append({'key': key, 'label': meta['label'], 'has_order': meta['has_order'], 'items': items})
        return render(request, 'school_admin/lookups.html', {'groups': groups, 'school': school})

    def post(self, request):
        school = request.current_school
        kind = request.POST.get('kind', '').strip()
        action = request.POST.get('action', '').strip()
        meta = self.LOOKUP_MODELS.get(kind)
        if not meta:
            messages.error(request, 'Unknown lookup type.')
            return redirect('school_admin_lookups')

        Model = meta['model']

        if action == 'create':
            name = request.POST.get('name', '').strip()
            order_raw = request.POST.get('order', '').strip()
            if not name:
                messages.error(request, 'Name is required.')
                return redirect('school_admin_lookups')
            fields = {'name': name, 'school': school}
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
            return redirect('school_admin_lookups')

        if action == 'edit':
            item_id = request.POST.get('item_id')
            name = request.POST.get('name', '').strip()
            order_raw = request.POST.get('order', '').strip()
            if not name:
                messages.error(request, 'Name is required.')
                return redirect('school_admin_lookups')
            item = get_object_or_404(Model, pk=item_id)
            if item.school_id != school.id:
                messages.error(request, 'Access denied.')
                return redirect('school_admin_lookups')
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
                return redirect('school_admin_lookups')
            messages.success(request, f'{meta["label"][:-1]} renamed to "{name}".')
            return redirect('school_admin_lookups')

        if action == 'delete':
            item_id = request.POST.get('item_id')
            item = get_object_or_404(Model, pk=item_id)
            if item.school_id != school.id:
                messages.error(request, 'Access denied.')
                return redirect('school_admin_lookups')
            usage_count = meta['usage'](item.name, school)
            if usage_count > 0:
                messages.error(request, f'Cannot delete "{item.name}": still used by {usage_count} {meta["usage_label"]}.')
                return redirect('school_admin_lookups')
            item.delete()
            messages.success(request, f'{meta["label"][:-1]} "{item.name}" deleted.')
            return redirect('school_admin_lookups')

        messages.error(request, 'Unknown action.')
        return redirect('school_admin_lookups')


class SchoolAdminStudentAssignView(View):
    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        school = request.current_school
        from users.forms import StudentClassAssignmentForm
        form = StudentClassAssignmentForm(school_id=school.id)
        return render(request, 'school_admin/assign_student.html', {
            'form': form, 'school': school,
        })

    def post(self, request):
        school = request.current_school
        from users.forms import StudentClassAssignmentForm
        form = StudentClassAssignmentForm(request.POST, school_id=school.id)
        if form.is_valid():
            student = form.cleaned_data['student']
            class_obj = form.cleaned_data['class_assigned']
            if student.school_id != school.id or class_obj.school_id != school.id:
                messages.error(request, 'Invalid selection.')
                return redirect('school_admin_student_assign')
            student.class_assigned = class_obj
            student.save()
            messages.success(request, f'{student.get_full_name()} assigned to {class_obj}.')
            return redirect('school_admin_classes')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, error)
        return render(request, 'school_admin/assign_student.html', {
            'form': form, 'school': school,
        })


class SchoolAdminBulkStudentAssignView(View):
    @method_decorator(school_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, class_id=None):
        school = request.current_school
        from users.forms import BulkStudentAssignmentForm
        form = BulkStudentAssignmentForm(school_id=school.id, initial_class_id=class_id)
        return render(request, 'school_admin/bulk_assign.html', {
            'form': form, 'school': school, 'preselected_class_id': class_id,
        })

    def post(self, request, class_id=None):
        school = request.current_school
        from users.forms import BulkStudentAssignmentForm
        form = BulkStudentAssignmentForm(
            request.POST, school_id=school.id, initial_class_id=class_id
        )
        if form.is_valid():
            students = form.cleaned_data['students']
            class_obj = form.cleaned_data['class_assigned']
            if class_obj.school_id != school.id:
                messages.error(request, 'Invalid class selection.')
                return redirect('school_admin_bulk_student_assign')
            count = 0
            for student in students:
                if student.school_id == school.id:
                    student.class_assigned = class_obj
                    student.save()
                    count += 1
            messages.success(request, f'{count} student(s) assigned to {class_obj}.')
            return redirect('school_admin_classes')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, error)
        return render(request, 'school_admin/bulk_assign.html', {
            'form': form, 'school': school,
        })
