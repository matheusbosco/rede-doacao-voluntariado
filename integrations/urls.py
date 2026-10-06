from django.urls import path

from . import views

urlpatterns = [
    path("enderecos/cep/<str:cep>/", views.consulta_cep, name="consulta-cep"),
]
