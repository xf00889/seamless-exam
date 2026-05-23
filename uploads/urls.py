from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'uploads'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='uploads:document_list', permanent=False), name='uploads_root'),
    path('upload/', views.document_upload_view, name='document_upload'),
    path('list/', views.document_list_view, name='document_list'),
    path('delete/<int:document_id>/', views.document_delete_view, name='document_delete'),
    path('process/<int:document_id>/', views.document_process_view, name='document_process'),
]
