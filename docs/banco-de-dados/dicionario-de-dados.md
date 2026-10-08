# Dados do DAI

O modelo cobre as contas, as ONGs, as campanhas, as contribuições, as postagens e o cache de CEP. Abaixo estão os nomes usados no banco PostgreSQL. PK identifica a chave principal. FK indica um vínculo com outra tabela.

Na coluna de preenchimento, “automático” significa que o sistema cuida do campo. “Condicional” depende do tipo ou do estado do registro. Texto opcional pode ficar vazio sem ser NULL.

## Usuário
Tabela: `accounts_user`.
| Campo | Tipo | Preenchimento | NULL? | Para que serve |
| --- | --- | --- | --- | --- |
| `id` PK | `bigint` | Automático | Não | Número que identifica o registro. |
| `password` | `varchar(128)` | Automático | Não | Senha protegida por hash. |
| `last_login` | `timestamp with time zone` | Opcional | Sim | Última entrada na conta. |
| `is_superuser` | `boolean` | Automático | Não | Permissão administrativa completa. |
| `username` | `varchar(150)` | Obrigatório | Não | Nome usado no login. Não se repete. |
| `last_name` | `varchar(150)` | Opcional | Não | Sobrenome da pessoa. |
| `is_staff` | `boolean` | Automático | Não | Permissão para analisar cadastros de ONG. |
| `is_active` | `boolean` | Automático | Não | Libera ou bloqueia a autenticação. |
| `date_joined` | `timestamp with time zone` | Automático | Não | Momento em que a conta foi aberta. |
| `email` | `varchar(254)` | Obrigatório | Não | E-mail da conta. Não se repete. |
| `first_name` | `varchar(150)` | Obrigatório | Não | Nome da pessoa. |

`username` e `email` são únicos. O e-mail é convertido para minúsculas pela aplicação. O responsável é identificado pelo vínculo com a ONG; o administrador, por `is_staff`.
## ONG
Tabela: `organizations_ong`.
| Campo | Tipo | Preenchimento | NULL? | Para que serve |
| --- | --- | --- | --- | --- |
| `id` PK | `bigint` | Automático | Não | Número que identifica o registro. |
| `responsavel_id` FK | `bigint` | Obrigatório | Não | Conta que administra a organização. Não se repete. |
| `nome` | `varchar(150)` | Obrigatório | Não | Nome apresentado ao público. |
| `descricao` | `text` | Obrigatório | Não | Apresentação da ONG. |
| `causa` | `varchar(80)` | Obrigatório | Não | Área em que a ONG atua. |
| `cnpj` | `varchar(14)` | Opcional | Sim | Identificação opcional da organização, com 14 dígitos. Não se repete. |
| `email_contato` | `varchar(254)` | Obrigatório | Não | Endereço de e-mail para contato público. |
| `telefone` | `varchar(20)` | Opcional | Não | Número de contato, quando informado. |
| `site` | `varchar(200)` | Opcional | Não | Endereço HTTP ou HTTPS da organização. |
| `cep` | `varchar(8)` | Obrigatório | Não | CEP sem hífen, com oito dígitos. |
| `logradouro` | `varchar(200)` | Obrigatório | Não | Rua ou outro logradouro do endereço. |
| `numero` | `varchar(20)` | Obrigatório | Não | Número informado pela ONG. |
| `complemento` | `varchar(120)` | Opcional | Não | Informação extra para localizar o endereço. |
| `bairro` | `varchar(100)` | Obrigatório | Não | Bairro da organização. |
| `cidade` | `varchar(100)` | Obrigatório | Não | Município do endereço. |
| `uf` | `varchar(2)` | Obrigatório | Não | Sigla do estado. Opções: AC, AL, AP, AM, BA, CE, DF, ES, GO, MA, MT, MS, MG, PA, PB, PR, PE, PI, RJ, RN, RS, RO, RR, SC, SP, SE, TO. |
| `instrucoes_recebimento` | `text` | Obrigatório | Não | Como combinar a ajuda fora da plataforma. |
| `status` | `varchar(8)` | Automático | Não | Situação atual do cadastro. Opções: pendente, aprovada, recusada. |
| `analisada_por_id` FK | `bigint` | Condicional | Sim | Administrador que decidiu sobre o cadastro. |
| `analisada_em` | `timestamp with time zone` | Condicional | Sim | Horário da decisão sobre a ONG. |
| `motivo_analise` | `varchar(500)` | Condicional | Não | Explicação da análise; necessária ao recusar. |
| `criada_em` | `timestamp with time zone` | Automático | Não | Horário de criação. |
| `atualizada_em` | `timestamp with time zone` | Automático | Não | Horário da alteração mais recente. |

