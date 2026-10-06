from organizations.models import Ong
from organizations.services import analisar_ong

from .base import APITestCase, dados_ong


class OngsTests(APITestCase):
    def test_lista_detalhe_publicos_e_privacidade(self):
        lista = self.client.get("/api/v1/ongs/").json()
        self.assertEqual(lista["count"], 1)
        detalhe = self.client.get(f"/api/v1/ongs/{self.ong.pk}/")
        self.assertEqual(detalhe.status_code, 200)
        self.assertEqual(detalhe.json()["endereco"]["cidade"], "São Paulo")
        self.assertEqual(lista["results"], [detalhe.json()])
        for campo in ("cnpj", "email", "motivo_analise", "responsavel", "status", "password", "analisada_em", "is_staff"):
            self.assertNotIn(campo, detalhe.json())
        self.assertNotIn(self.dono.email, detalhe.content.decode())
        self.erro(self.client.get(f"/api/v1/ongs/{self.outra_ong.pk}/"), 404, "nao_encontrado")

    def test_filtros_localizacao_busca_e_ordenacao(self):
        for filtros in ({"q": "educação"}, {"cidade": "Paulo"}, {"bairro": "Sé"}, {"uf": "SP"}, {"ordering": "-atualizada_em"}):
            with self.subTest(filtros=filtros):
                self.assertEqual(self.client.get("/api/v1/ongs/", filtros).json()["count"], 1)
        self.assertEqual(self.client.get("/api/v1/ongs/", {"q": "ausente"}).json()["count"], 0)
        for filtros, campo in (({"q": "a" * 101}, "q"), ({"uf": "XX"}, "uf"), ({"ordering": "cnpj"}, "ordering"), ({"x": "1"}, "x")):
            self.erro(self.client.get("/api/v1/ongs/", filtros), 400, "validacao", campo)

    def test_criar_editar_reanalise_e_segunda_ong(self):
        cliente = self.sessao(self.sem_ong)
        resposta = self.mutacao(cliente, "post", "ongs/", dados_ong(cnpj=""))
        self.assertEqual(resposta.status_code, 201, resposta.content)
        self.assertEqual(resposta.json()["status"], "pendente")
        self.erro(self.mutacao(cliente, "post", "ongs/", dados_ong(cnpj="")), 409, "possui_dependentes")
        dono = self.sessao()
        resposta = self.mutacao(dono, "patch", f"ongs/{self.ong.pk}/", {"descricao": "Atualizada"})
        self.assertEqual(resposta.status_code, 200, resposta.content)
        self.assertEqual(resposta.json()["status"], "aprovada")
        resposta = self.mutacao(dono, "patch", f"ongs/{self.ong.pk}/", {"numero": "11"})
        self.assertEqual(resposta.status_code, 200, resposta.content)
        self.assertEqual(resposta.json()["status"], "pendente")
        self.assertEqual(resposta.json()["endereco"]["logradouro"], self.ong.logradouro)
        self.erro(self.client.get(f"/api/v1/ongs/{self.ong.pk}/"), 404, "nao_encontrado")

    def test_validacao_campos_protegidos_e_formulario(self):
        cliente = self.sessao()
        for dados, campo in (({"status": "aprovada"}, "status"), ({"responsavel": self.outro.pk}, "responsavel"),
            ({"criada_em": "2020"}, "criada_em"), ({"x": 1}, "x"), ({"cnpj": "123"}, "cnpj"), ({"cep": "123"}, "cep")):
            with self.subTest(campo=campo):
                self.erro(self.mutacao(cliente, "patch", f"ongs/{self.ong.pk}/", dados), 400, "validacao", campo)

    def test_painel_exige_sessao_e_ong_e_expoe_so_privado_autorizado(self):
        self.erro(self.client.get("/api/v1/painel/ong/"), 403, "autenticacao_necessaria")
        self.erro(self.sessao(self.sem_ong).get("/api/v1/painel/ong/"), 404, "nao_encontrado")
        privado = self.sessao().get("/api/v1/painel/ong/")
        self.assertEqual(privado.status_code, 200)
        self.assertEqual(privado.json()["cnpj"], self.ong.cnpj)
        self.assertNotIn("responsavel", privado.json())

    def test_mutacoes_exigem_sessao_csrf_e_propriedade(self):
        for metodo, caminho, dados in (("post", "ongs/", dados_ong()), ("patch", f"ongs/{self.ong.pk}/", {"nome": "Novo"}),
            ("delete", f"ongs/{self.ong.pk}/", {}), ("post", f"ongs/{self.ong.pk}/reenviar/", {})):
            with self.subTest(metodo=metodo, caminho=caminho):
                self.erro(self.mutacao(self.client, metodo, caminho, dados), 403, "autenticacao_necessaria")
                self.erro(self.mutacao(self.sessao(csrf=True), metodo, caminho, dados), 403, "csrf_invalido")
                if caminho != "ongs/":
                    self.erro(self.mutacao(self.sessao(self.autor), metodo, caminho, dados), 404, "nao_encontrado")

    def test_excluir_sem_dependentes_e_com_dependentes(self):
        self.erro(self.mutacao(self.sessao(), "delete", f"ongs/{self.ong.pk}/"), 409, "possui_dependentes")
        cliente = self.sessao(self.sem_ong)
        pk = self.mutacao(cliente, "post", "ongs/", dados_ong(cnpj="")).json()["id"]
        self.assertEqual(self.mutacao(cliente, "delete", f"ongs/{pk}/").status_code, 204)
        self.assertFalse(Ong.objects.filter(pk=pk).exists())

    def test_analise_e_reenvio_com_conflitos(self):
        cliente = self.sessao(self.admin)
        pk = self.outra_ong.pk
        caminho = f"admin/ongs/{pk}/analise/"
        self.erro(self.mutacao(cliente, "post", caminho, {"decisao": "recusar"}), 400, "validacao", "motivo")
        resposta = self.mutacao(cliente, "post", caminho, {"decisao": "recusar", "motivo": "Endereço incompleto"})
        self.assertEqual(resposta.status_code, 200, resposta.content)
        self.assertEqual(resposta.json()["status"], "recusada")
        self.erro(self.mutacao(cliente, "post", caminho, {"decisao": "aprovar"}), 409, "conflito_estado")
        dono = self.sessao(self.outro)
        resposta = self.mutacao(dono, "post", f"ongs/{pk}/reenviar/")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["motivo_analise"], "")
        self.erro(self.mutacao(dono, "post", f"ongs/{pk}/reenviar/"), 409, "conflito_estado")
        self.assertEqual(self.mutacao(cliente, "post", caminho, {"decisao": "aprovar"}).status_code, 200)

    def test_admin_permissao_filtros_e_csrf(self):
        self.erro(self.client.get("/api/v1/admin/ongs/"), 403, "autenticacao_necessaria")
        self.erro(self.sessao().get("/api/v1/admin/ongs/"), 403, "proibido")
        cliente = self.sessao(self.admin)
        self.assertEqual(cliente.get("/api/v1/admin/ongs/").json()["results"][0]["id"], self.outra_ong.pk)
        self.assertEqual(cliente.get("/api/v1/admin/ongs/?status=aprovada").json()["count"], 1)
        self.erro(cliente.get("/api/v1/admin/ongs/?status=x"), 400, "validacao", "status")
        self.erro(self.mutacao(self.sessao(self.admin, csrf=True), "post", f"admin/ongs/{self.outra_ong.pk}/analise/", {"decisao": "aprovar"}), 403, "csrf_invalido")
        self.erro(self.mutacao(self.sessao(), "post", f"admin/ongs/{self.outra_ong.pk}/analise/", {"decisao": "aprovar"}), 403, "proibido")
