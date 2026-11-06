#!/usr/bin/env python3
"""
beats.py - transforma um roteiro de Reel numa minutagem por batida antes de
você gravar.

Versão em português do Brasil, adaptada de beats.py do projeto
instagram-agent-skill (Jake Schincariol, licença MIT).

Estima quanto tempo cada linha leva pra ser falada, empilha tudo em
minutagem e aponta as quatro coisas que matam um Reel na edição: gancho que
passa da marca de três segundos, batida longa o bastante pra pessoa ir
embora, sequência de linhas sem nada concreto e duração total diferente do
que você disse que ia fazer.

Os tempos são estimativa por contagem de palavras numa velocidade em palavras
por minuto. Servem pra planejar a edição, não substituem gravar. O padrão
aqui é 150 ppm, um ponto de partida pra português falado, que tem palavras
mais longas que o inglês. Cronometre você lendo um roteiro em voz alta e use
--wpm com o seu número: a maioria das pessoas fica entre 130 e 190.

Uso
  python3 beats.py roteiro.txt
  python3 beats.py roteiro.txt --target 30
  python3 beats.py roteiro.txt --wpm 170 --target 45
  pbpaste | python3 beats.py -
  python3 beats.py roteiro.txt --json
"""

import argparse
import json
import re
import sys
import unicodedata

NUM = r"\d(?:[.,]?\d)*"
WORD_RE = re.compile(r"R\$\s?" + NUM + r"%?|" + NUM + r"%?|[^\W\d_][\w'’-]*")
SENT_RE = re.compile(r"[^.!?]+[.!?]*")
UPPER = "A-ZÁÂÃÀÉÊÍÓÔÕÚÜÇ"
LOWER = "a-záâãàéêíóôõúüç"
CONCRETE_RE = re.compile(rf"R\$\s?\d|\b\d[\d.,]*\b|(?<!^)\b[{UPPER}][{LOWER}]{{2,}}\b",
                         re.MULTILINE)


def fold(text):
    nfd = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


# Número dito em voz alta também é concreto: "vinte mil" vale tanto quanto "20.000".
SPOKEN_NUMBERS = {fold(w) for w in (
    "zero", "dois", "duas", "três", "quatro", "cinco", "seis", "sete", "oito",
    "nove", "dez", "onze", "doze", "quinze", "vinte", "trinta", "quarenta",
    "cinquenta", "sessenta", "setenta", "oitenta", "noventa", "cem", "cento",
    "duzentos", "trezentos", "quinhentos", "mil", "milhão", "milhões", "bilhão",
    "reais", "metade", "dobro", "triplo",
)}
STOPWORDS = {fold(w) for w in (
    "o", "a", "os", "as", "um", "uma", "uns", "umas", "e", "ou", "mas", "se",
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas", "por",
    "pelo", "pela", "pra", "pro", "para", "com", "que", "isso", "isto", "esse",
    "essa", "este", "esta", "aquele", "aquela", "ele", "ela", "eles", "elas",
    "eu", "me", "meu", "minha", "você", "vc", "seu", "sua", "te", "nós",
    "gente", "é", "são", "foi", "era", "ser", "estar", "tá", "está", "não",
    "sim", "só", "já", "mais", "muito", "tem", "ter", "faz", "fazer", "vai",
    "vou", "ao", "aos", "à", "às", "como", "quando", "onde", "porque", "também",
    "então", "aí", "lá", "aqui", "todo", "toda", "tudo", "lhe",
)}

HOOK_WINDOW = 3.0        # segundos. Depois disso, o polegar já decidiu.
MAX_BEAT = 4.0           # segundos numa ideia só sem nada mudar na tela.
ABSTRACT_RUN = 3         # batidas seguidas sem nada que dê pra conferir.


def words(text):
    return WORD_RE.findall(text)


def concrete(text):
    spoken = [w for w in words(text) if fold(w) in SPOKEN_NUMBERS]
    return len(CONCRETE_RE.findall(text)) + len(spoken)


def tc(seconds):
    m, s = divmod(seconds, 60)
    return f"{int(m)}:{s:04.1f}"


def split_beats(raw, wps):
    """Uma linha é uma batida, a não ser que a linha seja longa demais pra ser uma."""
    beats = []
    for line in [l.strip() for l in raw.splitlines()]:
        if not line:
            continue
        if len(words(line)) / wps <= MAX_BEAT * 1.5:
            beats.append(line)
            continue
        # Parágrafo longo: quebra no fim das frases pra minutagem fazer sentido.
        parts = [p.strip() for p in SENT_RE.findall(line) if p.strip()]
        buf = ""
        for part in parts:
            candidate = (buf + " " + part).strip()
            if buf and len(words(candidate)) / wps > MAX_BEAT:
                beats.append(buf)
                buf = part
            else:
                buf = candidate
        if buf:
            beats.append(buf)
    return beats


