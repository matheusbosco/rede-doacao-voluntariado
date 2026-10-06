from rest_framework import serializers

from organizations.models import Postagem

from .base import EntradaModelo


class PostagemResposta(serializers.ModelSerializer):
    ong_id = serializers.IntegerField(read_only=True)
    campanha_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = Postagem
        fields = ("id", "ong_id", "campanha_id", "titulo", "conteudo", "publicada", "criada_em", "atualizada_em")


class PostagemEntrada(EntradaModelo):
    campanha_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)

    class Meta:
        model = Postagem
        fields = ("titulo", "conteudo", "campanha_id", "publicada")
