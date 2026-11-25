# users/views.py
# Purpose: Handle all user-related endpoints such as registration, login, logout,
# profile, and role-based routes (admin-only / manager-only).

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .permissions import IsManager
from .serializers import RegisterSerializer, UserPublicSerializer


class RegisterView(APIView):
    """
    POST /users/register/
    Allows anyone to create a new user account.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            data = UserPublicSerializer(user).data
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that returns access & refresh tokens
    plus basic user information.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Example of adding custom claims:
        token["username"] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add user info to the response so the frontend/test can see it.
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
        }
        return data


class LoginView(TokenObtainPairView):
    """
    POST /users/login/
    Returns JWT access and refresh tokens for valid credentials.
    """
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


class MeView(APIView):
    """
    GET /users/me/
    Returns the profile of the currently authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserPublicSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /users/logout/
    Body: {"refresh": "<refresh token>"}
    Blacklists the refresh token so it can't be used to get new access tokens.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"detail": "A refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh)
            # Stop one user from logging out someone else's session
            if str(token["user_id"]) != str(request.user.id):
                return Response({"detail": "Token does not belong to you."}, status=status.HTTP_403_FORBIDDEN)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Logged out."}, status=status.HTTP_205_RESET_CONTENT)


class AdminOnlyView(APIView):
    """
    GET /users/admin-only/
    Only staff/admin users can access this.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response({"detail": "You are an admin. Authorization works!"}, status=status.HTTP_200_OK)


class ManagerOnlyView(APIView):
    """
    GET /users/manager-only/
    Role-based authorization using a Django Group: only members of 'manager' can access this.
    """
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        return Response({"detail": "You are a manager. Group-based authorization works!"}, status=status.HTTP_200_OK)
