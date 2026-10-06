from rest_framework import serializers
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema_field

from campaigns.models import Campanha
from contributions.models import Contribuicao

from .base import Entrada


class ContribuicaoEntrada(Entrada):
    campanha_id = serializers.IntegerField(min_value=1)
    tipo = serializers.ChoiceField(choices=Campanha.Tipo.choices)
    valor = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    quantidade = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    observacao = serializers.CharField(max_length=500, required=False, allow_blank=True)


class ContribuicaoEdicao(ContribuicaoEntrada):
    campanha_id = None


class AvaliacaoEntrada(Entrada):
    acao = serializers.ChoiceField(choices=("aceitar", "confirmar", "recusar"))
    motivo = serializers.CharField(max_length=500, required=False, allow_blank=True)


class ContribuicaoResposta(serializers.ModelSerializer):
    campanha_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Contribuicao
        fields = ("id", "campanha_id", "tipo", "valor", "quantidade", "observacao", "status", "motivo_avaliacao", "avaliada_em", "criada_em", "atualizada_em")


class ContatoAutor(serializers.Serializer):
    nome = serializers.CharField()
    email = serializers.EmailField()


class ContribuicaoRecebida(ContribuicaoResposta):
    contato_autor = serializers.SerializerMethodField()

    @extend_schema_field(ContatoAutor)
    def get_contato_autor(self, obj):
        return {"nome": obj.autor.get_full_name() or obj.autor.username, "email": obj.autor.email}

    class Meta(ContribuicaoResposta.Meta):
        fields = (*ContribuicaoResposta.Meta.fields, "contato_autor")


ContribuicaoDetalhe = PolymorphicProxySerializer(
    component_name="ContribuicaoDetalhe",
    serializers=[ContribuicaoResposta, ContribuicaoRecebida],
    resource_type_field_name=None,
)
