"""Sanity check: every verse has at least as many rows as GRETIL tokens (periphrastic perfects count as one word)."""
import importlib, glob
from translit import load_verses

vs = load_verses("sarga1_iast.txt")
ALL = {}
for f in sorted(glob.glob("d0*.py")):
    ALL.update(importlib.import_module(f[:-3]).V)
short = 0
for k in sorted(vs):
    if k not in ALL:
        print(f"verse {k}: MISSING"); short += 1; continue
    rows = ALL[k][1]
    for r in rows:
        assert len(r) == 6, (k, r[0])
    ntok = len(vs[k]["tokens"]) - " ".join(vs[k]["iast"]).count("ām āsa")
    if len(rows) < ntok:
        print(f"verse {k}: {ntok} words but only {len(rows)} rows"); short += 1
print(f"{len(ALL)} verses, {sum(len(r) for _, r in ALL.values())} rows, {short} problems")
