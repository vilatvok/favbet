from rest_framework.permissions import BasePermission

from bets.models import Bet


class IsBetExists(BasePermission):
    message = 'You have already bet on this match'

    def has_object_permission(self, request, view, obj):
        exist_obj = Bet.objects.filter(
            user=request.user,
            match=obj,
        )
        return not exist_obj.exists()


class IsMatchStarted(BasePermission):
    message = 'Match has been already started'

    def has_object_permission(self, request, view, obj):
        if view.action == 'bet':
            return obj.status == 'Pending'
        elif view.action == 'destroy':
            return obj.match.status == 'Pending'
        return True
