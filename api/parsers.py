from io import BytesIO

from rest_framework.parsers import JSONParser

from .exceptions import ErroAPI


class JSONLimitado(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        conteudo = stream.read(65537)
        if len(conteudo) > 65536:
            raise ErroAPI("validacao", "O corpo JSON deve ter no máximo 64 KiB.", 413)
        return super().parse(BytesIO(conteudo), media_type, parser_context)
