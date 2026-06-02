from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Avg
from exams.models import Exam, Question, QuestionType, AIGenerationTask
from exams.forms import ExamForm, QuestionForm
from users.models import Class
from users.decorators import teacher_required
from services.auth_service import AuthenticationService
from services.exam_service import ExamService
from services.question_service import QuestionService
from services.exam_activation_service import ExamActivationService
from services.view_helpers import build_breadcrumbs
from django.urls import reverse
import logging
from itertools import groupby

logger = logging.getLogger(__name__)


# Initialize services
exam_service = ExamService()
question_service = QuestionService()
activation_service = ExamActivationService()
auth_service = AuthenticationService()


@teacher_required
def exam_list_view(request):
    """
    Display all exams for the logged-in teacher with pagination.
    Requirements: 2.5, 8.1
    """
    # Get teacher profile
    teacher = auth_service.get_current_teacher(request)
    
    # Get all exams created by this teacher
    exams = exam_service.get_exams_by_teacher(teacher.pk)
    
    # Implement pagination (20 items per page)
    paginator = Paginator(exams, 20)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        page_obj = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        page_obj = paginator.page(paginator.num_pages)

    page_exams = list(page_obj.object_list)
    page_exams.sort(key=lambda exam: (
        exam.quarter.order if exam.quarter else 9999,
        exam.quarter.name.lower() if exam.quarter else 'no quarter',
        -exam.created_at.timestamp(),
    ))

    grouped_exams = []
    for key, group in groupby(
        page_exams,
        key=lambda exam: (
            exam.quarter.id if exam.quarter else None,
            exam.quarter.name if exam.quarter else 'No Quarter',
            exam.quarter.order if exam.quarter else 9999,
        )
    ):
        group_items = list(group)
        grouped_exams.append({
            'quarter_id': key[0],
            'label': key[1],
            'exams': group_items,
        })
    
    # Build breadcrumbs
    breadcrumbs = build_breadcrumbs(
        ('Dashboard', reverse('teacher_dashboard')),
        'My Exams'
    )
    
    context = {
        'exams': page_obj,
        'grouped_exams': grouped_exams,
        'page_obj': page_obj,
        'teacher': teacher,
        'page_breadcrumbs': breadcrumbs
    }
    return render(request, 'exams/exam_list.html', context)


@teacher_required
def exam_create_view(request):
    """
    Create a new exam with form validation and support for two creation methods:
    1. File upload - Extract questions from uploaded documents
    2. Manual entry - Create questions manually in the editor
    
    Requirements: 1.5, 3.1
    """
    teacher = auth_service.get_current_teacher(request)
    
    if request.method == 'POST':
        form = ExamForm(request.POST, request.FILES, teacher=teacher)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if not form.is_valid():
            if is_ajax:
                errors = [e for field_errors in form.errors.values() for e in field_errors]
                return JsonResponse({'success': False, 'error': errors[0] if errors else 'Form validation failed.'})

            # Display field-specific error messages (Requirement 1.4)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            
            # Get teacher's classes for the template
            classes = Class.objects.filter(teacher=teacher).order_by('grade_level', 'strand', 'section')
            
            # Build breadcrumbs
            breadcrumbs = build_breadcrumbs(
                ('Dashboard', reverse('teacher_dashboard')),
                ('My Exams', reverse('exam_list')),
                'Create Exam'
            )
            
            return render(request, 'exams/exam_form.html', {
                'form': form,
                'classes': classes,
                'page_breadcrumbs': breadcrumbs
            })
        
        # Get generation method to route appropriately
        generation_method = form.cleaned_data.get('generation_method', 'manual')
        
        # Create exam first
        exam_data = {
            'title': form.cleaned_data['title'],
            'subject': form.cleaned_data.get('subject', ''),
            'quarter': form.cleaned_data.get('quarter'),
            'description': form.cleaned_data.get('description', ''),
            'duration_minutes': form.cleaned_data['duration_minutes'],
            'created_by': teacher
        }
        
        exam = exam_service.create_exam(exam_data)
        if not exam:
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'Failed to create exam.'})
            messages.error(request, 'Failed to create exam')
            
            # Get teacher's classes for the template
            classes = Class.objects.filter(teacher=teacher).order_by('grade_level', 'strand', 'section')
            
            # Build breadcrumbs
            breadcrumbs = build_breadcrumbs(
                ('Dashboard', reverse('teacher_dashboard')),
                ('My Exams', reverse('exam_list')),
                'Create Exam'
            )
            
            return render(request, 'exams/exam_form.html', {
                'form': form,
                'classes': classes,
                'page_breadcrumbs': breadcrumbs
            })
        
        # Create ExamClassAssignment records (Requirement 3.1)
        assigned_classes = form.cleaned_data.get('assigned_classes', [])
        if assigned_classes:
            from exams.models import ExamClassAssignment
            for class_obj in assigned_classes:
                ExamClassAssignment.objects.create(
                    exam=exam,
                    class_assigned=class_obj
                )
            messages.info(
                request,
                f'Exam assigned to {len(assigned_classes)} class(es)'
            )
        
        # Route to appropriate service based on generation method
        if generation_method == 'ai_generate':
            # AI generation - start background task
            import threading
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

            try:
                topic = request.POST.get('ai_topic', '').strip()
                difficulty = request.POST.get('ai_difficulty', 'medium')
                subject = exam_data.get('subject', '')
                grade_level = request.POST.get('ai_grade_level', 'grade_11_12')

                # Build per-type counts (safe int parsing)
                type_counts = {}
                for qt in ['MCQ', 'TRUE_FALSE', 'IDENTIFICATION', 'ENUMERATION', 'ESSAY']:
                    raw = request.POST.get(f'ai_count_{qt}', '0')
                    try:
                        count = int(raw) if raw else 0
                    except (ValueError, TypeError):
                        count = 0
                    if count > 0:
                        type_counts[qt] = count

                if not topic:
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': 'No topic provided for AI generation.'})
                    messages.warning(request, 'No topic provided for AI generation.')
                    return redirect('exam_edit', exam_id=exam.id)

                if not type_counts:
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': 'No question counts specified.'})
                    messages.warning(request, 'No question counts specified.')
                    return redirect('exam_edit', exam_id=exam.id)

                # Create task record
                task = AIGenerationTask.objects.create(
                    exam=exam,
                    topic=topic,
                    subject=subject,
                    difficulty=difficulty,
                    type_counts=type_counts,
                    total_requested=sum(type_counts.values()),
                    status='pending',
                )

                # Start background thread
                thread = threading.Thread(
                    target=_run_ai_generation,
                    args=(task.id, grade_level),
                    daemon=True,
                )
                thread.start()

                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'task_id': task.id,
                        'exam_id': exam.id,
                        'status': 'pending',
                    })

                messages.info(request, 'AI generation started. Questions will appear shortly.')
                return redirect('exam_edit', exam_id=exam.id)

            except Exception as e:
                import traceback
                import logging
                logging.getLogger(__name__).error(f'AI generation error: {traceback.format_exc()}')
                if is_ajax:
                    return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})
                messages.error(request, f'AI generation error: {e}')
                return redirect('exam_edit', exam_id=exam.id)

        else:  # manual
            # Manual entry - redirect to exam editor
            messages.success(
                request,
                f'Exam "{exam.title}" created successfully. Add questions manually.'
            )
            return redirect('exam_edit', exam_id=exam.id)
    
    form = ExamForm(teacher=teacher)
    
    # Get teacher's classes for the template
    classes = Class.objects.filter(teacher=teacher).order_by('grade_level', 'strand', 'section')
    
    # Build breadcrumbs
    breadcrumbs = build_breadcrumbs(
        ('Dashboard', reverse('teacher_dashboard')),
        ('My Exams', reverse('exam_list')),
        'Create Exam'
    )
    
    return render(request, 'exams/exam_form.html', {
        'form': form,
        'classes': classes,
        'page_breadcrumbs': breadcrumbs
    })


def _run_ai_generation(task_id, grade_level='grade_11_12'):
    """Background worker that generates AI questions in batches."""
    import django
    django.db.connections.close_all()

    from services.ai_generation_service import generate_exam_questions

    try:
        task = AIGenerationTask.objects.get(pk=task_id)
        task.status = 'processing'
        task.save(update_fields=['status'])

        questions = generate_exam_questions(
            task.topic, task.subject,
            type_counts=task.type_counts,
            difficulty=task.difficulty,
            grade_level=grade_level,
        )

        questions_by_type = {}
        for i, q in enumerate(questions):
            correct_answer = q.get('correct_answer')
            if correct_answer is None:
                correct_answer = ''
            Question.objects.create(
                exam=task.exam,
                question_type=q['question_type'],
                question_text=q['question_text'],
                options=q.get('options', []),
                correct_answer=correct_answer,
                points=q.get('points', 1.0),
                order_index=i + 1,
            )
            qt = q['question_type']
            questions_by_type[qt] = questions_by_type.get(qt, 0) + 1

        task.status = 'completed'
        task.total_generated = len(questions)
        task.questions_by_type = questions_by_type
        task.completed_at = timezone.now()
        task.save()

    except Exception as e:
        try:
            task = AIGenerationTask.objects.get(pk=task_id)
            task.status = 'failed'
            task.error_message = str(e)
            task.completed_at = timezone.now()
            task.save()
        except Exception:
            pass


@teacher_required
@require_http_methods(["GET"])
def ai_task_status_view(request, task_id):
    """Polling endpoint to check AI generation task status."""
    task = get_object_or_404(AIGenerationTask, pk=task_id)
    teacher = auth_service.get_current_teacher(request)
    if task.exam.created_by.pk != teacher.pk:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    return JsonResponse({
        'task_id': task.id,
        'exam_id': task.exam.id,
        'status': task.status,
        'total_requested': task.total_requested,
        'total_generated': task.total_generated,
        'questions_by_type': task.questions_by_type,
        'error': task.error_message,
    })


