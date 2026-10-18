#!/usr/bin/env python3
"""
build_grammar_json.py
======================
Builds a per-verse grammar-analysis JSON matching the structure of the
"comprehensive 10-component template" (COMPONENT_1_padaccheda through
COMPONENT_10_chandas, plus a COMPONENT_11_quiz note) -- by calling
directly into samasa_splitter.py's engine, which must be importable
(same directory, or on PYTHONPATH).

WHAT THIS SCRIPT CAN AUTO-GENERATE, RELIABLY, FROM THE ENGINE
--------------------------------------------------------------
- COMPONENT_1 (padaccheda)  -- word list, compounds shown hyphenated,
  glosses filled from the CDSL dictionaries where available.
- COMPONENT_4 (karaka)      -- karta/karma via analyze_karaka(), plus a
  best-effort karana/adhikarana/sambandha via guess_case() on every
  other tagged word (instrumental / locative / genitive respectively).
- COMPONENT_7 (pratyaya)    -- verb root+suffix via resolve_pratyaya(),
  matup stem+suffix via resolve_matup(), and a basic stem+vibhakti
  breakdown for any other word whose ending matches CASE_ENDING_TABLE_WX.
- COMPONENT_8 (sandhi)      -- every real junction restoration, with the
  actual Panini sutra citation the underlying sandhi engine already
  carries.
- COMPONENT_9 (samasa)      -- every compound split found, tagged with
  guess_samasa_type()'s structural guess.

WHAT THIS SCRIPT DELIBERATELY DOES **NOT** FABRICATE
-----------------------------------------------------
COMPONENT_2 (anvaya), COMPONENT_3's meaning/etymology/role prose,
COMPONENT_5 (full declension paradigms), COMPONENT_6 (full verb
conjugation paradigms), and COMPONENT_10 (chandas scansion + alankara)
require actual Sanskrit scholarly judgment -- a meter's mātrā count, a
rhetorical figure, a full 7-case x 3-number paradigm -- that string
-processing over CDSL dictionary data cannot responsibly manufacture.
This script emits those sections as an explicit, clearly-labeled
skeleton (word ids and surface forms filled in so a human reviewer, or
a follow-up authoring pass, has exactly the scaffold needed) rather
than inventing plausible-looking but unverified content. COMPONENT_11
is never data at all in the template itself -- it's generated at
render time from the other components -- so this script does not
attempt it either.

USAGE
-----
Single verse, ad hoc:
    python build_grammar_json.py --verse "tapaḥsvādhyāyanirataṃ tapasvī vāgvidāṃ varam" \\
        --verse2 "nāradaṃ paripapraccha vālmīkir munipuṅgavam" \\
        --id 1.1.1 --kanda 1 --sarga 1 --number 1 \\
        --cdsl mw.txt ap90.txt --out shloka_1.1.1.json

Batch, from a GRETIL-format corpus file (same format samasa_splitter.py's
--corpus mode uses):
    python build_grammar_json.py --corpus bala_1_1-5.txt --kanda 1 --sarga 1 \\
        --verse-start 1 --verse-end 5 --cdsl mw.txt ap90.txt \\
        --out-dir shloka_json/
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    from indic_transliteration import sanscript
except ImportError:
    sys.exit("Missing dependency: indic_transliteration. "
             "Install with: pip install indic_transliteration")

try:
    import samasa_splitter as ss
except ImportError:
    sys.exit("Cannot find samasa_splitter.py -- put this script in the same "
             "directory as samasa_splitter.py, or add it to PYTHONPATH.")


# --------------------------------------------------------------------------- #
# Sanskrit names for cases/numbers, used to label auto-generated karaka and
# pratyaya entries in the same terms the template itself uses.
# --------------------------------------------------------------------------- #
CASE_NAME_SA = {
    "nominative": "प्रथमा", "accusative": "द्वितीया", "instrumental": "तृतीया",
    "dative": "चतुर्थी", "ablative": "पञ्चमी", "genitive": "षष्ठी",
    "locative": "सप्तमी",
}
NUMBER_NAME_SA = {"singular": "एकवचनम्", "dual": "द्विवचनम्", "plural": "बहुवचनम्"}

SAMASA_TYPE_LABEL_SA = {
    "tatpuruSa": "tatpuruṣasamāsaḥ",
    "karmaXAraya": "karmadhārayasamāsaḥ",
    "bahuvrIhi": "bahuvrīhisamāsaḥ",
    "xvanxva": "dvandvasamāsaḥ",
    "avyayIBAva": "avyayībhāvasamāsaḥ",
}


def sanskrit_type_label(type_guess_wx_style):
    """
    guess_samasa_type() (samasa_splitter.py's core engine) returns a
    handful of FIXED heuristic strings that mix WX-encoded Sanskrit
    fragments with English commentary (e.g. "tatpuruSa / karmaXAraya /
    bahuvrIhi -- uncertain (needs meaning/dictionary glosses to
    disambiguate)", or an f-string embedding a raw WX morpheme like
    "tatpuruSa (upasarga-compound: 'vi-' is one of the 22 traditional
    upasargas)"). Rather than a naive substring replace (which leaves
    the English commentary and any un-mapped WX fragment untouched),
    this matches each of the six known return SHAPES from
    guess_samasa_type() directly and produces a clean IAST-Sanskrit
    label for each -- Devanagari-ized downstream by combine_grammar_
    json.py's to_deva(), same as every other Sanskrit-content field in
    this pipeline. If the engine's set of possible return strings ever
    changes, the final `else` branch is the fallback and should be
    revisited.
    """
    t = type_guess_wx_style
    m = re.match(r"^tatpuruSa \(upasarga-compound: '([^']+)-'", t)
    if m:
        return f"tatpuruṣasamāsaḥ (upasargapūrvapadam: '{m.group(1)}-')"
    m = re.match(r"^na\u00f1-tatpuruSa \(negative compound: '([^']+)-'", t)
    if m:
        return f"nañtatpuruṣasamāsaḥ ('{m.group(1)}-' niṣedhārthakam pūrvapadam)"
    m = re.match(r"^NOT a samasa -- '([^']+)' is a particle", t)
    if m:
        return f"na samāsaḥ -- '{m.group(1)}' nipātaḥ; kevalaṃ sandhiyuktam"
    if t.startswith("not a compound"):
        return "na samāsaḥ (ekapadam eva)"
    if t.startswith("dvigu"):
        return "dvigusamāsaḥ (sandigdham)"
    if t.startswith("avyayibhava"):
        return "avyayībhāvasamāsaḥ (sandigdham)"
    if t.startswith("tatpuruSa / karmaXAraya / bahuvrIhi"):
        return ("tatpuruṣaḥ / karmadhārayaḥ / bahuvrīhiḥ "
                "(arthāvadhāraṇena vinā niścetum aśakyam)")
    return t  # fallback: unrecognized shape, leave as-is for visibility


def word_gloss(sp, word_iast, scheme="iast"):
    g = ss.get_gloss(sp, word_iast, scheme=scheme)
    return g or ""


def build_padaccheda(sp, verse_lines, scheme="iast"):
    """
    COMPONENT_1: one entry per printed word. A word that samasa-split
    or matup-resolved is shown hyphenated (matching the template's own
    convention, e.g. "तपः-स्वाध्याय-निरतम्"); an ordinary word is shown
    as its sandhi-restored citation form (not the raw as-printed form,
    which may still carry a neighboring word's sandhi effect, e.g.
    "vālmīkir" before a following voiced consonant -- see
    restore_tokens()).
    """
    entries = []
    for line in verse_lines:
        samasa = line.get("samasa", {})
        matup = line.get("matup", {})
        fused = line.get("fused_sandhi", {})
        tokens = line["text"].split()
        restored = ss.restore_tokens(sp, tokens, scheme=scheme)
        for tok, restored_tok in zip(tokens, restored):
            if tok in samasa:
                members = samasa[tok]["members"]
                display = "-".join(members)
            elif tok in matup:
                mt = matup[tok]
                stem = mt["stem"] or restored_tok
                display = f"{stem}-{mt['pratyaya']}"
            elif tok in fused:
                members = fused[tok]["members"]
                display = "-".join(members)
            else:
                display = restored_tok
            gloss = word_gloss(sp, restored_tok, scheme=scheme)
            entries.append({
                "word": display,
                "surface": restored_tok,
                "meaning_sa": "",
                "meaning_en": gloss,
                "meaning_ta": "",
            })
    return entries


def build_sandhi(verse_lines):
    """COMPONENT_8: every junction where a real restoration happened,
    with the actual sutra citation the sandhi engine already carries."""
    entries = []
    for line in verse_lines:
        for j in line.get("junctions", []):
            t1, t2 = j["pair"]
            best = j["candidates"][0] if j["candidates"] else None
            if not best or best["left"] == t1:
                continue
            entries.append({
                "location": f"{best['left']} + {t2}",
                "original": f"{t1} {t2}",
                "result": f"{best['left']} + {t2}",
                "sandhi_type": best["sandhi_type"],
                "sandhi_rule_sa": best["sutra"],
                "confidence": "dictionary-verified" if best["dict_backed"] else "phonology-only",
            })
        for tok, r in line.get("fused_sandhi", {}).items():
            entries.append({
                "location": tok,
                "original": tok,
                "result": " + ".join(r["members"]),
                "sandhi_type": r.get("type_guess", ""),
                "sandhi_rule_sa": "",
                "confidence": r["confidence"],
            })
    return entries


def build_samasa(sp, verse_lines, scheme="iast"):
    """COMPONENT_9: every compound split found."""
    entries = []
    for line in verse_lines:
        for tok, r in line.get("samasa", {}).items():
            members = r["members"]
            meanings = [f"{m}: {word_gloss(sp, m, scheme=scheme) or '?'}" for m in members]
            entries.append({
                "word": tok,
                "compound_type": sanskrit_type_label(r["type_guess"]),
                "breakdown": " + ".join(members),
                "meaning": "; ".join(meanings),
                "meaning_ta": "",
                "confidence": r["confidence"],
            })
    return entries


def build_pratyaya(sp, verse_lines, scheme="iast"):
    """COMPONENT_7: verb root+suffix, matup stem+suffix, and a basic
    stem+vibhakti breakdown for any other word matching a known ending."""
    entries = []
    for line in verse_lines:
        pratyaya = line.get("pratyaya", {})
        matup = line.get("matup", {})
        samasa = line.get("samasa", {})
        fused = line.get("fused_sandhi", {})
        tokens = line["text"].split()
        restored = ss.restore_tokens(sp, tokens, scheme=scheme)
        for tok, tok_clean in zip(tokens, restored):
            if tok in pratyaya:
                p = pratyaya[tok]
                if p.get("ambiguous"):
                    root_disp = " / ".join(p["root"]) + " (sandigdham)"
                else:
                    root_disp = p["root"] or "?"
                entries.append({
                    "word": tok_clean,
                    "breakdown": f"{root_disp} + {p['pratyaya']}",
                    "pratyaya_name": p["pratyaya"],
                    "confidence": "resolved" if p["resolved"] else "recognized only",
                })
            elif tok in matup:
                mt = matup[tok]
                stem = mt["stem"] or "?"
                entries.append({
                    "word": tok_clean,
                    "breakdown": f"{stem} + {mt['pratyaya']}",
                    "pratyaya_name": "matvarthīyaḥ vat/mat-pratyayaḥ",
                    "confidence": "resolved" if mt["resolved"] else "recognized only",
                })
            elif tok in fused:
                # A token like "caikapriyadarśanaḥ" (ca + eka + priya +
                # darśana, particle-fused with no space in the source)
                # has already been correctly explained by the sandhi/
                # samasa engine as PARTICLE + WORD, not one opaque word
                # of its own -- see build_sandhi's separate handling of
                # the same "fused_sandhi" data. Run the case-ending
                # heuristic on the actual word (the last member, after
                # the leading particle), not on the raw garbled token,
                # which would otherwise show a case-analysis for a
                # string that still has "ca"/"vā"/etc. stuck to its front.
                members = fused[tok]["members"]
                real_word = members[-1] if len(members) > 1 else tok_clean
                wx = sp._to_wx(real_word, getattr(sanscript, scheme.upper()))
                case_info = ss.guess_case(sp, wx)
                if case_info:
                    case, number, _note = case_info
                    case_sa = CASE_NAME_SA.get(case, case)
                    number_sa = NUMBER_NAME_SA.get(number, number)
                    entries.append({
                        "word": real_word,
                        "breakdown": f"prakṛtiḥ + {case_sa}-{number_sa} vibhaktiḥ",
                        "pratyaya_name": f"{case_sa} vibhaktiḥ ({number_sa})",
                        "confidence": "heuristic (ending-match only, "
                                      "particle-prefix stripped)",
                    })
            elif tok not in samasa:
                # ordinary declined word -- try a basic case-ending match
                wx = sp._to_wx(tok_clean, getattr(sanscript, scheme.upper()))
                case_info = ss.guess_case(sp, wx)
                if case_info:
                    case, number, _note = case_info
                    case_sa = CASE_NAME_SA.get(case, case)
                    number_sa = NUMBER_NAME_SA.get(number, number)
                    entries.append({
                        "word": tok_clean,
                        "breakdown": f"prakṛtiḥ + {case_sa}-{number_sa} vibhaktiḥ",
                        "pratyaya_name": f"{case_sa} vibhaktiḥ ({number_sa})",
                        "confidence": "heuristic (ending-match only)",
                    })
    return entries


def build_karaka(sp, verse_lines, scheme="iast"):
    """COMPONENT_4: karta/karma via analyze_karaka(), plus a best-effort
    karana/adhikarana/sambandha via guess_case() on every other tagged
    word. analyze_karaka() expects already sandhi-restored tokens (it
    does not restore internally -- see restore_tokens()), and karta/
    karma can span across pada-lines within one verse, so every line's
    tokens are restored and concatenated before calling it once for the
    whole verse."""
    all_tokens = []
    for line in verse_lines:
        tokens = line["text"].split()
        all_tokens.extend(ss.restore_tokens(sp, tokens, scheme=scheme))
    entries = ss.analyze_karaka(sp, all_tokens, scheme=scheme)

    karta = karma = None
    karana, adhikarana, sambandha = [], [], []
    for e in entries:
        role = e["role"] or ""
        if role.startswith("karta"):
            karta = e["token"]
        elif role.startswith("karma"):
            karma = e["token"]
        elif e["case"]:
            case = e["case"][0]
            if case == "instrumental":
                karana.append(e["token"])
            elif case == "locative":
                adhikarana.append(e["token"])
            elif case == "genitive" and "qualifies" not in role:
                sambandha.append(e["token"])

    return {
        "karta": karta or "",
        "karma": karma or "",
        "karana": ", ".join(karana) if karana else "इदं श्लोके प्रत्यक्षं करणपदं नास्ति",
        "adhikarana": ", ".join(adhikarana) if adhikarana else "इदं श्लोके प्रत्यक्षम् अधिकरणपदं नास्ति",
        "sambandha": ", ".join(sambandha) if sambandha else "",
        "_note": "karta/karma via case-ending heuristic + proper-noun head "
                 "preference (see analyze_karaka in samasa_splitter.py); "
                 "karana/adhikarana/sambandha are a first-pass guess from "
                 "instrumental/locative/genitive case-tagged words, not a "
                 "semantic-role analysis -- verify before relying on these.",
    }


def build_skeleton_component(component_num, name_sa, verse_lines, needs):
    """A clearly-labeled placeholder for a component that needs real
    Sanskrit scholarly authorship (see module docstring)."""
    words = []
    for line in verse_lines:
        words.extend(line["text"].split())
    return {
        "description": f"{component_num}. {name_sa} -- NOT AUTO-GENERATED. {needs}",
        "status": "SKELETON_NEEDS_MANUAL_AUTHORING",
        "words_in_verse": [w.strip("'") for w in words],
    }


def build_verse_json(sp, verse_key, verse_lines, meta):
    kanda, sarga, shloka = verse_key
    verse_id = f"{kanda}.{sarga}.{shloka}"
    # Traditional daṇḍa punctuation: single "।" after every pada but the
    # last, double "॥" plus the kanda-sarga-shloka number after the last.
    padas = [line["text"] for line in verse_lines]
    verse_text = " । ".join(padas) + f" ॥ {kanda}-{sarga}-{shloka} ॥"

    doc = {
        "note": "Auto-generated by build_grammar_json.py from samasa_splitter.py's "
                "engine. Components 1/4/7/8/9 are mechanically derived and "
                "dictionary-checked; components 2/3/5/6/10 are unauthored "
                "skeletons -- see each component's own description.",
        "grammar_components": "१. पदच्छेदः | २. अन्वयः (skeleton) | ३. पद-विग्रहः (skeleton) "
                               "| ४. कारकः | ५. शब्दरूपाणि (skeleton) | ६. धातुरूपाणि (skeleton) "
                               "| ७. प्रत्ययाः | ८. सन्धिः | ९. समासः | १०. छन्दस्/अलङ्कारः (skeleton)",
        "shloka_metadata": {
            "id": verse_id,
            "number": meta.get("number"),
            "iast": verse_text,
            "kanda": meta.get("kanda_name", str(kanda)),
            "sarga": sarga,
        },
        "COMPONENT_1_padaccheda": {
            "description": "१. पदच्छेदः -- Word segmentation. Compounds/matup "
                            "words shown hyphenated. meaning_en from CDSL "
                            "glosses where found; meaning_sa/meaning_ta left "
                            "for manual completion.",
            "padaccheda": build_padaccheda(sp, verse_lines),
        },
        "COMPONENT_2_anvaya": build_skeleton_component(
            2, "अन्वयः", verse_lines,
            "Prose word-order reconstruction requires genuine syntactic "
            "judgment -- not derivable from sandhi/samasa splitting alone."),
        "COMPONENT_3_padavigraha": build_skeleton_component(
            3, "पद-विग्रहः", verse_lines,
            "Full per-word pos/gender/number/case/meaning/etymology/role "
            "needs manual grammatical analysis; see COMPONENT_1 for the "
            "segmented word list and COMPONENT_4/7 for what IS derived."),
        "COMPONENT_4_karaka": {
            "description": "४. कारकः -- karta/karma via the tool's karaka "
                            "heuristic; karana/adhikarana/sambandha are a "
                            "first-pass case-tag guess, not verified.",
            "karaka": build_karaka(sp, verse_lines),
        },
        "COMPONENT_5_shabdarupani": build_skeleton_component(
            5, "शब्दरूपाणि", verse_lines,
            "Full 7-case x 3-number declension paradigms are not generated "
            "by this tool (it only recognizes/reverses individual endings, "
            "not the full paradigm) -- needs manual authoring per stem."),
        "COMPONENT_6_dhaturupani": build_skeleton_component(
            6, "धातुरूपाणि", verse_lines,
            "Full verb conjugation paradigms are not generated by this "
            "tool -- needs manual authoring per root/lakara."),
        "COMPONENT_7_pratyaya": {
            "description": "७. प्रत्ययाः -- verb/matup suffix resolution is "
                            "dictionary-verified; plain declension entries "
                            "are a heuristic ending-match only (see "
                            "confidence field on each entry).",
            "pratyaya": build_pratyaya(sp, verse_lines),
        },
        "COMPONENT_8_sandhi": {
            "description": "८. सन्धिः -- every junction where a real "
                            "restoration happened, with the Panini sutra "
                            "citation from the underlying sandhi engine.",
            "sandhi": build_sandhi(verse_lines),
        },
        "COMPONENT_9_samasa": {
            "description": "९. समासः -- every compound split found, "
                            "confidence-tagged (\u2713 dictionary-verified vs "
                            "\u25e6 phonology-only -- see samasa_splitter.py's "
                            "own report legend).",
            "samasa": build_samasa(sp, verse_lines),
        },
        "COMPONENT_10_chandas": build_skeleton_component(
            10, "छन्दस्/अलङ्कारः", verse_lines,
            "Meter scansion and rhetorical-figure identification require "
            "genuine prosodic/literary judgment -- needs manual authoring."),
    }
    return doc


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cdsl", nargs="+", required=True,
                         help="mw.txt ap90.txt (or just one) -- required for "
                              "dictionary validation and gloss lookup.")
    parser.add_argument("--scheme", default="iast")

    single = parser.add_argument_group("Single-verse mode")
    single.add_argument("--verse", help="Verse text (one or more padas, "
                         "space-separated words; use --verse2/--verse3 for "
                         "additional padas of the same shloka)")
    single.add_argument("--verse2")
    single.add_argument("--verse3")
    single.add_argument("--id", help="e.g. 1.1.1")
    single.add_argument("--kanda", type=int)
    single.add_argument("--sarga", type=int)
    single.add_argument("--number", type=int)
    single.add_argument("--kanda-name", default=None)
    single.add_argument("--out", help="Output JSON path (single-verse mode)")

    batch = parser.add_argument_group("Batch mode (GRETIL-format corpus file)")
    batch.add_argument("--corpus", help="Path to a GRETIL-format source file "
                        "(same format as samasa_splitter.py's --corpus)")
    batch.add_argument("--verse-start", type=int)
    batch.add_argument("--verse-end", type=int)
    batch.add_argument("--out-dir", help="Directory to write one "
                        "shloka_<id>.json per verse (batch mode)")

    args = parser.parse_args()

    sp = ss.SamasaSplitter()
    n = sp.load_cdsl_dictionaries(args.cdsl)
    print(f"[loaded {n} unique stems from {', '.join(args.cdsl)}]", file=sys.stderr)
    sp.load_verb_roots(args.cdsl)
    sp.load_proper_nouns(args.cdsl)
    sp.load_compound_headwords(args.cdsl)
    sp.load_glosses(args.cdsl)

    if args.corpus:
        if not (args.out_dir and args.kanda and args.sarga
                and args.verse_start and args.verse_end):
            sys.exit("Batch mode needs --corpus --kanda --sarga --verse-start "
                      "--verse-end --out-dir")
        verses = ss.parse_gretil_verses(
            args.corpus, kanda=args.kanda, sarga=args.sarga,
            verse_start=args.verse_start, verse_end=args.verse_end)
        if not verses:
            sys.exit("No verses matched the given kanda/sarga/verse-range filters.")
        report, _stats = ss.analyze_verse_corpus(sp, verses, mode="both")
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for v in report:
            k, s, sh = map(int, v["verse"].split("."))
            doc = build_verse_json(sp, (k, s, sh), v["lines"],
                                    {"number": sh, "kanda_name": args.kanda_name or str(k)})
            out_path = out_dir / f"shloka_{v['verse']}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(doc, f, ensure_ascii=False, indent=2)
            print(f"[wrote {out_path}]", file=sys.stderr)
        return

    if args.verse:
        if not (args.id and args.kanda and args.sarga and args.out):
            sys.exit("Single-verse mode needs --verse --id --kanda --sarga --out")
        pada_texts = [p for p in (args.verse, args.verse2, args.verse3) if p]
        # Build a minimal in-memory "verses" dict + reuse analyze_verse_corpus
        # by faking the parsed-verse structure it expects.
        shloka_num = int(args.id.split(".")[-1])
        key = (args.kanda, args.sarga, shloka_num)
        verses = {key: pada_texts}
        report, _stats = ss.analyze_verse_corpus(sp, verses, mode="both")
        v = report[0]
        doc = build_verse_json(sp, key, v["lines"],
                                {"number": args.number or shloka_num,
                                 "kanda_name": args.kanda_name or str(args.kanda)})
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        print(f"[wrote {args.out}]", file=sys.stderr)
        return

    sys.exit("Provide either --verse (single-verse mode) or --corpus (batch mode). "
              "See --help.")


if __name__ == "__main__":
    main()
