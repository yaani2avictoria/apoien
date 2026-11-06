---
name: ig-comment
description: >-
  Escreve comentários em português nos posts e reels de outras pessoas que
  soam como alguém com opinião, não como robô. Use quando a pessoa colar um
  post ou reels e quiser um comentário, disser "comenta nisso", "interage com
  isso", "o que eu falo aqui", ou quiser um lote pra rodada diária de
  interação.
---

# ig-comment

Comentar é o tempo de maior alavancagem no Instagram, e o mais fácil de fazer
mal. Um comentário no topo de um reels com 40 mil views é visto por mais gente
que a maioria dos posts das próprias contas, e é o único lugar onde um
desconhecido pode tocar e ir direto pro perfil.

Um comentário genérico é pior que nenhum. Ele custa um toque que não leva a
lugar nenhum e marca a conta como conta de grupo de engajamento pra única
pessoa cuja opinião importava, que é quem criou o post.

## Entrada

A pessoa cola o texto do post ou do reels, ou um print, com o nome da conta.
Se ela mandar um link que você não consegue abrir, peça pra colar. Não use
ferramenta de navegador pra raspar o feed e não poste nada.

## Os nove tipos de comentário

Escolha pelo que o post realmente é. Nunca vá no tipo 1 por padrão.

| # | tipo | quando | formato |
| --- | --- | --- | --- |
| 1 | **Acrescentar um dado** | o post afirma algo que você consegue sustentar com número | "Aqui foi igual: 40% dos..." |
| 2 | **Acrescentar o caso que faltou** | o post está certo mas incompleto | "Isso vale até {condição}." |
| 3 | **Discordar com respeito** | você acha de verdade que está errado | diga primeiro onde concorda, depois onde diverge |
| 4 | **Estender uma frase** | uma frase do post é a boa | cite e construa em cima |
| 5 | **Fazer a pergunta de verdade** | o post pulou a parte difícil | uma pergunta, específica |
| 6 | **O recibo** | você já fez a coisa que ela descreveu | o que aconteceu, em duas frases |
| 7 | **A correção** | tem um erro de fato | esteja certo, seja breve, seja gentil, tenha certeza |
| 8 | **O outro ângulo** | fatos certos, enquadramento errado | "Outro jeito de ler isso:" |
| 9 | **A frase curta** | o post não precisa de nada, você quer presença | menos de 10 palavras, tem que ser engraçada ou verdadeira |

## Regras

- **De uma a três frases.** Comentário de Instagram é lido numa coluna estreita
  embaixo de um vídeo. Parágrafo fica escondido atrás do "mais" e ninguém toca.
- **Nunca comece com** "Que post incrível", "Amei", "Verdade", "Isso 👏",
  "Precisava ler isso hoje", "Conteúdo de valor", "Arrasou" ou o primeiro nome
  de quem postou com ponto de exclamação. São todos invisíveis.
- **Nada de comentário só com emoji**, e nada de emoji como primeiro caractere.
- **Nunca repita o reels.** Todo mundo que está vendo acabou de assistir.
- **Uma ideia.** Comentário com dois pontos parece sequestro do post.
- **Diga a coisa específica.** Se o comentário caberia embaixo de qualquer post
  sobre o tema, ele não é comentário, é ruído.
- **Nunca venda.** Nem a oferta, nem o link, nem "dá uma olhada no meu
  perfil". É o jeito mais rápido de ser bloqueado justamente pela pessoa que
  você queria alcançar.
- **Cedo importa mais aqui que em qualquer lugar.** Um comentário na primeira
  hora de um reels que depois viaja vai junto com ele.

## Saída

Dê **duas opções de tipos diferentes**, com rótulo, mais uma linha dizendo qual
você postaria e por quê. Passe as duas pela `/ig-human` antes: comentário é
curto, então um travessão ou um clichê pesa proporcionalmente mais que numa
legenda.

```
OPÇÕES DE COMENTÁRIO  (no reels da @conta sobre preço)

[6 · Recibo]
A gente subiu o preço 40% em março passado e perdeu exatamente um cliente,
que era o que ocupava metade da caixa de entrada. Levou oito meses pra eu
parar de ter medo disso.

[3 · Discordar com respeito]
Concordo com a ancoragem. O que eu questionaria é fazer isso no meio do
projeto. A gente tentou e perdeu uma renovação que estava tudo certo.

Poste a primeira. Ela concede alguma coisa e tem um número.
```

## Modo lote

Pra uma rodada de interação, peça de 5 a 10 posts colados numa mensagem só,
devolva um comentário pra cada num bloco único, e mantenha uma anotação em
`~/.claude/instagram/log.md` de quem já recebeu comentário nesta semana.
Comentar nas mesmas três contas todo dia é visível e parece exatamente o que é.

## Nunca

Não poste automaticamente, não automatize comentários e não use ferramenta de
navegador pra publicar em nome da pessoa. Interação automatizada viola os
Termos de Uso do Instagram e bloqueia contas. Esta skill escreve o comentário.
A pessoa posta.
