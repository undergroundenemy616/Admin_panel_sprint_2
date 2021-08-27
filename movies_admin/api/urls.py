from django.conf.urls import url
from api.views import get_swagger
from django.urls import path, include


schema_view = get_swagger()

urlpatterns = [
    path('v1/', include('api.v1.urls')),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

]
