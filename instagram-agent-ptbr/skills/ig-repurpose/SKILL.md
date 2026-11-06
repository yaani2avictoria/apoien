---
name: ig-repurpose
description: >-
  Transforma um conteúdo longo - vídeo do YouTube, podcast, live, newsletter,
  artigo de blog ou call com cliente - numa semana de reels e carrosséis em
  português. Use quando a pessoa disser "reaproveita isso", "transforma isso
  em reels", "tenho um vídeo/podcast/transcrição", "corta isso", ou colar
  algo longo e quiser no Instagram.
---

# ig-repurpose

Um bom conteúdo longo tem de quatro a seis posts dentro. A maioria das pessoas
tira um e joga o resto fora.

## Entrada

Uma transcrição, um artigo, uma newsletter, um roteiro, um resumo de call, uma
live. Se a pessoa mandar um link e esta sessão tiver uma ferramenta de
transcrição, use; se não, peça pra colar. Leia tudo antes de extrair qualquer
coisa.

Se a fonte é um vídeo da própria pessoa, peça o arquivo também. Um Reels feito
com a filmagem dela ganha de um feito com as palavras dela lidas de novo.

## Extraia, não resuma

Resumo de vídeo não é Reels. Ninguém quer o resumo. Passe pelo conteúdo e tire
as coisas que se sustentam sozinhas:

| tirar | o que é |
| --- | --- |
| **Afirmações** | toda frase que começaria uma discussão |
| **Números** | todo valor, custo, duração, porcentagem |
| **Histórias** | todo momento com uma pessoa, uma cena e um custo |
| **Mecanismos** | todo "o jeito que isso funciona de verdade é..." |
| **Erros** | toda admissão de algo que deu errado |
| **Frases** | toda frase que já dá pra citar do jeito que está |

Liste o que achou, com contagens, antes de escrever qualquer coisa. Se o
conteúdo rende menos de quatro itens, ele é ralo, e quatro posts espremidos
dele vão ser ralos também. Diga isso.

## Depois escolha o formato de cada extração

Nem tudo é Reels.

- **Afirmação, erro, história** viram Reels. Precisam de voz e rosto.
- **Mecanismo, lista numerada** viram carrossel. Precisam ser relidos.
- **Uma frase citável** vira um quadro de story, não um post.

## Depois monte a semana

Cada extração vira um post, e cada post se sustenta completamente sozinho.
Quem assiste não viu a fonte e nunca vai ver. Nunca escreva "como eu falei no
meu último vídeo". O post é a coisa.

Dê uma fórmula de gancho do `ig-reel/hooks.json` pra cada um e varie. Cinco
posts da mesma fonte com o mesmo formato de gancho parecem fábrica de
conteúdo, porque são.

Se a fonte é vídeo da própria pessoa, **use a filmagem de verdade**. O trecho
em que ela disse a coisa, com a reação de verdade, ganha de uma regravação
sempre. Corte na frase, não na respiração.

Ordene a semana pra afirmação mais forte ir primeiro, a história cair no meio
da semana e o mecanismo ir por último, quando quem gostou dos anteriores está
esperando por ele.

## Saída

```
FONTE: "Por que a gente matou a call de diagnóstico" (podcast de 42 min, 8.900 palavras)

ENCONTRADO  5 afirmações, 9 números, 3 histórias, 4 mecanismos, 2 erros, 7 frases citáveis

SEMANA
TER  REELS      #2  Comando Negativo  Para de fazer call de diagnóstico
                                      usar o trecho de 14:20, ele ri no fim
QUA  CARROSSEL  legenda Trabalho B    O formulário de 4 perguntas que substituiu a call
SEX  REELS      #21 Começo no Meio    "...e nove dias depois ele pediu reembolso"
DOM  REELS      #5  Colapso de Tempo  Seis horas por semana de volta, um link apagado

Diga "escreve terça" e eu faço o rascunho.
```

Depois escreva sob pedido, um de cada vez, cada um pela `/ig-reel` e pela
`/ig-human`. Não despeje quatro roteiros prontos de uma vez. Eles vão soar
todos iguais e a pessoa não vai gravar nenhum.
