from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from campaigns.models import Campanha

from .models import Ong, Postagem


class PostagemForm(forms.ModelForm):
    class Meta:
        model = Postagem
        fields = ("titulo", "conteudo", "campanha", "publicada")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["campanha"].queryset = Campanha.objects.filter(ong_id=self.instance.ong_id).order_by("titulo", "pk")


class BuscaPostagemForm(forms.Form):
    q = forms.CharField(label="Buscar", max_length=100, required=False)
    ong = forms.ModelChoiceField(label="ONG", queryset=Ong.objects.filter(status=Ong.Status.APROVADA).order_by("nome", "pk"), required=False)


@require_GET
def lista(request):
    form = BuscaPostagemForm(request.GET)
    postagens = Postagem.objects.select_related("ong").filter(publicada=True, ong__status=Ong.Status.APROVADA)
    if form.is_valid():
        if form.cleaned_data["q"]:
            busca = form.cleaned_data["q"]
            postagens = postagens.filter(Q(titulo__icontains=busca) | Q(conteudo__icontains=busca))
        if form.cleaned_data["ong"]:
            postagens = postagens.filter(ong=form.cleaned_data["ong"])
    else:
        postagens = postagens.none()
    pagina = Paginator(postagens.order_by("-criada_em", "-pk"), 20).get_page(request.GET.get("page"))
    parametros = request.GET.copy()
    parametros.pop("page", None)
    return render(request, "organizations/postagens_lista.html", {"form": form, "pagina": pagina, "filtros": parametros.urlencode()})


@require_GET
def detalhe(request, pk):
    postagem = get_object_or_404(
        Postagem.objects.select_related("ong", "campanha"), pk=pk,
        publicada=True, ong__status=Ong.Status.APROVADA,
    )
    return render(request, "organizations/postagem_detalhe.html", {"postagem": postagem})


@login_required
@require_GET
def painel(request):
    ong = Ong.objects.filter(responsavel=request.user).first()
    if not ong:
        messages.info(request, "Cadastre uma ONG para acessar suas postagens.")
        return redirect("ong-nova")
    return render(request, "organizations/postagens_painel.html", {
        "ong": ong, "postagens": ong.postagens.order_by("-criada_em", "-pk"),
    })


@login_required
@require_http_methods(["GET", "POST"])
def nova(request):
    ong = Ong.objects.filter(responsavel=request.user).first()
    if not ong:
        messages.info(request, "Cadastre uma ONG para criar postagens.")
        return redirect("ong-nova")
    if ong.status != Ong.Status.APROVADA:
        messages.error(request, "A ONG precisa de aprovação para criar postagens.")
        return redirect("postagem-painel")
    form = PostagemForm(request.POST if request.method == "POST" else None, instance=Postagem(ong=ong))
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Postagem criada.")
        return redirect("postagem-painel")
    return render(request, "organizations/postagem_formulario.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def editar(request, pk):
    postagem = get_object_or_404(Postagem.objects.select_related("ong"), pk=pk, ong__responsavel=request.user)
    if request.method == "POST" and request.POST.get("publicada") and postagem.ong.status != Ong.Status.APROVADA:
        messages.error(request, "A ONG precisa de aprovação para publicar postagens.")
        return redirect("postagem-painel")
    form = PostagemForm(request.POST if request.method == "POST" else None, instance=postagem)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Postagem atualizada.")
        return redirect("postagem-painel")
    return render(request, "organizations/postagem_formulario.html", {"form": form, "postagem": postagem})


@login_required
@require_POST
def excluir(request, pk):
    postagem = get_object_or_404(Postagem, pk=pk, ong__responsavel=request.user)
    postagem.delete()
    messages.success(request, "Postagem excluída.")
    return redirect("postagem-painel")