def analyse(raw, wpm=150, target=None):
    wps = wpm / 60.0
    beats = split_beats(raw, wps)
    if not beats:
        return None

    rows, clock = [], 0.0
    for i, text in enumerate(beats):
        n = len(words(text))
        dur = n / wps
        rows.append({
            "n": i + 1,
            "start": round(clock, 2),
            "dur": round(dur, 2),
            "words": n,
            "text": text,
            "concrete": concrete(text),
            "label": "",
            "flags": [],
        })
        clock += dur
    total = clock

    # Marca as posições estruturais em torno das quais um Reel é montado.
    for r in rows:
        if r["n"] == 1 or r["start"] + r["dur"] <= HOOK_WINDOW:
            r["label"] = "GANCHO"
    rows[-1]["label"] = "CTA" if rows[-1]["label"] != "GANCHO" else "GANCHO/CTA"
    half = total / 2
    for r in rows:
        if not r["label"] and r["start"] <= half < r["start"] + r["dur"]:
            r["label"] = "MEIO"

    notes = []
    if rows[0]["dur"] > HOOK_WINDOW:
        rows[0]["flags"].append(f"gancho dura {rows[0]['dur']:.1f}s, passa da marca de {HOOK_WINDOW:.0f}s")
        notes.append(f"A batida 1 leva {rows[0]['dur']:.1f}s pra ser falada. Corte pra "
                     f"{int(HOOK_WINDOW * wps)} palavras ou menos, ou o gancho chega depois "
                     "que a decisão já foi tomada.")
    if rows[0]["concrete"] == 0:
        notes.append("A batida 1 não tem número nem nome. Gancho sem nada que dê pra "
                     "conferir é o que a pessoa passa direto.")

    for r in rows:
        if r["dur"] > MAX_BEAT:
            r["flags"].append(f"{r['dur']:.1f}s numa batida só")
    long_beats = [r["n"] for r in rows if r["dur"] > MAX_BEAT]
    if long_beats:
        notes.append(f"Batida(s) {', '.join(map(str, long_beats))} passam de {MAX_BEAT:.0f}s. "
                     "Divida a linha ou mude o que está na tela no meio dela. "
                     "Quadro parado é onde a pessoa sai.")

    run, start = 0, None
    for r in rows:
        if r["concrete"] == 0:
            run += 1
            start = start if start is not None else r["n"]
            if run == ABSTRACT_RUN:
                notes.append(f"As batidas {start} a {r['n']} não têm nada concreto. "
                             "Coloque um número, um nome ou um preço em uma delas.")
        else:
            run, start = 0, None

    # A última linha devolve a pessoa pra primeira?
    first = {fold(w): w for w in words(rows[0]["text"]) if fold(w) not in STOPWORDS}
    last = {fold(w) for w in words(rows[-1]["text"]) if fold(w) not in STOPWORDS}
    loop = sorted(first[k] for k in first.keys() & last)
    if loop:
        notes.append(f"Tem loop: a última batida repete \"{', '.join(loop[:3])}\" do gancho. "
                     "Segunda visualização é alcance de graça.")
    else:
        notes.append("Sem loop. A última batida não repete nenhuma palavra do gancho, então "
                     "o vídeo termina reto. Ecoar uma palavra da batida 1 é o replay mais "
                     "barato que existe.")

    if target:
        delta = total - target
        if abs(delta) <= target * 0.1:
            notes.append(f"Duração dentro do alvo ({total:.1f}s pra {target:g}s).")
        elif delta > 0:
            notes.append(f"{delta:.1f}s acima do alvo. Corte umas {int(delta * wps)} palavras.")
        else:
            notes.append(f"{-delta:.1f}s abaixo do alvo. Acrescente {int(-delta * wps)} palavras "
                         "ou grave mais curto. Mais curto geralmente é o certo.")

    return {
        "wpm": wpm, "target": target,
        "total_seconds": round(total, 2),
        "total_words": sum(r["words"] for r in rows),
        "beats": rows,
        "notes": notes,
    }


def render(a, out=sys.stdout):
    head = (f"MINUTAGEM  ·  {a['total_words']} palavras  ·  ~{a['total_seconds']:.1f}s "
            f"a {a['wpm']:g} ppm" + (f"  ·  alvo {a['target']:g}s" if a["target"] else ""))
    print("\n" + head, file=out)
    print("=" * max(len(head), 74), file=out)
    for r in a["beats"]:
        label = f"{r['label']:<11}" if r["label"] else " " * 11
        print(f"  {tc(r['start'])}  {r['dur']:4.1f}s  {label}{r['text']}", file=out)
        for f in r["flags"]:
            print(f"  {'':>6}  {'':>5}  {'':<11}^ {f}", file=out)
    print("-" * max(len(head), 74), file=out)
    for n in a["notes"]:
        print(f"  - {n}", file=out)
    print("", file=out)


def main():
    ap = argparse.ArgumentParser(description="Cronometra um roteiro de Reel em batidas.")
    ap.add_argument("input", nargs="?", default="-", help="arquivo do roteiro, ou - pra stdin")
    ap.add_argument("--wpm", type=float, default=150,
                    help="velocidade de fala em palavras por minuto (padrão 150)")
    ap.add_argument("--target", type=float, help="duração alvo em segundos")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    a = analyse(raw, wpm=args.wpm, target=args.target)
    if not a:
        print("roteiro vazio", file=sys.stderr)
        sys.exit(2)
    if args.json:
        print(json.dumps(a, indent=2, ensure_ascii=False))
    else:
        render(a)
    sys.exit(0)


if __name__ == "__main__":
    main()
