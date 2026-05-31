from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
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
    
    # Build breadcrumbs
    breadcrumbs = build_breadcrumbs(
        ('Dashboard', reverse('teacher_dashboard')),
        'My Exams'
    )
    
    context = {
        'exams': page_obj,
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
    import json
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
        'questions_json': json.dumps(questions_data),
        'question_types': QuestionType.choices,
        'assigned_classes': assigned_classes,
        'classes': classes,
        'page_breadcrumbs': breadcrumbs
    }
    return render(request, 'exams/exam_edit.html', context)


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

    try:
        questions = generate_exam_questions(
            topic=subject,
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
def mps_report_view(request, exam_id):
    """
    Display DepEd-style MPS (Mean Percentage Score) report for an exam.
    Shows overall MPS and per-class/section breakdown.
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
        'MPS Report'
    )

    mps_gauge_offset = 377
    if summary_data.get('has_data') and summary_data.get('mps_data'):
        mps_gauge_offset = round(377 - (377 * summary_data['mps_data']['overall_mps'] / 100))

    context = {
        'exam': exam,
        'summary': summary_data,
        'mps_gauge_offset': mps_gauge_offset,
        'page_breadcrumbs': breadcrumbs,
    }

    return render(request, 'exams/mps_report.html', context)


@teacher_required
@require_http_methods(["GET"])
def mps_export_excel_view(request, exam_id):
    """
    Export MPS report to Excel with DepEd-style formatting.
    Includes overall MPS, per-class breakdown, and item-level data.
    """
    import os
    from io import BytesIO
    from django.conf import settings
    from django.http import HttpResponse
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.drawing.image import Image as XlImage
    from services.item_analysis_service import ItemAnalysisService

    exam = get_object_or_404(Exam, pk=exam_id)

    teacher = auth_service.get_current_teacher(request)
    if exam.created_by.pk != teacher.pk:
        messages.error(request, 'Permission denied')
        return redirect('exam_list')

    service = ItemAnalysisService()
    summary_data = service.get_item_summary(exam_id)

    if not summary_data or not summary_data.get('has_data'):
        messages.warning(request, 'No graded attempts to export')
        return redirect('mps_report', exam_id=exam_id)

    mps_data = summary_data['mps_data']
    items = summary_data['items']

    wb = Workbook()
    wb.remove(wb.active)

    brand_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'brand.png')
    has_brand = os.path.isfile(brand_path)

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

    # --- Sheet 1: MPS Summary ---
    ws = wb.create_sheet(title='MPS Summary')
    row = 1

    if has_brand:
        img = XlImage(brand_path)
        img.width = 120
        img.height = 60
        ws.add_image(img, 'A1')
        row = 5

    ws.cell(row=row, column=1, value='MEAN PERCENTAGE SCORE (MPS) REPORT')
    ws.cell(row=row, column=1).font = title_font
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
    row += 2

    info_labels = [
        ('Exam:', exam.title),
        ('Subject:', exam.subject or 'Not specified'),
        ('Teacher:', exam.created_by.user.get_full_name()),
        ('No. of Learners:', str(mps_data['total_learners'])),
        ('No. of Items:', str(mps_data['total_items'])),
    ]
    for label, value in info_labels:
        ws.cell(row=row, column=1, value=label)
        ws.cell(row=row, column=1).font = Font(bold=True)
        ws.cell(row=row, column=2, value=value)
        row += 1

    row += 1
    ws.cell(row=row, column=1, value='OVERALL MPS')
    ws.cell(row=row, column=1).font = header_font
    row += 1

    ws.cell(row=row, column=1, value='Total Correct Answers:')
    ws.cell(row=row, column=2, value=mps_data['total_correct'])
    row += 1
    ws.cell(row=row, column=1, value='Total Possible Answers:')
    ws.cell(row=row, column=2, value=mps_data['total_possible_answers'])
    row += 1
    ws.cell(row=row, column=1, value='MPS:')
    ws.cell(row=row, column=1).font = Font(bold=True)
    mps_cell = ws.cell(row=row, column=2, value=f"{mps_data['overall_mps']}%")
    mps_cell.font = get_mps_font(mps_data['overall_mps'])
    row += 1
    ws.cell(row=row, column=1, value='Performance Level:')
    ws.cell(row=row, column=2, value=get_performance_level(mps_data['overall_mps']))
    row += 2

    # Per-class breakdown
    if mps_data['per_class']:
        ws.cell(row=row, column=1, value='MPS BY CLASS / SECTION')
        ws.cell(row=row, column=1).font = header_font
        row += 1

        class_headers = ['Class / Section', 'No. of Learners', 'Total Correct', 'Total Possible', 'MPS', 'Performance Level']
        for col_idx, h in enumerate(class_headers, 1):
            cell = ws.cell(row=row, column=col_idx, value=h)
            cell.font = header_text
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
        row += 1

        for cls in mps_data['per_class']:
            row_data = [
                cls['class_name'],
                cls['learners'],
                cls['total_correct'],
                cls['total_possible'],
                f"{cls['mps']}%",
                get_performance_level(cls['mps']),
            ]
            for col_idx, value in enumerate(row_data, 1):
                cell = ws.cell(row=row, column=col_idx, value=value)
                cell.border = thin_border
                if col_idx in (2, 3, 4):
                    cell.alignment = Alignment(horizontal='center')
                if col_idx == 5:
                    cell.font = get_mps_font(cls['mps'])
                    cell.alignment = Alignment(horizontal='center')
                if col_idx == 6:
                    cell.alignment = Alignment(horizontal='center')
            row += 1

        # Overall row
        overall_row_data = [
            'OVERALL',
            mps_data['total_learners'],
            mps_data['total_correct'],
            mps_data['total_possible_answers'],
            f"{mps_data['overall_mps']}%",
            get_performance_level(mps_data['overall_mps']),
        ]
        for col_idx, value in enumerate(overall_row_data, 1):
            cell = ws.cell(row=row, column=col_idx, value=value)
            cell.border = thin_border
            cell.font = Font(bold=True)
            if col_idx in (2, 3, 4, 5, 6):
                cell.alignment = Alignment(horizontal='center')
            if col_idx == 5:
                cell.font = Font(bold=True, color='1F4E79')
        row += 1

    col_widths = [25, 15, 15, 15, 12, 18]
    for i, width in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = width

    # --- Sheet 2: Item Analysis ---
    ws2 = wb.create_sheet(title='Item Analysis')
    row = 1

    if has_brand:
        img2 = XlImage(brand_path)
        img2.width = 120
        img2.height = 60
        ws2.add_image(img2, 'A1')
        row = 5

    ws2.cell(row=row, column=1, value='ITEM ANALYSIS - CONTRIBUTION TO MPS')
    ws2.cell(row=row, column=1).font = title_font
    ws2.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
    row += 1

    ws2.cell(row=row, column=1, value=f'Exam: {exam.title}')
    ws2.cell(row=row, column=1).font = subheader_font
    row += 1
    ws2.cell(row=row, column=1, value=f'No. of Learners: {mps_data["total_learners"]}')
    row += 2

    item_headers = ['Item No.', 'Question Type', 'No. Correct', 'No. Wrong', 'Skipped', '% Correct', 'Difficulty Level']
    for col_idx, h in enumerate(item_headers, 1):
        cell = ws2.cell(row=row, column=col_idx, value=h)
        cell.font = header_text
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
    row += 1

    for item in items:
        item_row_data = [
            item['item_no'],
            item['question_type'],
            item['num_correct'],
            item['num_wrong'],
            item['num_skipped'],
            f"{item['percent_correct']}%",
            item['difficulty_level'],
        ]
        for col_idx, value in enumerate(item_row_data, 1):
            cell = ws2.cell(row=row, column=col_idx, value=value)
            cell.border = thin_border
            if col_idx in (1, 3, 4, 5, 6):
                cell.alignment = Alignment(horizontal='center')
            if col_idx == 6:
                pct = item['percent_correct']
                if pct >= 81:
                    cell.font = green_font
                elif pct <= 40:
                    cell.font = red_font
        row += 1

    # Totals row
    row += 1
    ws2.cell(row=row, column=1, value='TOTAL')
    ws2.cell(row=row, column=1).font = Font(bold=True)
    ws2.cell(row=row, column=3, value=mps_data['total_correct'])
    ws2.cell(row=row, column=3).font = Font(bold=True)
    ws2.cell(row=row, column=3).alignment = Alignment(horizontal='center')
    row += 1
    ws2.cell(row=row, column=1, value=f'MPS = ({mps_data["total_correct"]} / {mps_data["total_possible_answers"]}) x 100 = {mps_data["overall_mps"]}%')
    ws2.cell(row=row, column=1).font = Font(bold=True, size=12)
    ws2.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)

    item_col_widths = [10, 22, 12, 12, 10, 12, 18]
    for i, width in enumerate(item_col_widths, 1):
        ws2.column_dimensions[get_column_letter(i)].width = width

    # --- Sheet 3: Student-by-Item Matrix ---
    student_matrix = summary_data.get('student_matrix')
    if student_matrix and student_matrix['students']:
        ws3 = wb.create_sheet(title='Student Matrix')
        row = 1

        if has_brand:
            img3 = XlImage(brand_path)
            img3.width = 120
            img3.height = 60
            ws3.add_image(img3, 'A1')
            row = 5

        ws3.cell(row=row, column=1, value='STUDENT-BY-ITEM RESPONSE MATRIX')
        ws3.cell(row=row, column=1).font = title_font
        ws3.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
        row += 1
        ws3.cell(row=row, column=1, value=f'Exam: {exam.title}')
        ws3.cell(row=row, column=1).font = subheader_font
        row += 1
        ws3.cell(row=row, column=1, value=f'No. of Learners: {student_matrix["total_learners"]} | No. of Items: {student_matrix["total_items"]}')
        row += 2

        total_items = student_matrix['total_items']

        # Header row: #, Name, Item 1, Item 2, ..., Total, %
        matrix_headers = ['#', 'Student Name']
        for i in range(1, total_items + 1):
            matrix_headers.append(str(i))
        matrix_headers.extend(['Total', '%'])

        for col_idx, h in enumerate(matrix_headers, 1):
            cell = ws3.cell(row=row, column=col_idx, value=h)
            cell.font = header_text
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
        row += 1

        green_fill = PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid')
        red_fill = PatternFill(start_color='FCE4EC', end_color='FCE4EC', fill_type='solid')

        for idx, student in enumerate(student_matrix['students'], 1):
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

            total_col = total_items + 3
            pct_col = total_items + 4

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

        # Footer: Total correct per item
        footer_fill = PatternFill(start_color='D6E4F0', end_color='D6E4F0', fill_type='solid')
        ws3.cell(row=row, column=1, value='')
        ws3.cell(row=row, column=2, value='Total Correct')
        ws3.cell(row=row, column=2).font = Font(bold=True)
        ws3.cell(row=row, column=2).border = thin_border
        ws3.cell(row=row, column=2).fill = footer_fill

        for item_idx, count in enumerate(student_matrix['per_item_correct']):
            col = item_idx + 3
            cell = ws3.cell(row=row, column=col, value=count)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
            cell.fill = footer_fill

        cell = ws3.cell(row=row, column=total_items + 3, value=mps_data['total_correct'])
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
        cell.fill = footer_fill
        row += 1

        # Footer: % correct per item
        ws3.cell(row=row, column=2, value='% Correct')
        ws3.cell(row=row, column=2).font = Font(bold=True)
        ws3.cell(row=row, column=2).border = thin_border
        ws3.cell(row=row, column=2).fill = footer_fill

        for item_idx, pct in enumerate(student_matrix['per_item_percent']):
            col = item_idx + 3
            cell = ws3.cell(row=row, column=col, value=f"{pct}%")
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
            cell.fill = footer_fill
            if pct >= 75:
                cell.font = green_font
            elif pct < 50:
                cell.font = red_font

        cell = ws3.cell(row=row, column=total_items + 4, value=f"{mps_data['overall_mps']}%")
        cell.font = Font(bold=True, color='1F4E79')
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
        cell.fill = footer_fill
        row += 2

        ws3.cell(row=row, column=1, value=f'MPS = ({mps_data["total_correct"]} / {mps_data["total_possible_answers"]}) x 100 = {mps_data["overall_mps"]}%')
        ws3.cell(row=row, column=1).font = Font(bold=True, size=12)

        # Column widths
        ws3.column_dimensions['A'].width = 5
        ws3.column_dimensions['B'].width = 28
        for i in range(3, total_items + 5):
            ws3.column_dimensions[get_column_letter(i)].width = 5
        ws3.column_dimensions[get_column_letter(total_items + 3)].width = 8
        ws3.column_dimensions[get_column_letter(total_items + 4)].width = 8

    # Write to response
    output = BytesIO()
    wb.save(output)
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
    import os
    from io import BytesIO
    from django.conf import settings
    from django.http import HttpResponse
    from docx import Document
    from docx.shared import Inches, Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn
    from services.item_analysis_service import ItemAnalysisService

    exam = get_object_or_404(Exam, pk=exam_id)

    teacher = auth_service.get_current_teacher(request)
    if exam.created_by.pk != teacher.pk:
        messages.error(request, 'Permission denied')
        return redirect('exam_list')

    service = ItemAnalysisService()
    summary_data = service.get_item_summary(exam_id)

    if not summary_data or not summary_data.get('has_data'):
        messages.warning(request, 'No graded attempts to export')
        return redirect('mps_report', exam_id=exam_id)

    mps_data = summary_data['mps_data']
    items = summary_data['items']

    doc = Document()

    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    sections = doc.sections
    for section in sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

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

    # Brand logo
    brand_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'brand.png')
    if os.path.isfile(brand_path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(brand_path, width=Inches(1.2))

    # Title
    title = doc.add_heading('MEAN PERCENTAGE SCORE (MPS) REPORT', level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    # Exam info table
    info_table = doc.add_table(rows=3, cols=4)
    info_table.style = 'Table Grid'
    info_data = [
        ('School:', '________________________', 'Teacher:', exam.created_by.user.get_full_name()),
        ('Subject:', exam.subject or 'Not specified', 'No. of Learners:', str(mps_data['total_learners'])),
        ('Exam:', exam.title, 'No. of Items:', str(mps_data['total_items'])),
    ]
    for row_idx, (l1, v1, l2, v2) in enumerate(info_data):
        row = info_table.rows[row_idx]
        row.cells[0].text = l1
        row.cells[0].paragraphs[0].runs[0].bold = True if row.cells[0].paragraphs[0].runs else None
        row.cells[1].text = v1
        row.cells[2].text = l2
        row.cells[2].paragraphs[0].runs[0].bold = True if row.cells[2].paragraphs[0].runs else None
        row.cells[3].text = v2
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(2)
                paragraph.paragraph_format.space_before = Pt(2)
                for run in paragraph.runs:
                    run.font.size = Pt(10)

    # Make label cells bold
    for row_idx in range(3):
        for col_idx in [0, 2]:
            for para in info_table.rows[row_idx].cells[col_idx].paragraphs:
                for run in para.runs:
                    run.bold = True

    doc.add_paragraph()

    # Overall MPS section
    doc.add_heading('Overall MPS', level=2)

    mps_para = doc.add_paragraph()
    mps_para.add_run('Formula: ').bold = True
    mps_para.add_run('MPS = (Total Correct Answers / Total Possible Answers) x 100')

    comp_para = doc.add_paragraph()
    comp_para.add_run('Computation: ').bold = True
    comp_para.add_run(f'MPS = ({mps_data["total_correct"]} / {mps_data["total_possible_answers"]}) x 100 = ')
    mps_run = comp_para.add_run(f'{mps_data["overall_mps"]}%')
    mps_run.bold = True
    mps_run.font.size = Pt(14)
    if mps_data['overall_mps'] >= 75:
        mps_run.font.color.rgb = RGBColor(0, 97, 0)
    elif mps_data['overall_mps'] >= 50:
        mps_run.font.color.rgb = RGBColor(127, 96, 0)
    else:
        mps_run.font.color.rgb = RGBColor(156, 0, 6)

    level_para = doc.add_paragraph()
    level_para.add_run('Performance Level: ').bold = True
    level_para.add_run(get_performance_level(mps_data['overall_mps']))

    details_table = doc.add_table(rows=3, cols=2)
    details_table.style = 'Table Grid'
    detail_rows = [
        ('Total Correct Answers', str(mps_data['total_correct'])),
        ('Total Possible Answers', str(mps_data['total_possible_answers'])),
        ('Breakdown', f'{mps_data["total_learners"]} learners x {mps_data["total_items"]} items'),
    ]
    for row_idx, (label, value) in enumerate(detail_rows):
        row = details_table.rows[row_idx]
        row.cells[0].text = label
        row.cells[1].text = value
        for para in row.cells[0].paragraphs:
            for run in para.runs:
                run.bold = True
                run.font.size = Pt(10)
        for para in row.cells[1].paragraphs:
            for run in para.runs:
                run.font.size = Pt(10)

    doc.add_paragraph()

    # Per-class MPS breakdown
    if mps_data['per_class']:
        doc.add_heading('MPS by Class / Section', level=2)

        class_table = doc.add_table(rows=1, cols=6)
        class_table.style = 'Table Grid'
        class_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        headers = ['Class / Section', 'Learners', 'Total Correct', 'Total Possible', 'MPS', 'Performance Level']
        header_row = class_table.rows[0]
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

        for cls in mps_data['per_class']:
            row = class_table.add_row()
            row_data = [
                cls['class_name'],
                str(cls['learners']),
                str(cls['total_correct']),
                str(cls['total_possible']),
                f"{cls['mps']}%",
                get_performance_level(cls['mps']),
            ]
            for idx, value in enumerate(row_data):
                cell = row.cells[idx]
                cell.text = value
                for para in cell.paragraphs:
                    if idx > 0:
                        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs:
                        run.font.size = Pt(10)
                        if idx == 4:
                            run.bold = True
                            if cls['mps'] >= 75:
                                run.font.color.rgb = RGBColor(0, 97, 0)
                            elif cls['mps'] >= 50:
                                run.font.color.rgb = RGBColor(127, 96, 0)
                            else:
                                run.font.color.rgb = RGBColor(156, 0, 6)

        # Overall row
        overall_row = class_table.add_row()
        overall_data = [
            'OVERALL',
            str(mps_data['total_learners']),
            str(mps_data['total_correct']),
            str(mps_data['total_possible_answers']),
            f"{mps_data['overall_mps']}%",
            get_performance_level(mps_data['overall_mps']),
        ]
        for idx, value in enumerate(overall_data):
            cell = overall_row.cells[idx]
            cell.text = value
            set_cell_shading(cell, 'D6E4F0')
            for para in cell.paragraphs:
                if idx > 0:
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:
                    run.bold = True
                    run.font.size = Pt(10)

    doc.add_page_break()

    # Item Analysis section
    doc.add_heading('Item Analysis', level=2)

    item_table = doc.add_table(rows=1, cols=7)
    item_table.style = 'Table Grid'
    item_table.alignment = WD_TABLE_ALIGNMENT.CENTER

    item_headers = ['Item', 'Type', 'Correct', 'Wrong', 'Skipped', '% Correct', 'Difficulty']
    header_row = item_table.rows[0]
    for idx, h in enumerate(item_headers):
        cell = header_row.cells[idx]
        cell.text = h
        set_cell_shading(cell, '1F4E79')
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs:
                run.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.font.size = Pt(9)

    for item in items:
        row = item_table.add_row()
        row_data = [
            str(item['item_no']),
            item['question_type'],
            str(item['num_correct']),
            str(item['num_wrong']),
            str(item['num_skipped']),
            f"{item['percent_correct']}%",
            item['difficulty_level'],
        ]
        for idx, value in enumerate(row_data):
            cell = row.cells[idx]
            cell.text = value
            for para in cell.paragraphs:
                if idx != 1 and idx != 6:
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:
                    run.font.size = Pt(9)
                    if idx == 5:
                        pct = item['percent_correct']
                        if pct >= 81:
                            run.font.color.rgb = RGBColor(0, 97, 0)
                        elif pct <= 40:
                            run.font.color.rgb = RGBColor(156, 0, 6)

    doc.add_paragraph()
    formula_para = doc.add_paragraph()
    formula_para.add_run(
        f'MPS = ({mps_data["total_correct"]} / {mps_data["total_possible_answers"]}) x 100 = {mps_data["overall_mps"]}%'
    ).bold = True

    # MPS Interpretation Guide
    doc.add_paragraph()
    doc.add_heading('MPS Interpretation Guide', level=2)

    guide_table = doc.add_table(rows=1, cols=3)
    guide_table.style = 'Table Grid'
    guide_headers = ['MPS Range', 'Performance Level', 'Interpretation']
    header_row = guide_table.rows[0]
    for idx, h in enumerate(guide_headers):
        cell = header_row.cells[idx]
        cell.text = h
        set_cell_shading(cell, '1F4E79')
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs:
                run.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.font.size = Pt(10)

    guide_data = [
        ('75% - 100%', 'Mastered', 'Proceed to enrichment activities.'),
        ('50% - 74%', 'Nearing Mastery', 'Provide reinforcement and additional practice.'),
        ('Below 50%', 'Low Mastery', 'Intensive remediation and reteaching needed.'),
    ]
    for mps_range, level, interp in guide_data:
        row = guide_table.add_row()
        row.cells[0].text = mps_range
        row.cells[1].text = level
        row.cells[2].text = interp
        for cell in row.cells:
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.size = Pt(10)

    # Student-by-Item Matrix
    student_matrix = summary_data.get('student_matrix')
    if student_matrix and student_matrix['students']:
        doc.add_page_break()
        doc.add_heading('Student-by-Item Response Matrix', level=2)

        matrix_para = doc.add_paragraph()
        matrix_para.add_run('Legend: ').bold = True
        matrix_para.add_run('1 = Correct, 0 = Wrong/Skipped')

        total_items = student_matrix['total_items']
        num_cols = total_items + 4  # #, Name, items..., Total, %

        # For Word, limit columns to avoid overflow (landscape can fit ~25 items)
        # If more than 25 items, split into multiple tables
        max_items_per_table = 25
        item_chunks = []
        for start in range(0, total_items, max_items_per_table):
            end = min(start + max_items_per_table, total_items)
            item_chunks.append((start, end))

        for chunk_idx, (start_item, end_item) in enumerate(item_chunks):
            chunk_size = end_item - start_item
            cols_in_chunk = chunk_size + 4  # #, Name, items..., Total, %

            if chunk_idx > 0:
                doc.add_paragraph()
                cont_para = doc.add_paragraph()
                cont_para.add_run(f'(Continued - Items {start_item + 1} to {end_item})').italic = True

            matrix_table = doc.add_table(rows=1, cols=cols_in_chunk)
            matrix_table.style = 'Table Grid'

            # Header
            m_headers = ['#', 'Student Name']
            for i in range(start_item + 1, end_item + 1):
                m_headers.append(str(i))
            m_headers.extend(['Total', '%'])

            header_row = matrix_table.rows[0]
            for idx, h in enumerate(m_headers):
                cell = header_row.cells[idx]
                cell.text = h
                set_cell_shading(cell, '1F4E79')
                for para in cell.paragraphs:
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs:
                        run.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)
                        run.font.size = Pt(7)

            # Student rows
            for s_idx, student in enumerate(student_matrix['students'], 1):
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

                # Total and %
                row.cells[chunk_size + 2].text = str(student['total_correct'])
                row.cells[chunk_size + 3].text = f"{student['percent']}%"

                for cell in row.cells:
                    for para in cell.paragraphs:
                        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        for run in para.runs:
                            run.font.size = Pt(7)
                # Left-align name
                for para in row.cells[1].paragraphs:
                    para.alignment = WD_ALIGN_PARAGRAPH.LEFT

            # Footer: totals per item
            footer_row = matrix_table.add_row()
            footer_row.cells[0].text = ''
            footer_row.cells[1].text = 'Total'
            for item_idx in range(start_item, end_item):
                col = item_idx - start_item + 2
                footer_row.cells[col].text = str(student_matrix['per_item_correct'][item_idx])
            footer_row.cells[chunk_size + 2].text = str(mps_data['total_correct'])
            footer_row.cells[chunk_size + 3].text = f"{mps_data['overall_mps']}%"

            for cell in footer_row.cells:
                set_cell_shading(cell, 'D6E4F0')
                for para in cell.paragraphs:
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs:
                        run.bold = True
                        run.font.size = Pt(7)

        doc.add_paragraph()
        mps_final = doc.add_paragraph()
        mps_final.add_run(
            f'MPS = ({mps_data["total_correct"]} / {mps_data["total_possible_answers"]}) x 100 = {mps_data["overall_mps"]}%'
        ).bold = True

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