@teacher_required
def exam_create_test_view(request):
    """
    Simple test view for exam creation form
    """
    teacher = auth_service.get_current_teacher(request)
    
    if request.method == 'POST':
        # Just redirect back for testing
        messages.success(request, 'Test form submitted successfully!')
        return redirect('exam_create_test')
    
    # Get teacher's classes for the template
    from users.models import Class
    classes = Class.objects.filter(teacher=teacher).order_by('grade_level', 'strand', 'section')
    
    return render(request, 'exams/exam_form_simple.html', {
        'classes': classes
    })



@teacher_required
def exam_edit_view(request, exam_id):
    """
    Edit an existing exam and manage its questions.
    
    This view handles editing for exams created through two methods:
    - File upload
    - Manual entry
    
    All questions can be edited regardless of creation method (Requirement 6.5).
    
    Requirements: 1.2, 6.5, 3.1, 3.5
    """
    exam = get_object_or_404(Exam, pk=exam_id)
    teacher = auth_service.get_current_teacher(request)
    
    # Check if user owns this exam
    if exam.created_by.pk != teacher.pk:
        messages.error(request, 'You do not have permission to edit this exam')
        return redirect('exam_list')
    
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam, teacher=teacher)
        
        if not form.is_valid():
            # Display field-specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
        else:
            # Update exam with validated data
            exam_data = {
                'title': form.cleaned_data['title'],
                'subject': form.cleaned_data.get('subject', ''),
                'quarter': form.cleaned_data.get('quarter'),
                'description': form.cleaned_data.get('description', ''),
                'duration_minutes': form.cleaned_data['duration_minutes']
            }
            updated_exam = exam_service.update_exam(exam_id, exam_data)
            if updated_exam:
                # Update ExamClassAssignment records (Requirements 3.1, 3.5)
                from exams.models import ExamClassAssignment
                assigned_classes = form.cleaned_data.get('assigned_classes', [])
                
                # Get current assignments
                current_assignments = set(
                    ExamClassAssignment.objects.filter(exam=exam).values_list('class_assigned_id', flat=True)
                )
                new_assignments = set(c.id for c in assigned_classes)
                
                # Remove assignments that are no longer selected
                to_remove = current_assignments - new_assignments
                if to_remove:
                    ExamClassAssignment.objects.filter(
                        exam=exam,
                        class_assigned_id__in=to_remove
                    ).delete()
                
                # Add new assignments
                to_add = new_assignments - current_assignments
                for class_id in to_add:
                    ExamClassAssignment.objects.create(
                        exam=exam,
                        class_assigned_id=class_id
                    )
                
                messages.success(request, 'Exam updated successfully')
                exam = updated_exam
            else:
                messages.error(request, 'Failed to update exam')
    else:
        # Pre-populate assigned_classes with current assignments
        from exams.models import ExamClassAssignment
        current_class_ids = ExamClassAssignment.objects.filter(
            exam=exam
        ).values_list('class_assigned_id', flat=True)
        
        form = ExamForm(instance=exam, teacher=teacher)
        form.initial['assigned_classes'] = list(current_class_ids)
    
    # Get questions for this exam
    questions = question_service.get_questions_by_exam(exam_id)
    
    # Serialize question data for JavaScript
    questions_data = []
    for q in questions:
        # Get options - check if it's a field or property
        options_value = None
        if hasattr(q, 'options') and q.options:
            options_value = q.options
        
        # Get correct answer
        correct_answer_value = None
        if hasattr(q, 'correct_answer') and q.correct_answer:
            correct_answer_value = q.correct_answer
        
        q_data = {
            'id': q.id,
            'type': q.question_type,
            'text': q.question_text,
            'points': float(q.points),
            'correct_answer': correct_answer_value,
            'options': options_value,
        }
        questions_data.append(q_data)
    
    logger.info(f"Serialized {len(questions_data)} questions for JavaScript")
    if questions_data:
        logger.info(f"Sample question data: {questions_data[0]}")
    
    # Get current class assignments for display (Requirement 3.1)
    from exams.models import ExamClassAssignment
    from users.models import Class
    assigned_classes = Class.objects.filter(
        exam_assignments__exam=exam
    ).order_by('grade_level', 'strand', 'section')
    
    # Get all teacher's classes for the form
    classes = Class.objects.filter(teacher=teacher).order_by('grade_level', 'strand', 'section')
    
    # Build breadcrumbs
    breadcrumbs = build_breadcrumbs(
        ('Dashboard', reverse('teacher_dashboard')),
        ('My Exams', reverse('exam_list')),
        f'Edit: {exam.title}'
    )
    
    context = {
        'exam': exam,
        'form': form,
        'questions': questions,
        'questions_data': questions_data,
        'question_types': QuestionType.choices,
        'assigned_classes': assigned_classes,
        'classes': classes,
        'page_breadcrumbs': breadcrumbs
    }
    return render(request, 'exams/exam_edit.html', context)


@teacher_required
def exam_detail_view(request, exam_id):
    """
    Display a read-only overview of an exam with quick actions,
    question list, assigned classes, and taker summary.
    """
    exam = get_object_or_404(Exam, pk=exam_id)
    teacher = auth_service.get_current_teacher(request)

    if exam.created_by.pk != teacher.pk:
        messages.error(request, 'You do not have permission to view this exam')
        return redirect('exam_list')

    from attempts.models import Attempt, AttemptStatus
    from exams.models import ExamStudentAssignment
    from users.models import Student

    questions = list(question_service.get_questions_by_exam(exam_id))
    question_count = len(questions)
    total_points = sum(float(question.points) for question in questions)

    assigned_classes = Class.objects.filter(
        exam_assignments__exam=exam
    ).annotate(
        student_count=Count('students', distinct=True)
    ).order_by('grade_level', 'strand', 'section')

    assigned_class_count = assigned_classes.count()
    assigned_class_ids = list(assigned_classes.values_list('id', flat=True))
    assigned_students_count = Student.objects.filter(
        class_assigned_id__in=assigned_class_ids
    ).count() if assigned_class_ids else 0

    student_assignments = list(
        ExamStudentAssignment.objects.filter(exam=exam).select_related(
            'student', 'student__class_assigned'
        ).order_by('student__last_name', 'student__first_name')
    )
    access_mode = 'Assigned classes'
    accessible_students_count = assigned_students_count
    selected_students = []
    if student_assignments:
        access_mode = 'Selected students'
        accessible_students_count = len(student_assignments)
        selected_students = [assignment.student for assignment in student_assignments]

    attempts = Attempt.objects.filter(
        exam=exam
    ).select_related(
        'student', 'student__class_assigned'
    ).order_by('-submitted_at', '-started_at')

    total_attempts = attempts.count()
    in_progress_attempts = attempts.filter(status=AttemptStatus.IN_PROGRESS).count()
    submitted_attempts = attempts.filter(status=AttemptStatus.SUBMITTED).count()
    graded_attempts = attempts.filter(status=AttemptStatus.GRADED).count()
    unique_takers = attempts.filter(
        status__in=[AttemptStatus.SUBMITTED, AttemptStatus.GRADED]
    ).values('student_id').distinct().count()
    flagged_attempts = attempts.filter(is_flagged=True).count()

    average_score = attempts.filter(
        status__in=[AttemptStatus.SUBMITTED, AttemptStatus.GRADED]
    ).aggregate(avg_score=Avg('total_score'))['avg_score']
    average_score = float(average_score) if average_score is not None else None

    recent_attempts_data = []
    for attempt in attempts[:8]:
        percentage = 0
        if total_points > 0:
            percentage = (float(attempt.total_score) / total_points) * 100
        submitted_moment = attempt.submitted_at or attempt.started_at
        recent_attempts_data.append({
            'attempt': attempt,
            'student': attempt.student,
            'class_name': str(attempt.student.class_assigned) if attempt.student.class_assigned else 'No Class',
            'percentage': round(percentage, 2),
            'submitted_display': submitted_moment.strftime('%b %d, %Y %H:%M'),
        })

    breadcrumbs = build_breadcrumbs(
        ('Dashboard', reverse('teacher_dashboard')),
        ('My Exams', reverse('exam_list')),
        f'Exam Details: {exam.title}'
    )

    context = {
        'exam': exam,
        'questions': questions,
        'question_count': question_count,
        'total_points': total_points,
        'assigned_classes': assigned_classes,
        'assigned_class_count': assigned_class_count,
        'assigned_students_count': assigned_students_count,
        'selected_students': selected_students,
        'access_mode': access_mode,
        'accessible_students_count': accessible_students_count,
        'total_attempts': total_attempts,
        'in_progress_attempts': in_progress_attempts,
        'submitted_attempts': submitted_attempts,
        'graded_attempts': graded_attempts,
        'unique_takers': unique_takers,
        'flagged_attempts': flagged_attempts,
        'average_score': average_score,
        'recent_attempts_data': recent_attempts_data,
        'page_breadcrumbs': breadcrumbs,
    }

    return render(request, 'exams/exam_detail.html', context)


