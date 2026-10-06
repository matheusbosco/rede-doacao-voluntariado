import tempfile
from io import StringIO
from pathlib import Path

import yaml
from django.core.management import call_command

from .base import APITestCase


class DocumentacaoTests(APITestCase):
    def test_schema_valida_sem_avisos_e_documenta_todos_caminhos(self):
        # O arquivo fica no diretório temporário do sistema, fora do repositório.
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as arquivo:
            caminho = arquivo.name
        call_command("spectacular", validate=True, fail_on_warn=True, file=caminho, stdout=StringIO(), stderr=StringIO())
        schema = yaml.safe_load(Path(caminho).read_text(encoding="utf-8"))
        caminhos = schema["paths"]
        esperados = {
            "auth/csrf/", "auth/cadastro/", "auth/login/", "auth/logout/", "auth/me/",
            "ongs/", "ongs/{id}/", "ongs/{id}/reenviar/", "painel/ong/", "admin/ongs/", "admin/ongs/{id}/analise/",
            "campanhas/", "campanhas/{id}/", "campanhas/{id}/estado/", "painel/campanhas/", "painel/campanhas/{id}/",
            "postagens/", "postagens/{id}/", "painel/postagens/", "painel/postagens/{id}/",
            "contribuicoes/", "contribuicoes/{id}/", "contribuicoes/{id}/cancelar/", "contribuicoes/{id}/avaliacao/", "painel/contribuicoes/",
            "relatorios/campanhas/", "relatorios/campanhas/exportar/", "enderecos/cep/{cep}/",
        }
        self.assertEqual(set(caminhos), {f"/api/v1/{caminho}" for caminho in esperados})
        self.assertEqual(schema["info"]["title"], "DAI — API v1")
        for caminho, operacoes in caminhos.items():
            self.assertNotIn("put", operacoes)
            for operacao in operacoes.values():
                self.assertIn("summary", operacao)
                self.assertIn("tags", operacao)
                if caminho != "/api/v1/enderecos/cep/{cep}/":
                    self.assertIn("500", operacao["responses"])
        self.assertEqual(caminhos["/api/v1/auth/login/"]["post"]["security"], [{"csrf": []}])
        self.assertEqual(caminhos["/api/v1/campanhas/{id}/estado/"]["post"]["security"], [{"sessao": [], "csrf": []}])

    def test_schema_swagger_redoc_acessiveis(self):
        for caminho in ("schema", "docs", "redoc"):
            resposta = self.client.get(f"/api/{caminho}/")
            self.assertEqual(resposta.status_code, 200, resposta.content[:200])
        self.assertIn(b"cdn", self.client.get("/api/docs/").content)
        self.assertIn(b"cdn", self.client.get("/api/redoc/").content)
