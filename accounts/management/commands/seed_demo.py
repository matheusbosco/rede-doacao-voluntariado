import os
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from campaigns.models import Campanha
from campaigns.services import mudar_estado
from contributions.models import Contribuicao
from contributions.services import avaliar_contribuicao, cancelar_contribuicao, criar_contribuicao
from organizations.models import Ong, Postagem
from organizations.services import analisar_ong


USUARIOS = ("admin_demo", "ong_df_demo", "ong_sp_demo", "ong_pendente_demo", "doador_1_demo", "doador_2_demo")
CAMPANHAS = (
    (0, "Demo: apoio à educação", "dinheiro", "BRL", "1000", "ativa"),
    (0, "Demo: cestas solidárias", "item", "cesta", "100", "ativa"),
    (1, "Demo: horas de leitura", "horas", "hora", "80", "pausada"),
    (1, "Demo: biblioteca comunitária", "dinheiro", "BRL", "500", "encerrada"),
    (2, "Demo: materiais escolares", "item", "kit", "50", "rascunho"),
)
POSTAGENS = ("Demo: boas-vindas", "Demo: resultados da biblioteca", "Demo: planejamento")
CONTRIBUICOES = (
    (0, 0, "150.00", "confirmada"),
    (1, 1, "3", "confirmada"),
    (2, 0, "2.5", "confirmada"),
    (3, 1, "80.00", "confirmada"),
    (1, 0, "1", "declarada"),
    (2, 1, "4", "aceita"),
    (0, 1, "25.00", "recusada"),
    (1, 1, "2", "cancelada"),
)


