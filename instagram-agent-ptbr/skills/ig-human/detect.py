#!/usr/bin/env python3
"""
detect.py - um painel de cinco checagens que dá nota pro quanto um rascunho em
português parece escrito por máquina.

Versão em português do Brasil, adaptada de detect.py do projeto
instagram-agent-skill (Jake Schincariol, licença MIT).

O que é:  cinco heurísticas locais, inspiradas nos sinais que detectores
públicos de IA medem: variação no tamanho das frases, coisas concretas,
vocabulário de clichê, marcas tipográficas e voz. Toda nota é calculada na
sua máquina, só a partir do texto. Nada é enviado pra lugar nenhum.

O que NÃO é:  GPTZero, Originality, Copyleaks, Winston ou Turnitin. Não chama
a API deles e não promete o veredito deles. Pega as coisas que todos eles
olham, e por isso corrigir essas coisas costuma mexer nos números deles
também. A única afirmação honesta é a desta linha. Os limites foram
ajustados pra português, mas ainda não validados com um corpus brasileiro.

Cada checagem devolve uma nota HUMANA de 0 a 100. Quanto maior, melhor.

Uso
  python3 detect.py rascunho.txt
  pbpaste | python3 detect.py -
  python3 detect.py rascunho.txt --json
  python3 detect.py antes.txt depois.txt      # compara dois rascunhos
"""

import argparse
import json
import os
import re
import statistics
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
LEX = os.path.join(HERE, "slop.json")

SENT_RE = re.compile(r"[^.!?\n]+[.!?]*")
WORD_RE = re.compile(r"[^\W\d_][\w'’-]*")
NUMBERS = re.compile(r"R\$\s?\d|\b\d[\d.,]*%?")
UPPER = "A-ZÁÂÃÀÉÊÍÓÔÕÚÜÇ"
LOWER = "a-záâãàéêíóôõúüç"
PROPER = re.compile(rf"(?<![.!?]\s)(?<!^)\b[{UPPER}][{LOWER}]{{2,}}\b", re.MULTILINE)
ACCENTS = {"a": "aáàâã", "e": "eéê", "i": "ií", "o": "oóôõ", "u": "uúü", "c": "cç"}


def fold(text):
    nfd = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def folded_set(*items):
    return {fold(i) for i in items}


SPOKEN_NUMBERS = folded_set(
    "dois", "duas", "três", "quatro", "cinco", "seis", "sete", "oito", "nove",
    "dez", "quinze", "vinte", "trinta", "quarenta", "cinquenta", "cem", "mil",
    "milhão", "milhões", "reais",
)
# Português escrito por gente no Instagram usa marcas de fala: "pra", "tá",
# "né", "a gente". Texto gerado quase nunca usa. Esse é o equivalente das
# contrações do inglês ("don't", "it's") na versão original.
ORALITY = folded_set(
    "pra", "pro", "pras", "pros", "tá", "tô", "tava", "tavam", "tamo", "né",
    "cê", "cês", "vc", "vcs", "daí", "aí", "bora", "vamo", "pô", "beleza",
    "num", "numa", "dum", "duma", "cadê", "tipo",
)
PRONOUNS = folded_set(
    "eu", "me", "mim", "meu", "minha", "meus", "minhas", "comigo", "nosso",
    "nossa", "nossos", "nossas", "você", "vocês", "vc", "vcs", "cê", "seu",
    "sua", "seus", "suas", "te", "ti", "contigo",
)


def clamp(n):
    return max(0.0, min(100.0, n))


def scale(value, human, machine):
    """Leva o valor pra 0-100, onde `human` -> 100 e `machine` -> 0."""
    if human == machine:
        return 50.0
    return clamp((value - machine) / (human - machine) * 100)


def sentences(text):
    return [s.strip() for s in SENT_RE.findall(text) if len(s.split()) > 2]


def words(text):
    return WORD_RE.findall(text)


