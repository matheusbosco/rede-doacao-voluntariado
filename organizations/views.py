from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import BuscaOngForm, OngForm
from .models import Ong
from .services import ConflitoEstado, analisar_ong, reenviar_ong


@require_GET
def lista(request):
    form = BuscaOngForm(request.GET)
    ongs = Ong.objects.filter(status=Ong.Status.APROVADA)
    if form.is_valid():
        filtros = form.cleaned_data
        if filtros["q"]:
            ongs = ongs.filter(Q(nome__icontains=filtros["q"]) | Q(descricao__icontains=filtros["q"]) | Q(causa__icontains=filtros["q"]))
        for campo in ("cidade", "bairro"):
            if filtros[campo]:
                ongs = ongs.filter(**{f"{campo}__icontains": filtros[campo]})
        if filtros["uf"]:
            ongs = ongs.filter(uf=filtros["uf"])
    else:
        ongs = ongs.none()
    pagina = Paginator(ongs.order_by("nome", "pk"), 20).get_page(request.GET.get("page"))
    parametros = request.GET.copy()
    parametros.pop("page", None)
    return render(request, "organizations/lista.html", {
        "form": form, "pagina": pagina, "filtros": parametros.urlencode(),
    })


@require_GET
def detalhe(request, pk):
    ong = get_object_or_404(Ong, pk=pk)
    dono = request.user.is_authenticated and ong.responsavel_id == request.user.pk
    if ong.status != Ong.Status.APROVADA and not (dono or request.user.is_staff):
        raise Http404
    return render(request, "organizations/detalhe.html", {"ong": ong, "dono": dono})


@login_required
@require_http_methods(["GET", "POST"])
def nova(request):
    existente = Ong.objects.filter(responsavel=request.user).first()
    if existente:
        messages.info(request, "Você já tem uma ONG cadastrada. Edite as informações abaixo.")
        return redirect("ong-editar", pk=existente.pk)
    form = OngForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        ong = form.save(commit=False)
        ong.responsavel = request.user
        ong.save()
        messages.success(request, "ONG cadastrada. Ela fica em análise até a aprovação pela equipe.")
        return redirect("ong-detalhe", pk=ong.pk)
    return render(request, "organizations/formulario.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def editar(request, pk):
    ong = get_object_or_404(Ong, pk=pk, responsavel=request.user)
    status_anterior = ong.status
    form = OngForm(request.POST if request.method == "POST" else None, instance=ong)
    if request.method == "POST" and form.is_valid():
        ong = form.save()
        if status_anterior == Ong.Status.APROVADA and ong.status == Ong.Status.PENDENTE:
            messages.success(request, "Informações atualizadas. A ONG voltou para análise.")
        else:
            messages.success(request, "Informações da ONG atualizadas.")
        return redirect("ong-detalhe", pk=ong.pk)
    return render(request, "organizations/formulario.html", {"form": form, "ong": ong})


@login_required
@require_POST
def excluir(request, pk):
    ong = get_object_or_404(Ong, pk=pk, responsavel=request.user)
    try:
        ong.delete()
    except ProtectedError:
        messages.error(request, "Não é possível excluir a ONG porque há dependências vinculadas a ela.")
        return redirect("ong-detalhe", pk=pk)
    messages.success(request, "ONG excluída.")
    return redirect("painel")


@login_required
@require_POST
def reenviar(request, pk):
    ong = get_object_or_404(Ong, pk=pk, responsavel=request.user)
    try:
        reenviar_ong(ong)
    except ConflitoEstado as erro:
        messages.error(request, str(erro))
    else:
        messages.success(request, "ONG reenviada para análise.")
    return redirect("ong-detalhe", pk=pk)


@login_required
@require_GET
def minha(request):
    ong = Ong.objects.filter(responsavel=request.user).first()
    if ong:
        return redirect("ong-detalhe", pk=ong.pk)
    return redirect("ong-nova")


@require_GET
def fila(request):
    if not request.user.is_staff:
        raise PermissionDenied
    ongs = Ong.objects.filter(status=Ong.Status.PENDENTE).order_by("criada_em", "pk")
    return render(request, "organizations/fila.html", {"ongs": ongs})


@require_POST
def analise(request, pk):
    if not request.user.is_staff:
        raise PermissionDenied
    get_object_or_404(Ong, pk=pk)
    try:
        analisar_ong(pk, request.user, request.POST.get("decisao", ""), request.POST.get("motivo", ""))
    except ConflitoEstado:
        messages.error(request, "ONG já analisada")
    except ValueError as erro:
        messages.error(request, str(erro))
    else:
        messages.success(request, "Análise registrada.")
    return redirect("admin-ong-fila")
