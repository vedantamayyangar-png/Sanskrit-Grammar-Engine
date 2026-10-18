"""Run pada_analyser over the citation forms produced by run_combined_splitter.py, one reading per
printed token (best reading first, alternatives kept), for compare_with_gold.py --morph."""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pada_analyser import PadaAnalyser  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("system_json")
ap.add_argument("--out", required=True)
a = ap.parse_args()
pa = PadaAnalyser()
sysout = json.load(open(a.system_json, encoding="utf-8"))
out = {}
for v, lines in sysout.items():
    out[v] = []
    for line in lines:
        rows = []
        for r in line["rows"]:
            rd = pa.analyse(r["citation_form"], scheme="iast", max_readings=3)
            best = rd[0] if rd else None
            m = {"readings": rd}
            if best:
                m["is_verb"] = best["type"] == "verb"
                if best["type"] == "noun":
                    m["case"] = [{1: "nominative", 2: "accusative", 3: "instrumental", 4: "dative", 5: "ablative",
                                  6: "genitive", 7: "locative", 8: "vocative"}[best["case"]],
                                 {"e": "singular", "d": "dual", "b": "plural"}[best["num"]]]
                    m["stem"] = best["stem"]
                elif best["type"] == "verb":
                    m["stem"] = best["dhatu"]
                else:
                    m["stem"] = best["stem"]
            rows.append(m)
        out[v].append(rows)
json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("wrote", a.out)
