---
name: ig-viral
description: >-
  Vai atrás dos reels que estão funcionando agora no nicho da pessoa,
  ranqueia pelo quanto cada um superou a própria conta, dá nome à fórmula de
  gancho de cada um e transforma isso num arquivo de referências pra ela
  gravar. Use quando a pessoa disser "acha vídeos virais", "o que tá
  funcionando agora", "o que estão postando no meu nicho", "faz engenharia
  reversa desse perfil", "monta um arquivo de referências", "por que esse
  reels bombou", ou perguntar o que fazer em seguida sem ter evidência.
---

# ig-viral

A skill de pesquisa. Todas as outras deste pacote escrevem; esta vai olhar.
Rode uma vez por mês, não todo dia. Fórmula dura uma estação.

Uma ferramenta fica nesta pasta e ela roda:

```bash
python3 swipe.py coletados.tsv --out ~/.claude/instagram/swipe.md
```

## A ideia que faz isso valer a pena

**View bruta não é evidência.** Uma conta com dois milhões de seguidores
fazendo 400 mil views teve uma terça fraca. Uma conta com quatro mil
seguidores fazendo 400 mil views achou alguma coisa, e essa coisa dá pra copiar.

Então tudo aqui é ranqueado pelo **múltiplo**: views divididas pela mediana
recente da própria conta. Acima de 3x é sinal. Abaixo de 1,5x é o dia normal
daquela conta e não ensina nada, por maior que o número pareça.

Colete contas **até umas 10 vezes o tamanho da pessoa**. Uma fórmula que
funciona com 2 milhões de seguidores muitas vezes funciona porque a conta tem
2 milhões de seguidores.

## Passo 1: escolher as contas

Peça de 6 a 12 contas pra pessoa, ou proponha e peça aprovação:

- **4 diretas** - mesmo nicho, mesma oferta, um pouco à frente.
- **4 vizinhas** - nicho diferente, mesmo público. É daqui que os formatos são
  emprestados antes de alguém do nicho ter.
- **2 a 4 gigantes** - contas bem maiores, só pelo formato, nunca pela
  frequência ou pelo tom.

Peça também pra ela abrir a **coleção de Salvos** dela. É o acervo mais rápido
e mais relevante que existe, e já vem filtrado pelo gosto dela.

## Passo 2: ir olhar

Use a ferramenta de navegação que esta sessão realmente tem: um navegador
dentro do app, uma extensão conectada ao Chrome da própria pessoa, ou uma
ferramenta de uso do computador. Não existe API pra isso e não precisa,
porque o volume é pequeno o bastante pra ler.

**Regras que não se negociam:**

- **Nunca entre no Instagram em nome da pessoa e nunca peça senha.** Se a
  página pede login, quem já está logada é ela. Conduza o navegador dela com
  ela presente, ou peça pra ela colar.
- **Isso é leitura, não raspagem.** Dez contas, uma dúzia de reels cada, em
  velocidade de gente. Coleta automática em volume viola os Termos de Uso do
  Instagram e bloqueia contas. Não monte um robô, não use serviço de raspagem
  e não deixe isso rodando em segundo plano.
- **Copie a fórmula, nunca o vídeo.** O formato do gancho, a estrutura, a
  duração, o padrão de cortes. Não o roteiro, não a voz, não a edição. Cite a
  conta de origem em toda linha do arquivo de referências.

**O que anotar por reels**, nas palavras do criador:

| campo | observação |
| --- | --- |
| conta | o @ |
| seguidores | do perfil |
| mediana | olhe os últimos 12 reels e pegue o número de views do meio |
| views | deste reels |
| gancho | a primeira frase, falada ou na tela, literal, com erro de português e tudo |
| na tela | a primeira cartela de texto, se for diferente |
| duração | em segundos |
| cta | o que pediram no fim |

A mediana é a coluna importante. Sem ela, você volta a ranquear por número de
seguidores, que é exatamente o que esta skill existe pra evitar.

**Quando o Instagram não mostra o suficiente:** a mesma gramática de gancho
roda no YouTube Shorts, onde contagem de views e transcrição são públicas e
não precisa de login. É um segundo acervo legítimo, e o gancho falado é mais
fácil de pegar:

