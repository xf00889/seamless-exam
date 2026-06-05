from django.urls import path
from .views_superadmin import (
    SuperAdminLoginView,
    SuperAdminLogoutView,
    SuperAdminDashboardView,
    SuperAdminTeachersView,
    SuperAdminEditTeacherView,
    SuperAdminToggleTeacherActiveView,
    SuperAdminStudentsView,
    SuperAdminResetPasswordView,
    SuperAdminDeleteUserView,
    SuperAdminCreateView,
    SuperAdminNotificationsView,
    SuperAdminCreateTeacherView,
    SuperAdminSessionsView,
    SuperAdminLookupsView,
)
from .views_ai_settings import ai_settings_view

urlpatterns = [
    path('login/', SuperAdminLoginView.as_view(), name='superadmin_login'),
    path('logout/', SuperAdminLogoutView.as_view(), name='superadmin_logout'),
    path('dashboard/', SuperAdminDashboardView.as_view(), name='superadmin_dashboard'),
    path('teachers/', SuperAdminTeachersView.as_view(), name='superadmin_teachers'),
    path('teachers/<int:teacher_id>/edit/', SuperAdminEditTeacherView.as_view(), name='superadmin_edit_teacher'),
    path('teachers/<int:teacher_id>/toggle-active/', SuperAdminToggleTeacherActiveView.as_view(), name='superadmin_toggle_teacher_active'),
    path('students/', SuperAdminStudentsView.as_view(), name='superadmin_students'),
    path('notifications/', SuperAdminNotificationsView.as_view(), name='superadmin_notifications'),
    path('sessions/', SuperAdminSessionsView.as_view(), name='superadmin_sessions'),
    path('lookups/', SuperAdminLookupsView.as_view(), name='superadmin_lookups'),
    path('reset-password/', SuperAdminResetPasswordView.as_view(), name='superadmin_reset_password'),
    path('delete-user/', SuperAdminDeleteUserView.as_view(), name='superadmin_delete_user'),
    path('create/', SuperAdminCreateView.as_view(), name='superadmin_create'),
    path('create-teacher/', SuperAdminCreateTeacherView.as_view(), name='superadmin_create_teacher'),
    path('ai-settings/', ai_settings_view, name='superadmin_ai_settings'),
]
