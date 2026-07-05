from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from .views import cron_backup


urlpatterns = [
    path('', RedirectView.as_view(pattern_name='login', permanent=False), name='home'),
    path('admin/', admin.site.urls),
    path('cron/backup/', cron_backup, name='cron_backup'),
    path('', include('users.urls')),
    path('school-admin/', include('users.urls_school_admin')),
    path('superadmin/', include('users.urls_superadmin')),
    path('exams/', include('exams.urls')),
    path('', include('attempts.urls')),
    path('uploads/', include('uploads.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
