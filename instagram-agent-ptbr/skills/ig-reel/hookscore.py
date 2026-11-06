#!/usr/bin/env python3
"""
hookscore.py - dá nota à primeira frase de um Reel (o gancho) em cinco
propriedades que ganchos fortes têm em comum, e ranqueia vários ganchos entre si.

Versão em português do Brasil, adaptada de hookscore.py do projeto
instagram-agent-skill (Jake Schincariol, licença MIT).

O que é:  cinco heurísticas locais, calculadas na sua máquina só a partir do
texto. Elas medem propriedades que ganchos que seguram atenção costumam ter:
um tamanho que dá pra falar em menos de três segundos, algo concreto (número,
nome, valor em R$), algo em jogo, o ponto principal no começo da frase e não
no fim, e uma pessoa do outro lado pra quem a frase é dita.

O que NÃO é:  um previsor de views. A versão original, em inglês, foi testada
com 74 ganchos reais: separou bem gancho real de gancho propositalmente ruim
(AUC 0,83), mas quase não separou os acertos dos erros de um mesmo criador
(AUC 0,56, onde 0,50 é cara ou coroa). Esta versão em português troca as
listas de palavras e ainda NÃO foi validada com ganchos brasileiros reais.

Use para o que ela mede bem: pegar saudação, enrolação, gancho sem nada
concreto e gancho que leva cinco segundos pra falar. Ela não diz qual de dois
ganchos bons vai performar melhor. Isso quem decide é o seu rosto, a sua
edição, o seu áudio e pra quem o Instagram mostra. Confie no gráfico de
retenção mais do que neste script.

Cada checagem vai de 0 a 100. Quanto maior, melhor.

Uso
  python3 hookscore.py ganchos.txt              # um gancho por linha, ranqueados
  python3 hookscore.py --hook "Perdi R$ 18 mil por causa de uma cláusula."
  pbpaste | python3 hookscore.py -
  python3 hookscore.py ganchos.txt --json
"""

import argparse
import json
import re
import statistics
import sys
import unicodedata

NUM = r"\d(?:[.,]?\d)*"
# "R$ 18.000" é dito como uma coisa só, então conta como uma palavra só.
WORD_RE = re.compile(r"R\$\s?" + NUM + r"%?|" + NUM + r"%?|[^\W\d_][\w'’-]*")
NUMBER_RE = re.compile(
    r"R\$\s?\d(?:[.,]?\d)*"                               # dinheiro
    r"|\b\d(?:[.,]?\d)*\s?"                               # um número, com ou
    r"(?:%|k\b|x\b|mil\b|mi\b|h\b|hrs?\b|horas?\b|min\b"  # sem unidade
    r"|minutos?\b|seg\b|segundos?\b|dias?\b|semanas?\b|m[eê]s\b|meses\b|anos?\b)?",
    re.IGNORECASE)
UPPER = "A-ZÁÂÃÀÉÊÍÓÔÕÚÜÇ"
LOWER = "a-záâãàéêíóôõúüç"
# Nome próprio: maiúscula que não está no começo da frase.
PROPER_RE = re.compile(rf"(?<![.!?]\s)(?<!^)\b[{UPPER}][{LOWER}]{{2,}}\b")
PROPER_TOKEN = re.compile(rf"[{UPPER}][{LOWER}]{{2,}}")
HASHTAG_RE = re.compile(r"(?:^|\s)#\w+")
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")


def fold(text):
    """Minúsculas e sem acento, pra comparar 'você' com 'voce' e 'ninguém' com 'ninguem'."""
    nfd = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def folded_set(*items):
    return {fold(i) for i in items}


