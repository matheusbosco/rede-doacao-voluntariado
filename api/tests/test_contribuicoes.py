from contributions.models import Contribuicao
from contributions.services import avaliar_contribuicao, criar_contribuicao

from .base import APITestCase


class ContribuicoesTests(APITestCase):
    def caminho(self, sufixo=""):
        return f"contribuicoes/{self.contribuicao.pk}/{sufixo}"

    def test_criar_lista_propria_editar_e_cancelar(self):
        cliente = self.sessao(self.autor)
        resposta = self.mutacao(cliente, "post", "contribuicoes/", {"campanha_id": self.campanha.pk, "tipo": "item", "quantidade": "3.00"})
        self.assertEqual(resposta.status_code, 201, resposta.content)
        self.assertEqual(resposta.json()["quantidade"], "3.00")
        self.assertIsNone(resposta.json()["valor"])
        self.assertEqual(cliente.get("/api/v1/contribuicoes/").json()["count"], 2)
        resposta = self.mutacao(cliente, "patch", self.caminho(), {"quantidade": "5.00", "observacao": "Agendada"})
        self.assertEqual(resposta.status_code, 200, resposta.content)
        self.assertEqual(resposta.json()["quantidade"], "5.00")
        self.assertEqual(self.mutacao(cliente, "post", self.caminho("cancelar/")).status_code, 200)
        self.assertEqual(Contribuicao.objects.get(pk=self.contribuicao.pk).status, "cancelada")

    def test_detalhe_contato_so_responsavel_destinatario(self):
        caminho = f"/api/v1/{self.caminho()}"
        proprio = self.sessao(self.autor).get(caminho)
        self.assertEqual(proprio.status_code, 200)
        self.assertNotIn("contato_autor", proprio.json())
        self.assertNotIn("autor", proprio.json())
        recebido = self.sessao().get(caminho)
        self.assertEqual(recebido.json()["contato_autor"], {"nome": "Doadora Silva", "email": self.autor.email})
        self.erro(self.sessao(self.outro).get(caminho), 404, "nao_encontrado")
        self.erro(self.client.get(caminho), 403, "autenticacao_necessaria")
        self.assertEqual(self.sessao(self.outro).get("/api/v1/contribuicoes/").json()["count"], 0)

    def test_painel_restrito_filtros_contato(self):
        cliente = self.sessao()
        for filtros in ({"campanha_id": self.campanha.pk}, {"tipo": "item"}, {"status": "declarada"}):
            resposta = cliente.get("/api/v1/painel/contribuicoes/", filtros)
            self.assertEqual(resposta.status_code, 200)
            self.assertEqual(resposta.json()["count"], 1)
            self.assertIn("contato_autor", resposta.json()["results"][0])
        self.assertEqual(self.sessao(self.outro).get("/api/v1/painel/contribuicoes/").json()["count"], 0)
        self.erro(self.sessao(self.sem_ong).get("/api/v1/painel/contribuicoes/"), 404, "nao_encontrado")
        self.erro(self.client.get("/api/v1/painel/contribuicoes/"), 403, "autenticacao_necessaria")

    def test_validacoes_medida_tipo_e_campos_protegidos(self):
        cliente = self.sessao(self.autor)
        for dados, campo in (({"quantidade": "0.00"}, "quantidade"), ({"quantidade": "1.50"}, "quantidade"),
            ({"valor": "5.00"}, "valor"), ({"status": "confirmada"}, "status"), ({"autor": self.dono.pk}, "autor"),
            ({"avaliada_por": self.dono.pk}, "avaliada_por"), ({"avaliada_em": "2020"}, "avaliada_em"),
            ({"criada_em": "2020"}, "criada_em"), ({"campanha_id": self.dinheiro.pk}, "campanha_id"), ({"x": 1}, "x")):
            self.erro(self.mutacao(cliente, "patch", self.caminho(), dados), 400, "validacao", campo)
        self.erro(self.mutacao(cliente, "post", "contribuicoes/", {"campanha_id": self.campanha.pk, "tipo": "dinheiro", "valor": "5.00"}), 400, "validacao")

    def test_nova_contribuicao_em_rascunho_indisponivel_e_propria_ong(self):
        dados = {"campanha_id": self.rascunho.pk, "tipo": "item", "quantidade": "1.00"}
        self.erro(self.mutacao(self.sessao(self.autor), "post", "contribuicoes/", dados), 404, "nao_encontrado")
        dados["campanha_id"] = self.campanha.pk
        self.erro(self.mutacao(self.sessao(), "post", "contribuicoes/", dados), 403, "proibido")
        self.campanha.status = "pausada"
        self.campanha.save()
        self.erro(self.mutacao(self.sessao(self.autor), "post", "contribuicoes/", dados), 400, "validacao")

    def test_avaliacao_aceitar_confirmar_total_e_conflitos(self):
        cliente = self.sessao()
        self.erro(self.mutacao(cliente, "post", self.caminho("avaliacao/"), {"acao": "confirmar"}), 409, "conflito_estado")
        for acao, estado in (("aceitar", "aceita"), ("confirmar", "confirmada")):
            resposta = self.mutacao(cliente, "post", self.caminho("avaliacao/"), {"acao": acao})
            self.assertEqual(resposta.status_code, 200, resposta.content)
            self.assertEqual(resposta.json()["status"], estado)
            self.erro(self.mutacao(cliente, "post", self.caminho("avaliacao/"), {"acao": acao}), 409, "conflito_estado")
            self.assertEqual(Contribuicao.objects.get(pk=self.contribuicao.pk).status, estado)
        campanha = self.client.get(f"/api/v1/campanhas/{self.campanha.pk}/").json()
        self.assertEqual(campanha["total_confirmado"], "2.00")
        self.assertEqual(campanha["percentual_meta"], "2.00")
        self.erro(self.mutacao(self.sessao(self.autor), "patch", self.caminho(), {"quantidade": "3.00"}), 409, "conflito_estado")
        self.erro(self.mutacao(self.sessao(self.autor), "post", self.caminho("cancelar/")), 409, "conflito_estado")

    def test_dinheiro_sem_aceite_e_confirmacao_direta(self):
        contribuicao = criar_contribuicao(self.autor, self.dinheiro, {"valor": "150.00"})
        caminho = f"contribuicoes/{contribuicao.pk}/avaliacao/"
        self.erro(self.mutacao(self.sessao(), "post", caminho, {"acao": "aceitar"}), 400, "validacao", "acao")
        self.assertEqual(self.mutacao(self.sessao(), "post", caminho, {"acao": "confirmar"}).status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/campanhas/{self.dinheiro.pk}/").json()["total_confirmado"], "150.00")

    def test_recusar_exige_motivo_e_cancelamento_repetido(self):
        self.erro(self.mutacao(self.sessao(), "post", self.caminho("avaliacao/"), {"acao": "recusar"}), 400, "validacao")
        resposta = self.mutacao(self.sessao(), "post", self.caminho("avaliacao/"), {"acao": "recusar", "motivo": "Dados incorretos"})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["motivo_avaliacao"], "Dados incorretos")
        self.erro(self.mutacao(self.sessao(self.autor), "post", self.caminho("cancelar/")), 409, "conflito_estado")

    def test_cancelar_aceita_e_repetida(self):
        avaliar_contribuicao(self.contribuicao.pk, self.dono, "aceitar")
        cliente = self.sessao(self.autor)
        self.assertEqual(self.mutacao(cliente, "post", self.caminho("cancelar/")).status_code, 200)
        self.erro(self.mutacao(cliente, "post", self.caminho("cancelar/")), 409, "conflito_estado")

    def test_mutacoes_sessao_csrf_e_propriedade(self):
        for metodo, caminho, dados, usuario in (("post", "contribuicoes/", {"campanha_id": self.campanha.pk, "tipo": "item", "quantidade": "2.00"}, self.autor),
            ("patch", self.caminho(), {"quantidade": "3.00"}, self.autor), ("post", self.caminho("cancelar/"), {}, self.autor),
            ("post", self.caminho("avaliacao/"), {"acao": "aceitar"}, self.dono)):
            with self.subTest(metodo=metodo, caminho=caminho):
                self.erro(self.mutacao(self.client, metodo, caminho, dados), 403, "autenticacao_necessaria")
                self.erro(self.mutacao(self.sessao(usuario, csrf=True), metodo, caminho, dados), 403, "csrf_invalido")
                if caminho != "contribuicoes/":
                    self.erro(self.mutacao(self.sessao(self.outro), metodo, caminho, dados), 404, "nao_encontrado")
        self.erro(self.mutacao(self.sessao(), "patch", self.caminho(), {"quantidade": "3.00"}), 404, "nao_encontrado")
        self.erro(self.mutacao(self.sessao(self.autor), "post", self.caminho("avaliacao/"), {"acao": "aceitar"}), 404, "nao_encontrado")
