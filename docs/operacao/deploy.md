# Deploy do DAI: Render + Neon

O dono cria e mantém as duas contas pessoais, usando somente os planos gratuitos.
As credenciais ficam no painel do Render ou nas variáveis da sessão do terminal.
Nunca publique connection strings, senhas ou `SECRET_KEY` em Git, prints, issues ou logs.

## 1. Banco no Neon

1. Crie sua conta em <https://neon.com> e um projeto PostgreSQL no plano Free.
2. Escolha uma região próxima à aplicação; o Blueprint usa a região padrão do Render.
3. No painel do projeto, abra **Connect**, selecione a branch, o banco e o usuário.
   Copie a connection string PostgreSQL; para esta aplicação simples, use a conexão direta
   (desative **Connection pooling**). Guarde-a em local privado.
4. Confira o parâmetro `?sslmode=require` (ou `&sslmode=require` se já houver parâmetros).
   Preserve os demais parâmetros da string fornecida pelo Neon. O `dj_database_url`
   repassa `sslmode` ao driver PostgreSQL, sem precisar forçar TLS no código.

Referência: [conexões no Neon](https://neon.com/docs/connect/connect-from-any-app).

## 2. Serviço no Render

1. Crie a conta pessoal em <https://render.com> usando **GitHub**.
2. O dono deve disponibilizar no GitHub as alterações revisadas desta etapa;
   a preparação local não faz commit nem push.
3. No painel do Render, escolha **New > Blueprint**, autorize acesso ao repositório
   e selecione a branch que contém `render.yaml` na raiz.
4. Revise o único serviço web `dai`, runtime Python, plano **Free**. Não crie banco no Render.
5. Na configuração do Blueprint, informe `DATABASE_URL` com a string privada do Neon.
   Ela é solicitada por `sync: false`; depois pode ser alterada em **dai > Environment**.
6. Aplique o Blueprint. `SECRET_KEY` é gerada pelo Render; `DEBUG=false` e HSTS começa em zero.
   O hostname do Render entra automaticamente nos hosts e nas origens CSRF permitidos.

`PYTHON_VERSION=3.12.10` coincide com o ambiente local. Não é necessário duplicá-la
em `.python-version`: [precedência das versões](https://render.com/docs/python-version).
A região foi omitida para usar o padrão. `autoDeploy: true` segue o pedido, embora seja
um campo obsoleto, ainda equivalente a `autoDeployTrigger: commit` na
[referência do Blueprint](https://render.com/docs/blueprint-spec).

## 3. Primeiro deploy

Em **Events/Logs**, confira instalação das dependências, coleta dos estáticos,
migrações concluídas e inicialização dos workers do Gunicorn. O comando de início
interrompe se a migração falhar. Aguarde o estado **Live**.

Abra a URL HTTPS mostrada pelo Render e verifique:

- `/health/`: HTTP 200, somente `{"status": "ok"}`. Não testa a conexão com o banco.
- `/`: página inicial, estilos e links funcionando (esta página usa o banco).
- `/api/docs/`: documentação abre; Swagger usa assets de CDN.

O proxy informa HTTPS por `X-Forwarded-Proto`; somente `/health/` aceita HTTP interno
sem redirecionar. Em produção, os logs (WARNING ou acima, na saída padrão) trazem nível,
origem, mensagem e traceback, o suficiente para diagnosticar um erro 500 sem ligar
`DEBUG`. O Django não registra corpo de requisição nem campos de formulário; strings de
conexão com senha e pares como `password=`, `SECRET_KEY=` ou `DATABASE_URL=` são
substituídos por `[redigido]`. Mesmo assim, confira os logs antes de copiá-los para
qualquer lugar público.

## 4. Contas pelo terminal local, sem Shell do Render

O [serviço gratuito não tem Shell](https://render.com/docs/free). Abra um **terminal novo**
no computador do dono, na raiz do projeto, com a `.venv` existente e a mesma revisão
implantada. Os comandos abaixo modificam o banco do Neon. Digite os valores sensíveis
nos prompts ocultos, nunca na linha de comando. A chave temporária atende aos comandos
administrativos; não substitui a `SECRET_KEY` do Render.

### PowerShell

```powershell
$env:DATABASE_URL = [System.Net.NetworkCredential]::new('', (Read-Host 'Connection string do Neon' -AsSecureString)).Password
$env:DEBUG = 'false'
$env:SECRET_KEY = & .venv/Scripts/python -c "import secrets; print(secrets.token_urlsafe(64))"
$env:DEMO_PASSWORD = [System.Net.NetworkCredential]::new('', (Read-Host 'Senha forte para as contas demo' -AsSecureString)).Password
.venv/Scripts/python manage.py migrate --noinput
.venv/Scripts/python manage.py createsuperuser
.venv/Scripts/python manage.py seed_demo --permitir-producao
```

### Git Bash (Windows)

```bash
read -r -s -p 'Connection string do Neon: ' DATABASE_URL
printf '\n'
export DATABASE_URL
export DEBUG=false
export SECRET_KEY="$(.venv/Scripts/python -c 'import secrets; print(secrets.token_urlsafe(64))')"
read -r -s -p 'Senha forte para as contas demo: ' DEMO_PASSWORD
printf '\n'
export DEMO_PASSWORD
.venv/Scripts/python manage.py migrate --noinput
.venv/Scripts/python manage.py createsuperuser
.venv/Scripts/python manage.py seed_demo --permitir-producao
```

Confirme que `DEMO_PASSWORD` não ficou vazia: sem ela, o comando gera e imprime uma senha.
O seed usa dados fictícios; as contas são `admin_demo`, `ong_df_demo`, `ong_sp_demo`,
`ong_pendente_demo`, `doador_1_demo` e `doador_2_demo`, todas com a senha informada.
Executá-lo novamente redefine essas senhas. Não versione nem compartilhe publicamente a senha.
Para a equipe, crie contas individuais pelo cadastro da aplicação; `createsuperuser`
é para o dono ou quem realmente precisa de administração completa. `admin_demo` é staff,
sem ser superusuário. Ao terminar, **feche o terminal** para descartar as variáveis da sessão.

## 5. HSTS depois de validar HTTPS

Depois de confirmar certificado válido, login e ausência de loops, altere
`SECURE_HSTS_SECONDS` para `3600` no `render.yaml` e sincronize o Blueprint.
Após observar estabilidade, aumente progressivamente, por exemplo para `86400`.
Confira o cabeçalho `Strict-Transport-Security` depois de cada alteração.

HSTS faz o navegador exigir HTTPS até expirar o prazo já recebido. Voltar o valor
a zero no servidor não remove imediatamente essa exigência dos navegadores.
Não ative `includeSubDomains` nem preload nesta etapa.

## 6. Limitações dos planos gratuitos

Antes de depender do serviço, conferir suspensão por inatividade, primeira requisição
lenta, cotas de uso e condições de permanência em
[Render Free](https://render.com/docs/free). Conferir limites de armazenamento, conexões,
computação, suspensão do banco e validade/retenção do plano em
[Neon Plans](https://neon.com/docs/introduction/plans). Não presuma que os limites
permanecem iguais; consulte essas páginas novamente antes de apresentações.

## 7. Verificação e reversão

- [ ] HTTPS com certificado válido; sem loops nas páginas e API.
- [ ] `DEBUG=false` confirmado em **Environment**.
- [ ] `/health/`, página inicial, estáticos e `/api/docs/` respondem.
- [ ] Uma consulta real pela API autenticada funciona; o health não verifica o banco.
- [ ] Login funciona com CSRF; uma tentativa de POST sem token é recusada.
- [ ] `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` e HSTS após ativação.
- [ ] Cookies de sessão e CSRF com `Secure` e `SameSite=Lax`; sessão com `HttpOnly`.
- [ ] Nenhum segredo ou dado de formulário nos logs.

Para reverter, em **dai > Deploys**, encontre o deploy saudável anterior e selecione
**Rollback**, confirmando na tela seguinte. É necessário que o artefato ainda esteja disponível.
O rollback não desfaz migrações/dados do Neon. Ele reutiliza as variáveis daquele deploy
sem sobrescrever a configuração atual; confira também o ambiente e a compatibilidade do banco.
Pelo painel, o rollback desativa os deploys automáticos; reative-os em **Settings** depois
de corrigir o problema. Repita o checklist.
Confira o procedimento na [documentação de rollback](https://render.com/docs/rollbacks).
