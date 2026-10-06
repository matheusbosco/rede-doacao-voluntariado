from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, close_old_connections, connections, transaction
from django.db.models.deletion import ProtectedError
from django.forms.models import model_to_dict
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from campaigns.forms import CampanhaForm
from campaigns.models import Campanha
from campaigns.services import ConflitoEstado
from campaigns.tests import dados_campanha
from campaigns.totais import anotar_totais
from organizations.models import Ong
from organizations.tests import dados_ong

from .models import Contribuicao
from .services import avaliar_contribuicao, cancelar_contribuicao, criar_contribuicao, editar_contribuicao


def preparar_campanhas():
    dono = User.objects.create_user("responsavel", "responsavel@example.org", first_name="Responsável")
    autor = User.objects.create_user("doador", "doador@example.org", first_name="Nome privado do autor")
    ong = Ong.objects.create(
        responsavel=dono, **dados_ong(cep="01001000"), status="aprovada",
        analisada_por=dono, analisada_em=timezone.now(),
    )
    campanhas = {
        tipo: Campanha.objects.create(ong=ong, **dados_campanha(tipo=tipo, unidade=unidade, titulo=tipo), status="ativa")
        for tipo, unidade in (("dinheiro", "BRL"), ("item", "cesta"), ("horas", "hora"))
    }
    return dono, autor, ong, campanhas


class ContribuicaoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dono, cls.autor, cls.ong, cls.campanhas = preparar_campanhas()
        cls.outro = User.objects.create_user("outro", "outro@example.org")
        cls.outra_ong = Ong.objects.create(responsavel=cls.outro, **dados_ong(cep="01001000", nome="Outra ONG"))

    def criar(self, tipo_campanha="dinheiro", **dados):
        medida = {"valor": "10.25"} if tipo_campanha == "dinheiro" else {"quantidade": "2"}
        return criar_contribuicao(self.autor, self.campanhas[tipo_campanha], {**medida, **dados})

    def preparar_estado(self, tipo, status):
        contribuicao = self.criar(tipo)
        if status == "aceita" or (status == "confirmada" and tipo != "dinheiro"):
            avaliar_contribuicao(contribuicao.pk, self.dono, "aceitar")
        if status in ("confirmada", "recusada"):
            avaliar_contribuicao(contribuicao.pk, self.dono, "confirmar" if status == "confirmada" else "recusar", "Sem disponibilidade")
        if status == "cancelada":
            cancelar_contribuicao(contribuicao.pk, self.autor)
        contribuicao.refresh_from_db()
        return contribuicao

    def test_criacao_valida_dos_tres_tipos(self):
        for tipo in Campanha.Tipo.values:
            with self.subTest(tipo=tipo):
                contribuicao = self.criar(tipo, observacao="Disponível aos sábados")
                self.assertEqual(contribuicao.tipo, tipo)
                self.assertEqual(contribuicao.status, "declarada")
                self.assertEqual(contribuicao.autor, self.autor)
                self.assertIsNone(contribuicao.avaliada_por)
                self.assertIsNone(contribuicao.avaliada_em)
                self.assertIsNone(contribuicao.quantidade if tipo == "dinheiro" else contribuicao.valor)

    def test_dinheiro_e_horas_aceitam_fracao(self):
        self.assertEqual(self.criar(valor="0.01").valor, Decimal("0.01"))
        self.assertEqual(self.criar("horas", quantidade="0.25").quantidade, Decimal("0.25"))

    def test_tipo_diferente_e_campos_incompativeis_rejeitados(self):
        for tipo, dados in (("dinheiro", {"tipo": "item"}), ("dinheiro", {"quantidade": "1"}), ("item", {"valor": "1"}), ("horas", {"tipo": "dinheiro"})):
            with self.subTest(tipo=tipo, dados=dados), self.assertRaises(ValidationError):
                self.criar(tipo, **dados)
        self.assertEqual(Contribuicao.objects.count(), 0)

    def test_medidas_invalidas_rejeitadas_no_servico(self):
        for tipo in Campanha.Tipo.values:
            campo = "valor" if tipo == "dinheiro" else "quantidade"
            for valor in ("0", "-1", "1.001", "10000000000.00", "abc", "NaN", "Infinity", None):
                with self.subTest(tipo=tipo, valor=valor), self.assertRaises(ValidationError):
                    self.criar(tipo, **{campo: valor})
        with self.assertRaises(ValidationError):
            self.criar("item", quantidade="1.50")
        with self.assertRaises(ValidationError):
            self.criar(observacao="a" * 501)

    def test_cliente_nao_define_autor_estado_avaliacao_datas_nem_campanha(self):
        contribuicao = self.criar(
            autor=self.dono, status="confirmada", avaliada_por=self.dono,
            avaliada_em=timezone.now(), motivo_avaliacao="Inventado", criada_em=timezone.now() - timedelta(days=30),
            campanha=self.campanhas["item"], total_confirmado=999,
        )
        self.assertEqual(contribuicao.autor, self.autor)
        self.assertEqual(contribuicao.campanha, self.campanhas["dinheiro"])
        self.assertEqual(contribuicao.status, "declarada")
        self.assertEqual(contribuicao.motivo_avaliacao, "")
        self.assertEqual(timezone.localdate(contribuicao.criada_em), timezone.localdate())
        self.assertIsNone(contribuicao.avaliada_em)

    def test_indisponibilidade_bloqueia_criacao(self):
        campanha = self.campanhas["dinheiro"]
        hoje = timezone.localdate()
        alteracoes = [
            {"status": estado} for estado in ("rascunho", "pausada", "encerrada")
        ] + [
            {"data_inicio": hoje + timedelta(days=1)},
            {"data_inicio": hoje - timedelta(days=2), "data_fim": hoje - timedelta(days=1)},
        ]
        for dados in alteracoes:
            with self.subTest(dados=dados):
                Campanha.objects.filter(pk=campanha.pk).update(status="ativa", data_inicio=hoje, data_fim=hoje + timedelta(days=10))
                Campanha.objects.filter(pk=campanha.pk).update(**dados)
                with self.assertRaises(ValidationError):
                    self.criar()
        Campanha.objects.filter(pk=campanha.pk).update(status="ativa", data_inicio=hoje, data_fim=hoje)
        Ong.objects.filter(pk=self.ong.pk).update(status="pendente", analisada_por=None, analisada_em=None)
        with self.assertRaises(ValidationError):
            self.criar()
        self.assertEqual(Contribuicao.objects.count(), 0)

    def test_dono_e_anonimo_nao_contribuem(self):
        for usuario in (self.dono, AnonymousUser()):
            with self.subTest(usuario=usuario), self.assertRaises(PermissionDenied):
                criar_contribuicao(usuario, self.campanhas["dinheiro"], {"valor": "10"})

    def test_constraints_do_banco_exigem_medida_coerente(self):
        contribuicao = self.criar()
        for dados in (
            {"valor": 0}, {"valor": -1}, {"valor": None}, {"quantidade": 1},
            {"tipo": "item"}, {"tipo": "horas", "valor": None, "quantidade": 0},
            {"tipo": "item", "valor": None, "quantidade": None}, {"tipo": "invalido"},
        ):
            with self.subTest(dados=dados), self.assertRaises(IntegrityError):
                with transaction.atomic():
                    Contribuicao.objects.filter(pk=contribuicao.pk).update(**dados)

    def test_constraints_do_banco_exigem_avaliacao_e_motivo(self):
        contribuicao = self.criar()
        for dados in (
            {"status": "aceita", "avaliada_por": self.dono, "avaliada_em": timezone.now()},
            {"status": "confirmada"}, {"status": "recusada"},
            {"avaliada_por": self.dono}, {"avaliada_em": timezone.now()},
            {"status": "confirmada", "avaliada_por": self.dono},
            {"status": "recusada", "avaliada_por": self.dono, "avaliada_em": timezone.now()},
            {"status": "invalido"},
        ):
            with self.subTest(dados=dados), self.assertRaises(IntegrityError):
                with transaction.atomic():
                    Contribuicao.objects.filter(pk=contribuicao.pk).update(**dados)
        item = self.criar("item")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Contribuicao.objects.filter(pk=item.pk).update(status="aceita")

    def test_todas_transicoes_por_tipo_e_estado_sem_efeito_em_conflito(self):
        for tipo in Campanha.Tipo.values:
            estados = ["declarada", "confirmada", "recusada", "cancelada"]
            if tipo != "dinheiro":
                estados.append("aceita")
            for estado in estados:
                for acao in ("aceitar", "confirmar", "recusar", "cancelar", "invalida"):
                    with self.subTest(tipo=tipo, estado=estado, acao=acao):
                        contribuicao = self.preparar_estado(tipo, estado)
                        permitidas = set()
                        if estado == "declarada":
                            permitidas = {"recusar", "cancelar", "confirmar" if tipo == "dinheiro" else "aceitar"}
                        elif estado == "aceita":
                            permitidas = {"confirmar", "recusar", "cancelar"}
                        antes = model_to_dict(contribuicao)
                        atualizada_em = contribuicao.atualizada_em
                        def executar():
                            if acao == "cancelar":
                                return cancelar_contribuicao(contribuicao.pk, self.autor)
                            return avaliar_contribuicao(contribuicao.pk, self.dono, acao, "Motivo válido")
                        if acao in permitidas:
                            resultado = executar()
                            self.assertEqual(resultado.status, {"aceitar": "aceita", "confirmar": "confirmada", "recusar": "recusada", "cancelar": "cancelada"}[acao])
                            if acao != "cancelar":
                                self.assertEqual(resultado.avaliada_por, self.dono)
                                self.assertIsNotNone(resultado.avaliada_em)
                        else:
                            with self.assertRaises(ConflitoEstado):
                                executar()
                            contribuicao.refresh_from_db()
                            self.assertEqual(model_to_dict(contribuicao), antes)
                            self.assertEqual(contribuicao.atualizada_em, atualizada_em)

    def test_repeticao_de_acoes_gera_conflito(self):
        for tipo, acao in (("dinheiro", "confirmar"), ("item", "aceitar"), ("horas", "recusar")):
            contribuicao = self.criar(tipo)
            avaliar_contribuicao(contribuicao.pk, self.dono, acao, "Motivo")
            with self.subTest(acao=acao), self.assertRaises(ConflitoEstado):
                avaliar_contribuicao(contribuicao.pk, self.dono, acao, "Novo motivo")
            contribuicao.refresh_from_db()
            self.assertEqual(contribuicao.motivo_avaliacao, "Motivo")
        contribuicao = self.criar()
        cancelar_contribuicao(contribuicao.pk, self.autor)
        with self.assertRaises(ConflitoEstado):
            cancelar_contribuicao(contribuicao.pk, self.autor)

    def test_recusa_exige_motivo_de_ate_500_caracteres(self):
        contribuicao = self.criar()
        for motivo in ("", "   ", "a" * 501):
            with self.subTest(motivo=motivo), self.assertRaises(ValidationError):
                avaliar_contribuicao(contribuicao.pk, self.dono, "recusar", motivo)
        contribuicao.refresh_from_db()
        self.assertEqual(contribuicao.status, "declarada")
        resultado = avaliar_contribuicao(contribuicao.pk, self.dono, "recusar", "  " + "a" * 500 + "  ")
        self.assertEqual(len(resultado.motivo_avaliacao), 500)

    def test_analise_permitida_sem_disponibilidade_da_campanha(self):
        for status in ("pausada", "encerrada", "vencida"):
            contribuicao = self.criar()
            campanha = self.campanhas["dinheiro"]
            if status == "vencida":
                ontem = timezone.localdate() - timedelta(days=1)
                Campanha.objects.filter(pk=campanha.pk).update(data_inicio=ontem, data_fim=ontem)
            else:
                Campanha.objects.filter(pk=campanha.pk).update(status=status)
            self.assertEqual(avaliar_contribuicao(contribuicao.pk, self.dono, "confirmar").status, "confirmada")
            Campanha.objects.filter(pk=campanha.pk).update(status="ativa", data_inicio=timezone.localdate(), data_fim=timezone.localdate())

    def test_analise_exige_ong_aprovada_e_responsavel(self):
        contribuicao = self.criar()
        for usuario in (self.autor, self.outro, AnonymousUser()):
            with self.subTest(usuario=usuario), self.assertRaises(PermissionDenied):
                avaliar_contribuicao(contribuicao.pk, usuario, "confirmar")
        Ong.objects.filter(pk=self.ong.pk).update(status="pendente", analisada_por=None, analisada_em=None)
        with self.assertRaises(ValidationError):
            avaliar_contribuicao(contribuicao.pk, self.dono, "confirmar")
        contribuicao.refresh_from_db()
        self.assertEqual(contribuicao.status, "declarada")

    def test_so_autor_edita_e_cancela(self):
        contribuicao = self.criar()
        for usuario in (self.dono, self.outro, AnonymousUser()):
            with self.subTest(usuario=usuario):
                with self.assertRaises(PermissionDenied):
                    editar_contribuicao(contribuicao.pk, usuario, {"valor": "99"})
                with self.assertRaises(PermissionDenied):
                    cancelar_contribuicao(contribuicao.pk, usuario)
        resultado = editar_contribuicao(contribuicao.pk, self.autor, {"valor": "20", "observacao": "Ajustada", "status": "confirmada", "autor": self.dono})
        self.assertEqual(resultado.valor, Decimal("20"))
        self.assertEqual(resultado.observacao, "Ajustada")
        self.assertEqual(resultado.status, "declarada")
        self.assertEqual(resultado.autor, self.autor)

    def test_edicao_somente_declarada_e_validada(self):
        for estado in ("aceita", "confirmada", "recusada", "cancelada"):
            contribuicao = self.preparar_estado("item", estado)
            with self.subTest(estado=estado), self.assertRaises(ConflitoEstado):
                editar_contribuicao(contribuicao.pk, self.autor, {"quantidade": "99"})
        contribuicao = self.criar("item")
        for dados in ({"quantidade": "0"}, {"quantidade": "1.5"}, {"tipo": "horas"}, {"valor": "1"}, {"observacao": "a" * 501}):
            with self.subTest(dados=dados), self.assertRaises(ValidationError):
                editar_contribuicao(contribuicao.pk, self.autor, dados)
        self.assertEqual(editar_contribuicao(contribuicao.pk, self.autor, {"quantidade": "3"}).quantidade, 3)

    def test_total_conta_apenas_confirmadas_sem_duplicar(self):
        for tipo in Campanha.Tipo.values:
            for estado in ("declarada", "confirmada", "recusada", "cancelada"):
                self.preparar_estado(tipo, estado)
            if tipo != "dinheiro":
                self.preparar_estado(tipo, "aceita")
        with self.assertNumQueries(1):
            campanhas = list(anotar_totais(Campanha.objects.all()).order_by("tipo"))
            totais = {campanha.tipo: campanha.total_confirmado for campanha in campanhas}
            for campanha in campanhas:
                self.assertEqual(campanha.percentual_meta, campanha.total_confirmado)
        self.assertEqual(totais, {"dinheiro": Decimal("10.25"), "item": Decimal("2"), "horas": Decimal("2")})
        contribuicao = Contribuicao.objects.get(tipo="dinheiro", status="confirmada")
        with self.assertRaises(ConflitoEstado):
            avaliar_contribuicao(contribuicao.pk, self.dono, "confirmar")
        with self.assertNumQueries(1):
            self.assertEqual(self.campanhas["dinheiro"].total_confirmado, Decimal("10.25"))

    def test_percentual_pode_ultrapassar_cem(self):
        contribuicao = self.criar(valor="150")
        avaliar_contribuicao(contribuicao.pk, self.dono, "confirmar")
        self.assertEqual(self.campanhas["dinheiro"].percentual_meta, Decimal("150"))
        resposta = self.client.get(reverse("campanha-detalhe", args=[contribuicao.campanha_id]))
        self.assertContains(resposta, "150,00%")

    def test_total_sem_anotacao_acompanha_confirmacao_posterior(self):
        campanha = self.campanhas["dinheiro"]
        self.assertEqual(campanha.total_confirmado, 0)
        contribuicao = self.criar()
        self.assertEqual(campanha.total_confirmado, 0)
        avaliar_contribuicao(contribuicao.pk, self.dono, "confirmar")
        self.assertEqual(campanha.total_confirmado, Decimal("10.25"))
        self.assertEqual(campanha.percentual_meta, Decimal("10.25"))

    def test_tipo_unidade_imutaveis_inclusive_apos_cancelamento(self):
        contribuicao = self.criar("item")
        for cancelar in (False, True):
            if cancelar:
                cancelar_contribuicao(contribuicao.pk, self.autor)
            for dados in ({"tipo": "horas", "unidade": "hora"}, {"unidade": "pacote"}):
                campanha = Campanha.objects.get(pk=contribuicao.campanha_id)
                form = CampanhaForm({**model_to_dict(campanha), **dados}, instance=campanha)
                with self.subTest(cancelada=cancelar, dados=dados):
                    self.assertFalse(form.is_valid())
                    self.assertIn("unidade", form.errors)
            self.client.force_login(self.dono)
            campanha = Campanha.objects.get(pk=contribuicao.campanha_id)
            resposta = self.client.post(reverse("campanha-editar", args=[campanha.pk]), {**model_to_dict(campanha), "unidade": "pacote"})
            self.assertContains(resposta, "não podem mudar")
            campanha.refresh_from_db()
            self.assertEqual(campanha.unidade, "cesta")
        with self.assertRaises(ProtectedError):
            campanha.delete()

    def test_anonimo_vai_ao_login_e_volta(self):
        contribuicao = self.criar()
        for nome, argumentos, metodo in (
            ("contribuicao-criar", [contribuicao.campanha_id], "get"), ("contribuicao-minhas", [], "get"),
            ("contribuicao-painel", [], "get"), ("contribuicao-editar", [contribuicao.pk], "get"),
            ("contribuicao-cancelar", [contribuicao.pk], "post"), ("contribuicao-avaliar", [contribuicao.pk], "post"),
        ):
            url = reverse(nome, args=argumentos)
            with self.subTest(nome=nome):
                self.assertRedirects(getattr(self.client, metodo)(url), f"{reverse('login')}?next={url}")

    def test_formularios_exibem_medida_textos_e_ignoram_campos_proibidos(self):
        self.client.force_login(self.autor)
        for tipo in Campanha.Tipo.values:
            url = reverse("contribuicao-criar", args=[self.campanhas[tipo].pk])
            resposta = self.client.get(url)
            campo = "valor" if tipo == "dinheiro" else "quantidade"
            self.assertContains(resposta, f'name="{campo}"')
            self.assertNotContains(resposta, f'name="{"quantidade" if tipo == "dinheiro" else "valor"}"')
            self.assertContains(resposta, "Não informe dados bancários ou pessoais sensíveis.")
            self.assertContains(resposta, "A plataforma não processa pagamentos. Transfira pelo meio informado pela ONG e registre aqui o valor." if tipo == "dinheiro" else "Oferecer itens" if tipo == "item" else "Oferecer horas")
            self.assertRedirects(self.client.post(url, {campo: "2", "status": "confirmada", "autor": self.dono.pk}), reverse("contribuicao-minhas"))
        self.assertEqual(Contribuicao.objects.filter(autor=self.autor, status="declarada").count(), 3)

    def test_outros_usuarios_e_outra_ong_recebem_404(self):
        contribuicao = self.criar()
        for usuario in (self.outro, self.dono):
            self.client.force_login(usuario)
            self.assertEqual(self.client.get(reverse("contribuicao-editar", args=[contribuicao.pk])).status_code, 404)
            self.assertEqual(self.client.post(reverse("contribuicao-editar", args=[contribuicao.pk]), {"valor": "99"}).status_code, 404)
            self.assertEqual(self.client.post(reverse("contribuicao-cancelar", args=[contribuicao.pk])).status_code, 404)
        for usuario in (self.outro, self.autor):
            self.client.force_login(usuario)
            self.assertEqual(self.client.post(reverse("contribuicao-avaliar", args=[contribuicao.pk]), {"acao": "confirmar"}).status_code, 404)
        self.client.force_login(self.outro)
        self.assertNotContains(self.client.get(reverse("contribuicao-painel")), self.autor.email)

    def test_contato_aparece_so_para_responsavel(self):
        self.criar()
        self.client.force_login(self.dono)
        resposta = self.client.get(reverse("contribuicao-painel"))
        self.assertContains(resposta, self.autor.first_name)
        self.assertContains(resposta, self.autor.email)
        self.client.force_login(self.autor)
        for url in (reverse("contribuicao-minhas"), reverse("campanha-detalhe", args=[self.campanhas["dinheiro"].pk]), reverse("campanha-lista")):
            resposta = self.client.get(url)
            self.assertNotContains(resposta, self.autor.email)
            self.assertNotContains(resposta, self.autor.first_name)

    def test_botao_contribuir_depende_de_disponibilidade_e_dono(self):
        campanha = self.campanhas["dinheiro"]
        url = reverse("campanha-detalhe", args=[campanha.pk])
        self.assertContains(self.client.get(url), "Contribuir")
        self.client.force_login(self.dono)
        self.assertNotContains(self.client.get(url), "Contribuir")
        self.client.force_login(self.autor)
        Campanha.objects.filter(pk=campanha.pk).update(status="pausada")
        self.assertNotContains(self.client.get(url), "Contribuir")
        self.assertEqual(self.client.get(reverse("contribuicao-criar", args=[campanha.pk])).status_code, 404)

    def test_acoes_so_post_com_csrf(self):
        contribuicao = self.criar()
        for nome, usuario in (("contribuicao-cancelar", self.autor), ("contribuicao-avaliar", self.dono)):
            self.client.force_login(usuario)
            url = reverse(nome, args=[contribuicao.pk])
            self.assertEqual(self.client.get(url).status_code, 405)
            cliente = Client(enforce_csrf_checks=True)
            cliente.force_login(usuario)
            self.assertEqual(cliente.post(url, {"acao": "confirmar"}).status_code, 403)
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.autor)
        for nome, pk in (("contribuicao-criar", contribuicao.campanha_id), ("contribuicao-editar", contribuicao.pk)):
            self.assertEqual(cliente.post(reverse(nome, args=[pk]), {"valor": "10"}).status_code, 403)

    def test_edicao_cancelamento_e_avaliacao_pelas_telas(self):
        contribuicao = self.criar("item")
        self.client.force_login(self.autor)
        url = reverse("contribuicao-editar", args=[contribuicao.pk])
        self.assertContains(self.client.post(url, {"quantidade": "1.5"}), "deve ser inteira")
        self.assertRedirects(self.client.post(url, {"quantidade": "3", "observacao": "Alterada"}), reverse("contribuicao-minhas"))
        self.client.force_login(self.dono)
        url = reverse("contribuicao-avaliar", args=[contribuicao.pk])
        self.assertContains(self.client.post(url, {"acao": "confirmar"}, follow=True), "não é permitida")
        self.assertContains(self.client.post(url, {"acao": "aceitar"}, follow=True), "Contribuição analisada.")
        self.client.force_login(self.autor)
        self.assertRedirects(self.client.post(reverse("contribuicao-cancelar", args=[contribuicao.pk])), reverse("contribuicao-minhas"))
        contribuicao.refresh_from_db()
        self.assertEqual(contribuicao.status, "cancelada")
        self.assertIsNotNone(contribuicao.avaliada_em)

    def test_lista_autor_filtra_pagina_e_mostra_instrucoes(self):
        for estado in Contribuicao.Status.values:
            self.preparar_estado("item", estado)
        for indice in range(21):
            self.criar(observacao=f"Contribuição {indice}")
        self.client.force_login(self.autor)
        resposta = self.client.get(reverse("contribuicao-minhas"), {"tipo": "dinheiro"})
        self.assertEqual(resposta.context["pagina"].paginator.count, 21)
        self.assertEqual(len(resposta.context["pagina"]), 20)
        self.assertContains(resposta, "tipo=dinheiro&amp;page=2")
        resposta = self.client.get(reverse("contribuicao-minhas"), {"tipo": "item"})
        for texto in ("Aguardando análise", "Combine a realização com a ONG", "Confirmada", "Recusada", "Cancelada", "Sem disponibilidade"):
            self.assertContains(resposta, texto)
        for estado in Contribuicao.Status.values:
            self.assertEqual(self.client.get(reverse("contribuicao-minhas"), {"tipo": "item", "status": estado}).context["pagina"].paginator.count, 1)
        self.assertEqual(self.client.get(reverse("contribuicao-minhas"), {"status": "invalido"}).context["pagina"].paginator.count, 0)

    def test_painel_filtra_e_padrao_mostra_declaradas_e_aceitas(self):
        for estado in Contribuicao.Status.values:
            self.preparar_estado("item", estado)
        self.criar()
        self.client.force_login(self.dono)
        url = reverse("contribuicao-painel")
        self.assertEqual(self.client.get(url).context["pagina"].paginator.count, 3)
        self.assertEqual(self.client.get(url, {"status": "todos"}).context["pagina"].paginator.count, 6)
        filtros = {"tipo": "item", "status": "confirmada", "campanha": self.campanhas["item"].pk}
        self.assertEqual(self.client.get(url, filtros).context["pagina"].paginator.count, 1)
        self.assertEqual(self.client.get(url, {"tipo": "invalido"}).context["pagina"].paginator.count, 0)
        self.client.force_login(self.autor)
        self.assertRedirects(self.client.get(url), reverse("ong-nova"))

    def test_listas_sem_consultas_por_contribuicao_ou_campanha(self):
        for quantidade in (1, 8):
            for indice in range(quantidade):
                self.criar()
                Campanha.objects.create(ong=self.ong, **dados_campanha(titulo=f"Outra {quantidade} {indice}"), status="ativa")
            self.client.logout()
            with self.assertNumQueries(2):
                self.client.get(reverse("campanha-lista"))
            self.client.force_login(self.autor)
            with self.assertNumQueries(4):
                self.client.get(reverse("contribuicao-minhas"))
            self.client.force_login(self.dono)
            with self.assertNumQueries(6):
                self.client.get(reverse("contribuicao-painel"))


