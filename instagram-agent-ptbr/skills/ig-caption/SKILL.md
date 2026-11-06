---
name: ig-caption
description: >-
  Escreve a legenda do Instagram em português - a linha que sobrevive ao
  corte do "... mais", o corpo, o único pedido, os termos de busca e as
  hashtags - e revisa antes de sair. Use quando a pessoa disser "escreve a
  legenda", "faz a legenda disso", "o que eu coloco na descrição", tiver um
  reels ou carrossel pronto e precisar do texto, ou perguntar sobre hashtags.
---

# ig-caption

Uma ferramenta fica nesta pasta e ela roda:

```bash
python3 caption.py legenda.txt
python3 caption.py legenda.txt --keywords "proposta comercial,preço de freelancer"
```

Ela imprime a legenda do jeito que o feed imprime: os primeiros 125
caracteres numa caixa, todo o resto atrás do toque. Leia essa caixa antes de
ler qualquer outra coisa que você escreveu.

## Primeiro, decida qual é o trabalho dessa legenda

Essa é a decisão que estraga legenda quando é pulada.

**Trabalho A: o vídeo já prendeu a pessoa.** Um Reels carrega o próprio gancho
nos dois primeiros segundos, falado e na tela. A legenda não é um segundo
gancho, e competir com o vídeo é como você perde os dois. O trabalho dela é o
pedido, o contexto que faz o pedido fazer sentido, e as palavras que as
pessoas buscam.

**Trabalho B: a legenda é o conteúdo.** Uma foto, uma imagem só, uma capa de
carrossel que abre uma curiosidade. Aqui a linha um é o gancho e funciona
exatamente como gancho de Reels: concreto, curto, e cortado num suspense, não
no meio de uma oração.

Pergunte qual dos dois você está escrevendo. Se a pessoa tem um Reels com um
gancho forte, escreva o A e diga por quê.

## O formato

```
Linha 1     125 caracteres de espaço visível. Trabalho A: o pedido, direto.
            Trabalho B: o gancho.
            Nunca saudação ("oi gente"), nunca hashtag, nunca emoji como
            primeiro caractere.
Corpo       parágrafos curtos, uma linha em branco entre eles. De dois a seis.
            É aqui que moram os termos de busca.
O pedido    um. Comentar uma palavra, salvar ou chamar no direct. Um.
Hashtags    até cinco, numa linha própria no fim, ou nenhuma.
```

O limite é 2.200 caracteres e quase nada precisa de 2.200. Uma legenda que
ganha o toque e entrega 600 caracteres ganha de uma que entrega 1.800.

## Hashtags, com honestidade

Hashtag não é mais alavanca de alcance, e a plataforma disse isso com uma
mudança de produto. **O Instagram limitou as hashtags a cinco por post em 18
de dezembro de 2025**, contra trinta antes, dizendo aos criadores que "usar
menos (até 5) hashtags mais específicas, em vez de muitas genéricas" funciona
melhor. Adam Mosseri já tinha dito em fevereiro de 2025 que hashtag não
aumenta alcance e é uma etiqueta, não uma alavanca de distribuição. (Regra de
plataforma muda; se isso não bater com o que o Instagram faz hoje, o
Instagram está certo.)

Então: até cinco, específicas, como etiqueta de tema. Se a pessoa tem um bloco
de vinte salvo no bloco de notas, esse bloco agora é peso morto e o
`caption.py` vai reprovar.

`#viral`, `#fyp`, `#explore`, `#reelsbrasil`, `#instabrasil`, `#segueeusigodevolta`
não descrevem nada. Corte.

## Termos de busca importam mais que hashtag agora

A busca do Instagram lê o texto da legenda. Então a expressão pela qual a
pessoa quer ser encontrada entra na legenda como uma pessoa digitaria, numa
frase que se lê normal. "Proposta comercial" como palavras na linha três, não
"#propostacomercial" num bloco lá embaixo.

Peça dois ou três termos desses e passe pro `caption.py` (ele ignora acento na
comparação):

```bash
python3 caption.py rascunho.txt --keywords "proposta comercial,preço de agência"
```

## Regras

- **Sem link na legenda.** Legenda não é clicável. Um link no texto é texto
  morto que diz "eu não uso esta plataforma". Bio ou direct.
- **Um pedido.** Dois pedidos é o mesmo que nenhum. O `caption.py` conta.
- **O pedido de palavra-chave precisa de uma palavra que dá pra digitar.** Uma
  palavra, sem espaço, sem emoji, e fale ela em voz alta no vídeo também.
  `Comenta CONTRATO` funciona. `Comenta "o guia do contrato"` não. Evite
  palavra com acento ou cedilha como palavra-chave (PREÇO vira PRECO, PRÊMIO
  vira PREMIO na digitação, e a automação pode não reconhecer).
- **Escreva o primeiro comentário separado** se tiver link. Avise no recibo.
- **Emoji como pontuação, não enfeite.** O `caption.py` avisa acima de 4 a
  cada 100 caracteres.
- **Texto alternativo vale 20 segundos.** Pra carrossel e foto, escreva. Ele é
  lido por leitores de tela e pelo Instagram.
- **Publicidade se identifica.** Se o post é pago, permuta ou recebido de
  marca, diga isso de forma clara (por exemplo "#publi" ou "publicidade" e o
  rótulo de Parceria Paga do Instagram), como pede o Guia de Publicidade por
  Influenciadores Digitais do CONAR. Se usar #publi, ela conta no limite de
  cinco hashtags.

## O processo

1. Decida Trabalho A ou B e diga qual.
2. Escreva o rascunho.
3. Passe pela `/ig-human`. Legenda é curta, então clichê aparece mais aqui do
   que em qualquer outro lugar do pacote.
4. Rode o `caption.py` com os termos de busca da pessoa. Corrija toda FALHA.
   Decida em voz alta sobre todo AVISO em vez de ignorar calado.
5. Entregue o bloco pronto pra copiar e depois o recibo:

```
LEGENDA PRONTA
trabalho:   A - o reels carrega o gancho
visível:    118 de 125 caracteres usados antes do corte
pedido:     um, comentar CONTRATO
hashtags:   3
busca:      "proposta comercial" na linha 3, "preço de agência" na linha 5
revisão:    PRONTA
```

Nada é postado. A pessoa cola.
