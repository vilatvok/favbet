from django.contrib import admin
from django.contrib.admin.decorators import action

from bets.models import Match, Bet


class BetInline(admin.TabularInline):
    model = Bet
    extra = 1
    readonly_fields = ['income']


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = [
        'uid',
        'competition',
        'match_name',
        'home_team_odds',
        'draw_odds',
        'away_team_odds',
        'status',
        'date',
    ]
    fields = [
        'uid',
        'competition',
        ('home_team', 'away_team'),
        ('home_team_odds', 'draw_odds', 'away_team_odds'),
        'status',
        'score',
        'date',
    ]
    list_editable = ['status']
    list_filter = ['competition', 'status', 'date']
    list_per_page = 20
    list_max_show_all = 100
    search_fields = ['home_team__name', 'away_team__name']
    autocomplete_fields = ['home_team', 'away_team']
    ordering = ['-date']
    date_hierarchy = 'date'
    actions = ['set_pending', 'set_live', 'set_finished', 'set_cancelled']
    inlines = [BetInline]

    @action(description='Set pending status')
    def set_pending(self, request, queryset):
        queryset.update(status='Pending')

    @action(description='Set live status')
    def set_live(self, request, queryset):
        queryset.update(status='Live')

    @action(description='Set finished status')
    def set_finished(self, request, queryset):
        queryset.update(status='Finished')

    @action(description='Set cancelled status')
    def set_cancelled(self, request, queryset):
        queryset.update(status='Cancelled')


@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'match',
        'prediction',
        'amount',
        'status',
        'demo',
        'income',
        'created',
    ]
    list_filter = ['user', 'created']
    list_editable = ['status', 'demo']
    readonly_fields = ['income', 'payment_id']
    ordering = ['-created']
    autocomplete_fields = ['user', 'match']
