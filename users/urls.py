# users/urls.py
# Purpose: Local URL routes for the users app.

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import AdminOnlyView, LoginView, LogoutView, ManagerOnlyView, MeView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("admin-only/", AdminOnlyView.as_view(), name="admin-only"),
    path("manager-only/", ManagerOnlyView.as_view(), name="manager-only"),
]
