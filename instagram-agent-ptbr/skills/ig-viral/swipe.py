#!/usr/bin/env python3
"""
swipe.py - ranqueia os reels que você coletou pelo quanto cada um superou a
própria conta, dá nome à fórmula de gancho de cada um e escreve o arquivo de
referências (swipe file).

Versão em português do Brasil, adaptada de swipe.py do projeto
instagram-agent-skill (Jake Schincariol, licença MIT).

O objetivo deste script é uma correção só: view bruta não é evidência. Uma
conta com 2 milhões de seguidores fazendo 400 mil views teve um dia fraco.
Uma conta com 4 mil seguidores fazendo 400 mil views achou alguma coisa. Este
script ranqueia pelo múltiplo sobre a linha de base da própria conta, que é a
única versão de "viralizou" que ensina algo que dá pra copiar.

A entrada é um arquivo separado por TAB que você preenche enquanto navega, um
reels por linha, com um cabeçalho dando nome às colunas. Aceita os nomes em
português ou em inglês:

    conta      seguidores   mediana   views    gancho
    @alguem    48 mil       11.000    412000   ninguém te conta que seus primeiros 30 flopam

Números podem vir como 412000, 412.000, 412 mil, 412k ou 1,2 mi.
`mediana` é a média típica de views recentes da conta e é a melhor linha de
base. Se você só tem `seguidores`, deixe a mediana de fora e o script avisa.
`gancho` é a primeira frase do reels, falada ou na tela, nas palavras da pessoa.

Uso
  python3 swipe.py coletados.tsv
  python3 swipe.py coletados.tsv --out ~/.claude/instagram/swipe.md
  python3 swipe.py coletados.tsv --json
"""

import argparse
import json
import os
import re
import statistics
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
REEL = os.path.join(HERE, "..", "ig-reel")
# Instalada junto com a ig-reel, usa os arquivos dela. Enviada sozinha (por
# exemplo como .zip no claude.ai), usa as cópias que vierem nesta pasta.
HOOKS = next((p for p in (os.path.join(REEL, "hooks.json"), os.path.join(HERE, "hooks.json"))
              if os.path.exists(p)), os.path.join(REEL, "hooks.json"))
NUM = r"\d(?:[.,]?\d)*"
WORD_RE = re.compile(r"R\$\s?" + NUM + r"%?|" + NUM + r"%?|[^\W\d_][\w'’-]*")

try:                                              # opcional: dá nota aos ganchos também
    sys.path.insert(0, HERE)
    sys.path.insert(0, REEL)
    from hookscore import run as score_hook       # noqa: E402
except Exception:                                 # sem hookscore.py por perto
    score_hook = None

COLUMN_ALIASES = {
    "conta": "account", "perfil": "account", "account": "account",
    "seguidores": "followers", "followers": "followers",
    "mediana": "median", "median": "median",
    "views": "views", "visualizacoes": "views", "visualizações": "views", "plays": "views",
    "gancho": "hook", "hook": "hook",
}


def fold(text):
    nfd = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def parse_count(raw):
    """'412000', '412.000', '412 mil', '412k', '1,2 mi', '1.2M' -> inteiro, ou None."""
    s = fold(raw or "").replace(" ", "")
    m = re.fullmatch(r"([\d.,]+)(k|mil|m|mi|mm|milhao|milhoes|milhão|milhões)?\.?", s)
    if not m:
        digits = re.sub(r"[^\d]", "", s)
        return int(digits) if digits else None
    number, suffix = m.groups()
    if suffix:
        value = float(number.replace(".", "").replace(",", ".") if "," in number
                      else number)
        mult = 1_000 if suffix in ("k", "mil") else 1_000_000
        return int(round(value * mult))
    digits = re.sub(r"[^\d]", "", number)
    return int(digits) if digits else None


def fmt(n):
    """Separador de milhar no padrão brasileiro: 412.000."""
    return f"{n:,}".replace(",", ".")


def load_formulas(path):
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        return None
    by_id = {h["id"]: h for h in d["hooks"]}
    order = d.get("classify_order") or sorted(by_id)
    return [(by_id[i]["id"], by_id[i]["name"],
             re.compile(by_id[i]["match"], re.IGNORECASE)) for i in order if i in by_id]


def classify(hook, formulas):
    if not formulas:
        return None, "sem classificação"
    for fid, name, pattern in formulas:
        if pattern.search(hook):
            return fid, name
    return None, "sem classificação"


def read_rows(path):
    if path == "-":
        raw = sys.stdin.read()
    else:
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
    lines = [l for l in raw.splitlines() if l.strip() and not l.lstrip().startswith("#")]
    if not lines:
        return []
    head = [COLUMN_ALIASES.get(fold(c.strip()), fold(c.strip())) for c in lines[0].split("\t")]
    if "views" in head and "hook" in head:
        cols, body = head, lines[1:]
    else:
        cols, body = ["account", "followers", "views", "hook"], lines
    rows = []
    for line in body:
        cells = line.split("\t")
        if len(cells) < len(cols):
            cells += [""] * (len(cols) - len(cells))
        r = dict(zip(cols, [c.strip() for c in cells]))
        r["views"] = parse_count(r.get("views", "")) or 0
        for k in ("followers", "median"):
            r[k] = parse_count(r.get(k, "") or "")
        if r["views"] and r.get("hook"):
            rows.append(r)
    return rows


