import os
import hmac
import traceback

from django.http import JsonResponse
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET


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
        call_command('backup_to_drive', '--keep', '7')
        return JsonResponse({'status': 'ok', 'message': 'Backup completed successfully'})
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
