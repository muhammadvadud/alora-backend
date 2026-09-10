import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
import environ
import structlog

# Loyiha asosiy papkasi
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environ sozlamalari
env = environ.Env(
    DEBUG=(bool, False)
)

# .env fayli mavjud bo'lsa o'qiladi (repoga tushmaydi, .env.example namuna)
_env_file = BASE_DIR / '.env'
if _env_file.exists():
    environ.Env.read_env(_env_file)

SECRET_KEY = env('SECRET_KEY', default='insecure-key-for-dev')
DEBUG = env('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Tashqi kutubxonalar
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'drf_spectacular',
    
    # Bizning ilovalar
    'channels',

    # Loyiha ilovalari
    'apps.common',
    'apps.accounts',
    'apps.catalog',
    'apps.pricing',
    'apps.knowledge',
    'apps.chat',
    'apps.orders',
    'apps.usage',
    'apps.prompts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
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
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Channels — WebSocket qatlami (ovozli suhbat, TZ 5.2)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {'hosts': [env('REDIS_URL', default='redis://localhost:6379/0')]},
    }
}

# Ma'lumotlar bazasi
DATABASES = {
    'default': dj_database_url.config(
        default=env('DATABASE_URL', default='postgres://postgres:postgres@localhost:5432/postgres'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Parol xavfsizligi
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Xalqaro sozlamalar
LANGUAGE_CODE = 'uz'
LANGUAGES = [('uz', "O'zbekcha"), ('ru', 'Русский')]
LOCALE_PATHS = [BASE_DIR / 'apps' / 'common' / 'locale']
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User modeli (keyinchalik accounts app da yaratiladi)
AUTH_USER_MODEL = 'accounts.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'apps.common.pagination.StandardCursorPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'apps.common.exceptions.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'login': '5/minute',
        'user': '600/hour',
        'chat': '30/minute',
        'calc': '120/minute',
        'upload': '20/minute',
        'bulk': '10/minute',
    },
}

# drf-spectacular OpenAPI sxemasi
SPECTACULAR_SETTINGS = {
    "TITLE": "Alora Backend API",
    "DESCRIPTION": "Alora — parda va dekorativ to'qimachilik ishlab chiqarish platformasi API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "ENUM_NAME_OVERRIDES": {
        "RoleEnum": "apps.common.choices.UserRole.choices",
        "CurtainPartRoleEnum": "apps.common.choices.CurtainPartRole.choices",
        "PriceUnitEnum": "apps.common.choices.PriceUnit.choices",
        "OrderStatusEnum": "apps.common.choices.OrderStatus.choices",
        "ConversationStatusEnum": "apps.chat.models.ConversationStatus.choices",
    },
    "TAGS": [
        {"name": "auth", "description": "Autentifikatsiya (login, logout, token)"},
        {"name": "accounts", "description": "Foydalanuvchilar va jamoa"},
        {"name": "catalog", "description": "Katalog: kategoriya, mahsulot, variant"},
        {"name": "pricing", "description": "Narx hisob-kitobi va chegirmalar"},
        {"name": "chat", "description": "Suhbat va SSE gateway"},
        {"name": "orders", "description": "Buyurtmalar"},
        {"name": "usage", "description": "Foydalanish statistikasi"},
        {"name": "knowledge", "description": "Bilim qoidalari"},
        {"name": "prompts", "description": "System prompt boshqaruvi"},
    ],
}

# Simple JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Celery va Redis
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json_formatter",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
