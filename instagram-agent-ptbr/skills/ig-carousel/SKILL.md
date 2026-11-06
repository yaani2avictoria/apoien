---
name: ig-carousel
description: >-
  Monta um carrossel de Instagram em português - a capa que faz a pessoa
  arrastar, o texto slide a slide e os arquivos 1080x1350 pra subir. Use
  quando a pessoa disser "carrossel", "slides", "post de arrastar", "transforma
  isso num carrossel", ou tiver uma ideia em formato de lista ou de passo a
  passo que morreria numa imagem só.
---

# ig-carousel

Carrossel é o formato com mais tempo de atenção no grid, porque arrastar é uma
interação e rolar não é. E ele ganha uma segunda chance: o Instagram pode
mostrar o carrossel de novo, começando de um slide mais pra frente, pra quem
não interagiu da primeira vez. Então o slide dois também precisa se sustentar
sozinho.

O formato premia uma ideia quebrada em passos. E pune uma legenda picada em
pedaços.

## Quando usar no lugar de um Reels

Use carrossel quando a ideia tem **sequência e precisa ser relida**: passos,
um método com partes, um antes e depois, uma lista que vale print. Use Reels
quando a ideia tem movimento, rosto ou um resultado que precisa ser visto
acontecendo.

Se a ideia é uma afirmação só, não é nenhum dos dois. Passe pra `/ig-reel` e
diga isso.

## Estrutura

De 6 a 10 slides. O limite é 20, e 20 quase sempre é um livro que ninguém
termina. Com menos de 5, a pessoa nem começa a arrastar.

```
1         CAPA      o gancho. 6 palavras ou menos, num tamanho que dá pra ler
                    no grid em miniatura. Uma linha de promessa embaixo.
2         O QUE     por que isso importa, numa frase. Esse slide também é uma
          ESTÁ EM   segunda capa, então não pode ser preparação.
          JOGO
3 a N     UMA IDEIA POR SLIDE. Um título de 3 a 7 palavras, no máximo 25
                    palavras embaixo. Se um slide precisa de parágrafo, são
                    dois slides.
N+1       RESUMO    tudo numa lista. É o slide do print.
ÚLTIMO    CTA       uma ação. Salvar, comentar uma palavra ou seguir. Uma.
```

## Regras do texto dos slides

- **A capa é 80% do resultado.** Seis palavras. Grande. Nada no resto salva
  uma capa que ninguém arrasta.
- **Pense no corte do grid.** O grid do perfil corta num retângulo vertical,
  mais alto que largo, e a proporção exata já mudou mais de uma vez. Monte em
  1080x1350 e deixe o texto da capa bem no meio, longe dos 120 pixels de cada
  borda, e o corte deixa de importar.
- **Numere os slides** (3/8). A taxa de conclusão sobe quando a pessoa vê onde
  acaba.
- **Nenhum slide é parágrafo.** Se não dá pra dizer em 25 palavras, divida.
- **O slide de resumo é o que as pessoas printam e mandam.** Envio é o sinal
  mais forte que dá pra ganhar. Faça ele se sustentar sozinho, legível sem
  contexto.
- **O @ em todo slide**, pequeno, num canto de baixo. Print viaja sem você.
- **Texto alternativo pelo menos na capa.** É lido por leitores de tela e pelo
  Instagram.

## Montando os arquivos

O Instagram quer 1080x1350 (4:5), JPEG ou PNG, até 20 itens. Monte em HTML e
imprima cada slide:

```bash
# um <section> por slide, 1080x1350, page-break-after: always
# depois Chrome headless --print-to-pdf, ou qualquer HTML-pra-imagem que você já use
```

Escreva o HTML com `width:1080px; height:1350px`, uma cor de destaque só, e
nenhuma letra menor que 32px, porque isso é lido num celular a um terço do
tamanho real. Use uma fonte com acentuação completa (á, ã, ç, ê) e confira se
os acentos não estão cortados. Se o projeto tem uma skill de marca ou um
design system, use e não invente paleta.

## Saída

Primeiro o texto slide a slide, como uma lista numerada que a pessoa lê em dez
segundos e edita antes de qualquer coisa ser gerada. Depois a **legenda**, que
num carrossel é o Trabalho B da `/ig-caption`: a legenda trabalha aqui, porque
a capa já gastou as seis palavras dela.

Passe os dois pela `/ig-human`. Só gere os arquivos depois que a pessoa
aprovar o texto.

```
CARROSSEL  ·  8 slides

1  CAPA    A CLÁUSULA DE R$ 18 MIL
           Uma linha que hoje vai em todo contrato meu.
2  EM JOGO Eu aprovei o trabalho. Nove dias depois pediram o dinheiro de volta.
3          O QUE ELA DIZ
           Pagamento na entrega, não na aprovação.
...
7  RESUMO  As quatro linhas, em ordem.
8  CTA     Comenta CONTRATO que eu te mando a cláusula inteira.

Legenda: Trabalho B, gancho na linha 1, um pedido, 3 tags.
```

Nada é enviado. A pessoa posta.
