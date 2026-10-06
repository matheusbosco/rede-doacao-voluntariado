from datetime import timedelta
from unittest.mock import patch

from django.db import DatabaseError
from django.utils import timezone
from django.urls import reverse

from contributions.services import avaliar_contribuicao
from reports.consulta import consultar_relatorio
from reports.csv import gerar_csv
from reports.forms import RelatorioForm

from .base import APITestCase


class RelatoriosTests(APITestCase):
    def filtros(self, **alteracoes):
        hoje = timezone.localdate().isoformat()
        return {"inicio": hoje, "fim": hoje, **alteracoes}

    def test_json_e_csv_identicos_consulta_e_tela(self):
        avaliar_contribuicao(self.contribuicao.pk, self.dono, "aceitar")
        avaliar_contribuicao(self.contribuicao.pk, self.dono, "confirmar")
        instante = timezone.now()
        filtros = self.filtros(campanha_id=self.campanha.pk)
        cliente = self.sessao()
        with patch("api.views.relatorios.timezone.now", return_value=instante):
            resposta = cliente.get("/api/v1/relatorios/campanhas/", filtros)
            exportacao = cliente.get("/api/v1/relatorios/campanhas/exportar/", filtros)
        self.assertEqual(resposta.status_code, 200, resposta.content)
        self.assertEqual(resposta.json()["criterio_periodo"], "criacao_contribuicao")
        linha = resposta.json()["campanhas"][0]
        self.assertEqual(linha["campanha_id"], self.campanha.pk)
        self.assertEqual(linha["total_confirmado"], "2.00")
        self.assertEqual(linha["meta"], "100.00")
        self.assertEqual(linha["confirmadas"], 1)
        form = RelatorioForm(self.filtros(campanha=self.campanha.pk), ong=self.ong)
        self.assertTrue(form.is_valid())
        linhas = consultar_relatorio(self.ong, form.cleaned_data)
        self.assertEqual(exportacao.status_code, 200)
        self.assertEqual(exportacao["Content-Type"], "text/csv; charset=utf-8")
        self.assertEqual(exportacao.content, gerar_csv(linhas, form.cleaned_data, instante))
        with patch("reports.views.timezone.now", return_value=instante):
            tela_csv = cliente.get(reverse("relatorio-exportar"), self.filtros(campanha=self.campanha.pk))
        self.assertEqual(tela_csv.status_code, 200)
        self.assertEqual(tela_csv.content, exportacao.content)

    def test_filtros_tipo_e_ong_privada(self):
        cliente = self.sessao()
        resposta = cliente.get("/api/v1/relatorios/campanhas/", self.filtros(tipo="dinheiro"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.json()["campanhas"]), 1)
        self.assertEqual(resposta.json()["campanhas"][0]["tipo"], "dinheiro")
        privado = self.sessao(self.outro).get("/api/v1/relatorios/campanhas/", self.filtros())
        self.assertEqual([linha["campanha_id"] for linha in privado.json()["campanhas"]], [self.outra_campanha.pk])
        self.assertNotIn(self.autor.email, resposta.content.decode())
        self.assertNotIn("contato_autor", resposta.json()["campanhas"][0])

    def test_intervalo_obrigatorio_maximo_e_datas_invalidas(self):
        cliente = self.sessao()
        hoje = timezone.localdate()
        for filtros, campo in (({}, "inicio"), ({"inicio": hoje.isoformat()}, "fim"), (self.filtros(inicio="inválida"), "inicio"),
            (self.filtros(fim=(hoje - timedelta(days=1)).isoformat()), "fim"),
            (self.filtros(fim=(hoje + timedelta(days=366)).isoformat()), "fim"), (self.filtros(fim="9999-12-31"), "fim")):
            for sufixo in ("", "exportar/"):
                with self.subTest(filtros=filtros, sufixo=sufixo):
                    self.erro(cliente.get(f"/api/v1/relatorios/campanhas/{sufixo}", filtros), 400, "validacao", campo)
        self.assertEqual(cliente.get("/api/v1/relatorios/campanhas/", self.filtros(fim=(hoje + timedelta(days=365)).isoformat())).status_code, 200)

    def test_filtros_desconhecidos_protegidos_e_campanha_alheia(self):
        cliente = self.sessao()
        for campo, valor in (("campanha_id", self.outra_campanha.pk), ("tipo", "x"), ("autor", self.autor.pk), ("ordering", "titulo")):
            for sufixo in ("", "exportar/"):
                self.erro(cliente.get(f"/api/v1/relatorios/campanhas/{sufixo}", self.filtros(**{campo: valor})), 400, "validacao", campo)

    def test_sessao_ong_e_metodos(self):
        for sufixo in ("", "exportar/"):
            caminho = f"/api/v1/relatorios/campanhas/{sufixo}"
            self.erro(self.client.get(caminho, self.filtros()), 403, "autenticacao_necessaria")
            self.erro(self.sessao(self.sem_ong).get(caminho, self.filtros()), 404, "nao_encontrado")
            self.erro(self.sessao().post(caminho, {}, format="json"), 405, "metodo_nao_permitido")

    def test_falha_interna_sem_sql_ou_stack_trace(self):
        with patch("api.views.relatorios.consultar_relatorio", side_effect=DatabaseError("SQL segredo SELECT")):
            resposta = self.sessao().get("/api/v1/relatorios/campanhas/", self.filtros())
        self.erro(resposta, 500, "erro_interno")
        self.assertNotIn("SQL", resposta.content.decode())
        self.assertNotIn("SELECT", resposta.content.decode())
