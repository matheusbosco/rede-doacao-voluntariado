from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db import models
from django.utils import timezone

from organizations.models import Ong


class Campanha(models.Model):
    class Tipo(models.TextChoices):
        DINHEIRO = "dinheiro", "Dinheiro"
        ITEM = "item", "Item"
        HORAS = "horas", "Horas"

    class Status(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        ATIVA = "ativa", "Ativa"
        PAUSADA = "pausada", "Pausada"
        ENCERRADA = "encerrada", "Encerrada"

    ong = models.ForeignKey(Ong, on_delete=models.PROTECT, related_name="campanhas")
    titulo = models.CharField("título", max_length=150)
    descricao = models.TextField("descrição", validators=[MaxLengthValidator(5000)])
    tipo = models.CharField("tipo", max_length=8, choices=Tipo.choices)
    unidade = models.CharField("unidade", max_length=30)
    meta = models.DecimalField("meta", max_digits=12, decimal_places=2)
    data_inicio = models.DateField("data de início")
    data_fim = models.DateField("data de fim")
    status = models.CharField(max_length=9, choices=Status.choices, default=Status.RASCUNHO)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["ong", "status"], name="campanha_ong_status_idx"),
            models.Index(fields=["tipo", "status"], name="campanha_tipo_status_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(meta__gt=0), name="campanha_meta_positiva"),
            models.CheckConstraint(
                condition=models.Q(data_fim__gte=models.F("data_inicio")),
                name="campanha_datas_coerentes",
            ),
        ]

    def clean(self):
        erros = {}
        if self.meta is not None and self.meta <= 0:
            erros["meta"] = "A meta deve ser maior que zero."
        if self.tipo == self.Tipo.ITEM and self.meta is not None and self.meta % 1:
            erros["meta"] = "A meta de itens deve ser inteira."
        unidades = {self.Tipo.DINHEIRO: "BRL", self.Tipo.HORAS: "hora"}
        if self.tipo in unidades and self.unidade != unidades[self.tipo]:
            erros["unidade"] = f"Para este tipo, a unidade deve ser {unidades[self.tipo]}."
        if self.data_inicio and self.data_fim and self.data_fim < self.data_inicio:
            erros["data_fim"] = "A data de fim não pode ser anterior à data de início."
        if self.pk and self.contribuicoes.exists():
            original = Campanha.objects.only("tipo", "unidade").get(pk=self.pk)
            for campo in ("tipo", "unidade"):
                if getattr(self, campo) != getattr(original, campo):
                    erros[campo] = "Tipo e unidade não podem mudar após uma contribuição."
        if erros:
            raise ValidationError(erros)

    @property
    def total_confirmado(self):
        from .totais import anotar_totais

        if "_total_confirmado" in self.__dict__:
            return self._total_confirmado
        return anotar_totais(Campanha.objects.filter(pk=self.pk)).values_list("total_confirmado", flat=True).get()

    @total_confirmado.setter
    def total_confirmado(self, valor):
        # A anotação da listagem evita uma consulta por campanha.
        self._total_confirmado = valor

    @property
    def percentual_meta(self):
        return self.total_confirmado / self.meta * 100

    @property
    def disponivel(self):
        hoje = timezone.localdate()
        return (
            self.status == self.Status.ATIVA and self.ong.status == Ong.Status.APROVADA
            and self.data_inicio <= hoje <= self.data_fim
        )

    @property
    def motivo_indisponibilidade(self):
        if self.ong.status != Ong.Status.APROVADA:
            return "ONG não aprovada"
        if self.status == self.Status.RASCUNHO:
            return "Rascunho"
        if self.status == self.Status.PAUSADA:
            return "Pausada"
        if self.status == self.Status.ENCERRADA:
            return "Encerrada"
        if not self.data_inicio <= timezone.localdate() <= self.data_fim:
            return "Fora do prazo"
        return ""

    def __str__(self):
        return self.titulo
