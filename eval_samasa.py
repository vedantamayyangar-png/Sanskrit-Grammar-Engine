"""Score samasa_classifier.py (detection + type) against the gold rows, 1:1-aligned words only."""
import json, sys, re, importlib, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path[:0] = [os.path.join(PROJ, "03_Sandhi_and_Samasa_Tools", "morphology"),
                os.path.join(PROJ, "03_Sandhi_and_Samasa_Tools", "samasa"),
                os.path.join(PROJ, "03_Sandhi_and_Samasa_Tools", "sandhi"),
                os.path.join(HERE, "..", "working_files"), HERE]
from samasa_classifier import SamasaClassifier  # noqa
from translit import to_dev  # noqa
import compare_with_gold as C  # noqa
sysjson = sys.argv[1]
sc = SamasaClassifier()
GOLD = {}
for f in sorted(os.listdir(os.path.join(HERE, "..", "working_files"))):
    if re.fullmatch(r"d0\d\.py", f):
        GOLD.update(importlib.import_module(f[:-3]).V)
SYS = {int(k): v for k, v in json.load(open(sysjson, encoding="utf-8")).items()}
S = collections.Counter(); errs = collections.defaultdict(list)
for v in GOLD:
    rows = GOLD[v][1]; toks = []; srows = []
    for L in SYS[v]:
        for t, r in zip(L["tokens"], L["rows"]):
            toks.append(t); srows.append(r)
    for tix, rix in C.align([to_dev(t) for t in toks], rows):
        if len(tix) != 1 or len(rix) != 1:
            continue
        g = rows[rix[0]]; gcomp = C.is_compound_row(g)
        r = srows[tix[0]]
        cit = r["token_split"][-1] if r.get("token_split") else r["citation_form"]
        res = sc.analyse(cit, scheme="iast")
        if gcomp and res:
            S["tp"] += 1
            gt = C.gold_samasa_type(g[5])
            st = {"नञ्तत्पुरुषः": "तत्पुरुषः", "उपपदतत्पुरुषः": "तत्पुरुषः", "नञ्बहुव्रीहिः": "बहुव्रीहिः"}.get(res["type"], res["type"])
            S["typed"] += 1
            if st == gt:
                S["type_ok"] += 1
            else:
                errs[f"type gold {gt} / system {st}"].append(f"{v}: {g[0]} ({res['reason'][:40]})")
        elif gcomp:
            S["fn"] += 1; errs["missed"].append(f"{v}: {g[0]}")
        elif res:
            S["fp"] += 1; errs["invented"].append(f"{v}: {g[0]} → {'+'.join(res['members'])}")
p = S["tp"] / (S["tp"] + S["fp"]); rc = S["tp"] / (S["tp"] + S["fn"])
print(f"recall {S['tp']}/{S['tp']+S['fn']} = {100*rc:.1f}%  precision {S['tp']}/{S['tp']+S['fp']} = {100*p:.1f}%  "
      f"type {S['type_ok']}/{S['typed']} = {100*S['type_ok']/S['typed']:.1f}%")
if len(sys.argv) > 2:
    for k in sorted(errs, key=lambda k: -len(errs[k])):
        print(f"--- {k} ({len(errs[k])})"); print("\n".join(errs[k][:int(sys.argv[2])]))
