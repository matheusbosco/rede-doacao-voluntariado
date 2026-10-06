from rest_framework import serializers


class LinhaRelatorio(serializers.Serializer):
    campanha_id = serializers.IntegerField(source="id")
    titulo = serializers.CharField()
    tipo = serializers.CharField()
    unidade = serializers.CharField()
    meta = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_confirmado = serializers.DecimalField(max_digits=24, decimal_places=2)
    declaradas = serializers.IntegerField()
    aceitas = serializers.IntegerField()
    confirmadas = serializers.IntegerField()
    recusadas = serializers.IntegerField()
    canceladas = serializers.IntegerField()


class RelatorioResposta(serializers.Serializer):
    inicio = serializers.DateField()
    fim = serializers.DateField()
    gerado_em = serializers.DateTimeField()
    criterio_periodo = serializers.CharField(default="criacao_contribuicao")
    campanhas = LinhaRelatorio(many=True)
