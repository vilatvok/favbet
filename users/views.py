from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action

from users.models import User
from users.permissions import IsOwner
from users.serializers import (
    DemoWalletSerializer,
    UserCreateSerializer,
    UserSerializer,
    PasswordSerializer
)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsOwner]

    def get_serializer_class(self):
        if self.action in ['list', 'create']:
            return UserCreateSerializer
        return UserSerializer

    @action(methods=['post'], detail=True)
    def change_password(self, request, pk=None):
        serializer = PasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.get_object()
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({'status': 'Success'}, status=status.HTTP_201_CREATED)

    @action(detail=True, url_name='demo_wallet')
    def get_demo_wallet(self, request, pk=None):
        user = self.get_object()
        wallet = user.demo_wallet
        serializer = DemoWalletSerializer(wallet)
        return Response(serializer.data)
