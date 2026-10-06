from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from campaigns.models import Campanha


class Contribuicao(models.Model):
    class Status(models.TextChoices):
        DECLARADA = "declarada", "Declarada"
        ACEITA = "aceita", "Aceita"
        CONFIRMADA = "confirmada", "Confirmada"
        RECUSADA = "recusada", "Recusada"
        CANCELADA = "cancelada", "Cancelada"

    campanha = models.ForeignKey(Campanha, on_delete=models.PROTECT, related_name="contribuicoes")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="contribuicoes")
    tipo = models.CharField(max_length=8, choices=Campanha.Tipo.choices)
    valor = models.DecimalField("valor (BRL)", max_digits=12, decimal_places=2, null=True, blank=True)
    quantidade = models.DecimalField("quantidade", max_digits=12, decimal_places=2, null=True, blank=True)
    observacao = models.CharField("observação", max_length=500, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DECLARADA)
    avaliada_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    avaliada_em = models.DateTimeField(null=True, blank=True)
    motivo_avaliacao = models.CharField(max_length=500, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["campanha", "status"], name="contrib_campanha_status_idx"),
            models.Index(fields=["autor", "criada_em"], name="contrib_autor_criada_idx"),
            models.Index(fields=["criada_em"], name="contrib_criada_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=(
                models.Q(tipo="dinheiro", valor__isnull=False, valor__gt=0, quantidade__isnull=True)
                | models.Q(tipo__in=["item", "horas"], quantidade__isnull=False, quantidade__gt=0, valor__isnull=True)
            ), name="contrib_medida_coerente"),
            models.CheckConstraint(condition=~models.Q(tipo="dinheiro", status="aceita"), name="contrib_dinheiro_sem_aceite"),
            models.CheckConstraint(condition=(
                models.Q(status="declarada", avaliada_por__isnull=True, avaliada_em__isnull=True)
                | models.Q(status__in=["aceita", "confirmada", "recusada"], avaliada_por__isnull=False, avaliada_em__isnull=False)
                | models.Q(status="cancelada")
            ), name="contrib_avaliacao_coerente"),
            models.CheckConstraint(condition=~models.Q(status="recusada") | ~models.Q(motivo_avaliacao=""), name="contrib_recusa_com_motivo"),
        ]

    def clean(self):
        erros = {}
        if self.campanha_id and self.tipo != self.campanha.tipo:
            erros["tipo"] = "O tipo deve ser o mesmo da campanha."
        campo = "valor" if self.tipo == Campanha.Tipo.DINHEIRO else "quantidade"
        medida = getattr(self, campo)
        outro = "quantidade" if campo == "valor" else "valor"
        if medida is None or medida <= 0:
            erros[campo] = "Informe um valor maior que zero."
        if getattr(self, outro) is not None:
            erros[outro] = "Este campo não se aplica ao tipo da campanha."
        if self.tipo == Campanha.Tipo.ITEM and medida is not None and medida % 1:
            erros["quantidade"] = "A quantidade de itens deve ser inteira."
        if erros:
            raise ValidationError(erros)

    @property
    def instrucao(self):
        return {
            "declarada": "Aguardando análise",
            "aceita": "Combine a realização com a ONG",
            "confirmada": "Confirmada",
            "recusada": "Recusada",
            "cancelada": "Cancelada",
        }[self.status]
