from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.exceptions import MethodNotAllowed

from organizations.models import Ong

from api.pagination import Paginacao
from api.permissions import Autenticado, SessaoAuthentication
from api.serializers.base import validar
from api.throttles import Escrita, LeituraPublica, Usuario


class BaseView(APIView):
    http_method_names = ["get", "post", "patch", "delete"]
    protegida = False
    mutacao_anonima = False
    filtro = None
    throttle_classes = [LeituraPublica, Usuario, Escrita]

    def get_permissions(self):
        exige_sessao = self.protegida or (self.request.method != "GET" and not self.mutacao_anonima)
        return [Autenticado() if exige_sessao else AllowAny()]

    def initial(self, request, *args, **kwargs):
        if request.method.lower() not in self.http_method_names or not hasattr(self, request.method.lower()):
            raise MethodNotAllowed(request.method)
        # A sessão valida CSRF de usuários autenticados durante a autenticação.
        # Visitantes também devem validá-lo antes de login ou cadastro.
        if self.mutacao_anonima and request.method == "POST":
            SessaoAuthentication().enforce_csrf(request)
        super().initial(request, *args, **kwargs)
        self.filtros = validar(self.filtro, request.query_params.dict()) if self.filtro and request.method == "GET" else {}
        permitidos = set(self.filtro().fields) if self.filtro and request.method == "GET" else set()
        extras = set(request.query_params) - permitidos
        if extras:
            raise serializers.ValidationError({campo: ["Parâmetro desconhecido."] for campo in sorted(extras)})
        repetidos = [campo for campo in request.query_params if len(request.query_params.getlist(campo)) > 1]
        if repetidos:
            raise serializers.ValidationError({campo: ["Informe o parâmetro uma única vez."] for campo in repetidos})

    def check_throttles(self, request):
        if request.method in ("POST", "PATCH", "DELETE") and not isinstance(request.data, dict):
            raise serializers.ValidationError({"non_field_errors": ["Envie um objeto JSON."]})
        super().check_throttles(request)

    def paginar(self, consulta, serializer):
        pagina = Paginacao()
        objetos = pagina.paginate_queryset(consulta, self.request, view=self)
        return pagina.get_paginated_response(serializer(objetos, many=True).data)

    def minha_ong(self):
        return get_object_or_404(Ong, responsavel=self.request.user)

    def ordenar(self, consulta, padrao):
        return consulta.order_by(self.filtros.get("ordering", padrao), "pk")
