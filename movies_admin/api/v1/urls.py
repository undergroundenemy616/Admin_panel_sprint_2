from rest_framework.routers import DefaultRouter
from api.v1 import views

movie_router = DefaultRouter()
movie_router.register(r'movies', views.MovieViewSet)

urlpatterns = movie_router.urls
