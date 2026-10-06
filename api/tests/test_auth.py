from django.core.cache import cache
from rest_framework.test import APIClient

from accounts.models import User

from .base import APITestCase


class AutenticacaoTests(APITestCase):
    dados = {"username": "nova", "email": "nova@example.org", "first_name": "Nova",
        "password": "Uma frase segura! 729", "password_confirm": "Uma frase segura! 729"}

    def test_csrf_entrega_cookie_e_token(self):
        self.assertTrue(self.token(self.client))
        self.assertIn("csrftoken", self.client.cookies)

    def test_cadastro_sucesso_nao_inicia_sessao(self):
        resposta = self.mutacao(self.client, "post", "auth/cadastro/", self.dados)
        self.assertEqual(resposta.status_code, 201, resposta.content)
        self.assertEqual(set(resposta.json()), {"id", "username", "first_name"})
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertTrue(User.objects.get(username="nova").check_password(self.dados["password"]))

    def test_cadastro_validacao_senhas_email_e_campos(self):
        for campo, valor in (("password", "123"), ("password_confirm", "diverge"), ("email", self.dono.email),
            ("autor", 1), ("is_staff", True), ("desconhecido", "x")):
            with self.subTest(campo=campo):
                cache.clear()
                resposta = self.mutacao(self.client, "post", "auth/cadastro/", {**self.dados, campo: valor})
                self.erro(resposta, 400, "validacao")
                if campo in ("autor", "is_staff", "desconhecido"):
                    self.assertIn(campo, resposta.json()["erro"]["campos"])
        self.assertFalse(User.objects.filter(username="nova").exists())

    def test_csrf_anonimo_exigido_cadastro_e_login(self):
        cliente = APIClient(enforce_csrf_checks=True)
        for caminho in ("cadastro", "login"):
            with self.subTest(caminho=caminho):
                self.erro(self.mutacao(cliente, "post", f"auth/{caminho}/", self.dados), 403, "csrf_invalido")
        token = self.token(cliente)
        resposta = cliente.post("/api/v1/auth/cadastro/", self.dados, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(resposta.status_code, 201, resposta.content)

    def test_login_sessao_me_logout_com_csrf(self):
        User.objects.create_user("nova", "nova@example.org", self.dados["password"], first_name="Nova")
        cliente = APIClient(enforce_csrf_checks=True)
        resposta = cliente.post("/api/v1/auth/login/", {"username": "nova", "password": self.dados["password"]},
            format="json", HTTP_X_CSRFTOKEN=self.token(cliente))
        self.assertEqual(resposta.status_code, 200, resposta.content)
        self.assertEqual(set(resposta.json()), {"id", "username", "first_name"})
        perfil = cliente.get("/api/v1/auth/me/")
        self.assertEqual(perfil.status_code, 200)
        self.assertEqual(perfil.json()["email"], "nova@example.org")
        self.assertIsNone(perfil.json()["ong_id"])
        self.erro(self.mutacao(cliente, "post", "auth/logout/"), 403, "csrf_invalido")
        self.assertEqual(cliente.post("/api/v1/auth/logout/", {}, format="json", HTTP_X_CSRFTOKEN=self.token(cliente)).status_code, 204)
        self.erro(cliente.get("/api/v1/auth/me/"), 403, "autenticacao_necessaria")

    def test_credenciais_erradas_mesmo_erro_usuario_existente_ou_ausente(self):
        respostas = [self.mutacao(self.client, "post", "auth/login/", {"username": nome, "password": "senha errada"})
            for nome in ("dono", "inexistente")]
        for resposta in respostas:
            self.erro(resposta, 400, "credenciais_invalidas")
        self.assertEqual(respostas[0].json(), respostas[1].json())

    def test_login_campos_desconhecidos_e_query(self):
        self.erro(self.mutacao(self.client, "post", "auth/login/", {"username": "dono", "password": "x", "is_superuser": True}), 400, "validacao", "is_superuser")
        self.erro(self.client.get("/api/v1/auth/csrf/?x=1"), 400, "validacao", "x")

    def test_perfil_privado_e_metodos(self):
        self.erro(self.client.get("/api/v1/auth/me/"), 403, "autenticacao_necessaria")
        self.erro(self.mutacao(self.client, "post", "auth/logout/"), 403, "autenticacao_necessaria")
        self.erro(self.client.get("/api/v1/auth/login/"), 405, "metodo_nao_permitido")
        self.erro(self.client.put("/api/v1/auth/cadastro/", {}), 405, "metodo_nao_permitido")
        cliente = self.sessao()
        resposta = cliente.get("/api/v1/auth/me/")
        self.assertEqual(resposta.json()["ong_id"], self.ong.pk)
        self.assertNotIn("is_staff", resposta.json())
        self.assertNotIn("password", resposta.json())

    def test_limite_login_por_ip_e_username(self):
        for _ in range(5):
            self.assertEqual(self.mutacao(self.client, "post", "auth/login/", {"username": "x", "password": "y"}).status_code, 400)
        resposta = self.mutacao(self.client, "post", "auth/login/", {"username": "x", "password": "y"})
        self.erro(resposta, 429, "limite_excedido")
        self.assertGreater(int(resposta["Retry-After"]), 0)
        self.assertEqual(self.mutacao(self.client, "post", "auth/login/", {"username": "outro", "password": "y"}).status_code, 400)
        self.assertEqual(self.client.post("/api/v1/auth/login/", {"username": "x", "password": "y"}, format="json", REMOTE_ADDR="192.0.2.1").status_code, 400)

    def test_limite_cadastro_por_ip(self):
        for _ in range(5):
            self.assertEqual(self.mutacao(self.client, "post", "auth/cadastro/", {}).status_code, 400)
        resposta = self.mutacao(self.client, "post", "auth/cadastro/", {})
        self.erro(resposta, 429, "limite_excedido")
        self.assertIn("Retry-After", resposta)

    def test_corpo_limite_json_tipo_e_erro_parse(self):
        for caminho in ("auth/cadastro/", "auth/login/"):
            with self.subTest(caminho=caminho):
                self.erro(self.mutacao(self.client, "post", caminho, {"texto": "a" * 65536}), 413, "validacao")
        self.erro(self.client.post("/api/v1/auth/login/", "[1]", content_type="application/json"), 400, "validacao")
        self.erro(self.client.post("/api/v1/auth/login/", "{", content_type="application/json"), 400, "validacao")
