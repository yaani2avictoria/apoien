---
name: ig-plan
description: >-
  Monta a semana no Instagram em português - o que postar, em qual formato,
  quando, e com quem interagir. Use quando a pessoa disser "planeja minha
  semana", "o que eu posto", "calendário de conteúdo", "não tenho nada pra
  postar", "cronograma de posts", ou quiser uma agenda de postagem e uma lista
  de interação.
---

# ig-plan

A sala de controle. Todas as outras skills do pacote executam; esta decide o
que vai ser executado. Rode uma vez por semana, sempre no mesmo dia.

## Entrada

Se `~/.claude/instagram/voice.md`, `swipe.md` e `log.md` existirem, leia. O
arquivo de referências é a evidência da própria pessoa, vinda da `/ig-viral`,
sobre quais fórmulas estão funcionando no nicho dela agora, e ele vale mais
que qualquer coisa neste arquivo. O log impede o plano de repetir um tema das
últimas duas semanas.

Se não existirem, pergunte quatro coisas e anote:

1. O que a pessoa vende, e pra quem.
2. Os três ou quatro temas pelos quais ela quer ser conhecida.
3. O que aconteceu de verdade esta semana: uma call com cliente, um número, um
   erro, uma coisa que ela construiu, uma discussão que ela teve. É daqui que
   os posts saem.
4. Dez contas pra quem vale a pena ser visível.

## O que postar

De quatro a cinco posts por semana, e pelo menos três deles Reels. Reels é o
único formato do Instagram que chega com regularidade em quem não segue a
conta. Carrossel aprofunda com quem já segue. Stories são diários e
planejados à parte.

Misture ao longo da semana, nunca dois do mesmo tipo seguidos:

| tipo | quantidade | trabalho |
| --- | --- | --- |
| **Prova** | 1 por semana | algo que aconteceu, com um número. Reels. |
| **Ensino** | 1 a 2 por semana | uma coisa que a pessoa pode fazer hoje. Reels ou carrossel. |
| **Opinião** | 1 por semana | uma posição que pode te fazer perder seguidor. Reels. |
| **História** | 1 a cada 15 dias | uma cena com um custo. Reels. |
| **Oferta** | 1 a cada 15 dias | o que você vende, dito com clareza, sem pedir desculpa. Carrossel ou stories. |

Pra cada espaço, dê: o tema, o ângulo específico tirado do que aconteceu de
verdade nesta semana, o formato, e o número da fórmula de gancho do
`ig-reel/hooks.json`. Não um assunto, um ângulo. "IA" não é plano. "A proposta
que a gente perdeu porque o rascunho tinha um travessão" é um Reels.

## Quando postar

Poste quando o público da pessoa está acordado e não está trabalhando. Pra
maioria dos públicos de consumo, isso é começo da noite no horário local; pra
público de negócios, começo da manhã. No Brasil, lembre que a maior parte do
público costuma estar no horário de Brasília, mas não todo: se o público é do
Norte, do Nordeste ou de fora do país, ajuste.

Mas diga isso com clareza: **o horário importa muito menos que os dois
primeiros segundos.** O Instagram continua mostrando um Reels por dias se ele
performa, e enterra um bem cronometrado que não performa. Se a pessoa está
otimizando horário de postagem antes de os ganchos funcionarem, ela está
polindo a coisa errada, e você deve dizer isso.

Ancore os horários no fuso do público, não no da pessoa, se forem diferentes.

## A rodada de interação, que não é opcional

20 minutos por dia, antes de postar, não depois. Monte uma lista de 10:

- **5 de alcance** - contas com o público que a pessoa quer, onde um bom
  comentário é visto. Comente cedo, antes de o fio ter 200 comentários.
- **3 pares** - mesmo tamanho, mesma área. É o grupo que retribui.
- **2 compradores** - gente que poderia comprar de verdade. Comente por
  semanas antes de qualquer direct, e nunca venda num comentário.

Passe a lista pra `/ig-comment`.

## Saída

```
SEMANA DE 15/09

SEG  só interação  (20 min, lista abaixo)
TER  19h30  REELS      PROVA    #5  Colapso de Tempo  - proposta de 5h pra 20 min
QUA  só stories + interação
QUI  19h00  CARROSSEL  ENSINO   legenda Trabalho B    - a cláusula em 4 slides
SEX  19h30  REELS      OPINIÃO  #2  Comando Negativo  - para de fazer call de diagnóstico
SÁB  -
DOM  18h00  REELS      HISTÓRIA #21 Começo no Meio    - o e-mail de reembolso

STORIES  todo dia, de 3 a 5 quadros, caixa de perguntas na quinta.

INTERAÇÃO  (5 alcance / 3 pares / 2 compradores)
  ...

Diga "escreve terça" e eu faço o rascunho.
```

Grave o plano em `~/.claude/instagram/plan.md` pras outras skills lerem. Nada
é agendado nem postado em lugar nenhum. Isto é um plano e quem executa é a
pessoa.
