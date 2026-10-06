from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from campaigns.models import Campanha
from campaigns.tests import dados_campanha

from .models import Ong, Postagem
from .postagens import PostagemForm
from .tests import dados_ong


class PostagemTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dono = User.objects.create_user("dono", "dono@example.org")
        cls.outro = User.objects.create_user("outro", "outro@example.org")
        cls.sem_ong = User.objects.create_user("semong", "semong@example.org")
        cls.admin = User.objects.create_user("equipe", "equipe@example.org", is_staff=True)
        cls.ong = Ong.objects.create(
            responsavel=cls.dono, **dados_ong(cep="01001000"),
            status="aprovada", analisada_por=cls.admin, analisada_em=timezone.now(),
        )
        cls.pendente = Ong.objects.create(responsavel=cls.outro, **dados_ong(nome="ONG pendente", cep="01001000"))
        cls.campanha = Campanha.objects.create(ong=cls.ong, **dados_campanha(), status="ativa")
        cls.rascunho = Campanha.objects.create(ong=cls.ong, **dados_campanha(titulo="Campanha secreta"))
        cls.postagem = Postagem.objects.create(ong=cls.ong, titulo="Notícias da praça", conteudo="Apoio à comunidade")

    def dados_formulario(self, **alteracoes):
        dados = {"titulo": "Notícias da praça", "conteudo": "Apoio à comunidade", "campanha": ""}
        dados.update(alteracoes)
        return dados

    def deixar_ong_pendente(self):
        Ong.objects.filter(pk=self.ong.pk).update(status="pendente", analisada_por=None, analisada_em=None)

    def test_dono_cria_edita_publica_e_exclui(self):
        self.client.force_login(self.dono)
        self.assertContains(self.client.get(reverse("postagem-nova")), 'for="id_conteudo"')
        resposta = self.client.post(reverse("postagem-nova"), self.dados_formulario(titulo="Nova", ong=self.pendente.pk, campanha=self.campanha.pk))
        self.assertRedirects(resposta, reverse("postagem-painel"))
        nova = Postagem.objects.get(titulo="Nova")
        self.assertEqual(nova.ong, self.ong)
        self.assertFalse(nova.publicada)
        url = reverse("postagem-editar", args=[nova.pk])
        self.assertContains(self.client.get(url), "Nova")
        self.assertRedirects(self.client.post(url, self.dados_formulario(titulo="Editada", publicada="on", campanha=self.campanha.pk)), reverse("postagem-painel"))
        nova.refresh_from_db()
        self.assertEqual(nova.titulo, "Editada")
        self.assertTrue(nova.publicada)
        url = reverse("postagem-excluir", args=[nova.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url), reverse("postagem-painel"))
        self.assertFalse(Postagem.objects.filter(pk=nova.pk).exists())

    def test_campanha_de_outra_ong_rejeitada_no_modelo_e_formulario(self):
        outra = Campanha.objects.create(ong=self.pendente, **dados_campanha(titulo="Outra campanha"))
        with self.assertRaises(ValidationError) as erro:
            Postagem(ong=self.ong, campanha=outra, titulo="Título", conteudo="Texto").full_clean()
        self.assertIn("campanha", erro.exception.message_dict)
        self.client.force_login(self.dono)
        for nome, argumentos in (("postagem-nova", []), ("postagem-editar", [self.postagem.pk])):
            with self.subTest(nome=nome):
                resposta = self.client.post(reverse(nome, args=argumentos), self.dados_formulario(campanha=outra.pk))
                self.assertEqual(resposta.status_code, 200)
                self.assertIn("campanha", resposta.context["form"].errors)
                self.assertContains(resposta, 'role="alert"')
        self.assertEqual(Postagem.objects.count(), 1)
        self.postagem.refresh_from_db()
        self.assertIsNone(self.postagem.campanha)

    def test_formulario_so_oferece_campanhas_da_ong(self):
        Campanha.objects.create(ong=self.pendente, **dados_campanha())
        form = PostagemForm(instance=self.postagem)
        self.assertCountEqual(form.fields["campanha"].queryset, [self.campanha, self.rascunho])

    def test_publicar_exige_ong_aprovada_no_modelo(self):
        for status in ("pendente", "recusada"):
            self.pendente.status = status
            with self.subTest(status=status), self.assertRaises(ValidationError) as erro:
                Postagem(ong=self.pendente, titulo="Título", conteudo="Texto", publicada=True).full_clean()
            self.assertIn("publicada", erro.exception.message_dict)

    def test_ong_pendente_ve_painel_mas_criar_e_publicar_sao_bloqueados(self):
        self.deixar_ong_pendente()
        self.client.force_login(self.dono)
        self.assertEqual(self.client.get(reverse("postagem-painel")).status_code, 200)
        for metodo in (self.client.get, self.client.post):
            self.assertContains(metodo(reverse("postagem-nova"), self.dados_formulario(), follow=True), "precisa de aprovação")
        resposta = self.client.post(reverse("postagem-editar", args=[self.postagem.pk]), self.dados_formulario(publicada="on"), follow=True)
        self.assertContains(resposta, "precisa de aprovação")
        self.assertEqual(Postagem.objects.count(), 1)
        self.postagem.refresh_from_db()
        self.assertFalse(self.postagem.publicada)

    def test_publicar_com_campanha_rascunho_bloqueado(self):
        with self.assertRaises(ValidationError) as erro:
            Postagem(ong=self.ong, campanha=self.rascunho, titulo="Título", conteudo="Texto", publicada=True).full_clean()
        self.assertIn("campanha", erro.exception.message_dict)
        self.client.force_login(self.dono)
        for nome, argumentos in (("postagem-nova", []), ("postagem-editar", [self.postagem.pk])):
            resposta = self.client.post(reverse(nome, args=argumentos), self.dados_formulario(campanha=self.rascunho.pk, publicada="on"))
            self.assertContains(resposta, "campanha em rascunho")
            self.assertIn("campanha", resposta.context["form"].errors)
        self.postagem.refresh_from_db()
        self.assertFalse(self.postagem.publicada)

    def test_publicar_sem_campanha_ou_com_ativa_pausada_encerrada(self):
        for status in (None, "ativa", "pausada", "encerrada"):
            with self.subTest(status=status):
                if status:
                    self.campanha.status = status
                postagem = Postagem(ong=self.ong, campanha=self.campanha if status else None, titulo="Título", conteudo="Texto", publicada=True)
                postagem.full_clean()

    def test_rascunho_aceita_campanha_rascunho_e_edicao_sem_aprovacao(self):
        self.deixar_ong_pendente()
        self.client.force_login(self.dono)
        resposta = self.client.post(reverse("postagem-editar", args=[self.postagem.pk]), self.dados_formulario(campanha=self.rascunho.pk))
        self.assertRedirects(resposta, reverse("postagem-painel"))
        self.postagem.refresh_from_db()
        self.assertEqual(self.postagem.campanha, self.rascunho)
        self.assertFalse(self.postagem.publicada)

    def test_conteudo_limitado_a_5000_com_erro_no_campo(self):
        self.postagem.conteudo = "a" * 5001
        with self.assertRaises(ValidationError) as erro:
            self.postagem.full_clean()
        self.assertIn("conteudo", erro.exception.message_dict)
        self.client.force_login(self.dono)
        resposta = self.client.post(reverse("postagem-nova"), self.dados_formulario(conteudo="a" * 5001))
        self.assertIn("conteudo", resposta.context["form"].errors)
        self.assertEqual(Postagem.objects.count(), 1)

    def test_lista_publica_so_publicadas_de_aprovadas(self):
        publica = Postagem.objects.create(ong=self.ong, titulo="Notícia pública", conteudo="Texto", publicada=True)
        Postagem.objects.create(ong=self.pendente, titulo="Notícia pendente", conteudo="Texto", publicada=True)
        resposta = self.client.get(reverse("postagem-lista"))
        self.assertEqual(list(resposta.context["pagina"]), [publica])
        self.assertNotContains(resposta, self.postagem.titulo)

    def test_lista_filtra_titulo_conteudo_e_ong(self):
        Postagem.objects.filter(pk=self.postagem.pk).update(publicada=True)
        for filtro in ({"q": "PRAÇA"}, {"q": "comunidade"}, {"ong": self.ong.pk}, {"q": "apoio", "ong": self.ong.pk}):
            with self.subTest(filtro=filtro):
                self.assertEqual(list(self.client.get(reverse("postagem-lista"), filtro).context["pagina"]), [self.postagem])
        resposta = self.client.get(reverse("postagem-lista"), {"q": "ausente"})
        self.assertContains(resposta, "Nenhum resultado para estes filtros")
        self.assertContains(resposta, "Limpar filtros")

    def test_lista_filtra_ong_sem_misturar_outras_aprovadas(self):
        Ong.objects.filter(pk=self.pendente.pk).update(status="aprovada", analisada_por=self.admin, analisada_em=timezone.now())
        outra = Postagem.objects.create(ong=self.pendente, titulo="Outra notícia", conteudo="Texto", publicada=True)
        Postagem.objects.filter(pk=self.postagem.pk).update(publicada=True)
        self.assertEqual(list(self.client.get(reverse("postagem-lista"), {"ong": self.pendente.pk}).context["pagina"]), [outra])

    def test_filtro_invalido_mostra_erro_e_lista_vazia(self):
        Postagem.objects.filter(pk=self.postagem.pk).update(publicada=True)
        for campo, valor in (("q", "a" * 101), ("ong", "invalida"), ("ong", self.pendente.pk), ("ong", 99999)):
            with self.subTest(campo=campo, valor=valor):
                resposta = self.client.get(reverse("postagem-lista"), {campo: valor})
                self.assertIn(campo, resposta.context["form"].errors)
                self.assertEqual(list(resposta.context["pagina"]), [])
                self.assertContains(resposta, 'role="alert"')

    def test_lista_ordena_e_pagina_em_20_preservando_filtros(self):
        publicas = [Postagem.objects.create(ong=self.ong, titulo=f"Notícia {indice}", conteudo="Texto", publicada=True) for indice in range(21)]
        resposta = self.client.get(reverse("postagem-lista"), {"q": "Notícia"})
        self.assertEqual(list(resposta.context["pagina"]), list(reversed(publicas))[:20])
        self.assertEqual(resposta.context["pagina"].paginator.count, 21)
        self.assertContains(resposta, "page=2")
        self.assertIn("q=", resposta.context["filtros"])
        self.assertEqual(len(self.client.get(reverse("postagem-lista"), {"q": "Notícia", "page": 2}).context["pagina"]), 1)

    def test_detalhe_so_publicadas_de_aprovadas_inclusive_para_dono(self):
        pendente = Postagem.objects.create(ong=self.pendente, titulo="Notícia pendente", conteudo="Texto", publicada=True)
        for usuario in (None, self.dono, self.outro, self.admin):
            if usuario:
                self.client.force_login(usuario)
            for postagem in (self.postagem, pendente):
                with self.subTest(usuario=usuario, postagem=postagem.pk):
                    self.assertEqual(self.client.get(reverse("postagem-detalhe", args=[postagem.pk])).status_code, 404)
        Postagem.objects.filter(pk=self.postagem.pk).update(publicada=True)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("postagem-detalhe", args=[self.postagem.pk])).status_code, 200)

    def test_conteudo_html_escapado_no_detalhe_e_listas(self):
        Postagem.objects.filter(pk=self.postagem.pk).update(publicada=True, conteudo='<script>alert("teste")</script>')
        for nome, argumentos in (("postagem-detalhe", [self.postagem.pk]), ("postagem-lista", []), ("ong-detalhe", [self.ong.pk])):
            with self.subTest(nome=nome):
                resposta = self.client.get(reverse(nome, args=argumentos))
                self.assertContains(resposta, "&lt;script&gt;")
                self.assertNotContains(resposta, "<script>")

    def test_detalhe_ong_lista_campanhas_e_postagens_publicas_sem_rascunhos(self):
        publicada = Postagem.objects.create(ong=self.ong, titulo="Postagem pública", conteudo="Texto", publicada=True)
        for status in ("pausada", "encerrada"):
            Campanha.objects.create(ong=self.ong, **dados_campanha(titulo=f"Campanha {status}"), status=status)
        for usuario in (None, self.dono):
            if usuario:
                self.client.force_login(usuario)
            resposta = self.client.get(reverse("ong-detalhe", args=[self.ong.pk]))
            for texto in (self.campanha.titulo, publicada.titulo, "Campanha pausada", "Campanha encerrada"):
                self.assertContains(resposta, texto)
            self.assertNotContains(resposta, self.rascunho.titulo)
            self.assertNotContains(resposta, self.postagem.titulo)
        self.deixar_ong_pendente()
        resposta = self.client.get(reverse("ong-detalhe", args=[self.ong.pk]))
        self.assertEqual(list(resposta.context["campanhas"]), [])
        self.assertEqual(list(resposta.context["postagens"]), [])

    def test_painel_so_mostra_postagens_da_ong_inclusive_rascunhos(self):
        Postagem.objects.create(ong=self.pendente, titulo="De outra ONG", conteudo="Texto")
        publicada = Postagem.objects.create(ong=self.ong, titulo="Publicada", conteudo="Texto", publicada=True)
        self.client.force_login(self.dono)
        resposta = self.client.get(reverse("postagem-painel"))
        self.assertEqual(list(resposta.context["postagens"]), [publicada, self.postagem])
        self.assertContains(resposta, "Rascunho")
        self.assertContains(resposta, "Publicada")

    def test_outro_usuario_nao_edita_nem_exclui(self):
        self.client.force_login(self.outro)
        url = reverse("postagem-editar", args=[self.postagem.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, self.dados_formulario()).status_code, 404)
        self.assertEqual(self.client.post(reverse("postagem-excluir", args=[self.postagem.pk])).status_code, 404)
        self.assertTrue(Postagem.objects.filter(pk=self.postagem.pk).exists())

    def test_sem_ong_redireciona_painel_e_criacao(self):
        self.client.force_login(self.sem_ong)
        for nome in ("postagem-painel", "postagem-nova"):
            self.assertRedirects(self.client.get(reverse(nome)), reverse("ong-nova"))

    def test_anonimo_redirecionado_ao_login(self):
        for nome, argumentos, metodo in (("postagem-painel", [], "get"), ("postagem-nova", [], "get"), ("postagem-editar", [self.postagem.pk], "get"), ("postagem-excluir", [self.postagem.pk], "post")):
            with self.subTest(nome=nome):
                url = reverse(nome, args=argumentos)
                self.assertRedirects(getattr(self.client, metodo)(url), f"{reverse('login')}?next={url}")

    def test_excluir_campanha_desvincula_postagem_e_ong_e_protegida(self):
        self.postagem.campanha = self.campanha
        self.postagem.save()
        self.campanha.delete()
        self.postagem.refresh_from_db()
        self.assertIsNone(self.postagem.campanha)
        with self.assertRaises(ProtectedError):
            self.ong.delete()

    def test_painel_conta_tem_links_e_navegacao_publica(self):
        self.client.force_login(self.dono)
        resposta = self.client.get(reverse("painel"))
        for texto in ("Minhas campanhas", "Minhas postagens", "ONGs", "Campanhas"):
            self.assertContains(resposta, texto)
        self.client.force_login(self.sem_ong)
        resposta = self.client.get(reverse("painel"))
        self.assertNotContains(resposta, "Minhas campanhas")
        self.assertNotContains(resposta, "Minhas postagens")

    def test_acoes_exigem_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.dono)
        for nome, argumentos in (("postagem-nova", []), ("postagem-editar", [self.postagem.pk]), ("postagem-excluir", [self.postagem.pk])):
            self.assertEqual(cliente.post(reverse(nome, args=argumentos), self.dados_formulario()).status_code, 403)
