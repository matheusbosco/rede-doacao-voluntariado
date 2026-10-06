from django.urls import path

from .views import relatorio

urlpatterns = [
    path("painel/relatorios/", relatorio, name="relatorio-painel"),
    path("painel/relatorios/exportar/", relatorio, {"formato": "csv"}, name="relatorio-exportar"),
    path("painel/relatorios/imprimir/", relatorio, {"formato": "imprimir"}, name="relatorio-imprimir"),
]
