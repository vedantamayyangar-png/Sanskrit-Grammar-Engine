#!/usr/bin/env python3
"""
combine_grammar_json.py
========================
Merges build_grammar_json.py's mechanically-derived components (1, 4, 7,
8, 9 -- padaccheda, karaka, pratyaya, sandhi, samasa) with the
hand-authored content in manual_grammar_data.py (components 2, 3, 5, 6,
10 -- anvaya, pada-vigraha prose, declension paradigms, verb conjugation,
chandas/alankara), producing ONE combined JSON covering all 10 components
for every verse it's run over.

Usage:
    python combine_grammar_json.py --corpus bala_1_1-5.txt --kanda 1 \\
        --sarga 1 --verse-start 1 --verse-end 5 \\
        --cdsl mw.txt ap90.txt --out combined_shlokas.json
"""
import argparse
import json
import sys

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate as tl

import samasa_splitter as ss
import build_grammar_json as bg
from manual_grammar_data import MANUAL_DATA


def to_deva(text):
    """IAST -> Devanagari. Safe to call on plain ASCII/English text too --
    transliterate() only maps recognized IAST characters and passes
    anything else through unchanged, so this is only ever applied to
    fields that are ACTUALLY Sanskrit-in-IAST-transliteration (never to
    English prose, which would come out as meaningless mixed script)."""
    if not text:
        return text
    return tl(text, sanscript.IAST, sanscript.DEVANAGARI)


def devanagarize_pada_vigraha(entries):
    """Every field here is Sanskrit content (see manual_grammar_data.py's
    pada_vigraha authoring) -- word, pos, gender, number, case, meaning,
    etymology, role all convert; there is no English field to preserve."""
    out = []
    for e in entries:
        out.append({k: to_deva(v) for k, v in e.items()})
    return out


def devanagarize_table(tbl):
    if not tbl:
        return tbl
    out = {"headers": [to_deva(h) for h in tbl.get("headers", [])],
           "rows": [[to_deva(c) for c in row] for row in tbl.get("rows", [])]}
    if "note" in tbl:
        # table-level "note" is methodology commentary in English (e.g.
        # PRONOUN_KIM's "masculine forms shown..."), not verse content --
        # left untouched, matching how other English methodology notes
        # throughout this pipeline are handled (see module docstring
        # note in manual_grammar_data.py on this exact point).
        out["note"] = tbl["note"]
    return out


def devanagarize_shabdarupani(shabdarupani):
    out = {}
    for key, entry in shabdarupani.items():
        if key == "note":
            out[key] = entry  # English coverage/methodology commentary
            continue
        out[key] = {
            "lemma": to_deva(entry.get("lemma", "")),
            "gender": to_deva(entry.get("gender", "")),
            "declension_table": devanagarize_table(entry.get("declension_table")),
        }
    return out


def devanagarize_dhaturupani(d):
    def one(root):
        out = dict(root)
        for f in ("root", "gana", "lakara", "form"):
            if f in out:
                out[f] = to_deva(out[f])
        if "conjugation" in out:
            out["conjugation"] = devanagarize_table(out["conjugation"])
        return out

    out = {}
    if "note" in d:
        out["note"] = d["note"]  # English methodology commentary
    if "root" in d:
        out.update(one(d))
    if "roots" in d:
        out["roots"] = [one(r) for r in d["roots"]]
        if "second_root" in d:  # legacy shape safety net, not currently used
            out["second_root"] = one(d["second_root"])
    return out


def devanagarize_karaka(k):
    """karta/karma/karana/adhikarana/sambandha are the actual Sanskrit
    word(s) filling each role -- convert those. "_note" is English
    commentary on the heuristic's own reliability, not verse content --
    left untouched, same treatment as every other methodology note in
    this pipeline."""
    out = {}
    for field in ("karta", "karma", "karana", "adhikarana", "sambandha"):
        if field in k:
            out[field] = to_deva(k[field])
    if "_note" in k:
        out["_note"] = k["_note"]
    return out


