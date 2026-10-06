import csv
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from html.parser import HTMLParser
from io import StringIO
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from campaigns.models import Campanha
from campaigns.tests import dados_campanha
from contributions.models import Contribuicao
from contributions.services import avaliar_contribuicao, cancelar_contribuicao, criar_contribuicao
from contributions.tests import preparar_campanhas
from organizations.models import Ong
from organizations.tests import dados_ong

from .consulta import consultar_relatorio


class LeitorTabela(HTMLParser):
    """Lê as células para comparar os números efetivamente exibidos."""
    def __init__(self):
        super().__init__()
        self.linhas = []
        self.linha = []
        self.celula = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.linha = []
        elif tag == "td":
            self.celula = ""

    def handle_data(self, data):
        if self.celula is not None:
            self.celula += data

    def handle_endtag(self, tag):
        if tag == "td":
            self.linha.append(self.celula)
            self.celula = None
        elif tag == "tr" and self.linha:
            self.linhas.append(self.linha)


class RelatorioTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dono, cls.autor, cls.ong, cls.campanhas = preparar_campanhas()
        cls.outro = User.objects.create_user("outrong", "outra@example.org")
        cls.outra_ong = Ong.objects.create(responsavel=cls.outro, **dados_ong(cep="01001000"))
        cls.outra_campanha = Campanha.objects.create(ong=cls.outra_ong, **dados_campanha())
        cls.vazia = Campanha.objects.create(ong=cls.ong, **dados_campanha(titulo="Sem contribuições"))
        for tipo in Campanha.Tipo.values:
            for estado in Contribuicao.Status.values:
                if tipo == "dinheiro" and estado == "aceita":
                    continue
                dados = {"valor": "10.25"} if tipo == "dinheiro" else {"quantidade": "2" if tipo == "item" else "2.50"}
                contribuicao = criar_contribuicao(cls.autor, cls.campanhas[tipo], dados)
                if estado == "aceita" or (estado == "confirmada" and tipo != "dinheiro"):
                    avaliar_contribuicao(contribuicao.pk, cls.dono, "aceitar")
                if estado in ("confirmada", "recusada"):
                    avaliar_contribuicao(contribuicao.pk, cls.dono, "confirmar" if estado == "confirmada" else "recusar", "Motivo privado")
                if estado == "cancelada":
                    cancelar_contribuicao(contribuicao.pk, cls.autor)

    def setUp(self):
        self.client.force_login(self.dono)
        hoje = timezone.localdate().isoformat()
        self.filtros = {"inicio": hoje, "fim": hoje}

    def linhas_csv(self, resposta):
        return list(csv.DictReader(StringIO(resposta.content.decode("utf-8-sig")), delimiter=";"))

    def test_campanhas_sem_contribuicao_aparecem_com_zeros(self):
        resposta = self.client.get(reverse("relatorio-painel"), self.filtros)
        self.assertEqual(len(resposta.context["linhas"]), 4)
        linha = next(linha for linha in resposta.context["linhas"] if linha["titulo"] == self.vazia.titulo)
        self.assertEqual(linha["total_confirmado"], 0)
        for campo in ("declaradas", "aceitas", "confirmadas", "recusadas", "canceladas"):
            self.assertEqual(linha[campo], 0)

    def test_contagens_usam_estado_atual_e_total_apenas_confirmado(self):
        linhas = self.client.get(reverse("relatorio-painel"), self.filtros).context["linhas"]
        for tipo, total in (("dinheiro", "10.25"), ("item", "2"), ("horas", "2.5")):
            linha = next(linha for linha in linhas if linha["titulo"] == tipo)
            self.assertEqual(linha["total_confirmado"], Decimal(total))
            for campo in ("declaradas", "confirmadas", "recusadas", "canceladas"):
                self.assertEqual(linha[campo], 1)
            self.assertEqual(linha["aceitas"], 0 if tipo == "dinheiro" else 1)
        declarada = Contribuicao.objects.get(tipo="dinheiro", status="declarada")
        avaliar_contribuicao(declarada.pk, self.dono, "confirmar")
        linha = self.client.get(reverse("relatorio-painel"), {**self.filtros, "tipo": "dinheiro"}).context["linhas"][0]
        self.assertEqual(linha["total_confirmado"], Decimal("20.50"))
        self.assertEqual(linha["confirmadas"], 2)
        self.assertEqual(linha["declaradas"], 0)

    def test_periodo_inclusivo_e_fronteiras_no_fuso_de_sao_paulo(self):
        inicio, fim = date(2026, 1, 10), date(2026, 1, 11)
        sao_paulo = ZoneInfo("America/Sao_Paulo")
        horarios = (
            (datetime.combine(inicio - timedelta(days=1), time(23, 30), sao_paulo), False),
            (datetime.combine(inicio, time.min, sao_paulo), True),
            (datetime.combine(fim, time(23, 30), sao_paulo), True),
            (datetime.combine(fim + timedelta(days=1), time.min, sao_paulo), False),
        )
        for horario, incluido in horarios:
            contribuicao = criar_contribuicao(self.autor, self.campanhas["dinheiro"], {"valor": "5.50"})
            avaliar_contribuicao(contribuicao.pk, self.dono, "confirmar")
            Contribuicao.objects.filter(pk=contribuicao.pk).update(criada_em=horario)
            if incluido:
                self.assertGreaterEqual(horario.date(), inicio)
        filtros = {"inicio": inicio.isoformat(), "fim": fim.isoformat(), "tipo": "dinheiro"}
        linha = self.client.get(reverse("relatorio-painel"), filtros).context["linhas"][0]
        self.assertEqual(linha["total_confirmado"], Decimal("11"))
        self.assertEqual(linha["confirmadas"], 2)
        filtros["inicio"] = fim.isoformat()
        linha = self.client.get(reverse("relatorio-painel"), filtros).context["linhas"][0]
        self.assertEqual(linha["confirmadas"], 1)
        self.assertEqual(linha["total_confirmado"], Decimal("5.50"))

    def test_filtros_campanha_e_tipo(self):
        for tipo in Campanha.Tipo.values:
            for filtros in ({"campanha": self.campanhas[tipo].pk}, {"tipo": tipo, "campanha": self.campanhas[tipo].pk}):
                resposta = self.client.get(reverse("relatorio-painel"), {**self.filtros, **filtros})
                self.assertEqual([linha["titulo"] for linha in resposta.context["linhas"]], [tipo])
        resposta = self.client.get(reverse("relatorio-painel"), {**self.filtros, "tipo": "dinheiro"})
        self.assertEqual([linha["titulo"] for linha in resposta.context["linhas"]], ["dinheiro"])
        resposta = self.client.get(reverse("relatorio-painel"), {**self.filtros, "campanha": self.campanhas["dinheiro"].pk, "tipo": "horas"})
        self.assertEqual(resposta.context["linhas"], [])

    def test_campanha_de_outra_ong_rejeitada_em_todas_saidas(self):
        for nome in ("relatorio-painel", "relatorio-exportar", "relatorio-imprimir"):
            with self.subTest(nome=nome):
                resposta = self.client.get(reverse(nome), {**self.filtros, "campanha": self.outra_campanha.pk})
                self.assertEqual(resposta.status_code, 400)
                self.assertIn("campanha", resposta.context["form"].errors)
                self.assertNotIn("Content-Disposition", resposta)

    def test_datas_obrigatorias_validas_ordenadas_e_maximo_366_dias(self):
        casos = (
            ({"fim": "2026-01-01"}, "inicio"), ({"inicio": "2026-01-01"}, "fim"),
            ({"inicio": "inválido", "fim": "2026-01-01"}, "inicio"),
            ({"inicio": "2026-01-02", "fim": "2026-01-01"}, "fim"),
            ({"inicio": "2026-01-01", "fim": "2027-01-02"}, "fim"),
            ({"inicio": "9999-12-31", "fim": "9999-12-31"}, "fim"),
        )
        for filtros, campo in casos:
            for nome in ("relatorio-painel", "relatorio-exportar", "relatorio-imprimir"):
                with self.subTest(filtros=filtros, nome=nome):
                    resposta = self.client.get(reverse(nome), filtros)
                    self.assertEqual(resposta.status_code, 400)
                    self.assertIn(campo, resposta.context["form"].errors)
        resposta = self.client.get(reverse("relatorio-painel"), {"inicio": "2026-01-01", "fim": "2027-01-01"})
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("gerado_em", resposta.context)

    def test_tipo_invalido_rejeitado(self):
        resposta = self.client.get(reverse("relatorio-painel"), {**self.filtros, "tipo": "outro"})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("tipo", resposta.context["form"].errors)

    def test_tela_inicial_sem_consulta_ate_informar_periodo(self):
        resposta = self.client.get(reverse("relatorio-painel"))
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(resposta.context["form"].is_bound)
        self.assertNotIn("gerado_em", resposta.context)
        for nome in ("relatorio-exportar", "relatorio-imprimir"):
            self.assertEqual(self.client.get(reverse(nome)).status_code, 400)

    def test_sem_nomes_emails_ids_de_autores_ou_observacoes(self):
        Contribuicao.objects.update(observacao="Observação privada de teste")
        for nome in ("relatorio-painel", "relatorio-exportar", "relatorio-imprimir"):
            resposta = self.client.get(reverse(nome), self.filtros)
            for privado in (self.autor.first_name, self.autor.email, "Observação privada de teste", "Motivo privado"):
                self.assertNotContains(resposta, privado)
        colunas = self.linhas_csv(self.client.get(reverse("relatorio-exportar"), self.filtros))[0]
        self.assertEqual(set(colunas), {"titulo", "tipo", "unidade", "meta", "total_confirmado", "declaradas", "aceitas", "confirmadas", "recusadas", "canceladas", "inicio", "fim", "gerado_em"})

    def test_tela_csv_e_impressao_exibem_os_mesmos_numeros(self):
        tela = self.client.get(reverse("relatorio-painel"), self.filtros)
        impressao = self.client.get(reverse("relatorio-imprimir"), self.filtros)
        exportacao = self.client.get(reverse("relatorio-exportar"), self.filtros)
        self.assertEqual(tela.context["linhas"], impressao.context["linhas"])
        tabelas = []
        for resposta in (tela, impressao):
            leitor = LeitorTabela()
            leitor.feed(resposta.content.decode())
            tabelas.append(leitor.linhas)
        self.assertEqual(tabelas[0], tabelas[1])
        csv_linhas = self.linhas_csv(exportacao)
        for exibida, exportada in zip(tabelas[0], csv_linhas, strict=True):
            self.assertEqual(exibida[:3], [exportada[campo] for campo in ("titulo", "tipo", "unidade")])
            for indice, campo in ((3, "meta"), (4, "total_confirmado")):
                self.assertEqual(Decimal(exibida[indice].replace(".", "").replace(",", ".")), Decimal(exportada[campo].replace(",", ".")))
            self.assertEqual(exibida[5:], [exportada[campo] for campo in ("declaradas", "aceitas", "confirmadas", "recusadas", "canceladas")])

    def test_tres_saidas_chamam_a_mesma_consulta(self):
        with patch("reports.views.consultar_relatorio", wraps=consultar_relatorio) as consulta:
            for nome in ("relatorio-painel", "relatorio-exportar", "relatorio-imprimir"):
                self.assertEqual(self.client.get(reverse(nome), self.filtros).status_code, 200)
            self.assertEqual(consulta.call_count, 3)
            self.assertEqual(consulta.call_args_list[0], consulta.call_args_list[1])
            self.assertEqual(consulta.call_args_list[1], consulta.call_args_list[2])

    def test_csv_tem_bom_separador_decimal_cabecalho_e_datas(self):
        resposta = self.client.get(reverse("relatorio-exportar"), self.filtros)
        self.assertTrue(resposta.content.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(resposta["Content-Type"], "text/csv; charset=utf-8")
        self.assertEqual(resposta["Content-Disposition"], 'attachment; filename="relatorio-campanhas.csv"')
        self.assertContains(resposta, "titulo;tipo;unidade;meta;total_confirmado;")
        self.assertContains(resposta, ";10,25;")
        for linha in self.linhas_csv(resposta):
            self.assertEqual(linha["inicio"], self.filtros["inicio"])
            self.assertEqual(linha["fim"], self.filtros["fim"])
            self.assertIsNotNone(datetime.fromisoformat(linha["gerado_em"]).tzinfo)

    def test_csv_neutraliza_formulas_em_titulo_e_unidade(self):
        for prefixo in ("=", "+", "-", "@"):
            Campanha.objects.create(ong=self.ong, **dados_campanha(titulo=prefixo + "Título", unidade=prefixo + "Unidade"))
        linhas = self.linhas_csv(self.client.get(reverse("relatorio-exportar"), self.filtros))
        for prefixo in ("=", "+", "-", "@"):
            linha = next(linha for linha in linhas if linha["titulo"] == "'" + prefixo + "Título")
            self.assertEqual(linha["unidade"], "'" + prefixo + "Unidade")

    def test_csv_preserva_acentos_aspas_separadores_e_quebras(self):
        titulo = 'Ação; "comunidade"\nCestas'
        Campanha.objects.filter(pk=self.vazia.pk).update(titulo=titulo)
        linhas = self.linhas_csv(self.client.get(reverse("relatorio-exportar"), self.filtros))
        self.assertIn(titulo, [linha["titulo"] for linha in linhas])

    def test_falha_gera_mensagem_e_nunca_arquivo_parcial(self):
        for alvo, erro in (("reports.views.gerar_csv", csv.Error("Falha")), ("reports.views.consultar_relatorio", DatabaseError("Falha"))):
            with self.subTest(alvo=alvo), patch(alvo, side_effect=erro):
                resposta = self.client.get(reverse("relatorio-exportar"), self.filtros)
                self.assertRedirects(resposta, reverse("relatorio-painel"), fetch_redirect_response=False)
                self.assertNotIn("Content-Disposition", resposta)
                self.assertContains(self.client.get(reverse("relatorio-painel")), "Não foi possível gerar o relatório.")

    def test_impressao_tem_filtros_data_de_geracao_e_estilo(self):
        resposta = self.client.get(reverse("relatorio-imprimir"), {**self.filtros, "campanha": self.campanhas["dinheiro"].pk, "tipo": "dinheiro"})
        for texto in ("@media print", "Gerado em:", "Período:", "Campanha: dinheiro", "Tipo: dinheiro", "São Paulo"):
            self.assertContains(resposta, texto)
        self.assertNotContains(resposta, '<nav aria-label="Principal">')

    def test_acesso_sem_ong_redireciona_e_anonimo_vai_ao_login(self):
        for nome in ("relatorio-painel", "relatorio-exportar", "relatorio-imprimir"):
            url = reverse(nome)
            self.client.force_login(self.autor)
            self.assertRedirects(self.client.get(url, self.filtros), reverse("ong-nova"))
            self.client.logout()
            self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")

    def test_outra_ong_so_ve_as_proprias_campanhas(self):
        self.client.force_login(self.outro)
        linhas = self.client.get(reverse("relatorio-painel"), self.filtros).context["linhas"]
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0]["titulo"], self.outra_campanha.titulo)
        self.assertEqual(linhas[0]["total_confirmado"], 0)

    def test_consulta_agregada_nao_cresce_com_numero_de_campanhas(self):
        filtros = {"inicio": timezone.localdate(), "fim": timezone.localdate()}
        with self.assertNumQueries(1):
            consultar_relatorio(self.ong, filtros)
        for indice in range(15):
            Campanha.objects.create(ong=self.ong, **dados_campanha(titulo=f"Vazia {indice}"))
        with self.assertNumQueries(1):
            self.assertEqual(len(consultar_relatorio(self.ong, filtros)), 19)
