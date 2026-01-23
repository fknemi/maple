# core/urls.py
from django.urls import path

from core import views

urlpatterns = [
    # API Authentication endpoints
    path("auth/register", views.register, name="api_register"),
    path("auth/login", views.login, name="api_login"),
    path("auth/logout", views.logout, name="api_logout"),
    path("auth/me", views.get_current_user, name="current_user"),
    # GitHub OAuth
    path("auth/github", views.github_login, name="github_login"),
    path("auth/github/callback", views.github_callback, name="github_callback"),  # GitHub sends 'code' here
    path("auth/callback", views.auth_success, name="auth_callback"),  # Your app
    # Protected example
    path("protected", views.protected_post, name="protected"),
]
