import importlib.util
import io
import logging
import os
import secrets
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse

from .logging import FormatoSeguro


def carregar_settings(**variaveis):
    """Importa uma cópia isolada, sem alterar as configurações usadas pela suíte."""
    ambiente = {
        "DEBUG": "false", "SECRET_KEY": secrets.token_urlsafe(64),
        "DATABASE_URL": "postgresql://exemplo.invalid/banco",
    }
    ambiente.update(variaveis)
    especificacao = importlib.util.spec_from_file_location(
        "settings_teste_deploy", Path(__file__).with_name("settings.py"),
    )
    modulo = importlib.util.module_from_spec(especificacao)
    with patch.dict(os.environ, ambiente, clear=True):
        especificacao.loader.exec_module(modulo)
    return modulo


class HealthTests(SimpleTestCase):
    def test_get_publico_retorna_apenas_status_sem_acessar_banco(self):
        # SimpleTestCase proíbe consultas, inclusive as feitas por middleware.
        self.client.cookies[settings.SESSION_COOKIE_NAME] = "sessao-inexistente"
        resposta = self.client.get(reverse("health"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta["Content-Type"], "application/json")
        self.assertEqual(resposta.content, b'{"status": "ok"}')
        self.assertEqual(resposta.json(), {"status": "ok"})

    def test_outros_metodos_retornam_405_mesmo_sem_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        for metodo in ("post", "put", "patch", "delete", "head", "options", "trace"):
            with self.subTest(metodo=metodo):
                resposta = getattr(cliente, metodo)(reverse("health"))
                self.assertEqual(resposta.status_code, 405)
                self.assertEqual(resposta["Allow"], "GET")

    def test_nao_expoe_configuracao_nem_parametros(self):
        marcador = secrets.token_urlsafe(24)
        with override_settings(SECRET_KEY=marcador, ALLOWED_HOSTS=["testserver"]):
            resposta = self.client.get(reverse("health"), {"configuracao": marcador})
        self.assertEqual(resposta.content, b'{"status": "ok"}')
        self.assertNotIn(marcador, str(dict(resposta.headers)))


class ProducaoTests(SimpleTestCase):
    def setUp(self):
        self.configuracao = carregar_settings(RENDER_EXTERNAL_HOSTNAME="dai.onrender.com")

    def test_render_acrescenta_host_e_origem_sem_relaxar_listas(self):
        configuracao = carregar_settings(
            ALLOWED_HOSTS="exemplo.local", CSRF_TRUSTED_ORIGINS="https://exemplo.local",
            RENDER_EXTERNAL_HOSTNAME="dai.onrender.com",
        )
        self.assertEqual(configuracao.ALLOWED_HOSTS, ["exemplo.local", "dai.onrender.com"])
        self.assertEqual(configuracao.CSRF_TRUSTED_ORIGINS, [
            "https://exemplo.local", "https://dai.onrender.com",
        ])

    def test_sem_render_preserva_restricoes(self):
        for hostname in ("", "   "):
            with self.subTest(hostname=hostname):
                configuracao = carregar_settings(RENDER_EXTERNAL_HOSTNAME=hostname)
                self.assertEqual(configuracao.ALLOWED_HOSTS, [])
                self.assertEqual(configuracao.CSRF_TRUSTED_ORIGINS, [])

    def test_render_nao_duplica_host_e_origem(self):
        configuracao = carregar_settings(
            ALLOWED_HOSTS="dai.onrender.com", CSRF_TRUSTED_ORIGINS="https://dai.onrender.com",
            RENDER_EXTERNAL_HOSTNAME=" dai.onrender.com ",
        )
        self.assertEqual(configuracao.ALLOWED_HOSTS, ["dai.onrender.com"])
        self.assertEqual(configuracao.CSRF_TRUSTED_ORIGINS, ["https://dai.onrender.com"])

    def test_debug_preserva_hosts_locais(self):
        configuracao = carregar_settings(DEBUG="true")
        self.assertEqual(configuracao.ALLOWED_HOSTS, ["localhost", "127.0.0.1"])

    def test_seguranca_em_producao(self):
        configuracao = carregar_settings(SECURE_HSTS_SECONDS="3600")
        self.assertFalse(configuracao.DEBUG)
        self.assertEqual(configuracao.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https"))
        self.assertTrue(configuracao.SECURE_SSL_REDIRECT)
        self.assertEqual(configuracao.SECURE_REDIRECT_EXEMPT, [r"^health/$"])
        self.assertTrue(configuracao.SESSION_COOKIE_SECURE)
        self.assertTrue(configuracao.CSRF_COOKIE_SECURE)
        self.assertTrue(configuracao.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(configuracao.SESSION_COOKIE_SAMESITE, "Lax")
        self.assertEqual(configuracao.CSRF_COOKIE_SAMESITE, "Lax")
        self.assertEqual(configuracao.X_FRAME_OPTIONS, "DENY")
        self.assertEqual(configuracao.SECURE_HSTS_SECONDS, 3600)
        self.assertTrue(configuracao.SECURE_CONTENT_TYPE_NOSNIFF)

    def test_neon_preserva_sslmode_da_url_sem_forcar_tls_local(self):
        configuracao = carregar_settings(DATABASE_URL="postgresql://exemplo.invalid/banco?sslmode=require")
        self.assertEqual(configuracao.DATABASES["default"]["OPTIONS"]["sslmode"], "require")
        configuracao = carregar_settings(DATABASE_URL="postgresql://exemplo.invalid/banco")
        self.assertNotIn("sslmode", configuracao.DATABASES["default"].get("OPTIONS", {}))

    def test_health_interno_http_nao_redireciona(self):
        with override_settings(
            DEBUG=False, ALLOWED_HOSTS=self.configuracao.ALLOWED_HOSTS,
            SECURE_SSL_REDIRECT=self.configuracao.SECURE_SSL_REDIRECT,
            SECURE_REDIRECT_EXEMPT=self.configuracao.SECURE_REDIRECT_EXEMPT,
            SECURE_PROXY_SSL_HEADER=self.configuracao.SECURE_PROXY_SSL_HEADER,
        ):
            resposta = Client().get("/health/", HTTP_HOST="dai.onrender.com")
        self.assertEqual(resposta.status_code, 200)
        self.assertNotIn("Location", resposta)
        self.assertEqual(resposta.json(), {"status": "ok"})

    def test_somente_health_exato_fica_isento(self):
        with override_settings(
            DEBUG=False, ALLOWED_HOSTS=self.configuracao.ALLOWED_HOSTS,
            SECURE_SSL_REDIRECT=self.configuracao.SECURE_SSL_REDIRECT,
            SECURE_REDIRECT_EXEMPT=self.configuracao.SECURE_REDIRECT_EXEMPT,
            SECURE_PROXY_SSL_HEADER=self.configuracao.SECURE_PROXY_SSL_HEADER,
        ):
            cliente = Client()
            for caminho in ("/", "/api/docs/", "/health", "/health/outro/", "/outro/health/"):
                with self.subTest(caminho=caminho):
                    resposta = cliente.get(caminho, HTTP_HOST="dai.onrender.com")
                    self.assertEqual(resposta.status_code, 301)
                    self.assertEqual(resposta["Location"], f"https://dai.onrender.com{caminho}")

    def test_proxy_https_nao_entra_em_loop_e_envia_cabecalhos(self):
        with override_settings(
            DEBUG=False, ALLOWED_HOSTS=self.configuracao.ALLOWED_HOSTS,
            SECURE_SSL_REDIRECT=self.configuracao.SECURE_SSL_REDIRECT,
            SECURE_REDIRECT_EXEMPT=self.configuracao.SECURE_REDIRECT_EXEMPT,
            SECURE_PROXY_SSL_HEADER=self.configuracao.SECURE_PROXY_SSL_HEADER,
            SECURE_HSTS_SECONDS=3600,
        ):
            for caminho in ("/health/", "/api/docs/"):
                with self.subTest(caminho=caminho):
                    resposta = Client().get(caminho, HTTP_HOST="dai.onrender.com", HTTP_X_FORWARDED_PROTO="https")
                    self.assertEqual(resposta.status_code, 200)
                    self.assertNotIn("Location", resposta)
                    self.assertEqual(resposta["Strict-Transport-Security"], "max-age=3600")
                    self.assertEqual(resposta["X-Frame-Options"], "DENY")
                    self.assertEqual(resposta["X-Content-Type-Options"], "nosniff")

    def test_logging_warning_para_stdout_sem_handlers_inseguros_do_django(self):
        configuracao = self.configuracao.LOGGING
        console = configuracao["handlers"]["console"]
        self.assertEqual(console["stream"], "ext://sys.stdout")
        self.assertEqual(console["level"], "WARNING")
        self.assertEqual(configuracao["root"], {"handlers": ["console"], "level": "WARNING"})
        for nome in ("django", "django.server"):
            self.assertEqual(configuracao["loggers"][nome]["handlers"], [])
            self.assertTrue(configuracao["loggers"][nome]["propagate"])

    def _logar(self, escrever):
        saida = io.StringIO()
        handler = logging.StreamHandler(saida)
        handler.setLevel(self.configuracao.LOGGING["handlers"]["console"]["level"])
        handler.setFormatter(FormatoSeguro())
        logger = logging.Logger("django.request", level=logging.WARNING)
        logger.addHandler(handler)
        escrever(logger)
        return saida.getvalue()

    def test_logging_mantem_mensagem_e_traceback_para_diagnostico(self):
        def escrever(logger):
            try:
                raise ValueError("falha ao salvar contribuição 42")
            except ValueError:
                logger.exception("Internal Server Error: /api/v1/contribuicoes/")

        texto = self._logar(escrever)
        self.assertIn("ERROR django.request Internal Server Error: /api/v1/contribuicoes/", texto)
        self.assertIn("ValueError: falha ao salvar contribuição 42", texto)
        self.assertIn("Traceback", texto)

    def test_logging_nao_registra_info(self):
        self.assertEqual(self._logar(lambda logger: logger.info("não deve aparecer")), "")

    def test_logging_redige_credenciais_em_mensagem_e_excecao(self):
        senha = secrets.token_urlsafe(24)

        def escrever(logger):
            logger.warning("conexão com postgres://dai_user:%s@db.exemplo.neon.tech/dai falhou", senha)
            logger.warning("DATABASE_URL=%s e SECRET_KEY: %s", senha, senha)
            try:
                raise RuntimeError(f"password={senha}")
            except RuntimeError:
                logger.exception("erro inesperado")

        texto = self._logar(escrever)
        self.assertNotIn(senha, texto)
        self.assertIn("postgres://[redigido]@db.exemplo.neon.tech/dai", texto)
        self.assertIn("[redigido]", texto)
