import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
import environ
import structlog

# Loyiha asosiy papkasi
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environ sozlamalari
env = environ.Env(DEBUG=(bool, False))

# .env fayli mavjud bo'lsa o'qiladi (repoga tushmaydi, .env.example namuna)
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    environ.Env.read_env(_env_file)

SECRET_KEY = env("SECRET_KEY", default="insecure-key-for-dev")
DEBUG = env("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Tashqi kutubxonalar
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    # Bizning ilovalar
    "channels",
    # Loyiha ilovalari
    "apps.common",
    "apps.accounts",
    "apps.catalog",
    "apps.pricing",
    "apps.knowledge",
    "apps.chat",
    "apps.orders",
    "apps.usage",
    "apps.prompts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "config" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Channels — WebSocket qatlami (ovozli suhbat, TZ 5.2)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [env("REDIS_URL", default="redis://localhost:6379/0")]},
    }
}

# Ma'lumotlar bazasi
DATABASES = {
    "default": dj_database_url.config(
        default=env("DATABASE_URL", default="postgres://postgres:postgres@localhost:5432/postgres"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Parol xavfsizligi
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Xalqaro sozlamalar
LANGUAGE_CODE = "uz"
LANGUAGES = [("uz", "O'zbekcha"), ("ru", "Русский")]
LOCALE_PATHS = [BASE_DIR / "apps" / "common" / "locale"]
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
MEDIA_URL = "media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom User modeli (keyinchalik accounts app da yaratiladi)
AUTH_USER_MODEL = "accounts.User"

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardCursorPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "apps.common.exceptions.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "login": "5/minute",
        "user": "600/hour",
        "chat": "30/minute",
        "calc": "120/minute",
        "upload": "20/minute",
        "bulk": "10/minute",
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

# Django Unfold — admin interfeysi uchun zamonaviy tema (rules.md §17.5).
UNFOLD = {
    "SITE_TITLE": "Alora",
    "SITE_HEADER": "Alora",
    "SITE_SYMBOL": "curtains",
    # Brend palitrasi: asosiy petrol-yashil #0E5751, fon zig'ir #F2F3F0, brass #8A6620.
    "COLORS": {
        "primary": {
            "50": "#F0F7F6",
            "100": "#DCEBE9",
            "200": "#B8D6D2",
            "300": "#8DBAB4",
            "400": "#5F9E96",
            "500": "#3B8278",
            "600": "#1E6A61",
            "700": "#0E5751",
            "800": "#0A423D",
            "900": "#072F2B",
            "950": "#041C1A",
        },
        "base": {
            "50": "#FFFFFF",
            "100": "#FCFDFC",
            "200": "#F9FAF8",
            "300": "#F5F6F3",
            "400": "#F2F3F0",
            "500": "#E4E6E2",
            "600": "#CBD0CA",
            "700": "#9FA89F",
            "800": "#6E7A72",
            "900": "#45524A",
            "950": "#212B25",
        },
        "accent": {
            "50": "#F9F6EE",
            "100": "#F1E9D8",
            "200": "#E2D2AC",
            "300": "#D1B97E",
            "400": "#BE9D52",
            "500": "#A67F33",
            "600": "#8A6620",
            "700": "#6E501A",
            "800": "#523C14",
            "900": "#372A0E",
            "950": "#1D1608",
        },
    },
    "DASHBOARD_CALLBACK": "apps.common.admin_dashboard.dashboard_callback",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Foydalanuvchilar / Jamoa",
                "separator": True,
                "items": [
                    {
                        "title": "Ijarachilar",
                        "icon": "apartment",
                        "link": "admin:accounts_tenant_changelist",
                    },
                    {
                        "title": "Foydalanuvchilar",
                        "icon": "group",
                        "link": "admin:accounts_user_changelist",
                        "show_search": True,
                        "show_history": True,
                    },
                    {
                        "title": "Guruhlar",
                        "icon": "managed_accounts",
                        "link": "admin:auth_group_changelist",
                    },
                ],
            },
            {
                "title": "Katalog",
                "separator": True,
                "items": [
                    {
                        "title": "Kategoriyalar",
                        "icon": "sell",
                        "link": "admin:catalog_category_changelist",
                        "show_search": True,
                        "show_history": True,
                    },
                    {
                        "title": "Mahsulotlar",
                        "icon": "inventory_2",
                        "link": "admin:catalog_product_changelist",
                        "show_search": True,
                        "show_history": True,
                    },
                    {
                        "title": "Mahsulot variantlari",
                        "icon": "palette",
                        "link": "admin:catalog_productvariant_changelist",
                    },
                    {
                        "title": "Mahsulot rasmlari",
                        "icon": "image",
                        "link": "admin:catalog_productimage_changelist",
                    },
                    {
                        "title": "Fasonlar",
                        "icon": "curtains",
                        "link": "admin:catalog_fason_changelist",
                        "show_search": True,
                    },
                ],
            },
            {
                "title": "Narx va hisob",
                "separator": True,
                "items": [
                    {
                        "title": "Hisob qoidalari",
                        "icon": "calculate",
                        "link": "admin:pricing_calcrule_changelist",
                        "show_search": True,
                    },
                    {
                        "title": "Xizmat narxlari",
                        "icon": "sell",
                        "link": "admin:pricing_serviceprice_changelist",
                        "show_search": True,
                    },
                    {
                        "title": "Chegirma bosqichlari",
                        "icon": "percent",
                        "link": "admin:pricing_discounttier_changelist",
                    },
                    {
                        "title": "Chegirma siyosati",
                        "icon": "policy",
                        "link": "admin:pricing_discountpolicy_changelist",
                    },
                    {
                        "title": "Buyurtma sozlamalari",
                        "icon": "tune",
                        "link": "admin:pricing_orderdefaults_changelist",
                    },
                    {
                        "title": "Model narxlari",
                        "icon": "attach_money",
                        "link": "admin:pricing_modelpricing_changelist",
                    },
                ],
            },
            {
                "title": "Bilimlar bazasi",
                "separator": True,
                "items": [
                    {
                        "title": "Bilim qoidalari",
                        "icon": "school",
                        "link": "admin:knowledge_knowledgerule_changelist",
                        "show_search": True,
                    },
                ],
            },
            {
                "title": "Suhbatlar",
                "separator": True,
                "items": [
                    {
                        "title": "Suhbatlar",
                        "icon": "chat",
                        "link": "admin:chat_conversation_changelist",
                        "show_search": True,
                        "show_history": True,
                    },
                    {
                        "title": "Xabarlar",
                        "icon": "forum",
                        "link": "admin:chat_message_changelist",
                        "show_search": True,
                    },
                ],
            },
            {
                "title": "Buyurtmalar",
                "separator": True,
                "items": [
                    {
                        "title": "Buyurtmalar",
                        "icon": "receipt_long",
                        "link": "admin:orders_order_changelist",
                        "show_search": True,
                        "show_history": True,
                    },
                    {
                        "title": "Buyurtma o'lchovlari",
                        "icon": "straighten",
                        "link": "admin:orders_ordermeasurement_changelist",
                    },
                    {
                        "title": "Buyurtma parda bo'laklari",
                        "icon": "curtains_closed",
                        "link": "admin:orders_ordercurtainpart_changelist",
                    },
                    {
                        "title": "Buyurtma aksessuarlari",
                        "icon": "hardware",
                        "link": "admin:orders_orderaccessory_changelist",
                    },
                    {
                        "title": "Buyurtma xizmatlari",
                        "icon": "list_alt",
                        "link": "admin:orders_orderitem_changelist",
                    },
                ],
            },
            {
                "title": "Sarf / limitlar",
                "separator": True,
                "items": [
                    {
                        "title": "Foydalanish qaydnomalari",
                        "icon": "monitoring",
                        "link": "admin:usage_usagerecord_changelist",
                    },
                    {
                        "title": "Kunlik yig'malar",
                        "icon": "calendar_month",
                        "link": "admin:usage_usagedaily_changelist",
                    },
                    {
                        "title": "Foydalanish limitlari",
                        "icon": "speed",
                        "link": "admin:usage_usagelimit_changelist",
                    },
                ],
            },
            {
                "title": "Sozlamalar / prompt",
                "separator": True,
                "items": [
                    {
                        "title": "System prompt versiyalari",
                        "icon": "description",
                        "link": "admin:prompts_promptversion_changelist",
                        "show_history": True,
                    },
                ],
            },
        ],
    },
}

# Simple JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# Celery va Redis
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
GRPC_PORT = env.int("GRPC_PORT", default=9091)
GRPC_MAX_WORKERS = env.int("GRPC_MAX_WORKERS", default=16)
AGENT_SERVICE_TOKEN = env("AGENT_SERVICE_TOKEN", default="")
# Go agent gRPC manzili (Django -> Agent.Chat/VoiceChat/ResetSession); docker da "agent:9090".
GRPC_AGENT_ADDR = env("GRPC_AGENT_ADDR", default="localhost:50051")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

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
