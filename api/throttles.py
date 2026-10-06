"""Limites independentes para leitura, escrita e autenticação."""
from hashlib import sha256

from rest_framework.throttling import SimpleRateThrottle


class LeituraPublica(SimpleRateThrottle):
    scope = "publica"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated or request.method != "GET":
            return None
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class Usuario(SimpleRateThrottle):
    scope = "usuario"

    def get_cache_key(self, request, view):
        if not request.user.is_authenticated:
            return None
        return self.cache_format % {"scope": self.scope, "ident": request.user.pk}


class Escrita(Usuario):
    scope = "escrita"

    def get_cache_key(self, request, view):
        return None if request.method == "GET" else super().get_cache_key(request, view)


class Login(SimpleRateThrottle):
    scope = "login"

    def get_cache_key(self, request, view):
        nome = str(request.data.get("username", "")).strip().casefold()
        ident = sha256(f"{self.get_ident(request)}:{nome}".encode()).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": ident}


class Cadastro(SimpleRateThrottle):
    scope = "cadastro"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
