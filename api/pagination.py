from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError


class Paginacao(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_page_size(self, request):
        valor = request.query_params.get("page_size", "20")
        if not valor.isascii() or not valor.isdigit() or not 1 <= int(valor) <= 100:
            raise ValidationError({"page_size": ["Informe um inteiro entre 1 e 100."]})
        return int(valor)
