from django.db import transaction
from django.utils import timezone

from .models import Ong


class ConflitoEstado(ValueError):
    pass


def analisar_ong(ong_id, admin, decisao, motivo=""):
    if not admin.is_staff:
        raise ValueError("Somente a equipe pode analisar ONGs.")
    with transaction.atomic():
        ong = Ong.objects.select_for_update().get(pk=ong_id)
        if ong.status != Ong.Status.PENDENTE:
            raise ConflitoEstado("ONG já analisada")
        if decisao not in ("aprovar", "recusar"):
            raise ValueError("Escolha aprovar ou recusar.")
        motivo = motivo.strip()
        if decisao == "recusar" and not motivo:
            raise ValueError("Informe o motivo da recusa.")
        if len(motivo) > 500:
            raise ValueError("O motivo deve ter no máximo 500 caracteres.")
        ong.status = Ong.Status.APROVADA if decisao == "aprovar" else Ong.Status.RECUSADA
        ong.analisada_por = admin
        ong.analisada_em = timezone.now()
        ong.motivo_analise = motivo
        ong.save()
    return ong


def reenviar_ong(ong):
    with transaction.atomic():
        ong = Ong.objects.select_for_update().get(pk=ong.pk)
        if ong.status != Ong.Status.RECUSADA:
            raise ConflitoEstado("Somente ONGs recusadas podem ser reenviadas.")
        ong.status = Ong.Status.PENDENTE
        ong.analisada_por = None
        ong.analisada_em = None
        ong.motivo_analise = ""
        ong.save()
    return ong
