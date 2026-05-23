"""
Breadcrumb Service
Provides helper functions to generate breadcrumb navigation for templates.
"""

from django.urls import reverse


class BreadcrumbService:
    """Service for generating breadcrumb navigation."""
    
    @staticmethod
    def home():
        """Home breadcrumb."""
        return {'label': 'Home', 'url': reverse('home')}
    
    @staticmethod
    def teacher_dashboard():
        """Teacher dashboard breadcrumb."""
        return {'label': 'Dashboard', 'url': reverse('teacher_dashboard')}
    
    @staticmethod
    def student_dashboard():
        """Student dashboard breadcrumb."""
        return {'label': 'Dashboard', 'url': reverse('student_dashboard')}
    
    # Exam breadcrumbs
    @staticmethod
    def exam_list():
        """Exam list breadcrumb."""
        return {'label': 'My Exams', 'url': reverse('exam_list')}
    
    @staticmethod
    def exam_create():
        """Exam create breadcrumb (no URL - current page)."""
        return {'label': 'Create Exam', 'url': None}
    
    @staticmethod
    def exam_edit(exam_title):
        """Exam edit breadcrumb (no URL - current page)."""
        return {'label': f'Edit: {exam_title}', 'url': None}
    
    @staticmethod
    def exam_takers(exam_title):
        """Exam takers breadcrumb (no URL - current page)."""
        return {'label': f'Takers: {exam_title}', 'url': None}
    
    # Class breadcrumbs
    @staticmethod
    def class_list():
        """Class list breadcrumb."""
        return {'label': 'My Classes', 'url': reverse('class_list')}
    
    @staticmethod
    def class_detail(class_name):
        """Class detail breadcrumb (no URL - current page)."""
        return {'label': class_name, 'url': None}
    
    @staticmethod
    def class_create():
        """Class create breadcrumb (no URL - current page)."""
        return {'label': 'Create Class', 'url': None}
    
    @staticmethod
    def class_edit(class_name):
        """Class edit breadcrumb (no URL - current page)."""
        return {'label': f'Edit: {class_name}', 'url': None}
    
    # Student breadcrumbs
    @staticmethod
    def student_exams():
        """Student exams list breadcrumb."""
        return {'label': 'Available Exams', 'url': reverse('student_exam_list')}
    
    @staticmethod
    def student_profile():
        """Student profile breadcrumb."""
        return {'label': 'My Profile', 'url': reverse('student_profile')}
    
    @staticmethod
    def student_profile_edit():
        """Student profile edit breadcrumb (no URL - current page)."""
        return {'label': 'Edit Profile', 'url': None}
    
    @staticmethod
    def student_history():
        """Student history breadcrumb (no URL - current page)."""
        return {'label': 'Exam History', 'url': None}
    
    # Teacher breadcrumbs
    @staticmethod
    def teacher_profile():
        """Teacher profile breadcrumb."""
        return {'label': 'My Profile', 'url': reverse('teacher_profile')}
    
    @staticmethod
    def teacher_profile_edit():
        """Teacher profile edit breadcrumb (no URL - current page)."""
        return {'label': 'Edit Profile', 'url': None}
    
    @staticmethod
    def teacher_change_password():
        """Teacher change password breadcrumb (no URL - current page)."""
        return {'label': 'Change Password', 'url': None}
    
    @staticmethod
    def student_change_password():
        """Student change password breadcrumb (no URL - current page)."""
        return {'label': 'Change Password', 'url': None}
    
    # Grading breadcrumbs
    @staticmethod
    def grading_list():
        """Grading list breadcrumb."""
        return {'label': 'Grading Queue', 'url': reverse('teacher_grading_list')}
    
    @staticmethod
    def grading(student_name, exam_title):
        """Grading breadcrumb (no URL - current page)."""
        return {'label': f'Grade: {student_name} - {exam_title}', 'url': None}
    
    # Attempt breadcrumbs
    @staticmethod
    def exam_take(exam_title):
        """Exam take breadcrumb (no URL - current page)."""
        return {'label': f'Taking: {exam_title}', 'url': None}
    
    @staticmethod
    def exam_submitted():
        """Exam submitted breadcrumb (no URL - current page)."""
        return {'label': 'Exam Submitted', 'url': None}
    
    @staticmethod
    def student_results(exam_title):
        """Student results breadcrumb (no URL - current page)."""
        return {'label': f'Results: {exam_title}', 'url': None}
    
    @staticmethod
    def attempt_detail(student_name, exam_title):
        """Attempt detail breadcrumb (no URL - current page)."""
        return {'label': f'{student_name} - {exam_title}', 'url': None}
    
    # Upload breadcrumbs
    @staticmethod
    def upload_form():
        """Upload form breadcrumb."""
        return {'label': 'Upload Document', 'url': reverse('upload_form')}
    
    @staticmethod
    def process_form():
        """Process form breadcrumb (no URL - current page)."""
        return {'label': 'Process Document', 'url': None}
    
    @staticmethod
    def question_review():
        """Question review breadcrumb (no URL - current page)."""
        return {'label': 'Review Questions', 'url': None}
    
    @staticmethod
    def document_list():
        """Document list breadcrumb."""
        return {'label': 'My Documents', 'url': reverse('document_list')}
    
    # Student assignment breadcrumbs
    @staticmethod
    def bulk_student_assign():
        """Bulk student assignment breadcrumb (no URL - current page)."""
        return {'label': 'Assign Students', 'url': None}
    
    @staticmethod
    def student_remove_confirm(student_name):
        """Student remove confirmation breadcrumb (no URL - current page)."""
        return {'label': f'Remove: {student_name}', 'url': None}


# Helper function to build breadcrumb chains
def build_breadcrumbs(*breadcrumbs):
    """
    Build a breadcrumb chain from multiple breadcrumb items.
    
    Args:
        *breadcrumbs: Variable number of breadcrumb dictionaries
        
    Returns:
        list: List of breadcrumb dictionaries
        
    Example:
        breadcrumbs = build_breadcrumbs(
            BreadcrumbService.home(),
            BreadcrumbService.exam_list(),
            BreadcrumbService.exam_edit("Math Exam")
        )
    """
    return list(breadcrumbs)
