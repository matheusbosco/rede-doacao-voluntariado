from unittest.mock import patch

from django.core.cache import cache
from rest_framework.throttling import SimpleRateThrottle
from campaigns.models import Campanha

from .base import APITestCase, dados_campanha


class ContratoTests(APITestCase):
    listas = ("ongs/", "campanhas/", "postagens/", "admin/ongs/", "painel/campanhas/", "painel/postagens/",
        "contribuicoes/", "painel/contribuicoes/")

    def test_paginacao_em_todas_listas(self):
        cliente = self.sessao(self.admin)
        for caminho in self.listas:
            if caminho.startswith("painel/"):
                cliente.force_login(self.dono)
            elif caminho == "admin/ongs/":
                cliente.force_login(self.admin)
            elif caminho == "contribuicoes/":
                cliente.force_login(self.autor)
            else:
                cliente.force_login(self.dono)
            with self.subTest(caminho=caminho):
                resposta = cliente.get(f"/api/v1/{caminho}", {"page_size": 1})
                self.assertEqual(resposta.status_code, 200, resposta.content)
                self.assertEqual(set(resposta.json()), {"count", "next", "previous", "results"})
                self.assertLessEqual(len(resposta.json()["results"]), 1)
                self.erro(cliente.get(f"/api/v1/{caminho}", {"page": 9999}), 404, "nao_encontrado")
                for valor in ("0", "-1", "101", "abc", "1.5", ""):
                    self.erro(cliente.get(f"/api/v1/{caminho}", {"page_size": valor}), 400, "validacao", "page_size")
                cache.clear()

    def test_links_paginacao_e_tamanho_padrao(self):
        primeira = self.client.get("/api/v1/campanhas/?page_size=1").json()
        self.assertIsNone(primeira["previous"])
        segunda = self.client.get(primeira["next"]).json()
        self.assertIsNone(segunda["next"])
        self.assertIsNotNone(segunda["previous"])
        self.assertNotEqual(primeira["results"][0]["id"], segunda["results"][0]["id"])
        for valor in ("0", "-1", "x"):
            self.erro(self.client.get("/api/v1/campanhas/", {"page": valor}), 400, "validacao", "page")

    def test_tamanho_padrao_maximo_e_ordenacao_efetiva(self):
        for indice in range(21):
            Campanha.objects.create(ong=self.ong, status="ativa", **dados_campanha(titulo=f"Campanha {indice:02}"))
        padrao = self.client.get("/api/v1/campanhas/").json()
        self.assertEqual(padrao["count"], 23)
        self.assertEqual(len(padrao["results"]), 20)
        self.assertIsNotNone(padrao["next"])
        todas = self.client.get("/api/v1/campanhas/?page_size=100&ordering=titulo").json()
        self.assertEqual(len(todas["results"]), 23)
        self.assertIsNone(todas["next"])
        titulos = [campanha["titulo"] for campanha in todas["results"]]
        self.assertEqual(titulos, sorted(titulos))

    def test_query_desconhecida_e_ordenacao_invalida_todos_recursos(self):
        for caminho in self.listas:
            cliente = self.sessao(self.admin if caminho == "admin/ongs/" else self.dono)
            with self.subTest(caminho=caminho):
                self.erro(cliente.get(f"/api/v1/{caminho}?x=1"), 400, "validacao", "x")
                self.erro(cliente.get(f"/api/v1/{caminho}?ordering=password"), 400, "validacao", "ordering")
        self.erro(self.client.get("/api/v1/ongs/?q=a&q=b"), 400, "validacao", "q")
        for caminho in (f"ongs/{self.ong.pk}/", f"campanhas/{self.campanha.pk}/", f"postagens/{self.postagem.pk}/", "painel/ong/",
            f"contribuicoes/{self.contribuicao.pk}/", "auth/me/"):
            self.erro(self.sessao().get(f"/api/v1/{caminho}?x=1"), 400, "validacao", "x")

    def test_metodos_nao_oferecidos(self):
        cliente = self.sessao()
        for caminho in (*self.listas, f"ongs/{self.ong.pk}/", f"campanhas/{self.campanha.pk}/", f"postagens/{self.postagem.pk}/",
            f"contribuicoes/{self.contribuicao.pk}/"):
            self.erro(cliente.put(f"/api/v1/{caminho}", {}, format="json"), 405, "metodo_nao_permitido")
        self.erro(cliente.delete(f"/api/v1/contribuicoes/{self.contribuicao.pk}/"), 405, "metodo_nao_permitido")
        for caminho in (f"ongs/{self.ong.pk}/reenviar/", f"campanhas/{self.campanha.pk}/estado/", f"admin/ongs/{self.ong.pk}/analise/",
            f"contribuicoes/{self.contribuicao.pk}/avaliacao/", f"contribuicoes/{self.contribuicao.pk}/cancelar/"):
            self.erro(cliente.get(f"/api/v1/{caminho}"), 405, "metodo_nao_permitido")
        for caminho in ("painel/ong/", "painel/campanhas/", "painel/postagens/", "painel/contribuicoes/"):
            self.erro(cliente.post(f"/api/v1/{caminho}", {}, format="json"), 405, "metodo_nao_permitido")

    def test_corpo_protegido_nas_acoes_e_exclusoes(self):
        for metodo, caminho, dados, usuario in (("post", f"ongs/{self.ong.pk}/reenviar/", {"status": "pendente"}, self.dono),
            ("post", f"campanhas/{self.campanha.pk}/estado/", {"acao": "pausar", "status": "ativa"}, self.dono),
            ("post", f"admin/ongs/{self.outra_ong.pk}/analise/", {"decisao": "aprovar", "status": "aprovada"}, self.admin),
            ("post", f"contribuicoes/{self.contribuicao.pk}/avaliacao/", {"acao": "aceitar", "status": "aceita"}, self.dono),
            ("post", f"contribuicoes/{self.contribuicao.pk}/cancelar/", {"status": "cancelada"}, self.autor),
            ("delete", f"ongs/{self.ong.pk}/", {"status": "pendente"}, self.dono),
            ("delete", f"campanhas/{self.campanha.pk}/", {"status": "ativa"}, self.dono),
            ("delete", f"postagens/{self.postagem.pk}/", {"status": "x"}, self.dono),
            ("post", "auth/logout/", {"status": "x"}, self.dono)):
            self.erro(self.mutacao(self.sessao(usuario), metodo, caminho, dados), 400, "validacao", "status")

    def test_limites_leitura_publica_usuario_e_escrita_independentes(self):
        taxas = {**SimpleRateThrottle.THROTTLE_RATES, "publica": "2/min", "usuario": "3/min", "escrita": "1/min"}
        with patch.object(SimpleRateThrottle, "THROTTLE_RATES", taxas):
            self.assertEqual(self.client.get("/api/v1/ongs/").status_code, 200)
            self.assertEqual(self.client.get("/api/v1/ongs/").status_code, 200)
            self.erro(self.client.get("/api/v1/ongs/"), 429, "limite_excedido")
            self.assertEqual(self.client.get("/api/v1/ongs/", REMOTE_ADDR="192.0.2.2").status_code, 200)
            cache.clear()
            cliente = self.sessao()
            for _ in range(3):
                self.assertEqual(cliente.get("/api/v1/painel/ong/").status_code, 200)
            self.erro(cliente.get("/api/v1/painel/ong/"), 429, "limite_excedido")
            cache.clear()
            self.assertEqual(self.mutacao(cliente, "patch", f"ongs/{self.ong.pk}/", {"descricao": "Apoio"}).status_code, 200)
            resposta = self.mutacao(cliente, "patch", f"ongs/{self.ong.pk}/", {"descricao": "Revisão"})
            self.erro(resposta, 429, "limite_excedido")
            self.assertIn("Retry-After", resposta)
            self.assertEqual(cliente.get("/api/v1/painel/ong/").status_code, 200)

    def test_privacidade_publica_recursiva(self):
        proibidos = {"cnpj", "email", "password", "is_staff", "is_superuser", "analisada_por", "analisada_em", "motivo_analise",
            "autor", "autor_id", "avaliada_por", "contato_autor", "responsavel", "responsavel_id"}

        def conferir(valor):
            if isinstance(valor, dict):
                self.assertFalse(proibidos.intersection(valor))
                for item in valor.values():
                    conferir(item)
            elif isinstance(valor, list):
                for item in valor:
                    conferir(item)

        for caminho in ("ongs/", f"ongs/{self.ong.pk}/", "campanhas/", f"campanhas/{self.campanha.pk}/", "postagens/", f"postagens/{self.postagem.pk}/"):
            resposta = self.client.get(f"/api/v1/{caminho}")
            self.assertEqual(resposta.status_code, 200)
            conferir(resposta.json())
            for usuario in (self.dono, self.autor, self.admin):
                self.assertNotIn(usuario.email, resposta.content.decode())
