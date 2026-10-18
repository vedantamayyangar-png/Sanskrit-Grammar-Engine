#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression checks for the Sarga-1/Sarga-6 audit (run from the project folder: python3 regression_feedback_cases.py).

Each check states the expected outcome. Cases marked OPEN are known remaining errors and are reported
as XFAIL (expected to fail) rather than failing the run, so the list documents what is still wrong.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from combined_splitter import CombinedSplitter
from samasa_classifier import SamasaClassifier
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate as tl

cs = CombinedSplitter()
sc = SamasaClassifier(cs._pa())
pa = cs._pa()
results = []

def check(name, ok, open_=False):
    results.append((name, ok, open_))

# 1. fused-token splitting: no false splits of validated compounds / verbs
for t in ["satyavākyaḥ", "nihatāmitraḥ", "dharmātmanā", "vakṣyāmi", "bāhlīkaiḥ"]:
    check(f"no split: {t}", cs.split_fused_token(t) is None)
check("split nāvidvān -> na + avidvān", (cs.split_fused_token("nāvidvān") or {}).get("pieces") == ["na", "avidvān"])
check("visarga-lopa tuṣṭādhanaiḥ -> tuṣṭāḥ + dhanaiḥ (not a compound)", (cs.split_fused_token("tuṣṭādhanaiḥ") or {}).get("pieces") == ["tuṣṭāḥ", "dhanaiḥ"])
check("split caiva -> ca + eva", (cs.split_fused_token("caiva") or {}).get("pieces") == ["ca", "eva"])
check("split tasyābhiṣekasambhārān -> tasya + …", ((cs.split_fused_token("tasyābhiṣekasambhārān") or {}).get("pieces") or [""])[0] == "tasya")

# 2. classifier: finite verbs and phantom nañ are not compounds
for w in ["vidyate", "mahīyate", "dṛśyate", "ātmā", "āhave", "ātmānam"]:
    check(f"not compound: {w}", sc.analyse(w, scheme="iast") is None)
check("control nañ kept: arogaḥ", (sc.analyse("arogaḥ", scheme="iast") or {}).get("type") == "नञ्तत्पुरुषः")

# 3. samāsa types
def typ(w):
    r = sc.analyse(w, scheme="iast"); return r and r["type"]
check("sarvasaṃgrahaḥ is बहुव्रीहिः", typ("sarvasaṃgrahaḥ") == "बहुव्रीहिः")
check("dīrghāyuṣaḥ is बहुव्रीहिः", typ("dīrghāyuṣaḥ") == "बहुव्रीहिः")
check("satyavādinaḥ is उपपदतत्पुरुषः", typ("satyavādinaḥ") == "उपपदतत्पुरुषः")
check("mahātejāḥ is बहुव्रीहिः", typ("mahātejāḥ") == "बहुव्रीहिः")

# 4. morphology: neuter a-stem nouns, not phantom laṅ verbs
for w in ["vākyam", "vanam", "phalam"]:
    rd = pa.analyse(w, scheme="iast", max_readings=1)
    check(f"noun first: {w}", bool(rd) and rd[0]["type"] == "noun")

# OPEN: known remaining errors (XFAIL)
check("OPEN vedavit has a samāsa analysis", sc.analyse("vedavit", scheme="iast") is not None, open_=True)
check("OPEN satyavākya-type stem lookup in compound_split", False, open_=True)

n_ok = n_bad = n_x = 0
for name, ok, open_ in results:
    if open_:
        n_x += 1; print(f"XFAIL  {name}")
    elif ok:
        n_ok += 1; print(f"PASS   {name}")
    else:
        n_bad += 1; print(f"FAIL   {name}")
print(f"\n{n_ok} passed, {n_bad} failed, {n_x} known open")
sys.exit(1 if n_bad else 0)
