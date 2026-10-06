from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import CadastroForm


@require_http_methods(["GET", "POST"])
def cadastro(request):
    if request.user.is_authenticated:
        return redirect("painel")
    form = CadastroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Conta criada. Entre com seu usuário e senha.")
        return redirect("login")
    return render(request, "accounts/cadastro.html", {"form": form})


@login_required
def painel(request):
    return render(request, "accounts/painel.html")
