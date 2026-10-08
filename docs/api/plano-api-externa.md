# Consulta de endereço pelo ViaCEP

## 1. Para que entra no DAI

A consulta ajuda o responsável a preencher o endereço da ONG. Depois de salvo, cidade, bairro e UF servem para encontrar organizações próximas. A pessoa confere o resultado antes de concluir o cadastro. Se a consulta não funcionar, pode continuar preenchendo tudo manualmente.

## 2. Como a consulta acontece

A documentação oficial está em https://viacep.com.br/. O endereço externo usado é `GET https://viacep.com.br/ws/{cep}/json/`. O CEP vai com oito dígitos. A entrada pode ter hífen; o DAI retira a pontuação antes de consultar. O navegador usa `GET /api/v1/enderecos/cep/{cep}/`, e quem fala com o ViaCEP é o servidor. Primeiro ele procura uma resposta válida no cache.

## 3. Quais dados entram no cadastro

| Resposta externa | Campo no DAI |
| --- | --- |
| cep | cep |
| logradouro | logradouro |
| bairro | bairro |
| localidade | cidade |
| uf | uf |

Esses campos são guardados no cache por 24 horas. O endereço confirmado pelo responsável é salvo na ONG. Número e complemento são manuais. Os demais dados do ViaCEP não são necessários para esse fluxo. O cache é independente do cadastro, sem chave estrangeira entre eles.

## 4. Acesso e limites

O ViaCEP não exige chave ou token. Sua documentação alerta para bloqueio por uso massivo, sem garantir uma cota numérica. No DAI, a consulta exige login e permite 10 pedidos por minuto por conta. Esse limite fica na memória de cada processo; não é compartilhado entre todos os workers. Já o cache de endereços fica no PostgreSQL e evita repetir chamadas externas. Não há consulta em massa nem repetição automática em sequência.

## 5. O que acontece quando falha

| Problema | Resposta e continuidade |
| --- | --- |
| CEP mal formatado | 400. Corrigir os oito dígitos; nenhuma consulta externa é feita. |
| CEP que não existe | 404. Corrigir o número ou preencher o endereço. |
| Timeout ou falha de rede | 503. Mostrar a indisponibilidade e manter o preenchimento manual. |
| HTTP externo inesperado ou JSON inválido | 503. Descartar o resultado; não salvar no cache. |
| Campos inválidos ou CEP diferente do solicitado | 503. Não usar a resposta como endereço válido. |
| Limite de uso ultrapassado | 429. Respeitar Retry-After ou seguir pelo preenchimento manual. |

O timeout de conexão é 2 segundos; o de leitura, 3 segundos. Isso não é uma garantia de duração total de cinco segundos. O cliente não segue redirecionamentos. Uma entrada vencida no cache exige nova consulta. Bairro e logradouro vazios precisam ser completados no formulário. Na avaliação, vou mostrar consulta válida, resultado do cache e continuidade do cadastro sem o serviço externo.
