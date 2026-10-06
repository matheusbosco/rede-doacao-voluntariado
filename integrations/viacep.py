"""Cliente do ViaCEP: host fixo, timeout, validação rígida da resposta e cache de 24 h."""
import logging
import re
from datetime import timedelta

import requests
from django.utils import timezone

from .models import CacheCep
from .ufs import UFS

logger = logging.getLogger(__name__)

URL = "https://viacep.com.br/ws/{cep}/json/"
TIMEOUT = (2, 3)  # conexão, leitura (segundos)
VALIDADE_CACHE = timedelta(hours=24)


class CepInvalido(ValueError):
    pass


class CepNaoEncontrado(Exception):
    pass


class ViaCepIndisponivel(Exception):
    pass


def normalizar_cep(valor: str) -> str:
    """Aceita NNNNN-NNN ou 8 dígitos e devolve só os dígitos."""
    if not isinstance(valor, str) or not re.fullmatch(r"[0-9]{5}-?[0-9]{3}", valor.strip()):
        raise CepInvalido("Informe um CEP com 8 dígitos.")
    return valor.strip().replace("-", "")


def _texto(dados: dict, campo: str, *, obrigatorio: bool, maximo: int) -> str:
    valor = dados.get(campo)
    if not isinstance(valor, str):
        raise ViaCepIndisponivel(f"campo {campo} inválido")
    valor = valor.strip()
    if len(valor) > maximo:
        raise ViaCepIndisponivel(f"campo {campo} muito longo")
    if obrigatorio and not valor:
        raise ViaCepIndisponivel(f"campo {campo} ausente")
    return valor


def _buscar_externo(cep: str) -> dict:
    try:
        resposta = requests.get(
            URL.format(cep=cep), timeout=TIMEOUT, allow_redirects=False,
            headers={"Accept": "application/json"},
        )
    except requests.RequestException as erro:
        logger.warning("viacep: falha de rede (%s)", type(erro).__name__)
        raise ViaCepIndisponivel("falha de rede") from erro

    if resposta.status_code != 200:
        logger.warning("viacep: status %s", resposta.status_code)
        raise ViaCepIndisponivel(f"status {resposta.status_code}")

    try:
        dados = resposta.json()
    except ValueError as erro:
        logger.warning("viacep: resposta que não é JSON")
        raise ViaCepIndisponivel("resposta inválida") from erro
    if not isinstance(dados, dict):
        raise ViaCepIndisponivel("resposta inválida")

    if dados.get("erro") in (True, "true"):
        raise CepNaoEncontrado(cep)

    cep_resposta = _texto(dados, "cep", obrigatorio=True, maximo=9)
    if not re.fullmatch(r"[0-9]{5}-?[0-9]{3}", cep_resposta):
        raise ViaCepIndisponivel("CEP da resposta inválido")
    cep_resposta = cep_resposta.replace("-", "")
    uf = _texto(dados, "uf", obrigatorio=True, maximo=2).upper()
    if cep_resposta != cep or uf not in UFS:
        raise ViaCepIndisponivel("resposta divergente")
    return {
        "cep": cep,
        "logradouro": _texto(dados, "logradouro", obrigatorio=False, maximo=200),
        "bairro": _texto(dados, "bairro", obrigatorio=False, maximo=100),
        "cidade": _texto(dados, "localidade", obrigatorio=True, maximo=100),
        "uf": uf,
    }


def consultar_cep(valor: str) -> dict:
    """Devolve logradouro, bairro, cidade e UF do CEP, com a origem (cache ou viacep)."""
    cep = normalizar_cep(valor)
    em_cache = CacheCep.objects.filter(cep=cep, expira_em__gt=timezone.now()).first()
    if em_cache:
        return {
            "cep": cep, "logradouro": em_cache.logradouro, "bairro": em_cache.bairro,
            "cidade": em_cache.cidade, "uf": em_cache.uf, "origem": "cache",
        }

    dados = _buscar_externo(cep)
    CacheCep.objects.update_or_create(
        cep=cep, defaults={**{k: v for k, v in dados.items() if k != "cep"},
                           "expira_em": timezone.now() + VALIDADE_CACHE},
    )
    return {**dados, "origem": "viacep"}
