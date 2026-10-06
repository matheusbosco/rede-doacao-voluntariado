from unittest.mock import patch

from integrations.viacep import CepInvalido, CepNaoEncontrado, ViaCepIndisponivel

from .base import APITestCase


class EnderecosTests(APITestCase):
    dados = {"cep": "01001000", "logradouro": "Praça da Sé", "bairro": "Sé", "cidade": "São Paulo", "uf": "SP", "origem": "cache"}

    def test_cep_sessao_e_contrato_legacy_preservado(self):
        caminho = "/api/v1/enderecos/cep/01001000/"
        with patch("integrations.views.consultar_cep", return_value=self.dados) as consulta:
            resposta = self.client.get(caminho)
            self.assertEqual(resposta.status_code, 403)
            self.assertEqual(resposta.json()["erro"]["codigo"], "autenticacao_necessaria")
            consulta.assert_not_called()
            cliente = self.sessao()
            resposta = cliente.get(caminho)
            self.assertEqual(resposta.status_code, 200)
            self.assertEqual(resposta.json(), self.dados)
            self.erro(cliente.get(caminho, {"x": 1}), 400, "validacao", "x")
            self.erro(cliente.post(caminho, {}, format="json"), 405, "metodo_nao_permitido")

    def test_erros_cep_legados_sem_rede(self):
        cliente = self.sessao()
        for falha, status, codigo in ((CepInvalido("CEP inválido"), 400, "validacao"),
            (CepNaoEncontrado(), 404, "cep_nao_encontrado"), (ViaCepIndisponivel(), 503, "endereco_indisponivel")):
            with patch("integrations.views.consultar_cep", side_effect=falha):
                resposta = cliente.get("/api/v1/enderecos/cep/01001000/")
            self.assertEqual(resposta.status_code, status)
            self.assertEqual(resposta.json()["erro"]["codigo"], codigo)
            self.assertEqual(set(resposta.json()["erro"]), {"codigo", "mensagem"})

    def test_limite_cep_por_usuario_retry_after_original(self):
        cliente = self.sessao()
        with patch("integrations.views.consultar_cep", return_value=self.dados), patch("integrations.views.time.time", return_value=1200):
            for _ in range(10):
                self.assertEqual(cliente.get("/api/v1/enderecos/cep/01001000/").status_code, 200)
            resposta = cliente.get("/api/v1/enderecos/cep/01001000/")
            self.assertEqual(resposta.status_code, 429)
            self.assertEqual(resposta["Retry-After"], "60")
            self.assertEqual(resposta.json()["erro"]["codigo"], "limite_excedido")
            self.assertEqual(self.sessao(self.autor).get("/api/v1/enderecos/cep/01001000/").status_code, 200)
