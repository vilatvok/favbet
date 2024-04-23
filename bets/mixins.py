from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated

from bets.models import Bet
from bets.serializers import BetSerializer
from bets.permissions import IsMatchStarted


class BetMixin(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    serializer_class = BetSerializer
    permission_classes = [IsAuthenticated, IsMatchStarted]
    is_demo = None

    def get_queryset(self):
        return (
            Bet.objects.filter(user=self.request.user, demo=self.is_demo).
            select_related('match', 'user')
        )
