from django.urls import path

from . import listas, views

urlpatterns = [
    path("campanhas/<int:pk>/contribuir/", views.criar, name="contribuicao-criar"),
    path("minhas-contribuicoes/", listas.minhas, name="contribuicao-minhas"),
    path("minhas-contribuicoes/<int:pk>/editar/", views.editar, name="contribuicao-editar"),
    path("minhas-contribuicoes/<int:pk>/cancelar/", views.cancelar, name="contribuicao-cancelar"),
    path("painel/contribuicoes/", listas.painel, name="contribuicao-painel"),
    path("painel/contribuicoes/<int:pk>/avaliar/", views.avaliar, name="contribuicao-avaliar"),
]
