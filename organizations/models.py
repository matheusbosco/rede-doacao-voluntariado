from django.conf import settings
from django.core.validators import MaxLengthValidator, RegexValidator, URLValidator
from django.db import models

from integrations.ufs import UFS


class Ong(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        APROVADA = "aprovada", "Aprovada"
        RECUSADA = "recusada", "Recusada"

    responsavel = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ong"
    )
    nome = models.CharField("nome", max_length=150)
    descricao = models.TextField("descrição", validators=[MaxLengthValidator(5000)])
    causa = models.CharField("causa", max_length=80)
    cnpj = models.CharField(
        "CNPJ", max_length=14, unique=True, null=True, blank=True,
        validators=[RegexValidator(r"\A[0-9]{14}\Z", "Informe um CNPJ com 14 dígitos.")],
    )
    email_contato = models.EmailField("e-mail de contato")
    telefone = models.CharField("telefone", max_length=20, blank=True)
    site = models.URLField("site", blank=True, validators=[URLValidator(schemes=["http", "https"])])
    cep = models.CharField(
        "CEP", max_length=8,
        validators=[RegexValidator(r"\A[0-9]{8}\Z", "Informe um CEP com 8 dígitos.")],
    )
    logradouro = models.CharField("logradouro", max_length=200)
    numero = models.CharField("número", max_length=20)
    complemento = models.CharField("complemento", max_length=120, blank=True)
    bairro = models.CharField("bairro", max_length=100)
    cidade = models.CharField("cidade", max_length=100)
    uf = models.CharField("UF", max_length=2, choices=[(uf, uf) for uf in UFS])
    instrucoes_recebimento = models.TextField(
        "instruções de recebimento", validators=[MaxLengthValidator(2000)]
    )
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDENTE)
    analisada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    analisada_em = models.DateTimeField(null=True, blank=True)
    motivo_analise = models.CharField(max_length=500, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["uf", "cidade", "bairro"], name="ong_localizacao_idx"),
            models.Index(fields=["status", "nome"], name="ong_status_nome_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(status="pendente", analisada_por__isnull=True, analisada_em__isnull=True)
                    | models.Q(status__in=["aprovada", "recusada"],
                               analisada_por__isnull=False, analisada_em__isnull=False)
                ),
                name="ong_analise_coerente",
            ),
            models.CheckConstraint(
                condition=~models.Q(status="recusada") | ~models.Q(motivo_analise=""),
                name="ong_recusa_com_motivo",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.cnpj:
            self.cnpj = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome
