"""
Context processors for providing global template context.
Requirements: 1.3, 1.4
"""
from services.auth_service import AuthenticationService
from users.models import AdminNotification, Teacher, SystemSettings
from django.urls import reverse


def navbar_context(request):
    """
    Context processor to provide navbar data to all templates.
    Provides student/teacher profile information and navigation links.
    Requirements: 1.3, 1.4
    """
    context = {
        'navbar_student': None,
        'navbar_teacher': None,
        'navbar_profile_picture_url': None,
        'navbar_student_name': None,
        'navbar_nav_links': [],
    }
    
    # Ensure request has session attribute
    if not hasattr(request, 'session'):
        return context
    
    # Check if user is authenticated as student
    auth_service = AuthenticationService()
    
    def set_teacher_context(teacher_obj):
        """Populate teacher navbar context in one place."""
        context['navbar_teacher'] = teacher_obj
        context['navbar_student_name'] = (
            teacher_obj.user.get_full_name() or teacher_obj.user.username
        )

        current_path = request.path
        is_mps_path = current_path.startswith('/exams/mps')
        context['navbar_nav_links'] = [
            {
                'label': 'Dashboard',
                'url': reverse('teacher_dashboard'),
                'active': current_path.startswith('/attempts/teacher/dashboard/')
            },
            {
                'label': 'Exams',
                'url': reverse('exam_list'),
                'active': current_path.startswith('/exams/') and not is_mps_path
            },
            {
                'label': 'MPS',
                'url': reverse('mps_quarter_list'),
                'active': is_mps_path,
            },
            {
                'label': 'Classes',
                'url': reverse('class_list'),
                'active': current_path.startswith('/users/teacher/classes/')
            },
            {
                'label': 'Grading',
                'url': reverse('teacher_grading_list'),
                'active': current_path.startswith('/attempts/teacher/grading/')
            },
            {
                'label': 'Accounts',
                'url': reverse('student_account_management'),
                'active': current_path.startswith('/users/teacher/accounts/')
            },
        ]

    if auth_service.require_student(request):
        student = auth_service.get_current_student(request)
        
        if student:
            context['navbar_student'] = student
            context['navbar_student_name'] = student.get_full_name()

            # Define navigation links for students
            current_path = request.path
            context['navbar_nav_links'] = [
                {
                    'label': 'Dashboard',
                    'url': reverse('student_dashboard'),
                    'active': current_path.startswith('/users/student/dashboard/')
                },
                {
                    'label': 'Available Exams',
                    'url': reverse('student_exam_list'),
                    'active': current_path.startswith('/attempts/student/exams/')
                },
                {
                    'label': 'My History',
                    'url': reverse('student_history'),
                    'active': current_path.startswith('/users/student/history/')
                },
                {
                    'label': 'Activity Log',
                    'url': reverse('student_activity_log'),
                    'active': current_path.startswith('/users/student/activity-log/')
                },
            ]
    
    elif auth_service.require_teacher(request):
        # For teachers, provide profile context
        teacher = auth_service.get_current_teacher(request)
        if teacher:
            set_teacher_context(teacher)
    elif getattr(request, 'user', None) and request.user.is_authenticated:
        # Fallback for authenticated teacher users when session role flags are missing.
        teacher = Teacher.objects.filter(user=request.user).first()
        if teacher:
            set_teacher_context(teacher)

    return context


def system_settings_context(request):
    """
    Expose the SystemSettings singleton to all templates so superadmin pages
    can surface maintenance-mode status without an extra query per view.

    Also expose the latest notifications + unread count so the top-bar bell
    can render on every superadmin page without per-view boilerplate.
    """
    if not request.path.startswith('/superadmin/'):
        return {}
    context = {}
    try:
        context['system_settings'] = SystemSettings.load()
    except Exception:
        context['system_settings'] = None
    try:
        notif_qs = AdminNotification.objects.all()
        context['unread_notifications'] = notif_qs.filter(is_read=False).count()
        context['latest_notifications'] = list(notif_qs.order_by('-created_at')[:5])
    except Exception:
        context['unread_notifications'] = 0
        context['latest_notifications'] = []
    return context
