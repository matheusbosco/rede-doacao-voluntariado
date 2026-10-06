from rest_framework import serializers

from accounts.models import User

from .base import Entrada


class CadastroEntrada(Entrada):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)


class LoginEntrada(Entrada):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class UsuarioBasico(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name")


class MeuUsuario(UsuarioBasico):
    ong_id = serializers.IntegerField(source="ong.pk", read_only=True, default=None, allow_null=True)

    class Meta(UsuarioBasico.Meta):
        fields = (*UsuarioBasico.Meta.fields, "last_name", "email", "ong_id")


class CSRFResposta(serializers.Serializer):
    csrf_token = serializers.CharField()
