"""
Django settings for booking_api_django_new project.

Generated by 'django-admin startproject' using Django 3.0.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""
import logging
import os
from datetime import timedelta

import orjson
from dotenv import load_dotenv

load_dotenv(dotenv_path='booking_api_django_new/environments/' + os.environ.get('BRANCH', default='dev_simple_office') + '.env')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPEND_SLASH = False
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'yv18vx3=v*sm0)ma#j1)qubg$+lpeqg6vg9$cvcvm8vz2qazq$'

LOCAL = False if os.environ.get('LOCAL') else True
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False  # if os.environ.get('BRANCH') == 'prod_gpn' else True

ADMIN_HOST = os.environ.get('ADMIN_HOST')

SMS_MOCK_CONFIRM = os.environ.get("SMS_MOCK_CONFIRM")

KEY_EXPIRATION = 60  # seconds

BOOKING_PUSH_NOTIFY_UNTIL_MINS = 60
BOOKING_TIMEDELTA_CHECK = 15
PUSH_HOST = "https://push.liis.su"
PUSH_USERNAME = "omniman"
PUSH_PASSWORD = "slicing_unshipped_stopping_mystified"
PUSH_TOKEN = ''

SERVER_EMAIL = 'support@liis.su'
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
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],

    'EXCEPTION_HANDLER': 'core.exception.detail_exception_handler',

    'DEFAULT_RENDERER_CLASSES': [
        'drf_orjson_renderer.renderers.ORJSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'ORJSON_RENDERER_OPTIONS': (
        orjson.OPT_NON_STR_KEYS,
        orjson.OPT_SERIALIZE_DATACLASS,
        orjson.OPT_SERIALIZE_NUMPY,
    ),
    'DEFAULT_PARSER_CLASSES': (
        'drf_orjson_renderer.parsers.ORJSONParser',
    ),
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

ACCESS_TOKEN_LIFETIME = timedelta(days=7) if DEBUG else timedelta(hours=1)

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': ACCESS_TOKEN_LIFETIME,
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
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
    'group_bookings',
    'files',
    'floors',
    'licenses',
    'offices',
    'rooms',
    'tables',
    'room_types',
    'reports',
    'bookings',
    'push_tokens',
    'rest_framework',
    'drf_yasg',
    'mail',
    'django_apscheduler',
    'django_filters',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.postgres',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django-advanced_password_validation',
]
# 'django.contrib.admin',
#REDIS_URL = os.environ.get('REDIS_URL') or "redis://2.59.41.133:5556"

REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get('REDIS_PORT')
REDIS_SECRET_KEY = os.environ.get('REDIS_SECRET_KEY')
if REDIS_HOST and REDIS_PORT and REDIS_SECRET_KEY:
    REDIS_URL = f'redis://:{REDIS_SECRET_KEY}@{REDIS_HOST}:{REDIS_PORT}/0'
else:
    REDIS_URL = "redis://2.59.41.133:5556"



BROKER_PROTOCOL = os.environ.get('BROKER_PROTOCOL')
BROKER_HOST = os.environ.get('BROKER_HOST')
BROKER_PORT = os.environ.get('BROKER_PORT')
BROKER_SECRET_KEY = os.environ.get('BROKER_SECRET_KEY')

if BROKER_PROTOCOL and BROKER_HOST and BROKER_PORT and BROKER_SECRET_KEY:
    CELERY_BROKER_URL = f'{BROKER_PROTOCOL}://:{BROKER_SECRET_KEY}@{BROKER_HOST}:{BROKER_PORT}/1'
else:
    CELERY_BROKER_URL = "redis://2.59.41.133:5556"
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['application/json']

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}


ADMINS = [('Support', 'support@liis.su'), ]

DATA_UPLOAD_MAX_MEMORY_SIZE = 11534336

REQUEST_LOGGING_DATA_LOG_LEVEL = logging.INFO

REQUEST_LOGGING_MAX_BODY_LENGTH = 1000

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
            'django.server': {
                '()': 'django.utils.log.ServerFormatter',
                'format': '[{server_time}] {message}',
                'style': '{',
            }
        },
    'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse',
            },
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            },
            'not_500': {
                '()': 'core.filters.Not500'
            },
            'base_handler_log': {
                '()': 'core.filters.FilterBaseHandlerLog'
            }

        },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'django.server',
            'filters': ['base_handler_log']
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['not_500']
        },
        'logfile': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'filename': BASE_DIR + '/simple_office.log',
            'filters': ['base_handler_log'],
            'formatter': 'django.server'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console', 'logfile'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

MIDDLEWARE = [
    'core.middlewares.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'core.middlewares.SimpleLogMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
# 'django.contrib.messages.middleware.MessageMiddleware',
if LOCAL:
    MIDDLEWARE += ['booking_api_django_new.debug.PrintSqlQuery']
    MIDDLEWARE += ['core.middlewares.RequestTimeMiddleware']

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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('HOST') or '2.59.41.133',
        'PORT': os.environ.get('PORT') or '5432',
        'CONN_MAX_AGE': 1
    }
}

# SCHEDULER_CONFIG = {
#     "apscheduler.jobstores.default": {
#         "class": "django_apscheduler.jobstores:DjangoJobStore"
#     },
#     'apscheduler.executors.processpool': {
#         "type": "processpool",
#         "max_workers": "2"
#     },
#     'apscheduler.job_defaults.coalesce': 'false',
#     'apscheduler.job_defaults.max_instances': '2',
# }
# SCHEDULER_AUTOSTART = True

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
    {
        'NAME': 'django-advanced_password_validation.advanced_password_validation.ContainsDigitsValidator',
        'OPTIONS': {
            'min_digits': 1
        }
    },
    {
        'NAME': 'django-advanced_password_validation.advanced_password_validation.ContainsUppercaseValidator',
        'OPTIONS': {
            'min_uppercase': 1
        }
    },
    {
        'NAME': 'django-advanced_password_validation.advanced_password_validation.ContainsLowercaseValidator',
        'OPTIONS': {
            'min_lowercase': 1
        }
    },
    {
        'NAME': 'django-advanced_password_validation.advanced_password_validation.ContainsSpecialCharactersValidator',
        'OPTIONS': {
            'min_characters': 1
        }
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
FILES_USERNAME = os.environ.get('FILES_USERNAME').replace('"', '') if os.environ.get('FILES_USERNAME') else None
FILES_PASSWORD = os.environ.get('FILES_PASSWORD').replace('"', '') if os.environ.get('FILES_PASSWORD') else None
FILES_HOST = os.environ.get('FILES_HOST').replace('"', '') if os.environ.get('FILES_HOST') else None

HARDCODED_PHONE_NUMBER = (
    "+13371337133"  # hardcoded phone number for passing AppStore and PlayMarket tests
)
HARDCODED_SMS_CODE = 4832
