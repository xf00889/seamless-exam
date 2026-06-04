"""
Project-wide context processors.
"""
import os
from pathlib import Path

from django.conf import settings


_STATIC_VERSION_FILES = (
    'css/main.css',
    'js/main.js',
    'js/utils.js',
)


def _resolve_static_path(rel_path: str) -> Path:
    for static_dir in getattr(settings, 'STATICFILES_DIRS', []) or []:
        candidate = Path(static_dir) / rel_path
        if candidate.exists():
            return candidate
    static_root = getattr(settings, 'STATIC_ROOT', None)
    if static_root:
        candidate = Path(static_root) / rel_path
        if candidate.exists():
            return candidate
    return Path(rel_path)


def static_version(_request):
    """
    Expose a cache-busting version derived from the mtime of key static files.

    Use in templates as ``{{ static_version }}`` inside ``?v={{ static_version }}``
    query strings so browsers refetch changed assets without a hard refresh.
    """
    stamp = 0
    for rel_path in _STATIC_VERSION_FILES:
        try:
            stamp = max(stamp, int(_resolve_static_path(rel_path).stat().st_mtime))
        except OSError:
            continue
    if not stamp:
        stamp = int(os.environ.get('STATIC_VERSION', '0')) or 0
    return {
        'static_version': str(stamp),
        'app_version': getattr(settings, 'APP_VERSION', ''),
    }
