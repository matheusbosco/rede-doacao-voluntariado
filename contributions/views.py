from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from campaigns.models import Campanha
from campaigns.services import ConflitoEstado

from .forms import ContribuicaoForm
from .models import Contribuicao
from .services import criar_contribuicao, editar_contribuicao, cancelar_contribuicao, avaliar_contribuicao


@login_required
@require_http_methods(["GET", "POST"])
def criar(request, pk):
    campanha = get_object_or_404(Campanha.objects.select_related("ong"), pk=pk)
    if campanha.ong.responsavel_id == request.user.pk or not campanha.disponivel:
        raise Http404
    form = ContribuicaoForm(request.POST if request.method == "POST" else None, tipo=campanha.tipo)
    if request.method == "POST" and form.is_valid():
        try:
            criar_contribuicao(request.user, campanha, form.cleaned_data)
        except (ValidationError, PermissionDenied) as erro:
            form.add_error(None, "; ".join(erro.messages) if isinstance(erro, ValidationError) else str(erro))
        else:
            messages.success(request, "Contribuição declarada. Aguarde a análise da ONG.")
            return redirect("contribuicao-minhas")
    return render(request, "contributions/formulario.html", {"form": form, "campanha": campanha})


@login_required
@require_http_methods(["GET", "POST"])
def editar(request, pk):
    contribuicao = get_object_or_404(Contribuicao.objects.select_related("campanha"), pk=pk, autor=request.user)
    if contribuicao.status != "declarada":
        messages.error(request, "Somente contribuições declaradas podem ser editadas.")
        return redirect("contribuicao-minhas")
    inicial = {campo: getattr(contribuicao, campo) for campo in ("valor", "quantidade", "observacao")}
    form = ContribuicaoForm(request.POST if request.method == "POST" else None, tipo=contribuicao.tipo, initial=inicial)
    if request.method == "POST" and form.is_valid():
        try:
            editar_contribuicao(pk, request.user, form.cleaned_data)
        except (ValidationError, ConflitoEstado) as erro:
            form.add_error(None, "; ".join(erro.messages) if isinstance(erro, ValidationError) else str(erro))
        else:
            messages.success(request, "Contribuição atualizada.")
            return redirect("contribuicao-minhas")
    return render(request, "contributions/formulario.html", {"form": form, "campanha": contribuicao.campanha, "contribuicao": contribuicao})


@login_required
@require_POST
def cancelar(request, pk):
    get_object_or_404(Contribuicao, pk=pk, autor=request.user)
    try:
        cancelar_contribuicao(pk, request.user)
    except ConflitoEstado as erro:
        messages.error(request, str(erro))
    else:
        messages.success(request, "Contribuição cancelada.")
    return redirect("contribuicao-minhas")


@login_required
@require_POST
def avaliar(request, pk):
    get_object_or_404(Contribuicao, pk=pk, campanha__ong__responsavel=request.user)
    try:
        avaliar_contribuicao(pk, request.user, request.POST.get("acao", ""), request.POST.get("motivo", ""))
    except (ValidationError, ConflitoEstado) as erro:
        messages.error(request, "; ".join(erro.messages) if isinstance(erro, ValidationError) else str(erro))
    else:
        messages.success(request, "Contribuição analisada.")
    return redirect("contribuicao-painel")
