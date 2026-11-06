---
name: ig-reel
description: >-
  Escreve um Reels de Instagram em português a partir de uma ideia crua -
  opções de gancho com base em 26 fórmulas, o roteiro falado, o texto na tela
  e uma minutagem por batida - na voz da pessoa e com nota antes de gravar.
  Use sempre que a pessoa quiser um reels, roteiro de vídeo curto, gancho,
  locução, "faz um reels sobre X", "o que eu falo nesse vídeo", "me ajuda com
  o gancho", ou quando ela vai gravar e ainda não tem a primeira frase.
---

# ig-reel

Transforma uma ideia crua num Reels que alguém assiste até o fim.

Duas ferramentas ficam nesta pasta e as duas rodam de verdade. Use. Não avalie
o gancho no olho e não chute a duração.

```bash
python3 hookscore.py ganchos.txt              # ranqueia suas opções de gancho
python3 hookscore.py --hook "uma frase"       # avalia um gancho só
python3 beats.py roteiro.txt --target 30      # minutagem antes de gravar
```

## Antes de escrever

1. Leia `~/.claude/instagram/voice.md` se existir. É o perfil de voz da
   pessoa: como ela fala na câmera, o que ela nunca diz, com quem ela fala. Se
   não existir, peça **três reels dela**, transcreva ou leia, deduza a voz e
   escreva o arquivo. Roteiro na voz errada não serve, porque ela vai ter que
   falar aquilo em voz alta.
2. Leia `hooks.json` nesta pasta. São 26 fórmulas, cada uma com modelo,
   exemplo preenchido, versão pra tela, pra que serve e como costuma ser
   estragada. Os exemplos são ilustrativos: os números neles não são dados.
3. Se a ideia está rala, não encha linguiça. Faça uma pergunta só, agrupada:
   o que aconteceu, com quem, e quanto custou ou rendeu. Um Reels precisa de
   uma coisa específica e verdadeira. Consiga antes de escrever.
4. Se `~/.claude/instagram/swipe.md` existir, leia. Quem escreve esse arquivo
   é a `/ig-viral`, e ele é a evidência da própria pessoa sobre quais fórmulas
   estão funcionando no nicho dela agora. Ele vale mais que os padrões daqui.

## O formato

Um Reels é decidido nos dois primeiros segundos e segurado nos cinco seguintes.

```
0:00 - 0:02   GANCHO      a afirmação. Frase falada e frase da tela, escritas
                          separadas. Movimento no primeiro quadro, não um rosto parado.
0:02 - 0:07   O QUE ESTÁ  por que isso importa pra quem está assistindo. Uma frase.
              EM JOGO
0:07 - ...    O CORPO     uma ideia por batida, e o quadro muda a cada batida.
ÚLTIMOS 3s    A ENTREGA   entregue o que o gancho prometeu, depois o único pedido.
ÚLTIMA FRASE  O LOOP      repita uma palavra do gancho pra o replay emendar limpo.
```

Duração: de 15 a 45 segundos é a faixa que funciona. Reels vai até 3 minutos e
quase ninguém deveria usar. Abaixo de 7 segundos, a contagem de loop infla e
nada mais.

## O processo

**1. Escolha três ganchos, não um.** Passe a ideia pelo `hooks.json`, escolha
três fórmulas que realmente servem e escreva a frase falada e a frase da tela
de cada uma. Fórmulas diferentes, não três versões da mesma.

**2. Dê nota.** Coloque as três frases faladas num arquivo, uma por linha, e
rode o `hookscore.py`. Mostre o ranking. Se o primeiro está abaixo de 50, você
ainda não tem o gancho e nenhuma edição resolve isso.

**3. Escreva o roteiro** em cima do gancho vencedor. Português falado, do jeito
que a pessoa fala de verdade: "pra", "tá", "a gente", se é assim que ela fala.
Frases curtas. Nenhuma frase que ela precisaria ensaiar.

**4. Cronometre.** Rode `beats.py roteiro.txt --target {duração}`. Corrija todo
aviso: gancho passando de 3 segundos, batida acima de 4 segundos, sequência de
batidas sem nada concreto, falta de loop. Rode de novo até ficar limpo. Se a
pessoa sabe a própria velocidade de fala, passe com `--wpm`.

**5. Humanize.** Passe o roteiro pela `/ig-human` antes de mostrar. Frase com
cara de texto escrito fica óbvia no momento em que alguém fala em voz alta.

**6. Entregue o bloco.** O roteiro num bloco de código, o texto da tela numa
lista separada com os tempos, e depois:

```
REELS PRONTO
gancho:     #3 Ninguém Te Conta, nota 81 FORTE
duração:    28,4s em 9 batidas a 150 ppm
na tela:    6 cartelas
humanizador: 4 marcas removidas, nota humana 78 APROVADO
legenda:    rode /ig-caption em seguida

Responda "sim" pra registrar, ou me diga o que mudar.
```

**7. Nunca publique.** Esta skill produz um roteiro. A pessoa grava e posta.
No "sim", acrescente em `~/.claude/instagram/log.md` a data, a fórmula de
gancho usada e a primeira frase, pra `/ig-audit` ter histórico depois.

## Texto na tela é um roteiro à parte

Escreva separado, sempre. Ele é lido antes de ser ouvido.

- **Seis palavras ou menos por cartela.** É lido a um braço de distância por
  alguém que ainda nem está ouvindo.
- **A cartela do gancho aparece no quadro 1**, não depois de um silêncio.
- **Fique dentro da área segura.** Num quadro de 1080x1920, nada acima de
  y=230 ou abaixo de y=1440, e deixe os 230 pixels da direita livres. A
  interface fica por cima de tudo fora dessa caixa: a legenda, os botões
  laterais, a faixa de áudio.
- **Nunca coloque o gancho onde a legenda fica.** É a parte de baixo do quadro
  e ela fica coberta.
- **Coloque legenda no corpo do vídeo.** A maioria assiste sem som primeiro.

## Regras que fazem diferença

- **Uma ideia por Reels.** Se o roteiro tem duas, são dois Reels. Fale isso.
- **Número em vez de adjetivo.** "R$ 4.200" ganha de "muito dinheiro". Se a
  pessoa não deu o número, pergunte em vez de escrever em volta do buraco.
- **Corte a introdução.** Sem "oi gente", sem "nesse vídeo", sem nome, sem
  vinheta. O vídeo começa na frase que normalmente apareceria no sexto segundo.
- **Mude o quadro a cada batida.** Plano parado por 8 segundos é onde a pessoa
  sai, e o `beats.py` vai apontar.
- **Um pedido no fim.** Comentar uma palavra, salvar ou seguir. Um.
- **Nunca invente.** Nenhuma métrica, cliente, faturamento ou resultado
  inventado com o nome da pessoa, nem como exemplo. Se precisa de um número e
  ele não foi dado, deixe `{{seu número}}` no roteiro e avise.
- **Não escreva roteiro em cima de um áudio em alta que a pessoa não pode
  usar.** Se a ideia precisa da voz dela, diga.

## Exemplo

```
/ig-reel a gente reduziu o tempo de proposta de 5 horas pra 20 minutos com um modelo
```

```
GANCHOS  (notas do hookscore.py)
  81  FORTE  #1  Confissão de Custo "Eu cobrava quatro horas por semana só de formatação. Por dois anos."
                                    na tela: 2 ANOS JOGADOS FORA
  55  OK     #5  Colapso de Tempo   "Proposta me tomava cinco horas. Hoje leva vinte minutos."
                                    na tela: 5 HORAS -> 20 MIN
  37  FRACO  #9  Pode Roubar        "Rouba o modelo de proposta que fez isso."
                                    na tela: PODE ROUBAR

Gravando o #1: tem custo, tem número, e quem passa vergonha é você.
O #5 perde em TENSÃO, nada está em jogo na frase. Se você prefere o #5,
coloque o custo nele ("cinco horas que eu não cobrava de ninguém").
O #9 não tem nada concreto: "isso" não é número.
```
