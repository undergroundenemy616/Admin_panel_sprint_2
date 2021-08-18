from booking_api_django_new.base_settings import *

SHARED_APPS = [
    'django_tenants',
    'clients',
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
    'management',
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

TENANT_APPS = [
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
    'management',
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

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

TENANT_MODEL = 'clients.Client'
TENANT_DOMAIN_MODEL = 'clients.Domain'

MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',
    'core.middlewares.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'core.middlewares.SimpleLogMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'clients.middlewares.BlockUnpaidTenantMiddleware'
]

ROOT_URLCONF = 'booking_api_django_new.urls'
PUBLIC_SCHEMA_URLCONF = 'booking_api_django_new.urls_public'

DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('HOST') or '2.59.41.133',
        'PORT': os.environ.get('PORT') or '5432',
        'CONN_MAX_AGE': 1
    }
}

DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

SHOW_PUBLIC_IF_NO_TENANT_FOUND = True
