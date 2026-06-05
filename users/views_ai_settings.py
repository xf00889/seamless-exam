from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from users.models import SystemSettings
from services.ai_generation_service import FREE_MODELS


def superadmin_required(user):
    return user.is_authenticated and user.is_superuser


@login_required
@user_passes_test(superadmin_required)
def ai_settings_view(request):
    settings_obj = SystemSettings.load()

    if request.method == 'POST':
        settings_obj.ai_api_key = request.POST.get('ai_api_key', '').strip()
        settings_obj.ai_base_url = request.POST.get('ai_base_url', '').strip() or 'https://openrouter.ai/api/v1'
        settings_obj.ai_model = request.POST.get('ai_model', '').strip() or 'deepseek/deepseek-r1-0528:free'
        settings_obj.maintenance_mode = request.POST.get('maintenance_mode') == 'on'
        settings_obj.maintenance_message = request.POST.get('maintenance_message', '').strip()
        settings_obj.save()
        messages.success(request, 'Settings updated successfully.')
        return redirect('superadmin_ai_settings')

    context = {
        'settings': settings_obj,
        'free_models': FREE_MODELS,
    }
    return render(request, 'superadmin/ai_settings.html', context)
