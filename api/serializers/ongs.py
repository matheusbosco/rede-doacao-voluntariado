from rest_framework import serializers

from organizations.forms import OngForm
from organizations.models import Ong

from .base import Entrada, EntradaModelo


class Endereco(serializers.Serializer):
    cep = serializers.CharField()
    logradouro = serializers.CharField()
    numero = serializers.CharField()
    complemento = serializers.CharField()
    bairro = serializers.CharField()
    cidade = serializers.CharField()
    uf = serializers.CharField()


class OngPublica(serializers.ModelSerializer):
    endereco = Endereco(source="*")

    class Meta:
        model = Ong
        fields = ("id", "nome", "descricao", "causa", "email_contato", "telefone", "site", "endereco", "instrucoes_recebimento")


class OngPrivada(OngPublica):
    class Meta(OngPublica.Meta):
        fields = (*OngPublica.Meta.fields, "cnpj", "status", "motivo_analise", "criada_em", "atualizada_em")


class OngEntrada(EntradaModelo):
    cep = serializers.CharField(max_length=9)
    cnpj = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    uf = serializers.CharField(max_length=2)

    class Meta:
        model = Ong
        fields = OngForm.Meta.fields
        extra_kwargs = {"cnpj": {"validators": []}}


class AnaliseEntrada(Entrada):
    decisao = serializers.ChoiceField(choices=("aprovar", "recusar"))
    motivo = serializers.CharField(max_length=500, required=False, allow_blank=True)
