#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_sarga1_report_v2.py
==============================
Rebuild of generate_sarga1_report.py around the CORRECT pipeline
(CombinedSplitter.analyze_pada_line -- see combined_splitter.py) after
direct human review of v1's output found ~90%+ of its "Sandhi Rule(s)"
column wrong. Root cause: v1 called sandhi_splitter.split_word_recursive
on each ISOLATED GRETIL pada-token one at a time -- a within-a-single-
fused-word boundary finder, wrong when given an already-complete word
with no internal junction to find (it manufactures a fake one instead of
reporting "no sandhi here"). sandhi/SKILL.md already documented this
exact failure mode before v1 was written.

This version instead checks sandhi PAIRWISE, between each two adjacent
GRETIL tokens exactly as the source text already segments them (via
samasa_splitter.py's own restore_word_boundary, the real forward
Sandhi.sandhi() engine as oracle) -- the architecture sandhi/SKILL.md
itself prescribes. Samasa decomposition still runs per-word, but on
each word's own CITATION form (post sandhi-restoration), not on a
fragment manufactured by the wrong single-word split.

Verified against the same words a human reviewer flagged in v1's output
(see combined_splitter.py's own module docstring and analyze_pada_line's
docstring for the specific before/after cases) before this was trusted
enough to regenerate the full-corpus report.

Runs entirely from local project files -- no network/cloud calls.

USAGE
-----
    D:\\python\\python.exe generate_sarga1_report_v2.py [output.txt]
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
from build_ramayana_input import parasavarna_normalize  # noqa: E402
from samasa_splitter import parse_gretil_verses  # noqa: E402
from combined_splitter import CombinedSplitter  # noqa: E402

SOURCE_TEXT = os.path.normpath(os.path.join(
    HERE, "..", "..", "01_Ramayana_Project", "source_texts", "sa_rAmAyaNa.txt"))
DEFAULT_OUTPUT = os.path.join(HERE, "sarga1_sandhi_samasa_report_v2.txt")

COL_WIDTHS = [22, 14, 22, 30, 26, 30]
HEADERS = ["Word", "Verse", "Sandhi Rule(s)", "Sandhi Pada-Vigraha",
           "Samasa Type", "Samasa Pada-Vigraha"]


def _deva(iast_text):
    return parasavarna_normalize(tl(iast_text, sanscript.IAST, sanscript.DEVANAGARI))


def build_report_rows(cs):
    verses = parse_gretil_verses(SOURCE_TEXT, kanda=1, sarga=1)
    rows = []
    n_sandhi = 0
    n_samasa = 0
    for key in sorted(verses.keys()):
        kanda, sarga, verse_num = key
        ref = f"R_{kanda},{sarga:03d}.{verse_num:03d}"
        for pada_line in verses[key]:
            tokens = pada_line.split()
            if not tokens:
                continue
            for r in cs.analyze_pada_line(tokens):
                word_deva = _deva(r["word"])
                if r["sandhi_rule"] is not None:
                    n_sandhi += 1
                    sandhi_name = r["sandhi_rule"]
                    left_deva = _deva(r["sandhi_vigraha"][0])
                    right_deva = _deva(r["sandhi_vigraha"][1])
                    sandhi_vigraha = f"{left_deva} + {right_deva}"
                else:
                    sandhi_name = "-"
                    sandhi_vigraha = "-"
                if r["samasa"] is not None:
                    n_samasa += 1
                    samasa_type = r["samasa"]["type_guess"]
                    if samasa_type.startswith("tatpuruSa / karmaXAraya / bahuvrIhi"):
                        samasa_type = "uncertain (see samasa_splitter.py guess_samasa_type)"
                    samasa_vigraha = " + ".join(r["samasa"]["members"])
                else:
                    samasa_type = "-"
                    samasa_vigraha = "-"
                rows.append({
                    "word": word_deva, "verse": ref,
                    "sandhi_name": sandhi_name, "sandhi_vigraha": sandhi_vigraha,
                    "samasa_name": samasa_type, "samasa_vigraha": samasa_vigraha,
                })
        print(f"[done] {ref}", file=sys.stderr)
    return rows, n_sandhi, n_samasa


def _wrap(text, width):
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
    rows, n_sandhi, n_samasa = build_report_rows(cs)

    header_block = (
        "Valmiki Ramayana -- Balakanda, Sarga 1 (R_1,001.001-079)\n"
        "Combined sandhi_splitter.py + samasa_splitter.py analysis -- v2\n"
        "(rebuilt around pairwise word-boundary restoration after v1's\n"
        "per-isolated-token approach was found ~90%+ wrong by direct review)\n"
        f"Total words: {len(rows)}  |  "
        f"Words with a sandhi restoration found: {n_sandhi}  |  "
        f"Words with a samasa decomposition found: {n_samasa}\n"
        "\n"
        "Basis: 'Sandhi Rule(s)'/'Sandhi Pada-Vigraha' come from\n"
        "samasa_splitter.py's restore_word_boundary, checking sandhi BETWEEN\n"
        "each pair of adjacent words exactly as the source text (GRETIL)\n"
        "already segments them, using the real forward Sandhi.sandhi() engine\n"
        "as oracle plus apte_dictionary.sqlite for dictionary validation.\n"
        "'Samasa Type' is an explicitly heuristic structural guess\n"
        "(samasa_splitter.py's guess_samasa_type, NOT a substitute for real\n"
        "meaning-based classification); 'Samasa Pada-Vigraha' is only\n"
        "populated when a dictionary-verified 2+-member decomposition\n"
        "survived this pipeline's false-positive guards. A '-' means\n"
        "'checked, nothing found' -- never a guess presented as a result.\n"
        "\n"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header_block)
        f.write(format_table(rows))
        f.write("\n")

    print(f"\nWrote {output_path} ({len(rows)} words, "
          f"{n_sandhi} with sandhi restorations, {n_samasa} with samasa decompositions)",
          file=sys.stderr)


if __name__ == "__main__":
    main()