def analyse(rows, formulas):
    used_median = any(r.get("median") for r in rows)
    for r in rows:
        base = r.get("median") or r.get("followers") or 0
        r["baseline"] = base
        r["outlier"] = round(r["views"] / base, 2) if base else None
        r["formula_id"], r["formula"] = classify(r["hook"], formulas)
        r["words"] = len(WORD_RE.findall(r["hook"]))
        if score_hook:
            _, overall, verdict, _ = score_hook(r["hook"])
            r["hook_score"], r["hook_verdict"] = round(overall, 1), verdict
        else:
            r["hook_score"], r["hook_verdict"] = None, None
    ranked = sorted(rows, key=lambda r: -(r["outlier"] or 0))
    third = max(1, len(ranked) // 3)
    top, bottom = ranked[:third], ranked[-third:]

    def med(items, key):
        vals = [i[key] for i in items if i.get(key) is not None]
        return round(statistics.median(vals), 1) if vals else None

    counts = {}
    for r in top:
        counts[r["formula"]] = counts.get(r["formula"], 0) + 1
    return {
        "baseline": "mediana da conta" if used_median else "número de seguidores",
        "n": len(ranked),
        "accounts": len({r.get("account", "") for r in ranked}),
        "reels": ranked,
        "top_formulas": sorted(counts.items(), key=lambda kv: -kv[1]),
        "top_hook_score": med(top, "hook_score"),
        "bottom_hook_score": med(bottom, "hook_score"),
        "top_words": med(top, "words"),
        "bottom_words": med(bottom, "words"),
        "unclassified": sum(1 for r in ranked if r["formula"] == "sem classificação"),
    }


def render(a, out=sys.stdout):
    head = (f"REFERÊNCIAS  ·  {a['n']} reels  ·  {a['accounts']} contas  ·  "
            f"linha de base: {a['baseline']}")
    print("\n" + head, file=out)
    print("=" * max(len(head), 78), file=out)
    for r in a["reels"]:
        mult = f"{r['outlier']:.1f}x" if r["outlier"] else "   ?"
        score = f"{r['hook_score']:.0f}" if r["hook_score"] is not None else " -"
        fid = f"#{r['formula_id']:<2}" if r["formula_id"] else "-  "
        print(f"  {mult:>7}  gancho {score:>3}  {fid} {r['formula'][:22]:<22} "
              f"{r.get('account', '')[:16]:<16} {fmt(r['views']):>11}", file=out)
        print(f"           \"{r['hook'][:96]}\"", file=out)
    print("-" * max(len(head), 78), file=out)
    print("O QUE ESTÁ FUNCIONANDO NESTE LOTE", file=out)
    if a["top_formulas"]:
        print("  terço de cima por múltiplo:  "
              + ", ".join(f"{n} x{c}" for n, c in a["top_formulas"][:4]), file=out)
    if a["top_hook_score"] is not None:
        print(f"  nota mediana do gancho:      em cima {a['top_hook_score']:.0f}  "
              f"vs embaixo {a['bottom_hook_score']:.0f}", file=out)
    print(f"  tamanho mediano do gancho:   em cima {a['top_words']} palavras  "
          f"vs embaixo {a['bottom_words']} palavras", file=out)
    print(f"  sem classificação:           {a['unclassified']} de {a['n']}. Leia esses um por um, "
          "é ali que está escondida a fórmula que você ainda não tem.", file=out)
    print("\n  Um lote coletado à mão é evidência, não prova. Doze reels não mostram nada;\n"
          "  quarenta em seis contas mostram alguma coisa. Colete mais antes de acreditar.\n",
          file=out)


def to_markdown(a):
    lines = ["# Arquivo de referências", "",
             f"{a['n']} reels em {a['accounts']} contas. "
             f"Ranqueados pelo múltiplo sobre {a['baseline']}.", ""]
    for r in a["reels"]:
        mult = f"{r['outlier']:.1f}x" if r["outlier"] else "?"
        base = fmt(r["baseline"]) if r["baseline"] else "?"
        lines += [f"## {mult}  {r['formula']}  ({r.get('account', '')})",
                  f"- views: {fmt(r['views'])}  linha de base: {base}",
                  f"- nota do gancho: {r['hook_score']}  palavras: {r['words']}",
                  f"- gancho: \"{r['hook']}\"", ""]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Ranqueia reels coletados pelo múltiplo sobre a própria conta.")
    ap.add_argument("input", nargs="?", default="-", help="arquivo TSV, ou - pra stdin")
    ap.add_argument("--hooks", default=HOOKS, help="caminho do ig-reel/hooks.json")
    ap.add_argument("--out", help="também grava o arquivo de referências em markdown aqui")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = read_rows(args.input)
    if not rows:
        print("nenhuma linha utilizável. Precisa de um arquivo separado por TAB com pelo menos "
              "views e gancho.", file=sys.stderr)
        sys.exit(2)
    formulas = load_formulas(args.hooks)
    a = analyse(rows, formulas)
    if not formulas:
        print("aviso: hooks.json não encontrado, fórmulas sem nome. Use --hooks.", file=sys.stderr)
    if score_hook is None:
        print("aviso: hookscore.py não pôde ser importado, notas de gancho puladas.", file=sys.stderr)

    if args.json:
        print(json.dumps(a, indent=2, ensure_ascii=False))
    else:
        render(a)
    if args.out:
        path = os.path.expanduser(args.out)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        open(path, "w", encoding="utf-8").write(to_markdown(a))
        print(f"gravado em {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