@teacher_required
@require_http_methods(["POST"])
def exam_activate_view(request, exam_id):
    """
    Toggle exam activation status.
    When reopening, allows selection of which students can access the exam.
    """
    exam = get_object_or_404(Exam, pk=exam_id)
    
    # Check if user owns this exam
    teacher = auth_service.get_current_teacher(request)
    if exam.created_by.pk != teacher.pk:
        messages.error(request, 'You do not have permission to modify this exam')
        return redirect('exam_list')
    
    # Check if we're reactivating (exam is currently inactive)
    was_inactive = not exam.is_active
    
    # Toggle activation
    updated_exam = activation_service.toggle_activation(exam_id)
    
    if updated_exam:
        if updated_exam.is_active and was_inactive:
            # Exam is being reopened - handle student selection
            from repositories.exam_student_assignment_repository import ExamStudentAssignmentRepository
            from exams.models import ExamClassAssignment
            from users.models import Student
            
            assignment_repo = ExamStudentAssignmentRepository()
            
            # Clear existing assignments (reset access)
            assignment_repo.clear_assignments_for_exam(exam_id)
            
            # Get student IDs from POST
            student_ids = request.POST.getlist('student_ids')
            select_all = request.POST.get('select_all') == '1'
            
            if select_all:
                # Get all students from assigned classes
                assigned_classes = ExamClassAssignment.objects.filter(
                    exam=exam
                ).values_list('class_assigned_id', flat=True)
                
                all_student_ids = list(
                    Student.objects.filter(
                        class_assigned_id__in=assigned_classes
                    ).values_list('id', flat=True)
                )
                
                if all_student_ids:
                    assignment_repo.assign_students_to_exam(exam_id, all_student_ids)
                    messages.success(
                        request,
                        f'Exam "{updated_exam.title}" reopened successfully. All students from assigned classes can now access it.'
                    )
                else:
                    messages.warning(
                        request,
                        f'Exam "{updated_exam.title}" reopened, but no students found in assigned classes.'
                    )
            elif student_ids:
                # Assign selected students
                try:
                    student_ids_int = [int(sid) for sid in student_ids]
                    assignment_repo.assign_students_to_exam(exam_id, student_ids_int)
                    messages.success(
                        request,
                        f'Exam "{updated_exam.title}" reopened successfully. {len(student_ids_int)} selected student(s) can now access it.'
                    )
                except (ValueError, TypeError):
                    messages.error(request, 'Invalid student selection. Please try again.')
            else:
                # No students selected - exam reopened but no one can access
                messages.warning(
                    request,
                    f'Exam "{updated_exam.title}" reopened, but no students were selected. The exam is active but not accessible to any students.'
                )
        elif updated_exam.is_active:
            # Exam was already active, just activated again (shouldn't happen normally)
            messages.success(
                request, 
                f'Exam "{updated_exam.title}" is already active.'
            )
        else:
            # Exam is being closed
            messages.success(
                request, 
                f'Exam "{updated_exam.title}" closed successfully. It is now hidden from students.'
            )
    else:
        messages.error(request, 'Failed to update exam status')
    
    return redirect('exam_list')


@teacher_required
@require_http_methods(["POST"])
def exam_delete_view(request, exam_id):
    """
    Delete an exam with password confirmation for enhanced security.
    
    This view requires the user to enter their password to confirm deletion
    since exams contain important data (questions, student attempts, grades).
    
    Requirements:
    - User must own the exam
    - User must provide correct password
    - Deletes exam and all related data (questions, attempts, grades)
    """
    exam = get_object_or_404(Exam, pk=exam_id)
    teacher = auth_service.get_current_teacher(request)
    
    # Check if user owns this exam
    if exam.created_by.pk != teacher.pk:
        messages.error(request, 'You do not have permission to delete this exam')
        return redirect('exam_list')
    
    # Get password from request
    password = request.POST.get('password', '')
    
    if not password:
        messages.error(request, 'Password is required to delete an exam')
        return redirect('exam_list')
    
    # Verify password
    from django.contrib.auth import authenticate
    user = authenticate(username=teacher.user.username, password=password)
    
    if user is None:
        messages.error(
            request,
            'Incorrect password. Exam deletion cancelled for security.'
        )
        return redirect('exam_list')
    
    # Password verified - proceed with deletion
    exam_title = exam.title
    
    try:
        # Get counts for confirmation message
        question_count = exam.questions.count()
        from attempts.models import Attempt
        attempt_count = Attempt.objects.filter(exam=exam).count()
        
        # Delete the exam (cascade will delete related questions, attempts, etc.)
        exam.delete()
        
        logger.info(
            f"Exam deleted: '{exam_title}' (id={exam_id}) by teacher {teacher.user.username}. "
            f"Deleted {question_count} questions and {attempt_count} attempts."
        )
        
        messages.success(
            request,
            f'Exam "{exam_title}" has been permanently deleted. '
            f'Removed {question_count} questions and {attempt_count} student attempts.'
        )
        
    except Exception as e:
        logger.error(f"Error deleting exam {exam_id}: {str(e)}", exc_info=True)
        messages.error(
            request,
            'An error occurred while deleting the exam. Please try again or contact support.'
        )
    
    return redirect('exam_list')


@teacher_required
@require_http_methods(["POST"])
def question_create_view(request, exam_id):
    """
    Create a new question for an exam.
    """
    exam = get_object_or_404(Exam, pk=exam_id)
    
    # Check if user owns this exam
    teacher = auth_service.get_current_teacher(request)
    if exam.created_by.pk != teacher.pk:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get form data
    question_type = request.POST.get('question_type')
    question_text = request.POST.get('question_text', '').strip()
    points = request.POST.get('points', '1.0')
    
    # Validation
    if not question_text:
        return JsonResponse({'error': 'Question text is required'}, status=400)
    
    try:
        points = float(points)
        if points <= 0:
            return JsonResponse({'error': 'Points must be positive'}, status=400)
    except ValueError:
        return JsonResponse({'error': 'Points must be a valid number'}, status=400)
    
    # Prepare question data based on type
    question_data = {
        'exam': exam,
        'question_type': question_type,
        'question_text': question_text,
        'points': points
    }
    
    # Handle type-specific data
    if question_type == QuestionType.MCQ:
        # Parse MCQ options
        options = []
        correct_answer = request.POST.get('correct_answer', '')
        option_keys = request.POST.getlist('option_keys[]')
        option_values = request.POST.getlist('option_values[]')
        
        for key, value in zip(option_keys, option_values):
            if key and value:
                options.append({'key': key, 'value': value})
        
        if len(options) < 2:
            return JsonResponse({'error': 'MCQ must have at least 2 options'}, status=400)
        if not correct_answer:
            return JsonResponse({'error': 'Correct answer is required'}, status=400)
        
        question_data['options'] = options
        question_data['correct_answer'] = correct_answer
    
    elif question_type == QuestionType.IDENTIFICATION:
        correct_answer = request.POST.get('correct_answer', '').strip()
        if not correct_answer:
            return JsonResponse({'error': 'Correct answer is required'}, status=400)
        # Store as list to support multiple acceptable answers
        question_data['correct_answer'] = [correct_answer]
    
    elif question_type == QuestionType.ENUMERATION:
        correct_answers = request.POST.get('correct_answers', '').strip()
        if not correct_answers:
            return JsonResponse({'error': 'Correct answers are required'}, status=400)
        # Split by comma or newline
        answers = [ans.strip() for ans in correct_answers.replace('\n', ',').split(',') if ans.strip()]
        min_required = request.POST.get('min_required', len(answers))
        try:
            min_required = int(min_required)
        except ValueError:
            min_required = len(answers)
        
        question_data['correct_answer'] = {
            'items': answers,
            'min_required': min_required
        }
    
    elif question_type == QuestionType.TRUE_FALSE:
        correct_answer = request.POST.get('correct_answer', '')
        if correct_answer not in ['true', 'false']:
            return JsonResponse({'error': 'Correct answer must be true or false'}, status=400)
        question_data['correct_answer'] = correct_answer == 'true'
    
    elif question_type == QuestionType.ESSAY:
        # Essay questions don't have a correct answer
        question_data['correct_answer'] = None
    
    # Create question
    question = question_service.create_question(question_data)
    
    if question:
        return JsonResponse({
            'success': True,
            'message': 'Question created successfully',
            'question_id': question.id
        })
    else:
        return JsonResponse({'error': 'Failed to create question'}, status=500)


@teacher_required
@require_http_methods(["POST"])
def question_edit_view(request, question_id):
    """
    Edit an existing question.
    """
    question = get_object_or_404(Question, pk=question_id)
    exam = question.exam
    
    # Check if user owns this exam
    teacher = auth_service.get_current_teacher(request)
    if exam.created_by.pk != teacher.pk:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get form data
    question_type = request.POST.get('question_type')
    question_text = request.POST.get('question_text', '').strip()
    points = request.POST.get('points', '1.0')
    
    # Validation
    if not question_text:
        return JsonResponse({'error': 'Question text is required'}, status=400)
    
    try:
        points = float(points)
        if points <= 0:
            return JsonResponse({'error': 'Points must be positive'}, status=400)
    except ValueError:
        return JsonResponse({'error': 'Points must be a valid number'}, status=400)
    
    # Prepare question data based on type
    question_data = {
        'question_type': question_type,
        'question_text': question_text,
        'points': points
    }
    
    # Handle type-specific data
    if question_type == QuestionType.MCQ:
        # Parse MCQ options
        options = []
        correct_answer = request.POST.get('correct_answer', '')
        option_keys = request.POST.getlist('option_keys[]')
        option_values = request.POST.getlist('option_values[]')
        
        for key, value in zip(option_keys, option_values):
            if key and value:
                options.append({'key': key, 'value': value})
        
        if len(options) < 2:
            return JsonResponse({'error': 'MCQ must have at least 2 options'}, status=400)
        if not correct_answer:
            return JsonResponse({'error': 'Correct answer is required'}, status=400)
        
        question_data['options'] = options
        question_data['correct_answer'] = correct_answer
    
    elif question_type == QuestionType.IDENTIFICATION:
        correct_answer = request.POST.get('correct_answer', '').strip()
        if not correct_answer:
            return JsonResponse({'error': 'Correct answer is required'}, status=400)
        # Store as list to support multiple acceptable answers
        question_data['correct_answer'] = [correct_answer]
    
    elif question_type == QuestionType.ENUMERATION:
        correct_answers = request.POST.get('correct_answers', '').strip()
        if not correct_answers:
            return JsonResponse({'error': 'Correct answers are required'}, status=400)
        # Split by comma or newline
        answers = [ans.strip() for ans in correct_answers.replace('\n', ',').split(',') if ans.strip()]
        min_required = request.POST.get('min_required', len(answers))
        try:
            min_required = int(min_required)
        except ValueError:
            min_required = len(answers)
        
        question_data['correct_answer'] = {
            'items': answers,
            'min_required': min_required
        }
    
    elif question_type == QuestionType.TRUE_FALSE:
        correct_answer = request.POST.get('correct_answer', '')
        if correct_answer not in ['true', 'false']:
            return JsonResponse({'error': 'Correct answer must be true or false'}, status=400)
        question_data['correct_answer'] = correct_answer == 'true'
    
    elif question_type == QuestionType.ESSAY:
        # Essay questions don't have a correct answer
        question_data['correct_answer'] = None
    
    # Update question
    updated_question = question_service.update_question(question_id, question_data)
    
    if updated_question:
        return JsonResponse({
            'success': True,
            'message': 'Question updated successfully',
            'question_id': updated_question.id
        })
    else:
        return JsonResponse({'error': 'Failed to update question'}, status=500)


