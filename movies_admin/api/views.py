from typing import Any

from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view


class APISchemeGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.host = '127.0.0.1:8000'
        schema.schemes = [f'http', f'https']
        return schema


def get_swagger() -> Any:
    swagger = get_schema_view(
        openapi.Info(
            title="Movie API",
            default_version='v1',
            contact=openapi.Contact(email="tfo@liis.su"),
        ),
        public=True,
        generator_class=APISchemeGenerator
    )
    return swagger
