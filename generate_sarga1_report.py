#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_sarga1_report.py
==========================
Runs the combined sandhi+samasa pipeline (`combined_splitter.py`) over
EVERY word of Valmiki Ramayana, Balakanda, Sarga 1 (all 79 slokas,
R_1,001.001-079) and writes a plain-text report:

    word | verse | sandhi rule(s) | sandhi pada-vigraha | samasa type | samasa pada-vigraha

Runs entirely from local project files -- no network/cloud calls:
  - Verse text: `sandhi/build_ramayana_input.py`'s own VERSES dict (IAST,
    copied verbatim from sa_rAmAyaNa.txt -- see that file's docstring),
    transliterated to Devanagari via the already-installed
    indic_transliteration package (local, no network).
  - Sandhi analysis: `sandhi/sandhi_splitter.py` against
    `sandhi/apte_dictionary.sqlite` (local file).
  - Samasa analysis: `samasa/samasa_splitter.py` against the SAME
    sqlite dictionary (see combined_splitter.py).

Each row is either populated from a real rule/dictionary hit or marked
"-" -- nothing here is a guess dressed up as a result. Per the "basis
for checking" clarification given earlier: the dictionary hits are
objective (real sqlite lookups); the sandhi RULE NAMES come directly
from sandhi_splitter.py's own niyama-rule citations; the samasa TYPE
GUESS is explicitly labelled a heuristic (samasa_splitter.py's own
guess_samasa_type() docstring: "NOT a substitute for real classification").

USAGE
-----
    D:\\python\\python.exe generate_sarga1_report.py [output.txt]
    (default output: sarga1_sandhi_samasa_report.txt, next to this script)
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SANDHI_DIR = os.path.normpath(os.path.join(HERE, "..", "sandhi"))
for d in (SANDHI_DIR, HERE):
    if d not in sys.path:
        sys.path.insert(0, d)

from indic_transliteration import sanscript  # noqa: E402
from indic_transliteration.sanscript import transliterate as tl  # noqa: E402
import build_ramayana_input  # noqa: E402  (sandhi/build_ramayana_input.py)
from combined_splitter import CombinedSplitter  # noqa: E402

DEFAULT_OUTPUT = os.path.join(HERE, "sarga1_sandhi_samasa_report.txt")

COL_WIDTHS = [22, 14, 22, 30, 26, 30]
HEADERS = ["Word", "Verse", "Sandhi Rule(s)", "Sandhi Pada-Vigraha",
           "Samasa Type", "Samasa Pada-Vigraha"]


def build_verse_words():
    """
    Devanagari-transliterate every verse in build_ramayana_input.VERSES
    (all 79 slokas, R_1,001.001-079) and split each into whitespace
    tokens, exactly as sandhi/build_ramayana_input.py already does for
    its own output -- i.e. GRETIL pada-tokenized words (see
    sandhi/SKILL.md's "Running it" section: a printed space at every
    pada boundary, not necessarily a real word boundary). Returns
    [(verse_ref, word), ...] in verse order, word order.
    """
    rows = []
    for ref, iast in build_ramayana_input.VERSES.items():
        deva = tl(iast, sanscript.IAST, sanscript.DEVANAGARI)
        deva = build_ramayana_input.parasavarna_normalize(deva)
        for word in deva.split():
            if word:
                rows.append((ref, word))
    return rows


def _sandhi_name(sandhi_rules):
    if not sandhi_rules:
        return "-"
    return " ; ".join(r["rule_id"] for r in sandhi_rules)


def _sandhi_vigraha(sandhi_pieces):
    if len(sandhi_pieces) < 2:
        return "-"
    return " + ".join(sandhi_pieces)


def _shorten_type_guess(type_guess):
    """
    samasa_splitter.py's guess_samasa_type() returns a long, self-
    documenting sentence (by design -- see its own docstring: "NOT a
    substitute for real ... classification"). That's the right choice
    for its own CLI output, but repeated verbatim across ~100+ report
    rows it just floods a fixed-width text table with word-wrapped
    duplicate sentences. This keeps the SAME information (uncertain
    heuristic vs a specific named type) in a short form for the report
    table only -- the full sentence is never altered at the source.
    """
    if type_guess.startswith("tatpuruSa / karmaXAraya / bahuvrIhi"):
        return "uncertain (see samasa_splitter.py guess_samasa_type)"
    return type_guess


