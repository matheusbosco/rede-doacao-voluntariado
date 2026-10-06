# API DAI v1

Base: `/api/v1/`. Documentação: `/api/docs/` e `/api/redoc/`;
OpenAPI: `/api/schema/`. As interfaces de documentação usam assets de CDN.

Antes de cadastrar, entrar ou modificar dados, faça `GET /api/v1/auth/csrf/`.
Preserve os cookies e envie o token retornado no cabeçalho `X-CSRFToken`.
O login rotaciona o token: consulte-o novamente depois de entrar.
Cadastro não inicia sessão. A API recebe JSON e não processa pagamentos.

As entradas de ONG usam os campos planos do `OngForm` (`cep`, `logradouro`,
`numero`, etc.); as respostas agrupam esses campos em `endereco`.
Postagens recebem `campanha_id`, convertido para o campo do formulário existente.
PATCH preenche os campos omitidos com os valores atuais antes de validar o formulário.

## Decisões nos pontos sem contrato explícito

- Mutação e ações retornam a representação atual com 200; criação retorna 201;
  exclusão e logout retornam 204. DELETE e ações sem parâmetros aceitam corpo vazio
  ou `{}` e rejeitam quaisquer campos enviados.
- Apenas GET, POST, PATCH e DELETE especificados são habilitados. HEAD, OPTIONS e
  PUT retornam 405. Valores inválidos de `page` retornam 400; página inexistente, 404.
  Parâmetros de query repetidos são rejeitados com 400.
- Ordenação das postagens: `-criada_em` (padrão) ou `titulo`; contribuições:
  `-criada_em` (padrão) ou `criada_em`; fila administrativa: `criada_em` (padrão)
  ou `nome`. Empates usam o ID crescente.
- O painel de contribuições retorna todos os estados por padrão; o filtro `status`
  restringe a lista. O contato do autor aparece apenas para o responsável destinatário,
  no detalhe e no painel. Respostas das ações não incluem contato.
- Criar postagem exige ONG aprovada, preservando a regra da tela existente.
  Uma ONG pendente pode editar seus rascunhos; a publicação segue a validação do modelo.
- Relatório é um documento completo, com `campanhas[]`, conforme o contrato explícito;
  não é paginado. A consulta compartilhada passou a retornar também o ID da campanha;
  CSV e números da tela permanecem iguais.
- `AcaoIncompativel` deriva de `ConflitoEstado`: o serviço continua sendo o único
  lugar que rejeita aceite de dinheiro, e a API traduz essa rejeição para 400.
  As transições de estado inválidas continuam retornando 409.
- O CEP usa uma APIView que delega à função existente. Preserva as respostas legadas
  de GET, inclusive erros sem `campos`, códigos `cep_nao_encontrado` e
  `endereco_indisponivel`, status e `Retry-After`. Queries desconhecidas passam a ser
  rejeitadas; erros de método usam o envelope novo. O limite original de 10/min é
  preservado, sem somar os limites globais da API.
- Os exemplos de senha e token CSRF da documentação são textos fictícios, sem contas
  ou sessões associadas. Bandit B105 identifica quatro ocorrências desses exemplos;
  não há supressões.

## Arquivos da implementação

Criados: `api/__init__.py`, `api/README.md`, `api/examples.py`, `api/exceptions.py`,
`api/pagination.py`, `api/parsers.py`, `api/permissions.py`, `api/schema.py`,
`api/throttles.py`, `api/urls.py`.

Criados em `api/serializers/`: `__init__.py`, `auth.py`, `base.py`, `campanhas.py`,
`contribuicoes.py`, `filtros.py`, `ongs.py`, `postagens.py`, `relatorios.py`.

Criados em `api/views/`: `__init__.py`, `auth.py`, `base.py`, `campanhas.py`,
`contribuicoes.py`, `ongs.py`, `postagens.py`, `relatorios.py`.

Criados em `api/tests/`: `__init__.py`, `base.py`, `test_auth.py`, `test_campanhas.py`,
`test_cep.py`, `test_contrato.py`, `test_contribuicoes.py`, `test_fluxo.py`,
`test_ongs.py`, `test_postagens.py`, `test_relatorios.py`, `test_schema.py`.

Alterados: `config/settings.py`, `config/urls.py`, `integrations/views.py`,
`integrations/urls.py`, `contributions/services.py`, `reports/consulta.py`.
