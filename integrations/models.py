from django.db import models


class CacheCep(models.Model):
    """Resposta positiva do ViaCEP guardada por 24 h. Auxiliar: não tem relação com o domínio."""

    cep = models.CharField(max_length=8, primary_key=True)
    logradouro = models.CharField(max_length=200, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100)
    uf = models.CharField(max_length=2)
    expira_em = models.DateTimeField()
