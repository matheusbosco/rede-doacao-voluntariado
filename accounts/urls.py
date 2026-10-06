from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.painel, name="painel"),
    path("cadastro/", views.cadastro, name="cadastro"),
    path("entrar/", auth_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
]
