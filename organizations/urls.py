from django.urls import path

from . import postagens, views

urlpatterns = [
    path("postagens/", postagens.lista, name="postagem-lista"),
    path("postagens/<int:pk>/", postagens.detalhe, name="postagem-detalhe"),
    path("painel/postagens/", postagens.painel, name="postagem-painel"),
    path("painel/postagens/nova/", postagens.nova, name="postagem-nova"),
    path("painel/postagens/<int:pk>/editar/", postagens.editar, name="postagem-editar"),
    path("painel/postagens/<int:pk>/excluir/", postagens.excluir, name="postagem-excluir"),
    path("ongs/", views.lista, name="ong-lista"),
    path("ongs/nova/", views.nova, name="ong-nova"),
    path("ongs/minha/", views.minha, name="ong-minha"),
    path("ongs/<int:pk>/", views.detalhe, name="ong-detalhe"),
    path("ongs/<int:pk>/editar/", views.editar, name="ong-editar"),
    path("ongs/<int:pk>/excluir/", views.excluir, name="ong-excluir"),
    path("ongs/<int:pk>/reenviar/", views.reenviar, name="ong-reenviar"),
    path("administracao/ongs/", views.fila, name="admin-ong-fila"),
    path("administracao/ongs/<int:pk>/analise/", views.analise, name="admin-ong-analise"),
]
