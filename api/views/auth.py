from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from accounts.forms import CadastroForm
from api.exceptions import ErroAPI
from api.schema import documentar
from api.serializers.auth import CadastroEntrada, CSRFResposta, LoginEntrada, MeuUsuario, UsuarioBasico
from api.serializers.base import Entrada, validar
from api.throttles import Cadastro, Login

from .base import BaseView


class CSRFView(BaseView):
    @documentar("Obter cookie e token CSRF", "Autenticação", CSRFResposta)
    def get(self, request):
        return Response({"csrf_token": get_token(request)})


class CadastroView(BaseView):
    mutacao_anonima = True
    throttle_classes = [*BaseView.throttle_classes, Cadastro]

    @documentar("Cadastrar usuário sem iniciar sessão", "Autenticação", UsuarioBasico, CadastroEntrada, status=201,
        exemplo={"username": "maria", "email": "maria@example.org", "first_name": "Maria", "password": "Frase segura! 2026", "password_confirm": "Frase segura! 2026"})
    def post(self, request):
        dados = validar(CadastroEntrada, request.data)
        dados["password1"] = dados.pop("password")
        dados["password2"] = dados.pop("password_confirm")
        form = CadastroForm(dados)
        if not form.is_valid():
            nomes = {"password1": "password", "password2": "password_confirm"}
            raise ValidationError({nomes.get(campo, campo): list(erros) for campo, erros in form.errors.items()})
        return Response(UsuarioBasico(form.save()).data, status=201)


class LoginView(BaseView):
    mutacao_anonima = True
    throttle_classes = [*BaseView.throttle_classes, Login]

    @documentar("Entrar com sessão Django", "Autenticação", UsuarioBasico, LoginEntrada,
        exemplo={"username": "maria", "password": "Frase segura! 2026"})
    def post(self, request):
        dados = validar(LoginEntrada, request.data)
        usuario = authenticate(request=request, **dados)
        if usuario is None:
            raise ErroAPI("credenciais_invalidas", "Usuário ou senha inválidos.")
        login(request, usuario)
        return Response(UsuarioBasico(usuario).data)


class LogoutView(BaseView):
    protegida = True

    @documentar("Encerrar sessão", "Autenticação", entrada=Entrada, status=204, exemplo={})
    def post(self, request):
        validar(Entrada, request.data)
        logout(request)
        return Response(status=204)


class MeView(BaseView):
    protegida = True

    @documentar("Consultar meu perfil", "Autenticação", MeuUsuario)
    def get(self, request):
        return Response(MeuUsuario(request.user).data)
