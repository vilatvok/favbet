from rest_framework import serializers

from bets.models import Bet, Match


class MatchSerializer(serializers.ModelSerializer):
    competition = serializers.CharField(source='competition.name')
    match_name = serializers.CharField()

    class Meta:
        model = Match
        exclude = ['uid', 'home_team', 'away_team']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        score = representation.pop('score')
        if not score:
            representation['score'] = 'Match hasnt been started yet'
        return representation


class BetSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(source='user.username')
    match = serializers.StringRelatedField(source='match.match_name')

    class Meta:
        model = Bet
        exclude = ['demo', 'payment_id']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('user')
        income = representation.get('income')
        if not income:
            representation.pop('income')
        return representation
