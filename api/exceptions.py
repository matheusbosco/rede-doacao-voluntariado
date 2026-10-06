"""Traduz erros da API sem expor detalhes internos."""
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.db.models.deletion import ProtectedError
from django.http import Http404
from rest_framework import exceptions
from rest_framework.response import Response

from campaigns.services import ConflitoEstado as ConflitoCampanha
from organizations.services import ConflitoEstado as ConflitoOng
from contributions.services import AcaoIncompativel


class ErroAPI(exceptions.APIException):
    def __init__(self, codigo, mensagem, status=400):
        self.status_code = status
        self.codigo = codigo
        super().__init__(mensagem)


def envelope(codigo, mensagem, campos=None):
    return {"erro": {"codigo": codigo, "mensagem": mensagem, "campos": campos or {}}}


def tratar_excecao(erro, contexto):
    from rest_framework.views import exception_handler as drf_handler
    campos = {}
    resposta = drf_handler(erro, contexto)
    if isinstance(erro, ErroAPI):
        codigo, mensagem, status = erro.codigo, str(erro.detail), erro.status_code
    elif isinstance(erro, AcaoIncompativel):
        codigo, mensagem, status = "validacao", "Confira os campos informados.", 400
        campos = {"acao": [str(erro)]}
    elif isinstance(erro, (ConflitoCampanha, ConflitoOng)):
        codigo, mensagem, status = "conflito_estado", str(erro), 409
    elif isinstance(erro, ProtectedError):
        codigo, mensagem, status = "possui_dependentes", "Há dependências vinculadas a este recurso.", 409
    elif isinstance(erro, (exceptions.ValidationError, DjangoValidationError)):
        detalhes = erro.detail if isinstance(erro, exceptions.ValidationError) else (
            erro.message_dict if hasattr(erro, "message_dict") else erro.messages
        )
        campos = detalhes if isinstance(detalhes, dict) else {"non_field_errors": detalhes}
        campos = {campo: valor if isinstance(valor, list) else [valor] for campo, valor in campos.items()}
        codigo, mensagem, status = "validacao", "Confira os campos informados.", 400
    elif isinstance(erro, exceptions.NotAuthenticated):
        codigo, mensagem, status = "autenticacao_necessaria", "Entre para acessar este recurso.", 403
    elif isinstance(erro, (exceptions.PermissionDenied, PermissionDenied)):
        codigo, mensagem, status = "proibido", "Você não tem permissão para esta ação.", 403
    elif isinstance(erro, (exceptions.NotFound, Http404)):
        codigo, mensagem, status = "nao_encontrado", "Recurso não encontrado.", 404
    elif isinstance(erro, exceptions.MethodNotAllowed):
        codigo, mensagem, status = "metodo_nao_permitido", "Método não permitido.", 405
    elif isinstance(erro, exceptions.Throttled):
        codigo, mensagem, status = "limite_excedido", "Muitas solicitações. Tente novamente em instantes.", 429
    elif isinstance(erro, (exceptions.ParseError, exceptions.UnsupportedMediaType)):
        codigo, mensagem, status = "validacao", "Envie um objeto JSON válido.", erro.status_code
    else:
        codigo, mensagem, status = "erro_interno", "Não foi possível concluir a solicitação.", 500
    if resposta is None:
        resposta = Response(status=status)
    resposta.status_code = status
    resposta.data = envelope(codigo, mensagem, campos)
    return resposta
