"""
Configuración del proyecto — Terracogua Arcillas
Sistema de gestión de inventario y pedidos.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carga las variables definidas en el archivo .env (no versionado).
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-clave-solo-para-desarrollo')

DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

# Django exige declarar los orígenes HTTPS de confianza para aceptar formularios
# (POST). Si no se define en el .env, se derivan de ALLOWED_HOSTS.
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]
if not CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS = [
        f'https://{h}' for h in ALLOWED_HOSTS
        if h not in ('localhost', '127.0.0.1', '*') and not h.replace('.', '').isdigit()
    ]

# Detrás de un proxy o balanceador que termina el TLS (Apache, ALB), Django ve
# la petición como HTTP salvo que confíe en esta cabecera.
if os.getenv('USE_X_FORWARDED_PROTO', 'False').lower() in ('true', '1', 'yes'):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'inventario',
    'pedidos',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', 'db_inventario'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True


# --- Archivos estáticos y media --------------------------------------------
# Configuración híbrida según el estándar de despliegue Vadom (ver s3.md):
# en desarrollo (DEBUG=True) se sirven del disco local; en producción
# (DEBUG=False) viven en el bucket S3 compartido `vadomdata`, separados por
# cliente mediante el prefijo S3_CLIENT_PREFIX. Las credenciales AWS llegan
# solas por el IAM Role del EC2 — no van en el .env.

STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'

if DEBUG:
    # Desarrollo: archivos locales.
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'
    STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    }
else:
    # Producción: AWS S3 (credenciales vía IAM Role del EC2).
    from storages.backends.s3boto3 import S3Boto3Storage

    AWS_STORAGE_BUCKET_NAME = 'vadomdata'
    AWS_S3_REGION_NAME = 'us-east-1'
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_DEFAULT_ACL = None

    S3_PREFIX = os.getenv('S3_CLIENT_PREFIX', 'terracogua')

    class StaticStorage(S3Boto3Storage):
        location = f'{S3_PREFIX}/static'
        default_acl = None

    class MediaStorage(S3Boto3Storage):
        location = f'{S3_PREFIX}/media'
        default_acl = None

    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{S3_PREFIX}/static/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{S3_PREFIX}/media/'

    STORAGES = {
        'default': {'BACKEND': 'config.settings.MediaStorage'},
        'staticfiles': {'BACKEND': 'config.settings.StaticStorage'},
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'


# Datos del emisor que salen impresos en la remisión. Van en el .env porque
# son del cliente y no del código; las líneas vacías no se imprimen.
EMPRESA = {
    'nombre': os.getenv('EMPRESA_NOMBRE', 'Terracogua Arcillas'),
    'nit': os.getenv('EMPRESA_NIT', ''),
    'direccion': os.getenv('EMPRESA_DIRECCION', ''),
    'ciudad': os.getenv('EMPRESA_CIUDAD', ''),
    'telefono': os.getenv('EMPRESA_TELEFONO', ''),
    'email': os.getenv('EMPRESA_EMAIL', ''),
}
