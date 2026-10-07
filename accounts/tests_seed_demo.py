import os
import secrets
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models.deletion import ProtectedError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from campaigns.models import Campanha
from contributions.models import Contribuicao
from organizations.models import Ong, Postagem
from organizations.tests import dados_ong
from reports.consulta import consultar_relatorio

from .management.commands.seed_demo import USUARIOS
from .models import User


@override_settings(DEBUG=True, PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class SeedDemoTests(TestCase):
    def setUp(self):
        self.senha = secrets.token_urlsafe(24)
        self.ambiente = patch.dict(os.environ, {"DEMO_PASSWORD": self.senha})
        self.ambiente.start()
        self.addCleanup(self.ambiente.stop)

    def executar(self, *argumentos):
        saida = StringIO()
        call_command("seed_demo", *argumentos, stdout=saida)
        return saida.getvalue()

    def contagens(self):
        return [modelo.objects.count() for modelo in (User, Ong, Campanha, Postagem, Contribuicao)]

    def test_cria_dados_esperados_e_validos(self):
        self.executar()
        self.assertEqual(self.contagens(), [6, 3, 5, 3, 8])
        self.assertTrue(User.objects.get(username="admin_demo").is_staff)
        self.assertEqual(User.objects.filter(is_staff=True).count(), 1)
        self.assertEqual(Ong.objects.filter(status="aprovada").count(), 2)
        self.assertEqual(Ong.objects.filter(status="pendente").count(), 1)
        self.assertEqual(set(Campanha.objects.values_list("tipo", flat=True)), set(Campanha.Tipo.values))
        self.assertEqual(set(Campanha.objects.values_list("status", flat=True)), set(Campanha.Status.values))
        self.assertEqual(set(Contribuicao.objects.values_list("status", flat=True)), set(Contribuicao.Status.values))
        self.assertEqual(Postagem.objects.filter(publicada=False).count(), 1)
        for modelo in (User, Ong, Campanha, Postagem, Contribuicao):
            for registro in modelo.objects.all():
                registro.full_clean()
        self.assertTrue(Contribuicao.objects.get(status="recusada").motivo_avaliacao)

    def test_idempotente_preserva_contagens_ids_e_estados(self):
        self.executar()
        antes = self.contagens()
        ids = list(Contribuicao.objects.values_list("pk", "status"))
        self.executar()
        self.assertEqual(self.contagens(), antes)
        self.assertEqual(list(Contribuicao.objects.values_list("pk", "status")), ids)

    def test_limpar_remove_so_demo_e_pode_repetir(self):
        usuario = User.objects.create_user("independente", "independente@example.org")
        ong = Ong.objects.create(responsavel=usuario, **dados_ong(cep="01001000"))
        self.executar()
        self.executar("--limpar")
        self.executar("--limpar")
        self.assertEqual(self.contagens(), [1, 1, 0, 0, 0])
        self.assertTrue(User.objects.filter(pk=usuario.pk).exists())
        self.assertTrue(Ong.objects.filter(pk=ong.pk).exists())

    def test_limpar_nao_apaga_dependencias_externas_e_reverte_transacao(self):
        self.executar()
        postagem = Postagem.objects.create(
            ong=Ong.objects.get(responsavel__username="ong_df_demo"),
            titulo="Postagem criada à parte", conteudo="Dados independentes",
        )
        antes = self.contagens()
        with self.assertRaises(ProtectedError):
            self.executar("--limpar")
        self.assertEqual(self.contagens(), antes)
        self.assertTrue(Postagem.objects.filter(pk=postagem.pk).exists())

    @override_settings(DEBUG=False)
    def test_recusa_sem_debug_inclusive_limpeza(self):
        for argumentos in ((), ("--limpar",)):
            with self.subTest(argumentos=argumentos), self.assertRaisesMessage(CommandError, "O seed exige DEBUG=true"):
                self.executar(*argumentos)
        self.assertEqual(self.contagens(), [0, 0, 0, 0, 0])

    @override_settings(DEBUG=False)
    def test_permite_producao_apenas_com_argumento(self):
        self.executar("--permitir-producao")
        self.assertEqual(self.contagens(), [6, 3, 5, 3, 8])

    def test_senha_do_ambiente_em_hash_e_nunca_na_saida(self):
        for _ in range(2):
            self.assertNotIn(self.senha, self.executar())
        for usuario in User.objects.all():
            self.assertNotEqual(usuario.password, self.senha)
            self.assertTrue(usuario.check_password(self.senha))
        self.assertNotIn(self.senha, self.executar("--limpar"))

    def test_senha_gerada_aparece_uma_vez_e_funciona(self):
        with patch.dict(os.environ, {}, clear=True), patch(
            "accounts.management.commands.seed_demo.secrets.token_urlsafe", return_value=self.senha,
        ) as gerar:
            saida = self.executar()
        gerar.assert_called_once_with(24)
        self.assertEqual(saida.count(self.senha), 1)
        for usuario in User.objects.all():
            self.assertTrue(usuario.check_password(self.senha))

    def test_colisao_de_username_nao_modifica_conta_ou_cria_demo(self):
        usuario = User.objects.create_user(USUARIOS[0], "conta-independente@example.org")
        for argumentos in ((), ("--limpar",)):
            with self.subTest(argumentos=argumentos), self.assertRaises(CommandError):
                self.executar(*argumentos)
        self.assertEqual(self.contagens(), [1, 0, 0, 0, 0])
        usuario.refresh_from_db()
        self.assertFalse(usuario.is_staff)

    def test_falha_reverte_todos_os_dados_sem_imprimir_senha(self):
        saida = StringIO()
        with patch("accounts.management.commands.seed_demo.criar_contribuicao", side_effect=ValueError("Falha de teste")):
            with self.assertRaises(ValueError):
                call_command("seed_demo", stdout=saida)
        self.assertEqual(self.contagens(), [0, 0, 0, 0, 0])
        self.assertNotIn(self.senha, saida.getvalue())

    def test_totais_confirmados_aparecem_na_campanha_e_relatorio(self):
        self.executar()
        totais = {"dinheiro": [Decimal("150"), Decimal("80")], "item": [Decimal("3")], "horas": [Decimal("2.5")]}
        for tipo, valores in totais.items():
            campanhas = Campanha.objects.filter(tipo=tipo).exclude(status="rascunho").order_by("pk")
            self.assertEqual([campanha.total_confirmado for campanha in campanhas], valores)
        hoje = timezone.localdate()
        linhas = consultar_relatorio(Ong.objects.get(responsavel__username="ong_df_demo"), {"inicio": hoje, "fim": hoje})
        self.assertEqual(sum(linha["confirmadas"] for linha in linhas), 2)
        resposta = self.client.get(reverse("campanha-lista"))
        self.assertContains(resposta, "R$ 150,00")
        self.assertContains(resposta, "3 cestas")
        self.assertContains(resposta, "2,5 horas")

    def test_pendente_e_rascunhos_nao_aparecem_nas_listas_publicas(self):
        self.executar()
        pendente = Ong.objects.get(status="pendente")
        self.assertNotContains(self.client.get(reverse("ong-lista")), pendente.nome)
        self.assertEqual(self.client.get(reverse("ong-detalhe", args=[pendente.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("campanha-lista")), Campanha.objects.get(status="rascunho").titulo)
        self.assertNotContains(self.client.get(reverse("postagem-lista")), Postagem.objects.get(publicada=False).titulo)
