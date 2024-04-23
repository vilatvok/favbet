from rest_framework import serializers

from teams.models import Competition, Team


class CompetitionSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='competition-detail',
        lookup_field='slug',
    )
    country = serializers.CharField(source='country.name')
    season = serializers.CharField(source='season.name')

    class Meta:
        model = Competition
        exclude = ['slug']


class TeamCompetitionsSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)


class TeamSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='team-detail',
        lookup_field='slug',
    )
    country = serializers.CharField(source='country.name')
    competitions = serializers.SlugRelatedField(
        slug_field='name',
        many=True,
        read_only=True,
    )

    class Meta:
        model = Team
        exclude = ['slug']
