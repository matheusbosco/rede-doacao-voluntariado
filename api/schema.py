"""Documentação compartilhada dos erros, da paginação e da proteção CSRF."""
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers
from django.utils.text import slugify
from functools import lru_cache

from .examples import RESPOSTAS


class ErroDetalhe(serializers.Serializer):
    codigo = serializers.CharField()
    mensagem = serializers.CharField()
    campos = serializers.DictField(child=serializers.ListField(child=serializers.CharField()))


class ErroResposta(serializers.Serializer):
    erro = ErroDetalhe()


@lru_cache
def pagina_schema(resposta):
    return inline_serializer(name=f"Pagina{resposta.__name__}", fields={
        "count": serializers.IntegerField(),
        "next": serializers.URLField(allow_null=True),
        "previous": serializers.URLField(allow_null=True),
        "results": resposta(many=True),
    })


def documentar(resumo, tag, resposta=None, entrada=None, filtros=None, lista=False, status=200, exemplo=None, mime="application/json"):
    nome = resposta.__name__ if isinstance(resposta, type) else getattr(resposta, "component_name", None)
    sucesso = RESPOSTAS.get(nome)
    if lista:
        resposta = pagina_schema(resposta)
        sucesso = {"count": 1, "next": None, "previous": None, "results": [sucesso]}
    respostas = {(status, mime): resposta, **{codigo: ErroResposta for codigo in (400, 403, 404, 405, 409, 413, 429, 500)}}
    exemplos = [OpenApiExample("Erro de validação", value={"erro": {
        "codigo": "validacao", "mensagem": "Confira os campos informados.",
        "campos": {"campo": ["Campo desconhecido ou protegido."]},
    }}, response_only=True, status_codes=["400"])]
    if exemplo is not None:
        exemplos.append(OpenApiExample("Requisição", value=exemplo, request_only=True))
    if sucesso is not None:
        exemplos.append(OpenApiExample("Resposta de sucesso", value=sucesso, response_only=True, status_codes=[str(status)]))
    parametros = [filtros] if filtros else []
    if entrada is not None:
        parametros.append(OpenApiParameter("X-CSRFToken", str, OpenApiParameter.HEADER, required=True,
            description="Token obtido em auth/csrf/. Envie também o cookie csrftoken."))
    parametros.append(OpenApiParameter("Retry-After", int, OpenApiParameter.HEADER, response=[429],
        description="Segundos até permitir nova tentativa."))
    seguranca = None
    if entrada is not None:
        seguranca = [{"csrf": []}] if tag == "Autenticação" and status != 204 else [{"sessao": [], "csrf": []}]
    return extend_schema(summary=resumo, operation_id=slugify(resumo).replace("-", "_"), tags=[tag], request=entrada, responses=respostas, auth=seguranca,
        parameters=parametros, examples=exemplos,
        description="Erros seguem o envelope erro{codigo,mensagem,campos}. Campos e queries desconhecidos são rejeitados. Corpo JSON: até 64 KiB. Limites: leitura pública 60/min por IP, sessão 120/min, escrita 30/min por usuário; login 5/min por IP+username e cadastro 5/min por IP.")
