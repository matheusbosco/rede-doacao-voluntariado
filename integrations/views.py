import time

from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_GET

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
