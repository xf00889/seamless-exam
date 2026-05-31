from django.urls import path
from . import views

urlpatterns = [
    # Exam management URLs
    path('', views.exam_list_view, name='exam_list'),
    path('create/', views.exam_create_view, name='exam_create'),
    path('create/test/', views.exam_create_test_view, name='exam_create_test'),
    path('<int:exam_id>/edit/', views.exam_edit_view, name='exam_edit'),
    path('<int:exam_id>/activate/', views.exam_activate_view, name='exam_activate'),
    path('<int:exam_id>/delete/', views.exam_delete_view, name='exam_delete'),
    path('<int:exam_id>/takers/', views.exam_takers_view, name='exam_takers'),
    path('<int:exam_id>/item-summary/', views.item_summary_view, name='item_summary'),
    path('<int:exam_id>/item-summary/analyze/', views.item_summary_ai_analyze_view, name='item_summary_analyze'),
    path('<int:exam_id>/mps/', views.mps_report_view, name='mps_report'),
    path('<int:exam_id>/mps/export/', views.mps_export_excel_view, name='mps_export_excel'),
    path('<int:exam_id>/mps/export-word/', views.mps_export_word_view, name='mps_export_word'),
    path('<int:exam_id>/students/', views.get_exam_students_view, name='exam_students'),
    
    # Question management URLs
    path('<int:exam_id>/questions/create/', views.question_create_view, name='question_create'),
    path('<int:exam_id>/questions/ai-generate/', views.ai_generate_questions_view, name='ai_generate_questions'),
    path('<int:exam_id>/questions/ai-inline/', views.ai_inline_generate_view, name='ai_inline_generate'),
    path('ai-task/<int:task_id>/status/', views.ai_task_status_view, name='ai_task_status'),
    path('question/<int:question_id>/edit/', views.question_edit_view, name='question_edit'),
    path('questions/<int:question_id>/delete/', views.question_delete_view, name='question_delete'),
]
