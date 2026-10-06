from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from campaigns.models import Campanha
from campaigns.services import ConflitoEstado
from organizations.models import Ong

from .models import Contribuicao


def preencher_dados(contribuicao, dados):
    """Somente a medida, o tipo compatível e a observação podem vir do cliente."""
    if dados.get("tipo", contribuicao.tipo) != contribuicao.tipo:
        raise ValidationError("O tipo deve ser o mesmo da campanha.")
    for campo in ("valor", "quantidade", "observacao"):
        if campo in dados:
            valor = contribuicao._meta.get_field(campo).clean(dados[campo], contribuicao)
            setattr(contribuicao, campo, valor)
    contribuicao.full_clean()


def criar_contribuicao(autor, campanha, dados):
    if not autor.is_authenticated:
        raise PermissionDenied("Entre para contribuir.")
    with transaction.atomic():
        campanha = Campanha.objects.select_related("ong").select_for_update().get(pk=campanha.pk)
        if campanha.ong.responsavel_id == autor.pk:
            raise PermissionDenied("O responsável não pode contribuir para sua própria ONG.")
        if not campanha.disponivel:
            raise ValidationError("Esta campanha não está disponível para novas contribuições.")
        contribuicao = Contribuicao(campanha=campanha, autor=autor, tipo=campanha.tipo)
        preencher_dados(contribuicao, dados)
        contribuicao.save()
    return contribuicao


def editar_contribuicao(contribuicao_id, autor, dados):
    with transaction.atomic():
        contribuicao = Contribuicao.objects.select_related("campanha").select_for_update(of=("self",)).get(pk=contribuicao_id)
        if not autor.is_authenticated or contribuicao.autor_id != autor.pk:
            raise PermissionDenied("Somente o autor pode editar a contribuição.")
        if contribuicao.status != Contribuicao.Status.DECLARADA:
            raise ConflitoEstado("Somente contribuições declaradas podem ser editadas.")
        preencher_dados(contribuicao, dados)
        contribuicao.save(update_fields=["valor", "quantidade", "observacao", "atualizada_em"])
    return contribuicao


def cancelar_contribuicao(contribuicao_id, autor):
    with transaction.atomic():
        contribuicao = Contribuicao.objects.select_for_update().get(pk=contribuicao_id)
        if not autor.is_authenticated or contribuicao.autor_id != autor.pk:
            raise PermissionDenied("Somente o autor pode cancelar a contribuição.")
        if contribuicao.status not in (Contribuicao.Status.DECLARADA, Contribuicao.Status.ACEITA):
            raise ConflitoEstado("Esta contribuição não pode ser cancelada no estado atual.")
        contribuicao.status = Contribuicao.Status.CANCELADA
        contribuicao.save(update_fields=["status", "atualizada_em"])
    return contribuicao


def avaliar_contribuicao(contribuicao_id, responsavel, acao, motivo=""):
    with transaction.atomic():
        contribuicao = Contribuicao.objects.select_related("campanha__ong").select_for_update(of=("self",)).get(pk=contribuicao_id)
        ong = contribuicao.campanha.ong
        if not responsavel.is_authenticated or ong.responsavel_id != responsavel.pk:
            raise PermissionDenied("Somente o responsável da ONG pode analisar a contribuição.")
        if ong.status != Ong.Status.APROVADA:
            raise ValidationError("A ONG precisa de aprovação para analisar contribuições.")
        dinheiro = contribuicao.tipo == Campanha.Tipo.DINHEIRO
        transicoes = {
            "aceitar": (["declarada"] if not dinheiro else [], "aceita"),
            "confirmar": (["declarada"] if dinheiro else ["aceita"], "confirmada"),
            "recusar": (["declarada", "aceita"], "recusada"),
        }
        if acao not in transicoes or contribuicao.status not in transicoes[acao][0]:
            raise ConflitoEstado("Esta ação não é permitida no estado atual da contribuição.")
        motivo = motivo.strip()
        if acao == "recusar" and not motivo:
            raise ValidationError("Informe o motivo da recusa.")
        if len(motivo) > 500:
            raise ValidationError("O motivo deve ter no máximo 500 caracteres.")
        contribuicao.status = transicoes[acao][1]
        contribuicao.avaliada_por = responsavel
        contribuicao.avaliada_em = timezone.now()
        contribuicao.motivo_avaliacao = motivo
        contribuicao.full_clean()
        contribuicao.save(update_fields=["status", "avaliada_por", "avaliada_em", "motivo_avaliacao", "atualizada_em"])
    return contribuicao