# Ganchos falados dizem os números em voz alta. "Zero real" e "vinte mil" são
# tão concretos quanto "R$ 0" e "R$ 20.000". "Um", "uma" e "primeiro" ficam de
# fora de propósito: na maioria das vezes são enchimento, não quantidade.
SPOKEN_NUMBERS = folded_set(
    "zero", "dois", "duas", "três", "quatro", "cinco", "seis", "sete", "oito",
    "nove", "dez", "onze", "doze", "treze", "quatorze", "catorze", "quinze",
    "dezesseis", "dezessete", "dezoito", "dezenove", "vinte", "trinta",
    "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa", "cem",
    "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "mil",
    "milhão", "milhões", "bilhão", "bilhões", "dúzia", "dezena", "dezenas",
    "centena", "centenas", "metade", "dobro", "triplo",
)
MONEY_WORDS = folded_set(
    "reais", "conto", "contos", "pila", "pilas", "grana", "faturamento",
    "faturei", "faturou", "lucro", "lucrei", "salário", "aluguel", "centavos",
    "milionário", "milionária", "bilionário", "prejuízo", "dívida",
)

# Palavras que colocam algo em jogo. Um gancho sem nenhuma delas é uma
# afirmação; com uma, vira motivo pra continuar assistindo. "Para" fica de
# fora porque quase sempre é preposição; "para de" é tratado à parte.
STAKES = folded_set(
    "pare", "parei", "parar", "parem", "nunca", "jamais", "errado", "errada",
    "erro", "erros", "errei", "errando", "perdi", "perder", "perdendo", "perdeu",
    "perda", "custo", "custou", "custa", "quebrei", "quebrado", "faliu", "fali",
    "falência", "falhei", "falhou", "fracasso", "fracassei", "ninguém", "não",
    "nem", "desisti", "desistir", "demitido", "demitida", "demiti", "apaguei",
    "apagar", "apague", "matou", "mata", "matar", "substituiu", "substitui",
    "cortei", "grátis", "paguei", "pagar", "cobrei", "cobrar", "contratei",
    "economizei", "proibido", "ilegal", "pior", "piores", "odeio", "odiava",
    "desperdicei", "desperdício", "golpe", "mentira", "mentiu", "verdade",
    "segredo", "escondido", "roubou", "roubei", "roubado", "antes", "até",
    "mas", "porém", "exceto", "problema", "risco", "perigo", "cuidado",
    "alerta", "arrependo", "arrependimento", "deveria", "ainda", "já", "só",
    "apenas", "sem", "versus", "vs", "medo", "vergonha", "caro", "falso",
    "primeiro",
)

# Aberturas que gastam o primeiro segundo sem dizer nada. Comparadas palavra
# por palavra, não por prefixo, pra "oi" não pegar "oito".
WEAK_OPENERS = [tuple(fold(w).split()) for w in [
    "então", "oi", "olá", "e aí", "eai", "eae", "fala galera", "fala pessoal",
    "fala gente", "galera", "gente", "pessoal", "bom dia", "boa tarde",
    "boa noite", "hoje", "basicamente", "sinceramente", "honestamente", "olha",
    "escuta", "seguinte", "o seguinte", "tipo", "bom", "bem", "enfim", "ah",
    "hum", "vamos", "vamo", "bora", "eu queria", "eu quero", "eu vim", "vim",
    "vou falar", "um dos", "uma das", "você já", "vocês já", "você sabia",
    "sabia que", "você sabe", "você tem", "você está", "você tá", "neste",
    "nesse", "no vídeo", "a coisa", "muita gente", "existe", "existem",
    "tem muita", "isso é", "esse é", "este é", "essa é", "como um", "como uma",
    "quando se trata", "se você já", "sabe",
]]