```bash
# contagem de views dos shorts de um canal
python3 -m yt_dlp --flat-playlist --playlist-end 40 -J \
  "https://www.youtube.com/@CANAL/shorts" > canal.json

# a primeira frase falada de um short, pelas legendas automáticas em português
python3 -m yt_dlp --skip-download --write-auto-subs --sub-langs "pt.*" \
  --sub-format json3 -o gancho "https://www.youtube.com/watch?v=ID_DO_VIDEO"
```

Pegue toda palavra da legenda com marca de tempo abaixo de 3,0 segundos. Esse é
o gancho como foi dito, não como foi escrito.

## Passo 3: ranquear

Preencha um arquivo separado por TAB com uma linha de cabeçalho e rode o
script. Ele aceita os nomes de coluna em português e números como "48 mil",
"412.000", "900k" ou "1,2 mi":

```
conta	seguidores	mediana	views	gancho
@alguem	48 mil	11.000	412.000	ninguém te conta que seus primeiros 30 reels são pra flopar
```

```bash
python3 swipe.py coletados.tsv --out ~/.claude/instagram/swipe.md
```

Ele calcula o múltiplo, dá nome à fórmula de gancho usando as mesmas 26
fórmulas com que a `/ig-reel` escreve, dá nota a cada gancho com o
`hookscore.py` e mostra o que separa o terço de cima do terço de baixo.

## Passo 4: dizer o que significa, com cuidado

Relate três coisas e nada mais:

1. **Quais fórmulas aparecem mais** no terço de cima, com contagem. Duas
   fórmulas aparecendo quatro vezes cada em seis contas é um achado. Uma
   aparecendo duas vezes não é.
2. **O que o terço de cima tem em comum na estrutura** que o terço de baixo
   não tem: tamanho do gancho, se a entrega é visual, se o primeiro quadro se
   mexe, onde fica o pedido.
3. **As linhas sem classificação.** Todo gancho que o classificador não
   conseguiu nomear é ruído ou é uma fórmula que ainda não está no
   `hooks.json`. Leia um por um. Essa é a coluna mais valiosa da saída, e é
   por isso que o script mostra a contagem. As fórmulas em português são uma
   adaptação nova: espere mais linhas sem classificação do que no original, e
   quando um padrão se repetir, acrescente no `hooks.json`.

Depois diga o tamanho da amostra e a confiança em palavras simples. Quarenta
reels em seis contas sustentam uma afirmação. Doze não, e dizer isso é a
diferença entre pesquisa e horóscopo.

## Passo 5: transformar em algo pra gravar

Pras três fórmulas do topo, escreva **a versão da pessoa**: a história dela, o
número dela, no formato que está funcionando. Passe cada uma pra `/ig-reel`
com o número da fórmula já escolhido.

Nunca devolva "faz um reels igual a esse". Devolva uma frase de gancho que ela
conseguiria falar amanhã.

## Saída

```
REFERÊNCIAS  ·  38 reels  ·  7 contas  ·  linha de base: mediana da conta

FORA DA CURVA (acima de 3x)
  38.4x  gancho 81  #3  Ninguém Te Conta   @conta_a   412.000  (mediana 10.700)
  11.2x  gancho 79  #9  Pode Roubar        @conta_c   180.000  (mediana 16.100)
  ...

O QUE ESTÁ APARECENDO MAIS
  #3 Ninguém Te Conta   x5 no terço de cima, 0 no de baixo
  #2 Comando Negativo   x4
  tamanho mediano do gancho   8 palavras em cima, 19 embaixo

SEM CLASSIFICAÇÃO (6)
  Dois desses têm o mesmo formato e ele não está no hooks.json: um gancho
  que abre lendo o comentário de outra pessoa em voz alta. Vale acrescentar.

SUA VERSÃO
  #3  "Ninguém te conta que as primeiras 20 propostas são pra perder."
  ...
```

(Os números acima ilustram o formato da saída; os seus vêm do `swipe.py`.)

Grave o arquivo em `~/.claude/instagram/swipe.md`. A `/ig-reel` e a `/ig-plan`
leem ele, e esse é o ponto: depois que isso roda uma vez, o resto do pacote
trabalha com a evidência da própria pessoa em vez dos padrões.

Nada é postado, seguido, curtido ou enviado por esta skill. Ela lê.
