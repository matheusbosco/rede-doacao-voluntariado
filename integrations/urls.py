from django.urls import path

from . import views

urlpatterns = [
    path("enderecos/cep/<str:cep>/", views.ConsultaCepAPIView.as_view(), name="consulta-cep"),
]