Uma conta pode ser responsável por uma única ONG. CNPJ preenchido não pode se repetir. Os estados são `pendente`, `aprovada` e `recusada`. A decisão exige administrador e horário; recusa também exige motivo. Nome, CNPJ ou endereço alterados após aprovação fazem o cadastro voltar para análise.
## Campanha
Tabela: `campaigns_campanha`.
| Campo | Tipo | Preenchimento | NULL? | Para que serve |
| --- | --- | --- | --- | --- |
| `id` PK | `bigint` | Automático | Não | Número que identifica o registro. |
| `ong_id` FK | `bigint` | Obrigatório | Não | Organização à qual o registro está ligado. |
| `titulo` | `varchar(150)` | Obrigatório | Não | Nome curto exibido na interface. |
| `descricao` | `text` | Obrigatório | Não | Necessidade que a campanha quer atender. |
| `tipo` | `varchar(8)` | Obrigatório | Não | Modalidade de ajuda definida na campanha. Opções: dinheiro, item, horas. |
| `unidade` | `varchar(30)` | Obrigatório | Não | Medida usada pela campanha. |
| `meta` | `numeric(12, 2)` | Obrigatório | Não | Quantidade ou valor que se pretende alcançar. |
| `data_inicio` | `date` | Obrigatório | Não | Primeiro dia de recebimento. |
| `data_fim` | `date` | Obrigatório | Não | Último dia de recebimento. |
| `status` | `varchar(9)` | Automático | Não | Etapa atual da campanha. Opções: rascunho, ativa, pausada, encerrada. |
| `criada_em` | `timestamp with time zone` | Automático | Não | Horário de criação. |
| `atualizada_em` | `timestamp with time zone` | Automático | Não | Horário da alteração mais recente. |

A meta deve ser positiva e o fim não pode vir antes do início. Os tipos são `dinheiro`, `item` e `horas`. Os estados são `rascunho`, `ativa`, `pausada` e `encerrada`. Dinheiro usa BRL; voluntariado usa hora. Itens têm meta inteira. Tipo e unidade ficam protegidos depois da primeira contribuição.
## Contribuição
Tabela: `contributions_contribuicao`.
| Campo | Tipo | Preenchimento | NULL? | Para que serve |
| --- | --- | --- | --- | --- |
| `id` PK | `bigint` | Automático | Não | Número que identifica o registro. |
| `campanha_id` FK | `bigint` | Obrigatório | Não | Campanha associada ao registro. |
| `autor_id` FK | `bigint` | Obrigatório | Não | Conta que ofereceu ou declarou a ajuda. |
| `tipo` | `varchar(8)` | Automático | Não | Modalidade da campanha vinculada. Opções: dinheiro, item, horas. |
| `valor` | `numeric(12, 2)` | Condicional | Sim | Quantia em reais, usada para dinheiro. |
| `quantidade` | `numeric(12, 2)` | Condicional | Sim | Medida de itens ou de horas. |
| `observacao` | `varchar(500)` | Opcional | Não | Comentário que acompanha a contribuição. |
| `status` | `varchar(10)` | Automático | Não | Etapa atual da contribuição. Opções: declarada, aceita, confirmada, recusada, cancelada. |
| `avaliada_por_id` FK | `bigint` | Condicional | Sim | Responsável que tomou a última decisão. |
| `avaliada_em` | `timestamp with time zone` | Condicional | Sim | Horário da última avaliação. |
| `motivo_avaliacao` | `varchar(500)` | Condicional | Não | Justificativa da decisão; necessária na recusa. |
| `criada_em` | `timestamp with time zone` | Automático | Não | Horário de criação. |
| `atualizada_em` | `timestamp with time zone` | Automático | Não | Horário da alteração mais recente. |

