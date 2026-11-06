# Instagram com Claude, em português do Brasil

Treze skills do Claude para cuidar de uma conta de Instagram, adaptadas para
português do Brasil. Grátis, licença MIT, sem cadastro, sem chave de API, nada
pra conectar.

É uma adaptação do [instagram-agent-skill](https://github.com/Jakeschincariol/instagram-agent-skill),
de Jake Schincariol. As instruções foram traduzidas e adaptadas ao contexto
brasileiro, e os scripts em Python foram reescritos para entender português:
acentos, R$, números escritos como "18 mil" ou "1,2 mi", gírias e clichês
daqui.

**Nada é postado sem você dizer sim.** Essas skills escrevem. Quem posta é você.

## Instalação

### Opção 1: Claude Code (recomendada)

No terminal:

```bash
git clone https://github.com/yaani2avictoria/apoien.git
mkdir -p ~/.claude/skills ~/.claude/instagram
cp -r apoien/instagram-agent-ptbr/skills/ig-* ~/.claude/skills/
cp apoien/instagram-agent-ptbr/templates/voice.md ~/.claude/instagram/voice.md
```

Depois abra o Claude Code e digite `/ig-reel` pra testar.

Se você já tinha instalado a versão original em inglês, esses comandos
substituem ela, porque as skills têm o mesmo nome (`ig-reel`, `ig-caption`...).

Se o repositório `apoien` for privado, o `git clone` só funciona com uma conta
do GitHub que tenha acesso a ele.

### Opção 2: como plugin do Claude Code

Dentro do Claude Code:

```
/plugin marketplace add yaani2avictoria/apoien
/plugin install instagram-agent-ptbr@apoien
```

### Opção 3: sem Claude Code

Abra o `SKILL.md` da skill que quiser (por exemplo `skills/ig-caption/SKILL.md`),
copie tudo e cole no começo de uma conversa com o Claude. Funciona, mas sem os
scripts em Python, que são a maior parte do valor da `/ig-reel` e da `/ig-human`.

### Depois de instalar: o seu voice.md

Gaste dez minutos no `~/.claude/instagram/voice.md`. Preencha à mão, ou mande
três reels ou legendas suas pro Claude e diga "escreve meu voice.md a partir
destes". Todas as skills leem esse arquivo. Aqui ele importa mais do que em
qualquer outra rede, porque você vai falar as palavras em voz alta.

## As treze skills

| comando | o que faz |
| --- | --- |
| `/ig-reel` | Uma ideia vira um Reels. Três ganchos a partir de [26 fórmulas](skills/ig-reel/hooks.json), com nota, depois o roteiro, o texto da tela e a minutagem. |
| `/ig-viral` | Vai atrás do que está funcionando no seu nicho, ranqueia pelo múltiplo sobre a mediana da própria conta, dá nome à fórmula e escreve o arquivo de referências. |
| `/ig-caption` | A legenda, revisada. Mostra os 125 caracteres que o feed mostra antes do "... mais". |
| `/ig-carousel` | Carrossel. A capa que faz arrastar, o texto de cada slide e os arquivos 1080x1350. |
| `/ig-story` | A sequência de stories do dia, qual figurinha faz qual trabalho, e o funil pro direct que começa com a pessoa se mexendo primeiro. |
| `/ig-profile` | Dá nota ao seu perfil com uma [rubrica de 12 itens](skills/ig-profile/rubric.json), de 0 a 100, e reescreve na ordem do que mais perde ponto. |
| `/ig-plan` | A semana. O que postar, em qual formato, quando, e as 10 contas com quem interagir. |
| `/ig-human` | O humanizador. Dois scripts que rodam de verdade. Veja abaixo. |
| `/ig-comment` | Comentários nos posts dos outros. Nove tipos, escolhidos pelo que o post é. Nunca "🔥🔥🔥". |
| `/ig-reply` | Os comentários do seu post. Separa em palavra-chave / lead / substância / pergunta / apoio / ruído, e responde nessa ordem. |
| `/ig-dm` | A entrega da palavra-chave, a primeira mensagem, a proposta de collab e os dois follow-ups. Dois. |
| `/ig-repurpose` | Um vídeo, podcast ou newsletter vira uma semana de reels e carrosséis que se sustentam sozinhos. |
| `/ig-audit` | Pós-morte do que você já postou. Ranqueia por múltiplo e por envios por alcance, não por views. |

## As ferramentas que rodam de verdade

Só biblioteca padrão do Python 3, sem dependências, sem internet, nada é
enviado pra lugar nenhum. Rodam na sua máquina, no seu texto.

```bash
python3 skills/ig-reel/hookscore.py ganchos.txt            # ranqueia ganchos
python3 skills/ig-reel/beats.py roteiro.txt --target 30    # minutagem do roteiro
python3 skills/ig-caption/caption.py legenda.txt --keywords "contrato de cliente"
python3 skills/ig-human/humanize.py rascunho.txt --report  # limpa e mostra o que mudou
python3 skills/ig-human/detect.py antes.txt depois.txt     # nota antes e depois
python3 skills/ig-viral/swipe.py coletados.tsv --out ~/.claude/instagram/swipe.md
```

Exemplo real do `hookscore.py` nesta versão:

```
RANKING DE GANCHOS
==============================================================================
->  81.4 FORTE  Ninguém te conta que seus primeiros 30 reels são pra flopar
    81.4 FORTE  Perdi R$ 18.000 por causa de um contrato sem uma cláusula.
    80.2 FORTE  Para de postar três vezes por dia.
    54.4 OK     Para de rolar se você quer crescer no Instagram em 2026 🔥
        eliminatório: Abre com "para de rolar". Pedir atenção prova que você ainda não conquistou.
        eliminatório: Emoji no gancho. Texto na tela no tamanho de gancho tem espaço pra palavras ou pra emoji, não pros dois.
     9.6 FRACO  Oi gente, hoje eu queria falar sobre estratégia de conteúdo
        eliminatório: Saudação. Ninguém abriu o feed pra ser cumprimentado.
```

E do humanizador, numa legenda escrita pra ser a pior possível (travessão,
"alavancar", "sua jornada", "o algoritmo ama", "nesse vídeo eu vou te
mostrar", "me segue pra mais"):

```
29.0 SINALIZADO  ->  56.7 REVISAR   (+27.7)
```

O resto do caminho até APROVADO é reescrever à mão as estruturas que o script
aponta ("não é só X, é Y", lista de emoji, parede de hashtags), que é
exatamente o que a `/ig-human` manda o Claude fazer.

## O que mudou em relação ao original

- **Instruções em português**, com exemplos em R$, horário de Brasília,
  "direct", "link na bio", gírias e clichês brasileiros.
- **Avaliador de ganchos** com listas de palavras em português: números por
  extenso ("vinte mil"), valores em R$, palavras de tensão ("perdi", "nunca",
  "ninguém"), aberturas fracas ("oi gente", "então", "hoje eu vim falar"),
  saudações ("fala galera", "salve"), e reconhecimento de primeira pessoa
  sem pronome ("Perdi", "Cobrei"), já que o português esconde o sujeito.
- **26 fórmulas de gancho** reescritas em português, com padrões que
  reconhecem fala brasileira. Cada exemplo é reconhecido pela própria fórmula
  (há um teste pra isso). "Ditado Invertido" usa ditados daqui ("Quem espera
  nunca alcança").
- **Vocabulário de clichês** novo, com cerca de 250 termos do português
  gerado por IA e de Instagram brasileiro ("vale ressaltar", "alavancar",
  "virada de chave", "conteúdo de valor", "para de rolar", "me segue pra
  mais"), com trocas que respeitam o gênero das palavras ("o mindset" vira
  "a mentalidade", não "o mentalidade").
- **A busca ignora acento**, então "voce" e "você" contam igual.
- **Checagem de voz** troca as contrações do inglês pelas marcas de fala do
  português ("pra", "tá", "né", "a gente").
- **Legenda**: reconhece pedidos em português ("Comenta CONTRATO", "me chama
  no direct", "link na bio"), links `.com.br`, hashtags genéricas daqui
  (`#reelsbrasil`, `#segueeusigodevolta`) e lembra de identificar publicidade
  como pede o CONAR.
- **Arquivo de referências** aceita colunas em português e números como
  "48 mil", "412.000" ou "1,2 mi", e mostra os números no padrão brasileiro.
- Algumas correções de detalhes do original (por exemplo, "oi" não pega mais
  "oito"; frases que terminam em "?" agora são reconhecidas no vocabulário).

## Limitações, com honestidade

- **As notas não foram validadas com conteúdo brasileiro real.** O original
  testou o avaliador de ganchos com 74 ganchos em inglês: ele separa bem
  gancho ruim de gancho real, mas quase não prevê qual de dois ganchos bons
  vai performar melhor. Esta versão troca as listas de palavras e ajusta
  alguns limites, mas ninguém mediu ainda com ganchos e legendas brasileiras.
  Trate as notas como orientação. Se você testar e achar outra coisa, vale
  ajustar.
- **A velocidade de fala padrão é 150 palavras por minuto**, um ponto de
  partida pra português. Cronometre você lendo um roteiro e use `--wpm`.
- **Essas skills não postam no Instagram.** Automação de postagem, comentário,
  curtida ou direct fora das ferramentas oficiais viola os Termos de Uso do
  Instagram e bloqueia contas. Toda skill termina com um bloco pronto pra
  copiar, e você posta.
- **A `/ig-viral` lê, não raspa.** Poucas contas, em velocidade de gente, com
  você no seu próprio navegador. Nunca pede senha.
- **As cinco checagens do humanizador são heurísticas locais**, não GPTZero,
  Originality ou similares. Ninguém pode vender "indetectável" com honestidade.
- **Nada aqui inventa dado.** Se um rascunho precisa de um número que você não
  deu, ele volta com `{{seu número}}` e um aviso.
- **Regra de plataforma muda.** O limite de 5 hashtags e outros números vêm
  do original e podem ter mudado. Se algo aqui contradiz o que o Instagram
  faz quando você lê, o Instagram está certo.

## Testes

Da raiz do repositório:

```bash
python3 -m unittest discover -s instagram-agent-ptbr/tests -v
```

## Arquivos

```
skills/ig-reel/hooks.json          26 fórmulas de gancho em português, com regex de reconhecimento
skills/ig-reel/hookscore.py        o painel de cinco propriedades do gancho
skills/ig-reel/beats.py            roteiro vira minutagem
skills/ig-caption/caption.py       a prévia do corte do feed e a revisão da legenda
skills/ig-human/slop.json          o vocabulário: ~250 termos, 18 invisíveis, 18 estruturas
skills/ig-human/humanize.py        as três passadas de limpeza
skills/ig-human/detect.py          o painel de cinco checagens
skills/ig-viral/swipe.py           ranking por múltiplo e classificação de fórmula
skills/ig-profile/rubric.json      a nota de 100 pontos do perfil
templates/voice.md                 seu perfil de voz. Preencha primeiro.
tests/test_ferramentas.py          testes dos scripts
```

## Créditos e licença

Original: [instagram-agent-skill](https://github.com/Jakeschincariol/instagram-agent-skill),
de Jake Schincariol ([opusjake.ai](https://opusjake.ai)), licença MIT.

Esta adaptação também é MIT. Veja [LICENSE](LICENSE), que mantém o aviso de
copyright original.
