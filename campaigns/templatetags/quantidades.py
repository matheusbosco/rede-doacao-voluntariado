from decimal import Decimal

from django import template
from django.utils.formats import number_format


register = template.Library()


@register.filter
def medida(valor, campanha):
    """Formata a medida para a tela; aceita campanha ou linha de relatório."""
    tipo = campanha["tipo"] if isinstance(campanha, dict) else campanha.tipo
    unidade = campanha["unidade"] if isinstance(campanha, dict) else campanha.unidade
    valor = Decimal(valor)
    if tipo == "dinheiro":
        return f"R$ {number_format(valor, decimal_pos=2, use_l10n=True)}"
    if tipo == "horas":
        numero = number_format(valor, decimal_pos=2, use_l10n=True).rstrip("0").rstrip(",")
        return f"{numero} {'hora' if valor == 1 else 'horas'}"
    if valor != 1:
        # A unidade é informada no singular no formulário de campanha.
        palavras = unidade.split()
        especiais = {"pão": "pães", "mão": "mãos", "cão": "cães", "grão": "grãos", "lápis": "lápis", "fóssil": "fósseis"}
        for indice, palavra in enumerate(palavras):
            if palavra in ("de", "do", "da", "para", "com"):
                break
            if palavra in especiais:
                palavra = especiais[palavra]
            elif palavra.endswith("ão"):
                palavra = palavra[:-2] + "ões"
            elif palavra.endswith("m"):
                palavra = palavra[:-1] + "ns"
            elif palavra.endswith("el"):
                palavra = palavra[:-2] + "éis"
            elif palavra.endswith("ol"):
                palavra = palavra[:-2] + "óis"
            elif palavra.endswith("l"):
                palavra = palavra[:-1] + ("s" if palavra.endswith("il") else "is")
            elif palavra.endswith(("r", "z")):
                palavra += "es"
            elif not palavra.endswith("s"):
                palavra += "s"
            palavras[indice] = palavra
        unidade = " ".join(palavras)
    return f"{number_format(valor, decimal_pos=0, use_l10n=True)} {unidade}"
