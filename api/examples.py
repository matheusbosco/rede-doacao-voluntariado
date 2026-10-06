"""Respostas ilustrativas da documentação, sem dados pessoais reais."""
ENDERECO = {"cep": "01001000", "logradouro": "Praça da Sé", "numero": "10", "complemento": "",
    "bairro": "Sé", "cidade": "São Paulo", "uf": "SP"}
ONG = {"id": 1, "nome": "Amigos", "descricao": "Apoio social", "causa": "Educação",
    "email_contato": "contato@example.org", "telefone": "", "site": "", "endereco": ENDERECO,
    "instrucoes_recebimento": "Agende a entrega."}
INSTANTES = {"criada_em": "2026-10-06T10:00:00-03:00", "atualizada_em": "2026-10-06T10:00:00-03:00"}
CAMPANHA = {"id": 1, "ong_id": 1, "titulo": "Cestas", "descricao": "Alimentos", "tipo": "item",
    "unidade": "cesta", "meta": "100.00", "data_inicio": "2026-10-06", "data_fim": "2026-10-16",
    "status": "ativa", "total_confirmado": "15.00", "percentual_meta": "15.00", "disponivel": True, **INSTANTES}
CONTRIBUICAO = {"id": 1, "campanha_id": 1, "tipo": "item", "valor": None, "quantidade": "15.00",
    "observacao": "Entrega agendada", "status": "declarada", "motivo_avaliacao": "", "avaliada_em": None, **INSTANTES}
RESPOSTAS = {
    "CSRFResposta": {"csrf_token": "token emitido pelo servidor"},
    "UsuarioBasico": {"id": 1, "username": "maria", "first_name": "Maria"},
    "MeuUsuario": {"id": 1, "username": "maria", "first_name": "Maria", "last_name": "Silva", "email": "maria@example.org", "ong_id": 1},
    "OngPublica": ONG,
    "OngPrivada": {**ONG, "cnpj": None, "status": "pendente", "motivo_analise": "", **INSTANTES},
    "CampanhaResposta": CAMPANHA,
    "PostagemResposta": {"id": 1, "ong_id": 1, "campanha_id": 1, "titulo": "Novidades", "conteudo": "Doações recebidas", "publicada": True, **INSTANTES},
    "ContribuicaoResposta": CONTRIBUICAO,
    "ContribuicaoDetalhe": CONTRIBUICAO,
    "ContribuicaoRecebida": {**CONTRIBUICAO, "contato_autor": {"nome": "Maria Silva", "email": "maria@example.org"}},
    "RelatorioResposta": {"inicio": "2026-10-06", "fim": "2026-10-06", "gerado_em": "2026-10-06T10:00:00-03:00",
        "criterio_periodo": "criacao_contribuicao", "campanhas": [{"campanha_id": 1, "titulo": "Cestas", "tipo": "item",
            "unidade": "cesta", "meta": "100.00", "total_confirmado": "15.00", "declaradas": 0, "aceitas": 0,
            "confirmadas": 1, "recusadas": 0, "canceladas": 0}]},
}
