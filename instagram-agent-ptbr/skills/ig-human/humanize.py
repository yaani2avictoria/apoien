#!/usr/bin/env python3
"""
humanize.py - tira a marca de máquina de um rascunho em português.

Versão em português do Brasil, adaptada de humanize.py do projeto
instagram-agent-skill (Jake Schincariol, licença MIT).

Três passadas, nesta ordem:

  1. INVISÍVEIS   apaga ou normaliza caracteres que um teclado de gente nunca
                  produz: zero-width joiners, word joiners, hífen suave, BOM,
                  caracteres de tag Unicode, espaços rígidos e estreitos. Eles
                  sobrevivem ao copiar e colar e são a marca mais mecânica de
                  qualquer texto gerado.
  2. TIPOGRAFIA   travessão -> vírgula, meia-risca -> hífen, aspas curvas ->
                  retas, reticências de um caractere -> três pontos,
                  marcador -> hífen.
  3. VOCABULÁRIO  troca os clichês do slop.json por palavras simples,
                  mantendo maiúsculas, ignorando acento na busca e sem mexer
                  em links.

Marcas de estrutura (trio de três, "não é só X, é Y", parede de hashtags) são
APONTADAS, nunca reescritas automaticamente: mudar o formato de uma frase
exige julgamento, e isso é trabalho do modelo, não de um regex.

Uso
  python3 humanize.py rascunho.txt
  python3 humanize.py rascunho.txt --report
  pbpaste | python3 humanize.py - --report
  python3 humanize.py rascunho.txt --json
  python3 humanize.py rascunho.txt -o limpo.txt
"""

import argparse
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
LEX = os.path.join(HERE, "slop.json")

URL_RE = re.compile(r"https?://\S+|www\.\S+|\S+@\S+\.\S+")
SENT_RE = re.compile(r"[^.!?\n]+[.!?]*")
ACCENTS = {"a": "aáàâã", "e": "eéê", "i": "ií", "o": "oóôõ", "u": "uúü", "c": "cç"}


def load_lexicon(path=LEX):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def fold(text):
    nfd = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def term_pattern(find):
    """Regex de um termo do vocabulário que ignora acento e maiúscula.

    'você' casa com 'voce' e 'Você'. A borda de palavra só entra onde o termo
    começa ou termina com letra, pra 'o que vocês acham?' casar no fim da linha.
    """
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


def _cp(spec):
    """'U+200B' -> 0x200b;  'U+E0000-U+E007F' -> (início, fim)."""
    if "-" in spec:
        a, b = spec.split("-")
        return (int(a[2:], 16), int(b[2:], 16))
    return int(spec[2:], 16)


def protect_urls(text):
    """Troca links por marcadores pra nenhuma passada reescrever dentro de um link."""
    found = []

    def stash(m):
        found.append(m.group(0))
        return f"\x00URL{len(found) - 1}\x00"

    return URL_RE.sub(stash, text), found


def restore_urls(text, found):
    for i, url in enumerate(found):
        text = text.replace(f"\x00URL{i}\x00", url)
    return text


def pass_invisible(text, lex):
    """Apaga ou transforma em espaço os caracteres invisíveis. Devolve (texto, ocorrências)."""
    hits = []
    for entry in lex["invisible"]:
        cp = _cp(entry["cp"])
        if isinstance(cp, tuple):
            pattern = "[" + re.escape(chr(cp[0])) + "-" + re.escape(chr(cp[1])) + "]"
        else:
            pattern = re.escape(chr(cp))
        n = len(re.findall(pattern, text))
        if n:
            hits.append({"name": entry["cp"] + " " + entry["name"], "count": n,
                         "action": "apagar" if entry["action"] == "delete" else "espaço"})
            text = re.sub(pattern, "" if entry["action"] == "delete" else " ", text)
    # Qualquer caractere Cf (formato) que sobrou é invisível por definição.
    stray = [c for c in text if unicodedata.category(c) == "Cf"]
    if stray:
        hits.append({"name": "outros caracteres invisíveis de formato", "count": len(stray),
                     "action": "apagar"})
        text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    return text, hits


