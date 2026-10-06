from django.urls import path

from .views import auth, campanhas, contribuicoes, ongs, postagens, relatorios

app_name = "api"
urlpatterns = [
    path("auth/csrf/", auth.CSRFView.as_view(), name="csrf"),
    path("auth/cadastro/", auth.CadastroView.as_view(), name="cadastro"),
    path("auth/login/", auth.LoginView.as_view(), name="login"),
    path("auth/logout/", auth.LogoutView.as_view(), name="logout"),
    path("auth/me/", auth.MeView.as_view(), name="me"),
    path("ongs/", ongs.OngsView.as_view(), name="ongs"),
    path("ongs/<int:pk>/", ongs.OngView.as_view(), name="ong"),
    path("ongs/<int:pk>/reenviar/", ongs.ReenviarView.as_view(), name="reenviar"),
    path("painel/ong/", ongs.PainelOngView.as_view(), name="painel-ong"),
    path("admin/ongs/", ongs.AdminOngsView.as_view(), name="admin-ongs"),
    path("admin/ongs/<int:pk>/analise/", ongs.AnaliseView.as_view(), name="analise"),
    path("campanhas/", campanhas.CampanhasView.as_view(), name="campanhas"),
    path("campanhas/<int:pk>/", campanhas.CampanhaView.as_view(), name="campanha"),
    path("campanhas/<int:pk>/estado/", campanhas.EstadoView.as_view(), name="estado"),
    path("painel/campanhas/", campanhas.PainelCampanhasView.as_view(), name="painel-campanhas"),
    path("painel/campanhas/<int:pk>/", campanhas.PainelCampanhaView.as_view(), name="painel-campanha"),
    path("postagens/", postagens.PostagensView.as_view(), name="postagens"),
    path("postagens/<int:pk>/", postagens.PostagemView.as_view(), name="postagem"),
    path("painel/postagens/", postagens.PainelPostagensView.as_view(), name="painel-postagens"),
    path("painel/postagens/<int:pk>/", postagens.PainelPostagemView.as_view(), name="painel-postagem"),
    path("contribuicoes/", contribuicoes.ContribuicoesView.as_view(), name="contribuicoes"),
    path("contribuicoes/<int:pk>/", contribuicoes.ContribuicaoView.as_view(), name="contribuicao"),
    path("contribuicoes/<int:pk>/cancelar/", contribuicoes.CancelarView.as_view(), name="cancelar"),
    path("contribuicoes/<int:pk>/avaliacao/", contribuicoes.AvaliacaoView.as_view(), name="avaliacao"),
    path("painel/contribuicoes/", contribuicoes.PainelContribuicoesView.as_view(), name="painel-contribuicoes"),
    path("relatorios/campanhas/", relatorios.RelatorioView.as_view(), name="relatorio"),
    path("relatorios/campanhas/exportar/", relatorios.ExportarRelatorioView.as_view(), name="exportar"),
]
