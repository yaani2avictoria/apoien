#!/usr/bin/env python3
"""
caption.py - revisa uma legenda de Instagram e mostra exatamente o que o feed
mostra antes do "... mais".

Versão em português do Brasil, adaptada de caption.py do projeto
instagram-agent-skill (Jake Schincariol, licença MIT).

O Instagram mostra uns 125 caracteres da legenda no feed e esconde o resto
atrás de um toque. Quase toda legenda que falha, falha ali: o gancho está na
terceira frase, ou a primeira linha é um "oi gente", ou tudo começa com uma
hashtag. Este script imprime essa janela visível dentro de uma caixa, pra você
ler como lê um desconhecido rolando o feed, e depois confere as coisas que vale
a pena conferir.

O corte de 125 caracteres é uma aproximação. O número real muda com o
aparelho, o tamanho da fonte e onde caem as quebras de linha, e é por isso que
você quer uma margem e não uma legenda calculada pra terminar no 125. Mude
com --truncate se quiser testar um corte mais apertado.

Uso
  python3 caption.py legenda.txt
  python3 caption.py legenda.txt --keywords "proposta comercial,contrato de cliente"
  pbpaste | python3 caption.py -
  python3 caption.py legenda.txt --json
"""

import argparse
import json
import re
import sys
import textwrap
import unicodedata

LIMIT = 2200             # Limite máximo de caracteres de legenda do Instagram.
TRUNCATE = 125           # Mais ou menos onde o feed corta pro "... mais".
HASHTAG_LIMIT = 5        # Limite por post ou reels desde 18/12/2025, era 30.
                         # Anunciado pela conta @Creators, recomendando
                         # "usar menos (até 5) hashtags mais específicas, em vez
                         # de muitas genéricas". Confira se ainda vale.

HASHTAG_RE = re.compile(r"(?:^|\s)(#\w+)")
MENTION_RE = re.compile(r"(?:^|\s)(@[\w.]+)")
LINK_RE = re.compile(r"https?://\S+|\bwww\.\S+"
                     r"|\b[a-z0-9-]+\.(?:com\.br|net\.br|org\.br|com|br|co|io|net|org|ai|app|me|link)\b(?:/\S*)?",
                     re.IGNORECASE)
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF☀-➿←-⇿️]")
UPPER = "A-ZÁÂÃÀÉÊÍÓÔÕÚÜÇ"
LOWER = "a-záâãàéêíóôõúüç"
CONCRETE_RE = re.compile(
    rf"R\$\s?\d|\b\d[\d.,]*\b|(?<![.!?]\s)(?<!^)\b[{UPPER}][{LOWER}]{{2,}}\b"
    r"|\b(?:mil|milh[ãa]o|milh[õo]es|reais)\b", re.MULTILINE)

ASKS = [
    (re.compile(r"\b(?i:comenta|comente|comentem|escreve|escreva)\s+(?i:a palavra\s+|aqui\s+|s[óo]\s+)?[\"“]?"
                rf"[{UPPER}0-9]{{2,}}\b"), "comentar uma palavra-chave"),
    (re.compile(r"(?i)\bme (?:chama|chame|manda|mande|envia|envie)\b"
                r"|\b(?:chama|chame|manda|mande) (?:no|na|um|uma) (?:direct|dm|inbox|mensagem|direto)\b"),
     "me chamar no direct"),
    (re.compile(r"(?i)\b(?:salva|salve|salvem) (?:esse|este|essa|esta|isso|o post|o v[íi]deo|pra|para)\b"),
     "salvar"),
    (re.compile(r"(?i)\b(?:compartilha|compartilhe|compartilhem)\b"
                r"|\b(?:manda|mande|envia|envie) (?:esse|este|isso) (?:pra|para)\b"
                r"|\b(?:manda|mande|envia|envie) (?:pra|para) (?:algu[ée]m|quem)\b"), "compartilhar"),
    (re.compile(r"(?i)\bme (?:segue|siga|sigam)\b|\b(?:segue|siga|sigam) (?:o perfil|a gente|pra mais|para mais|@)"),
     "seguir"),
    (re.compile(r"(?i)\blink (?:na|da|est[áa] na|t[áa] na) (?:minha )?bio\b|\blink no (?:meu )?perfil\b"),
     "link na bio"),
    (re.compile(r"(?i)\b(?:arrasta|arraste|desliza|deslize|passa|passe) (?:pro|para o|pra) lado\b"
                r"|\b(?:arrasta|arraste|desliza|deslize) (?:pra|para a?) (?:esquerda|direita)\b"),
     "arrastar pro lado"),
    (re.compile(r"(?i)\bme (?:conta|conte|diz|diga|fala|fale)\b|\bqual (?:voc[êe]|vc) (?:escolheria|prefere|usaria)\b"
                r"|\bo que (?:voc[êe]|vc) faria\b|\bqual d[oa]s (?:dois|duas|tr[êe]s)\b"),
     "responder uma pergunta"),
]

