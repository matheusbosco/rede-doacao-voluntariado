from unittest.mock import patch

from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.forms.models import model_to_dict
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .forms import OngForm
from .models import Ong
from .services import ConflitoEstado, analisar_ong, reenviar_ong


def dados_ong(**alteracoes):
    dados = {
        "nome": "Amigos da Praça", "descricao": "Apoio à comunidade", "causa": "Educação",
        "cnpj": "", "email_contato": "contato@example.org", "telefone": "", "site": "",
        "cep": "01001-000", "logradouro": "Praça da Sé", "numero": "10", "complemento": "",
        "bairro": "Sé", "cidade": "São Paulo", "uf": "SP",
        "instrucoes_recebimento": "Recebemos de segunda a sexta.",
    }
    dados.update(alteracoes)
    return dados


class OngTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dono = User.objects.create_user("dono", "responsavel@example.org")
        cls.outro = User.objects.create_user("outro", "outro@example.org")
        cls.admin = User.objects.create_user("equipe", "equipe@example.org", is_staff=True)
        cls.ong = Ong.objects.create(responsavel=cls.dono, **dados_ong(cep="01001000", cnpj="12345678000190"))

    def aprovar(self):
        self.ong = analisar_ong(self.ong.pk, self.admin, "aprovar")

    def editar(self, **alteracoes):
        dados = model_to_dict(self.ong, fields=OngForm.Meta.fields)
        dados.update(alteracoes)
        self.client.force_login(self.dono)
        return self.client.post(reverse("ong-editar", args=[self.ong.pk]), dados)

    def test_lista_publica_so_mostra_aprovadas(self):
        pendente = Ong.objects.create(responsavel=self.outro, **dados_ong(nome="ONG pendente", cep="01001000"))
        self.aprovar()
        resposta = self.client.get(reverse("ong-lista"))
        self.assertContains(resposta, self.ong.nome)
        self.assertNotContains(resposta, pendente.nome)
        analisar_ong(pendente.pk, self.admin, "recusar", "Dados incompletos")
        self.assertNotContains(self.client.get(reverse("ong-lista")), pendente.nome)

    def test_lista_respeita_cada_filtro(self):
        self.aprovar()
        filtros = (
            {"q": "amigos"}, {"q": "COMUNIDADE"}, {"q": "educação"},
            {"cidade": "paulo"}, {"bairro": "sé"}, {"uf": "SP"},
            {"q": "amigos", "cidade": "São", "bairro": "Sé", "uf": "SP"},
        )
        for filtro in filtros:
            with self.subTest(filtro=filtro):
                resposta = self.client.get(reverse("ong-lista"), filtro)
                self.assertEqual(list(resposta.context["pagina"]), [self.ong])
        for filtro in ({"q": "ausente"}, {"cidade": "Brasília"}, {"bairro": "Centro"}, {"uf": "DF"}):
            with self.subTest(filtro=filtro):
                resposta = self.client.get(reverse("ong-lista"), filtro)
                self.assertEqual(list(resposta.context["pagina"]), [])
                self.assertContains(resposta, "Nenhum resultado para estes filtros")
                self.assertContains(resposta, "Limpar filtros")

    def test_filtro_invalido_mostra_erro_e_lista_vazia(self):
        self.aprovar()
        for filtro, campo in (({"uf": "XX"}, "uf"), ({"q": "a" * 101}, "q")):
            with self.subTest(filtro=filtro):
                resposta = self.client.get(reverse("ong-lista"), filtro)
                self.assertTrue(resposta.context["form"].errors[campo])
                self.assertEqual(list(resposta.context["pagina"]), [])
                self.assertContains(resposta, 'role="alert"')

    def test_lista_ordena_e_pagina_em_20_preservando_filtros(self):
        self.aprovar()
        for indice in range(21):
            usuario = User.objects.create_user(f"dono{indice}", f"dono{indice}@example.org")
            Ong.objects.create(
                responsavel=usuario, **dados_ong(nome=f"Grupo {indice:02}", cep="01001000"),
                status=Ong.Status.APROVADA, analisada_por=self.admin, analisada_em=timezone.now(),
            )
        resposta = self.client.get(reverse("ong-lista"), {"uf": "SP"})
        pagina = resposta.context["pagina"]
        self.assertEqual(len(pagina), 20)
        self.assertEqual(pagina.paginator.count, 22)
        self.assertEqual(pagina[0].nome, "Amigos da Praça")
        self.assertContains(resposta, "uf=SP&amp;page=2")
        segunda = self.client.get(reverse("ong-lista"), {"uf": "SP", "page": 2})
        self.assertEqual(len(segunda.context["pagina"]), 2)

    def test_detalhe_pendente_so_dono_e_staff(self):
        url = reverse("ong-detalhe", args=[self.ong.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        for usuario, status in ((self.outro, 404), (self.dono, 200), (self.admin, 200)):
            with self.subTest(usuario=usuario.username):
                self.client.force_login(usuario)
                self.assertEqual(self.client.get(url).status_code, status)

    def test_detalhe_publico_nao_expoe_cnpj_ou_email_do_responsavel(self):
        self.aprovar()
        url = reverse("ong-detalhe", args=[self.ong.pk])
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 200)
        self.assertNotContains(resposta, self.ong.cnpj)
        self.assertNotContains(resposta, self.dono.email)
        self.assertContains(resposta, self.ong.email_contato)
        self.assertContains(resposta, "Aprovação não garante idoneidade; confira as informações")
        self.client.force_login(self.outro)
        self.assertNotContains(self.client.get(url), self.ong.cnpj)
        for usuario in (self.dono, self.admin):
            self.client.force_login(usuario)
            self.assertContains(self.client.get(url), self.ong.cnpj)

    def test_criar_ong_pendente_com_responsavel_certo(self):
        self.client.force_login(self.outro)
        resposta = self.client.post(reverse("ong-nova"), dados_ong(
            responsavel=self.dono.pk, status="aprovada", uf="sp", cnpj="98.765.432/0001-10",
        ))
        ong = Ong.objects.get(responsavel=self.outro)
        self.assertRedirects(resposta, reverse("ong-detalhe", args=[ong.pk]), fetch_redirect_response=False)
        self.assertEqual(ong.status, Ong.Status.PENDENTE)
        self.assertEqual(ong.cep, "01001000")
        self.assertEqual(ong.cnpj, "98765432000110")
        self.assertEqual(ong.uf, "SP")
        self.assertIsNone(ong.analisada_por)
        self.assertContains(self.client.get(resposta.url), "Ela fica em análise")

    def test_segunda_ong_do_usuario_e_bloqueada(self):
        self.client.force_login(self.dono)
        for metodo in (self.client.get, self.client.post):
            resposta = metodo(reverse("ong-nova"), dados_ong())
            self.assertRedirects(resposta, reverse("ong-editar", args=[self.ong.pk]))
        self.assertEqual(Ong.objects.filter(responsavel=self.dono).count(), 1)

    def test_cadastro_exige_login(self):
        url = reverse("ong-nova")
        self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")

    def test_outro_usuario_nao_edita_nem_exclui(self):
        self.client.force_login(self.outro)
        self.assertEqual(self.client.get(reverse("ong-editar", args=[self.ong.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("ong-editar", args=[self.ong.pk]), dados_ong()).status_code, 404)
        self.assertEqual(self.client.post(reverse("ong-excluir", args=[self.ong.pk])).status_code, 404)
        self.assertTrue(Ong.objects.filter(pk=self.ong.pk).exists())

    def test_editar_identificacao_ou_endereco_volta_para_pendente(self):
        alteracoes = {
            "nome": "Novo nome", "cnpj": "98765432000110", "cep": "70000000",
            "logradouro": "Rua Nova", "numero": "11", "complemento": "Sala 1",
            "bairro": "Centro", "cidade": "Brasília", "uf": "DF",
        }
        for campo, valor in alteracoes.items():
            with self.subTest(campo=campo):
                self.aprovar()
                resposta = self.editar(**{campo: valor})
                self.assertEqual(resposta.status_code, 302)
                self.ong.refresh_from_db()
                self.assertEqual(self.ong.status, Ong.Status.PENDENTE)
                self.assertIsNone(self.ong.analisada_por)
                self.assertIsNone(self.ong.analisada_em)
                self.assertEqual(self.ong.motivo_analise, "")

    def test_editar_descricao_contato_site_e_instrucoes_mantem_aprovacao(self):
        self.aprovar()
        data_analise = self.ong.analisada_em
        resposta = self.editar(
            descricao="Nova descrição", email_contato="novo@example.org", telefone="11999999999",
            site="https://example.org", instrucoes_recebimento="Aos sábados", causa="Saúde",
        )
        self.assertEqual(resposta.status_code, 302)
        self.ong.refresh_from_db()
        self.assertEqual(self.ong.status, Ong.Status.APROVADA)
        self.assertEqual(self.ong.descricao, "Nova descrição")
        self.assertEqual(self.ong.analisada_em, data_analise)

    def test_editar_apenas_formatacao_de_cep_cnpj_e_uf_mantem_aprovacao(self):
        self.aprovar()
        self.assertEqual(self.editar(cep="01001-000", cnpj="12.345.678/0001-90", uf="sp").status_code, 302)
        self.ong.refresh_from_db()
        self.assertEqual(self.ong.status, Ong.Status.APROVADA)

    def test_excluir_so_por_post_e_pelo_dono(self):
        self.client.force_login(self.dono)
        url = reverse("ong-excluir", args=[self.ong.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url), reverse("painel"))
        self.assertFalse(Ong.objects.filter(pk=self.ong.pk).exists())

    def test_exclusao_com_dependencias_mostra_mensagem(self):
        self.client.force_login(self.dono)
        with patch("organizations.models.Ong.delete", side_effect=ProtectedError("Dependência", [self.ong])):
            resposta = self.client.post(reverse("ong-excluir", args=[self.ong.pk]), follow=True)
        self.assertContains(resposta, "há dependências vinculadas")
        self.assertTrue(Ong.objects.filter(pk=self.ong.pk).exists())

    def test_staff_aprova(self):
        self.client.force_login(self.admin)
        resposta = self.client.post(reverse("admin-ong-analise", args=[self.ong.pk]), {"decisao": "aprovar"})
        self.assertRedirects(resposta, reverse("admin-ong-fila"))
        self.ong.refresh_from_db()
        self.assertEqual(self.ong.status, Ong.Status.APROVADA)
        self.assertEqual(self.ong.analisada_por, self.admin)
        self.assertIsNotNone(self.ong.analisada_em)

    def test_staff_recusa_com_motivo(self):
        self.client.force_login(self.admin)
        resposta = self.client.post(reverse("admin-ong-analise", args=[self.ong.pk]), {
            "decisao": "recusar", "motivo": "  Falta documentação  ",
        })
        self.assertRedirects(resposta, reverse("admin-ong-fila"))
        self.ong.refresh_from_db()
        self.assertEqual(self.ong.status, Ong.Status.RECUSADA)
        self.assertEqual(self.ong.motivo_analise, "Falta documentação")
        self.client.force_login(self.dono)
        self.assertContains(self.client.get(reverse("ong-detalhe", args=[self.ong.pk])), "Motivo da recusa: Falta documentação")

    def test_recusar_sem_motivo_falha_sem_alterar(self):
        self.client.force_login(self.admin)
        resposta = self.client.post(reverse("admin-ong-analise", args=[self.ong.pk]), {
            "decisao": "recusar", "motivo": "  ",
        }, follow=True)
        self.assertContains(resposta, "Informe o motivo da recusa.")
        self.ong.refresh_from_db()
        self.assertEqual(self.ong.status, Ong.Status.PENDENTE)
        self.assertIsNone(self.ong.analisada_em)

    def test_decisao_invalida_e_motivo_longo_falham(self):
        for decisao, motivo in (("outra", ""), ("recusar", "a" * 501)):
            with self.subTest(decisao=decisao), self.assertRaises(ValueError):
                analisar_ong(self.ong.pk, self.admin, decisao, motivo)
        self.ong.refresh_from_db()
        self.assertEqual(self.ong.status, Ong.Status.PENDENTE)

    def test_nao_staff_recebe_403_na_fila_e_analise(self):
        for usuario in (None, self.dono, self.outro):
            if usuario:
                self.client.force_login(usuario)
            with self.subTest(usuario=usuario):
                self.assertEqual(self.client.get(reverse("admin-ong-fila")).status_code, 403)
                self.assertEqual(self.client.post(reverse("admin-ong-analise", args=[self.ong.pk]), {"decisao": "aprovar"}).status_code, 403)
        with self.assertRaises(ValueError):
            analisar_ong(self.ong.pk, self.dono, "aprovar")

    def test_analisar_duas_vezes_nao_altera_segunda_vez(self):
        self.aprovar()
        antes = model_to_dict(self.ong)
        with self.assertRaises(ConflitoEstado):
            analisar_ong(self.ong.pk, self.admin, "recusar", "Outro motivo")
        self.client.force_login(self.admin)
        resposta = self.client.post(reverse("admin-ong-analise", args=[self.ong.pk]), {
            "decisao": "recusar", "motivo": "Outro motivo",
        }, follow=True)
        self.assertContains(resposta, "ONG já analisada")
        self.ong.refresh_from_db()
        self.assertEqual(model_to_dict(self.ong), antes)

    def test_fila_so_lista_pendentes(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("admin-ong-fila")), self.ong.nome)
        self.aprovar()
        self.assertNotContains(self.client.get(reverse("admin-ong-fila")), self.ong.nome)

    def test_analise_so_aceita_post(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("admin-ong-analise", args=[self.ong.pk])).status_code, 405)

    def test_reenviar_recusada_volta_a_pendente_so_pelo_dono(self):
        analisar_ong(self.ong.pk, self.admin, "recusar", "Corrija os dados")
        url = reverse("ong-reenviar", args=[self.ong.pk])
        for usuario in (self.outro, self.admin):
            self.client.force_login(usuario)
            self.assertEqual(self.client.post(url).status_code, 404)
        self.client.force_login(self.dono)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url), reverse("ong-detalhe", args=[self.ong.pk]))
        self.ong.refresh_from_db()
        self.assertEqual(self.ong.status, Ong.Status.PENDENTE)
        self.assertIsNone(self.ong.analisada_por)
        self.assertIsNone(self.ong.analisada_em)
        self.assertEqual(self.ong.motivo_analise, "")

    def test_reenviar_pendente_ou_aprovada_e_rejeitado(self):
        with self.assertRaises(ConflitoEstado):
            reenviar_ong(self.ong)
        self.aprovar()
        self.client.force_login(self.dono)
        resposta = self.client.post(reverse("ong-reenviar", args=[self.ong.pk]), follow=True)
        self.assertContains(resposta, "Somente ONGs recusadas")
        self.ong.refresh_from_db()
        self.assertEqual(self.ong.status, Ong.Status.APROVADA)

    def test_reenviar_verifica_estado_atual_do_banco(self):
        antiga = analisar_ong(self.ong.pk, self.admin, "recusar", "Corrija")
        reenviar_ong(antiga)
        analisar_ong(self.ong.pk, self.admin, "aprovar")
        with self.assertRaises(ConflitoEstado):
            reenviar_ong(antiga)
        self.ong.refresh_from_db()
        self.assertEqual(self.ong.status, Ong.Status.APROVADA)

    def test_minha_redireciona_para_detalhe_ou_cadastro(self):
        self.client.force_login(self.dono)
        self.assertRedirects(self.client.get(reverse("ong-minha")), reverse("ong-detalhe", args=[self.ong.pk]))
        self.client.force_login(self.outro)
        self.assertRedirects(self.client.get(reverse("ong-minha")), reverse("ong-nova"))

    def test_painel_tem_links_da_ong_e_fila_para_staff(self):
        self.client.force_login(self.dono)
        self.assertContains(self.client.get(reverse("painel")), "Minha ONG")
        self.client.force_login(self.outro)
        resposta = self.client.get(reverse("painel"))
        self.assertContains(resposta, "Cadastrar ONG")
        self.assertNotContains(resposta, reverse("admin-ong-fila"))
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("painel")), reverse("admin-ong-fila"))

    def test_constraints_rejeitam_estados_inconsistentes(self):
        estados = (
            {"status": "pendente", "analisada_por": self.admin},
            {"status": "pendente", "analisada_em": timezone.now()},
            {"status": "aprovada"},
            {"status": "aprovada", "analisada_por": self.admin},
            {"status": "aprovada", "analisada_em": timezone.now()},
            {"status": "recusada", "motivo_analise": "Motivo"},
            {"status": "recusada", "analisada_por": self.admin, "motivo_analise": "Motivo"},
            {"status": "recusada", "analisada_em": timezone.now(), "motivo_analise": "Motivo"},
            {"status": "recusada", "analisada_por": self.admin, "analisada_em": timezone.now()},
        )
        for estado in estados:
            with self.subTest(estado=estado), self.assertRaises(IntegrityError):
                with transaction.atomic():
                    Ong.objects.filter(pk=self.ong.pk).update(**estado)
        self.ong.refresh_from_db()
        self.assertEqual(self.ong.status, Ong.Status.PENDENTE)

    def test_cnpj_duplicado_rejeitado_no_cadastro(self):
        self.client.force_login(self.outro)
        resposta = self.client.post(reverse("ong-nova"), dados_ong(cnpj="12.345.678/0001-90"))
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("cnpj", resposta.context["form"].errors)
        self.assertFalse(Ong.objects.filter(responsavel=self.outro).exists())
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Ong.objects.create(responsavel=self.outro, **dados_ong(cep="01001000", cnpj=self.ong.cnpj))

    def test_cnpj_vazio_duas_vezes_e_aceito_com_null(self):
        for usuario in (self.outro, self.admin):
            self.client.force_login(usuario)
            resposta = self.client.post(reverse("ong-nova"), dados_ong())
            self.assertEqual(resposta.status_code, 302)
            self.assertIsNone(Ong.objects.get(responsavel=usuario).cnpj)
        self.assertEqual(Ong.objects.filter(cnpj__isnull=True).count(), 2)

    def test_formulario_rejeita_cep_cnpj_uf_site_e_textos_invalidos(self):
        alteracoes = (
            ("cep", "123"), ("cnpj", "123"), ("cnpj", "abc"), ("uf", "XX"),
            ("site", "ftp://example.org"), ("descricao", "a" * 5001),
            ("instrucoes_recebimento", "a" * 2001),
        )
        for campo, valor in alteracoes:
            with self.subTest(campo=campo):
                form = OngForm(dados_ong(**{campo: valor}))
                self.assertFalse(form.is_valid())
                self.assertIn(campo, form.errors)

    def test_formulario_invalido_exibe_erros_e_consulta_cep(self):
        self.client.force_login(self.outro)
        resposta = self.client.post(reverse("ong-nova"), dados_ong(cep="123"))
        self.assertContains(resposta, "Informe um CEP com 8 dígitos.")
        self.assertContains(resposta, "Consultar CEP")
        self.assertContains(resposta, 'aria-live="polite"')
        self.assertContains(resposta, 'for="id_cep"')

    def test_criar_exige_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.outro)
        self.assertEqual(cliente.post(reverse("ong-nova"), dados_ong()).status_code, 403)
        self.assertFalse(Ong.objects.filter(responsavel=self.outro).exists())