@teacher_required
@require_http_methods(["POST"])
def question_delete_view(request, question_id):
    """
    Delete a question.
    """
    question = get_object_or_404(Question, pk=question_id)
    
    # Check if user owns the exam
    teacher = auth_service.get_current_teacher(request)
    if question.exam.created_by.pk != teacher.pk:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    exam_id = question.exam.id
    success = question_service.delete_question(question_id)
    
    if success:
        messages.success(request, 'Question deleted successfully')
        return redirect('exam_edit', exam_id=exam_id)
    else:
        messages.error(request, 'Failed to delete question')
        return redirect('exam_edit', exam_id=exam_id)


@teacher_required
@require_http_methods(["POST"])
def ai_generate_questions_view(request, exam_id):
    """Generate questions using AI and add them to an exam."""
    import json as json_module
    from services.ai_generation_service import generate_exam_questions

    exam = get_object_or_404(Exam, pk=exam_id)
    teacher = auth_service.get_current_teacher(request)
    if exam.created_by.pk != teacher.pk:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        body = json_module.loads(request.body)
    except json_module.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    topic = body.get('topic', '').strip()
    subject = body.get('subject', exam.subject or '').strip()
    type_counts = body.get('type_counts', {})
    difficulty = body.get('difficulty', 'medium')
    grade_level = body.get('grade_level', 'grade_11_12')

    if not topic:
        return JsonResponse({'error': 'Topic is required'}, status=400)
    if not type_counts or not any(v > 0 for v in type_counts.values()):
        return JsonResponse({'error': 'At least one question type count must be greater than 0'}, status=400)

    try:
        questions = generate_exam_questions(topic, subject, type_counts=type_counts, difficulty=difficulty, grade_level=grade_level)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

    current_max_order = exam.questions.count()
    created_questions = []

    for i, q in enumerate(questions):
        question = Question.objects.create(
            exam=exam,
            question_type=q['question_type'],
            question_text=q['question_text'],
            options=q.get('options', []),
            correct_answer=q.get('correct_answer') or '',
            points=q.get('points', 1.0),
            order_index=current_max_order + i + 1,
        )
        created_questions.append({
            'id': question.id,
            'question_type': question.question_type,
            'question_text': question.question_text,
            'points': float(question.points),
        })

    return JsonResponse({
        'status': 'ok',
        'message': f'Generated {len(created_questions)} questions',
        'questions': created_questions,
    })


@teacher_required
@require_http_methods(["POST"])
def ai_inline_generate_view(request, exam_id):
    """
    Generate a single question via AI without saving to DB.
    Used for inline question generation in the Add Question modal.
    Returns the question text and metadata for the teacher to review before saving.
    """
    import json as json_module
    from services.ai_generation_service import generate_exam_questions

    exam = get_object_or_404(Exam, pk=exam_id)
    teacher = auth_service.get_current_teacher(request)
    if exam.created_by.pk != teacher.pk:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        body = json_module.loads(request.body)
    except json_module.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    question_type = body.get('question_type', 'MCQ')
    grade_level = body.get('grade_level', 'grade_11_12')
    subject = exam.subject or 'General'

    if question_type not in ['MCQ', 'TRUE_FALSE', 'IDENTIFICATION', 'ENUMERATION', 'ESSAY']:
        return JsonResponse({'error': 'Invalid question type'}, status=400)

    # Build topic context from exam title, description, and existing questions
    topic_parts = [exam.title]
    if exam.description:
        topic_parts.append(exam.description)
    existing_questions = exam.questions.all().order_by('order_index')[:10]
    if existing_questions:
        sample_texts = [q.question_text[:80] for q in existing_questions[:5]]
        topic_parts.append('Related questions already in this exam: ' + '; '.join(sample_texts))
    topic = '. '.join(topic_parts)

    try:
        questions = generate_exam_questions(
            topic=topic,
            subject=subject,
            type_counts={question_type: 1},
            difficulty='medium',
            grade_level=grade_level,
        )
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

    if not questions:
        return JsonResponse({'error': 'AI failed to generate a question. Please try again.'}, status=500)

    q = questions[0]
    return JsonResponse({
        'success': True,
        'question': {
            'question_type': q['question_type'],
            'question_text': q['question_text'],
            'options': q.get('options', []),
            'correct_answer': q.get('correct_answer'),
            'points': q.get('points', 1.0),
        }
    })


@teacher_required
def exam_takers_view(request, exam_id):
    """
    Display all students who have taken a specific exam.
    Shows student name, ID, scores, and answers for grading.
    """
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    exam = get_object_or_404(Exam, pk=exam_id)
    
    # Check if user owns this exam
    teacher = auth_service.get_current_teacher(request)
    if exam.created_by.pk != teacher.pk:
        messages.error(request, 'You do not have permission to view this exam')
        return redirect('exam_list')
    
    # Import necessary models
    from attempts.models import Attempt, AttemptStatus
    from users.models import Student
    
    # Get all attempts for this exam (submitted and graded)
    attempts = Attempt.objects.filter(
        exam_id=exam_id,
        status__in=[AttemptStatus.SUBMITTED, AttemptStatus.GRADED]
    ).select_related('student').order_by('-submitted_at')
    
    # Calculate total possible points
    total_possible_points = sum(float(q.points) for q in exam.questions.all())
    
    # Prepare takers data
    takers_data = []
    for attempt in attempts:
        student = attempt.student
        
        # Calculate percentage
        percentage = 0
        if total_possible_points > 0:
            percentage = (float(attempt.total_score) / total_possible_points) * 100
        
        takers_data.append({
            'attempt': attempt,
            'student': student,
            'percentage': round(percentage, 2),
            'total_possible': total_possible_points
        })
    
    # Implement pagination (20 items per page)
    paginator = Paginator(takers_data, 20)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Build breadcrumbs
    breadcrumbs = build_breadcrumbs(
        ('Dashboard', reverse('teacher_dashboard')),
        ('My Exams', reverse('exam_list')),
        f'{exam.title} - Takers'
    )
    
    context = {
        'exam': exam,
        'takers_data': page_obj.object_list,
        'page_obj': page_obj,
        'total_takers': len(takers_data),
        'total_possible_points': total_possible_points,
        'question_count': exam.questions.count(),
        'page_breadcrumbs': breadcrumbs
    }
    
    return render(request, 'exams/exam_takers.html', context)


@teacher_required
def get_exam_students_view(request, exam_id):
    """
    API endpoint to get list of students from classes assigned to an exam.
    Used by the reopen modal to populate student selection.
    """
    exam = get_object_or_404(Exam, pk=exam_id)
    
    # Check if user owns this exam
    teacher = auth_service.get_current_teacher(request)
    if exam.created_by.pk != teacher.pk:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get classes assigned to this exam
    from exams.models import ExamClassAssignment
    assigned_classes = ExamClassAssignment.objects.filter(
        exam=exam
    ).select_related('class_assigned').values_list('class_assigned_id', flat=True)
    
    # Get all students from assigned classes
    from users.models import Student
    students = Student.objects.filter(
        class_assigned_id__in=assigned_classes
    ).order_by('last_name', 'first_name')
    
    # Serialize student data
    students_data = []
    for student in students:
        students_data.append({
            'id': student.id,
            'school_id': student.school_id,
            'full_name': student.get_full_name(),
            'class_name': str(student.class_assigned) if student.class_assigned else 'No Class'
        })
    
    return JsonResponse({
        'success': True,
        'students': students_data,
        'count': len(students_data)
    })


@teacher_required
def item_summary_view(request, exam_id):
    """
    Display DepEd-style Item Summary Sheet with item analysis.
    Shows difficulty levels, action needed, and competency summary.
    Optionally generates AI-powered teacher analysis.
    """
    from services.item_analysis_service import ItemAnalysisService

    exam = get_object_or_404(Exam, pk=exam_id)

    teacher = auth_service.get_current_teacher(request)
    if exam.created_by.pk != teacher.pk:
        messages.error(request, 'You do not have permission to view this exam')
        return redirect('exam_list')

    service = ItemAnalysisService()
    summary_data = service.get_item_summary(exam_id)

    if summary_data is None:
        messages.error(request, 'Exam not found')
        return redirect('exam_list')

    breadcrumbs = build_breadcrumbs(
        ('Dashboard', reverse('teacher_dashboard')),
        ('My Exams', reverse('exam_list')),
        (exam.title, reverse('exam_takers', args=[exam_id])),
        'Item Summary'
    )

    context = {
        'exam': exam,
        'summary': summary_data,
        'page_breadcrumbs': breadcrumbs,
    }

    return render(request, 'exams/item_summary.html', context)


