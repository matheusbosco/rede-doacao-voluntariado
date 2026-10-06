from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from campaigns.models import Campanha
from contributions.services import criar_contribuicao
from organizations.models import Ong, Postagem
from organizations.services import analisar_ong


def dados_ong(**alteracoes):
    dados = {
        "nome": "Amigos da Praça", "descricao": "Apoio à comunidade", "causa": "Educação",
        "cnpj": "12345678000190", "email_contato": "contato@example.org",
        "cep": "01001000", "logradouro": "Praça da Sé", "numero": "10",
        "bairro": "Sé", "cidade": "São Paulo", "uf": "SP",
        "instrucoes_recebimento": "Agende a entrega.",
    }
    return {**dados, **alteracoes}


def dados_campanha(**alteracoes):
    hoje = timezone.localdate()
    return {"titulo": "Cestas", "descricao": "Alimentos", "tipo": "item", "unidade": "cesta",
        "meta": "100.00", "data_inicio": hoje.isoformat(), "data_fim": (hoje + timedelta(days=10)).isoformat(), **alteracoes}


class APITestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dono = User.objects.create_user("dono", "dono@example.org", first_name="Responsável")
        cls.autor = User.objects.create_user("autor", "autor@example.org", first_name="Doadora", last_name="Silva")
        cls.outro = User.objects.create_user("outro", "outro@example.org")
        cls.sem_ong = User.objects.create_user("semong", "semong@example.org")
        cls.admin = User.objects.create_user("equipe", "equipe@example.org", is_staff=True)
        cls.ong = Ong.objects.create(responsavel=cls.dono, **dados_ong())
        cls.ong = analisar_ong(cls.ong.pk, cls.admin, "aprovar")
        cls.outra_ong = Ong.objects.create(responsavel=cls.outro, **dados_ong(cnpj=None, nome="Pendente"))
        cls.campanha = Campanha.objects.create(ong=cls.ong, status="ativa", **dados_campanha())
        cls.rascunho = Campanha.objects.create(ong=cls.ong, **dados_campanha(titulo="Rascunho"))
        cls.dinheiro = Campanha.objects.create(ong=cls.ong, status="ativa", **dados_campanha(tipo="dinheiro", unidade="BRL"))
        cls.outra_campanha = Campanha.objects.create(ong=cls.outra_ong, **dados_campanha())
        cls.postagem = Postagem.objects.create(ong=cls.ong, campanha=cls.campanha, titulo="Notícias", conteudo="Ações", publicada=True)
        cls.postagem_rascunho = Postagem.objects.create(ong=cls.ong, titulo="Privada", conteudo="Em preparação")
        cls.contribuicao = criar_contribuicao(cls.autor, cls.campanha, {"quantidade": "2.00"})

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.client = APIClient()

    def sessao(self, usuario=None, csrf=False):
        cliente = APIClient(enforce_csrf_checks=csrf)
        cliente.force_login(usuario or self.dono)
        return cliente

    def erro(self, resposta, status, codigo, campo=None):
        self.assertEqual(resposta.status_code, status, resposta.content)
        self.assertEqual(set(resposta.json()), {"erro"})
        detalhe = resposta.json()["erro"]
        self.assertEqual(set(detalhe), {"codigo", "mensagem", "campos"})
        self.assertEqual(detalhe["codigo"], codigo)
        if campo:
            self.assertIn(campo, detalhe["campos"])

    def mutacao(self, cliente, metodo, caminho, dados=None):
        return getattr(cliente, metodo)(f"/api/v1/{caminho}", dados or {}, format="json")

    def token(self, cliente):
        resposta = cliente.get("/api/v1/auth/csrf/")
        self.assertEqual(resposta.status_code, 200)
        return resposta.json()["csrf_token"]