def term_pattern(find):
    out = []
    for ch in find:
        base = fold(ch)
        if ch == " ":
            out.append(r"\s+")
        elif base in ACCENTS:
            out.append("[" + ACCENTS[base] + "]")
        else:
            out.append(re.escape(ch))
    lead = r"\b" if re.match(r"\w", find) else ""
    tail = r"\b" if re.search(r"\w$", find) else ""
    return re.compile(lead + "".join(out) + tail, re.IGNORECASE)


def check_burstiness(text):
    """Gente varia muito o tamanho da frase. Modelo escreve tudo igual."""
    lens = [len(s.split()) for s in sentences(text)]
    if len(lens) < 4:
        return 50.0, "curto demais pra julgar"
    mean = statistics.mean(lens)
    cv = statistics.pstdev(lens) / mean if mean else 0
    score = scale(cv, human=0.70, machine=0.22)
    return score, f"variação {cv:.2f} em {len(lens)} frases (ideal: 0.55 ou mais)"


def check_specificity(text):
    """Números, nomes e coisas concretas. Clichê é abstrato."""
    w = words(text)
    if len(w) < 25:
        return 50.0, "curto demais pra julgar"
    per100 = 100 / len(w)
    spoken = sum(1 for x in w if fold(x) in SPOKEN_NUMBERS)
    hits = len(NUMBERS.findall(text)) + len(set(PROPER.findall(text))) + spoken
    density = hits * per100
    score = scale(density, human=6.0, machine=0.5)
    return score, f"{hits} marcadores concretos, {density:.1f} a cada 100 palavras (ideal: 4 ou mais)"


def check_slop(text, lex):
    """Densidade de clichês do vocabulário."""
    w = words(text)
    if not w:
        return 50.0, "vazio"
    hits, found = 0, []
    for entry in lex["words"] + lex["phrases"]:
        n = len(term_pattern(entry["find"]).findall(text))
        if n:
            hits += n
            found.append(entry["find"])
    density = hits * 100 / len(w)
    score = scale(density, human=0.0, machine=4.0)
    detail = f"{hits} clichês, {density:.1f} a cada 100 palavras"
    if found:
        detail += " (" + ", ".join(sorted(found)[:4]) + (", ..." if len(found) > 4 else "") + ")"
    return score, detail


def check_fingerprint(text):
    """Caracteres que teclado de celular não produz sozinho."""
    invisible = sum(1 for c in text if unicodedata.category(c) == "Cf")
    em = text.count("—")
    curly = sum(text.count(c) for c in "‘’“”")
    ellip = text.count("…")
    nbsp = sum(text.count(c) for c in "   ")
    total = invisible * 4 + em * 2 + curly + ellip + nbsp
    per1k = total * 1000 / max(len(text), 1)
    score = scale(per1k, human=0.0, machine=12.0)
    detail = (f"{invisible} invisível, {em} travessão, {curly} aspa curva, "
              f"{ellip} reticências, {nbsp} espaço rígido")
    return score, detail


def check_voice(text, lex):
    """Marcas de fala, pessoa e os formatos que o modelo usa por padrão."""
    w = words(text)
    if len(w) < 25:
        return 50.0, "curto demais pra julgar"
    per100 = 100 / len(w)
    low = [fold(x) for x in w]
    orality = (sum(1 for x in low if x in ORALITY)
               + len(re.findall(r"\ba gente\b", fold(text)))) * per100
    # Português esconde o sujeito ("Perdi", "Cobrei"), então verbo em primeira
    # pessoa do passado também conta como pessoa.
    person = sum(1 for x in low if x in PRONOUNS or (len(x) >= 5 and x.endswith("ei"))) * per100
    tells = 0
    names = []
    for s in lex["structures"]:
        try:
            n = len(re.compile(s["regex"], re.MULTILINE).findall(text))
        except re.error:
            continue
        if n:
            tells += n
            names.append(s["id"])
    bullets = [len(b.split()) for b in re.findall(r"(?m)^\s*[-*•]\s+(.+)$", text)]
    uniform = (len(bullets) >= 3 and statistics.pstdev(bullets) < 1.6)
    score = (scale(orality, human=3.0, machine=0.0) * 0.35
             + scale(person, human=6.0, machine=1.0) * 0.35
             + clamp(100 - tells * 22) * 0.30)
    if uniform:
        score -= 12
        names.append("marcadores-iguais")
    detail = (f"{orality:.1f} marcas de fala, {person:.1f} marcas de pessoa "
              f"a cada 100 palavras, {tells} marca(s) de estrutura")
    if names:
        detail += " [" + ", ".join(names[:4]) + "]"
    return clamp(score), detail


