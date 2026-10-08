# API do DAI

A versão atual usa `/api/v1/`. As operações abaixo recebem e devolvem JSON. Os exemplos são fictícios. IDs e horários servem só para mostrar a estrutura; não precisam ser iguais aos dados de outra instalação. O [OpenAPI](openapi.yaml) reúne o contrato completo.

## 1. Encontrar ONGs

`GET /api/v1/ongs/?q=ONG%20Exemplo%20DAI&cidade=Bras%C3%ADlia`

**Quem pode usar:** Visitante ou conta autenticada.

A busca mostra apenas ONGs aprovadas. Use q, cidade, bairro e uf para restringir a lista.

**Envio:**

Sem corpo. Os filtros vão na URL.

**Retorno de exemplo — HTTP 200:**

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 4,
      "nome": "ONG Aprender",
      "descricao": "Organização fictícia que recebe materiais escolares.",
      "causa": "Educacao",
      "email_contato": "contato@example.org",
      "telefone": "",
      "site": "",
      "endereco": {
        "cep": "70000000",
        "logradouro": "Rua Ficticia",
        "numero": "10",
        "complemento": "",
        "bairro": "Bairro Demonstracao",
        "cidade": "Brasília",
        "uf": "DF"
      },
      "instrucoes_recebimento": "Combine a entrega pelo contato da ONG. Dados ficticios."
    }
  ]
}
```

**Status previstos:** 200, 400 e 404.

## 2. Encontrar campanhas

`GET /api/v1/campanhas/?q=Campanha%20Exemplo%20DAI&tipo=item&cidade=Bras%C3%ADlia&disponivel=true`

**Quem pode usar:** Visitante ou conta autenticada.

Use q, tipo, cidade, bairro, uf, ong_id e disponivel. Tipo aceita dinheiro, item ou horas.

**Envio:**

Sem corpo. Os filtros vão na URL.

**Retorno de exemplo — HTTP 200:**

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 6,
      "ong_id": 4,
      "titulo": "Materiais para estudar",
      "descricao": "Recebimento de cestas para demonstracao.",
      "tipo": "item",
      "unidade": "cesta",
      "meta": "100.00",
      "data_inicio": "2026-10-08",
      "data_fim": "2026-12-11",
      "status": "ativa",
      "total_confirmado": "0.00",
      "percentual_meta": "0.00",
      "disponivel": true,
      "criada_em": "2026-10-08T12:12:01.557722-03:00",
      "atualizada_em": "2026-10-08T12:12:01.583255-03:00"
    }
  ]
}
```

**Status previstos:** 200, 400 e 404.

## 3. Criar conta

`POST /api/v1/auth/cadastro/`

**Quem pode usar:** Pessoa ainda sem conta.

Os dois campos de senha precisam ser iguais. E-mail e username não podem repetir cadastros existentes.

**Envio:**

```json
{
  "username": "julia",
  "email": "julia@example.org",
  "first_name": "Julia",
  "password": "Senha somente de exemplo! 2026",
  "password_confirm": "Senha somente de exemplo! 2026"
}
```

**Retorno de exemplo — HTTP 201:**

```json
{
  "id": 7,
  "username": "julia",
  "first_name": "Julia"
}
```

**Status previstos:** 201, 400 e 403.

## 4. Entrar

`POST /api/v1/auth/login/`

**Quem pode usar:** Pessoa com uma conta ativa.

Usa nome de usuário e senha. Credenciais incorretas retornam 400.

**Envio:**

```json
{
  "username": "julia",
  "password": "Senha somente de exemplo! 2026"
}
```

**Retorno de exemplo — HTTP 200:**

```json
{
  "id": 7,
  "username": "julia",
  "first_name": "Julia"
}
```

**Status previstos:** 200, 400 e 403.

## 5. Enviar cadastro de ONG

`POST /api/v1/ongs/`

**Quem pode usar:** Conta autenticada que ainda não seja responsável por outra ONG.

O cadastro começa pendente. Quem envia torna-se responsável; não escolhe outro usuário no corpo.

**Envio:**

```json
{
  "nome": "ONG Aprender",
  "descricao": "Organização fictícia que recebe materiais escolares.",
  "causa": "Educacao",
  "cnpj": null,
  "email_contato": "contato@example.org",
  "telefone": "",
  "site": "",
  "cep": "70000000",
  "logradouro": "Rua Ficticia",
  "numero": "10",
  "complemento": "",
  "bairro": "Bairro Demonstracao",
  "cidade": "Brasília",
  "uf": "DF",
  "instrucoes_recebimento": "Combine a entrega pelo contato da ONG. Dados ficticios."
}
```

