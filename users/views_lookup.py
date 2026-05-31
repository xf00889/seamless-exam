from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from users.decorators import teacher_required
from users.models import GradeLevel, Strand, Section, Subject, Quarter
from services.view_helpers import build_breadcrumbs
from django.urls import reverse
import json


@method_decorator(teacher_required, name='dispatch')
class LookupManagementView(View):
    """Page to manage all lookup tables: Grade Levels, Strands, Sections, Subjects."""

    def get(self, request):
        breadcrumbs = build_breadcrumbs(
            ('Dashboard', reverse('teacher_dashboard')),
            'Manage Options'
        )
        context = {
            'grade_levels': GradeLevel.objects.all(),
            'strands': Strand.objects.all(),
            'sections': Section.objects.all(),
            'subjects': Subject.objects.all(),
            'quarters': Quarter.objects.all(),
            'page_breadcrumbs': breadcrumbs,
        }
        return render(request, 'users/lookup_management.html', context)


@teacher_required
@require_http_methods(["POST"])
def create_grade_level_view(request):
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
    except (json.JSONDecodeError, AttributeError):
        name = request.POST.get('name', '').strip()

    if not name:
        return JsonResponse({'error': 'Name is required'}, status=400)

    obj, created = GradeLevel.objects.get_or_create(name=name)
    if not created:
        return JsonResponse({'error': 'This grade level already exists'}, status=400)

    return JsonResponse({'success': True, 'id': obj.id, 'name': obj.name})


@teacher_required
@require_http_methods(["POST"])
def create_strand_view(request):
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
    except (json.JSONDecodeError, AttributeError):
        name = request.POST.get('name', '').strip()

    if not name:
        return JsonResponse({'error': 'Name is required'}, status=400)

    obj, created = Strand.objects.get_or_create(name=name)
    if not created:
        return JsonResponse({'error': 'This strand already exists'}, status=400)

    return JsonResponse({'success': True, 'id': obj.id, 'name': obj.name})


@teacher_required
@require_http_methods(["POST"])
def create_section_view(request):
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
    except (json.JSONDecodeError, AttributeError):
        name = request.POST.get('name', '').strip()

    if not name:
        return JsonResponse({'error': 'Name is required'}, status=400)

    obj, created = Section.objects.get_or_create(name=name)
    if not created:
        return JsonResponse({'error': 'This section already exists'}, status=400)

    return JsonResponse({'success': True, 'id': obj.id, 'name': obj.name})


@teacher_required
@require_http_methods(["POST"])
def create_subject_view(request):
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
    except (json.JSONDecodeError, AttributeError):
        name = request.POST.get('name', '').strip()

    if not name:
        return JsonResponse({'error': 'Name is required'}, status=400)

    obj, created = Subject.objects.get_or_create(name=name)
    if not created:
        return JsonResponse({'error': 'This subject already exists'}, status=400)

    return JsonResponse({'success': True, 'id': obj.id, 'name': obj.name})


@teacher_required
@require_http_methods(["POST"])
def create_quarter_view(request):
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
    except (json.JSONDecodeError, AttributeError):
        name = request.POST.get('name', '').strip()

    if not name:
        return JsonResponse({'error': 'Name is required'}, status=400)

    obj, created = Quarter.objects.get_or_create(name=name)
    if not created:
        return JsonResponse({'error': 'This quarter already exists'}, status=400)

    return JsonResponse({'success': True, 'id': obj.id, 'name': obj.name})


@teacher_required
@require_http_methods(["POST"])
def update_quarter_view(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    quarter_id = data.get('id')
    name = data.get('name', '').strip()

    if not quarter_id or not name:
        return JsonResponse({'error': 'Quarter ID and name are required'}, status=400)

    try:
        quarter = Quarter.objects.get(id=quarter_id)
    except Quarter.DoesNotExist:
        return JsonResponse({'error': 'Quarter not found'}, status=404)

    if Quarter.objects.exclude(id=quarter.id).filter(name__iexact=name).exists():
        return JsonResponse({'error': 'This quarter already exists'}, status=400)

    quarter.name = name
    quarter.save()

    return JsonResponse({'success': True, 'id': quarter.id, 'name': quarter.name})


@teacher_required
@require_http_methods(["POST"])
def delete_lookup_view(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    lookup_type = data.get('type', '')
    lookup_id = data.get('id')

    if not lookup_type or not lookup_id:
        return JsonResponse({'error': 'Type and ID are required'}, status=400)

    model_map = {
        'grade_level': GradeLevel,
        'strand': Strand,
        'section': Section,
        'subject': Subject,
        'quarter': Quarter,
    }

    model = model_map.get(lookup_type)
    if not model:
        return JsonResponse({'error': 'Invalid type'}, status=400)

    try:
        obj = model.objects.get(id=lookup_id)
        obj.delete()
        return JsonResponse({'success': True})
    except model.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)
