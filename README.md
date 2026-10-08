# DAI — rede de doação e voluntariado local

Aplicação web em Django que reúne ONGs e suas campanhas e registra contribuições em dinheiro, itens e horas de voluntariado. **A plataforma não processa pagamentos**: transferências, entregas e atividades acontecem fora do sistema, e só contribuições confirmadas pela ONG entram nos totais. Decisão tomada por uma questão da complexidade que representa a integração do sistema com gateways de pagamento.

**Instituição:** UniCEUB · **Curso:** Ciência da Computação · **Disciplina:** Desenvolvimento Web (turma B, matutino)
**Professor:** Felippe Pires Ferreira · **Integrante:** Matheus Benjamim de Souza Bosco ([@matheusbosco] **Matrícula:** 22612082. (https://github.com/matheusbosco)), trabalho individual
**Situação:** em desenvolvimento · **Aplicação publicada:** a publicar · **API (Swagger):** `/api/docs/` na aplicação publicada

## Documentação

- [Documento de Visão](docs/visao/documento-de-visao.md) — problema, objetivos, escopo, riscos e critérios de sucesso
- [Casos de uso](docs/casos-de-uso/) — [lista de atores e ações](docs/casos-de-uso/atores-e-acoes.md), diagrama (`DAI-Casos-de-Uso.drawio` e `.png`)
- [Telas do sistema](docs/prototipos/telas/) — capturas reais em 1280 px e 360 px (dados fictícios)
- [Esquema OpenAPI da API](docs/api/openapi.yaml) — gerado pelo sistema
- [Guia de deploy (Render + Neon)](docs/operacao/deploy.md)

## O que o sistema faz

- Cadastro de ONGs com aprovação por um administrador; perfil público só depois de aprovado.
- Campanhas (dinheiro, itens ou horas) com ciclo rascunho → ativa → pausada → encerrada, e postagens das ONGs.
- Busca pública de ONGs e campanhas por texto, cidade, bairro, UF, tipo e disponibilidade.
- Contribuições: declarada → (aceita) → confirmada, recusada ou cancelada; totais por campanha só com as confirmadas, sem somar dinheiro, itens e horas.
- Relatório por período com exportação em CSV e versão para impressão.
- API REST própria (`/api/v1/`) com documentação OpenAPI, Swagger e Redoc.
- Consulta de endereço pelo ViaCEP no cadastro da ONG, com preenchimento manual se o serviço falhar.

## Tecnologias

Python 3.12, Django 5.2, Django REST Framework, drf-spectacular, PostgreSQL, WhiteNoise, Gunicorn, `requests` (ViaCEP), HTML/CSS e JavaScript simples. Testes com o runner do Django; Bandit para análise estática; GitHub Actions para integração contínua.

## Como executar localmente

Pré-requisitos: Python 3.12, Git e um PostgreSQL (por exemplo em Docker).

```bash
git clone https://github.com/matheusbosco/rede-doacao-voluntariado.git
cd rede-doacao-voluntariado
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# banco local descartável
docker run -d --name dai-postgres -e POSTGRES_USER=dai -e POSTGRES_PASSWORD=<senha-local> -e POSTGRES_DB=dai -p 5433:5432 postgres:16-alpine

# defina as variáveis na sessão do terminal (veja a tabela abaixo) e então:
python manage.py migrate
python manage.py seed_demo      # dados 100% fictícios; mostra a senha se DEMO_PASSWORD não estiver definida
python manage.py runserver
```

### Variáveis de ambiente (sem valores)

| Variável | Para que serve |
|---|---|
| `SECRET_KEY` | segredo do Django (obrigatório fora do modo de desenvolvimento) |
| `DEBUG` | `true` só em desenvolvimento |
| `DATABASE_URL` | conexão PostgreSQL |
| `ALLOWED_HOSTS` | hosts permitidos, separados por vírgula |
| `CSRF_TRUSTED_ORIGINS` | origens HTTPS confiáveis, separadas por vírgula |
| `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS` | endurecimento de produção |
| `DEMO_PASSWORD` | senha das contas fictícias do `seed_demo` |

Nenhum segredo, senha ou arquivo `.env` é versionado.

## Testes e segurança

```bash
python manage.py test
python manage.py spectacular --validate --fail-on-warn --file schema.yml
python -m bandit -ll -r accounts config integrations organizations campaigns contributions reports api
```

O CI (`.github/workflows/ci.yml`) roda essas verificações a cada push. A rodada de SAST/DAST e o relatório de segurança são da Fase 2.

## Uso de inteligência artificial

As decisões de projeto (tema, escopo, regras de negócio e fluxos)  e a redação são minhas, também revisei todo o material antes da entrega. Ferramentas de IA generativa (ChatGPT/Codex e Claude) foram usadas na revisão dos documentos da Fase 1 em `docs/`, na geração de diagramas, imagens e PDFs e na conferência técnica contra o código.

O código, os testes, o CI e a configuração de deploy foram escritos com assistência de IA (Claude Code coordenando o Codex), sob direção do autor. As capturas de tela, o esquema OpenAPI e este README técnico foram gerados por ferramenta a partir do sistema.

## Licença e origem

Sem licença definida; uso acadêmico. A estrutura inicial do repositório vem do template da disciplina: <https://github.com/Felippe-Pires/template_projects>.