**Retorno de exemplo — HTTP 201:**

```json
{
  "id": 4,
  "nome": "ONG Aprender",
  "descricao": "Organização fictícia que recebe materiais escolares.",
  "causa": "Educacao",
  "email_contato": "contato@example.org",
  "telefone": "",
  "site": "",
  "endereco": {
    "cep": "70000000",
    "logradouro": "Rua Ficticia",
    "numero": "10",
    "complemento": "",
    "bairro": "Bairro Demonstracao",
    "cidade": "Brasília",
    "uf": "DF"
  },
  "instrucoes_recebimento": "Combine a entrega pelo contato da ONG. Dados ficticios.",
  "cnpj": null,
  "status": "pendente",
  "motivo_analise": "",
  "criada_em": "2026-10-08T12:12:01.520481-03:00",
  "atualizada_em": "2026-10-08T12:12:01.520505-03:00"
}
```

**Status previstos:** 201, 400, 403 e 409.

## 6. Decidir sobre uma ONG

`POST /api/v1/admin/ongs/4/analise/`

**Quem pode usar:** Administrador autenticado, com is_staff.

Apenas cadastros pendentes podem ser avaliados. decisao também aceita recusar, com motivo obrigatório.

**Envio:**

```json
{
  "decisao": "aprovar"
}
```

**Retorno de exemplo — HTTP 200:**

```json
{
  "id": 4,
  "nome": "ONG Aprender",
  "descricao": "Organização fictícia que recebe materiais escolares.",
  "causa": "Educacao",
  "email_contato": "contato@example.org",
  "telefone": "",
  "site": "",
  "endereco": {
    "cep": "70000000",
    "logradouro": "Rua Ficticia",
    "numero": "10",
    "complemento": "",
    "bairro": "Bairro Demonstracao",
    "cidade": "Brasília",
    "uf": "DF"
  },
  "instrucoes_recebimento": "Combine a entrega pelo contato da ONG. Dados ficticios.",
  "cnpj": null,
  "status": "aprovada",
  "motivo_analise": "",
  "criada_em": "2026-10-08T12:12:01.520481-03:00",
  "atualizada_em": "2026-10-08T12:12:01.544171-03:00"
}
```

**Status previstos:** 200, 400, 403, 404 e 409.

## 7. Cadastrar campanha

`POST /api/v1/campanhas/`

**Quem pode usar:** Responsável por uma ONG aprovada.

A campanha nasce em rascunho. Para receber ajuda, é preciso publicar pela rota de estado.

**Envio:**

```json
{
  "titulo": "Materiais para estudar",
  "descricao": "Recebimento de cestas para demonstracao.",
  "tipo": "item",
  "unidade": "cesta",
  "meta": "100.00",
  "data_inicio": "2026-10-08",
  "data_fim": "2026-12-11"
}
```

**Retorno de exemplo — HTTP 201:**

```json
{
  "id": 6,
  "ong_id": 4,
  "titulo": "Materiais para estudar",
  "descricao": "Recebimento de cestas para demonstracao.",
  "tipo": "item",
  "unidade": "cesta",
  "meta": "100.00",
  "data_inicio": "2026-10-08",
  "data_fim": "2026-12-11",
  "status": "rascunho",
  "total_confirmado": "0.00",
  "percentual_meta": "0.00",
  "disponivel": false,
  "criada_em": "2026-10-08T12:12:01.557722-03:00",
  "atualizada_em": "2026-10-08T12:12:01.557738-03:00"
}
```

**Status previstos:** 201, 400 e 403.

## 8. Registrar ajuda

`POST /api/v1/contribuicoes/`

**Quem pode usar:** Conta autenticada, diferente do responsável da ONG da campanha.

Exige campanha ativa, dentro do período e ONG aprovada. Dinheiro usa valor; itens e horas usam quantidade. O registro começa declarada.

**Envio:**

```json
{
  "campanha_id": 6,
  "tipo": "item",
  "quantidade": "2.00",
  "observacao": "Combinei a entrega com a ONG."
}
```

**Retorno de exemplo — HTTP 201:**

```json
{
  "id": 9,
  "campanha_id": 6,
  "tipo": "item",
  "valor": null,
  "quantidade": "2.00",
  "observacao": "Combinei a entrega com a ONG.",
  "status": "declarada",
  "motivo_avaliacao": "",
  "avaliada_em": null,
  "criada_em": "2026-10-08T12:12:01.650230-03:00",
  "atualizada_em": "2026-10-08T12:12:01.650261-03:00"
}
```

**Status previstos:** 201, 400, 403, 404 e 409.

## 9. Conferir a ajuda

