from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from organizations.models import Postagem
from organizations.postagens import PostagemForm
from api.schema import documentar
from api.serializers.base import Entrada, formulario, validar
from api.serializers.filtros import PainelPostagemFiltro, PostagemFiltro
from api.serializers.postagens import PostagemEntrada, PostagemResposta

from .base import BaseView


def salvar_postagem(dados, postagem):
    if "campanha_id" in dados:
        dados["campanha"] = dados.pop("campanha_id")
    try:
        form = formulario(PostagemForm, dados, postagem)
    except ValidationError as erro:
        raise ValidationError({"campanha_id" if campo == "campanha" else campo: mensagens
            for campo, mensagens in erro.detail.items()}) from erro
    return form.save()


class PostagensView(BaseView):
    filtro = PostagemFiltro
    painel = False

    @documentar("Listar postagens publicadas", "Postagens", PostagemResposta, filtros=PostagemFiltro, lista=True)
    def get(self, request):
        consulta = Postagem.objects.all()
        consulta = consulta.filter(ong=self.minha_ong()) if self.painel else consulta.filter(publicada=True, ong__status="aprovada")
        if busca := self.filtros.get("q"):
            consulta = consulta.filter(Q(titulo__icontains=busca) | Q(conteudo__icontains=busca))
        for campo in ("ong_id", "campanha_id", "publicada"):
            if campo in self.filtros:
                consulta = consulta.filter(**{campo: self.filtros[campo]})
        return self.paginar(self.ordenar(consulta, "-criada_em"), PostagemResposta)

    @documentar("Criar postagem da minha ONG", "Postagens", PostagemResposta, PostagemEntrada, status=201,
        exemplo={"titulo": "Novidades", "conteudo": "Recebemos doações.", "publicada": True})
    def post(self, request):
        dados = validar(PostagemEntrada, request.data)
        ong = self.minha_ong()
        if ong.status != "aprovada":
            raise PermissionDenied("A ONG precisa de aprovação para criar postagens.")
        return Response(PostagemResposta(salvar_postagem(dados, Postagem(ong=ong))).data, status=201)


class PainelPostagensView(PostagensView):
    http_method_names = ["get"]
    protegida = True
    painel = True
    filtro = PainelPostagemFiltro

    @documentar("Listar minhas postagens, incluindo rascunhos", "Postagens", PostagemResposta, filtros=PainelPostagemFiltro, lista=True)
    def get(self, request):
        return super().get(request)


class PostagemView(BaseView):
    @documentar("Consultar postagem publicada", "Postagens", PostagemResposta)
    def get(self, request, pk):
        postagem = get_object_or_404(Postagem, pk=pk, publicada=True, ong__status="aprovada")
        return Response(PostagemResposta(postagem).data)

    @documentar("Editar minha postagem", "Postagens", PostagemResposta, PostagemEntrada, exemplo={"publicada": True})
    def patch(self, request, pk):
        dados = validar(PostagemEntrada, request.data, parcial=True)
        with transaction.atomic():
            postagem = get_object_or_404(Postagem.objects.select_for_update(of=("self",)), pk=pk, ong__responsavel=request.user)
            postagem = salvar_postagem(dados, postagem)
        return Response(PostagemResposta(postagem).data)

    @documentar("Excluir minha postagem", "Postagens", entrada=Entrada, status=204, exemplo={})
    def delete(self, request, pk):
        validar(Entrada, request.data)
        get_object_or_404(Postagem, pk=pk, ong__responsavel=request.user).delete()
        return Response(status=204)


class PainelPostagemView(BaseView):
    protegida = True

    @documentar("Consultar minha postagem, incluindo rascunho", "Postagens", PostagemResposta)
    def get(self, request, pk):
        postagem = get_object_or_404(Postagem, pk=pk, ong__responsavel=request.user)
        return Response(PostagemResposta(postagem).data)
