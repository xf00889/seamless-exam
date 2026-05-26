"""
Context processors for providing global template context.
Requirements: 1.3, 1.4
"""
from services.auth_service import AuthenticationService
from users.models import Teacher


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
        context['navbar_nav_links'] = [
            {
                'label': 'Dashboard',
                'url': '/attempts/teacher/dashboard/',
                'active': current_path.startswith('/attempts/teacher/dashboard/')
            },
            {
                'label': 'Exams',
                'url': '/exams/',
                'active': current_path.startswith('/exams/')
            },
            {
                'label': 'Classes',
                'url': '/users/teacher/classes/',
                'active': current_path.startswith('/users/teacher/classes/')
            },
            {
                'label': 'Grading',
                'url': '/attempts/teacher/grading/',
                'active': current_path.startswith('/attempts/teacher/grading/')
            },
            {
                'label': 'Accounts',
                'url': '/users/teacher/accounts/',
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
                    'url': '/users/student/dashboard/',
                    'active': current_path.startswith('/users/student/dashboard/')
                },
                {
                    'label': 'Available Exams',
                    'url': '/attempts/student/exams/',
                    'active': current_path.startswith('/attempts/student/exams/')
                },
                {
                    'label': 'My History',
                    'url': '/users/student/history/',
                    'active': current_path.startswith('/users/student/history/')
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
