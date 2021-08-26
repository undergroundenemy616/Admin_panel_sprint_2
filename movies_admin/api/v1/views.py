from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from api.v1.pagination import MoviePagination
from api.v1.serializer import MovieSerializer
from movies.models import FilmWork


class MovieViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    serializer_class = MovieSerializer
    pagination_class = MoviePagination
    permission_classes = [AllowAny]
    queryset = FilmWork.objects.prefetch_related('genres', 'actors', 'writers', 'directors')
