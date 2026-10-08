# Casos de uso

## 1. Registrar contribuição

**Quem participa:** doador ou voluntário. O responsável por uma ONG também pode ajudar outra organização.

**Objetivo:** declarar uma doação feita fora da plataforma ou oferecer itens e horas para uma campanha.

**Antes de começar:** a pessoa precisa estar logada. A ONG deve estar aprovada. A campanha precisa estar ativa e dentro das datas, incluindo o primeiro e o último dia. O responsável não pode contribuir para a própria ONG. Se for dinheiro, a transferência deve ter sido feita fora do DAI; o sistema não consegue verificar isso sozinho.

**Ao terminar:** o registro fica em `declarada`, aguardando a ONG. Ele ainda não aumenta o total da campanha. Se os dados forem recusados, nenhuma contribuição é criada.

### Caminho principal

1. O usuário entra na página da campanha.
2. O usuário escolhe a opção de contribuir.
3. O sistema apresenta os campos daquele tipo de campanha.
4. O usuário preenche a medida e pode deixar uma observação.
5. O usuário envia os dados.
6. O sistema verifica a conta, a ONG e a disponibilidade da campanha.
7. O sistema confere o valor ou a quantidade informada.
8. O sistema salva o registro como `declarada` e avisa que a ONG vai analisar.

### Outros caminhos

- Em dinheiro, o usuário preenche `valor`. A transferência acontece por fora.
- Em itens, o usuário informa uma quantidade inteira, na unidade da campanha.
- Em voluntariado, o usuário informa as horas. São permitidas até duas casas decimais.
- Enquanto o registro estiver `declarada`, o autor pode corrigir a medida ou a observação.
- Se desistir, o autor pode cancelar um registro `declarada` ou `aceita`.

### Quando não dá para continuar

- Sem login, a pessoa precisa entrar na conta.
- Zero, número negativo ou medida incompatível não são aceitos.
- Uma campanha que encerre antes da gravação não recebe o novo registro.
- A tentativa de ajudar a própria ONG é bloqueada.
- Se a gravação falhar, o sistema desfaz a operação e não informa sucesso.

No diagrama, este caso corresponde a CU08, CU09 e CU10. Consulta e alteração ficam em CU11 e CU12.

## 2. Conferir contribuição

**Quem participa:** responsável pela ONG da campanha.

**Objetivo:** dizer se a contribuição foi recebida ou realizada. Para itens e horas, também decidir se a oferta será aceita.

**Antes de começar:** o responsável deve estar logado e sua ONG aprovada. O registro precisa pertencer à organização. A ação escolhida deve ser possível no estado atual. A confirmação depende de conferir o recebimento ou a atividade fora do DAI.

**Ao terminar:** o sistema guarda a decisão, o responsável e o horário. Quando o estado vira `confirmada`, a medida entra nos totais. Apenas aceitar uma oferta não altera o total confirmado. Uma tentativa inválida mantém o registro como estava.

### Caminho principal: dinheiro

1. O responsável abre a lista de contribuições recebidas.
2. O sistema mostra os registros da sua ONG.
3. O responsável abre uma contribuição declarada.
4. O responsável verifica por fora se o dinheiro chegou.
5. O responsável pede a confirmação.
6. O sistema verifica a permissão e o estado do registro.
7. O sistema salva `confirmada` e os dados da avaliação.
8. O sistema inclui esse valor na soma das contribuições confirmadas.

### Outros caminhos

- Para itens ou horas, o responsável primeiro aceita a oferta. O registro passa a `aceita`. Depois da entrega ou da atividade, ele retorna para confirmar.
- Se não puder receber ou se a contribuição não acontecer, o responsável escolhe recusar e escreve o motivo. A recusa é possível em `declarada` ou `aceita`.
- Uma campanha pausada ou encerrada ainda permite conferir contribuições anteriores. Ela só deixa de receber novos registros.

### Quando não dá para continuar

- Outra pessoa ou outra ONG não pode fazer a avaliação.
- ONG pendente ou recusada não tem essa permissão.
- Dinheiro não pode passar por `aceita`.
- Itens e horas precisam do aceite antes da confirmação.
- A recusa precisa de motivo, com no máximo 500 caracteres.
- Uma segunda confirmação ou outra mudança incompatível gera conflito.
- Se houver falha ao salvar, a decisão não é aplicada.

O total vem de uma soma dos registros confirmados. A avaliação usa transação e bloqueio do registro. Por isso, clicar novamente em confirmar não conta a contribuição duas vezes.

No diagrama, a conferência está em CU18 e CU19.

## 3. Aprovar ONG

**Quem participa:** administrador com `is_staff` habilitado.

**Objetivo:** avaliar o cadastro antes de permitir a divulgação da ONG.

**Antes de começar:** o administrador precisa estar logado. O cadastro deve existir e estar `pendente`. Os dados enviados precisam estar disponíveis para análise.

**Ao terminar:** a aprovação deixa a ONG em `aprovada`, com a identificação do administrador e a data. O perfil pode aparecer nas buscas e a ONG pode publicar campanhas. Se houver recusa, o cadastro fica em `recusada`, com o motivo. Essa análise não é uma certificação da instituição.

### Caminho principal

1. O administrador acessa a fila de cadastros.
2. O sistema apresenta as ONGs pendentes.
3. O administrador abre uma ONG e verifica seus dados.
4. O administrador escolhe aprovar.
5. O sistema verifica o acesso e confirma que o estado ainda é `pendente`.
6. O sistema grava a aprovação, quem decidiu e quando.
7. O sistema permite que a ONG apareça na consulta pública.

### Outros caminhos

- Se o cadastro não for aceito, o administrador escolhe recusar e informa o motivo.
- O responsável pode corrigir uma ONG recusada e reenviar. Ela volta para a fila como `pendente`, sem manter os dados da decisão anterior como análise vigente.
- Mudar nome, CNPJ ou endereço de uma ONG aprovada exige nova análise. O sistema volta o cadastro para `pendente`.

### Quando não dá para continuar

- Uma conta sem permissão administrativa não consegue decidir.
- Cadastro inexistente não pode ser analisado.
- Se o cadastro já saiu de `pendente`, outra decisão gera conflito.
- Recusa sem motivo ou com mais de 500 caracteres não é salva.
- Uma decisão diferente de aprovar ou recusar é inválida.
- Falha na gravação mantém a situação anterior.

No diagrama, CU21 e CU22 tratam da consulta para análise. CU23 representa aprovação e CU24 representa recusa.
