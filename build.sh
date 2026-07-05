#!/usr/bin/env bash
set -o errexit
set -x

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate --fake-initial
python manage.py createcachetable
python manage.py shell -c "from django.core.cache import caches; [cache.clear() for cache in caches.all()]; print('Cleared Django caches')"
