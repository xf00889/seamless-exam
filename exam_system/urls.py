"""
URL configuration for exam_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.shortcuts import render
from users.views_setup import FirstTimeSetupView
from users.models import Teacher, Student

from .views import cron_backup


def health_check(request):
    return JsonResponse({'status': 'ok'})


def home_view(request):
    context = {}
    if request.user.is_authenticated:
        if request.user.is_superuser and not Teacher.objects.filter(user=request.user).exists():
            context['dashboard_url'] = '/superadmin/dashboard/'
            context['dashboard_label'] = 'Go to Admin Panel'
        elif Teacher.objects.filter(user=request.user).exists():
            context['dashboard_url'] = '/exams/'
            context['dashboard_label'] = 'Go to Dashboard'
    if request.session.get('student_id'):
        try:
            student = Student.objects.get(id=request.session['student_id'])
            context['dashboard_url'] = '/exams/available/'
            context['dashboard_label'] = 'Go to Exams'
        except Student.DoesNotExist:
            pass
    return render(request, 'home.html', context)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('setup/', FirstTimeSetupView.as_view(), name='setup'),
    path('health/', health_check, name='health_check'),
    path('cron/backup/', cron_backup, name='cron_backup'),
    path('users/', include('users.urls')),
    path('superadmin/', include('users.urls_superadmin')),
    path('exams/', include('exams.urls')),
    path('attempts/', include('attempts.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Django Debug Toolbar
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
