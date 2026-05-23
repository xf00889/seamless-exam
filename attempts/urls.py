from django.urls import path
from . import views

urlpatterns = [
    # Student exam-taking URLs
    path('student/exams/', views.student_exam_list_view, name='student_exam_list'),
    path('student/exams/<int:exam_id>/start/', views.exam_start_view, name='exam_start'),
    path('student/exams/<int:exam_id>/recover/', views.recover_interrupted_attempt_view, name='recover_attempt'),
    path('student/attempts/<int:attempt_id>/take/', views.exam_take_view, name='exam_take'),
    path('student/attempts/<int:attempt_id>/review/', views.exam_review_view, name='exam_review'),
    path('student/attempts/<int:attempt_id>/save/', views.save_answer_view, name='save_answer'),
    path('student/attempts/<int:attempt_id>/submit/', views.submit_exam_view, name='submit_exam'),
    path('student/attempts/<int:attempt_id>/submitted/', views.exam_submitted_view, name='exam_submitted'),
    path('student/attempts/<int:attempt_id>/results/', views.student_results_view, name='student_results'),
    
    # Tab monitoring URLs
    path('student/attempts/<int:attempt_id>/tab-switch/', views.record_tab_switch_view, name='record_tab_switch'),
    path('student/attempts/<int:attempt_id>/violations/', views.get_tab_violations_view, name='get_tab_violations'),
    
    # Teacher grading URLs
    path('teacher/grading/', views.teacher_grading_list_view, name='teacher_grading_list'),
    path('teacher/grading/<int:attempt_id>/', views.teacher_grading_view, name='teacher_grading'),
    path('teacher/grading/essay/<int:answer_id>/grade/', views.grade_essay_view, name='grade_essay'),
    path('teacher/grading/essay/<int:answer_id>/update/', views.update_essay_score_view, name='update_essay_score'),
    
    # Teacher dashboard and analytics URLs
    path('teacher/dashboard/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('teacher/attempts/<int:attempt_id>/', views.teacher_attempt_detail_view, name='teacher_attempt_detail'),
    path('teacher/attempts/<int:attempt_id>/activity/', views.view_activity_log_view, name='view_activity_log'),
]