class ConcorrenciaContribuicaoTests(TransactionTestCase):
    def setUp(self):
        self.dono, self.autor, self.ong, self.campanhas = preparar_campanhas()

    def disputar(self, tipo, acoes):
        contribuicao = criar_contribuicao(self.autor, self.campanhas[tipo], {"valor": "10"} if tipo == "dinheiro" else {"quantidade": "2"})
        if tipo != "dinheiro":
            avaliar_contribuicao(contribuicao.pk, self.dono, "aceitar")
        barreira = Barrier(2)

        def executar(acao):
            close_old_connections()
            try:
                barreira.wait(timeout=10)
                if acao == "cancelar":
                    cancelar_contribuicao(contribuicao.pk, self.autor)
                else:
                    avaliar_contribuicao(contribuicao.pk, self.dono, "confirmar")
            except ConflitoEstado:
                return "conflito"
            else:
                return acao
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados = list(executor.map(executar, acoes))
        contribuicao.refresh_from_db()
        self.assertEqual(resultados.count("conflito"), 1)
        vencedora = next(resultado for resultado in resultados if resultado != "conflito")
        self.assertEqual(contribuicao.status, "cancelada" if vencedora == "cancelar" else "confirmada")
        campanha = anotar_totais(Campanha.objects.filter(pk=contribuicao.campanha_id)).get()
        self.assertEqual(campanha.total_confirmado, (Decimal("10") if tipo == "dinheiro" else Decimal("2")) if vencedora == "confirmar" else Decimal("0"))

    def test_duas_confirmacoes_simultaneas_so_uma_vence(self):
        for tipo in Campanha.Tipo.values:
            with self.subTest(tipo=tipo):
                self.disputar(tipo, ("confirmar", "confirmar"))

    def test_cancelar_e_confirmar_simultaneos_so_uma_vence(self):
        for tipo in Campanha.Tipo.values:
            with self.subTest(tipo=tipo):
                self.disputar(tipo, ("cancelar", "confirmar"))