# Imperativos que merecem a primeira posição.
IMPERATIVES = folded_set(
    "pare", "parem", "rouba", "roube", "copia", "copie", "apaga", "apague",
    "tenta", "tente", "assiste", "assista", "veja", "vê", "lê", "leia",
    "salva", "salve", "usa", "use", "monta", "monte", "faz", "faça", "escreve",
    "escreva", "manda", "mande", "envia", "envie", "pega", "pegue", "começa",
    "comece", "larga", "largue", "nunca", "sempre", "não", "testa", "teste",
    "coloca", "coloque", "confere", "confira", "olha", "olhe", "pensa", "pense",
    "esquece", "esqueça", "evita", "evite", "cobra", "cobre", "aprende",
    "aprenda", "guarda", "guarde", "anota", "anote", "escuta", "escute",
)

SECOND_PERSON = folded_set(
    "você", "vocês", "vc", "vcs", "cê", "cês", "seu", "sua", "seus", "suas",
    "te", "ti", "contigo", "tu", "teu", "tua", "teus", "tuas",
)
FIRST_PERSON = folded_set(
    "eu", "meu", "minha", "meus", "minhas", "me", "mim", "comigo", "nosso",
    "nossa", "nossos", "nossas",
)
# Português esconde o sujeito ("Perdi R$ 18 mil" já é primeira pessoa), então
# alguns verbos comuns em primeira pessoa contam também.
FIRST_PERSON_VERBS = folded_set(
    "fiz", "tive", "fui", "perdi", "vendi", "descobri", "aprendi", "consegui",
    "decidi", "pedi", "recebi", "escrevi", "vivi", "abri", "sou", "estou", "tô",
    "tenho", "faço", "sei", "quero", "acho", "uso", "cobro", "vendo", "posto",
)

DEALBREAKERS = [
    (re.compile(r"(?i)^\s*(?:(?:para|pare|parem) de (?:rolar|passar|arrastar)"
                r"|n[ãa]o (?:role|rola|passe|passa|pule|pula|arraste)\b"
                r"|espera[,!.]?\s+n[ãa]o\b)"),
     "Abre com \"para de rolar\". Pedir atenção prova que você ainda não conquistou."),
    (re.compile(r"(?i)\b(?:nesse|neste|no) (?:v[íi]deo|reels?|post)(?: de hoje)?\b"
                r"|\b(?:hoje )?(?:eu )?vou (?:te |lhes? )?(?:mostrar|ensinar|explicar)\b"),
     "Enrolação de vídeo (\"nesse vídeo eu vou te mostrar\"). Apaga e abre no resultado."),
    (re.compile(r"(?i)^\s*(?:oi|ol[áa]|e a[íi]|eai|eae|bom dia|boa tarde|boa noite"
                r"|fala,? (?:galera|pessoal|gente|rapaziada|time|fam[íi]lia)"
                r"|salve,? (?:galera|gente|pessoal|rapaziada|fam[íi]lia)|salve salve)\b"),
     "Saudação. Ninguém abriu o feed pra ser cumprimentado."),
    (HASHTAG_RE,
     "Hashtag no gancho. Hashtag vai no fim da legenda, se for."),
    (EMOJI_RE,
     "Emoji no gancho. Texto na tela no tamanho de gancho tem espaço pra palavras ou pra emoji, não pros dois."),
]


def clamp(n):
    return max(0.0, min(100.0, n))


def words(text):
    return WORD_RE.findall(text)


def folded_words(text):
    return [fold(w).strip("'’-") for w in words(text)]


def is_first_person_verb(token):
    return token in FIRST_PERSON_VERBS or (len(token) >= 5 and token.endswith("ei"))


def check_length(text):
    """O gancho precisa chegar antes do polegar mexer. Uns dois segundos."""
    n = len(words(text))
    secs = n / 2.5                       # ~150 palavras por minuto, falado
    chars = len(text.strip())
    if 5 <= n <= 12:
        score = 100.0
    elif n < 5:
        score = clamp(100 - (5 - n) * 20)
    else:
        score = clamp(100 - (n - 12) * 11)
    if chars > 70:                       # duas linhas de texto grande na tela.
        score -= 12                      # Português é mais longo que inglês,
                                         # por isso 70 e não 60.
    return clamp(score), f"{n} palavras, {chars} caracteres, ~{secs:.1f}s falado (ideal: 5 a 12 palavras)"