@teacher_required
@require_http_methods(["POST"])
def item_summary_ai_analyze_view(request, exam_id):
    """
    AJAX endpoint to generate AI-powered teacher analysis for item summary.
    Returns JSON with the analysis results.
    """
    from services.item_analysis_service import ItemAnalysisService

    exam = get_object_or_404(Exam, pk=exam_id)

    teacher = auth_service.get_current_teacher(request)
    if exam.created_by.pk != teacher.pk:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    service = ItemAnalysisService()
    summary_data = service.get_item_summary(exam_id)

    if not summary_data or not summary_data.get('has_data'):
        return JsonResponse({'error': 'No graded attempts available for analysis'}, status=400)

    analysis = service.generate_ai_analysis(summary_data)
    if analysis is None:
        return JsonResponse({
            'error': 'AI analysis unavailable. Check your AI API settings in Superadmin > AI Settings.'
        }, status=503)

    return JsonResponse({'success': True, 'analysis': analysis})


@teacher_required
def mps_entrypoint_view(request):
    """
    Entry point for the teacher MPS report.
    Redirects to the newest exam with a quarter-based MPS report.
    """
    from exams.models import Exam
    from attempts.models import AttemptStatus
    from services.item_analysis_service import ItemAnalysisService

    teacher = auth_service.get_current_teacher(request)

    candidate_exams = Exam.objects.filter(
        created_by=teacher,
        quarter__isnull=False,
        attempts__status=AttemptStatus.GRADED,
    ).select_related('quarter').distinct().order_by('-created_at', '-id')

    service = ItemAnalysisService()
    for exam in candidate_exams:
        summary_data = service.get_mps_report_summary(exam.id)
        if summary_data and summary_data.get('has_data'):
            return redirect('mps_report', exam_id=exam.id)

    messages.info(request, 'No graded quarter MPS reports are available yet.')
    return redirect('exam_list')


@teacher_required
def mps_report_view(request, exam_id):
    """
    Display a quarter-based DepEd-style MPS (Mean Percentage Score) report.
    The report aggregates all exams in the same quarter as the selected exam.
    """
    from services.item_analysis_service import ItemAnalysisService

    exam = get_object_or_404(Exam, pk=exam_id)

    teacher = auth_service.get_current_teacher(request)
    if exam.created_by.pk != teacher.pk:
        messages.error(request, 'You do not have permission to view this exam')
        return redirect('exam_list')

    service = ItemAnalysisService()
    summary_data = service.get_mps_report_summary(exam_id)

    if summary_data is None:
        messages.error(request, 'Exam not found')
        return redirect('exam_list')

    breadcrumbs = build_breadcrumbs(
        ('Dashboard', reverse('teacher_dashboard')),
        ('My Exams', reverse('exam_list')),
        (exam.title, reverse('exam_takers', args=[exam_id])),
        'MPS Report'
    )

    mps_gauge_offset = 377
    quarter_summary = summary_data.get('quarter_summary')
    if summary_data.get('has_data') and quarter_summary:
        mps_gauge_offset = round(377 - (377 * quarter_summary['overall_mps'] / 100))

    context = {
        'exam': exam,
        'summary': summary_data,
        'mps_gauge_offset': mps_gauge_offset,
        'page_breadcrumbs': breadcrumbs,
    }

    return render(request, 'exams/mps_report.html', context)


def _configure_docx_branding(document, report_title, exam, meta_lines, footer_label):
    import os
    from django.conf import settings
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Inches, Pt, RGBColor

    brand_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'brand.png')

    section = document.sections[0]
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    section.header_distance = Cm(0.2)
    section.footer_distance = Cm(0.2)

    header = section.header
    footer = section.footer
    header.is_linked_to_previous = False
    footer.is_linked_to_previous = False

    header_paragraph = header.paragraphs[0]
    header_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    header_paragraph.paragraph_format.space_before = Pt(0)
    header_paragraph.paragraph_format.space_after = Pt(0)
    if os.path.isfile(brand_path):
        logo_run = header_paragraph.add_run()
        logo_run.add_picture(brand_path, width=Inches(1.05))
    else:
        placeholder_run = header_paragraph.add_run('School Logo')
        placeholder_run.bold = True
        placeholder_run.font.size = Pt(9)
        placeholder_run.font.color.rgb = RGBColor(90, 90, 90)
    if os.path.isfile(brand_path):
        placeholder_paragraph = header.add_paragraph()
        placeholder_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        placeholder_paragraph.paragraph_format.space_before = Pt(0)
        placeholder_paragraph.paragraph_format.space_after = Pt(0)
        placeholder_run = placeholder_paragraph.add_run('School Logo')
        placeholder_run.bold = True
        placeholder_run.font.size = Pt(8)
        placeholder_run.font.color.rgb = RGBColor(90, 90, 90)

    footer_paragraph = footer.paragraphs[0]
    footer_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_paragraph.paragraph_format.space_before = Pt(0)
    footer_paragraph.paragraph_format.space_after = Pt(0)
    footer_run = footer_paragraph.add_run('Generated by: seamless.dpdns.org')
    footer_run.font.size = Pt(8)
    footer_run.font.color.rgb = RGBColor(107, 114, 128)


def _write_docx_question_block(document, question, question_number):
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt, RGBColor

    title_paragraph = document.add_paragraph()
    title_paragraph.paragraph_format.space_after = Pt(2)
    title_paragraph.add_run(f'{question_number}. ').bold = True
    question_run = title_paragraph.add_run(question.question_text)
    question_run.font.size = Pt(11)
    question_run.font.color.rgb = RGBColor(31, 41, 55)

    meta_paragraph = document.add_paragraph()
    meta_paragraph.paragraph_format.space_after = Pt(4)
    meta_paragraph.paragraph_format.left_indent = Cm(0.3)
    meta_run = meta_paragraph.add_run(
        f'{question.get_question_type_display()} • {question.points} point{"s" if question.points != 1 else ""}'
    )
    meta_run.italic = True
    meta_run.font.size = Pt(9)
    meta_run.font.color.rgb = RGBColor(107, 114, 128)

    if question.question_type == QuestionType.MCQ:
        for option in question.options or []:
            option_paragraph = document.add_paragraph()
            option_paragraph.paragraph_format.left_indent = Cm(0.9)
            option_paragraph.paragraph_format.space_after = Pt(1)
            option_run = option_paragraph.add_run(f"{option.get('key', '')}. {option.get('value', '')}")
            option_run.font.size = Pt(10)
    elif question.question_type == QuestionType.TRUE_FALSE:
        for label in ('True', 'False'):
            option_paragraph = document.add_paragraph()
            option_paragraph.paragraph_format.left_indent = Cm(0.9)
            option_paragraph.paragraph_format.space_after = Pt(1)
            option_run = option_paragraph.add_run(f'☐ {label}')
            option_run.font.size = Pt(10)
    else:
        answer_paragraph = document.add_paragraph()
        answer_paragraph.paragraph_format.left_indent = Cm(0.9)
        answer_paragraph.paragraph_format.space_after = Pt(4)
        answer_run = answer_paragraph.add_run('Answer: ______________________________')
        answer_run.font.size = Pt(10)


@teacher_required
@require_http_methods(["GET"])
def exam_export_word_view(request, exam_id):
    """
    Export a printable exam paper as a Word document.
    Includes exam metadata, a branded header/footer, and the full question list.
    """
    import os
    from io import BytesIO
    from django.conf import settings
    from django.http import HttpResponse
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt

    exam = get_object_or_404(Exam, pk=exam_id)

    teacher = auth_service.get_current_teacher(request)
    if exam.created_by.pk != teacher.pk:
        messages.error(request, 'Permission denied')
        return redirect('exam_list')

    questions = list(question_service.get_questions_by_exam(exam_id))

    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    _configure_docx_branding(
        doc,
        'EXAMINATION PAPER',
        exam,
        [
            ('Exam Title', exam.title),
            ('Subject', exam.subject or 'Not specified'),
            ('Duration', f'{exam.duration_minutes} minutes'),
            ('Teacher', exam.created_by.user.get_full_name() or exam.created_by.user.username),
        ],
        'Exam Export',
    )

    intro_title = doc.add_paragraph()
    intro_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    intro_run = intro_title.add_run('EXAMINATION PAPER')
    intro_run.bold = True
    intro_run.font.size = Pt(16)

    exam_meta = doc.add_table(rows=4, cols=2)
    exam_meta.style = 'Table Grid'
    meta_rows = [
        ('Exam Title', exam.title),
        ('Subject', exam.subject or 'Not specified'),
        ('Duration', f'{exam.duration_minutes} minutes'),
        ('Instructions', 'Read each item carefully and answer all questions.'),
    ]
    for row_index, (label, value) in enumerate(meta_rows):
        row = exam_meta.rows[row_index]
        row.cells[0].text = label
        row.cells[1].text = value
        for run in row.cells[0].paragraphs[0].runs:
            run.bold = True
            run.font.size = Pt(10)
        for run in row.cells[1].paragraphs[0].runs:
            run.font.size = Pt(10)

    doc.add_paragraph()
    questions_title = doc.add_paragraph()
    questions_title.paragraph_format.space_after = Pt(6)
    questions_run = questions_title.add_run('Questions')
    questions_run.bold = True
    questions_run.font.size = Pt(13)

    if questions:
        for index, question in enumerate(questions, start=1):
            _write_docx_question_block(doc, question, index)
    else:
        empty_paragraph = doc.add_paragraph()
        empty_paragraph.add_run('No questions have been added to this exam yet.')

    output = BytesIO()
    doc.save(output)
    output.seek(0)

    safe_title = exam.title.replace(' ', '_')[:30]
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename="Exam_{safe_title}.docx"'
    return response


