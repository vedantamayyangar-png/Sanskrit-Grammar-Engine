"""Run the combined sandhi+samasa pipeline (CombinedSplitter.analyze_pada_line) over one sarga and
cache the raw output as JSON, so compare_with_gold.py can be re-run without re-splitting.

Usage:
  python run_combined_splitter.py [--tools DIR] [--source FILE] [--kanda 1] [--sarga 1]
                                  [--verses 1-79] [--out FILE]
"""
import argparse, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))  # ...\Sanskrit & Tamil Scholarship

ap = argparse.ArgumentParser()
ap.add_argument("--tools", default=os.path.join(PROJ, "03_Sandhi_and_Samasa_Tools"))
ap.add_argument("--source", default=os.path.join(PROJ, "01_Ramayana_Project", "source_texts", "sa_rAmAyaNa.txt"))
ap.add_argument("--kanda", type=int, default=1)
ap.add_argument("--sarga", type=int, default=1)
ap.add_argument("--verses", default=None, help="e.g. 1-10 (default: all)")
ap.add_argument("--out", default=os.path.join(HERE, "system_output_sarga1.json"))
a = ap.parse_args()

sys.path[:0] = [os.path.join(a.tools, "sandhi"), os.path.join(a.tools, "samasa")]
from samasa_splitter import parse_gretil_verses  # noqa: E402
from combined_splitter import CombinedSplitter  # noqa: E402

verses = parse_gretil_verses(a.source, kanda=a.kanda, sarga=a.sarga)
lo, hi = (map(int, a.verses.split("-")) if a.verses else (1, 10 ** 6))
cs = CombinedSplitter()
out = {}
t0 = time.time()
for key in sorted(verses):
    k, s, v = key
    if not (lo <= v <= hi):
        continue
    lines = []
    for line in verses[key]:
        toks = line.split()
        if toks:
            lines.append({"tokens": toks, "rows": cs.analyze_pada_line(toks)})
    out[v] = lines
    print(f"verse {v} done ({time.time() - t0:.0f}s)", flush=True)
with open(a.out, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)
print("wrote", a.out)
