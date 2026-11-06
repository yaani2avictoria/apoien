---
name: ig-audit
description: >-
  Faz o pós-morte do que a pessoa já postou - quais reels funcionaram de
  verdade, por quê, e o que parar de fazer. Use quando a pessoa colar os
  insights ou posts antigos do Instagram e perguntar "o que tá funcionando",
  "por que esse flopou", "lê minhas métricas", "audita meu conteúdo", ou
  quiser saber do que fazer mais.
---

# ig-audit

A única fonte honesta do que funciona pra uma conta é a própria conta. Toda
regra de todo guia de Instagram, incluindo as deste pacote, é um palpite
inicial. Os últimos 30 posts da pessoa são a evidência.

## Entrada

Peça o que a pessoa tiver:

- Insights por post: visualizações, alcance, interações, tempo de exibição,
  salvamentos, compartilhamentos, seguidores ganhos, e a fatia do alcance que
  veio de não seguidores. Print serve.
- Ou o gráfico de retenção dos melhores e piores reels recentes. Esse print
  sozinho vale mais que todo o resto junto.
- Ou só os posts e as views, que basta pra uma primeira passada.

Leia também `~/.claude/instagram/log.md` se existir, porque ele registra qual
fórmula de gancho cada post usou.

## O que medir de verdade

View bruta é o número menos útil da tela, porque depende principalmente de
quantas pessoas já seguem a conta. Calcule estes no lugar, e mostre a conta:

| métrica | como | o que te diz |
| --- | --- | --- |
| **Múltiplo** | views / mediana de views da própria conta | se foi acerto de verdade ou um dia normal |
| **Alcance de não seguidores** | % do alcance vindo de quem não segue | se o post viajou |
| **Retenção aos 3s** | quem ainda está aos 3s / quem começou | se o gancho funcionou. É a nota do gancho. |
| **Tempo médio de exibição** | direto dos insights | se o meio funcionou |
| **Envios por alcance** | compartilhamentos / alcance | o sinal mais forte que dá pra ganhar. Um envio é uma pessoa colocando o nome dela no seu post. |
| **Seguidores por alcance** | seguidores ganhos / alcance | se o perfil converteu a atenção |

Ranqueie por múltiplo e por envios por alcance, não por views. Um reels com
4.000 views e 90 envios ganhou do que teve 60.000 views e 11.

## Depois ache o padrão

Com os cinco de cima e os cinco de baixo lado a lado, procure o que separa os
dois grupos, e esteja disposto a concluir algo que a pessoa não vai gostar:

- **Retenção aos 3 segundos.** Se o grupo de cima e o de baixo diferem aqui, é
  o gancho e nada mais, e todo o resto é distração.
- **Fórmula de gancho.** Quais números do `ig-reel/hooks.json` estão nos cinco
  de cima?
- **Formato.** Reels, carrossel, imagem única.
- **Duração.** Agrupe em menos de 15s, de 15 a 30s, de 30 a 60s, mais de 60s.
- **Tema.**
- **Se a pessoa respondeu comentários na primeira hora.**
- **Dia e horário.** Olhe isso **por último**, e só se o resto não mostrar
  nada. Quase nunca é a causa, e é onde as pessoas querem que seja.

Diga o achado como uma afirmação com a evidência junto, e diga o quanto ele é
confiável. Com 30 posts dá pra ver um padrão. Com 6 não dá, e dizer isso é
melhor que inventar um.

## A distinção que economiza meses

**Um reels que tem views e não traz seguidor não é um reels que falhou, é um
problema de perfil.** Um reels sem views é um problema de gancho. Separe os
dois antes de recomendar qualquer coisa. Se o alcance de não seguidores é alto
e os seguidores por alcance são baixos, pare de reescrever gancho e vá pra
`/ig-profile`.

## Saída

```
AUDITORIA  ·  31 posts  ·  12/06 a 05/09  ·  mediana de views 4.100

5 DE CIMA POR MÚLTIPLO
  18.2x  #3  Ninguém Te Conta    74.600 views  62% não seguidores  ret@3s 71%  128 envios
   6.4x  #1  Confissão de Custo  26.300 views  48% não seguidores  ret@3s 64%   71 envios
  ...

5 DE BAIXO
   0.3x  #11 Lista com Favorito   1.200 views   9% não seguidores  ret@3s 31%    2 envios
  ...

O QUE OS DADOS DIZEM
1. Retenção aos 3 segundos é a história inteira. Os cinco de cima têm média de
   66%, os de baixo 33%. Todo o resto que te preocupa vem depois dos dois
   primeiros segundos.
2. Os posts em que quem passou vergonha foi você: média de 8,1x contra 0,9x de
   todo o resto. n=5. É o sinal mais forte aqui, e não tem disputa.
3. Lista de ferramentas dá view e nada mais. Alcance alto, nenhum envio,
   nenhum seguidor. Três dos seus cinco de baixo.
4. Dia da semana não mostra nada. As médias de terça e sexta estão dentro do
   ruído. Para de otimizar isso.

PARE: listas de ferramentas.
FAÇA MAIS: os posts com um custo que você pagou e um número junto.
```

(Os números acima ilustram o formato; os seus vêm dos insights da pessoa.)

Depois passe as conclusões pra `/ig-plan`, pra próxima semana ser montada com
a evidência da própria pessoa e não com padrões, e pra `/ig-viral`, pro
arquivo de referências ser filtrado pelas fórmulas que funcionam pra esta
conta especificamente.
