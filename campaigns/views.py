from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from organizations.models import Ong

from .forms import BuscaCampanhaForm, CampanhaForm, FiltroPainelCampanhaForm
from .models import Campanha
from .services import ConflitoEstado, mudar_estado


@require_GET
def lista(request):
    form = BuscaCampanhaForm(request.GET)
    campanhas = Campanha.objects.select_related("ong").filter(ong__status=Ong.Status.APROVADA).exclude(status=Campanha.Status.RASCUNHO)
    ordenacao = "-criada_em"
    if form.is_valid():
        filtros = form.cleaned_data
        if filtros["q"]:
            campanhas = campanhas.filter(Q(titulo__icontains=filtros["q"]) | Q(descricao__icontains=filtros["q"]))
        for campo in ("cidade", "bairro"):
            if filtros[campo]:
                campanhas = campanhas.filter(**{f"ong__{campo}__icontains": filtros[campo]})
        if filtros["uf"]:
            campanhas = campanhas.filter(ong__uf=filtros["uf"])
        for campo in ("tipo", "status"):
            if filtros[campo]:
                campanhas = campanhas.filter(**{campo: filtros[campo]})
        if filtros["disponivel"]:
            hoje = timezone.localdate()
            campanhas = campanhas.filter(status=Campanha.Status.ATIVA, data_inicio__lte=hoje, data_fim__gte=hoje)
        ordenacao = filtros["ordenacao"] or ordenacao
    else:
        campanhas = campanhas.none()
    pagina = Paginator(campanhas.order_by(ordenacao, "-pk"), 20).get_page(request.GET.get("page"))
    parametros = request.GET.copy()
    parametros.pop("page", None)
    return render(request, "campaigns/lista.html", {"form": form, "pagina": pagina, "filtros": parametros.urlencode()})


@require_GET
def detalhe(request, pk):
    campanha = get_object_or_404(Campanha.objects.select_related("ong"), pk=pk)
    dono = request.user.is_authenticated and campanha.ong.responsavel_id == request.user.pk
    if not dono and (campanha.ong.status != Ong.Status.APROVADA or campanha.status == Campanha.Status.RASCUNHO):
        raise Http404
    return render(request, "campaigns/detalhe.html", {"campanha": campanha, "dono": dono})


@login_required
@require_GET
def painel(request):
    ong = Ong.objects.filter(responsavel=request.user).first()
    if not ong:
        messages.info(request, "Cadastre uma ONG para acessar suas campanhas.")
        return redirect("ong-nova")
    form = FiltroPainelCampanhaForm(request.GET)
    campanhas = ong.campanhas.order_by("-criada_em", "-pk")
    if form.is_valid():
        if form.cleaned_data["status"]:
            campanhas = campanhas.filter(status=form.cleaned_data["status"])
    else:
        campanhas = campanhas.none()
    return render(request, "campaigns/painel.html", {"ong": ong, "campanhas": campanhas, "form": form})


@login_required
@require_http_methods(["GET", "POST"])
def nova(request):
    ong = Ong.objects.filter(responsavel=request.user).first()
    if not ong:
        messages.info(request, "Cadastre uma ONG para criar campanhas.")
        return redirect("ong-nova")
    if ong.status != Ong.Status.APROVADA:
        messages.error(request, "A ONG precisa de aprovação para criar campanhas.")
        return redirect("campanha-painel")
    form = CampanhaForm(request.POST if request.method == "POST" else None, instance=Campanha(ong=ong))
    if request.method == "POST" and form.is_valid():
        campanha = form.save()
        messages.success(request, "Campanha criada como rascunho.")
        return redirect("campanha-detalhe", pk=campanha.pk)
    return render(request, "campaigns/formulario.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def editar(request, pk):
    campanha = get_object_or_404(Campanha, pk=pk, ong__responsavel=request.user)
    form = CampanhaForm(request.POST if request.method == "POST" else None, instance=campanha)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Campanha atualizada.")
        return redirect("campanha-detalhe", pk=pk)
    return render(request, "campaigns/formulario.html", {"form": form, "campanha": campanha})


@login_required
@require_POST
def estado(request, pk):
    campanha = get_object_or_404(Campanha, pk=pk, ong__responsavel=request.user)
    try:
        mudar_estado(campanha, request.POST.get("acao", ""))
    except ConflitoEstado as erro:
        messages.error(request, str(erro))
    else:
        messages.success(request, "Estado da campanha atualizado.")
    return redirect("campanha-painel")


@login_required
@require_POST
def excluir(request, pk):
    campanha = get_object_or_404(Campanha, pk=pk, ong__responsavel=request.user)
    try:
        campanha.delete()
    except ProtectedError:
        messages.error(request, "Não é possível excluir a campanha porque há dependências vinculadas a ela.")
    else:
        messages.success(request, "Campanha excluída.")
    return redirect("campanha-painel")