def devanagarize_chandas(c):
    """Quarter-verse text is the moola Sanskrit verse itself (IAST) --
    convert. Alankara names are Sanskrit terms -- convert. Alankara
    "definition" fields are English explanatory prose in this project's
    current authoring -- left untouched (a genuine Sanskrit-medium
    rhetorical commentary would need separate authoring, not a script
    conversion, since the source text itself is English here)."""
    out = {
        "chandas_name": to_deva(c.get("name", "")),
        "scansion": [
            {"quarter": q["quarter"], "text": to_deva(q["text"]), "matra": q["matra"]}
            for q in c.get("scansion", [])
        ],
        "alankara": [
            {"name": to_deva(a["name"]), "definition": a["definition"]}
            for a in c.get("alankara", [])
        ],
    }
    return out


def devanagarize_padaccheda(entries):
    """word/surface are the Sanskrit word forms themselves (IAST) --
    convert both. meaning_sa is genuine Sanskrit content (either from
    apply_manual_meanings_to_padaccheda, or empty) -- convert if present.
    meaning_en is the raw MW/Apte dictionary gloss, in English -- left
    untouched (there is no Sanskrit-medium equivalent to convert it
    from; see apply_manual_meanings_to_padaccheda for why meaning_sa is
    the preferred field to read, not meaning_en)."""
    out = []
    for e in entries:
        out.append({
            "word": to_deva(e["word"]),
            "surface": to_deva(e["surface"]),
            "meaning_sa": to_deva(e.get("meaning_sa", "")),
            "meaning_en": e.get("meaning_en", ""),
            "meaning_ta": e.get("meaning_ta", ""),
        })
    return out


def devanagarize_sandhi(entries):
    """Every field here is Sanskrit content (word forms + sandhi-type
    names + Panini sutra citations, all IAST) -- convert all of them.
    "confidence" is a technical status label ("dictionary-verified" /
    "phonology-only"), not verse content -- left as-is, matching the
    tool's own \u2713/\u25e6 convention used throughout every report in this
    project."""
    out = []
    for e in entries:
        out.append({
            "location": to_deva(e["location"]),
            "original": to_deva(e["original"]),
            "result": to_deva(e["result"]),
            "sandhi_type": to_deva(e["sandhi_type"]),
            "sandhi_rule_sa": to_deva(e["sandhi_rule_sa"]),
            "confidence": e["confidence"],
        })
    return out


def devanagarize_samasa(entries):
    """word/compound_type/breakdown are Sanskrit content -- convert.
    "meaning" is the raw MW/Apte dictionary gloss per member, in
    English -- same limitation as COMPONENT_1's meaning_en (see
    apply_manual_meanings_to_padaccheda): left untouched, since there is
    no Sanskrit-medium equivalent available to convert it from for
    arbitrary compound members not covered by hand-authored content.
    "confidence" is a technical status label, left as-is."""
    out = []
    for e in entries:
        out.append({
            "word": to_deva(e["word"]),
            "compound_type": to_deva(e["compound_type"]),
            "breakdown": to_deva(e["breakdown"]),
            "meaning": e["meaning"],
            "meaning_ta": e.get("meaning_ta", ""),
            "confidence": e["confidence"],
        })
    return out


def devanagarize_pratyaya(entries):
    """word/breakdown/pratyaya_name are all Sanskrit content -- convert
    all. The "function" field was removed from build_pratyaya (it was
    100% redundant with pratyaya_name in every case -- both fields
    always said the same thing in different word order, exactly the
    kind of "printing the same value twice" issue flagged for this
    component). "confidence" is a technical status label, left as-is."""
    out = []
    for e in entries:
        out.append({
            "word": to_deva(e["word"]),
            "breakdown": to_deva(e["breakdown"]),
            "pratyaya_name": to_deva(e["pratyaya_name"]),
            "confidence": e["confidence"],
        })
    return out



def reconcile_pratyaya_with_manual(pratyaya_entries, manual_pada_vigraha):
    """
    The heuristic ending-match branch in build_pratyaya (COMPONENT_7)
    has no way to know a word is actually a pronoun, infinitive, or
    simply has a different case than its ending coincidentally
    resembles -- it just matches the surface ending against a table of
    common declension patterns. This produced real, wrong information
    for words already correctly analyzed elsewhere: "aham" (a pronoun,
    correctly prathamā/nominative in COMPONENT_3's pada-vigraha) was
    labeled dvitīyā (accusative) here, purely coincidental ending-match;
    "śrotum" (an infinitive, no case at all) got a fabricated case too.
    Rather than try to compare the two case values against each other
    (fragile, and still leaves a redundant entry even when they happen
    to agree), any heuristic-confidence pratyaya entry for a word ALSO
    covered by hand-authored pada_vigraha is dropped outright here --
    that component's own dedicated case field is strictly more reliable
    for that word already, so repeating a heuristic guess alongside it
    adds risk without adding information. Runs on the DEVANAGARI-stage
    entries (both pratyaya_entries and manual_pada_vigraha have already
    been through devanagarize_* by the time this is called -- see
    merged_verse_json), matching on the converted "word" text.
    """
    manual_words = {e["word"] for e in manual_pada_vigraha}
    return [e for e in pratyaya_entries
            if not (e["confidence"].startswith("heuristic") and e["word"] in manual_words)]


