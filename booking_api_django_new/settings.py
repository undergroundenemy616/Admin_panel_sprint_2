"""
Django settings for booking_api_django_new project.

Generated by 'django-admin startproject' using Django 3.0.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""
from datetime import timedelta
import os

from dotenv import load_dotenv

load_dotenv(dotenv_path='booking_api_django_new/environments/' + os.environ.get('BRANCH', default='master') + '.env')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPEND_SLASH = False
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'yv18vx3=v*sm0)ma#j1)qubg$+lpeqg6vg9$cvcvm8vz2qazq$'

LOCAL = True if os.getenv('LOCAL') == 'True' else False
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

KEY_EXPIRATION = 60 * 3  # 3 minutes

BOOKING_PUSH_NOTIFY_UNTIL_MINS = 60

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.yandex.com'
EMAIL_PORT = 465
EMAIL_HOST_USER = 'support@liis.su'
EMAIL_HOST_PASSWORD = 'Rfr:tktpyjujhcr&'
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True

ALLOWED_HOSTS = ['*']

# Application definition

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
}

SMSC = {
    'SMSC_LOGIN': "liis_engineering",  # логин клиента
    'SMSC_PASSWORD': "Zz5eM5!kn!",  # пароль
    'SMSC_POST': False,  # использовать метод POST
    'SMSC_HTTPS': False,  # использовать HTTPS протокол
    'SMSC_CHARSET': 'utf-8',  # кодировка сообщения (windows-1251 или koi8-r), по умолчанию используется utf-8
    'SMSC_DEBUG': True,  # флаг отладки
    'SMSC_SEND_URL': 'https://smsc.ru/sys/send.php'
    # 'SMSC_COST_URL': 'https://smsc.ru/sys/send.php?cost=1'
}

ACCESS_TOKEN_LIFETIME = timedelta(days=1) if DEBUG else timedelta(minutes=30)

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': ACCESS_TOKEN_LIFETIME,
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer', 'JWT'),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=30),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

INSTALLED_APPS = [
    'users.apps.UsersConfig',
    'groups.apps.GroupsConfig',
    'files',
    'floors',
    'licenses',
    'offices',
    'rooms',
    'tables',
    'room_types',
    'report',
    'bookings',
    'push_tokens',
    'rest_framework',
    'drf_yasg',
    'mail',
    'django_apscheduler',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

REDIS_URL = os.environ.get('REDIS_URL') or "redis://2.59.41.133:5556"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# LOGGING = {
#     'version': 1,
#     'filters': {
#         'require_debug_true': {
#             '()': 'django.utils.log.RequireDebugTrue',
#         }
#     },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'filters': ['require_debug_true'],
#             'class': 'logging.StreamHandler',
#         }
#     },
#     'loggers': {
#         'django.db.backends': {
#             'level': 'DEBUG',
#             'handlers': ['console'],
#         }
#     }
# }

MIDDLEWARE = [
    'core.middlewares.CorsMiddleware',
    'core.middlewares.RequestTimeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if LOCAL:
    MIDDLEWARE += ['booking_api_django_new.debug.PrintSqlQuery']

ROOT_URLCONF = 'booking_api_django_new.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'booking_api_django_new.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

print({
    'NAME': os.environ.get('DB_NAME'),
    'USER': os.environ.get('DB_USER'),
    'PASSWORD': os.environ.get('DB_PASSWORD'),
})

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('HOST') or '2.59.41.133',
        'PORT': os.environ.get('PORT') or '5432',
    }
}

SCHEDULER_CONFIG = {
    "apscheduler.jobstores.default": {
        "class": "django_apscheduler.jobstores:DjangoJobStore"
    },
    'apscheduler.executors.processpool': {
        "type": "threadpool"
    },
}
SCHEDULER_AUTOSTART = True

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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

SWAGGER_SETTINGS = {
    'SHOW_REQUEST_HEADERS': True,
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT authorization'
        }
    }
}

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'upload/')
MEDIA_URL = '/media/'
FILES_USERNAME = os.environ.get('FILES_USERNAME')
FILES_PASSWORD = os.environ.get('FILES_PASSWORD')
FILES_HOST = os.environ.get('FILES_HOST')
