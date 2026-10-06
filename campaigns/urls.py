from django.urls import path

from . import views

urlpatterns = [
    path("campanhas/", views.lista, name="campanha-lista"),
    path("campanhas/<int:pk>/", views.detalhe, name="campanha-detalhe"),
    path("painel/campanhas/", views.painel, name="campanha-painel"),
    path("painel/campanhas/nova/", views.nova, name="campanha-nova"),
    path("painel/campanhas/<int:pk>/editar/", views.editar, name="campanha-editar"),
    path("painel/campanhas/<int:pk>/estado/", views.estado, name="campanha-estado"),
    path("painel/campanhas/<int:pk>/excluir/", views.excluir, name="campanha-excluir"),
]
