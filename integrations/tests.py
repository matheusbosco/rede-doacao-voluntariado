from datetime import timedelta
from unittest.mock import Mock, patch

import requests
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .models import CacheCep
from .viacep import CepInvalido, CepNaoEncontrado, ViaCepIndisponivel, consultar_cep


def resposta_viacep(**alteracoes):
    dados = {
        "cep": "01001-000", "logradouro": "Praça da Sé", "bairro": "Sé",
        "localidade": "São Paulo", "uf": "SP",
    }
    dados.update(alteracoes)
    return dados


class ViaCepTests(TestCase):
    def setUp(self):
        cache.clear()
        self.rede = patch("integrations.viacep.requests.get").start()
        self.addCleanup(patch.stopall)
        self.rede.return_value = Mock(status_code=200)
        self.rede.return_value.json.return_value = resposta_viacep()

    def test_sucesso_grava_cache_por_24_horas(self):
        antes = timezone.now()
        dados = consultar_cep("01001-000")
        self.assertEqual(dados["origem"], "viacep")
        self.assertEqual(dados["cidade"], "São Paulo")
        salvo = CacheCep.objects.get(cep="01001000")
        self.assertEqual(salvo.logradouro, "Praça da Sé")
        self.assertGreaterEqual(salvo.expira_em, antes + timedelta(hours=24))
        self.assertLessEqual(salvo.expira_em, timezone.now() + timedelta(hours=24))
        self.rede.assert_called_once_with(
            "https://viacep.com.br/ws/01001000/json/", timeout=(2, 3),
            allow_redirects=False, headers={"Accept": "application/json"},
        )

    def test_segunda_consulta_usa_cache_sem_rede(self):
        consultar_cep("01001000")
        self.rede.reset_mock()
        self.assertEqual(consultar_cep("01001-000")["origem"], "cache")
        self.rede.assert_not_called()

    def test_cache_expirado_e_atualizado(self):
        consultar_cep("01001000")
        CacheCep.objects.update(expira_em=timezone.now() - timedelta(seconds=1))
        self.assertEqual(consultar_cep("01001000")["origem"], "viacep")
        self.assertEqual(self.rede.call_count, 2)
        self.assertEqual(CacheCep.objects.count(), 1)

    def test_cep_inexistente_booleano_ou_texto(self):
        for erro in (True, "true"):
            with self.subTest(erro=erro):
                self.rede.return_value.json.return_value = {"erro": erro}
                with self.assertRaises(CepNaoEncontrado):
                    consultar_cep("01001000")
        self.assertFalse(CacheCep.objects.exists())

    def test_cep_invalido_nao_chama_rede(self):
        for cep in ("", "123", "01001/000", "abcdefgh", "٠١٠٠١٠٠٠", None):
            with self.subTest(cep=cep), self.assertRaises(CepInvalido):
                consultar_cep(cep)
        self.rede.assert_not_called()

    def test_timeout(self):
        self.rede.side_effect = requests.Timeout("Tempo esgotado")
        with self.assertRaises(ViaCepIndisponivel):
            consultar_cep("01001000")
        self.assertFalse(CacheCep.objects.exists())

    def test_erro_de_conexao(self):
        self.rede.side_effect = requests.ConnectionError("Sem conexão")
        with self.assertRaises(ViaCepIndisponivel):
            consultar_cep("01001000")

    def test_status_500_403_e_429_do_servico(self):
        for status in (500, 403, 429):
            with self.subTest(status=status):
                self.rede.return_value.status_code = status
                with self.assertRaises(ViaCepIndisponivel):
                    consultar_cep("01001000")
        self.rede.return_value.json.assert_not_called()

    def test_corpo_html_em_vez_de_json(self):
        self.rede.return_value.json.side_effect = ValueError("HTML")
        with self.assertRaises(ViaCepIndisponivel):
            consultar_cep("01001000")

    def test_json_que_nao_e_objeto(self):
        for dados in ([], "texto", None, 1):
            with self.subTest(dados=dados):
                self.rede.return_value.json.return_value = dados
                with self.assertRaises(ViaCepIndisponivel):
                    consultar_cep("01001000")

    def test_campos_ausentes_ou_com_tipo_errado(self):
        for campo in ("cep", "logradouro", "bairro", "localidade", "uf"):
            for valor in (None, 123, []):
                with self.subTest(campo=campo, valor=valor):
                    self.rede.return_value.json.return_value = resposta_viacep(**{campo: valor})
                    with self.assertRaises(ViaCepIndisponivel):
                        consultar_cep("01001000")
            with self.subTest(campo_ausente=campo):
                dados = resposta_viacep()
                del dados[campo]
                self.rede.return_value.json.return_value = dados
                with self.assertRaises(ViaCepIndisponivel):
                    consultar_cep("01001000")
        self.assertFalse(CacheCep.objects.exists())

    def test_campos_obrigatorios_vazios(self):
        for campo in ("cep", "localidade", "uf"):
            with self.subTest(campo=campo):
                self.rede.return_value.json.return_value = resposta_viacep(**{campo: " "})
                with self.assertRaises(ViaCepIndisponivel):
                    consultar_cep("01001000")

    def test_campos_maiores_que_o_cache_rejeitados(self):
        for campo, limite in (("logradouro", 200), ("bairro", 100), ("localidade", 100)):
            with self.subTest(campo=campo):
                self.rede.return_value.json.return_value = resposta_viacep(**{campo: "a" * (limite + 1)})
                with self.assertRaises(ViaCepIndisponivel):
                    consultar_cep("01001000")

    def test_cep_divergente(self):
        self.rede.return_value.json.return_value = resposta_viacep(cep="70000-000")
        with self.assertRaises(ViaCepIndisponivel):
            consultar_cep("01001000")

    def test_uf_invalida(self):
        self.rede.return_value.json.return_value = resposta_viacep(uf="XX")
        with self.assertRaises(ViaCepIndisponivel):
            consultar_cep("01001000")

    def test_redirect_nao_e_seguido(self):
        self.rede.return_value.status_code = 302
        with self.assertRaises(ViaCepIndisponivel):
            consultar_cep("01001000")
        self.assertFalse(self.rede.call_args.kwargs["allow_redirects"])
        self.rede.return_value.json.assert_not_called()

    def test_cep_sem_logradouro_e_bairro_aceita_preenchimento_manual(self):
        self.rede.return_value.json.return_value = resposta_viacep(logradouro="", bairro="")
        self.assertEqual(consultar_cep("01001000")["logradouro"], "")


class ConsultaCepTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.usuario = User.objects.create_user("ana", "ana@example.org")
        self.url = reverse("consulta-cep", args=["01001000"])
        self.rede = patch("integrations.viacep.requests.get").start()
        self.addCleanup(patch.stopall)
        self.rede.return_value = Mock(status_code=200)
        self.rede.return_value.json.return_value = resposta_viacep()

    def test_endpoint_exige_login_com_erro_json(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(resposta.json()["erro"]["codigo"], "autenticacao_necessaria")
        self.rede.assert_not_called()

    def test_endpoint_autenticado_devolve_endereco(self):
        self.client.force_login(self.usuario)
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["cep"], "01001000")

    def test_limite_10_por_minuto_com_retry_after(self):
        self.client.force_login(self.usuario)
        with patch("integrations.views.time.time", return_value=1200):
            for _ in range(10):
                self.assertEqual(self.client.get(self.url).status_code, 200)
            resposta = self.client.get(self.url)
            self.assertEqual(resposta.status_code, 429)
            self.assertEqual(resposta["Retry-After"], "60")
            self.assertEqual(resposta.json()["erro"]["codigo"], "limite_excedido")
        with patch("integrations.views.time.time", return_value=1260):
            self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_limite_e_por_usuario(self):
        self.client.force_login(self.usuario)
        with patch("integrations.views.time.time", return_value=1200):
            for _ in range(11):
                self.client.get(self.url)
            outro = User.objects.create_user("outro", "outro@example.org")
            self.client.force_login(outro)
            self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_erros_do_cliente_sao_json(self):
        self.client.force_login(self.usuario)
        resposta = self.client.get(reverse("consulta-cep", args=["invalido"]))
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.json()["erro"]["codigo"], "validacao")
        self.rede.assert_not_called()
        self.rede.return_value.json.return_value = {"erro": True}
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.rede.side_effect = requests.Timeout()
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 503)
        self.assertEqual(resposta.json()["erro"]["codigo"], "endereco_indisponivel")

    def test_endpoint_so_aceita_get(self):
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.post(self.url).status_code, 405)
        self.rede.assert_not_called()
