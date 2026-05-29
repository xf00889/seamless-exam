import os
import hmac
import traceback
import io

from django.http import JsonResponse, HttpResponse
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.conf import settings


@require_GET
def service_worker_view(request):
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    with open(sw_path, 'r') as f:
        return HttpResponse(f.read(), content_type='application/javascript')



@csrf_exempt
@require_GET
def cron_backup(request):
    token = os.environ.get('CRON_SECRET_TOKEN', '')
    provided_token = request.headers.get('X-Cron-Token', '') or request.GET.get('token', '')

    if not token:
        return JsonResponse({'error': 'CRON_SECRET_TOKEN not configured'}, status=500)

    if not hmac.compare_digest(token, provided_token):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        stdout = io.StringIO()
        stderr = io.StringIO()
        call_command('backup_to_drive', '--keep', '7', stdout=stdout, stderr=stderr)
        return JsonResponse({
            'status': 'ok',
            'message': 'Backup completed successfully',
            'output': stdout.getvalue(),
            'errors': stderr.getvalue(),
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
