from .common import *

ALLOWED_HOSTS = get_required_env_var('DJANGO_ALLOWED_HOSTS').split()

# django-secure settings
SECURE_FRAME_DENY = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True

# Make sure djangosecure is first middleware class loaded
MIDDLEWARE_CLASSES = (
    ('djangosecure.middleware.SecurityMiddleware',) + MIDDLEWARE_CLASSES
)

INSTALLED_APPS += ('djangosecure',)

# Celery
BROKER_USE_SSL = True