Dinheiro usa valor positivo e quantidade nula. Itens e horas usam quantidade positiva e valor nulo. Itens não aceitam fração. Os estados são `declarada`, `aceita`, `confirmada`, `recusada` e `cancelada`. Dinheiro não passa por aceite. Avaliação exige responsável e horário; recusa exige motivo. O tipo deve ser o da campanha.
## Postagem
Tabela: `organizations_postagem`.
| Campo | Tipo | Preenchimento | NULL? | Para que serve |
| --- | --- | --- | --- | --- |
| `id` PK | `bigint` | Automático | Não | Número que identifica o registro. |
| `ong_id` FK | `bigint` | Obrigatório | Não | Organização à qual o registro está ligado. |
| `campanha_id` FK | `bigint` | Opcional | Sim | Campanha associada ao registro. |
| `titulo` | `varchar(150)` | Obrigatório | Não | Nome curto exibido na interface. |
| `conteudo` | `text` | Obrigatório | Não | Texto da atualização da ONG. |
| `publicada` | `boolean` | Automático | Não | Indica se a postagem saiu do rascunho. |
| `criada_em` | `timestamp with time zone` | Automático | Não | Horário de criação. |
| `atualizada_em` | `timestamp with time zone` | Automático | Não | Horário da alteração mais recente. |

A campanha é opcional. Quando preenchida, precisa ser da mesma ONG. Publicar exige ONG aprovada e, se houver campanha, ela não pode estar em rascunho. O texto tem limite de 5.000 caracteres.
## Cache de CEP
Tabela: `integrations_cachecep`.
| Campo | Tipo | Preenchimento | NULL? | Para que serve |
| --- | --- | --- | --- | --- |
| `cep` PK | `varchar(8)` | Obrigatório | Não | CEP usado como chave do endereço guardado. |
| `logradouro` | `varchar(200)` | Opcional | Não | Rua ou outro logradouro do endereço. |
| `bairro` | `varchar(100)` | Opcional | Não | Bairro da organização. |
| `cidade` | `varchar(100)` | Obrigatório | Não | Município do endereço. |
| `uf` | `varchar(2)` | Obrigatório | Não | Sigla do estado. |
| `expira_em` | `timestamp with time zone` | Automático | Não | Prazo de validade do endereço no cache. |

Só recebe endereços válidos. Cada CEP identifica uma entrada com validade de 24 horas. Logradouro e bairro podem chegar vazios. O cache não tem vínculo por chave estrangeira com a ONG.
## Vínculos
| Relação | Quantidade |
| --- | --- |
| Usuário responsável → ONG | Usuário: zero ou uma ONG. ONG: um responsável. |
| Usuário administrador → ONG analisada | Usuário: várias ONGs. ONG: zero ou um analisador. |
| ONG → Campanha | ONG: várias campanhas. Campanha: uma ONG. |
| ONG → Postagem | ONG: várias postagens. Postagem: uma ONG. |
| Campanha → Postagem | Campanha: várias postagens. Postagem: zero ou uma campanha. |
| Campanha → Contribuição | Campanha: várias contribuições. Contribuição: uma campanha. |
| Usuário autor → Contribuição | Usuário: várias contribuições. Contribuição: um autor. |
| Usuário avaliador → Contribuição | Usuário: várias avaliações. Contribuição: zero ou um avaliador. |

“Várias” inclui zero registros. A exclusão de registros referenciados é protegida. No vínculo da postagem com a campanha, excluir a campanha apenas retira essa referência.
## Regras que precisam continuar valendo
O banco verifica medidas positivas, ordem das datas e coerência dos dados de avaliação. A aplicação confere permissões, escolhas de estado, unidade e vínculos entre registros. Os estados são textos validados, sem ENUM nativo do PostgreSQL.
O relatório não vira uma tabela. Ele reúne os registros confirmados e separa dinheiro, itens e horas. Total, percentual e disponibilidade são calculados. Sessões, grupos e permissões internas do Django ficam fora destas seis entidades.
## Onde cada entidade entra
Usuário participa do login e das contribuições. ONG participa do cadastro e da aprovação. Campanha é o destino da ajuda. Contribuição guarda o registro e a decisão da ONG. Postagem divulga atualizações. Cache de CEP auxilia o endereço durante o cadastro.
[Diagrama PNG](modelo.png) · [Fonte DBML](modelo.dbml) · [Fonte draw.io](modelo.drawio)