CHECKS = ["RITMO", "ESPECIFICIDADE", "CLICHÊS", "MARCAS", "VOZ"]


def run(text, lex):
    results = {}
    results["RITMO"] = check_burstiness(text)
    results["ESPECIFICIDADE"] = check_specificity(text)
    results["CLICHÊS"] = check_slop(text, lex)
    results["MARCAS"] = check_fingerprint(text)
    results["VOZ"] = check_voice(text, lex)
    scores = [results[c][0] for c in CHECKS]
    # A checagem mais fraca puxa o veredito: um detector só precisa de um sinal.
    overall = statistics.mean(scores) * 0.6 + min(scores) * 0.4
    verdict = "APROVADO" if overall >= 70 and min(scores) >= 55 else (
        "REVISAR" if overall >= 50 else "SINALIZADO")
    return results, overall, verdict


def bar(score, width=24):
    filled = round(score / 100 * width)
    return "#" * filled + "." * (width - filled)


def render(results, overall, verdict, label=None, out=sys.stdout):
    title = "PAINEL DE DETECÇÃO" + (f"  -  {label}" if label else "")
    print("\n" + title, file=out)
    print("=" * max(len(title), 64), file=out)
    for name in CHECKS:
        score, detail = results[name]
        print(f"  {name:<15} {bar(score)} {score:5.1f}", file=out)
        print(f"  {'':<15} {detail}", file=out)
    print("-" * 64, file=out)
    print(f"  {'NOTA HUMANA':<15} {bar(overall)} {overall:5.1f}   {verdict}", file=out)
    if verdict != "APROVADO":
        weakest = min(CHECKS, key=lambda c: results[c][0])
        print(f"\n  Sinal mais fraco: {weakest}. Corrija esse primeiro.", file=out)
    print("", file=out)


def main():
    ap = argparse.ArgumentParser(description="Dá nota pro quanto um rascunho parece escrito por máquina.")
    ap.add_argument("input", nargs="?", default="-", help="arquivo, ou - pra stdin")
    ap.add_argument("compare", nargs="?", help="segundo arquivo, pra mostrar antes e depois")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--lexicon", default=LEX)
    args = ap.parse_args()

    lex = json.load(open(args.lexicon, encoding="utf-8"))
    read = lambda p: sys.stdin.read() if p == "-" else open(p, encoding="utf-8").read()

    targets = [(args.input, read(args.input))]
    if args.compare:
        targets.append((args.compare, read(args.compare)))

    payload = []
    for name, text in targets:
        results, overall, verdict = run(text, lex)
        payload.append({
            "source": name,
            "checks": {k: {"score": round(v[0], 1), "detail": v[1]} for k, v in results.items()},
            "human_score": round(overall, 1),
            "verdict": verdict,
        })

    if args.json:
        print(json.dumps(payload if args.compare else payload[0], indent=2, ensure_ascii=False))
        return

    for (name, text), p in zip(targets, payload):
        results, overall, verdict = run(text, lex)
        render(results, overall, verdict, label=os.path.basename(name) if args.compare else None)
    if args.compare:
        a, b = payload
        delta = b["human_score"] - a["human_score"]
        print(f"  {a['human_score']:.1f} {a['verdict']}  ->  "
              f"{b['human_score']:.1f} {b['verdict']}   ({delta:+.1f})\n")

    sys.exit(0 if payload[-1]["verdict"] == "APROVADO" else 1)


if __name__ == "__main__":
    main()
