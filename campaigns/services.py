from django.db import transaction
from django.utils import timezone

from organizations.models import Ong

from .models import Campanha


class ConflitoEstado(ValueError):
    pass


def mudar_estado(campanha, acao, hoje=None):
    hoje = hoje if hoje is not None else timezone.localdate()
    with transaction.atomic():
        campanha = Campanha.objects.select_related("ong").select_for_update().get(pk=campanha.pk)
        transicoes = {
            "publicar": ([Campanha.Status.RASCUNHO], Campanha.Status.ATIVA),
            "pausar": ([Campanha.Status.ATIVA], Campanha.Status.PAUSADA),
            "reativar": ([Campanha.Status.PAUSADA], Campanha.Status.ATIVA),
            "encerrar": ([Campanha.Status.ATIVA, Campanha.Status.PAUSADA], Campanha.Status.ENCERRADA),
        }
        if acao not in transicoes or campanha.status not in transicoes[acao][0]:
            raise ConflitoEstado("Esta ação não é permitida no estado atual da campanha.")
        if acao in ("publicar", "reativar"):
            if campanha.ong.status != Ong.Status.APROVADA:
                raise ConflitoEstado("A ONG precisa de aprovação para publicar ou reativar campanhas.")
            if campanha.data_fim < hoje:
                raise ConflitoEstado("A data de fim não pode estar no passado.")
        campanha.status = transicoes[acao][1]
        campanha.save(update_fields=["status", "atualizada_em"])
    return campanha
