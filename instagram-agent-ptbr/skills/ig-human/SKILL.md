---
name: ig-human
description: >-
  Tira a marca de máquina de qualquer rascunho em português - travessão,
  clichês de IA, caracteres invisíveis - e dá nota num painel de cinco
  checagens antes de o texto sair. Use sempre que um texto precisar soar
  humano, quando a pessoa disser "humaniza", "isso tá com cara de IA",
  "tira os travessões", "parece ChatGPT", "deixa mais natural", ou antes de
  mostrar qualquer legenda, roteiro, comentário, resposta ou direct.
---

# ig-human

Duas ferramentas ficam nesta pasta e as duas rodam de verdade. Use. Não faça
isso no olho.

```bash
python3 humanize.py rascunho.txt --report        # limpa e mostra o que mudou
python3 detect.py rascunho.txt                    # dá nota, cinco checagens
python3 detect.py antes.txt depois.txt            # mostra a diferença
```

As duas leem o `slop.json`: cerca de 250 palavras e expressões de clichê com
troca em português simples, 18 tipos de caractere invisível, 11 trocas
tipográficas e 18 marcas de estrutura. O último bloco é específico do
Instagram, o vocabulário que só aparece em legenda e locução ("para de
rolar", "nesse vídeo eu vou te mostrar", "me segue pra mais", "o algoritmo
ama"). A busca ignora acento, então "voce" e "você" casam igual.

O arquivo é pra ser editado. Se a pessoa usa de verdade uma palavra que a
lista troca, tire a palavra do arquivo. Se ela usa travessão de propósito
(diálogo, por exemplo), tire o travessão da lista `typographic`.

## Por que isso pesa mais no Instagram do que parece

Legenda é curta e roteiro é falado em voz alta. Uma frase com cara de texto
escrito numa legenda de 600 caracteres ocupa uma fatia maior do que a mesma
frase numa redação, e uma locução que ninguém falaria naturalmente fica óbvia
na primeira tomada. O problema aqui não é um detector marcar o post. O
problema é uma pessoa passar direto por algo que parece post de marca, ou um
criador tropeçando no próprio roteiro.

## O que é corrigido sozinho

**1. Caracteres invisíveis.** Zero-width spaces e joiners, word joiners, hífen
suave, BOM, caracteres de tag Unicode, separadores invisíveis, espaços rígidos
e estreitos. Teclado não produz isso. Eles sobrevivem ao copiar e colar, são
invisíveis em qualquer editor e são a coisa mais mecânica de um texto gerado.
O `humanize.py` apaga todos, inclusive qualquer caractere de formato Unicode
que não tenha nome na lista.

**2. Tipografia.** Travessão vira vírgula, meia-risca vira hífen, aspas curvas
viram retas, reticências de um caractere viram três pontos, marcador vira
hífen. A troca que importa é a do travessão: ele vira vírgula e depois o
script limpa a pontuação dupla e os pontos órfãos que sobram.

Atenção: o iPhone troca aspas retas por curvas sozinho (Pontuação
Inteligente). Aspa curva conta pouco na nota, mas se a pessoa escreve no
iPhone isso não é sinal de IA.

**3. Os clichês.** alavancar, potencializar, crucial, robusto, "sua jornada",
"vale ressaltar que", "no mundo acelerado de hoje", "virada de chave",
"conteúdo de valor", e o bloco do Instagram. Cada um trocado por uma palavra
simples ou apagado, mantendo maiúsculas e sem mexer em links.

## O que NÃO é corrigido sozinho

Marcas de estrutura são **apontadas, não reescritas**, porque mudar o formato
de uma frase exige julgamento:

- "Não é só X, é Y" e "não apenas X, mas também Y"
- "Não é sobre X. É sobre Y."
- Trios de três itens
- Linha de pergunta retórica: "O resultado?"
- A enrolação de vídeo: "nesse vídeo eu vou te mostrar", "vem comigo"
- A abertura "você sabia que"
- Lista com emoji no lugar de marcador
- Três ou mais palavras gritadas em caixa alta seguidas
- Parede de hashtags
- Isca automática: "me segue pra mais", "marca alguém que", "curte se"

Essa lista é trabalho seu. Reescreva cada linha apontada à mão, mantendo o
sentido, e rode o `detect.py` de novo. É essa parte que leva a nota de
REVISAR pra APROVADO, e é a parte que um script não consegue fazer.

Apagar uma abertura às vezes deixa um pedaço de frase ("Como repensar sua
mentalidade..."). Sempre releia o texto limpo e conserte a frase.

## As cinco checagens

O `detect.py` dá nota de 0 a 100 pra cinco sinais, e quanto maior, mais humano:

| checagem | o que mede | máquina parece |
| --- | --- | --- |
| RITMO | variação no tamanho das frases | toda frase do mesmo tamanho |
| ESPECIFICIDADE | números, nomes, R$, coisas concretas a cada 100 palavras | substantivo abstrato, nenhum número |
| CLICHÊS | ocorrências do vocabulário a cada 100 palavras | vocabulário de manual |
| MARCAS | invisíveis, travessões, aspas curvas a cada 1.000 caracteres | tipografia perfeita demais |
| VOZ | marcas de fala ("pra", "tá", "né", "a gente"), pessoa, marcas de estrutura | nenhuma marca de fala, revelações encenadas |

O veredito pesa a média em 60% e a **pior checagem** em 40%, porque um sinal
basta. APROVADO precisa de 70 ou mais no total e nenhuma checagem abaixo de 55.

A checagem VOZ é a principal adaptação pro português: no lugar das contrações
do inglês ("don't", "it's"), ela conta marcas de fala do português
brasileiro. Se a pessoa escreve de um jeito mais formal de propósito, a VOZ
vai ficar baixa e tudo bem: explique isso em vez de enfiar "pra" no texto dela.

## Fale isso com honestidade

São cinco heurísticas locais inspiradas nos sinais que detectores públicos
olham. Rodam inteiras na máquina da pessoa e nada é enviado. **Não** são
GPTZero, Originality, Copyleaks, Winston ou Turnitin, não chamam essas APIs e
não podem prometer o veredito delas. Corrigir o que elas medem costuma mexer
nesses números, porque elas medem as mesmas coisas por baixo. Essa é a
afirmação. Não faça uma maior em nome da pessoa e nunca diga que o texto dela
é indetectável.

Os limites foram herdados da versão em inglês e ajustados pro português, mas
ainda não foram validados com textos brasileiros reais. Trate a nota como
orientação, não como sentença.

## Ordem das operações

1. `humanize.py rascunho.txt -o limpo.txt --report`
2. Leia as marcas de estrutura. Reescreva essas linhas você mesmo.
3. `detect.py rascunho.txt limpo.txt` pra mostrar o antes e depois.
4. Se o veredito não é APROVADO, corrija a checagem mais fraca indicada na
   saída e rode de novo. Duas rodadas é normal. Cinco quer dizer que o
   rascunho foi escrito por fórmula, e a solução é outro rascunho, não mais
   rodadas.
5. Mostre pra pessoa o texto limpo e a nota. Nunca só a nota.
