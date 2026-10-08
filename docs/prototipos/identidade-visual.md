# Identidade do DAI

## Nome

O projeto se chama DAI, sempre em maiúsculas. Quero que a pessoa entre, encontre uma ONG e entenda como pode ajudar. Por isso, a interface usa fundo branco, azul nas ações e blocos com espaço suficiente para ler.

## Paleta

| Uso | Cor |
| --- | --- |
| Botões e links | Azul `#1D4ED8` |
| Marca e títulos | Azul escuro `#12315A` |
| Fundo e cartões | Branco `#FFFFFF` |
| Áreas de apoio | Azul claro `#EFF6FF` |
| Texto | `#223047` |
| Observações | `#52647A` |
| Bordas | `#CBD5E1` |
| Erros e recusa | `#B91C1C` |
| Confirmação | `#166534` |

Um estado precisa ter nome e mensagem. Só mudar a cor não é suficiente para explicar se a ajuda foi aceita ou recusada.

## Fontes

Hoje o app usa **Georgia nos títulos e na marca**. Nos textos, campos e botões, usa **a fonte do sistema, com system-ui**. Essas são as fontes da interface atual.

Lora e Inter ficam como uma possibilidade de mudança: Lora para títulos e Inter para o restante. A troca ainda não foi aplicada. Se eu mantiver essa escolha, vou atualizar o CSS e conferir as telas antes de tratar as duas como fontes oficiais do app. Não será usada a fonte proprietária da Anthropic.

## Logotipo

A marca é a própria escrita DAI, em azul escuro, sem símbolo adicional. O [SVG](logo.svg) mantém as letras editáveis e pede Georgia, com serif como alternativa. O [PNG](logo.png) é uma exportação transparente em DejaVu Serif, uma substituição de renderização; ele não representa uma fonte já instalada no aplicativo. A licença dessa fonte acompanha o arquivo.

Vou manter espaço em volta da marca e preservar suas proporções. Sobre fundo azul, a versão pode ser branca. Não vou esticar as letras nem acrescentar sombra.

## Telas

| Tela | O que a pessoa encontra |
| --- | --- |
| Busca de ONGs | Organizações aprovadas, com filtros de texto e endereço. |
| Busca de campanhas | Necessidades que podem ser filtradas por tipo e localização. |
| Perfil da ONG | Apresentação, contatos, endereço e formas de ajudar. |
| Campanha | Meta, prazo, progresso confirmado e opção de contribuir. |
| Registro da contribuição | Campo de valor ou quantidade e espaço para observação. |
| Painel da ONG | Campanhas, atualizações e contribuições para conferir. |
| Login | Entrada com nome de usuário e senha. |
| Cadastro | Dados necessários para abrir uma conta. |
| Cadastro da ONG | Identificação e endereço, com consulta de CEP opcional. |
| Minhas contribuições | Situação dos registros e ações permitidas ao autor. |
| Relatório | Resultado por campanha, com CSV e impressão. |
| Administração | Cadastros de ONGs aguardando uma decisão. |

As capturas existentes devem acompanhar essas descrições. O acesso público começa em /ongs/ e /campanhas/. A página / é o painel da conta, com login. No celular, vou conferir principalmente busca, cadastro e contribuição, para campos e botões continuarem fáceis de usar.
