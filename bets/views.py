import stripe

from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError

from django_filters.rest_framework import DjangoFilterBackend

from bets.models import Bet, Match
from bets.serializers import BetSerializer, MatchSerializer
from bets.permissions import IsBetExists, IsMatchStarted
from bets.mixins import BetMixin

from users.models import User


stripe.api_key = settings.STRIPE_SECRET_KEY


class MatchPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 20


class MatchViewSet(ReadOnlyModelViewSet):
    queryset = (
        Match.objects.filter(date__gt=timezone.now()).
        select_related('home_team', 'away_team', 'competition')
    )
    serializer_class = MatchSerializer
    pagination_class = MatchPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['^home_team__name', '^away_team__name']
    filterset_fields = ['competition']
    ordering_fields = ['date']

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[
            IsAuthenticated,
            IsMatchStarted,
            IsBetExists,
        ],
    )
    def make_bet(self, request, pk=None):
        match = self.get_object()
        user = request.user
        serializer = BetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            wallet = user.demo_wallet
            if wallet.is_active:
                value = Bet._meta.get_field('amount').validators[0].limit_value
                if wallet.balance < value:
                    raise ValidationError('Your balance is too low')
                serializer.save(user=user, match=match)
                return Response(
                    data={'status': 'Success'},
                    status=status.HTTP_201_CREATED,
                )
            success_url = 'http://localhost:8000/bets/'
            cancel_url = f'http://localhost:8000/matches/{match.id}/'
            amount = int(serializer.validated_data['amount'] * 100)

            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'unit_amount': amount,
                            'product_data': {
                                'name': match.match_name,
                            },
                        },
                        'quantity': 1,
                    }
                ],
                metadata={
                    'user_id': user.id,
                    'match_id': match.id,
                    'prediction': serializer.validated_data['prediction'],
                },
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=user.email,
            )

            success_status = {
                'status': 'redirect',
                'payment_link': checkout_session.url,
            }
            return Response(success_status, status=status.HTTP_303_SEE_OTHER)
        except Exception as e:
            return Response(
                data={'status': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DemoBetViewSet(BetMixin):
    is_demo = True


class BetViewSet(BetMixin):
    is_demo = False


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK,
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata']['user_id']
        match_id = session['metadata']['match_id']
        prediction = session['metadata']['prediction']
        amount = session['amount_total'] / 100
        payment_id = session['payment_intent']

        user = User.objects.get(id=user_id)
        match = Match.objects.get(id=match_id)
        Bet.objects.create(
            user=user,
            match=match,
            prediction=prediction,
            amount=amount,
            demo=False,
            payment_id=payment_id,
        )
    return HttpResponse(status=200)