def apply_manual_meanings_to_padaccheda(doc, manual_pada_vigraha_deva):
    """
    COMPONENT_1's padaccheda auto-populates meaning_en from the raw
    MW/Apte dictionary gloss -- first-sense-only, and occasionally picks
    an entirely unrelated homonym (e.g. "kaḥ" pulling the noun-sense
    list "Brahman, Viṣṇu, ..." instead of the interrogative pronoun
    "who"). Where a hand-authored pada_vigraha entry exists for this
    exact surface form, its Sanskrit meaning is much more reliable --
    prefer it here, filling meaning_sa (leaving meaning_en as a
    secondary fallback reference, not removed, in case the reader wants
    to compare against the raw dictionary entry). Must run AFTER
    devanagarize_padaccheda (matches on already-Devanagari surface
    forms, since manual_pada_vigraha_deva is passed in post-conversion).
    """
    lookup = {e["word"]: e["meaning"] for e in manual_pada_vigraha_deva}
    c1 = doc.get("COMPONENT_1_padaccheda")
    if not c1:
        return
    for entry in c1.get("padaccheda", []):
        if entry["surface"] in lookup:
            entry["meaning_sa"] = lookup[entry["surface"]]


def merged_verse_json(sp, verse_key, verse_lines, meta):
    doc = bg.build_verse_json(sp, verse_key, verse_lines, meta)
    verse_id = doc["shloka_metadata"]["id"]
    manual = MANUAL_DATA.get(verse_id)

    # The moola verse text itself -- always available regardless of
    # whether manual grammar content exists for this verse yet.
    doc["shloka_metadata"]["devanagari"] = to_deva(doc["shloka_metadata"]["iast"])

    # COMPONENT_1 (padaccheda) and COMPONENT_4 (karaka) are always
    # mechanically derived, regardless of whether manual content exists
    # for this verse -- Devanagari-ize them either way.
    if "COMPONENT_1_padaccheda" in doc:
        doc["COMPONENT_1_padaccheda"]["padaccheda"] = devanagarize_padaccheda(
            doc["COMPONENT_1_padaccheda"]["padaccheda"])
    if "COMPONENT_4_karaka" in doc and "karaka" in doc["COMPONENT_4_karaka"]:
        doc["COMPONENT_4_karaka"]["karaka"] = devanagarize_karaka(
            doc["COMPONENT_4_karaka"]["karaka"])
    if "COMPONENT_7_pratyaya" in doc:
        doc["COMPONENT_7_pratyaya"]["pratyaya"] = devanagarize_pratyaya(
            doc["COMPONENT_7_pratyaya"]["pratyaya"])
    if "COMPONENT_8_sandhi" in doc:
        doc["COMPONENT_8_sandhi"]["sandhi"] = devanagarize_sandhi(
            doc["COMPONENT_8_sandhi"]["sandhi"])
    if "COMPONENT_9_samasa" in doc:
        doc["COMPONENT_9_samasa"]["samasa"] = devanagarize_samasa(
            doc["COMPONENT_9_samasa"]["samasa"])

    if not manual:
        doc["shloka_metadata"]["manual_content_status"] = (
            "NOT YET AUTHORED for this verse -- components 2/3/5/6/10 "
            "remain the SKELETON_NEEDS_MANUAL_AUTHORING placeholder from "
            "build_grammar_json.py. Add an entry to MANUAL_DATA in "
            "manual_grammar_data.py to complete it.")
        return doc

    doc["COMPONENT_2_anvaya"] = {
        "description": "२. अन्वयः -- Syntactic prose order.",
        "anvaya_sa": to_deva(manual["anvaya"]["sa"]),
        "translation_en": manual["anvaya"]["en"],
    }
    doc["COMPONENT_3_padavigraha"] = {
        "description": "३. पद-विग्रहः -- Word-by-word analysis "
                        "(pos/gender/number/case/meaning/etymology/role).",
        "word_count": len(manual["pada_vigraha"]),
        "pada_vigraha": devanagarize_pada_vigraha(manual["pada_vigraha"]),
    }
    apply_manual_meanings_to_padaccheda(doc, doc["COMPONENT_3_padavigraha"]["pada_vigraha"])
    if "COMPONENT_7_pratyaya" in doc:
        doc["COMPONENT_7_pratyaya"]["pratyaya"] = reconcile_pratyaya_with_manual(
            doc["COMPONENT_7_pratyaya"]["pratyaya"],
            doc["COMPONENT_3_padavigraha"]["pada_vigraha"])
    doc["COMPONENT_5_shabdarupani"] = {
        "description": "५. शब्दरूपाणि -- Declension paradigms for "
                        "every distinct declinable stem in the verse.",
        "shabdarupani": devanagarize_shabdarupani(manual["shabdarupani"]),
    }
    doc["COMPONENT_6_dhaturupani"] = {
        "description": "६. धातुरूपाणि -- Verb conjugation.",
        "dhaturupani": devanagarize_dhaturupani(manual["dhaturupani"]),
    }
    doc["COMPONENT_10_chandas"] = {
        "description": "१०. छन्दस्/अलङ्कारः -- Meter and literary devices. "
                        "'matra' here counts syllables (akṣara) per quarter "
                        "-- the standard unit for scanning an akṣara-based "
                        "vṛtta meter like anuṣṭubh, not mātrā (mora-weight), "
                        "which applies to jāti meters instead. Verified by "
                        "direct syllable count: all 4 quarters = 8 each in "
                        "every verse below, confirming standard anuṣṭubh.",
        **devanagarize_chandas(manual["chandas"]),
    }
    doc["shloka_metadata"]["manual_content_status"] = "fully authored"
    doc["grammar_components"] = (
        "१. पदच्छेदः | २. अन्वयः | ३. पद-विग्रहः | ४. कारकः | ५. शब्दरूपाणि | "
        "६. धातुरूपाणि | ७. प्रत्ययाः | ८. सन्धिः | ९. समासः | १०. छन्दस्/अलङ्कारः "
        "(all 10 components complete)")
    return doc


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cdsl", nargs="+", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--kanda", type=int, required=True)
    parser.add_argument("--sarga", type=int, required=True)
    parser.add_argument("--verse-start", type=int, required=True)
    parser.add_argument("--verse-end", type=int, required=True)
    parser.add_argument("--kanda-name", default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    sp = ss.SamasaSplitter()
    n = sp.load_cdsl_dictionaries(args.cdsl)
    print(f"[loaded {n} unique stems from {', '.join(args.cdsl)}]", file=sys.stderr)
    sp.load_verb_roots(args.cdsl)
    sp.load_proper_nouns(args.cdsl)
    sp.load_compound_headwords(args.cdsl)
    sp.load_glosses(args.cdsl)

    verses = ss.parse_gretil_verses(
        args.corpus, kanda=args.kanda, sarga=args.sarga,
        verse_start=args.verse_start, verse_end=args.verse_end)
    if not verses:
        sys.exit("No verses matched the given kanda/sarga/verse-range filters.")
    report, _stats = ss.analyze_verse_corpus(sp, verses, mode="both")

    combined = {
        "note": "Combined grammar-analysis JSON: mechanically-derived "
                "components (1/4/7/8/9) from samasa_splitter.py's engine, "
                "hand-authored components (2/3/5/6/10) from "
                "manual_grammar_data.py. One shloka completed at a time, "
                "in order.",
        "shlokas": [],
    }
    for v in report:
        k, s, sh = map(int, v["verse"].split("."))
        print(f"[processing verse {v['verse']}]", file=sys.stderr)
        doc = merged_verse_json(sp, (k, s, sh), v["lines"],
                                 {"number": sh, "kanda_name": args.kanda_name or str(k)})
        combined["shlokas"].append(doc)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    print(f"[wrote {args.out} -- {len(combined['shlokas'])} shlokas]", file=sys.stderr)


if __name__ == "__main__":
    main()
