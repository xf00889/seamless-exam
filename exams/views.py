from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from exams.models import Exam, Question, QuestionType
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
        
        if not form.is_valid():
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
        
        # Route to appropriate service based on generation method (Requirement 1.5)
        if generation_method == 'upload':
            # Handle file upload and automatic extraction
            return _handle_file_upload(request, exam, form)
        
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



def _handle_file_upload(request, exam, form):
    """
    Handle file upload and automatic question extraction.
    
    This function maintains the existing file upload functionality
    while integrating with the new generation method routing.
    
    Args:
        request: HTTP request
        exam: Created Exam instance
        form: Validated ExamForm
    
    Returns:
        HTTP response (redirect)
    """
    questionnaire_file = form.cleaned_data.get('questionnaire_file')
    answer_key_file = form.cleaned_data.get('answer_key_file')
    
    if questionnaire_file or answer_key_file:
        # Save files to exam
        if questionnaire_file:
            exam.questionnaire_file = questionnaire_file
        if answer_key_file:
            exam.answer_key_file = answer_key_file
        exam.save()
        
        # Attempt automatic extraction
        try:
            from services.exam_extraction_service import ExamExtractionService
            extraction_service = ExamExtractionService()
            
            extracted_questions = []
            answers = {}
            
            # Extract questions from questionnaire
            if questionnaire_file:
                text_result = extraction_service.extract_text_from_file(questionnaire_file)
                if text_result.is_success():
                    extracted_text = text_result.value
                    extracted_questions = extraction_service.parse_questions_from_text(extracted_text)
                    
                    if len(extracted_questions) == 0:
                        # Show debug info if no questions found
                        debug_text = extraction_service.debug_extracted_text(extracted_text, 20)
                        logger.warning(f"No questions extracted. First 20 lines:\n{debug_text}")
                        messages.warning(
                            request,
                            f'No questions found in questionnaire. Please check the format. '
                            f'Questions should be numbered (1., 2., 3., etc.)'
                        )
                    else:
                        messages.info(request, f'Extracted {len(extracted_questions)} questions from questionnaire')
                else:
                    messages.warning(request, f'Could not extract questions: {text_result.error.message}')
            
            # Extract answers from answer key
            if answer_key_file:
                text_result = extraction_service.extract_text_from_file(answer_key_file)
                if text_result.is_success():
                    answers = extraction_service.parse_answers_from_text(text_result.value)
                    messages.info(request, f'Extracted {len(answers)} answers from answer key')
                else:
                    messages.warning(request, f'Could not extract answers: {text_result.error.message}')
            
            # Merge and create questions
            if extracted_questions:
                merged_questions = extraction_service.merge_questions_and_answers(
                    extracted_questions,
                    answers
                )
                created_questions = extraction_service.create_questions_from_extracted_data(
                    exam,
                    merged_questions
                )
                
                if created_questions:
                    exam.auto_extracted = True
                    exam.save()
                    messages.success(
                        request,
                        f'Successfully created {len(created_questions)} questions automatically. '
                        f'Please review and edit as needed.'
                    )
            
        except Exception as e:
            logger.error(f"Error during automatic extraction: {str(e)}")
            messages.warning(
                request,
                'Automatic extraction encountered an error. You can add questions manually.'
            )
    
    messages.success(request, f'Exam "{exam.title}" created successfully')
    return redirect('exam_edit', exam_id=exam.id)


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