class Command(BaseCommand):
    help = "Cria dados fictícios de demonstração, sem duplicar registros."

    def add_arguments(self, parser):
        parser.add_argument("--limpar", action="store_true", help="Remove somente os registros de demonstração.")
        parser.add_argument("--permitir-producao", action="store_true", help="Permite executar sem DEBUG.")

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["permitir_producao"]:
            raise CommandError("O seed exige DEBUG=true ou --permitir-producao.")
        with transaction.atomic():
            # Um username reservado com outro e-mail não pertence ao seed.
            for username in USUARIOS:
                if User.objects.filter(username=username).exclude(email=f"{username}@example.org").exists():
                    raise CommandError(f"O username {username} já pertence a outra conta.")
            if options["limpar"]:
                self.limpar()
                self.stdout.write(self.style.SUCCESS("Dados de demonstração removidos."))
                return
            senha = os.environ.get("DEMO_PASSWORD")
            gerada = not senha
            if gerada:
                senha = secrets.token_urlsafe(24)
            usuarios = []
            for username in USUARIOS:
                usuario, _ = User.objects.get_or_create(
                    username=username, email=f"{username}@example.org",
                    defaults={"first_name": "Equipe demo" if username == "admin_demo" else username},
                )
                usuario.is_staff = username == "admin_demo"
                usuario.set_password(senha)
                usuario.full_clean()
                usuario.save()
                usuarios.append(usuario)
            ongs = []
            for indice, (nome, cidade, uf) in enumerate((
                ("Demo: Sementes do Amanhã", "Brasília", "DF"),
                ("Demo: Pontes da Leitura", "São Paulo", "SP"),
                ("Demo: Novos Caminhos", "Brasília", "DF"),
            )):
                ong, criada = Ong.objects.get_or_create(
                    responsavel=usuarios[indice + 1],
                    defaults={
                        "nome": nome, "descricao": "ONG fictícia para demonstração do DAI.",
                        "causa": "Educação", "email_contato": f"contato_demo_{indice}@example.org",
                        "cep": "70000000" if uf == "DF" else "01000000",
                        "logradouro": "Rua Fictícia", "numero": str(indice + 1),
                        "bairro": "Bairro Demonstração", "cidade": cidade, "uf": uf,
                        "instrucoes_recebimento": "Consulte contato@example.org (dados fictícios).",
                    },
                )
                if ong.nome != nome or ong.email_contato != f"contato_demo_{indice}@example.org":
                    raise CommandError("O responsável demo possui uma ONG que não pertence ao seed.")
                if criada and indice < 2:
                    ong = analisar_ong(ong.pk, usuarios[0], "aprovar")
                ong.full_clean()
                ongs.append(ong)
            hoje = timezone.localdate()
            campanhas = []
            novas = []
            for indice, titulo, tipo, unidade, meta, status in CAMPANHAS:
                campanha, criada = Campanha.objects.get_or_create(
                    ong=ongs[indice], titulo=titulo,
                    defaults={"descricao": "Campanha fictícia de demonstração.", "tipo": tipo,
                              "unidade": unidade, "meta": meta, "data_inicio": hoje,
                              "data_fim": hoje + timedelta(days=90)},
                )
                campanha.full_clean()
                if criada and status != "rascunho":
                    campanha = mudar_estado(campanha, "publicar")
                campanhas.append(campanha)
                novas.append(criada)
            for indice, (campanha_indice, doador, medida, status) in enumerate(CONTRIBUICOES):
                campanha = campanhas[campanha_indice]
                autor = usuarios[4 + doador]
                observacao = f"Demonstração fictícia DAI {indice + 1}."
                if Contribuicao.objects.filter(campanha=campanha, autor=autor, observacao=observacao).exists():
                    continue
                campo = "valor" if campanha.tipo == "dinheiro" else "quantidade"
                contribuicao = criar_contribuicao(autor, campanha, {campo: medida, "observacao": observacao})
                dono = campanha.ong.responsavel
                if status in ("aceita", "confirmada") and campanha.tipo != "dinheiro":
                    avaliar_contribuicao(contribuicao.pk, dono, "aceitar")
                if status == "confirmada":
                    avaliar_contribuicao(contribuicao.pk, dono, "confirmar")
                elif status == "recusada":
                    avaliar_contribuicao(contribuicao.pk, dono, "recusar", "Exemplo fictício: oferta incompatível com a campanha.")
                elif status == "cancelada":
                    cancelar_contribuicao(contribuicao.pk, autor)
            for campanha, criada, dados in zip(campanhas, novas, CAMPANHAS, strict=True):
                if criada and dados[5] in ("pausada", "encerrada"):
                    mudar_estado(campanha, "pausar" if dados[5] == "pausada" else "encerrar")
            for indice, titulo in enumerate(POSTAGENS):
                postagem, _ = Postagem.objects.get_or_create(
                    ong=ongs[indice], titulo=titulo,
                    defaults={"conteudo": "Notícia fictícia de demonstração, sem dados reais.",
                              "campanha": campanhas[(0, 3, 4)[indice]], "publicada": indice < 2},
                )
                postagem.full_clean()
        if gerada:
            self.stdout.write(f"Senha gerada para as contas demo: {senha}")
        self.stdout.write(self.style.SUCCESS("Dados fictícios de demonstração disponíveis."))

    def limpar(self):
        usuarios = User.objects.filter(username__in=USUARIOS, email__in=[f"{nome}@example.org" for nome in USUARIOS])
        ongs = Ong.objects.filter(responsavel__in=usuarios, email_contato__in=[f"contato_demo_{i}@example.org" for i in range(3)])
        campanhas = Campanha.objects.filter(ong__in=ongs, titulo__in=[dados[1] for dados in CAMPANHAS])
        Contribuicao.objects.filter(
            campanha__in=campanhas, autor__in=usuarios,
            observacao__in=[f"Demonstração fictícia DAI {i + 1}." for i in range(len(CONTRIBUICOES))],
        ).delete()
        Postagem.objects.filter(ong__in=ongs, titulo__in=POSTAGENS).delete()
        campanhas.delete()
        ongs.delete()
        usuarios.delete()