def _samasa_name(samasa_decompositions):
    if not samasa_decompositions:
        return "-"
    return " ; ".join(_shorten_type_guess(d["type_guess"]) for d in samasa_decompositions)


def _samasa_vigraha(samasa_decompositions):
    if not samasa_decompositions:
        return "-"
    return " ; ".join(" + ".join(d["members"]) for d in samasa_decompositions)


def _wrap(text, width):
    """Cheap word-wrap so long rule names / vigrahas don't blow out the
    fixed-width columns into unreadable ragged rows."""
    text = str(text)
    if len(text) <= width:
        return [text]
    lines, cur = [], ""
    for tok in text.split(" "):
        if cur and len(cur) + 1 + len(tok) > width:
            lines.append(cur)
            cur = tok
        else:
            cur = (cur + " " + tok) if cur else tok
    if cur:
        lines.append(cur)
    return lines or [""]


def format_table(rows):
    """rows: list of dicts with keys word/verse/sandhi_name/sandhi_vigraha/
    samasa_name/samasa_vigraha. Returns the full report as one string."""
    lines = []
    sep = "+" + "+".join("-" * (w + 2) for w in COL_WIDTHS) + "+"
    header = "| " + " | ".join(h.ljust(w) for h, w in zip(HEADERS, COL_WIDTHS)) + " |"
    lines.append(sep)
    lines.append(header)
    lines.append(sep)
    for row in rows:
        cells = [row["word"], row["verse"], row["sandhi_name"], row["sandhi_vigraha"],
                  row["samasa_name"], row["samasa_vigraha"]]
        wrapped = [_wrap(c, w) for c, w in zip(cells, COL_WIDTHS)]
        n_lines = max(len(w) for w in wrapped)
        for i in range(n_lines):
            parts = []
            for col, w in zip(wrapped, COL_WIDTHS):
                parts.append((col[i] if i < len(col) else "").ljust(w))
            lines.append("| " + " | ".join(parts) + " |")
        lines.append(sep)
    return "\n".join(lines)


def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT

    cs = CombinedSplitter()
    verse_words = build_verse_words()

    report_rows = []
    n_sandhi = 0
    n_samasa = 0
    for i, (ref, word) in enumerate(verse_words, 1):
        result = cs.split_word(word)
        sandhi_name = _sandhi_name(result["sandhi_rules"])
        sandhi_vigraha = _sandhi_vigraha(result["sandhi_pieces"])
        samasa_name = _samasa_name(result["samasa_decompositions"])
        samasa_vigraha = _samasa_vigraha(result["samasa_decompositions"])
        if sandhi_name != "-":
            n_sandhi += 1
        if samasa_name != "-":
            n_samasa += 1
        report_rows.append({
            "word": word, "verse": ref,
            "sandhi_name": sandhi_name, "sandhi_vigraha": sandhi_vigraha,
            "samasa_name": samasa_name, "samasa_vigraha": samasa_vigraha,
        })
        print(f"[{i}/{len(verse_words)}] {ref} {word}", file=sys.stderr)

    header_block = (
        "Valmiki Ramayana -- Balakanda, Sarga 1 (R_1,001.001-079)\n"
        "Combined sandhi_splitter.py + samasa_splitter.py analysis\n"
        f"Total words: {len(verse_words)}  |  "
        f"Words with a sandhi split found: {n_sandhi}  |  "
        f"Words with a samasa decomposition found: {n_samasa}\n"
        "\n"
        "Basis: 'Sandhi Rule(s)'/'Sandhi Pada-Vigraha' come directly from\n"
        "sandhi_splitter.py's own niyama-rule citations and dictionary\n"
        "validation (apte_dictionary.sqlite). 'Samasa Type' is an explicitly\n"
        "heuristic structural guess (samasa_splitter.py's guess_samasa_type,\n"
        "NOT a substitute for real meaning-based classification);\n"
        "'Samasa Pada-Vigraha' is only populated when a dictionary-verified\n"
        "2+-member decomposition survived this pipeline's false-positive\n"
        "guards (see combined_splitter.py's module docstring). A '-' means\n"
        "'checked, nothing found' -- never a guess presented as a result.\n"
        "\n"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header_block)
        f.write(format_table(report_rows))
        f.write("\n")

    print(f"\nWrote {output_path} ({len(verse_words)} words, "
          f"{n_sandhi} with sandhi splits, {n_samasa} with samasa decompositions)",
          file=sys.stderr)


if __name__ == "__main__":
    main()
