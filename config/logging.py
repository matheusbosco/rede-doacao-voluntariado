import logging
import re

# URLs com usuário e senha (postgres://usuario:senha@host) e pares chave=valor sensíveis.
_URL_COM_CREDENCIAL = re.compile(r"([A-Za-z][A-Za-z0-9+.-]*://)[^\s/@:]+:[^\s/@]+@")
_PAR_SENSIVEL = re.compile(
    r"(?i)\b(password|passwd|senha|secret_key|secret|token|api_key|database_url)\b(\s*[=:]\s*)\S+"
)


def redigir(texto: str) -> str:
    texto = _URL_COM_CREDENCIAL.sub(r"\1[redigido]@", texto)
    return _PAR_SENSIVEL.sub(r"\1\2[redigido]", texto)


class FormatoSeguro(logging.Formatter):
    """Mantém mensagem e traceback (necessários para diagnosticar erros) e redige credenciais.

    O Django não registra corpo de requisição nem parâmetros de formulário; o que sobra de
    sensível são strings de conexão e pares chave=valor, que são substituídos por [redigido].
    """

    def __init__(self, fmt="%(levelname)s %(name)s %(message)s", **kwargs):
        super().__init__(fmt, **kwargs)

    def format(self, record):
        return redigir(super().format(record))
