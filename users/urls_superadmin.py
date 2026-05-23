from django.urls import path
from .views_superadmin import (
    SuperAdminLoginView,
    SuperAdminLogoutView,
    SuperAdminDashboardView,
    SuperAdminTeachersView,
    SuperAdminStudentsView,
    SuperAdminResetPasswordView,
    SuperAdminDeleteUserView,
    SuperAdminCreateView,
    SuperAdminNotificationsView,
)

urlpatterns = [
    path('login/', SuperAdminLoginView.as_view(), name='superadmin_login'),
    path('logout/', SuperAdminLogoutView.as_view(), name='superadmin_logout'),
    path('dashboard/', SuperAdminDashboardView.as_view(), name='superadmin_dashboard'),
    path('teachers/', SuperAdminTeachersView.as_view(), name='superadmin_teachers'),
    path('students/', SuperAdminStudentsView.as_view(), name='superadmin_students'),
    path('notifications/', SuperAdminNotificationsView.as_view(), name='superadmin_notifications'),
    path('reset-password/', SuperAdminResetPasswordView.as_view(), name='superadmin_reset_password'),
    path('delete-user/', SuperAdminDeleteUserView.as_view(), name='superadmin_delete_user'),
    path('create/', SuperAdminCreateView.as_view(), name='superadmin_create'),
]
