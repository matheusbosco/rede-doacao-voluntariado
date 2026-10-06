"""Entrada estrita e adaptação dos formulários já usados pelas telas."""
from django.forms.models import model_to_dict
from rest_framework import serializers


class Estrito:
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError({"non_field_errors": ["Envie um objeto JSON."]})
        extras = set(data) - {nome for nome, campo in self.fields.items() if not campo.read_only}
        if extras:
            raise serializers.ValidationError({nome: ["Campo desconhecido ou protegido."] for nome in sorted(extras)})
        return super().to_internal_value(data)


class Entrada(Estrito, serializers.Serializer):
    pass


class EntradaModelo(Estrito, serializers.ModelSerializer):
    # Os formulários existentes fazem a validação única do modelo e das regras.
    def get_validators(self):
        return []


def validar(serializer, dados, parcial=False):
    entrada = serializer(data=dados, partial=parcial)
    entrada.is_valid(raise_exception=True)
    return entrada.validated_data


def formulario(classe, dados, instancia=None, **kwargs):
    if instancia is not None and instancia.pk:
        iniciais = model_to_dict(instancia, fields=classe.Meta.fields)
        dados = {**iniciais, **dados}
    form = classe(data=dados, instance=instancia, **kwargs) if instancia is not None else classe(data=dados, **kwargs)
    if not form.is_valid():
        raise serializers.ValidationError({campo: list(erros) for campo, erros in form.errors.items()})
    return form
