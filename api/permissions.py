"""Autenticação por sessão e proteção CSRF, inclusive para visitantes."""
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import CSRFCheck, SessionAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from .exceptions import ErroAPI


class SessaoAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        verificacao = CSRFCheck(lambda requisicao: None)
        verificacao.process_request(request)
        motivo = verificacao.process_view(request, None, (), {})
        if motivo:
            raise ErroAPI("csrf_invalido", "Token CSRF ausente ou inválido.", 403)


class Autenticado(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            raise NotAuthenticated()
        return True


class Equipe(Autenticado):
    def has_permission(self, request, view):
        super().has_permission(request, view)
        if not request.user.is_staff:
            raise PermissionDenied()
        return True


class SegurancaSessao(OpenApiAuthenticationExtension):
    target_class = "api.permissions.SessaoAuthentication"
    name = ["sessao", "csrf"]

    def get_security_requirement(self, auto_schema):
        if auto_schema.method in ("POST", "PATCH", "DELETE"):
            if auto_schema.view.mutacao_anonima:
                return {"csrf": []}
            return {"sessao": [], "csrf": []}
        return {"sessao": []}

    def get_security_definition(self, auto_schema):
        return [
            {"type": "apiKey", "in": "cookie", "name": "sessionid"},
            {"type": "apiKey", "in": "header", "name": "X-CSRFToken",
             "description": "Obtenha o cookie e o token em /api/v1/auth/csrf/. Obrigatório nas mutações."},
        ]
