from django.contrib import admin
from django.http.request import HttpRequest

from teams.models import Country, Competition, Team


class TeamInline(admin.TabularInline):
    model = Team.competitions.through
    extra = 1


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('uid', 'name', 'logo')
    fields = [
        'uid',
        ('name', 'slug'),
        'logo',
    ]
    search_fields = ('name',)
    prepopulated_fields = {'slug': ['name']}


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('uid', 'name', 'season', 'country', 'logo')
    list_filter = ('country',)
    fields = [
        'uid',
        ('name', 'slug'),
        'country',
        'season',
        'logo',
    ]
    search_fields = ('name',)
    prepopulated_fields = {'slug': ['name']}
    inlines = [TeamInline]


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('uid', 'name', 'country', 'logo', 'team_competitions')
    list_filter = ('country', 'competitions')
    list_per_page = 20
    fields = [
        'uid',
        ('name', 'slug'),
        'country',
        'competitions',
        'logo',
    ]
    search_fields = ('name',)
    prepopulated_fields = {'slug': ['name']}
    actions = ('set_leagues',)

    @admin.action(description='Set leagues')
    def set_leagues(self, request, queryset):
        comp = {c.country.id: c.id for c in Competition.objects.all()}
        for i in queryset:
            c = comp.get(i.country.id)
            i.competitions.add(c)

    def get_queryset(self, request: HttpRequest):
        return super().get_queryset(request).prefetch_related('competitions')

    def team_competitions(self, obj):
        return [i.name for i in obj.competitions.all()]