@teacher_required
@require_http_methods(["GET"])
def mps_export_excel_view(request, exam_id):
    """
    Export MPS report to Excel with DepEd-style formatting.
    Includes overall MPS, per-class breakdown, and item-level data.
    """
    import os
    from decimal import Decimal
    from io import BytesIO
    from django.conf import settings
    from django.http import HttpResponse
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    from services.item_analysis_service import ItemAnalysisService

    # Safely import XlImage – requires Pillow
    XlImage = None
    try:
        from openpyxl.drawing.image import Image as XlImage
    except Exception:
        pass

    def _safe_val(v):
        """Coerce a value to a type openpyxl can serialise."""
        if isinstance(v, Decimal):
            return float(v)
        return v

    exam = get_object_or_404(Exam, pk=exam_id)

    teacher = auth_service.get_current_teacher(request)
    if teacher is None or exam.created_by.pk != teacher.pk:
        messages.error(request, 'Permission denied')
        return redirect('exam_list')

    service = ItemAnalysisService()
    summary_data = service.get_mps_report_summary(exam_id)

    if not summary_data or not summary_data.get('has_data'):
        messages.warning(request, 'No graded attempts to export')
        return redirect('mps_report', exam_id=exam_id)

    quarter_summary = summary_data.get('quarter_summary')
    quarter_summaries = summary_data.get('quarter_summaries') or []
    quarter_matrix = summary_data.get('quarter_matrix')

    wb = Workbook()
    wb.remove(wb.active)

    brand_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'brand.png')
    has_brand = XlImage is not None and os.path.isfile(brand_path)

    def _add_brand_image(sheet, cell_ref='A1'):
        """Safely add brand image to a sheet; silently skip on failure."""
        if not has_brand:
            return False
        try:
            img = XlImage(brand_path)
            img.width = 120
            img.height = 60
            sheet.add_image(img, cell_ref)
            return True
        except Exception:
            logger.warning('Could not load brand.png for Excel export', exc_info=True)
            return False

    title_font = Font(name='Calibri', bold=True, size=14)
    header_font = Font(name='Calibri', bold=True, size=12)
    subheader_font = Font(name='Calibri', bold=True, size=11)
    header_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
    header_text = Font(name='Calibri', bold=True, size=11, color='FFFFFF')
    green_font = Font(name='Calibri', bold=True, color='006100')
    yellow_font = Font(name='Calibri', bold=True, color='7F6000')
    red_font = Font(name='Calibri', bold=True, color='9C0006')
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    def get_mps_font(mps_val):
        if mps_val >= 75:
            return green_font
        elif mps_val >= 50:
            return yellow_font
        return red_font

    def get_performance_level(mps_val):
        if mps_val >= 75:
            return 'Mastered'
        elif mps_val >= 50:
            return 'Nearing Mastery'
        return 'Low Mastery'

    # --- Sheet 0: Quarter Overview ---
    if quarter_summaries:
        wso = wb.create_sheet(title='Quarter Overview')
        row = 1

        if _add_brand_image(wso):
            row = 5

        wso.cell(row=row, column=1, value='QUARTER MPS OVERVIEW')
        wso.cell(row=row, column=1).font = title_font
        wso.merge_cells(start_row=row, start_column=1, end_row=row, end_column=8)
        row += 2

        overview_headers = ['Quarter', 'Exam Count', 'Graded Exams', 'Attempts', 'Total Correct', 'Total Possible', 'MPS']
        for col_idx, h in enumerate(overview_headers, 1):
            cell = wso.cell(row=row, column=col_idx, value=h)
            cell.font = header_text
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
        row += 1

        for q_summary in quarter_summaries:
            row_data = [
                q_summary['quarter_name'],
                q_summary['exam_count'],
                q_summary['graded_exam_count'],
                q_summary['graded_attempts'],
                q_summary['total_correct'],
                q_summary['total_possible_answers'],
                f"{q_summary['overall_mps']}%",
            ]
            for col_idx, value in enumerate(row_data, 1):
                cell = wso.cell(row=row, column=col_idx, value=_safe_val(value))
                cell.border = thin_border
                if col_idx in (2, 3, 4, 5, 6, 7):
                    cell.alignment = Alignment(horizontal='center')
                if col_idx == 7:
                    cell.font = get_mps_font(q_summary['overall_mps'])
            if quarter_summary and q_summary.get('quarter_id') == quarter_summary.get('quarter_id'):
                for col_idx in range(1, 8):
                    wso.cell(row=row, column=col_idx).fill = PatternFill(start_color='EEF2FF', end_color='EEF2FF', fill_type='solid')
            row += 1

        for i, width in enumerate([24, 12, 12, 12, 14, 16, 12], 1):
            wso.column_dimensions[get_column_letter(i)].width = width

    # --- Sheet 1: Quarter Summary ---
    ws = wb.create_sheet(title='Quarter Summary')
    row = 1

    if _add_brand_image(ws):
        row = 5

    ws.cell(row=row, column=1, value='QUARTER MEAN PERCENTAGE SCORE (MPS) REPORT')
    ws.cell(row=row, column=1).font = title_font
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
    row += 2

    if quarter_summary:
        info_labels = [
            ('Quarter:', quarter_summary['quarter_name']),
            ('Subject:', exam.subject or 'Not specified'),
            ('Teacher:', exam.created_by.user.get_full_name() or exam.created_by.user.username),
            ('No. of Learners:', str(quarter_summary['graded_attempts'])),
            ('Quarter Exam Count:', str(quarter_summary['exam_count'])),
            ('Quarter MPS:', f"{quarter_summary['overall_mps']}%"),
        ]
        for label, value in info_labels:
            ws.cell(row=row, column=1, value=label)
            ws.cell(row=row, column=1).font = Font(bold=True)
            ws.cell(row=row, column=2, value=value)
            row += 1

        row += 1
        ws.cell(row=row, column=1, value='QUARTER SUMMARY')
        ws.cell(row=row, column=1).font = header_font
        row += 1

        quarter_headers = ['Exam', 'Subject', 'Attempts', 'Items', 'MPS']
        for col_idx, h in enumerate(quarter_headers, 1):
            cell = ws.cell(row=row, column=col_idx, value=h)
            cell.font = header_text
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
        row += 1

        for exam_summary in quarter_summary['exams']:
            row_data = [
                exam_summary['title'],
                exam_summary['subject'],
                exam_summary['total_learners'],
                exam_summary['total_items'],
                f"{exam_summary['overall_mps']}%" if exam_summary['has_data'] else 'No data',
            ]
            for col_idx, value in enumerate(row_data, 1):
                cell = ws.cell(row=row, column=col_idx, value=_safe_val(value))
                cell.border = thin_border
                if col_idx in (3, 4, 5):
                    cell.alignment = Alignment(horizontal='center')
                if col_idx == 5 and exam_summary['has_data']:
                    cell.font = get_mps_font(exam_summary['overall_mps'])
            row += 1

        row += 1
        ws.cell(row=row, column=1, value='MPS BY EXAM')
        ws.cell(row=row, column=1).font = header_font
        row += 1

        exam_headers = ['Exam', 'Learners', 'Total Correct', 'Total Possible', 'MPS', 'Level']
        for col_idx, h in enumerate(exam_headers, 1):
            cell = ws.cell(row=row, column=col_idx, value=h)
            cell.font = header_text
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
        row += 1

        for exam_summary in quarter_summary['exams']:
            row_data = [
                exam_summary['title'],
                exam_summary['total_learners'],
                exam_summary['total_correct'],
                exam_summary['total_possible_answers'],
                f"{exam_summary['overall_mps']}%" if exam_summary['has_data'] else 'No data',
                get_performance_level(exam_summary['overall_mps']),
            ]
            for col_idx, value in enumerate(row_data, 1):
                cell = ws.cell(row=row, column=col_idx, value=_safe_val(value))
                cell.border = thin_border
                if col_idx in (2, 3, 4, 5, 6):
                    cell.alignment = Alignment(horizontal='center')
                if col_idx == 5 and exam_summary['has_data']:
                    cell.font = get_mps_font(exam_summary['overall_mps'])
            row += 1

        for i, width in enumerate([28, 14, 14, 14, 12, 16], 1):
            ws.column_dimensions[get_column_letter(i)].width = width

    row += 2
    ws.cell(row=row, column=1, value='Prepared by:')
    ws.cell(row=row, column=1).font = Font(bold=True, size=10)
    row += 1
    ws.cell(row=row, column=1, value='________________________________________')
    ws.cell(row=row, column=1).font = Font(size=10)
    row += 1
    ws.cell(row=row, column=1, value='Name of Teacher:')
    ws.cell(row=row, column=1).font = Font(bold=True, size=10)
    ws.cell(row=row, column=2, value=exam.created_by.user.get_full_name() or exam.created_by.user.username)
    ws.cell(row=row, column=2).font = Font(bold=True, size=10)

    # --- Sheet 2: Quarter Matrix ---
    if quarter_matrix and quarter_matrix['students']:
        ws3 = wb.create_sheet(title='Quarter Matrix')
        row = 1

        if _add_brand_image(ws3):
            row = 5

        ws3.cell(row=row, column=1, value='QUARTER STUDENT-BY-ITEM RESPONSE MATRIX')
        ws3.cell(row=row, column=1).font = title_font
        ws3.merge_cells(start_row=row, start_column=1, end_row=row, end_column=quarter_matrix['total_items'] + 4)
        row += 1
        ws3.cell(row=row, column=1, value=f'Quarter: {quarter_summary["quarter_name"] if quarter_summary else "Not specified"}')
        ws3.cell(row=row, column=1).font = subheader_font
        row += 1
        ws3.cell(row=row, column=1, value=f'No. of Learners: {quarter_matrix["total_learners"]} | No. of Items: {quarter_matrix["total_items"]}')
        row += 2

        total_items = quarter_matrix['total_items']
        header_row_1 = row
        header_row_2 = row + 1

        ws3.cell(row=header_row_1, column=1, value='#')
        ws3.cell(row=header_row_1, column=2, value='Student Name')
        for cell in (ws3.cell(row=header_row_1, column=1), ws3.cell(row=header_row_1, column=2)):
            cell.font = header_text
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
        ws3.merge_cells(start_row=header_row_1, start_column=1, end_row=header_row_2, end_column=1)
        ws3.merge_cells(start_row=header_row_1, start_column=2, end_row=header_row_2, end_column=2)

        col_cursor = 3
        for section in quarter_matrix['exam_sections']:
            if section['item_count'] <= 0:
                continue
            start_col = col_cursor
            end_col = col_cursor + section['item_count'] - 1
            ws3.cell(row=header_row_1, column=start_col, value=section['title'])
            ws3.merge_cells(start_row=header_row_1, start_column=start_col, end_row=header_row_1, end_column=end_col)
            top_cell = ws3.cell(row=header_row_1, column=start_col)
            top_cell.font = header_text
            top_cell.fill = header_fill
            top_cell.alignment = Alignment(horizontal='center')
            top_cell.border = thin_border
            ws3.cell(row=header_row_2, column=start_col, value=f"{section['overall_mps']}% MPS")
            ws3.merge_cells(start_row=header_row_2, start_column=start_col, end_row=header_row_2, end_column=end_col)
            second_cell = ws3.cell(row=header_row_2, column=start_col)
            second_cell.font = header_text
            second_cell.fill = header_fill
            second_cell.alignment = Alignment(horizontal='center')
            second_cell.border = thin_border
            col_cursor += section['item_count']

        total_col = total_items + 3
        pct_col = total_items + 4
        for col_idx, label in [(total_col, 'Total'), (pct_col, '%')]:
            ws3.cell(row=header_row_1, column=col_idx, value=label)
            ws3.cell(row=header_row_1, column=col_idx).font = header_text
            ws3.cell(row=header_row_1, column=col_idx).fill = header_fill
            ws3.cell(row=header_row_1, column=col_idx).alignment = Alignment(horizontal='center')
            ws3.cell(row=header_row_1, column=col_idx).border = thin_border
            ws3.merge_cells(start_row=header_row_1, start_column=col_idx, end_row=header_row_2, end_column=col_idx)

        for item_idx, item in enumerate(quarter_matrix['items']):
            cell = ws3.cell(row=header_row_2, column=item_idx + 3, value=item['exam_item_no'])
            cell.font = header_text
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border

        row = header_row_2 + 1
        green_fill = PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid')
        red_fill = PatternFill(start_color='FCE4EC', end_color='FCE4EC', fill_type='solid')

        for idx, student in enumerate(quarter_matrix['students'], 1):
            ws3.cell(row=row, column=1, value=idx)
            ws3.cell(row=row, column=1).border = thin_border
            ws3.cell(row=row, column=1).alignment = Alignment(horizontal='center')

            ws3.cell(row=row, column=2, value=student['name'])
            ws3.cell(row=row, column=2).border = thin_border

            for item_idx, mark in enumerate(student['responses']):
                col = item_idx + 3
                cell = ws3.cell(row=row, column=col, value=mark)
                cell.alignment = Alignment(horizontal='center')
                cell.border = thin_border
                cell.fill = green_fill if mark == 1 else red_fill

            cell_total = ws3.cell(row=row, column=total_col, value=student['total_correct'])
            cell_total.font = Font(bold=True)
            cell_total.alignment = Alignment(horizontal='center')
            cell_total.border = thin_border

            cell_pct = ws3.cell(row=row, column=pct_col, value=f"{student['percent']}%")
            cell_pct.alignment = Alignment(horizontal='center')
            cell_pct.border = thin_border
            if student['percent'] >= 75:
                cell_pct.font = green_font
            elif student['percent'] < 50:
                cell_pct.font = red_font

            row += 1

        footer_fill = PatternFill(start_color='D6E4F0', end_color='D6E4F0', fill_type='solid')
        ws3.cell(row=row, column=1, value='')
        ws3.cell(row=row, column=2, value='Total Correct')
        ws3.cell(row=row, column=2).font = Font(bold=True)
        ws3.cell(row=row, column=2).border = thin_border
        ws3.cell(row=row, column=2).fill = footer_fill

        for item_idx, count in enumerate(quarter_matrix['per_item_correct']):
            col = item_idx + 3
            cell = ws3.cell(row=row, column=col, value=count)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
            cell.fill = footer_fill

        cell = ws3.cell(row=row, column=total_col, value=quarter_matrix['total_correct'])
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
        cell.fill = footer_fill
        row += 1

        ws3.cell(row=row, column=2, value='% Correct')
        ws3.cell(row=row, column=2).font = Font(bold=True)
        ws3.cell(row=row, column=2).border = thin_border
        ws3.cell(row=row, column=2).fill = footer_fill

        for item_idx, pct in enumerate(quarter_matrix['per_item_percent']):
            col = item_idx + 3
            cell = ws3.cell(row=row, column=col, value=f"{pct}%")
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
            cell.fill = footer_fill
            if pct >= 75:
                cell.font = green_font
            elif pct < 50:
                cell.font = red_font

        cell = ws3.cell(row=row, column=pct_col, value=f"{quarter_matrix['overall_mps']}%")
        cell.font = Font(bold=True, color='1F4E79')
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
        cell.fill = footer_fill
        row += 2

        ws3.cell(row=row, column=1, value=f'MPS = ({quarter_matrix["total_correct"]} / {quarter_matrix["total_possible_answers"]}) x 100 = {quarter_matrix["overall_mps"]}%')
        ws3.cell(row=row, column=1).font = Font(bold=True, size=12)

        ws3.column_dimensions['A'].width = 5
        ws3.column_dimensions['B'].width = 28
        for i in range(3, total_items + 5):
            ws3.column_dimensions[get_column_letter(i)].width = 5
        ws3.column_dimensions[get_column_letter(total_col)].width = 8
        ws3.column_dimensions[get_column_letter(pct_col)].width = 8

    # Write to response
    output = BytesIO()
    try:
        wb.save(output)
    except Exception:
        logger.error('openpyxl failed to save MPS Excel workbook', exc_info=True)
        messages.error(request, 'Failed to generate Excel file. Please try again.')
        return redirect('mps_report', exam_id=exam_id)
    output.seek(0)

    safe_title = exam.title.replace(' ', '_')[:30]
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="MPS_Report_{safe_title}.xlsx"'
    return response


