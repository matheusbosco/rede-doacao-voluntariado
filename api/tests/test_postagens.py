from organizations.models import Ong, Postagem

from .base import APITestCase


class PostagensTests(APITestCase):
    dados = {"titulo": "Novidades", "conteudo": "Doações recebidas", "publicada": True}

    def test_publicas_detalhe_e_filtros(self):
        resposta = self.client.get(f"/api/v1/postagens/{self.postagem.pk}/")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["campanha_id"], self.campanha.pk)
        self.assertNotIn("autor", resposta.json())
        for filtros in ({"q": "ações"}, {"ong_id": self.ong.pk}, {"campanha_id": self.campanha.pk}):
            self.assertEqual(self.client.get("/api/v1/postagens/", filtros).json()["count"], 1)
        self.erro(self.client.get(f"/api/v1/postagens/{self.postagem_rascunho.pk}/"), 404, "nao_encontrado")
        Ong.objects.filter(pk=self.ong.pk).update(status="pendente", analisada_por=None, analisada_em=None)
        self.assertEqual(self.client.get("/api/v1/postagens/").json()["count"], 0)
        self.erro(self.client.get(f"/api/v1/postagens/{self.postagem.pk}/"), 404, "nao_encontrado")

    def test_painel_rascunhos_filtro_e_privacidade(self):
        cliente = self.sessao()
        self.assertEqual(cliente.get("/api/v1/painel/postagens/").json()["count"], 2)
        self.assertEqual(cliente.get("/api/v1/painel/postagens/?publicada=false").json()["count"], 1)
        self.assertEqual(cliente.get(f"/api/v1/painel/postagens/{self.postagem_rascunho.pk}/").status_code, 200)
        self.erro(self.sessao(self.outro).get(f"/api/v1/painel/postagens/{self.postagem.pk}/"), 404, "nao_encontrado")
        self.erro(self.sessao(self.sem_ong).get("/api/v1/painel/postagens/"), 404, "nao_encontrado")
        self.erro(self.client.get("/api/v1/painel/postagens/"), 403, "autenticacao_necessaria")

    def test_criar_editar_e_excluir(self):
        cliente = self.sessao()
        resposta = self.mutacao(cliente, "post", "postagens/", {**self.dados, "campanha_id": self.campanha.pk})
        self.assertEqual(resposta.status_code, 201, resposta.content)
        pk = resposta.json()["id"]
        resposta = self.mutacao(cliente, "patch", f"postagens/{pk}/", {"titulo": "Editada", "campanha_id": None})
        self.assertEqual(resposta.status_code, 200, resposta.content)
        self.assertEqual(resposta.json()["titulo"], "Editada")
        self.assertIsNone(resposta.json()["campanha_id"])
        self.assertEqual(self.mutacao(cliente, "delete", f"postagens/{pk}/").status_code, 204)
        self.assertFalse(Postagem.objects.filter(pk=pk).exists())

    def test_campanha_mesma_ong_e_publicacao_fora_rascunho(self):
        cliente = self.sessao()
        for pk in (self.outra_campanha.pk, self.rascunho.pk):
            self.erro(self.mutacao(cliente, "post", "postagens/", {**self.dados, "campanha_id": pk}), 400, "validacao")
        resposta = self.mutacao(cliente, "post", "postagens/", {**self.dados, "campanha_id": self.rascunho.pk, "publicada": False})
        self.assertEqual(resposta.status_code, 201, resposta.content)
        self.erro(self.mutacao(cliente, "patch", f"postagens/{resposta.json()['id']}/", {"publicada": True}), 400, "validacao")

    def test_publicar_e_criar_exige_aprovacao(self):
        self.erro(self.mutacao(self.sessao(self.outro), "post", "postagens/", self.dados), 403, "proibido")
        Ong.objects.filter(pk=self.ong.pk).update(status="pendente", analisada_por=None, analisada_em=None)
        self.erro(self.mutacao(self.sessao(), "patch", f"postagens/{self.postagem_rascunho.pk}/", {"publicada": True}), 400, "validacao", "publicada")
        self.assertEqual(self.mutacao(self.sessao(), "patch", f"postagens/{self.postagem_rascunho.pk}/", {"conteudo": "Revisão"}).status_code, 200)

    def test_campos_protegidos_e_validacao(self):
        cliente = self.sessao()
        for campo, valor in (("ong_id", self.outra_ong.pk), ("autor", 1), ("criada_em", "2020"), ("x", 1), ("conteudo", "a" * 5001)):
            self.erro(self.mutacao(cliente, "patch", f"postagens/{self.postagem.pk}/", {campo: valor}), 400, "validacao", campo)
        self.erro(self.client.get("/api/v1/postagens/?q=" + "a" * 101), 400, "validacao", "q")
        self.erro(cliente.get("/api/v1/painel/postagens/?publicada=talvez"), 400, "validacao", "publicada")

    def test_mutacoes_sessao_csrf_e_propriedade(self):
        for metodo, caminho, dados in (("post", "postagens/", self.dados), ("patch", f"postagens/{self.postagem.pk}/", {"titulo": "Novo"}),
            ("delete", f"postagens/{self.postagem.pk}/", {})):
            with self.subTest(metodo=metodo, caminho=caminho):
                self.erro(self.mutacao(self.client, metodo, caminho, dados), 403, "autenticacao_necessaria")
                self.erro(self.mutacao(self.sessao(csrf=True), metodo, caminho, dados), 403, "csrf_invalido")
                if caminho != "postagens/":
                    self.erro(self.mutacao(self.sessao(self.outro), metodo, caminho, dados), 404, "nao_encontrado")
