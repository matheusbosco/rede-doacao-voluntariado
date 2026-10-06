from rest_framework import serializers

from campaigns.forms import CampanhaForm
from campaigns.models import Campanha

from .base import Entrada, EntradaModelo


class CampanhaResposta(serializers.ModelSerializer):
    ong_id = serializers.IntegerField(read_only=True)
    total_confirmado = serializers.DecimalField(max_digits=24, decimal_places=2, read_only=True)
    percentual_meta = serializers.DecimalField(max_digits=30, decimal_places=2, read_only=True)
    disponivel = serializers.BooleanField(read_only=True)

    class Meta:
        model = Campanha
        fields = ("id", "ong_id", "titulo", "descricao", "tipo", "unidade", "meta", "data_inicio", "data_fim", "status", "total_confirmado", "percentual_meta", "disponivel", "criada_em", "atualizada_em")


class CampanhaEntrada(EntradaModelo):
    class Meta:
        model = Campanha
        fields = CampanhaForm.Meta.fields


class EstadoEntrada(Entrada):
    acao = serializers.ChoiceField(choices=("publicar", "pausar", "reativar", "encerrar"))
