from datetime import datetime, time, timedelta, timezone as fuso
from zoneinfo import ZoneInfo

from django.db.models import Count, Q

from campaigns.totais import anotar_totais
from contributions.models import Contribuicao


def consultar_relatorio(ong, filtros):
    """Usa a criação em São Paulo e o estado atual, sem dados de autores."""
    sao_paulo = ZoneInfo("America/Sao_Paulo")
    inicio = datetime.combine(filtros["inicio"], time.min, sao_paulo).astimezone(fuso.utc)
    fim = datetime.combine(filtros["fim"] + timedelta(days=1), time.min, sao_paulo).astimezone(fuso.utc)
    campanhas = ong.campanhas.all()
    if filtros.get("campanha"):
        campanhas = campanhas.filter(pk=filtros["campanha"].pk)
    if filtros.get("tipo"):
        campanhas = campanhas.filter(tipo=filtros["tipo"])
    periodo = Q(contribuicoes__criada_em__gte=inicio, contribuicoes__criada_em__lt=fim)
    campanhas = anotar_totais(campanhas, periodo)
    contagens = {
        f"{status}s": Count("contribuicoes", filter=periodo & Q(contribuicoes__status=status))
        for status in Contribuicao.Status.values
    }
    return list(campanhas.annotate(**contagens).order_by("titulo", "pk").values(
        "id", "titulo", "tipo", "unidade", "meta", "total_confirmado", *contagens,
    ))
