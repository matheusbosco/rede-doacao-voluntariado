import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from organizations.models import Ong

from .consulta import consultar_relatorio
from .csv import gerar_csv
from .forms import RelatorioForm


@login_required
@require_GET
def relatorio(request, formato="tela"):
    ong = Ong.objects.filter(responsavel=request.user).first()
    if not ong:
        messages.info(request, "Cadastre uma ONG para acessar os relatórios.")
        return redirect("ong-nova")
    form = RelatorioForm(request.GET if request.GET or formato != "tela" else None, ong=ong)
    contexto = {"form": form, "ong": ong, "linhas": [], "filtros_url": request.GET.urlencode()}
    if form.is_bound and form.is_valid():
        gerado_em = timezone.now()
        try:
            linhas = consultar_relatorio(ong, form.cleaned_data)
            if formato == "csv":
                conteudo = gerar_csv(linhas, form.cleaned_data, gerado_em)
        except (DatabaseError, csv.Error, UnicodeError, OSError):
            messages.error(request, "Não foi possível gerar o relatório. Tente novamente.")
            return redirect("relatorio-painel")
        if formato == "csv":
            resposta = HttpResponse(conteudo, content_type="text/csv; charset=utf-8")
            resposta["Content-Disposition"] = 'attachment; filename="relatorio-campanhas.csv"'
            return resposta
        contexto.update(linhas=linhas, filtros=form.cleaned_data, gerado_em=gerado_em)
        if formato == "imprimir":
            return render(request, "reports/imprimir.html", contexto)
    return render(request, "reports/relatorio.html", contexto, status=400 if form.is_bound and form.errors else 200)
