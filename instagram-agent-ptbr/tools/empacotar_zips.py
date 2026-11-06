#!/usr/bin/env python3
"""Gera um .zip por skill, no formato que o claude.ai aceita em Personalizar > Skills.

Cada zip tem a pasta da skill no topo (ig-reel/SKILL.md, não SKILL.md solto).
A ig-viral leva junto cópias de hooks.json e hookscore.py, porque no claude.ai
cada skill fica isolada e ela não enxerga a pasta da ig-reel.

Uso, a partir da raiz do repositório:
    python3 instagram-agent-ptbr/tools/empacotar_zips.py dist/skills-zip
"""
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
EXTRAS = {"ig-viral": [SKILLS / "ig-reel" / "hooks.json", SKILLS / "ig-reel" / "hookscore.py"]}


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "dist/skills-zip")
    out.mkdir(parents=True, exist_ok=True)
    for folder in sorted(p for p in SKILLS.iterdir() if (p / "SKILL.md").exists()):
        target = out / f"{folder.name}.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(folder.rglob("*")):
                if f.is_file() and "__pycache__" not in f.parts:
                    zf.write(f, f"{folder.name}/{f.relative_to(folder)}")
            for extra in EXTRAS.get(folder.name, []):
                zf.write(extra, f"{folder.name}/{extra.name}")
        print(target)


if __name__ == "__main__":
    main()
