from rest_framework.fields import ChoiceField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from movies.models import FilmWork, Genre, Person


class MovieSerializer(ModelSerializer):
    genres = PrimaryKeyRelatedField(queryset=Genre.objects.all(), many=True, required=False)
    actors = PrimaryKeyRelatedField(queryset=Person.objects.all(), many=True, required=False)
    directors = PrimaryKeyRelatedField(queryset=Person.objects.all(), many=True, required=False)
    writers = PrimaryKeyRelatedField(queryset=Person.objects.all(), many=True, required=False)
    type = ChoiceField(choices=FilmWork.FilmWorkType.choices)

    class Meta:
        model = FilmWork
        fields = ['id', 'title', 'description', 'creation_date',
                  'rating', 'type', 'genres', 'actors', 'directors',
                  'writers']

    def to_representation(self, instance):
        representaion = super(MovieSerializer, self).to_representation(instance)
        representaion['genres'] = [genre.title for genre in instance.genres.all()]
        representaion['actors'] = [f'{actor.first_name} {actor.last_name}' for actor in instance.actors.all()]
        representaion['writers'] = [f'{writers.first_name} {writers.last_name}' for writers in instance.writers.all()]
        representaion['directors'] = [f'{directors.first_name} {directors.last_name}' for directors in instance.directors.all()]
        return representaion


