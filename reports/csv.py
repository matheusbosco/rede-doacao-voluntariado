import csv
from io import StringIO

from django.utils import timezone


def texto_seguro(valor):
    texto = str(valor)
    return "'" + texto if texto.startswith(("=", "+", "-", "@")) else texto


def gerar_csv(linhas, filtros, gerado_em):
    """Monta o arquivo inteiro antes de produzir uma resposta."""
    saida = StringIO(newline="")
    escritor = csv.writer(saida, delimiter=";")
    campos = ("titulo", "tipo", "unidade", "meta", "total_confirmado", "declaradas", "aceitas", "confirmadas", "recusadas", "canceladas")
    escritor.writerow((*campos, "inicio", "fim", "gerado_em"))
    for linha in linhas:
        valores = []
        for campo in campos:
            valor = linha[campo]
            if campo in ("titulo", "tipo", "unidade"):
                valor = texto_seguro(valor)
            elif campo in ("meta", "total_confirmado"):
                valor = format(valor, ".2f").replace(".", ",")
            valores.append(valor)
        escritor.writerow((*valores, filtros["inicio"].isoformat(), filtros["fim"].isoformat(), timezone.localtime(gerado_em).isoformat()))
    return ("\ufeff" + saida.getvalue()).encode("utf-8")