def pass_typographic(text, lex):
    hits = []
    for entry in lex["typographic"]:
        ch = entry["from"]
        n = text.count(ch)
        if not n:
            continue
        hits.append({"name": f"{ch} {entry['name']}", "count": n, "to": entry["to"].strip() or "(espaço)"})
        if ch == "—":
            # " palavra — palavra " e "palavra—palavra" viram vírgula + espaço.
            text = re.sub(r"\s*—\s*", ", ", text)
        elif ch == "–":
            text = re.sub(r"\s*–\s*(?=\d)", "-", text)      # 5–10  -> 5-10
            text = re.sub(r"\s+–\s+", ", ", text)            # usada como travessão
            text = text.replace("–", "-")
        else:
            text = text.replace(ch, entry["to"])
    # Vírgula inserida antes de outra pontuação fica errado.
    text = re.sub(r",\s*([,.;:!?])", r"\1", text)
    text = re.sub(r",\s*\n", "\n", text)
    # Travessão no começo da linha (fala de diálogo) virou ", ": tira.
    text = re.sub(r"(?m)^,\s*", "", text)
    return text, hits


def _match_case(src, repl):
    if not repl:
        return repl
    if src.isupper() and len(src) > 1:
        return repl.upper()
    if src[0].isupper():
        return repl[0].upper() + repl[1:]
    return repl


