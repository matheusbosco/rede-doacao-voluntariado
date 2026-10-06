from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from organizations.models import Ong

from .forms import FiltroContribuicaoForm, FiltroRecebidasForm
from .models import Contribuicao


def renderizar_lista(request, contribuicoes, form, recebidas=False):
    if form.is_valid():
        dados = form.cleaned_data
        for campo in ("tipo", "campanha"):
            if dados.get(campo):
                contribuicoes = contribuicoes.filter(**{campo: dados[campo]})
        if dados["status"] and dados["status"] != "todos":
            contribuicoes = contribuicoes.filter(status=dados["status"])
        elif recebidas and not dados["status"]:
            contribuicoes = contribuicoes.filter(status__in=["declarada", "aceita"])
    else:
        contribuicoes = contribuicoes.none()
    pagina = Paginator(contribuicoes.order_by("-criada_em", "-pk"), 20).get_page(request.GET.get("page"))
    parametros = request.GET.copy()
    parametros.pop("page", None)
    return render(request, "contributions/lista.html", {
        "pagina": pagina, "form": form, "recebidas": recebidas, "filtros": parametros.urlencode(),
    })


@login_required
@require_GET
def minhas(request):
    contribuicoes = Contribuicao.objects.select_related("campanha").filter(autor=request.user)
    return renderizar_lista(request, contribuicoes, FiltroContribuicaoForm(request.GET))


@login_required
@require_GET
def painel(request):
    ong = Ong.objects.filter(responsavel=request.user).first()
    if not ong:
        messages.info(request, "Cadastre uma ONG para acessar as contribuições recebidas.")
        return redirect("ong-nova")
    contribuicoes = Contribuicao.objects.select_related("campanha", "autor").filter(campanha__ong=ong)
    return renderizar_lista(request, contribuicoes, FiltroRecebidasForm(request.GET, ong=ong), recebidas=True)