`POST /api/v1/contribuicoes/9/avaliacao/`

**Quem pode usar:** Responsável pela ONG aprovada que recebeu o registro.

Dinheiro pode ser confirmado ou recusado. Itens e horas passam pelo aceite. Recusa exige motivo. Uma confirmação repetida retorna 409.

**Envio:**

```json
{
  "acao": "confirmar"
}
```

**Retorno de exemplo — HTTP 200:**

```json
{
  "id": 9,
  "campanha_id": 6,
  "tipo": "item",
  "valor": null,
  "quantidade": "2.00",
  "observacao": "Combinei a entrega com a ONG.",
  "status": "confirmada",
  "motivo_avaliacao": "",
  "avaliada_em": "2026-10-08T12:12:01.683584-03:00",
  "criada_em": "2026-10-08T12:12:01.650230-03:00",
  "atualizada_em": "2026-10-08T12:12:01.691594-03:00"
}
```

**Status previstos:** 200, 400, 403, 404 e 409.

## 10. Consultar resultado

`GET /api/v1/relatorios/campanhas/?inicio=2026-10-08&fim=2026-10-08&campanha_id=6`

**Quem pode usar:** Responsável autenticado, para a própria ONG.

Filtra pela data de criação da contribuição. Os totais usam apenas registros atualmente confirmados. Não exige que a ONG esteja aprovada para consultar seu relatório.

**Envio:**

Sem corpo. Os filtros vão na URL.

**Retorno de exemplo — HTTP 200:**

```json
{
  "inicio": "2026-10-08",
  "fim": "2026-10-08",
  "gerado_em": "2026-10-08T12:12:01.720216-03:00",
  "criterio_periodo": "criacao_contribuicao",
  "campanhas": [
    {
      "campanha_id": 6,
      "titulo": "Materiais para estudar",
      "tipo": "item",
      "unidade": "cesta",
      "meta": "100.00",
      "total_confirmado": "2.00",
      "declaradas": 0,
      "aceitas": 0,
      "confirmadas": 1,
      "recusadas": 0,
      "canceladas": 0
    }
  ]
}
```

**Status previstos:** 200, 400, 403 e 404.

## Login e proteção das alterações

O cliente começa com `GET /api/v1/auth/csrf/`. Mantém os cookies e envia o token em `X-CSRFToken` para cadastrar, entrar e alterar registros. Depois do login, busca o token de novo, porque ele muda. A autenticação usa a sessão Django, sem JWT. Ausência de sessão em rota privada ou falha de CSRF retorna 403. Recursos privados de outra pessoa podem retornar 404.

## Erros

As operações descritas usam este formato:

```json
{"erro":{"codigo":"validacao","mensagem":"Revise os dados enviados.","campos":{"quantidade":["Informe uma quantidade positiva."]}}}
```

O código identifica o problema. A mensagem explica o que aconteceu. Campos aponta onde corrigir. A consulta de CEP ainda devolve seus erros sem a chave campos; essa diferença precisa ser mantida no cliente até a padronização.

200 indica conclusão; 201 indica criação. Dados inválidos retornam 400, acesso bloqueado retorna 403 e registro inexistente retorna 404. Uma ação incompatível com o estado atual retorna 409. Também podem ocorrer 405 para método não permitido, 413 para corpo acima de 64 KiB, 415 para conteúdo não aceito e 429 para excesso de pedidos.

## Listas e filtros

As listas usam count, next, previous e results. O padrão é 20 registros. page_size vai de 1 a 100. page precisa ser inteiro positivo; uma página inexistente retorna 404. Filtros desconhecidos e parâmetros repetidos são rejeitados. ONGs permitem ordering=nome ou -atualizada_em; campanhas permitem -criada_em, data_fim ou titulo.

O relatório não tem paginação. Os filtros inicio e fim consideram datas inclusivas. A rota `/api/v1/relatorios/campanhas/exportar/` entrega CSV com os mesmos filtros. Na interface, o relatório também tem impressão. Criar uma campanha não publica automaticamente: o responsável usa `POST /api/v1/campanhas/{id}/estado/` com `{"acao":"publicar"}`.

## Frequência de uso

| Pedido | Limite |

| --- | --- |

| Leitura pública sem login | 60 por minuto por IP |

| Conta autenticada | 120 por minuto por conta |

| Alteração autenticada | 30 por minuto, além do limite da conta |

| Login | 5 por minuto por IP e username |

| Cadastro | 5 por minuto por IP |

| CEP | 10 por minuto por conta |

Os contadores ficam na memória de cada processo. Com vários workers, esses limites não formam uma cota global. Quando houver Retry-After, o cliente deve aguardar o tempo informado.
