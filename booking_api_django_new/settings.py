"""
Django settings for booking_api_django_new project.

Generated by 'django-admin startproject' using Django 3.0.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""
import datetime
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

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

KEY_EXPIRATION = 60 * 3  # 3 minutes

if DEBUG is True:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = []

# Application definition

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'core.authorization.BookingAuthentication',
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

JWT_AUTH = {
    # 'JWT_ENCODE_HANDLER':
    # 'rest_framework_jwt.utils.jwt_encode_handler',
    'JWT_ENCODE_HANDLER':
        'users.backends.jwt_encode_handler',

    'JWT_DECODE_HANDLER':
        'users.backends.jwt_decode_handler',

    'JWT_PAYLOAD_HANDLER':
        'users.backends.jwt_payload_handler',

    'JWT_PAYLOAD_GET_USER_ID_HANDLER':
        'rest_framework_jwt.utils.jwt_get_user_id_from_payload_handler',

    'JWT_RESPONSE_PAYLOAD_HANDLER':
        'users.backends.jwt_response_payload_handler',

    'JWT_PAYLOAD_GET_USERNAME_HANDLER':
        'users.backends.jwt_get_username_from_payload',

    'JWT_SECRET_KEY': SECRET_KEY,
    'JWT_GET_USER_SECRET_KEY': None,
    'JWT_ALGORITHM': 'HS256',
    'JWT_PUBLIC_KEY': None,
    'JWT_VERIFY': True,
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=60 * 30),  # expiration 30 minutes, then go to refresh

    'JWT_ALLOW_REFRESH': True,  # Was False
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=14),  # 14 days for login
    'JWT_AUTH_HEADER_PREFIX': 'Bearer',
}

INSTALLED_APPS = [
    'users.apps.UsersConfig',
    'groups.apps.GroupsConfig',
    'files',
    'floors',
    'licenses',
    'offices',
    'rooms',
    'drf_yasg',
    'tables',
    'room_types',
    'bookings',
    'rest_framework',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://2.59.41.133:5556",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

LOGGING = {
    'version': 1,
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        }
    }
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

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
