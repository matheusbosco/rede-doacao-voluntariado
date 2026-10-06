# [Nome do Projeto]

> Substitua os trechos entre colchetes `[ ]` pelas informações reais do trabalho. Remova esta nota e as demais orientações em *itálico* antes da entrega.

[![Status](https://img.shields.io/badge/status-[em_desenvolvimento]-yellow)]()
[![Versão](https://img.shields.io/badge/versão-[0.1.0]-blue)]()
[![Licença](https://img.shields.io/badge/licença-[acadêmica]-lightgrey)]()

**Instituição:** [Nome da instituição]  
**Curso:** [Nome do curso]  
**Disciplina:** [Nome da disciplina]  
**Turma / Semestre:** [Ex.: 2026.2]  
**Professor(a):** [Nome completo]  
**Status do projeto:** [Protótipo / MVP / Em desenvolvimento / Concluído]

---

## Sumário

- [1. Descrição do projeto](#1-descrição-do-projeto)
- [2. Funcionalidades](#2-funcionalidades)
- [3. Demonstração](#3-demonstração)
- [4. Tecnologias utilizadas](#4-tecnologias-utilizadas)
- [5. Arquitetura](#5-arquitetura)
- [6. Organização dos diretórios](#6-organização-dos-diretórios)
- [7. Participantes](#7-participantes)
- [8. Como executar](#8-como-executar)
- [9. Configuração](#9-configuração)
- [10. Testes](#10-testes)
- [11. Uso de inteligência artificial](#11-uso-de-inteligência-artificial)
- [12. Contribuição e fluxo de trabalho](#12-contribuição-e-fluxo-de-trabalho)
- [13. Histórico de versões](#13-histórico-de-versões)
- [14. Limitações e próximos passos](#14-limitações-e-próximos-passos)
- [15. Licença, referências e contato](#15-licença-referências-e-contato)

---

## 1. Descrição do projeto

*Apresente o contexto, o problema e a solução proposta. Use linguagem objetiva (dois a quatro parágrafos).*

[Descreva o que o sistema faz, para quem ele se destina e qual problema ele resolve.]

### Objetivos

*Liste os objetivos gerais e específicos do projeto.*

- **Objetivo geral:** [Ex.: desenvolver uma aplicação web para gerenciar reservas de laboratórios.]
- **Objetivos específicos:**
  - [Ex.: permitir cadastro e autenticação de usuários.]
  - [Ex.: registrar e consultar reservas por data e laboratório.]
  - [Ex.: gerar relatórios de ocupação.]

### Público-alvo

- [Ex.: estudantes da instituição]
- [Ex.: professores responsáveis pelos laboratórios]
- [Ex.: equipe administrativa]

---

## 2. Funcionalidades

*Liste as funções implementadas (ou previstas) no sistema. Marque o status de cada uma.*

| Funcionalidade | Descrição | Status |
| --- | --- | --- |
| [Ex.: Autenticação] | [Ex.: login, logout e recuperação de senha] | [Implementada / Em andamento / Planejada] |
| [Ex.: Cadastro de usuários] | [Ex.: criação e edição de perfis] | [Implementada / Em andamento / Planejada] |
| [Ex.: Relatórios] | [Ex.: exportação em PDF] | [Implementada / Em andamento / Planejada] |

### Requisitos não funcionais

*Informe restrições de qualidade, quando existirem.*

- **Desempenho:** [Ex.: respostas da API em menos de 2 segundos]
- **Segurança:** [Ex.: senhas armazenadas com hash; HTTPS em produção]
- **Usabilidade:** [Ex.: interface responsiva para desktop e celular]
- **Disponibilidade:** [Ex.: uso em ambiente local / laboratório da disciplina]

---

## 3. Demonstração

*Inclua capturas de tela, GIF ou link para vídeo. Coloque as imagens em `images/`.*

![Tela principal](images/[screenshot-principal].png)

| Tela | Descrição |
| --- | --- |
| [Login] | [Acesso ao sistema com e-mail e senha] |
| [Painel] | [Visão geral das reservas do dia] |

**Vídeo / protótipo:** [URL do YouTube, Loom ou Figma]

---

## 4. Tecnologias utilizadas

*Informe as tecnologias de fato usadas no projeto. Remova as linhas que não se aplicarem.*

| Camada | Tecnologia | Versão |
| --- | --- | --- |
| Linguagem | [Ex.: Python, Java, TypeScript] | [Ex.: 3.12] |
| Frontend | [Ex.: HTML, CSS, React] | [Ex.: 18] |
| Backend | [Ex.: Flask, Spring Boot, Node.js] | [Ex.: 3.x] |
| Banco de dados | [Ex.: PostgreSQL, SQLite, MongoDB] | [Ex.: 16] |
| Testes | [Ex.: pytest, JUnit, Jest] | [Ex.: 8] |
| Infraestrutura | [Ex.: Docker, GitHub Actions] | — |
| Outras ferramentas | [Ex.: Git, Figma, Postman] | — |

---

## 5. Arquitetura

*Explique como o sistema está organizado: camadas, principais componentes e o fluxo entre eles. Inclua um diagrama no PDF de arquitetura ou de classes em `docs/` e descreva-o em texto.*

[Ex.: a solução segue uma arquitetura em camadas (apresentação, aplicação, domínio e persistência). O frontend consome uma API REST. O backend aplica as regras de negócio e persiste os dados no banco.]

```text
[Usuário] → [Interface / Frontend] → [API / Backend] → [Banco de dados]
```

**Decisões relevantes:**

- [Ex.: uso de API REST para separar cliente e servidor.]
- [Ex.: persistência relacional porque os dados possuem relacionamentos bem definidos.]

### Endpoints principais (quando houver API)

| Método | Rota | Descrição |
| --- | --- | --- |
| `POST` | `/api/[recurso]` | [Ex.: criar um registro] |
| `GET` | `/api/[recurso]` | [Ex.: listar registros] |
| `GET` | `/api/[recurso]/{id}` | [Ex.: obter um registro] |
| `PUT` | `/api/[recurso]/{id}` | [Ex.: atualizar um registro] |
| `DELETE` | `/api/[recurso]/{id}` | [Ex.: remover um registro] |

Documentação completa da API: [link para Swagger, Postman ou `docs/api.md`]

---

## 6. Organização dos diretórios

*Mantenha a árvore alinhada à estrutura real do repositório. Ajuste pastas conforme o tipo de projeto.*

```text
.
├── README.md                 # Documentação principal do projeto
├── .env.example              # Modelo de variáveis de ambiente (sem segredos)
├── docs/                     # Modelagem e demais artefatos técnicos (PDF)
│   ├── README.pdf            # Índice da pasta docs/
│   └── modelagem/
│       ├── casos-de-uso/
│       │   └── especificacoes-casos-de-uso.pdf
│       ├── classes/
│       │   └── diagrama-de-classes.pdf
│       └── banco-de-dados/
│           ├── diagrama-er.pdf
│           └── modelo-logico.pdf
├── images/                   # Figuras da documentação geral (ex.: política de IA)
├── src/                      # Código-fonte da aplicação
│   ├── frontend/             # Interface com o usuário (quando houver)
│   └── backend/              # Regras de negócio, API e acesso a dados (quando houver)
├── tests/                    # Testes automatizados
└── scripts/                  # Scripts auxiliares de setup, build ou deploy
```

| Diretório / arquivo | Função |
| --- | --- |
| `README.md` | Apresentação do projeto, objetivos, tecnologias e instruções de uso |
| `.env.example` | Lista das variáveis necessárias, sem credenciais reais |
| `docs/` | Artefatos de análise e modelagem em PDF |
| `docs/modelagem/` | Casos de uso, classes e modelo de dados (diagramas embutidos nos PDFs) |
| `images/` | Figuras da documentação geral do repositório (não usar para diagramas de modelagem) |
| `src/` | Código-fonte organizado por camada ou módulo |
| `tests/` | Casos de teste e evidências de verificação |
| `scripts/` | Automação de ambiente e execução |

---

## 7. Participantes

*Informe nome completo, função no grupo e, se houver, o identificador acadêmico (matrícula).*

| Nome | Matrícula | Função no projeto |
| --- | --- | --- |
| [Nome completo] | [000000] | [Ex.: coordenação / backend / frontend / testes / documentação] |
| [Nome completo] | [000000] | [Ex.: backend] |
| [Nome completo] | [000000] | [Ex.: frontend] |
| [Nome completo] | [000000] | [Ex.: testes e documentação] |

**Professor(a) responsável:** [Nome completo]

---

## 8. Como executar

*Preencha com os comandos reais do projeto para que outra pessoa consiga reproduzir o ambiente.*

### Pré-requisitos

- [Ex.: Git]
- [Ex.: Python 3.12+]
- [Ex.: Node.js 20+]
- [Ex.: Docker]

### Instalação e execução

```bash
# 1. Clonar o repositório
git clone [URL_DO_REPOSITORIO]
cd [NOME_DA_PASTA]

# 2. Instalar dependências
[comando de instalação]

# 3. Configurar variáveis de ambiente
cp .env.example .env
# edite o arquivo .env com as credenciais locais

# 4. Executar a aplicação
[comando de execução]
```

**Acesso local:** [Ex.: http://localhost:3000]

### Implantação (quando houver)

- **Ambiente:** [Ex.: Render, Railway, Vercel, servidor da instituição]
- **URL de produção:** [https://...]
- **Observações:** [Ex.: é necessário configurar as variáveis de ambiente no painel do provedor]

---

## 9. Configuração

*Liste as variáveis de ambiente usadas pelo sistema. Nunca publique senhas, tokens ou chaves neste arquivo.*

| Variável | Obrigatória | Descrição | Exemplo |
| --- | --- | --- | --- |
| `PORT` | Sim | Porta da aplicação | `3000` |
| `DATABASE_URL` | Sim | Conexão com o banco | `postgresql://user:senha@localhost:5432/app` |
| `SECRET_KEY` | Sim | Chave de sessão / JWT | `[gerar localmente]` |

Credenciais reais devem ficar apenas no arquivo `.env` (não versionado).

---

## 10. Testes

*Descreva como executar os testes e o que eles cobrem.*

```bash
[comando para executar os testes]
```

| Tipo | Ferramenta | O que verifica |
| --- | --- | --- |
| Unitários | [Ex.: pytest / JUnit / Jest] | [Ex.: regras de negócio isoladas] |
| Integração | [Ex.: ...] | [Ex.: API e banco de dados] |
| Manuais | [Ex.: checklist em `docs/`] | [Ex.: fluxos principais da interface] |

**Cobertura atual:** [Ex.: 70% / não medida]

---

## 11. Uso de inteligência artificial

Este repositório segue a política de uso de IA da disciplina (semáforo pedagógico):

![Política de uso de IA — semáforo](images/semaforo.png)

| Situação | Significado |
| --- | --- |
| **Vermelho — uso proibido** | Atividades de autonomia intelectual (ex.: provas presenciais sem consulta). |
| **Amarelo — uso limitado** | IA pode ser ferramenta auxiliar, desde que haja declaração de uso. |
| **Verde — uso permitido** | Uso livre ao longo da atividade acadêmica. |

### Declaração de uso

*Preencha de forma honesta. Se não houve uso de IA, declare explicitamente.*

- **Houve uso de IA neste projeto?** [Sim / Não]
- **Ferramentas utilizadas:** [Ex.: ChatGPT, GitHub Copilot, Gemini — ou “nenhuma”]
- **Finalidade:** [Ex.: revisão de texto, geração de esboço de testes, esclarecimento de dúvidas de sintaxe]
- **O que NÃO foi delegado à IA:** [Ex.: definição do problema, modelagem, implementação das regras de negócio, testes finais]

---

## 12. Contribuição e fluxo de trabalho

*Padronize o trabalho em equipe. Ajuste as regras ao combinado da disciplina.*

### Branches

- `main` — versão estável para avaliação
- `develop` — integração do grupo *(opcional)*
- `feat/[nome]` — nova funcionalidade
- `fix/[nome]` — correção de defeito
- `docs/[nome]` — alterações só de documentação

### Commits

Use mensagens curtas e no imperativo, por exemplo:

- `feat: adiciona cadastro de reservas`
- `fix: corrige validação de data`
- `docs: atualiza instruções de execução`

### Passos sugeridos

1. Criar uma branch a partir de `main`.
2. Implementar e testar localmente.
3. Abrir um *pull request* / *merge request* para revisão do grupo.
4. Só então integrar à branch principal.

**Issues e quadro de tarefas:** [link do GitHub Projects, Trello ou similar]

---

## 13. Histórico de versões

*Registre entregas relevantes (sprints, checkpoints ou versões avaliadas).*

| Versão | Data | Descrição |
| --- | --- | --- |
| `0.1.0` | [AAAA-MM-DD] | [Ex.: primeira versão executável / MVP] |
| `0.0.1` | [AAAA-MM-DD] | [Ex.: estrutura inicial do repositório] |

---

## 14. Limitações e próximos passos

### Problemas conhecidos

- [Ex.: a recuperação de senha ainda não envia e-mail]
- [Ex.: o layout quebra em telas menores que 360 px]

### Roadmap

- [ ] [Ex.: autenticação com dois fatores]
- [ ] [Ex.: exportação de relatórios em CSV]
- [ ] [Ex.: implantação em ambiente de homologação]

---

## 15. Licença, referências e contato

**Licença:** [Ex.: uso exclusivamente acadêmico / MIT / outro]

Este material destina-se a fins educacionais. Verifique com a disciplina se o código pode ser reutilizado fora do curso.

### Documentação complementar

- Índice da pasta `docs/`: [`docs/README.pdf`](docs/README.pdf)
- Casos de uso (diagrama + especificações): [`docs/modelagem/casos-de-uso/especificacoes-casos-de-uso.pdf`](docs/modelagem/casos-de-uso/especificacoes-casos-de-uso.pdf)
- Diagrama de classes: [`docs/modelagem/classes/diagrama-de-classes.pdf`](docs/modelagem/classes/diagrama-de-classes.pdf)
- Modelo conceitual (ER): [`docs/modelagem/banco-de-dados/diagrama-er.pdf`](docs/modelagem/banco-de-dados/diagrama-er.pdf)
- Modelo lógico: [`docs/modelagem/banco-de-dados/modelo-logico.pdf`](docs/modelagem/banco-de-dados/modelo-logico.pdf)
- Apresentação: [`docs/apresentacao.pdf`](docs/)

### Referências

- [Autor. Título. Ano. URL ou dados bibliográficos.]
- [Documentação oficial da tecnologia X.]

### Contato

Dúvidas sobre o projeto: [e-mail institucional do grupo ou issue no repositório]

**Agradecimentos:** [Ex.: professor(a), monitoria, materiais da disciplina]
