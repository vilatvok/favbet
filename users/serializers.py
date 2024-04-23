from rest_framework import serializers

from django.db import transaction
from django.contrib.auth import password_validation

from users.models import User, DemoWallet


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        repr_copy = representation.copy()
        for k, v in repr_copy.items():
            try:
                if not len(v):
                    representation.pop(k)
            except TypeError:
                continue
        return representation


class UserCreateSerializer(UserSerializer):
    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ['password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        instance = User.objects.create_user(**validated_data)
        DemoWallet.objects.create(user=instance)
        return instance


class PasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, value):
        password_validation.validate_password(value['new_password'])
        if value['old_password'] != value['new_password']:
            raise serializers.ValidationError('Passwords do not match')
        return value


class DemoWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemoWallet
        exclude = ['user']