def pass_lexical(text, lex):
    """Troca clichês de palavra e de frase. Os mais longos primeiro, pra frase ganhar."""
    hits = []
    entries = sorted(lex["phrases"] + lex["words"],
                     key=lambda e: len(e["find"]), reverse=True)
    for entry in entries:
        pattern = term_pattern(entry["find"])
        found = pattern.findall(text)
        if not found:
            continue
        hits.append({"find": entry["find"], "replace": entry["replace"] or "(apagado)",
                     "count": len(found), "family": entry["family"]})
        text = pattern.sub(lambda m: _match_case(m.group(0), entry["replace"]), text)
    # Limpeza depois das remoções. Apagar uma oração inteira deixa pontuação
    # órfã pra trás ("sistema. ." ou uma linha que agora começa com vírgula),
    # e isso fica pior que o clichê.
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"(?m)^[ \t]*(?:[,.;:]+[ \t]*)+", "", text)
    text = re.sub(r"(?m)^[ \t](?=\S)", "", text)       # um espaço deixado por uma remoção.
                                                      # Recuos maiores são de propósito.
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r",\s*([,.;:!?])", r"\1", text)      # um travessão virou vírgula e
                                                      # depois a oração seguinte sumiu
    text = text.replace("...", "\x00ELL\x00")          # protege reticências de verdade
    text = re.sub(r"\.\s*\.+", ".", text)
    text = re.sub(r"([!?])\s*\.", r"\1", text)
    text = re.sub(r"\.[ \t]*[!?]+", ".", text)          # "negócio. !" depois de apagar
                                                      # "Me segue pra mais!"
    text = text.replace("\x00ELL\x00", "...")
    text = re.sub(r"(?m)^[ \t]+$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Travessão que virou vírgula seguido de conectivo deixa uma emenda
    # ("é importante, também, é prova"). Promove pra ponto final.
    text = re.sub(r",\s*(também|então|assim|no fim|enfim)\s*,\s*",
                  lambda m: ". " + m.group(1)[0].upper() + m.group(1)[1:] + ", ", text)
    return text, hits


def scan_structures(text, lex):
    flags = []
    for s in lex["structures"]:
        try:
            pattern = re.compile(s["regex"], re.MULTILINE)
        except re.error:
            continue
        found = pattern.findall(text)
        if found:
            flags.append({"name": s["name"], "count": len(found), "fix": s["fix"]})
    # Frases todas do mesmo tamanho também é marca de estrutura.
    lens = [len(s.split()) for s in SENT_RE.findall(text) if len(s.split()) > 2]
    if len(lens) >= 4:
        mean = sum(lens) / len(lens)
        var = sum((n - mean) ** 2 for n in lens) / len(lens)
        cv = (var ** 0.5) / mean if mean else 0
        if cv < 0.35:
            flags.append({
                "name": f"Frases do mesmo tamanho (variação {cv:.2f})",
                "count": len(lens),
                "fix": "Quebre uma frase no meio. Deixe outra correr longa. Máquina escreve tudo igual.",
            })
    return flags


LETTER = "A-Za-zÁÂÃÀÉÊÍÓÔÕÚÜÇáâãàéêíóôõúüç"


def restore_capitals(original, text):
    """Apagar uma abertura deixa a próxima palavra em minúscula.

    Só corrige pra quem já começa frase com maiúscula: um estilo todo em
    minúsculas é escolha, não defeito, e passar por cima dele seria
    exatamente o tipo de coisa que este script existe pra evitar.
    """
    starts = re.findall(rf"(?:^|[.!?]\s+|\n)\s*([{LETTER}])", original)
    if not starts or sum(1 for c in starts if c.isupper()) * 2 < len(starts):
        return text
    return re.sub(r"(?:^|(?<=[.!?] )|(?<=[.!?]\n)|(?<=\n))\s*([a-záâãàéêíóôõúüç])",
                  lambda m: m.group(0)[:-1] + m.group(1).upper(), text)


def humanize(text, lex):
    raw_for_case = text
    text, urls = protect_urls(text)
    text, inv = pass_invisible(text, lex)
    text, typo = pass_typographic(text, lex)
    text, lexi = pass_lexical(text, lex)
    text = restore_capitals(raw_for_case, text)
    text = restore_urls(text, urls)
    return text.strip() + "\n", {
        "invisible": inv,
        "typographic": typo,
        "lexical": lexi,
        "structures": scan_structures(text, lex),
    }


def render_report(report, out=sys.stderr):
    def head(title):
        print(f"\n{title}\n" + "-" * len(title), file=out)

    total = sum(h["count"] for h in report["invisible"]) \
        + sum(h["count"] for h in report["typographic"]) \
        + sum(h["count"] for h in report["lexical"])

    head("RELATÓRIO DO HUMANIZADOR")
    print(f"{total} marcas de máquina removidas, "
          f"{len(report['structures'])} marcas de estrutura apontadas pra reescrever", file=out)

    if report["invisible"]:
        head("1. CARACTERES INVISÍVEIS")
        for h in report["invisible"]:
            print(f"  {h['count']:>3}x  {h['name']}  -> {h['action']}", file=out)
    if report["typographic"]:
        head("2. TIPOGRAFIA")
        for h in report["typographic"]:
            print(f"  {h['count']:>3}x  {h['name']}  -> {h['to']}", file=out)
    if report["lexical"]:
        head("3. CLICHÊS")
        for h in report["lexical"]:
            print(f"  {h['count']:>3}x  {h['find']}  -> {h['replace']}   [{h['family']}]", file=out)
    if report["structures"]:
        head("4. MARCAS DE ESTRUTURA  (não corrigidas sozinhas - reescreva você)")
        for h in report["structures"]:
            print(f"  {h['count']:>3}x  {h['name']}\n        {h['fix']}", file=out)
    if not any(report.values()):
        head("LIMPO")
        print("  Nada pra tirar.", file=out)
    print("", file=out)


def main():
    ap = argparse.ArgumentParser(description="Tira a marca de máquina de um rascunho.")
    ap.add_argument("input", nargs="?", default="-", help="arquivo, ou - pra stdin")
    ap.add_argument("-o", "--out", help="grava o texto limpo aqui em vez de imprimir")
    ap.add_argument("--report", action="store_true", help="mostra o que mudou, no stderr")
    ap.add_argument("--json", action="store_true", help="imprime {text, report} em JSON")
    ap.add_argument("--lexicon", default=LEX, help="caminho do slop.json")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    lex = load_lexicon(args.lexicon)
    clean, report = humanize(raw, lex)

    if args.json:
        print(json.dumps({"text": clean, "report": report}, indent=2, ensure_ascii=False))
        return
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(clean)
        print(f"gravado em {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(clean)
    if args.report:
        render_report(report)


if __name__ == "__main__":
    main()
