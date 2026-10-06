from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.forms.models import model_to_dict
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from organizations.models import Ong
from organizations.tests import dados_ong

from .forms import CampanhaForm
from .models import Campanha
from .services import ConflitoEstado, mudar_estado


def dados_campanha(**alteracoes):
    hoje = timezone.localdate()
    dados = {
        "titulo": "Cestas para famílias", "descricao": "Alimentos para a comunidade",
        "tipo": "item", "unidade": "cesta", "meta": Decimal("100.00"),
        "data_inicio": hoje, "data_fim": hoje + timedelta(days=10),
    }
    dados.update(alteracoes)
    return dados


class CampanhaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dono = User.objects.create_user("dono", "dono@example.org")
        cls.outro = User.objects.create_user("outro", "outro@example.org")
        cls.sem_ong = User.objects.create_user("semong", "semong@example.org")
        cls.admin = User.objects.create_user("equipe", "equipe@example.org", is_staff=True)
        cls.ong = Ong.objects.create(
            responsavel=cls.dono, **dados_ong(cep="01001000"),
            status=Ong.Status.APROVADA, analisada_por=cls.admin, analisada_em=timezone.now(),
        )
        cls.pendente = Ong.objects.create(responsavel=cls.outro, **dados_ong(cep="01001000", nome="ONG pendente"))
        cls.campanha = Campanha.objects.create(ong=cls.ong, **dados_campanha())

    def dados_formulario(self, **alteracoes):
        dados = model_to_dict(self.campanha, fields=CampanhaForm.Meta.fields)
        dados.update(alteracoes)
        return dados

    def deixar_ong_pendente(self):
        Ong.objects.filter(pk=self.ong.pk).update(status="pendente", analisada_por=None, analisada_em=None)

    def test_validacao_rejeita_meta_nao_positiva(self):
        for meta in (Decimal("0"), Decimal("-1")):
            with self.subTest(meta=meta), self.assertRaises(ValidationError) as erro:
                Campanha(ong=self.ong, **dados_campanha(meta=meta)).full_clean()
            self.assertIn("meta", erro.exception.message_dict)

    def test_validacao_rejeita_datas_invertidas(self):
        with self.assertRaises(ValidationError) as erro:
            Campanha(ong=self.ong, **dados_campanha(data_fim=timezone.localdate() - timedelta(days=1))).full_clean()
        self.assertIn("data_fim", erro.exception.message_dict)

    def test_validacao_exige_unidade_do_tipo(self):
        for tipo, unidade in (("dinheiro", "real"), ("dinheiro", "brl"), ("horas", "horas")):
            with self.subTest(tipo=tipo, unidade=unidade), self.assertRaises(ValidationError) as erro:
                Campanha(ong=self.ong, **dados_campanha(tipo=tipo, unidade=unidade)).full_clean()
            self.assertIn("unidade", erro.exception.message_dict)

    def test_meta_item_inteira_e_dinheiro_horas_fracionados(self):
        with self.assertRaises(ValidationError) as erro:
            Campanha(ong=self.ong, **dados_campanha(meta=Decimal("1.50"))).full_clean()
        self.assertIn("meta", erro.exception.message_dict)
        for tipo, unidade, meta in (("item", "cesta", "2.00"), ("horas", "hora", "1.25"), ("dinheiro", "BRL", "0.01")):
            with self.subTest(tipo=tipo):
                Campanha(ong=self.ong, **dados_campanha(tipo=tipo, unidade=unidade, meta=Decimal(meta))).full_clean()

    def test_descricao_tem_limite_e_meta_tem_duas_casas(self):
        for campo, valor in (("descricao", "a" * 5001), ("meta", Decimal("1.001"))):
            with self.subTest(campo=campo), self.assertRaises(ValidationError) as erro:
                Campanha(ong=self.ong, **dados_campanha(**{campo: valor})).full_clean()
            self.assertIn(campo, erro.exception.message_dict)

    def test_constraints_do_banco_rejeitam_meta_e_datas(self):
        for alteracoes in ({"meta": 0}, {"meta": -1}, {"data_fim": timezone.localdate() - timedelta(days=1)}):
            with self.subTest(alteracoes=alteracoes), self.assertRaises(IntegrityError):
                with transaction.atomic():
                    Campanha.objects.filter(pk=self.campanha.pk).update(**alteracoes)
        self.campanha.refresh_from_db()
        self.assertEqual(self.campanha.meta, Decimal("100"))

    def test_formulario_criacao_rejeita_fim_no_passado(self):
        ontem = timezone.localdate() - timedelta(days=1)
        form = CampanhaForm(dados_campanha(data_inicio=ontem, data_fim=ontem))
        self.assertFalse(form.is_valid())
        self.assertIn("data_fim", form.errors)

    def test_formulario_edicao_permite_campanha_vencida_e_rejeita_datas_invertidas(self):
        ontem = timezone.localdate() - timedelta(days=1)
        self.assertTrue(CampanhaForm(self.dados_formulario(data_inicio=ontem, data_fim=ontem), instance=self.campanha).is_valid())
        form = CampanhaForm(self.dados_formulario(data_inicio=timezone.localdate(), data_fim=ontem), instance=self.campanha)
        self.assertFalse(form.is_valid())
        self.assertIn("data_fim", form.errors)

    def test_transicoes_validas(self):
        for acao, status in (("publicar", "ativa"), ("pausar", "pausada"), ("reativar", "ativa"), ("encerrar", "encerrada")):
            with self.subTest(acao=acao):
                resultado = mudar_estado(self.campanha, acao)
                self.campanha.refresh_from_db()
                self.assertEqual(resultado.status, status)
                self.assertEqual(self.campanha.status, status)

    def test_encerrar_pausada(self):
        mudar_estado(self.campanha, "publicar")
        mudar_estado(self.campanha, "pausar")
        self.assertEqual(mudar_estado(self.campanha, "encerrar").status, "encerrada")

    def test_transicoes_invalidas_e_encerrada_terminal(self):
        permitidas = {"rascunho": {"publicar"}, "ativa": {"pausar", "encerrar"}, "pausada": {"reativar", "encerrar"}, "encerrada": set()}
        for status, acoes in permitidas.items():
            Campanha.objects.filter(pk=self.campanha.pk).update(status=status)
            for acao in ("publicar", "pausar", "reativar", "encerrar", "invalida"):
                if acao not in acoes:
                    with self.subTest(status=status, acao=acao), self.assertRaises(ConflitoEstado):
                        mudar_estado(self.campanha, acao)
            self.campanha.refresh_from_db()
            self.assertEqual(self.campanha.status, status)

    def test_repeticao_verifica_estado_atual_do_banco(self):
        for acao in ("publicar", "pausar", "reativar", "encerrar"):
            mudar_estado(self.campanha, acao)
            with self.subTest(acao=acao), self.assertRaises(ConflitoEstado):
                mudar_estado(self.campanha, acao)

    def test_publicar_e_reativar_exigem_aprovacao(self):
        self.deixar_ong_pendente()
        for status, acao in (("rascunho", "publicar"), ("pausada", "reativar")):
            Campanha.objects.filter(pk=self.campanha.pk).update(status=status)
            with self.subTest(acao=acao), self.assertRaisesMessage(ConflitoEstado, "precisa de aprovação"):
                mudar_estado(self.campanha, acao)
            self.campanha.refresh_from_db()
            self.assertEqual(self.campanha.status, status)

    def test_publicar_e_reativar_exigem_prazo_e_aceitam_ultimo_dia(self):
        for status, acao in (("rascunho", "publicar"), ("pausada", "reativar")):
            Campanha.objects.filter(pk=self.campanha.pk).update(status=status)
            with self.subTest(acao=acao), self.assertRaisesMessage(ConflitoEstado, "passado"):
                mudar_estado(self.campanha, acao, hoje=self.campanha.data_fim + timedelta(days=1))
            self.assertEqual(mudar_estado(self.campanha, acao, hoje=self.campanha.data_fim).status, "ativa")

    def test_pausar_e_encerrar_nao_exigem_aprovacao_ou_prazo(self):
        self.deixar_ong_pendente()
        Campanha.objects.filter(pk=self.campanha.pk).update(status="ativa")
        futuro = self.campanha.data_fim + timedelta(days=1)
        self.assertEqual(mudar_estado(self.campanha, "pausar", futuro).status, "pausada")
        self.assertEqual(mudar_estado(self.campanha, "encerrar", futuro).status, "encerrada")

    def test_disponivel_inclui_bordas_e_exclui_dias_fora(self):
        self.campanha.status = "ativa"
        for dia, esperado in ((self.campanha.data_inicio - timedelta(days=1), False), (self.campanha.data_inicio, True), (self.campanha.data_fim, True), (self.campanha.data_fim + timedelta(days=1), False)):
            with self.subTest(dia=dia), patch("campaigns.models.timezone.localdate", return_value=dia):
                self.assertEqual(self.campanha.disponivel, esperado)
                self.assertEqual(self.campanha.motivo_indisponibilidade, "" if esperado else "Fora do prazo")

    def test_disponivel_exige_ativa_e_ong_aprovada(self):
        for status, motivo in (("rascunho", "Rascunho"), ("pausada", "Pausada"), ("encerrada", "Encerrada")):
            self.campanha.status = status
            self.assertFalse(self.campanha.disponivel)
            self.assertEqual(self.campanha.motivo_indisponibilidade, motivo)
        self.campanha.status = "ativa"
        self.campanha.ong.status = "pendente"
        self.assertFalse(self.campanha.disponivel)
        self.assertEqual(self.campanha.motivo_indisponibilidade, "ONG não aprovada")

    def test_lista_publica_so_aprovadas_sem_rascunho(self):
        publicas = [Campanha.objects.create(ong=self.ong, **dados_campanha(titulo=status), status=status) for status in ("ativa", "pausada", "encerrada")]
        Campanha.objects.create(ong=self.pendente, **dados_campanha(titulo="Oculta"), status="ativa")
        resposta = self.client.get(reverse("campanha-lista"))
        self.assertEqual(list(resposta.context["pagina"]), list(reversed(publicas)))
        self.client.force_login(self.dono)
        self.assertNotContains(self.client.get(reverse("campanha-lista")), self.campanha.titulo)

    def test_lista_respeita_cada_filtro(self):
        Campanha.objects.filter(pk=self.campanha.pk).update(status="ativa")
        filtros = ({"q": "CESTAS"}, {"q": "comunidade"}, {"cidade": "paulo"}, {"bairro": "sé"}, {"uf": "SP"}, {"tipo": "item"}, {"status": "ativa"}, {"disponivel": "on"}, {"q": "cestas", "cidade": "paulo", "bairro": "sé", "uf": "SP", "tipo": "item", "status": "ativa", "disponivel": "on"})
        for filtro in filtros:
            with self.subTest(filtro=filtro):
                self.assertEqual(list(self.client.get(reverse("campanha-lista"), filtro).context["pagina"]), [self.campanha])
        for filtro in ({"q": "ausente"}, {"cidade": "Brasília"}, {"bairro": "Centro"}, {"uf": "DF"}, {"tipo": "horas"}, {"status": "pausada"}):
            with self.subTest(filtro=filtro):
                resposta = self.client.get(reverse("campanha-lista"), filtro)
                self.assertEqual(list(resposta.context["pagina"]), [])
                self.assertContains(resposta, "Nenhum resultado para estes filtros")
                self.assertContains(resposta, "Limpar filtros")

    def test_filtro_disponivel_exclui_pausadas_encerradas_e_fora_do_prazo(self):
        Campanha.objects.filter(pk=self.campanha.pk).update(status="ativa")
        hoje = timezone.localdate()
        for alteracoes in ({"status": "pausada"}, {"status": "encerrada"}, {"data_inicio": hoje + timedelta(days=1)}, {"data_inicio": hoje - timedelta(days=2), "data_fim": hoje - timedelta(days=1)}):
            Campanha.objects.create(ong=self.ong, **dados_campanha(**{"status": "ativa", **alteracoes}))
        resposta = self.client.get(reverse("campanha-lista"), {"disponivel": "on"})
        self.assertEqual(list(resposta.context["pagina"]), [self.campanha])

    def test_filtros_invalidos_mostram_erros_e_lista_vazia(self):
        mudar_estado(self.campanha, "publicar")
        for campo, valor in (("q", "a" * 101), ("cidade", "a" * 101), ("bairro", "a" * 101), ("uf", "XX"), ("tipo", "outro"), ("status", "rascunho"), ("ordenacao", "titulo")):
            with self.subTest(campo=campo):
                resposta = self.client.get(reverse("campanha-lista"), {campo: valor})
                self.assertIn(campo, resposta.context["form"].errors)
                self.assertEqual(list(resposta.context["pagina"]), [])
                self.assertContains(resposta, 'role="alert"')

    def test_lista_ordena_por_criacao_ou_data_fim(self):
        mudar_estado(self.campanha, "publicar")
        nova = Campanha.objects.create(ong=self.ong, **dados_campanha(data_fim=self.campanha.data_fim + timedelta(days=1)), status="ativa")
        self.assertEqual(list(self.client.get(reverse("campanha-lista")).context["pagina"]), [nova, self.campanha])
        self.assertEqual(list(self.client.get(reverse("campanha-lista"), {"ordenacao": "data_fim"}).context["pagina"]), [self.campanha, nova])

    def test_paginacao_em_20_preserva_filtros(self):
        for indice in range(21):
            Campanha.objects.create(ong=self.ong, **dados_campanha(titulo=f"Campanha {indice}"), status="ativa")
        resposta = self.client.get(reverse("campanha-lista"), {"uf": "SP"})
        self.assertEqual(len(resposta.context["pagina"]), 20)
        self.assertEqual(resposta.context["pagina"].paginator.count, 21)
        self.assertContains(resposta, "uf=SP&amp;page=2")
        self.assertEqual(len(self.client.get(reverse("campanha-lista"), {"uf": "SP", "page": 2}).context["pagina"]), 1)

    def test_detalhe_oculto_so_dono_inclusive_staff_recebe_404(self):
        for ong, status in ((self.ong, "rascunho"), (self.pendente, "ativa")):
            campanha = Campanha.objects.create(ong=ong, **dados_campanha(), status=status)
            url = reverse("campanha-detalhe", args=[campanha.pk])
            self.client.logout()
            self.assertEqual(self.client.get(url).status_code, 404)
            for usuario in (self.dono, self.outro, self.admin):
                with self.subTest(ong=ong.pk, usuario=usuario.pk):
                    self.client.force_login(usuario)
                    self.assertEqual(self.client.get(url).status_code, 200 if ong.responsavel_id == usuario.pk else 404)

    def test_detalhe_publico_mostra_dados_recebimento_e_motivo(self):
        mudar_estado(self.campanha, "publicar")
        url = reverse("campanha-detalhe", args=[self.campanha.pk])
        resposta = self.client.get(url)
        for texto in ("Item", "cesta", "100", "Início:", "Fim:", "Ativa", "Disponível hoje", self.ong.instrucoes_recebimento, "Aprovação não garante idoneidade; confira as informações"):
            self.assertContains(resposta, texto)
        for status, motivo in (("pausada", "Pausada"), ("encerrada", "Encerrada")):
            Campanha.objects.filter(pk=self.campanha.pk).update(status=status)
            self.assertContains(self.client.get(url), f"Indisponível: {motivo}")

    def test_criar_e_editar_pelo_dono_sem_alterar_ong_ou_status(self):
        self.client.force_login(self.dono)
        resposta = self.client.get(reverse("campanha-nova"))
        self.assertContains(resposta, 'for="id_titulo"')
        resposta = self.client.post(reverse("campanha-nova"), self.dados_formulario(titulo="Nova", ong=self.pendente.pk, status="ativa"))
        nova = Campanha.objects.get(titulo="Nova")
        self.assertRedirects(resposta, reverse("campanha-detalhe", args=[nova.pk]))
        self.assertEqual(nova.ong, self.ong)
        self.assertEqual(nova.status, "rascunho")
        url = reverse("campanha-editar", args=[nova.pk])
        self.assertContains(self.client.get(url), 'type="date"')
        self.assertEqual(self.client.post(url, self.dados_formulario(titulo="Editada", status="encerrada")).status_code, 302)
        nova.refresh_from_db()
        self.assertEqual(nova.titulo, "Editada")
        self.assertEqual(nova.status, "rascunho")

    def test_formulario_invalido_exibe_erro_sem_criar(self):
        self.client.force_login(self.dono)
        resposta = self.client.post(reverse("campanha-nova"), self.dados_formulario(meta="0"))
        self.assertContains(resposta, "A meta deve ser maior que zero.")
        self.assertEqual(Campanha.objects.count(), 1)

    def test_painel_inclui_rascunhos_so_da_ong_e_filtra_status(self):
        Campanha.objects.create(ong=self.pendente, **dados_campanha(titulo="De outra ONG"))
        ativa = Campanha.objects.create(ong=self.ong, **dados_campanha(titulo="Ativa"), status="ativa")
        self.client.force_login(self.dono)
        resposta = self.client.get(reverse("campanha-painel"))
        self.assertEqual(list(resposta.context["campanhas"]), [ativa, self.campanha])
        self.assertEqual(list(self.client.get(reverse("campanha-painel"), {"status": "rascunho"}).context["campanhas"]), [self.campanha])
        resposta = self.client.get(reverse("campanha-painel"), {"status": "invalido"})
        self.assertIn("status", resposta.context["form"].errors)
        self.assertEqual(list(resposta.context["campanhas"]), [])

    def test_sem_ong_redireciona_painel_e_criacao(self):
        self.client.force_login(self.sem_ong)
        for nome in ("campanha-painel", "campanha-nova"):
            self.assertRedirects(self.client.get(reverse(nome)), reverse("ong-nova"))

    def test_ong_pendente_ve_painel_mas_nao_cria(self):
        self.client.force_login(self.outro)
        self.assertEqual(self.client.get(reverse("campanha-painel")).status_code, 200)
        for metodo in (self.client.get, self.client.post):
            resposta = metodo(reverse("campanha-nova"), self.dados_formulario(), follow=True)
            self.assertContains(resposta, "precisa de aprovação")
        self.assertFalse(self.pendente.campanhas.exists())

    def test_mudar_estado_por_post_mostra_sucesso_ou_conflito(self):
        self.client.force_login(self.dono)
        url = reverse("campanha-estado", args=[self.campanha.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertContains(self.client.post(url, {"acao": "publicar"}, follow=True), "Estado da campanha atualizado.")
        self.assertContains(self.client.post(url, {"acao": "publicar"}, follow=True), "não é permitida")
        self.deixar_ong_pendente()
        mudar_estado(self.campanha, "pausar")
        self.assertContains(self.client.post(url, {"acao": "reativar"}, follow=True), "precisa de aprovação")

    def test_outro_usuario_nao_edita_muda_estado_nem_exclui(self):
        self.client.force_login(self.outro)
        self.assertEqual(self.client.get(reverse("campanha-editar", args=[self.campanha.pk])).status_code, 404)
        for nome, dados in (("campanha-editar", self.dados_formulario()), ("campanha-estado", {"acao": "publicar"}), ("campanha-excluir", {})):
            with self.subTest(nome=nome):
                self.assertEqual(self.client.post(reverse(nome, args=[self.campanha.pk]), dados).status_code, 404)
        self.campanha.refresh_from_db()
        self.assertEqual(self.campanha.status, "rascunho")

    def test_anonimo_redirecionado_ao_login_em_todas_rotas_do_painel(self):
        for nome, argumentos, metodo in (("campanha-painel", [], "get"), ("campanha-nova", [], "get"), ("campanha-editar", [self.campanha.pk], "get"), ("campanha-estado", [self.campanha.pk], "post"), ("campanha-excluir", [self.campanha.pk], "post")):
            with self.subTest(nome=nome):
                url = reverse(nome, args=argumentos)
                self.assertRedirects(getattr(self.client, metodo)(url), f"{reverse('login')}?next={url}")

    def test_exclusao_so_por_post_e_pelo_dono(self):
        self.client.force_login(self.dono)
        url = reverse("campanha-excluir", args=[self.campanha.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url), reverse("campanha-painel"))
        self.assertFalse(Campanha.objects.filter(pk=self.campanha.pk).exists())

    def test_exclusao_protegida_mostra_mensagem(self):
        self.client.force_login(self.dono)
        with patch("campaigns.models.Campanha.delete", side_effect=ProtectedError("Dependência", [self.campanha])):
            resposta = self.client.post(reverse("campanha-excluir", args=[self.campanha.pk]), follow=True)
        self.assertContains(resposta, "há dependências vinculadas")
        self.assertTrue(Campanha.objects.filter(pk=self.campanha.pk).exists())

    def test_acoes_exigem_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.dono)
        for nome, argumentos in (("campanha-nova", []), ("campanha-editar", [self.campanha.pk]), ("campanha-estado", [self.campanha.pk]), ("campanha-excluir", [self.campanha.pk])):
            self.assertEqual(cliente.post(reverse(nome, args=argumentos), self.dados_formulario()).status_code, 403)
