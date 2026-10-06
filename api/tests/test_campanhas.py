from campaigns.models import Campanha
from organizations.models import Ong

from .base import APITestCase, dados_campanha


class CampanhasTests(APITestCase):
    def test_publicas_totais_formatos_e_rascunhos_privados(self):
        resposta = self.client.get(f"/api/v1/campanhas/{self.campanha.pk}/")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["meta"], "100.00")
        self.assertEqual(resposta.json()["total_confirmado"], "0.00")
        self.assertEqual(resposta.json()["percentual_meta"], "0.00")
        self.assertTrue(resposta.json()["disponivel"])
        self.assertEqual(resposta.json()["ong_id"], self.ong.pk)
        for pk in (self.rascunho.pk, self.outra_campanha.pk):
            self.erro(self.client.get(f"/api/v1/campanhas/{pk}/"), 404, "nao_encontrado")
        self.assertEqual(self.client.get("/api/v1/campanhas/").json()["count"], 2)

    def test_filtros_e_busca_ordenacao(self):
        for filtros in ({"q": "alimentos"}, {"ong_id": self.ong.pk}, {"cidade": "Paulo"}, {"bairro": "Sé"}, {"uf": "SP"},
            {"status": "ativa"}, {"disponivel": "true"}, {"ordering": "titulo"}, {"ordering": "data_fim"}):
            with self.subTest(filtros=filtros):
                self.assertEqual(self.client.get("/api/v1/campanhas/", filtros).json()["count"], 2)
        self.assertEqual(self.client.get("/api/v1/campanhas/?tipo=item").json()["count"], 1)
        self.assertEqual(self.client.get("/api/v1/campanhas/?disponivel=false").json()["count"], 0)
        for filtros, campo in (({"status": "rascunho"}, "status"), ({"ong_id": "x"}, "ong_id"), ({"tipo": "x"}, "tipo"),
            ({"disponivel": "talvez"}, "disponivel"), ({"q": "a" * 101}, "q"), ({"ordering": "meta"}, "ordering")):
            self.erro(self.client.get("/api/v1/campanhas/", filtros), 400, "validacao", campo)

    def test_painel_lista_e_detalhe_rascunho(self):
        cliente = self.sessao()
        self.assertEqual(cliente.get("/api/v1/painel/campanhas/").json()["count"], 3)
        self.assertEqual(cliente.get("/api/v1/painel/campanhas/?status=rascunho").json()["count"], 1)
        self.assertEqual(cliente.get(f"/api/v1/painel/campanhas/{self.rascunho.pk}/").status_code, 200)
        self.erro(cliente.get(f"/api/v1/painel/campanhas/{self.outra_campanha.pk}/"), 404, "nao_encontrado")
        self.erro(self.sessao(self.sem_ong).get("/api/v1/painel/campanhas/"), 404, "nao_encontrado")
        for caminho in ("painel/campanhas/", f"painel/campanhas/{self.rascunho.pk}/"):
            self.erro(self.client.get(f"/api/v1/{caminho}"), 403, "autenticacao_necessaria")

    def test_criar_editar_e_excluir_sem_dependentes(self):
        cliente = self.sessao()
        resposta = self.mutacao(cliente, "post", "campanhas/", dados_campanha())
        self.assertEqual(resposta.status_code, 201, resposta.content)
        self.assertEqual(resposta.json()["status"], "rascunho")
        pk = resposta.json()["id"]
        resposta = self.mutacao(cliente, "patch", f"campanhas/{pk}/", {"titulo": "Editada", "meta": "150.00"})
        self.assertEqual(resposta.status_code, 200, resposta.content)
        self.assertEqual(resposta.json()["titulo"], "Editada")
        self.assertEqual(resposta.json()["meta"], "150.00")
        self.assertEqual(self.mutacao(cliente, "delete", f"campanhas/{pk}/").status_code, 204)
        self.assertFalse(Campanha.objects.filter(pk=pk).exists())

    def test_criar_exige_ong_aprovada(self):
        self.erro(self.mutacao(self.sessao(self.outro), "post", "campanhas/", dados_campanha()), 403, "proibido")
        self.erro(self.mutacao(self.sessao(self.sem_ong), "post", "campanhas/", dados_campanha()), 404, "nao_encontrado")

    def test_validacoes_modelo_e_campos_protegidos(self):
        cliente = self.sessao()
        for dados, campo in (({"status": "ativa"}, "status"), ({"ong_id": self.outra_ong.pk}, "ong_id"),
            ({"total_confirmado": "99"}, "total_confirmado"), ({"meta": "0.00"}, "meta"), ({"meta": "1.50"}, "meta"),
            ({"data_fim": "2000-01-01"}, "data_fim"), ({"desconhecido": 1}, "desconhecido")):
            self.erro(self.mutacao(cliente, "patch", f"campanhas/{self.campanha.pk}/", dados), 400, "validacao", campo)
        for campo, valor in (("tipo", "horas"), ("unidade", "pacote")):
            self.erro(self.mutacao(cliente, "patch", f"campanhas/{self.campanha.pk}/", {campo: valor}), 400, "validacao", campo)

    def test_estado_ciclo_completo_e_conflito_sem_efeito(self):
        cliente = self.sessao()
        caminho = f"campanhas/{self.rascunho.pk}/estado/"
        for acao, estado in (("publicar", "ativa"), ("pausar", "pausada"), ("reativar", "ativa"), ("encerrar", "encerrada")):
            resposta = self.mutacao(cliente, "post", caminho, {"acao": acao})
            self.assertEqual(resposta.status_code, 200, resposta.content)
            self.assertEqual(resposta.json()["status"], estado)
            self.erro(self.mutacao(cliente, "post", caminho, {"acao": acao}), 409, "conflito_estado")
            self.assertEqual(Campanha.objects.get(pk=self.rascunho.pk).status, estado)

    def test_estado_validacao_aprovacao_e_dependentes(self):
        cliente = self.sessao()
        self.erro(self.mutacao(cliente, "post", f"campanhas/{self.rascunho.pk}/estado/", {"acao": "x"}), 400, "validacao", "acao")
        self.erro(self.mutacao(cliente, "delete", f"campanhas/{self.campanha.pk}/"), 409, "possui_dependentes")
        Ong.objects.filter(pk=self.ong.pk).update(status="pendente", analisada_por=None, analisada_em=None)
        self.erro(self.mutacao(cliente, "post", f"campanhas/{self.rascunho.pk}/estado/", {"acao": "publicar"}), 409, "conflito_estado")

    def test_mutacoes_sessao_csrf_e_propriedade(self):
        for metodo, caminho, dados in (("post", "campanhas/", dados_campanha()), ("patch", f"campanhas/{self.campanha.pk}/", {"titulo": "Novo"}),
            ("delete", f"campanhas/{self.campanha.pk}/", {}), ("post", f"campanhas/{self.campanha.pk}/estado/", {"acao": "pausar"})):
            with self.subTest(caminho=caminho, metodo=metodo):
                self.erro(self.mutacao(self.client, metodo, caminho, dados), 403, "autenticacao_necessaria")
                self.erro(self.mutacao(self.sessao(csrf=True), metodo, caminho, dados), 403, "csrf_invalido")
                if caminho != "campanhas/":
                    self.erro(self.mutacao(self.sessao(self.outro), metodo, caminho, dados), 404, "nao_encontrado")
