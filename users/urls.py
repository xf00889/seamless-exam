from django.urls import path
from .views import (
    TeacherLoginView,
    StudentLoginView,
    LogoutView,
    StudentProfileView,
    StudentProfileEditView,
    ChangePasswordView,
    StudentDashboardView,
    StudentHistoryView,
    ExportHistoryView,
    TeacherProfileView,
    TeacherProfileEditView,
    TeacherChangePasswordView,
    ClassListView,
    ClassCreateView,
    ClassUpdateView,
    ClassDeleteView,
    ClassDetailView,
    StudentAssignView,
    StudentRemoveView,
    BulkStudentAssignView,
    StudentAccountManagementView
)
from .views_setup import FirstTimeSetupView
from .views_request import RequestAccessView

urlpatterns = [
    # First-time setup route
    path('setup/', FirstTimeSetupView.as_view(), name='first_time_setup'),

    # Access request (public)
    path('request-access/', RequestAccessView.as_view(), name='request_access'),
    
    # Authentication routes
    path('teacher/login/', TeacherLoginView.as_view(), name='teacher_login'),
    path('student/login/', StudentLoginView.as_view(), name='student_login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Student profile management routes
    path('student/profile/', StudentProfileView.as_view(), name='student_profile'),
    path('student/profile/edit/', StudentProfileEditView.as_view(), name='student_profile_edit'),
    path('student/profile/password/', ChangePasswordView.as_view(), name='change_password'),
    
    # Student dashboard and history routes
    path('student/dashboard/', StudentDashboardView.as_view(), name='student_dashboard'),
    path('student/history/', StudentHistoryView.as_view(), name='student_history'),
    path('student/history/export/', ExportHistoryView.as_view(), name='export_history'),
    
    # Teacher profile management routes
    path('teacher/profile/', TeacherProfileView.as_view(), name='teacher_profile'),
    path('teacher/profile/edit/', TeacherProfileEditView.as_view(), name='teacher_profile_edit'),
    path('teacher/profile/password/', TeacherChangePasswordView.as_view(), name='teacher_change_password'),
    
    # Class management routes
    path('teacher/classes/', ClassListView.as_view(), name='class_list'),
    path('teacher/classes/create/', ClassCreateView.as_view(), name='class_create'),
    path('teacher/classes/<int:class_id>/', ClassDetailView.as_view(), name='class_detail'),
    path('teacher/classes/<int:class_id>/edit/', ClassUpdateView.as_view(), name='class_update'),
    path('teacher/classes/<int:class_id>/delete/', ClassDeleteView.as_view(), name='class_delete'),
    
    # Student assignment routes
    path('teacher/students/assign/', StudentAssignView.as_view(), name='student_assign'),
    path('teacher/students/<int:student_id>/remove/', StudentRemoveView.as_view(), name='student_remove'),
    path('teacher/students/bulk-assign/', BulkStudentAssignView.as_view(), name='bulk_student_assign'),
    
    # Student account management
    path('teacher/accounts/', StudentAccountManagementView.as_view(), name='student_account_management'),
]
