import time

from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from .viacep import CepInvalido, CepNaoEncontrado, ViaCepIndisponivel, consultar_cep

LIMITE_POR_MINUTO = 10


def _erro(status: int, codigo: str, mensagem: str, **cabecalhos) -> JsonResponse:
    resposta = JsonResponse({"erro": {"codigo": codigo, "mensagem": mensagem}}, status=status)
    for nome, valor in cabecalhos.items():
        resposta[nome.replace("_", "-")] = valor
    return resposta


def _excedeu_limite(usuario_id: int) -> int | None:
    """Janela fixa de 1 minuto por usuário. Devolve os segundos para tentar de novo, ou None."""
    agora = int(time.time())
    janela = agora // 60
    chave = f"cep:{usuario_id}:{janela}"
    cache.add(chave, 0, timeout=70)
    if cache.incr(chave) > LIMITE_POR_MINUTO:
        return (janela + 1) * 60 - agora
    return None


@require_GET
def consulta_cep(request, cep):
    if not request.user.is_authenticated:
        return _erro(403, "autenticacao_necessaria", "Entre para consultar o CEP.")
    espera = _excedeu_limite(request.user.pk)
    if espera is not None:
        return _erro(429, "limite_excedido", "Muitas consultas. Tente novamente em instantes.",
                     Retry_After=str(espera))
    try:
        return JsonResponse(consultar_cep(cep))
    except CepInvalido as erro:
        return _erro(400, "validacao", str(erro))
    except CepNaoEncontrado:
        return _erro(404, "cep_nao_encontrado", "CEP não encontrado. Confira o número ou informe o endereço.")
    except ViaCepIndisponivel:
        return _erro(503, "endereco_indisponivel",
                     "Não foi possível consultar o CEP agora. Preencha o endereço manualmente.")


erro_cep_schema = inline_serializer(name="ErroCEPLegado", fields={
    "erro": inline_serializer(name="DetalheErroCEP", fields={
        "codigo": serializers.CharField(), "mensagem": serializers.CharField(),
    }),
})


class ConsultaCepAPIView(APIView):
    """Documenta o contrato existente, preservando corpo, status e limite do CEP."""
    http_method_names = ["get"]
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]
    throttle_classes = []

    @extend_schema(
        summary="Consultar CEP com sessão (10 consultas por minuto)", tags=["Endereços"],
        auth=[{"cookieAuth": []}],
        description="Contrato legado: erros de CEP mantêm codigo e mensagem, sem campos. Limite por usuário com Retry-After.",
        responses={200: inline_serializer(name="EnderecoCEP", fields={
            campo: serializers.CharField() for campo in ("cep", "logradouro", "bairro", "cidade", "uf", "origem")
        }), **{status: erro_cep_schema for status in (400, 403, 404, 429, 503)}},
        examples=[OpenApiExample("Endereço", value={"cep": "01001000", "logradouro": "Praça da Sé", "bairro": "Sé", "cidade": "São Paulo", "uf": "SP", "origem": "cache"}, response_only=True)],
    )
    def get(self, request, cep):
        if request.user.is_authenticated and request.query_params:
            raise ValidationError({campo: ["Parâmetro desconhecido."] for campo in request.query_params})
        return consulta_cep(request._request, cep)
