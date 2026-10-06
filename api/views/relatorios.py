from django.http import HttpResponse
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiTypes

from reports.consulta import consultar_relatorio
from reports.csv import gerar_csv
from reports.forms import RelatorioForm
from api.schema import documentar
from api.serializers.filtros import RelatorioFiltro
from api.serializers.relatorios import RelatorioResposta

from .base import BaseView


class RelatorioView(BaseView):
    protegida = True
    filtro = RelatorioFiltro
    exportar = False

    @documentar("Consultar relatório por criação da contribuição", "Relatórios", RelatorioResposta, filtros=RelatorioFiltro)
    def get(self, request):
        ong = self.minha_ong()
        filtros = dict(self.filtros)
        if "campanha_id" in filtros:
            filtros["campanha"] = filtros.pop("campanha_id")
        form = RelatorioForm(filtros, ong=ong)
        if not form.is_valid():
            raise ValidationError({"campanha_id" if campo == "campanha" else campo: list(erros) for campo, erros in form.errors.items()})
        linhas = consultar_relatorio(ong, form.cleaned_data)
        gerado_em = timezone.now()
        if self.exportar:
            resposta = HttpResponse(gerar_csv(linhas, form.cleaned_data, gerado_em), content_type="text/csv; charset=utf-8")
            resposta["Content-Disposition"] = 'attachment; filename="relatorio-campanhas.csv"'
            return resposta
        return Response(RelatorioResposta({**form.cleaned_data, "gerado_em": gerado_em,
            "criterio_periodo": "criacao_contribuicao", "campanhas": linhas}).data)


class ExportarRelatorioView(RelatorioView):
    exportar = True

    @documentar("Exportar o mesmo CSV do relatório da tela", "Relatórios", resposta=OpenApiTypes.BINARY, filtros=RelatorioFiltro, mime="text/csv")
    def get(self, request):
        return super().get(request)
