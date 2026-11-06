---
name: ig-profile
description: >-
  Dá nota de 0 a 100 a um perfil de Instagram com uma rubrica de 12 itens e
  reescreve em português as partes que perdem pontos - campo de nome, bio,
  link, destaques, os três fixados, grid. Use quando a pessoa disser
  "otimiza meu perfil", "arruma minha bio", "dá nota no meu Instagram", "por
  que ninguém me segue", ou colar o perfil e perguntar como ele soa.
---

# ig-profile

Quase todo mundo otimiza a coisa errada aqui. O perfil não é uma vitrine que
as pessoas ficam olhando. É uma **tela de decisão**, onde a pessoa chega vinda
de um reels, e ela tem uns três segundos pra responder uma pergunta: tem mais
disso aqui, e é pra mim?

## Entrada

Peça pra pessoa colar ou mandar print de: o campo de nome, o @, a bio, pra onde
o link aponta, os nomes dos destaques, o que está fixado e as nove primeiras
capas do grid. Um print do topo do perfil mais as duas primeiras linhas do
grid basta pra uma primeira passada.

Não entre no Instagram em nome dela.

## Dê a nota

Leia o `rubric.json` nesta pasta. Doze itens, 100 pontos, cada um com como é
a nota cheia e como costuma falhar. Dê nota em todos, mostre a tabela, dê o
total, com honestidade. A maioria dos perfis fica entre 30 e 49 na primeira
passada, e nota generosa não serve pra nada.

```
NOTA DO PERFIL  38/100

  campo de nome          2/12   só o nome, nenhuma palavra que alguém buscaria
  primeira linha da bio  3/12   três substantivos e um emoji de café
  três fixados           0/10   nada fixado
  destaques              2/8    "Aleatório", "Vida", "2023"
  leitura do grid        4/8    seis das nove capas são um rosto no meio da frase
  ...
```

## Depois reescreva, nesta ordem

Corrija na ordem de pontos perdidos, do maior pro menor. Não reescreva tudo de
uma vez: a pessoa precisa ir lá e mudar cada uma dessas coisas.

**1. O campo de nome (30 caracteres).** A linha em negrito embaixo da foto, não
o @. É o campo que a busca do Instagram compara, e a maioria das contas coloca
só um nome. Formato que funciona: `{Nome} | {o que faz, em palavras buscadas}`.
Pense em como um brasileiro digitaria na busca: "nutricionista esportiva",
"contabilidade pra MEI", "fotógrafa de casamento SP". Dê três opções.

**2. Primeira linha da bio.** Pra quem é e o que muda. Não é cargo, não são
adjetivos, não é uma lista de identidades separada por barras. O resto dos 150
caracteres carrega uma prova ou uma oferta simples.

**3. Os três fixados.** Três espaços, três trabalhos: a melhor prova, a
explicação mais clara da oferta, a melhor apresentação da pessoa. É a
correção de maior alavancagem do perfil inteiro e leva quatro toques. Um grid
sem fixados mostra o que foi postado por último, que é cara ou coroa.

**4. Destaques.** De quatro a seis, com nome das perguntas que um comprador faz:
Preços, Resultados, Como funciona, Sobre. Não "Aleatório". Apague o resto.

**5. O link.** Um destino que combina com o que a bio acabou de prometer. São
permitidos cinco; dois já é um cardápio, e cardápio converte pior que porta.
Se a pessoa vende pelo WhatsApp, o link pode ir direto pra conversa, com uma
mensagem pré-preenchida.

**6. Capas do grid.** As nove primeiras em tamanho de miniatura. Capa de reels
é escolhida, não deixada no primeiro quadro. Quatro palavras de texto numa
capa deixam o grid legível numa olhada.

## Profissões regulamentadas

Se a pessoa é de uma profissão com regra de publicidade (advocacia, medicina,
odontologia, psicologia, nutrição, mercado financeiro, por exemplo), pergunte
se existe alguma restrição do conselho dela antes de escrever promessa de
resultado, preço ou depoimento na bio. Não adivinhe a regra: peça pra ela
confirmar com o próprio conselho.

## Saída

Tabela de nota, depois as reescritas como blocos prontos pra copiar, na ordem
de correção, cada uma passada pela `/ig-human`. Dê a nota de novo no fim e
mostre a diferença com honestidade. Se a reescrita chega a 84 e não a 98, diga
84, e diga o que falta, que geralmente é um grid, um hábito de stories e um
post fixado que ainda não existe. Nada disso é reescrita.

Nada é salvo no Instagram por esta skill. A pessoa edita cada campo.
