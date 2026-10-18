#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_lexicon_index.py - build lexicon_index.json (SLP1 headword -> gender/POS tags) from apte_dictionary.sqlite.
Tags: m f n = gender, a = adjective, i = indeclinable/avyaya, v = verb root (dhatu), p = pronoun.
Usage: python build_lexicon_index.py [apte_dictionary.sqlite] [out_dir]
"""
import json, os, re, sqlite3, sys
HERE = os.path.dirname(os.path.abspath(__file__))

def _first_existing(paths):
    for p in paths:
        if p and os.path.isfile(p):
            return p
    return None

# apte_dictionary.sqlite: argument, then this folder, then ../sandhi, then the project tree
db = _first_existing([sys.argv[1] if len(sys.argv) > 1 else None,
                      os.path.join(HERE, "apte_dictionary.sqlite"),
                      os.path.join(HERE, "..", "sandhi", "apte_dictionary.sqlite"),
                      os.path.join(HERE, "..", "apte_dictionary.sqlite")])
if db is None:
    sys.exit("apte_dictionary.sqlite not found. Put it next to this script or pass its path:\n"
             "    python build_lexicon_index.py D:\\path\\to\\apte_dictionary.sqlite")
# output: the folder pada_analyser.py reads lexicon_index.json from (its DICT_DIR)
if len(sys.argv) > 2:
    out = sys.argv[2]
else:
    try:
        sys.path.insert(0, HERE)
        from pada_analyser import DICT_DIR as out
    except Exception:
        out = HERE
os.makedirs(out, exist_ok=True)
AB = re.compile(r"<ab>([a-z\.\s]+?)</ab>")
SKD_G = (("m", re.compile(r"(?:^|\s)puM(?:\s|,|\.)")), ("n", re.compile(r"(?:^|\s)klI(?:\s|,|\.)")),
         ("f", re.compile(r"(?:^|\s)strI(?:\s|,|\.)")), ("a", re.compile(r"(?:^|\s)tri(?:\s|,|\.)")))
lex = {}
def citation_gender(k1):
    """Heuristic only: Apte/SKD cite nouns in nominative singular (naraH m., phalam n., latA f.)."""
    if k1.endswith(("H", "aH")): return "m"
    if k1.endswith("am"): return "n"
    if k1.endswith(("A", "I", "U")): return "f"
    return "n"
def add(k, tags):
    if k:
        lex[k] = "".join(sorted(set(lex.get(k, "")) | set(tags)))
c = sqlite3.connect(db)
for src, k1, body, stem in c.execute("select e.source_dict,e.k1_raw,e.body_text,s.stem from stems s join entries e on e.entry_id=s.entry_id where e.is_crossref=0"):
    head = body.split("\n", 1)[1][:260] if "\n" in body else body[:260]
    tags = set()
    if src == "ap90":
        for ab in AB.findall(head):
            ab = ab.strip().lower()
            if ab in ("m.", "m"): tags.add("m")
            elif ab in ("f.", "f"): tags.add("f")
            elif ab in ("n.", "n"): tags.add("n")
            elif ab in ("a.", "a"): tags.add("a")
            elif ab.startswith("ind"): tags.add("i")
            elif ab.startswith("pron"): tags.add("p")
            elif ab in ("c.", "p.", "a. p.") or ab.startswith(("c1", "c2")): pass
        if re.search(r"\{c\d+\}|<ab>(?:P|A|U)\.</ab>", head) and not tags & set("mfna"):
            tags.add("v")
        if not tags:
            tags.add(citation_gender(k1))
    else:
        for t, rx in SKD_G:
            if rx.search(head[:80]): tags.add(t)
        if not tags: tags.add(citation_gender(k1))
    if stem.endswith("M") and len(stem) > 3:      # neuter citation form vAkyaM -> also the stem vAkya (and vAkyam)
        add(stem[:-1], tags | {"a"})        # citation form is neuter, but participles/adjectives (rataM) take all genders
        add(stem[:-1] + "m", tags | {"a"})
    if "p" in tags:
        tags.add("a")          # pronouns/numerals (eka, sarva, ...) are valid compound members
    add(stem, tags)
p = os.path.join(out, "lexicon_index.json")
json.dump(lex, open(p, "w", encoding="utf-8"), ensure_ascii=False)
print(len(lex), "headwords ->", p)