def check_specificity(text):
    """Uma coisa concreta vale mais que três abstratas."""
    nums = [n.strip() for n in NUMBER_RE.findall(text) if n.strip()]
    propers = set(PROPER_RE.findall(text))
    low = folded_words(text)
    spoken = [w for w in low if w in SPOKEN_NUMBERS or w in MONEY_WORDS]
    hits = len(nums) + len(propers) + len(spoken)
    score = 15.0 if hits == 0 else clamp(45 + hits * 30)
    found = ", ".join(nums[:2] + sorted(propers)[:2] + spoken[:2])
    return score, (f"{hits} marcador(es) concreto(s)" + (f": {found}" if found else
                   " - sem número, sem nome, nada que dê pra conferir"))


def check_stakes(text):
    """Tensão, custo, negação. Algo que quem assiste pode perder."""
    low = folded_words(text)
    markers = sorted({w for w in low if w in STAKES})
    if re.search(r"\b(?:para|pare|parem) de\b", fold(text)):
        markers.append("para de")
    if re.search(r"R\$\s?\d", text):
        markers.append("um preço")
    n = len(markers)
    score = {0: 20.0, 1: 70.0}.get(n, 100.0)
    detail = f"{n} marcador(es) de tensão" + (f": {', '.join(markers[:4])}" if markers else
                                              " - nada está em jogo nessa frase")
    return clamp(score), detail


def weak_opener(low):
    for weak in WEAK_OPENERS:
        if tuple(low[:len(weak)]) == weak:
            return " ".join(weak)
    return None


def check_frontload(text):
    """A palavra interessante não pode estar na nona posição."""
    w = words(text)
    if not w:
        return 0.0, "vazio"
    low = folded_words(text)
    hit_opener = weak_opener(low)
    penalty = 30 if hit_opener else 0
    payload = None
    for i, token in enumerate(low):
        stop_cmd = token in ("para", "pare", "parem") and low[i + 1:i + 2] == ["de"]
        if (stop_cmd or token in STAKES or token in SPOKEN_NUMBERS or token in MONEY_WORDS
                or NUMBER_RE.match(w[i]) or (i and PROPER_TOKEN.fullmatch(w[i]))):
            payload = i
            break
    if payload is None:
        base = 30.0
        where = "nenhuma palavra de impacto na frase"
    elif payload <= 3:
        base = 100.0
        where = f"impacto na palavra {payload + 1}"
    elif payload <= 6:
        base = 70.0
        where = f"impacto na palavra {payload + 1}, dá pra trazer pra frente"
    else:
        base = 40.0
        where = f"impacto na palavra {payload + 1}, tarde demais"
    detail = where + (f"; abertura fraca \"{hit_opener}\"" if hit_opener else "")
    return clamp(base - penalty), detail


def check_address(text):
    """Falando com uma pessoa, ou solto no ar."""
    low = folded_words(text)
    raw = [x.lower() for x in words(text)]
    if any(w in SECOND_PERSON for w in low):
        return 100.0, "fala com quem está assistindo"
    if low and (low[0] in IMPERATIVES or (low[0] == "para" and low[1:2] == ["de"])):
        return 90.0, f"abre com imperativo (\"{words(text)[0]}\")"
    if (any(w in FIRST_PERSON for w in low) or "nós" in raw
            or "a gente" in " ".join(low) or any(is_first_person_verb(w) for w in low)):
        return 70.0, "primeira pessoa, sem falar com ninguém"
    return 35.0, "terceira pessoa, ninguém na sala"


CHECKS = ["TAMANHO", "ESPECIFICIDADE", "TENSÃO", "ABERTURA", "DIRECIONAMENTO"]