FILLER_TAGS = {"#viral", "#fyp", "#fy", "#explore", "#explorar", "#explorepage", "#foryou",
               "#foryoupage", "#paravoce", "#pravoce", "#trending", "#instagood", "#love",
               "#follow", "#like4like", "#reels", "#reelsinstagram", "#viralreels", "#instadaily",
               "#instabrasil", "#brasil", "#reelsbrasil", "#viralizar", "#seguidores",
               "#seguidoresbrasil", "#sigam", "#segueeusigodevolta", "#sigoevolta", "#curtir",
               "#curta", "#tbt"}


def fold(text):
    nfd = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def visible_window(text, cut):
    """O que o feed mostra. O Instagram corta no meio da palavra, então aqui também."""
    flat = text.strip()
    return flat if len(flat) <= cut else flat[:cut]


def render_box(window, truncated, out=sys.stdout, width=52):
    print("\n  O QUE O FEED MOSTRA", file=out)
    print("  +" + "-" * (width + 2) + "+", file=out)
    lines = []
    for raw in window.split("\n"):
        lines.extend(textwrap.wrap(raw, width) or [""])
    for line in lines[:8]:
        print(f"  | {line:<{width}} |", file=out)
    tail = "... mais" if truncated else "(a legenda inteira cabe)"
    print("  +" + "-" * (width + 2 - len(tail) - 2) + f" {tail} " + "+", file=out)


