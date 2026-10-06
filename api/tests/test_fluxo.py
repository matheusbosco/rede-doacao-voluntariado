import csv
from io import StringIO

from rest_framework.test import APIClient
from django.utils import timezone

from .base import APITestCase, dados_campanha, dados_ong


class FluxoCompletoTests(APITestCase):
    def test_cadastro_ate_relatorio_pela_api_com_sessao_e_csrf(self):
        responsavel = APIClient(enforce_csrf_checks=True)
        doador = APIClient(enforce_csrf_checks=True)
        equipe = self.sessao(self.admin, csrf=True)

        def enviar(cliente, caminho, dados):
            return cliente.post(f"/api/v1/{caminho}", dados, format="json", HTTP_X_CSRFTOKEN=self.token(cliente))

        for cliente, username in ((responsavel, "responsavel_novo"), (doador, "doador_novo")):
            dados = {"username": username, "email": f"{username}@example.org", "first_name": "Maria",
                "password": "Frase segura com símbolos! 4729", "password_confirm": "Frase segura com símbolos! 4729"}
            self.assertEqual(enviar(cliente, "auth/cadastro/", dados).status_code, 201)
            self.assertEqual(enviar(cliente, "auth/login/", {"username": username, "password": dados["password"]}).status_code, 200)
        ong = enviar(responsavel, "ongs/", dados_ong(cnpj="")).json()
        self.assertEqual(ong["status"], "pendente")
        aprovada = enviar(equipe, f"admin/ongs/{ong['id']}/analise/", {"decisao": "aprovar"})
        self.assertEqual(aprovada.status_code, 200)
        criada = enviar(responsavel, "campanhas/", dados_campanha())
        self.assertEqual(criada.status_code, 201, criada.content)
        campanha = criada.json()
        self.assertEqual(enviar(responsavel, f"campanhas/{campanha['id']}/estado/", {"acao": "publicar"}).status_code, 200)
        declarada = enviar(doador, "contribuicoes/", {"campanha_id": campanha["id"], "tipo": "item", "quantidade": "15.00"})
        self.assertEqual(declarada.status_code, 201, declarada.content)
        contribuicao = declarada.json()
        for acao in ("aceitar", "confirmar"):
            self.assertEqual(enviar(responsavel, f"contribuicoes/{contribuicao['id']}/avaliacao/", {"acao": acao}).status_code, 200)
        publica = self.client.get(f"/api/v1/campanhas/{campanha['id']}/").json()
        self.assertEqual(publica["total_confirmado"], "15.00")
        self.assertEqual(publica["percentual_meta"], "15.00")
        hoje = timezone.localdate().isoformat()
        filtros = {"inicio": hoje, "fim": hoje, "campanha_id": campanha["id"]}
        json = responsavel.get("/api/v1/relatorios/campanhas/", filtros)
        self.assertEqual(json.status_code, 200, json.content)
        linha = json.json()["campanhas"][0]
        self.assertEqual(linha["total_confirmado"], "15.00")
        self.assertEqual(linha["confirmadas"], 1)
        csv_resposta = responsavel.get("/api/v1/relatorios/campanhas/exportar/", filtros)
        self.assertEqual(csv_resposta.status_code, 200)
        linhas = list(csv.DictReader(StringIO(csv_resposta.content.decode("utf-8-sig")), delimiter=";"))
        self.assertEqual(linhas[0]["total_confirmado"], "15,00")
        self.assertEqual(linhas[0]["confirmadas"], "1")
