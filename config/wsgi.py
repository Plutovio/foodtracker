"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

_django_app = get_wsgi_application()

def application(environ, start_response):
    is_vercel = os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV') or 'var/task' in str(os.getcwd())
    if is_vercel and not os.environ.get('DATABASE_URL') and not getattr(application, '_db_initialized', False):
        try:
            from django.core.management import call_command
            from django.contrib.auth.models import User
            call_command('migrate', interactive=False)
            if not User.objects.filter(username='resident').exists():
                User.objects.create_superuser('resident', '', 'password123')
            setattr(application, '_db_initialized', True)
        except Exception as e:
            print(f"Vercel auto-init notice: {e}")
    return _django_app(environ, start_response)

app = application