def run(text):
    results = {
        "TAMANHO": check_length(text),
        "ESPECIFICIDADE": check_specificity(text),
        "TENSÃO": check_stakes(text),
        "ABERTURA": check_frontload(text),
        "DIRECIONAMENTO": check_address(text),
    }
    flags = [msg for pattern, msg in DEALBREAKERS if pattern.search(text)]
    scores = [results[c][0] for c in CHECKS]
    # A propriedade mais fraca limita o gancho, mesma lógica do detect.py: uma
    # propriedade ruim basta pro polegar continuar rolando.
    overall = statistics.mean(scores) * 0.6 + min(scores) * 0.4 - len(flags) * 15
    overall = clamp(overall)
    verdict = "FORTE" if overall >= 70 and min(scores) >= 55 and not flags else (
        "OK" if overall >= 50 else "FRACO")
    return results, overall, verdict, flags


def bar(score, width=24):
    filled = round(score / 100 * width)
    return "#" * filled + "." * (width - filled)


def render_one(text, results, overall, verdict, flags, out=sys.stdout):
    print("\nNOTA DO GANCHO", file=out)
    print("=" * 64, file=out)
    print(f"  \"{text.strip()}\"\n", file=out)
    for name in CHECKS:
        score, detail = results[name]
        print(f"  {name:<15} {bar(score)} {score:5.1f}", file=out)
        print(f"  {'':<15} {detail}", file=out)
    print("-" * 64, file=out)
    print(f"  {'NOTA FINAL':<15} {bar(overall)} {overall:5.1f}   {verdict}", file=out)
    for f in flags:
        print(f"\n  ELIMINATÓRIO  {f}", file=out)
    if verdict != "FORTE":
        weakest = min(CHECKS, key=lambda c: results[c][0])
        print(f"\n  Ponto mais fraco: {weakest}. Corrija esse e rode de novo.", file=out)
    print("", file=out)


def render_table(rows, out=sys.stdout):
    print("\nRANKING DE GANCHOS\n" + "=" * 78, file=out)
    for i, r in enumerate(rows, 1):
        mark = "->" if i == 1 else "  "
        hook = r["hook"] if len(r["hook"]) <= 62 else r["hook"][:59] + "..."
        print(f"{mark} {r['score']:5.1f} {r['verdict']:<6} {hook}", file=out)
        print(f"        mais fraco: {r['weakest']} ({r['checks'][r['weakest']]['score']:.0f})", file=out)
        for f in r["flags"]:
            print(f"        eliminatório: {f}", file=out)
    print("\nGrave o primeiro. Se o primeiro está abaixo de 50, nenhum desses é o gancho.\n",
          file=out)


def main():
    ap = argparse.ArgumentParser(description="Dá nota a ganchos de Reels em cinco propriedades.")
    ap.add_argument("input", nargs="?", default="-", help="arquivo com um gancho por linha, ou -")
    ap.add_argument("--hook", help="avalia um único gancho passado na linha de comando")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.hook:
        lines = [args.hook]
    else:
        raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
    if not lines:
        print("nada pra avaliar", file=sys.stderr)
        sys.exit(2)

    payload = []
    for line in lines:
        results, overall, verdict, flags = run(line)
        payload.append({
            "hook": line,
            "checks": {k: {"score": round(v[0], 1), "detail": v[1]} for k, v in results.items()},
            "weakest": min(CHECKS, key=lambda c: results[c][0]),
            "flags": flags,
            "score": round(overall, 1),
            "verdict": verdict,
        })

    if args.json:
        print(json.dumps(payload if len(payload) > 1 else payload[0], indent=2, ensure_ascii=False))
        return

    if len(payload) == 1:
        results, overall, verdict, flags = run(lines[0])
        render_one(lines[0], results, overall, verdict, flags)
    else:
        render_table(sorted(payload, key=lambda r: -r["score"]))

    sys.exit(0 if max(p["score"] for p in payload) >= 70 else 1)


if __name__ == "__main__":
    main()
