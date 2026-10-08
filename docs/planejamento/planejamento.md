# Planejamento

O DAI é um projeto individual. Eu, Matheus Bosco, fico responsável pelas decisões, pela revisão e pela entrega. A implementação e a preparação destes documentos têm apoio de IA, como registrado no README. A ideia agora é terminar a documentação, colocar a aplicação no ar e deixar tempo para corrigir o que aparecer nos testes de segurança.

## Tarefas

| O que precisa ser feito | Responsável | Prazo | Situação |
| --- | --- | --- | --- |
| Construir os cadastros, campanhas, postagens e contribuições | Matheus Bosco, com apoio de IA | 06–07/10/2026 | Implementado |
| Construir busca, relatório, API e consulta de CEP | Matheus Bosco, com apoio de IA | 06–07/10/2026 | Implementado |
| Configurar a integração contínua e verificar as execuções | Matheus Bosco, com apoio de IA | 08/10/2026 | CI aprovado em três execuções |
| Revisar visão, casos, banco, arquitetura, APIs e identidade | Matheus Bosco, com apoio de IA na redação | 09/10/2026 | Em revisão |
| Conferir README, links e declaração de uso de IA | Matheus Bosco | 09/10/2026 | A conferir |
| Confirmar a data da Fase 1 e resolver o convite ao professor | Matheus Bosco | 09/10/2026 | A conferir |
| Validar os fluxos de dinheiro, itens e voluntariado | Matheus Bosco, com apoio de IA nos testes | 16/10/2026 | A fazer |
| Revisar as telas no celular e decidir a troca das fontes | Matheus Bosco | 23/10/2026 | A fazer |
| Testar as falhas do ViaCEP e revisar os exemplos da API | Matheus Bosco, com apoio de IA | 30/10/2026 | A fazer |
| Publicar no Render, conectar o Neon e conferir o HTTPS | Matheus Bosco, com apoio de IA | 06/11/2026 | Configuração pronta; publicação a validar |
| Preparar contas e dados fictícios para avaliação | Matheus Bosco | 13/11/2026 | A fazer no ambiente publicado |
| Executar SAST e analisar os resultados | Matheus Bosco, com apoio de IA na execução | 20/11/2026 | Rodada final a fazer |
| Executar DAST na aplicação própria e corrigir os achados | Matheus Bosco, com apoio de IA | 27/11/2026 | A fazer após a publicação |
| Repetir as verificações e escrever o relatório de segurança | Matheus Bosco | 04/12/2026 | A fazer |
| Atualizar documentação e links de acesso | Matheus Bosco | 04/12/2026 | A fazer |
| Preparar e ensaiar a apresentação | Matheus Bosco | 04/12/2026 | A fazer |
| Testar as contas e a disponibilidade da hospedagem | Matheus Bosco | 04/12/2026 | A fazer |
| Apresentar e entregar a Fase 2 | Matheus Bosco | 04/12/2026 | Agendado |

O prazo da Fase 1 é 09/10/2026 e o da Fase 2 é 04/12/2026, ambos às 08:00, conforme o portal da disciplina. A hospedagem precisa continuar funcionando até o fim da avaliação.

## Riscos

| O que pode atrapalhar | Como vou lidar com isso |
| --- | --- |
| Faltar tempo por ser um trabalho individual | Dividir as tarefas por semana e fechar primeiro o que a disciplina exige. |
| A hospedagem gratuita parar ou ficar lenta | Publicar em novembro e testar com antecedência, incluindo o acesso ao banco. |
| Aparecer uma falha de segurança perto da entrega | Fazer SAST e DAST em novembro e reservar o início de dezembro para ajustes. |
| O ViaCEP ficar indisponível na demonstração | Manter o endereço manual disponível e testar esse caminho antes. |
| O documento dizer uma coisa e o app fazer outra | Revisar os documentos sempre que uma regra mudar. |

## Como vou acompanhar

Cada tarefa concluída precisa ter algo que eu consiga mostrar: o fluxo funcionando, um teste aprovado ou um arquivo revisado. CI aprovado não encerra a avaliação de segurança. Ainda preciso interpretar os resultados, executar DAST e reunir as evidências finais.

Vou fazer commits por tarefa ou documento, usando `tipo(escopo): descrição` em inglês. Commit, push, merge e tag continuam dependendo da confirmação combinada. Na apresentação, vou mostrar uma contribuição desde o registro até a confirmação e conferir se ela aparece corretamente no relatório.
