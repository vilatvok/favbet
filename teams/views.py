from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.pagination import PageNumberPagination

from teams.models import Competition, Team
from teams.serializers import CompetitionSerializer, TeamSerializer

from django_filters.rest_framework import DjangoFilterBackend


class CompetitionViewSet(ReadOnlyModelViewSet):
    queryset = Competition.objects.select_related('country', 'season')
    serializer_class = CompetitionSerializer
    lookup_field = 'slug'


class TeamPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class TeamViewSet(ReadOnlyModelViewSet):
    queryset = (
        Team.objects.select_related('country').prefetch_related('competitions')
    )
    serializer_class = TeamSerializer
    pagination_class = TeamPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['country', 'competitions']
    search_fields = ['^name']
    lookup_field = 'slug'
