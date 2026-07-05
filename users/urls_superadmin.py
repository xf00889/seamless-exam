from django.urls import path
from .views_superadmin import (
    SuperAdminLoginView,
    SuperAdminLogoutView,
    SuperAdminDashboardView,
    SuperAdminCreateView,
    SuperAdminManageView,
    SuperAdminNotificationsView,
    SuperAdminSessionsView,
    SuperAdminCreateSchoolView,
    SuperAdminCreateSchoolAdminView,
    SuperAdminEditSchoolView,
    SuperAdminDeleteSchoolView,
    SuperAdminDeleteSchoolAdminView,
    SuperAdminSchoolAdminDetailView,
)
from .views_ai_settings import ai_settings_view

urlpatterns = [
    path('login/', SuperAdminLoginView.as_view(), name='superadmin_login'),
    path('logout/', SuperAdminLogoutView.as_view(), name='superadmin_logout'),
    path('dashboard/', SuperAdminDashboardView.as_view(), name='superadmin_dashboard'),
    path('manage/', SuperAdminManageView.as_view(), name='superadmin_manage'),
    path('manage/school-admin/<int:admin_id>/', SuperAdminSchoolAdminDetailView.as_view(), name='superadmin_school_admin_detail'),
    path('manage/school-admin/<int:admin_id>/delete/', SuperAdminDeleteSchoolAdminView.as_view(), name='superadmin_delete_school_admin'),
    path('notifications/', SuperAdminNotificationsView.as_view(), name='superadmin_notifications'),
    path('sessions/', SuperAdminSessionsView.as_view(), name='superadmin_sessions'),
    path('create/', SuperAdminCreateView.as_view(), name='superadmin_create'),
    path('schools/create/', SuperAdminCreateSchoolView.as_view(), name='superadmin_create_school'),
    path('schools/<int:school_id>/edit/', SuperAdminEditSchoolView.as_view(), name='superadmin_edit_school'),
    path('schools/<int:school_id>/delete/', SuperAdminDeleteSchoolView.as_view(), name='superadmin_delete_school'),
    path('school-admins/create/', SuperAdminCreateSchoolAdminView.as_view(), name='superadmin_create_school_admin'),
    path('ai-settings/', ai_settings_view, name='superadmin_ai_settings'),
]
