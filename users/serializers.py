# users/serializers.py
# Purpose: Convert Django model instances <-> JSON for API requests/responses.
# Note: We'll use Django's built-in User model for speed (no custom user).

from django.contrib.auth.models import User
from rest_framework import serializers


class UserPublicSerializer(serializers.ModelSerializer):
    """
    Serializer used to expose safe user information.
    """
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer used for user registration.
    Ensures the password is write-only and is hashed correctly.
    """
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        # Use create_user so the password is hashed properly.
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user
