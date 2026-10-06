from decimal import Decimal

from django.db.models import Case, DecimalField, F, Q, Sum, Value, When
from django.db.models.functions import Coalesce


def anotar_totais(campanhas, filtro=Q()):
    """Calcula os totais de todas as campanhas na mesma consulta."""
    medida = Case(
        When(tipo="dinheiro", then=F("contribuicoes__valor")),
        default=F("contribuicoes__quantidade"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    return campanhas.annotate(total_confirmado=Coalesce(
        Sum(medida, filter=filtro & Q(contribuicoes__status="confirmada")),
        Value(Decimal("0.00")), output_field=DecimalField(max_digits=12, decimal_places=2),
    ))
