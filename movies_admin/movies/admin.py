from django.contrib import admin

from movies.models import FilmWork, Genre, Person


class DirectorsInline(admin.TabularInline):
    model = FilmWork.directors.through
    extra = 0
    verbose_name = "режиссер"
    verbose_name_plural = "режиссеры"


class WritersInline(admin.TabularInline):
    model = FilmWork.writers.through
    extra = 0
    verbose_name = "сценарист"
    verbose_name_plural = "сценаристы"


class ActorsInline(admin.TabularInline):
    model = FilmWork.actors.through
    extra = 0
    verbose_name = "актер"
    verbose_name_plural = "актеры"


@admin.register(FilmWork)
class FilmWorkAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'creation_date', 'rating',)

    fieldsets = (
        (None, {
            'fields': ('title', 'type', 'description', 'creation_date')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('age_qualification', 'file_path', 'rating', 'writers', 'genres', 'directors', 'actors'),
        }),
    )

    raw_id_fields = ('genres', 'writers', 'directors', 'actors')

    inlines = [
        DirectorsInline,
        WritersInline,
        ActorsInline
    ]

    list_filter = ('type', 'age_qualification', 'directors', 'actors', 'writers', 'rating',)
    search_fields = ('title', 'description', 'id',)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'get_roles')

    def get_roles(self, obj):
        return ",\n".join([role.title for role in obj.roles.all()])


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('title', 'description',)
    search_fields = ('title', 'description',)
