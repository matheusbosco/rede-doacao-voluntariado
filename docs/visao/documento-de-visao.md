# Documento de Visão — DAI

Projeto: DAI, rede de doação e voluntariado local.
Autor: Matheus Benjamim de Souza Bosco · Disciplina: Desenvolvimento Web (UniCEUB) · Versão 1.0, 08/10/2026.

## 1. Contexto e problema

O problema acontece dos dois lados. Tem gente que tem vontade de doar, fazer trabalho vokuntário e ações de caridade mas não faz ideia de por onde começar, não conhece ONGs, não sabe o que elas estão precisando e nem como ajudar. E tem ONG precisando de apoio, principalmente uma que está começando agora e depende de redes sociais com poucos seguidores para encontrar essas pessoas. Como as informações ficam espalhadas em vários lugares, quem quer ajudar pode acabar ficando perdido, enquanto a organização continua sem conseguir o apoio que precisa.

## 2. Justificativa

Escolhi esse tema porque achei interessante trabalhar com uma dificuldade em que existe gente querendo ajudar e gente precisando dessa ajuda, mas falta uma forma mais fácil de conectar os dois lados. Eu mesmo sinto que me enquadro nisto, tenho disposição e vontade de fazer ações de caridade, mas não sei por onde começar. E principalmente pensando nas ONGs menores, que podem estar fazendo um trabalho importante e ainda não ter visibilidade. O que me motivou foi a possibilidade de usar o projeto para facilitar esse encontro e dar mais espaço para essas organizações mostrarem o que fazem e do que precisam. Também existem motivações religiosas cristãs da minha parte, o próprio nome DAI foi inspirado em passagens bíblicas. “Dá a quem te pedir e não te desvies daquele que quiser que lhe emprestes.” Mateus 5:42.

## 3. Proposta

A ideia do DAI é reunir ONGs e suas campanhas em um só lugar, para facilitar o encontro entre quem precisa de apoio e quem quer ajudar.

## 4. Objetivos

O objetivo principal do DAI é facilitar o encontro entre quem quer ajudar e as ONGs que precisam desse apoio, principalmente as menores e que ainda não têm tanta visibilidade. Para isso, quero reunir as informações das organizações, permitir que publiquem campanhas e facilitar a busca por localização e interesse. Também quero que tanto o usuário quanto a ONG consigam acompanhar as contribuições, diferenciando o que foi apenas oferecido do que realmente aconteceu. Na parte técnica, os objetivos são entregar uma aplicação com banco de dados, API própria, integração com o ViaCEP e relatório que possa ser consultado e exportado.

## 5. Público-alvo e funcionalidades por perfil

Quem estiver só conhecendo a plataforma poderá entrar como visitante e pesquisar ONGs e campanhas. Os doadores e voluntários poderão se cadastrar, registrar doações ou oferecer itens e horas de voluntariado, além de acompanhar o que aconteceu com essas contribuições. Já os responsáveis pelas ONGs vão cuidar dos perfis, publicar campanhas e postagens e confirmar o recebimento das doações ou a realização das atividades. Também haverá um administrador para analisar e aprovar os cadastros das organizações.

## 6. Stakeholders

Os stakeholders são todos os envolvidos ou afetados pelo projeto. Nesse caso, entram os doadores e voluntários, que procuram oportunidades para ajudar, os responsáveis pelas ONGs, que precisam divulgar suas necessidades e acompanhar as contribuições, e os visitantes que ainda estão conhecendo a plataforma. Também entram o administrador que analisa os cadastros, as comunidades beneficiadas pelo trabalho das organizações, eu como responsável pelo desenvolvimento e o professor que acompanha e avalia a entrega.

## 7. Fora do escopo

Eu decidi que o DAI não vai processar pagamentos, porque isso aumentaria muito a complexidade do projeto. A transferência acontece por fora, e a pessoa depois registra no sistema que fez aquela doação. A entrega dos itens e o trabalho voluntário também são combinados fora da plataforma. Além disso, não vou incluir integrações bancárias, recibos fiscais, chat, aplicativo móvel nativo ou certificação de que uma ONG é confiável. Quero manter um escopo que eu consiga desenvolver e entregar funcionando.

## 8. Restrições

Estou fazendo o projeto sozinho e tenho até 04/12/2026 para entregar a aplicação completa. Então preciso dividir meu tempo entre desenvolvimento, documentação, testes e publicação. Sobre dinheiro e hospedagem, a intenção é usar serviços gratuitos, o que também exige cuidado com os limites desses serviços e com a disponibilidade da aplicação.

## 9. Premissas

Sobre as premissas, estou partindo da ideia de que as ONGs vão fornecer informações verdadeiras e manter seus perfis e campanhas atualizados. Também considero que haverá um administrador disponível para analisar os cadastros e que os responsáveis pelas organizações vão conferir as contribuições antes de confirmá-las. Como a transferência, a entrega e o voluntariado acontecem fora do DAI, é preciso que a ONG disponibilize um contato ou instruções para combinar esses detalhes. Outra premissa é que os usuários tenham acesso à internet e consigam utilizar a plataforma pelo navegador, tanto no computador quanto no celular.

## 10. Riscos

Uma preocupação é alguém cadastrar uma ONG falsa, registrar uma doação que não fez ou oferecer uma ajuda e depois não realizar. Para diminuir esses problemas, os cadastros das ONGs passarão por aprovação, e as contribuições só entrarão nos totais depois da confirmação da organização. Também preciso evitar que dados pessoais fiquem expostos ou que um usuário consiga alterar informações de outra pessoa. Para isso, vou usar controle de acesso e testar essas permissões. Se o ViaCEP falhar, será possível preencher o endereço manualmente; sobre a hospedagem, vou acompanhar os limites e verificar se a aplicação continua disponível.

## 11. Critérios de sucesso

No fim, quero conseguir demonstrar todo o caminho funcionando: cadastrar e aprovar uma ONG, publicar uma campanha, encontrar essa campanha pela busca, registrar uma contribuição e confirmar sua realização. Vou conferir também se uma contribuição ainda não confirmada fica fora dos totais e se, depois da confirmação, entra uma única vez, sempre separando dinheiro, itens e horas. O relatório com exportação em CSV, a API própria e a consulta pelo ViaCEP precisam funcionar, e a aplicação deve estar acessível por HTTPS. Os testes também precisam mostrar que cada usuário só consegue alterar o que tem permissão para alterar.
