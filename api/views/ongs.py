from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from accounts.models import User
from organizations.forms import OngForm
from organizations.models import Ong
from organizations.services import ConflitoEstado, analisar_ong, reenviar_ong
from api.exceptions import ErroAPI
from api.permissions import Equipe
from api.schema import documentar
from api.serializers.base import Entrada, formulario, validar
from api.serializers.filtros import AdminOngFiltro, OngFiltro
from api.serializers.ongs import AnaliseEntrada, OngEntrada, OngPrivada, OngPublica

from .base import BaseView


class OngsView(BaseView):
    filtro = OngFiltro

    @documentar("Listar ONGs aprovadas", "ONGs", OngPublica, filtros=OngFiltro, lista=True)
    def get(self, request):
        consulta = Ong.objects.filter(status="aprovada")
        if busca := self.filtros.get("q"):
            consulta = consulta.filter(Q(nome__icontains=busca) | Q(descricao__icontains=busca) | Q(causa__icontains=busca))
        for campo in ("cidade", "bairro", "uf"):
            if valor := self.filtros.get(campo):
                consulta = consulta.filter(**{campo if campo == "uf" else f"{campo}__icontains": valor})
        return self.paginar(self.ordenar(consulta, "nome"), OngPublica)

    @documentar("Cadastrar minha ONG para análise", "ONGs", OngPrivada, OngEntrada, status=201,
        exemplo={"nome": "Amigos", "descricao": "Apoio social", "causa": "Educação", "email_contato": "contato@example.org", "cep": "01001000", "logradouro": "Praça da Sé", "numero": "10", "bairro": "Sé", "cidade": "São Paulo", "uf": "SP", "instrucoes_recebimento": "Agende a entrega."})
    def post(self, request):
        dados = validar(OngEntrada, request.data)
        with transaction.atomic():
            User.objects.select_for_update().get(pk=request.user.pk)
            if Ong.objects.filter(responsavel=request.user).exists():
                raise ErroAPI("possui_dependentes", "Você já possui uma ONG.", 409)
            ong = formulario(OngForm, dados, Ong(responsavel=request.user)).save()
        return Response(OngPrivada(ong).data, status=201)


class OngView(BaseView):
    @documentar("Consultar ONG aprovada", "ONGs", OngPublica)
    def get(self, request, pk):
        return Response(OngPublica(get_object_or_404(Ong, pk=pk, status="aprovada")).data)

    @documentar("Editar minha ONG", "ONGs", OngPrivada, OngEntrada, exemplo={"nome": "Novo nome"})
    def patch(self, request, pk):
        dados = validar(OngEntrada, request.data, parcial=True)
        with transaction.atomic():
            ong = get_object_or_404(Ong.objects.select_for_update(), pk=pk, responsavel=request.user)
            ong = formulario(OngForm, dados, ong).save()
        return Response(OngPrivada(ong).data)

    @documentar("Excluir minha ONG sem dependências", "ONGs", entrada=Entrada, status=204, exemplo={})
    def delete(self, request, pk):
        validar(Entrada, request.data)
        get_object_or_404(Ong, pk=pk, responsavel=request.user).delete()
        return Response(status=204)


class PainelOngView(BaseView):
    protegida = True

    @documentar("Consultar dados privados da minha ONG", "ONGs", OngPrivada)
    def get(self, request):
        return Response(OngPrivada(self.minha_ong()).data)


class ReenviarView(BaseView):
    protegida = True

    @documentar("Reenviar ONG recusada para análise", "ONGs", OngPrivada, Entrada, exemplo={})
    def post(self, request, pk):
        validar(Entrada, request.data)
        ong = get_object_or_404(Ong, pk=pk, responsavel=request.user)
        return Response(OngPrivada(reenviar_ong(ong)).data)


class AdminOngsView(BaseView):
    filtro = AdminOngFiltro

    def get_permissions(self):
        return [Equipe()]

    @documentar("Listar ONGs para análise da equipe", "Administração", OngPrivada, filtros=AdminOngFiltro, lista=True)
    def get(self, request):
        consulta = Ong.objects.filter(status=self.filtros["status"])
        return self.paginar(self.ordenar(consulta, "criada_em"), OngPrivada)


class AnaliseView(AdminOngsView):
    http_method_names = ["post"]
    filtro = None

    @documentar("Aprovar ou recusar ONG pendente", "Administração", OngPrivada, AnaliseEntrada,
        exemplo={"decisao": "recusar", "motivo": "Confira o endereço."})
    def post(self, request, pk):
        dados = validar(AnaliseEntrada, request.data)
        get_object_or_404(Ong, pk=pk)
        try:
            ong = analisar_ong(pk, request.user, **dados)
        except ConflitoEstado:
            raise
        except ValueError as erro:
            raise ValidationError({"motivo": [str(erro)]}) from erro
        return Response(OngPrivada(ong).data)