@teacher_required
@require_http_methods(["GET"])
def mps_export_word_view(request, exam_id):
    """
    Export MPS report to Word (DOCX) with DepEd-style formatting.
    Includes overall MPS, per-class breakdown, and item-level data.
    """
    from io import BytesIO
    from django.http import HttpResponse
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from services.item_analysis_service import ItemAnalysisService

    exam = get_object_or_404(Exam, pk=exam_id)

    teacher = auth_service.get_current_teacher(request)
    if exam.created_by.pk != teacher.pk:
        messages.error(request, 'Permission denied')
        return redirect('exam_list')

    service = ItemAnalysisService()
    summary_data = service.get_mps_report_summary(exam_id)

    if not summary_data or not summary_data.get('has_data'):
        messages.warning(request, 'No graded attempts to export')
        return redirect('mps_report', exam_id=exam_id)

    quarter_summary = summary_data.get('quarter_summary')
    quarter_summaries = summary_data.get('quarter_summaries') or []
    quarter_matrix = summary_data.get('quarter_matrix')

    doc = Document()

    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    _configure_docx_branding(
        doc,
        'QUARTER MEAN PERCENTAGE SCORE (MPS) REPORT',
        exam,
        [
            ('Quarter', quarter_summary['quarter_name'] if quarter_summary else 'Not specified'),
            ('Subject', exam.subject or 'Not specified'),
            ('Teacher', exam.created_by.user.get_full_name() or exam.created_by.user.username),
            ('No. of Learners', quarter_summary['graded_attempts'] if quarter_summary else 0),
            ('Quarter Exams', quarter_summary['exam_count'] if quarter_summary else 0),
        ],
        'Quarter MPS Report',
    )

    from docx.oxml.ns import qn

    def set_cell_shading(cell, color):
        shading_elm = cell._element.get_or_add_tcPr()
        shading = shading_elm.makeelement(qn('w:shd'), {
            qn('w:val'): 'clear',
            qn('w:color'): 'auto',
            qn('w:fill'): color,
        })
        shading_elm.append(shading)

    def get_performance_level(mps_val):
        if mps_val >= 75:
            return 'Mastered'
        elif mps_val >= 50:
            return 'Nearing Mastery'
        return 'Low Mastery'

    # Title
    title = doc.add_heading('QUARTER MEAN PERCENTAGE SCORE (MPS) REPORT', level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    # Exam info block
    info_block = [
        ('School', '________________________'),
        ('Teacher', exam.created_by.user.get_full_name() or exam.created_by.user.username),
        ('Subject', exam.subject or 'Not specified'),
        ('Quarter', quarter_summary['quarter_name'] if quarter_summary else 'Not specified'),
        ('No. of Learners', str(quarter_summary['graded_attempts'] if quarter_summary else 0)),
        ('Focus Exam', exam.title),
        ('No. of Items', str(quarter_summary['total_items'] if quarter_summary else 0)),
    ]
    for label, value in info_block:
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(2)
        label_run = paragraph.add_run(f'{label}: ')
        label_run.bold = True
        label_run.font.size = Pt(10)
        value_run = paragraph.add_run(str(value))
        value_run.font.size = Pt(10)

    doc.add_paragraph()

    # Quarter overview
    if quarter_summaries:
        doc.add_heading('Quarter MPS Overview', level=2)
        overview_table = doc.add_table(rows=1, cols=7)
        overview_table.style = 'Table Grid'
        overview_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        overview_headers = ['Quarter', 'Exam Count', 'Graded Exams', 'Attempts', 'Total Correct', 'Total Possible', 'MPS']
        header_row = overview_table.rows[0]
        for idx, h in enumerate(overview_headers):
            cell = header_row.cells[idx]
            cell.text = h
            set_cell_shading(cell, '1F4E79')
            for para in cell.paragraphs:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:
                    run.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)
                    run.font.size = Pt(9)
        for q_summary in quarter_summaries:
            row = overview_table.add_row()
            row_data = [
                q_summary['quarter_name'],
                str(q_summary['exam_count']),
                str(q_summary['graded_exam_count']),
                str(q_summary['graded_attempts']),
                str(q_summary['total_correct']),
                str(q_summary['total_possible_answers']),
                f"{q_summary['overall_mps']}%",
            ]
            for idx, value in enumerate(row_data):
                cell = row.cells[idx]
                cell.text = value
                for para in cell.paragraphs:
                    if idx > 0:
                        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs:
                        run.font.size = Pt(9)
                        if idx == 6:
                            run.bold = True
                            if q_summary['overall_mps'] >= 75:
                                run.font.color.rgb = RGBColor(0, 97, 0)
                            elif q_summary['overall_mps'] >= 50:
                                run.font.color.rgb = RGBColor(127, 96, 0)
                            else:
                                run.font.color.rgb = RGBColor(156, 0, 6)
        doc.add_paragraph()

    # Selected quarter summary
    if quarter_summary:
        doc.add_heading(f'Quarter Summary - {quarter_summary["quarter_name"]}', level=2)
        quarter_meta = doc.add_paragraph()
        quarter_meta.paragraph_format.space_after = Pt(2)
        quarter_meta.add_run('Quarter MPS: ').bold = True
        quarter_meta.add_run(f'{quarter_summary["overall_mps"]}%')

        quarter_meta_2 = doc.add_paragraph()
        quarter_meta_2.paragraph_format.space_after = Pt(4)
        quarter_meta_2.add_run('Graded Attempts: ').bold = True
        quarter_meta_2.add_run(str(quarter_summary['graded_attempts']))

        quarter_table = doc.add_table(rows=1, cols=5)
        quarter_table.style = 'Table Grid'
        quarter_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        quarter_headers = ['Exam', 'Subject', 'Attempts', 'Items', 'MPS']
        header_row = quarter_table.rows[0]
        for idx, h in enumerate(quarter_headers):
            cell = header_row.cells[idx]
            cell.text = h
            set_cell_shading(cell, '1F4E79')
            for para in cell.paragraphs:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:
                    run.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)
                    run.font.size = Pt(9)

        for exam_summary in quarter_summary['exams']:
            row = quarter_table.add_row()
            row_data = [
                exam_summary['title'],
                exam_summary['subject'],
                str(exam_summary['total_learners']),
                str(exam_summary['total_items']),
                f"{exam_summary['overall_mps']}%" if exam_summary['has_data'] else 'No data',
            ]
            for idx, value in enumerate(row_data):
                cell = row.cells[idx]
                cell.text = value
                for para in cell.paragraphs:
                    if idx > 0:
                        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs:
                        run.font.size = Pt(9)
                        if idx == 4 and exam_summary['has_data']:
                            if exam_summary['overall_mps'] >= 75:
                                run.font.color.rgb = RGBColor(0, 97, 0)
                            elif exam_summary['overall_mps'] >= 50:
                                run.font.color.rgb = RGBColor(127, 96, 0)
                            else:
                                run.font.color.rgb = RGBColor(156, 0, 6)

        doc.add_paragraph()
        doc.add_heading('MPS by Exam', level=2)
        exam_table = doc.add_table(rows=1, cols=6)
        exam_table.style = 'Table Grid'
        exam_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        headers = ['Exam', 'Learners', 'Total Correct', 'Total Possible', 'MPS', 'Performance Level']
        header_row = exam_table.rows[0]
        for idx, h in enumerate(headers):
            cell = header_row.cells[idx]
            cell.text = h
            set_cell_shading(cell, '1F4E79')
            for para in cell.paragraphs:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:
                    run.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)
                    run.font.size = Pt(9)

        for exam_summary in quarter_summary['exams']:
            row = exam_table.add_row()
            row_data = [
                exam_summary['title'],
                str(exam_summary['total_learners']),
                str(exam_summary['total_correct']),
                str(exam_summary['total_possible_answers']),
                f"{exam_summary['overall_mps']}%" if exam_summary['has_data'] else 'No data',
                get_performance_level(exam_summary['overall_mps']),
            ]
            for idx, value in enumerate(row_data):
                cell = row.cells[idx]
                cell.text = value
                for para in cell.paragraphs:
                    if idx > 0:
                        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs:
                        run.font.size = Pt(9)
                        if idx == 4 and exam_summary['has_data']:
                            run.bold = True
                            if exam_summary['overall_mps'] >= 75:
                                run.font.color.rgb = RGBColor(0, 97, 0)
                            elif exam_summary['overall_mps'] >= 50:
                                run.font.color.rgb = RGBColor(127, 96, 0)
                            else:
                                run.font.color.rgb = RGBColor(156, 0, 6)

    # Quarter matrix
    if quarter_matrix and quarter_matrix['students']:
        doc.add_page_break()
        doc.add_heading('Quarter Student-by-Item Response Matrix', level=2)

        matrix_para = doc.add_paragraph()
        matrix_para.add_run('Legend: ').bold = True
        matrix_para.add_run('1 = Correct, 0 = Wrong/Skipped')

        total_items = quarter_matrix['total_items']
        max_items_per_table = 25
        item_chunks = []
        for start in range(0, total_items, max_items_per_table):
            end = min(start + max_items_per_table, total_items)
            item_chunks.append((start, end))

        for chunk_idx, (start_item, end_item) in enumerate(item_chunks):
            chunk_size = end_item - start_item
            cols_in_chunk = chunk_size + 4

            if chunk_idx > 0:
                doc.add_paragraph()
                cont_para = doc.add_paragraph()
                cont_para.add_run(f'(Continued - Items {start_item + 1} to {end_item})').italic = True

            matrix_table = doc.add_table(rows=2, cols=cols_in_chunk)
            matrix_table.style = 'Table Grid'
            matrix_table.alignment = WD_TABLE_ALIGNMENT.CENTER

            # Base header cells
            matrix_table.cell(0, 0).text = '#'
            matrix_table.cell(0, 1).text = 'Student Name'
            set_cell_shading(matrix_table.cell(0, 0), '1F4E79')
            set_cell_shading(matrix_table.cell(0, 1), '1F4E79')
            for cell in (matrix_table.cell(0, 0), matrix_table.cell(0, 1)):
                for para in cell.paragraphs:
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs:
                        run.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)
                        run.font.size = Pt(7)
            matrix_table.cell(1, 0).text = ''
            matrix_table.cell(1, 1).text = ''

            # Item headers
            for i in range(start_item + 1, end_item + 1):
                cell = matrix_table.cell(1, i - start_item + 1)
                cell.text = str(i)
                set_cell_shading(cell, '1F4E79')
                for para in cell.paragraphs:
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs:
                        run.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)
                        run.font.size = Pt(7)

            # Totals columns
            matrix_table.cell(0, chunk_size + 2).text = 'Total'
            matrix_table.cell(0, chunk_size + 3).text = '%'
            for c in (chunk_size + 2, chunk_size + 3):
                set_cell_shading(matrix_table.cell(0, c), '1F4E79')
                for para in matrix_table.cell(0, c).paragraphs:
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs:
                        run.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)
                        run.font.size = Pt(7)
            matrix_table.cell(1, chunk_size + 2).text = ''
            matrix_table.cell(1, chunk_size + 3).text = ''

            # Student rows
            for s_idx, student in enumerate(quarter_matrix['students'], 1):
                row = matrix_table.add_row()
                row.cells[0].text = str(s_idx)
                row.cells[1].text = student['name']

                for item_idx in range(start_item, end_item):
                    col = item_idx - start_item + 2
                    mark = student['responses'][item_idx]
                    cell = row.cells[col]
                    cell.text = str(mark)
                    if mark == 1:
                        set_cell_shading(cell, 'E2EFDA')
                    else:
                        set_cell_shading(cell, 'FCE4EC')

                row.cells[chunk_size + 2].text = str(student['total_correct'])
                row.cells[chunk_size + 3].text = f"{student['percent']}%"

                for cell in row.cells:
                    for para in cell.paragraphs:
                        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        for run in para.runs:
                            run.font.size = Pt(7)
                for para in row.cells[1].paragraphs:
                    para.alignment = WD_ALIGN_PARAGRAPH.LEFT

            # Footer: totals per item
            footer_row = matrix_table.add_row()
            footer_row.cells[0].text = ''
            footer_row.cells[1].text = 'Total'
            for item_idx in range(start_item, end_item):
                col = item_idx - start_item + 2
                footer_row.cells[col].text = str(quarter_matrix['per_item_correct'][item_idx])
            footer_row.cells[chunk_size + 2].text = str(quarter_matrix['total_correct'])
            footer_row.cells[chunk_size + 3].text = f"{quarter_matrix['overall_mps']}%"

            for cell in footer_row.cells:
                set_cell_shading(cell, 'D6E4F0')
                for para in cell.paragraphs:
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs:
                        run.bold = True
                        run.font.size = Pt(7)

    doc.add_paragraph()
    prepared_by_para = doc.add_paragraph()
    prepared_by_para.paragraph_format.space_after = Pt(2)
    prepared_by_run = prepared_by_para.add_run('Prepared by:')
    prepared_by_run.bold = True
    prepared_by_run.font.size = Pt(10)

    signature_line = doc.add_paragraph()
    signature_line.paragraph_format.space_after = Pt(2)
    signature_run = signature_line.add_run('________________________________________')
    signature_run.font.size = Pt(10)

    name_para = doc.add_paragraph()
    name_para.paragraph_format.space_after = Pt(0)
    name_label = name_para.add_run('Name of Teacher: ')
    name_label.bold = True
    name_label.font.size = Pt(10)
    name_value = name_para.add_run(exam.created_by.user.get_full_name() or exam.created_by.user.username)
    name_value.bold = True
    name_value.font.size = Pt(10)

    # Write to response
    output = BytesIO()
    doc.save(output)
    output.seek(0)

    safe_title = exam.title.replace(' ', '_')[:30]
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename="MPS_Report_{safe_title}.docx"'
    return response
