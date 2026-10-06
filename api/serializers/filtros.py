from rest_framework import serializers

from campaigns.models import Campanha
from contributions.models import Contribuicao
from integrations.ufs import UFS
from organizations.models import Ong

from .base import Entrada


class ListaFiltro(Entrada):
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100)


class BuscaFiltro(ListaFiltro):
    q = serializers.CharField(required=False, allow_blank=True, max_length=100)


class OngFiltro(BuscaFiltro):
    cidade = serializers.CharField(required=False, max_length=100, allow_blank=True)
    bairro = serializers.CharField(required=False, max_length=100, allow_blank=True)
    uf = serializers.ChoiceField(required=False, choices=UFS)
    ordering = serializers.ChoiceField(required=False, choices=("nome", "-atualizada_em"))


class AdminOngFiltro(ListaFiltro):
    status = serializers.ChoiceField(required=False, choices=Ong.Status.choices, default="pendente")
    ordering = serializers.ChoiceField(required=False, choices=("criada_em", "nome"))


class CampanhaFiltro(OngFiltro):
    ong_id = serializers.IntegerField(required=False, min_value=1)
    tipo = serializers.ChoiceField(required=False, choices=Campanha.Tipo.choices)
    status = serializers.ChoiceField(required=False, choices=("ativa", "pausada", "encerrada"))
    disponivel = serializers.BooleanField(required=False)
    ordering = serializers.ChoiceField(required=False, choices=("-criada_em", "data_fim", "titulo"))


class PainelCampanhaFiltro(CampanhaFiltro):
    status = serializers.ChoiceField(required=False, choices=Campanha.Status.choices)


class PostagemFiltro(BuscaFiltro):
    ong_id = serializers.IntegerField(required=False, min_value=1)
    campanha_id = serializers.IntegerField(required=False, min_value=1)
    ordering = serializers.ChoiceField(required=False, choices=("-criada_em", "titulo"))


class PainelPostagemFiltro(PostagemFiltro):
    publicada = serializers.BooleanField(required=False)


class ContribuicaoFiltro(ListaFiltro):
    campanha_id = serializers.IntegerField(required=False, min_value=1)
    tipo = serializers.ChoiceField(required=False, choices=Campanha.Tipo.choices)
    status = serializers.ChoiceField(required=False, choices=Contribuicao.Status.choices)
    ordering = serializers.ChoiceField(required=False, choices=("-criada_em", "criada_em"))


class RelatorioFiltro(Entrada):
    inicio = serializers.DateField()
    fim = serializers.DateField()
    campanha_id = serializers.IntegerField(required=False, min_value=1)
    tipo = serializers.ChoiceField(required=False, choices=Campanha.Tipo.choices)