def analyse(text, cut=TRUNCATE, keywords=None):
    text = text.rstrip()
    stripped = text.strip()
    chars = len(stripped)
    lines = [l for l in stripped.split("\n")]
    first_line = lines[0].strip() if lines else ""
    tags = HASHTAG_RE.findall(stripped)
    mentions = MENTION_RE.findall(stripped)
    links = LINK_RE.findall(stripped)
    emoji = EMOJI_RE.findall(stripped)
    window = visible_window(stripped, cut)
    truncated = chars > cut
    asks = [name for pattern, name in ASKS if pattern.search(stripped)]
    filler = [t for t in tags if fold(t) in FILLER_TAGS]
    keywords = [k.strip() for k in (keywords or []) if k.strip()]

    checks = []

    def add(name, status, detail):
        checks.append({"check": name, "status": status, "detail": detail})

    add("TAMANHO", "FALHA" if chars > LIMIT else "OK",
        f"{chars} / {LIMIT} caracteres" + (f", {chars - LIMIT} acima do limite"
                                           if chars > LIMIT else ""))

    if not first_line:
        add("PRIMEIRA LINHA", "FALHA", "a legenda começa com uma linha em branco")
    elif first_line.startswith("#") or first_line.startswith("@"):
        add("PRIMEIRA LINHA", "FALHA",
            "começa com hashtag ou menção, na única posição que merece uma frase")
    elif re.match(r"(?i)^\s*(?:oi|ol[áa]|e a[íi]|bom dia|boa tarde|boa noite|fala,? (?:galera|pessoal|gente))\b",
                  first_line):
        add("PRIMEIRA LINHA", "AVISO", "começa com saudação, gastando a janela visível com nada")
    elif len(first_line) > cut:
        add("PRIMEIRA LINHA", "AVISO",
            f"{len(first_line)} caracteres, então é cortada no {cut} no meio do pensamento. "
            "Tudo bem se o corte é um suspense, ruim se é uma oração subordinada")
    else:
        add("PRIMEIRA LINHA", "OK", f"{len(first_line)} caracteres, aparece inteira")

    add("GANCHO CONCRETO", "OK" if CONCRETE_RE.search(window) else "AVISO",
        f"{len(CONCRETE_RE.findall(window))} número(s) ou nome(s) na janela visível"
        + ("" if CONCRETE_RE.search(window) else " - nada que dê pra conferir antes do toque"))

    if len(tags) > HASHTAG_LIMIT:
        add("HASHTAGS", "FALHA", f"{len(tags)} tags, acima do limite de {HASHTAG_LIMIT} do Instagram. "
                                 "Tags depois da quinta não contam e o bloco parece antigo")
    elif len(tags) == HASHTAG_LIMIT and filler:
        add("HASHTAGS", "AVISO", f"{len(tags)} tags, no limite, e "
                                 f"{len(filler)} delas genéricas. Use as cinco em temas")
    elif filler:
        add("HASHTAGS", "AVISO", f"{len(tags)} tags, {len(filler)} delas genéricas "
                                 f"({', '.join(filler[:3])}). Essas não descrevem nada")
    else:
        add("HASHTAGS", "OK", f"{len(tags)} tag(s)" + (f": {' '.join(tags)}" if tags else ""))

    if not tags:
        add("POSIÇÃO DAS TAGS", "OK", "sem tags pra posicionar")
    elif any(re.search(r"(?:^|\s)" + re.escape(t) + r"\b", window) for t in tags):
        add("POSIÇÃO DAS TAGS", "AVISO", "tem hashtag dentro da janela visível, "
                                         "gastando espaço do feed com etiqueta")
    else:
        add("POSIÇÃO DAS TAGS", "OK", "as tags estão abaixo da dobra")

    add("LINKS", "AVISO" if links else "OK",
        f"{len(links)} link(s) na legenda, e legenda não é clicável. "
        f"Leve pra bio ou pro direct" if links else "nenhum link morto no texto")

    if len(asks) == 1:
        add("UM PEDIDO", "OK", f"uma chamada pra ação: {asks[0]}")
    elif not asks:
        add("UM PEDIDO", "AVISO", "nenhuma chamada pra ação. Decida pra que serve esse post")
    else:
        add("UM PEDIDO", "AVISO", f"{len(asks)} pedidos ({', '.join(asks)}). "
                                  "Dois pedidos é o mesmo que nenhum")

    density = len(emoji) * 100 / max(chars, 1)
    add("EMOJI", "AVISO" if density > 4 else "OK",
        f"{len(emoji)} emoji, {density:.1f} a cada 100 caracteres"
        + (" - parece enfeite" if density > 4 else ""))

    if keywords:
        low = fold(stripped)
        lwin = fold(window)
        found = [k for k in keywords if fold(k) in low]
        missing = [k for k in keywords if fold(k) not in low]
        in_window = [k for k in found if fold(k) in lwin]
        status = "OK" if not missing else ("AVISO" if found else "FALHA")
        add("TERMOS DE BUSCA", status,
            f"{len(found)}/{len(keywords)} presentes"
            + (f", {len(in_window)} na janela visível" if found else "")
            + (f". Faltando: {', '.join(missing)}" if missing else ""))

    fails = sum(1 for c in checks if c["status"] == "FALHA")
    warns = sum(1 for c in checks if c["status"] == "AVISO")
    verdict = "CORRIGIR" if fails else ("REVISAR" if warns else "PRONTA")

    return {
        "characters": chars, "limit": LIMIT, "truncate_at": cut,
        "visible": window, "truncated": truncated,
        "first_line_chars": len(first_line),
        "hashtags": tags, "mentions": mentions, "links": links,
        "emoji": len(emoji), "asks": asks,
        "checks": checks, "verdict": verdict,
    }


def render(a, out=sys.stdout):
    head = (f"REVISÃO DA LEGENDA  ·  {a['characters']} / {a['limit']} caracteres  ·  "
            f"{len(a['hashtags'])} hashtags  ·  {len(a['asks'])} pedido(s)")
    print("\n" + head, file=out)
    print("=" * max(len(head), 62), file=out)
    render_box(a["visible"], a["truncated"], out=out)
    print("", file=out)
    for c in a["checks"]:
        print(f"  {c['status']:<5} {c['check']:<17} {c['detail']}", file=out)
    print("-" * max(len(head), 62), file=out)
    print(f"  VEREDITO  {a['verdict']}\n", file=out)


def main():
    ap = argparse.ArgumentParser(description="Revisa uma legenda de Instagram.")
    ap.add_argument("input", nargs="?", default="-", help="arquivo da legenda, ou - pra stdin")
    ap.add_argument("--truncate", type=int, default=TRUNCATE,
                    help=f"caracteres mostrados antes do '... mais' (padrão {TRUNCATE})")
    ap.add_argument("--keywords", default="",
                    help="termos separados por vírgula pelos quais você quer ser encontrado")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    a = analyse(raw, cut=args.truncate, keywords=args.keywords.split(","))
    if args.json:
        print(json.dumps(a, indent=2, ensure_ascii=False))
    else:
        render(a)
    sys.exit(0 if a["verdict"] == "PRONTA" else 1)


if __name__ == "__main__":
    main()
