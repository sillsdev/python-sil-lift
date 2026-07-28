"""Generate a synthetic large LIFT 0.13 file for streaming/perf tests.

Deterministic for a given (--entries, --seed): the same arguments always produce the
same bytes. Entries average roughly 1 KB, so --entries 200000 yields a file of a few
hundred MB. Output is written incrementally (bounded memory) to
tests/corpus/generated/ (git-ignored; regenerate on demand).

Usage: python tests/tools/generate_large.py [--entries N] [--seed N] [-o PATH]
"""

import argparse
import random
import sys
import uuid
from pathlib import Path
from typing import TextIO
from xml.sax.saxutils import escape

DEFAULT_DIR = Path(__file__).resolve().parents[1] / "corpus" / "generated"

VERNACULAR = "qaa-x-syn"
ANALYSIS = "en"
CONSONANTS = "ptkbdgmnŋfsʃhwlrj"
VOWELS = "aeiouɛɔ"
POS_VALUES = ["Noun", "Verb", "Adjective", "Adverb", "Pronoun", "Conjunction"]
GLOSS_WORDS = [
    "house",
    "water",
    "tree",
    "stone",
    "fire",
    "path",
    "river",
    "mountain",
    "bird",
    "fish",
    "hand",
    "eye",
    "speak",
    "walk",
    "eat",
    "sleep",
    "big",
    "small",
    "red",
    "old",
    "new",
    "good",
    "child",
    "woman",
    "man",
    "sky",
]


def word(rng: random.Random) -> str:
    return "".join(rng.choice(CONSONANTS) + rng.choice(VOWELS) for _ in range(rng.randint(2, 4)))


def write_entry(out: TextIO, rng: random.Random, index: int) -> None:
    guid = uuid.UUID(int=rng.getrandbits(128), version=4)
    lexeme = word(rng)
    out.write(f'<entry id="{lexeme}_{guid}" guid="{guid}">\n')
    out.write(
        f'<lexical-unit><form lang="{VERNACULAR}"><text>{escape(lexeme)}</text></form>'
        "</lexical-unit>\n"
    )
    for _ in range(rng.randint(1, 3)):
        gloss = rng.choice(GLOSS_WORDS)
        pos = rng.choice(POS_VALUES)
        out.write("<sense>\n")
        out.write(f'<grammatical-info value="{pos}"/>\n')
        out.write(f'<gloss lang="{ANALYSIS}"><text>{escape(gloss)}</text></gloss>\n')
        out.write(
            f'<definition><form lang="{ANALYSIS}"><text>{escape(gloss)} (sense of '
            f"{escape(lexeme)}, entry {index})</text></form></definition>\n"
        )
        if rng.random() < 0.5:
            sentence = " ".join(word(rng) for _ in range(rng.randint(4, 9)))
            translation = " ".join(rng.choice(GLOSS_WORDS) for _ in range(rng.randint(4, 9)))
            out.write("<example>\n")
            out.write(f'<form lang="{VERNACULAR}"><text>{escape(sentence)}</text></form>\n')
            out.write(
                f'<translation type="Free translation"><form lang="{ANALYSIS}">'
                f"<text>{escape(translation)}</text></form></translation>\n"
            )
            out.write("</example>\n")
        out.write("</sense>\n")
    out.write("</entry>\n")


def generate(path: Path, entries: int, seed: int) -> None:
    rng = random.Random(seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as out:
        out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        out.write(f'<lift version="0.13" producer="sil-lift generate_large.py seed={seed}">\n')
        for index in range(entries):
            write_entry(out, rng, index)
        out.write("</lift>\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entries", type=int, default=200_000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()
    output: Path = args.output or DEFAULT_DIR / f"synthetic-{args.entries}-seed{args.seed}.lift"
    generate(output, args.entries, args.seed)
    print(f"wrote {output} ({output.stat().st_size:,} bytes, {args.entries:,} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
