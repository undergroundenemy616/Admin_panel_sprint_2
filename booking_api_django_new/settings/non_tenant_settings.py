from .base import *

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
    'teams',
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

if LOCAL:
    MIDDLEWARE += ['booking_api_django_new.debug.PrintSqlQuery']
    MIDDLEWARE += ['core.middlewares.RequestTimeMiddleware']

ROOT_URLCONF = 'booking_api_django_new.urls'

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
