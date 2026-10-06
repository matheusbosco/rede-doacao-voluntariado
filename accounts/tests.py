from django.test import Client, TestCase
from django.urls import reverse

from .models import User

SENHA = "Senha-Forte-123"


def dados_cadastro(**extra):
    base = {
        "first_name": "Ana", "last_name": "Souza", "username": "ana",
        "email": "ana@example.org", "password1": SENHA, "password2": SENHA,
    }
    base.update(extra)
    return base


class CadastroTests(TestCase):
    def test_cria_conta_com_senha_em_hash(self):
        resposta = self.client.post(reverse("cadastro"), dados_cadastro())
        self.assertRedirects(resposta, reverse("login"))
        usuario = User.objects.get(username="ana")
        self.assertNotEqual(usuario.password, SENHA)
        self.assertTrue(usuario.check_password(SENHA))
        self.assertFalse(usuario.is_staff)

    def test_email_duplicado_ignora_maiusculas(self):
        User.objects.create_user("outro", "ANA@example.org", SENHA, first_name="Outro")
        resposta = self.client.post(reverse("cadastro"), dados_cadastro())
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(User.objects.filter(username="ana").exists())
        self.assertContains(resposta, "Já existe uma conta com este e-mail.")

    def test_senha_fraca_e_rejeitada(self):
        resposta = self.client.post(
            reverse("cadastro"), dados_cadastro(password1="12345678", password2="12345678")
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(User.objects.filter(username="ana").exists())

    def test_senhas_diferentes_sao_rejeitadas(self):
        resposta = self.client.post(reverse("cadastro"), dados_cadastro(password2="Outra-Senha-456"))
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(User.objects.filter(username="ana").exists())

    def test_cadastro_exige_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        resposta = cliente.post(reverse("cadastro"), dados_cadastro())
        self.assertEqual(resposta.status_code, 403)
        self.assertFalse(User.objects.filter(username="ana").exists())


class SessaoTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("ana", "ana@example.org", SENHA, first_name="Ana")

    def test_login_valido_abre_o_painel(self):
        resposta = self.client.post(reverse("login"), {"username": "ana", "password": SENHA})
        self.assertRedirects(resposta, reverse("painel"))

    def test_login_invalido_nao_revela_se_usuario_existe(self):
        resposta = self.client.post(reverse("login"), {"username": "ana", "password": "errada"})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Usuário ou senha incorretos.")
        resposta = self.client.post(reverse("login"), {"username": "ninguem", "password": "errada"})
        self.assertContains(resposta, "Usuário ou senha incorretos.")

    def test_login_exige_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        resposta = cliente.post(reverse("login"), {"username": "ana", "password": SENHA})
        self.assertEqual(resposta.status_code, 403)

    def test_painel_exige_login(self):
        resposta = self.client.get(reverse("painel"))
        self.assertRedirects(resposta, f"{reverse('login')}?next={reverse('painel')}")

    def test_logout_so_por_post_e_encerra_a_sessao(self):
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        resposta = self.client.post(reverse("logout"))
        self.assertRedirects(resposta, reverse("login"))
        self.assertEqual(self.client.get(reverse("painel")).status_code, 302)
