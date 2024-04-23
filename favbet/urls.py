from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from users.views import UserViewSet
from bets.views import BetViewSet, DemoBetViewSet, MatchViewSet, stripe_webhook
from teams.views import CompetitionViewSet, TeamViewSet

router = DefaultRouter()

router.register(r'users', UserViewSet, basename='user')
router.register(r'matches', MatchViewSet, basename='match')
router.register(r'bets', BetViewSet, basename='bet')
router.register(r'demo_bets', DemoBetViewSet, basename='demo_bet')
router.register(r'competitions', CompetitionViewSet, basename='competition')
router.register(r'teams', TeamViewSet, basename='team')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('__debug__/', include('debug_toolbar.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/schema/swagger-ui/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path(
        'api/schema/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc',
    ),
    path('auth/', include('drf_social_oauth2.urls', namespace='drf')),
    path('stripe-webhook/', stripe_webhook, name='stripe-webhook'),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
