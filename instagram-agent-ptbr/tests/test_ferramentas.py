"""Testes das ferramentas em Python do pacote instagram-agent-ptbr.

Rodar a partir da raiz do repositório:
    python3 -m unittest discover -s instagram-agent-ptbr/tests -v

Só usa a biblioteca padrão. Nada acessa a rede.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def load(name, rel):
    path = SKILLS / rel
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(path.parent))


hookscore = load("hookscore", "ig-reel/hookscore.py")
beats = load("beats", "ig-reel/beats.py")
caption = load("caption", "ig-caption/caption.py")
humanize = load("humanize", "ig-human/humanize.py")
detect = load("detect", "ig-human/detect.py")
swipe = load("swipe", "ig-viral/swipe.py")
LEX = humanize.load_lexicon(SKILLS / "ig-human" / "slop.json")


class HookScoreTest(unittest.TestCase):
    def test_greeting_hook_is_weak_with_dealbreaker(self):
        _, overall, verdict, flags = hookscore.run("Oi gente, hoje eu queria falar sobre estratégia de conteúdo")
        self.assertEqual(verdict, "FRACO")
        self.assertLess(overall, 50)
        self.assertTrue(any("Saudação" in f for f in flags))

    def test_concrete_hook_is_strong(self):
        _, overall, verdict, flags = hookscore.run("Ninguém te conta que seus primeiros 30 reels são pra flopar")
        self.assertEqual(verdict, "FORTE")
        self.assertGreaterEqual(overall, 70)
        self.assertEqual(flags, [])

    def test_accents_are_ignored_in_word_lists(self):
        with_accent = hookscore.check_stakes("Ninguém te conta isso")
        without = hookscore.check_stakes("Ninguem te conta isso")
        self.assertEqual(with_accent[0], without[0])

    def test_reais_count_as_concrete(self):
        score, detail = hookscore.check_specificity("Perdi R$ 18.000 num contrato")
        self.assertGreaterEqual(score, 75)
        self.assertIn("R$ 18.000", detail)

    def test_stop_scrolling_and_preamble_are_dealbreakers(self):
        _, _, _, flags = hookscore.run("Para de rolar que nesse vídeo eu vou te mostrar tudo")
        self.assertEqual(len(flags), 2)

    def test_weak_opener_matches_whole_words_only(self):
        # "oi" não pode pegar "oito".
        self.assertIsNone(hookscore.weak_opener(["oito", "anos"]))
        self.assertEqual(hookscore.weak_opener(["oi", "gente"]), "oi")

    def test_pro_drop_first_person_is_detected(self):
        score, _ = hookscore.check_address("Perdi R$ 18 mil numa cláusula")
        self.assertEqual(score, 70.0)


class HookFormulasTest(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((SKILLS / "ig-reel" / "hooks.json").read_text(encoding="utf-8"))
        self.formulas = swipe.load_formulas(SKILLS / "ig-reel" / "hooks.json")

    def test_has_26_formulas_and_full_order(self):
        self.assertEqual(len(self.doc["hooks"]), 26)
        self.assertEqual(sorted(self.doc["classify_order"]), list(range(1, 27)))

    def test_every_example_is_named_by_its_own_formula(self):
        for h in self.doc["hooks"]:
            fid, _ = swipe.classify(h["example"], self.formulas)
            self.assertEqual(fid, h["id"], h["example"])

    def test_classifier_abstains_on_plain_text(self):
        for text in ["Oi gente, hoje eu queria falar sobre estratégia", "Comprei um café hoje"]:
            self.assertEqual(swipe.classify(text, self.formulas), (None, "sem classificação"))


class BeatsTest(unittest.TestCase):
    SCRIPT = ("Perdi R$ 18 mil por causa de um contrato sem uma cláusula importante.\n"
              "Aprovação é sentimento. Entrega é data.\n"
              "Essa troca vale R$ 18 mil pra mim.\n")

    def test_long_hook_is_flagged(self):
        a = beats.analyse(self.SCRIPT, wpm=150)
        self.assertEqual(a["beats"][0]["label"], "GANCHO")
        self.assertTrue(a["beats"][0]["flags"])

    def test_loop_is_detected(self):
        a = beats.analyse(self.SCRIPT, wpm=150)
        self.assertTrue(any(n.startswith("Tem loop") for n in a["notes"]))

    def test_spoken_numbers_are_concrete(self):
        self.assertGreater(beats.concrete("faturei vinte mil em três meses"), 0)

    def test_target_note(self):
        a = beats.analyse(self.SCRIPT, wpm=150, target=60)
        self.assertTrue(any("abaixo do alvo" in n for n in a["notes"]))


class CaptionTest(unittest.TestCase):
    def status(self, a, name):
        return next(c["status"] for c in a["checks"] if c["check"] == name)

    def test_good_caption(self):
        text = ("Perdi R$ 18 mil por causa de uma cláusula que faltava.\n\n"
                "Hoje todo contrato de cliente tem pagamento na entrega.\n\n"
                "Comenta CONTRATO que eu te mando a cláusula.\n\n#freelancer #contratos\n")
        a = caption.analyse(text, keywords=["contrato de cliente"])
        self.assertEqual(a["asks"], ["comentar uma palavra-chave"])
        self.assertEqual(self.status(a, "HASHTAGS"), "OK")
        self.assertEqual(self.status(a, "TERMOS DE BUSCA"), "OK")
        self.assertEqual(a["verdict"], "PRONTA")

    def test_too_many_hashtags_fail(self):
        a = caption.analyse("Texto. " + " ".join(f"#tag{i}" for i in range(6)))
        self.assertEqual(self.status(a, "HASHTAGS"), "FALHA")
        self.assertEqual(a["verdict"], "CORRIGIR")

    def test_brazilian_link_and_greeting(self):
        a = caption.analyse("Oi gente! Confere em meusite.com.br/oferta")
        self.assertEqual(self.status(a, "LINKS"), "AVISO")
        self.assertEqual(self.status(a, "PRIMEIRA LINHA"), "AVISO")

    def test_lowercase_comment_is_not_a_keyword(self):
        a = caption.analyse("Comenta aqui embaixo o que você achou")
        self.assertNotIn("comentar uma palavra-chave", a["asks"])

    def test_search_terms_ignore_accents(self):
        a = caption.analyse("Falo de precificacao todo dia", keywords=["precificação"])
        self.assertEqual(self.status(a, "TERMOS DE BUSCA"), "OK")


class HumanizeTest(unittest.TestCase):
    def test_em_dash_and_lexicon(self):
        clean, report = humanize.humanize("É crucial alavancar ferramentas — sempre.", LEX)
        self.assertNotIn("—", clean)
        self.assertIn("importante", clean)
        self.assertIn("usar", clean)
        self.assertEqual(len(report["typographic"]), 1)

    def test_gender_agreement_kept(self):
        clean, _ = humanize.humanize("Mudei o mindset e foi um divisor de águas.", LEX)
        self.assertIn("a mentalidade", clean)
        self.assertIn("um marco", clean)

    def test_accent_insensitive_match(self):
        clean, _ = humanize.humanize("Alem disso, vale ressaltar que funciona.", LEX)
        self.assertNotIn("ressaltar", clean)
        self.assertIn("Também", clean)

    def test_question_mark_phrase_at_end_of_line(self):
        clean, _ = humanize.humanize("Postei todo dia por 60 dias.\nO que vocês acham?\n", LEX)
        self.assertNotIn("acham", clean)

    def test_orphan_punctuation_after_deletion(self):
        clean, _ = humanize.humanize("Leve seu negócio pro próximo nível. Me segue pra mais!", LEX)
        self.assertEqual(clean.strip(), "Leve seu negócio.")

    def test_urls_untouched(self):
        clean, _ = humanize.humanize("Veja https://exemplo.com.br/crucial-jornada agora", LEX)
        self.assertIn("https://exemplo.com.br/crucial-jornada", clean)

    def test_human_text_is_unchanged(self):
        text = ("Perdi R$ 18 mil em março porque esqueci uma cláusula. Uma.\n"
                "A gente aprende do jeito caro, né?\n")
        clean, report = humanize.humanize(text, LEX)
        self.assertEqual(clean, text)
        self.assertEqual(report["lexical"], [])

    def test_invisible_characters_removed(self):
        clean, report = humanize.humanize("pala​vra aqui", LEX)
        self.assertEqual(clean.strip(), "palavra aqui")
        self.assertEqual(len(report["invisible"]), 2)

    def test_structures_flagged(self):
        _, report = humanize.humanize("Não é só sobre postar, é sobre conectar.\nVocê sabia que isso existe?", LEX)
        names = " ".join(s["name"] for s in report["structures"])
        self.assertIn("Não é só", names)
        self.assertIn("você sabia que", names)


class DetectTest(unittest.TestCase):
    BAD = ("No mundo acelerado de hoje, é crucial alavancar ferramentas robustas — elas potencializam "
           "sua jornada de forma eficaz. Além disso, vale ressaltar que o algoritmo ama conteúdo de valor. "
           "Não é só sobre postar, é sobre se conectar de verdade. Nesse vídeo eu vou te mostrar como "
           "ressignificar seu mindset e levar seu negócio pro próximo nível. Me segue pra mais!")

    def test_bad_text_is_flagged_and_cleaning_helps(self):
        _, before, verdict = detect.run(self.BAD, LEX)
        self.assertEqual(verdict, "SINALIZADO")
        clean, _ = humanize.humanize(self.BAD, LEX)
        _, after, _ = detect.run(clean, LEX)
        self.assertGreater(after, before + 15)

    def test_orality_counts_in_voice(self):
        casual = ("A gente tava pensando nisso né, e pra mim tá claro que dá pra fazer. "
                  "Eu cobrei R$ 3 mil e o cliente topou na hora, tipo sem pensar duas vezes.")
        formal = ("Considera-se que a empresa realizou a cobrança adequada. O cliente aceitou "
                  "a proposta apresentada. A decisão foi tomada de maneira rápida e objetiva pelo comitê.")
        self.assertGreater(detect.check_voice(casual, LEX)[0], detect.check_voice(formal, LEX)[0])


class SwipeTest(unittest.TestCase):
    def test_parse_count(self):
        cases = {"412000": 412000, "412.000": 412000, "412 mil": 412000, "412k": 412000,
                 "1,2 mi": 1200000, "1.2M": 1200000, "900k": 900000, "": None}
        for raw, expected in cases.items():
            self.assertEqual(swipe.parse_count(raw), expected, raw)

    def test_ranking_by_outlier(self):
        tsv = ("conta\tseguidores\tmediana\tviews\tgancho\n"
               "@a\t2 mi\t900k\t1,2 mi\tnesse vídeo eu vou te mostrar minha rotina\n"
               "@b\t12k\t3000\t180000\trouba essa mensagem de quatro linhas\n")
        with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False, encoding="utf-8") as fh:
            fh.write(tsv)
        try:
            rows = swipe.read_rows(fh.name)
        finally:
            os.unlink(fh.name)
        a = swipe.analyse(rows, swipe.load_formulas(SKILLS / "ig-reel" / "hooks.json"))
        self.assertEqual(a["reels"][0]["account"], "@b")
        self.assertEqual(a["reels"][0]["outlier"], 60.0)
        self.assertEqual(a["reels"][0]["formula_id"], 9)
        self.assertEqual(a["baseline"], "mediana da conta")
        self.assertIn("180.000", swipe.to_markdown(a))


class PackageTest(unittest.TestCase):
    NAMES = ["ig-audit", "ig-caption", "ig-carousel", "ig-comment", "ig-dm", "ig-human",
             "ig-plan", "ig-profile", "ig-reel", "ig-reply", "ig-repurpose", "ig-story", "ig-viral"]

    def test_thirteen_skills_with_frontmatter(self):
        found = sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md"))
        self.assertEqual(found, self.NAMES)
        for name in self.NAMES:
            text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
            m = re.match(r"---\nname: (\S+)\ndescription: >-\n(.+?)\n---\n", text, re.S)
            self.assertIsNotNone(m, name)
            self.assertEqual(m.group(1), name)

    def test_rubric_sums_to_100(self):
        rubric = json.loads((SKILLS / "ig-profile" / "rubric.json").read_text(encoding="utf-8"))
        self.assertEqual(sum(i["points"] for i in rubric["items"]), rubric["total"])
        self.assertEqual(len(rubric["items"]), 12)

    def test_lexicon_is_valid(self):
        for s in LEX["structures"]:
            re.compile(s["regex"])
        finds = [e["find"].lower() for e in LEX["words"] + LEX["phrases"]]
        self.assertEqual(len(finds), len(set(finds)))

    def test_cli_entry_points_run(self):
        sample = "Perdi R$ 18 mil numa cláusula. A gente aprende do jeito caro, né?\n"
        runs = [
            (["ig-reel/hookscore.py", "--hook", "Perdi R$ 18 mil numa cláusula"], "NOTA DO GANCHO"),
            (["ig-reel/beats.py", "-"], "MINUTAGEM"),
            (["ig-caption/caption.py", "-"], "O QUE O FEED MOSTRA"),
            (["ig-human/humanize.py", "-", "--report"], "RELATÓRIO DO HUMANIZADOR"),
            (["ig-human/detect.py", "-"], "PAINEL DE DETECÇÃO"),
        ]
        for argv, expected in runs:
            proc = subprocess.run([sys.executable, str(SKILLS / argv[0]), *argv[1:]],
                                  input=sample, capture_output=True, text=True,
                                  encoding="utf-8", timeout=30)
            self.assertIn(proc.returncode, (0, 1), proc.stderr)
            self.assertIn(expected, proc.stdout + proc.stderr, argv[0])


if __name__ == "__main__":
    unittest.main()
