#!/usr/bin/env python3
"""Evaluate pada_analyser + samasa_classifier against compound_gold_UNVERIFIED.json.

Usage (from the folder that holds pada_analyser.py, samasa_classifier.py, transliterate.py,
the four data JSON files and apte_dictionary.sqlite):
    python eval_compound_gold.py compound_gold_UNVERIFIED.json

Matching: member stems are compared after stripping trailing case/visarga/anusvāra signs
(तपः == तपस्). Rows are only meaningful once the gold file has been verified by a scholar.
"""
import json, re, sys
from pada_analyser import PadaAnalyser
from samasa_classifier import SamasaClassifier

TAIL = re.compile(r'[ःंँ्िीुूृेैोौाम्स्न्र्]+$')
def stem(x): return TAIL.sub('', x.strip())

def main(path):
    gold = json.load(open(path, encoding='utf-8'))['rows']
    sc = SamasaClassifier(PadaAnalyser())
    ok = none = 0
    for g in gold:
        r = sc.analyse(g['word'], scheme='deva')
        got = r['members'] if r else None
        if not got:
            none += 1
            print('NONE ', g['word'], '| gold', g['members']); continue
        if [stem(x) for x in got] == [stem(x) for x in g['members']]:
            ok += 1
        else:
            print('WRONG', g['word'], '| got', got, '| gold', g['members'])
    print(f"exact: {ok}/{len(gold)}   no analysis: {none}   (gold is UNVERIFIED)")

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'compound_gold_UNVERIFIED.json')
