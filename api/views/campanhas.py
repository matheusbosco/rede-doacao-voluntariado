from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from campaigns.forms import CampanhaForm
from campaigns.models import Campanha
from campaigns.services import mudar_estado
from campaigns.totais import anotar_totais
from api.schema import documentar
from api.serializers.base import Entrada, formulario, validar
from api.serializers.campanhas import CampanhaEntrada, CampanhaResposta, EstadoEntrada
from api.serializers.filtros import CampanhaFiltro, PainelCampanhaFiltro

from .base import BaseView


def consulta_campanhas():
    return anotar_totais(Campanha.objects.select_related("ong"))


class CampanhasView(BaseView):
    filtro = CampanhaFiltro
    painel = False

    @documentar("Listar campanhas públicas", "Campanhas", CampanhaResposta, filtros=CampanhaFiltro, lista=True)
    def get(self, request):
        consulta = consulta_campanhas()
        if self.painel:
            consulta = consulta.filter(ong=self.minha_ong())
        else:
            consulta = consulta.filter(ong__status="aprovada").exclude(status="rascunho")
        if busca := self.filtros.get("q"):
            consulta = consulta.filter(Q(titulo__icontains=busca) | Q(descricao__icontains=busca))
        for campo in ("ong_id", "tipo", "status"):
            if valor := self.filtros.get(campo):
                consulta = consulta.filter(**{campo: valor})
        for campo in ("cidade", "bairro", "uf"):
            if valor := self.filtros.get(campo):
                consulta = consulta.filter(**{f"ong__{campo}" if campo == "uf" else f"ong__{campo}__icontains": valor})
        if "disponivel" in self.filtros:
            hoje = timezone.localdate()
            disponiveis = Q(status="ativa", ong__status="aprovada", data_inicio__lte=hoje, data_fim__gte=hoje)
            consulta = consulta.filter(disponiveis if self.filtros["disponivel"] else ~disponiveis)
        return self.paginar(self.ordenar(consulta, "-criada_em"), CampanhaResposta)

    @documentar("Criar campanha como rascunho", "Campanhas", CampanhaResposta, CampanhaEntrada, status=201,
        exemplo={"titulo": "Cestas", "descricao": "Alimentos", "tipo": "item", "unidade": "cesta", "meta": "100.00", "data_inicio": "2026-10-06", "data_fim": "2026-10-16"})
    def post(self, request):
        dados = validar(CampanhaEntrada, request.data)
        with transaction.atomic():
            ong = self.minha_ong()
            if ong.status != "aprovada":
                raise PermissionDenied("A ONG precisa de aprovação.")
            campanha = formulario(CampanhaForm, dados, Campanha(ong=ong)).save()
        return Response(CampanhaResposta(campanha).data, status=201)


class PainelCampanhasView(CampanhasView):
    http_method_names = ["get"]
    protegida = True
    painel = True
    filtro = PainelCampanhaFiltro

    @documentar("Listar minhas campanhas, incluindo rascunhos", "Campanhas", CampanhaResposta, filtros=PainelCampanhaFiltro, lista=True)
    def get(self, request):
        return super().get(request)


class CampanhaView(BaseView):
    @documentar("Consultar campanha pública", "Campanhas", CampanhaResposta)
    def get(self, request, pk):
        campanha = get_object_or_404(consulta_campanhas().filter(ong__status="aprovada").exclude(status="rascunho"), pk=pk)
        return Response(CampanhaResposta(campanha).data)

    @documentar("Editar minha campanha", "Campanhas", CampanhaResposta, CampanhaEntrada, exemplo={"meta": "150.00"})
    def patch(self, request, pk):
        dados = validar(CampanhaEntrada, request.data, parcial=True)
        with transaction.atomic():
            campanha = get_object_or_404(Campanha.objects.select_for_update(of=("self",)), pk=pk, ong__responsavel=request.user)
            campanha = formulario(CampanhaForm, dados, campanha).save()
        return Response(CampanhaResposta(campanha).data)

    @documentar("Excluir campanha sem contribuições", "Campanhas", entrada=Entrada, status=204, exemplo={})
    def delete(self, request, pk):
        validar(Entrada, request.data)
        get_object_or_404(Campanha, pk=pk, ong__responsavel=request.user).delete()
        return Response(status=204)


class PainelCampanhaView(BaseView):
    protegida = True

    @documentar("Consultar minha campanha, incluindo rascunho", "Campanhas", CampanhaResposta)
    def get(self, request, pk):
        campanha = get_object_or_404(consulta_campanhas(), pk=pk, ong__responsavel=request.user)
        return Response(CampanhaResposta(campanha).data)


class EstadoView(BaseView):
    protegida = True

    @documentar("Publicar, pausar, reativar ou encerrar campanha", "Campanhas", CampanhaResposta, EstadoEntrada,
        exemplo={"acao": "publicar"})
    def post(self, request, pk):
        dados = validar(EstadoEntrada, request.data)
        campanha = get_object_or_404(Campanha, pk=pk, ong__responsavel=request.user)
        return Response(CampanhaResposta(mudar_estado(campanha, **dados)).data)
