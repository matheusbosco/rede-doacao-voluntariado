from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from campaigns.models import Campanha
from contributions.models import Contribuicao
from contributions.services import avaliar_contribuicao, cancelar_contribuicao, criar_contribuicao, editar_contribuicao
from api.schema import documentar
from api.serializers.base import Entrada, validar
from api.serializers.contribuicoes import (
    AvaliacaoEntrada, ContribuicaoDetalhe, ContribuicaoEdicao, ContribuicaoEntrada, ContribuicaoRecebida, ContribuicaoResposta,
)
from api.serializers.filtros import ContribuicaoFiltro

from .base import BaseView


def consulta_contribuicoes():
    return Contribuicao.objects.select_related("campanha__ong", "autor")


class ContribuicoesView(BaseView):
    protegida = True
    filtro = ContribuicaoFiltro
    painel = False

    @documentar("Listar minhas contribuições", "Contribuições", ContribuicaoResposta, filtros=ContribuicaoFiltro, lista=True)
    def get(self, request):
        consulta = consulta_contribuicoes()
        consulta = consulta.filter(campanha__ong=self.minha_ong()) if self.painel else consulta.filter(autor=request.user)
        for campo in ("campanha_id", "tipo", "status"):
            if campo in self.filtros:
                consulta = consulta.filter(**{campo: self.filtros[campo]})
        serializer = ContribuicaoRecebida if self.painel else ContribuicaoResposta
        return self.paginar(self.ordenar(consulta, "-criada_em"), serializer)

    @documentar("Declarar contribuição sem processar pagamento", "Contribuições", ContribuicaoResposta, ContribuicaoEntrada,
        status=201, exemplo={"campanha_id": 1, "tipo": "item", "quantidade": "2.00", "observacao": "Entrego amanhã."})
    def post(self, request):
        dados = validar(ContribuicaoEntrada, request.data)
        campanha = get_object_or_404(Campanha.objects.filter(ong__status="aprovada").exclude(status="rascunho"), pk=dados.pop("campanha_id"))
        return Response(ContribuicaoResposta(criar_contribuicao(request.user, campanha, dados)).data, status=201)


class PainelContribuicoesView(ContribuicoesView):
    http_method_names = ["get"]
    painel = True

    @documentar("Listar contribuições recebidas pela minha ONG", "Contribuições", ContribuicaoRecebida, filtros=ContribuicaoFiltro, lista=True)
    def get(self, request):
        return super().get(request)


class ContribuicaoView(BaseView):
    protegida = True

    @documentar("Consultar contribuição própria ou recebida", "Contribuições", ContribuicaoDetalhe)
    def get(self, request, pk):
        contribuicao = get_object_or_404(consulta_contribuicoes().filter(
            Q(autor=request.user) | Q(campanha__ong__responsavel=request.user)), pk=pk)
        serializer = ContribuicaoRecebida if contribuicao.campanha.ong.responsavel_id == request.user.pk else ContribuicaoResposta
        return Response(serializer(contribuicao).data)

    @documentar("Editar minha contribuição declarada", "Contribuições", ContribuicaoResposta, ContribuicaoEdicao,
        exemplo={"quantidade": "3.00"})
    def patch(self, request, pk):
        dados = validar(ContribuicaoEdicao, request.data, parcial=True)
        get_object_or_404(Contribuicao, pk=pk, autor=request.user)
        return Response(ContribuicaoResposta(editar_contribuicao(pk, request.user, dados)).data)


class CancelarView(BaseView):
    protegida = True

    @documentar("Cancelar minha contribuição", "Contribuições", ContribuicaoResposta, Entrada, exemplo={})
    def post(self, request, pk):
        validar(Entrada, request.data)
        get_object_or_404(Contribuicao, pk=pk, autor=request.user)
        return Response(ContribuicaoResposta(cancelar_contribuicao(pk, request.user)).data)


class AvaliacaoView(BaseView):
    protegida = True

    @documentar("Aceitar, confirmar ou recusar contribuição recebida", "Contribuições", ContribuicaoResposta, AvaliacaoEntrada,
        exemplo={"acao": "confirmar"})
    def post(self, request, pk):
        dados = validar(AvaliacaoEntrada, request.data)
        get_object_or_404(Contribuicao, pk=pk, campanha__ong__responsavel=request.user)
        return Response(ContribuicaoResposta(avaliar_contribuicao(pk, request.user, **dados)).data)
