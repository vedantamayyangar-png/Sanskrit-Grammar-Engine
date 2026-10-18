"""Baseline: what the tools that existed BEFORE this pass can say about each word's morphology
(samasa_splitter.guess_case / looks_like_verb_form / resolve_pratyaya, and
sandhi_splitter._stem_after_common_inflection) — for an honest before/after comparison."""
import argparse, json, os, sys
PROJ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
T = os.path.join(PROJ, "03_Sandhi_and_Samasa_Tools")
sys.path[:0] = [os.path.join(T, "sandhi"), os.path.join(T, "samasa")]
import sandhi_splitter  # noqa
from combined_splitter import CombinedSplitter  # noqa
from samasa_splitter import guess_case  # noqa
from indic_transliteration import sanscript  # noqa
from indic_transliteration.sanscript import transliterate as tl  # noqa
from build_ramayana_input import parasavarna_normalize  # noqa

ap = argparse.ArgumentParser(); ap.add_argument("system_json"); ap.add_argument("--out", required=True)
a = ap.parse_args()
cs = CombinedSplitter(); sp = cs.sp
out = {}
for v, lines in json.load(open(a.system_json, encoding="utf-8")).items():
    out[v] = []
    for line in lines:
        rows = []
        for r in line["rows"]:
            c = r["citation_form"]
            deva = parasavarna_normalize(tl(c, sanscript.IAST, sanscript.DEVANAGARI))
            is_verb = bool(sp.resolve_pratyaya(c, scheme="iast")) or sp.looks_like_verb_form(c, scheme="iast") \
                or sp.looks_like_upasarga_verb(c, scheme="iast")
            g = guess_case(sp, sp._to_wx(c, sanscript.IAST))
            stem = sandhi_splitter._stem_after_common_inflection(deva)
            rows.append({"is_verb": is_verb, "case": list(g[:2]) if g else None, "stem": stem})
        out[v].append(rows)
json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
