#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_10component_quality_report.py
=========================================
Produces the 10-component grammar quality-report XLSX for a verse range
of Valmiki Ramayana, Balakanda Sarga 1 -- one row per Component-1 word,
one column per grammar component (Padaccheda, Anvaya, Pada-vigraha,
Karaka, Sabdarupani, Dhaturupani, Pratyaya, Sandhi, Samasa, Chandas),
plus a Quality flag (amber cell fill) and a final Internal/External
provenance column.

DATA SOURCES (all internal to the project folder -- see provenance column)
-----------------------------------------------------------------------
- Verses 1.1.1-1.1.5: `sanskrit_grammar_engine.py`'s own Library-only
  10-component treatise (`generate_treatise_record`) -- real, previously
  Library-verified data (SOURCE_ASSERTION / COMPUTED_EVIDENCE), reused
  as-is and reformatted into this report's row/column shape. Rule
  citations already embedded in that engine's own output
  (`rulebook_citation` fields) are carried through unchanged.
- Verses 1.1.6-1.1.10: no Library evidence exists for these verses
  anywhere in the project (the v8.1/comprehensive template files are
  explicitly scoped to 1.1.1-1.1.5) -- computed instead via this
  project's own sandhi/samasa tools (`combined_splitter.py`,
  `samasa_splitter.py`), marked with an amber Quality flag as
  DELIBERATELY LESS CERTAIN than the Library-sourced verses 1-5.
  Components with no computational tool available at all (Anvaya,
  Pada-vigraha's full etymology/morphology, Sabdarupani, Dhaturupani,
  full Chandas scansion) are left as "-" (GAP) rather than fabricated.
- Rule citations: `citation_lookup.py` (same folder), hand-verified
  against `sandhi_rulebook.json` / `samasah_rulebook.json` /
  `vibhakti_prakarana_rulebook.json` -- see that module's own docstring.
- Sabdarupani (Component 5) paradigm references: `vibhakti_reference.py`
  loads `04_Laghu_Siddhanta_Kaumudi/vibhakti_table.json`, now itself
  upgraded (this pass) from `sabdamanjari_vibhakti_tables.json` (a
  page-cited Śabdamañjarī-textbook extraction) for 5 of its 6
  previously-"External" classes -- see `vibhakti_reference.py`'s own
  module docstring.
- Dhaturupani (Component 6) root citations: `dhatu_manjari_citation()`
  (this file, below), reading `Dhatu-Manjari.json` (2,259-root
  Dhatupatha) and `Dhatu-Lakara.json` (gana names only) -- see the block
  comment above `DHATU_MANJARI_ROOT_BASEINDEX`.

DEVANAGARI-ONLY
----------------
Every grammar-concept label (sandhi/samasa type names, karaka roles,
pratyaya names) is rendered in Devanagari via `citation_lookup.py`,
never as the IAST/WX strings this project's tools return internally.

OUTPUT
------
By default written to
`E:\\Sanskrit & Tamil Scholarship\\01_Ramayana_Project\\quality_reports\\`
(created if missing), filename `10component_report_1.1.<start>-<end>.xlsx`.
Both the destination and the filename are overridable -- see USAGE.

USAGE (all flags optional; run with no arguments for the original
verses-1-5 Library-verified report, unchanged)
-----
    D:\\python\\python.exe generate_10component_quality_report.py ^
        --input-file "E:\\Sanskrit & Tamil Scholarship\\01_Ramayana_Project\\source_texts\\sa_rAmAyaNa.txt" ^
        --verse-start 6 --verse-end 10 ^
        --output-file "10component_report_1.1.6-10.xlsx" ^
        --format xlsx

    --input-file   GRETIL-format IAST source text. Only consulted for verses
                   beyond --verse-end 5 (the Library-verified ceiling);
                   verses 1-5 always come from this project's own Library
                   data regardless of this flag. Default: this project's own
                   01_Ramayana_Project/source_texts/sa_rAmAyaNa.txt.
    --verse-start  First verse number in Sarga 1 (default 1).
    --verse-end    Last verse number in Sarga 1 (default 5 -- the
                   Library-verified ceiling; pass a higher number
                   explicitly to also pull in the less-certain computed
                   range, e.g. --verse-end 10).
    --output-file  Bare filename -> written into quality_reports\\ above;
                   a path with a directory -> used exactly as given
                   (directory created if missing). Extension is normalized
                   to match --format. Default:
                   10component_report_1.1.<start>-<end>.<format>.
    --format       xlsx (default; the only format implemented today --
                   see OUTPUT_WRITERS below).

    Run `D:\\python\\python.exe generate_10component_quality_report.py --help`
    for the full, current flag reference (kept in argparse itself, not
    duplicated here, so it can't drift out of sync with this docstring).
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SANDHI_TOOLS = os.path.normpath(os.path.join(HERE, "..", "..", "03_Sandhi_and_Samasa_Tools"))
SANDHI_DIR = os.path.join(SANDHI_TOOLS, "sandhi")
SAMASA_DIR = os.path.join(SANDHI_TOOLS, "samasa")
SOURCE_TEXT = os.path.normpath(os.path.join(
    HERE, "..", "..", "01_Ramayana_Project", "source_texts", "sa_rAmAyaNa.txt"))
QUALITY_REPORTS_DIR = os.path.normpath(os.path.join(
    HERE, "..", "..", "01_Ramayana_Project", "quality_reports"))
DHATU_MANJARI_PATH = os.path.normpath(os.path.join(
    HERE, "..", "..", "04_Laghu_Siddhanta_Kaumudi", "Dhatu-Manjari.json"))
DHATU_LAKARA_PATH = os.path.normpath(os.path.join(
    HERE, "..", "..", "04_Laghu_Siddhanta_Kaumudi", "Dhatu-Lakara.json"))

for d in (HERE, SANDHI_DIR, SAMASA_DIR):
    if d not in sys.path:
        sys.path.insert(0, d)

import openpyxl  # noqa: E402
from openpyxl.styles import Font, Alignment, PatternFill  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402
from openpyxl.worksheet.hyperlink import Hyperlink  # noqa: E402
from indic_transliteration import sanscript  # noqa: E402
from indic_transliteration.sanscript import transliterate as tl  # noqa: E402

import sanskrit_grammar_engine as sge  # noqa: E402
import citation_lookup as cite  # noqa: E402
import vibhakti_reference as vibref  # noqa: E402
from build_ramayana_input import parasavarna_normalize  # noqa: E402
from samasa_splitter import parse_gretil_verses, restore_tokens, analyze_karaka, guess_case  # noqa: E402
from combined_splitter import CombinedSplitter  # noqa: E402

LIBRARY_VERSE_MAX = 5  # sanskrit_grammar_engine.py's fixed benchmark ceiling

# --------------------------------------------------------------------------- #
# Dhatu-Manjari.json / Dhatu-Lakara.json citation support (this session's
# new work) -- both files were added to 04_Laghu_Siddhanta_Kaumudi this
# session. Dhatu-Manjari.json is the full 2,259-root Dhatupatha reference
# (gana/pada/artha/lsk_sutra/sk_sutra per root, keyed by a stable
# `baseindex`); Dhatu-Lakara.json is a smaller, 30-root (3-per-gana) full
# tinanta-paradigm demonstration set, used here ONLY as an Internal,
# project-sourced table of each gana's traditional Devanagari name
# (its own `gana_name` field), not for conjugation forms -- this
# benchmark's actual conjugation tables already come from
# combined_shlokas_1-5_deva.json's lexical_evidence (Stage 35; unchanged
# by this pass).
#
# The four roots with finite/participial verb evidence in this 5-verse
# benchmark -- प्रच्छ् (परिपप्रच्छ, 1.1.1), भी (बिभ्यति, 1.1.4), इष्
# (इच्छामि, 1.1.5), अस् (असि, 1.1.5) -- were each hand-matched to their
# correct Dhatu-Manjari.json `baseindex`, verified by MEANING against the
# verse's own sense (Dhatu-Manjari lists 3 homonymous अस् roots across
# ganas 1/2/4 and 3 homonymous इष् roots across ganas 4/6/9 -- an exact
# root-string match alone is not enough): अस् "असि" = existential "to be"
# (भुवि, gana 2, अदादिः) matching the deva.json-asserted gana already on
# this cell, not gana-1 "to go/shine" or gana-4 "to throw"; इष् "इच्छामि"
# = "to wish" (इच्छायाम्, gana 6, तुदादिः), not gana-4 "to go" or gana-9
# "to repeat, be persistent". Both selections were cross-checked against
# the gana sanskrit_grammar_engine.py's own COMPONENT_6 evidence already
# asserts for that cell (Stage 35's deva.json values) before being
# recorded here -- all four agree, confirming the match rather than
# silently trusting either source alone.
DHATU_MANJARI_ROOT_BASEINDEX = {
    "प्रच्छ्": "06.0149",  # ज्ञीप्सायाम्, गण ६ (तुदादिः) -- परिपप्रच्छ
    "भी": "03.0002",       # भये, गण ३ (जुहोत्यादिः) -- बिभ्यति
    "इष्": "06.0078",      # इच्छायाम्, गण ६ (तुदादिः) -- इच्छामि
    "अस्": "02.0060",      # भुवि, गण २ (अदादिः) -- असि
}

_PADA_DEVA = {"P": "परस्मैपदी", "A": "आत्मनेपदी", "U": "उभयपदी"}

_dhatu_manjari_cache = None
_dhatu_gana_names_cache = None


def _load_dhatu_manjari():
    global _dhatu_manjari_cache
    if _dhatu_manjari_cache is None:
        try:
            with open(DHATU_MANJARI_PATH, encoding="utf-8") as f:
                by_baseindex = {}
                for entry in json.load(f).get("data", []):
                    if isinstance(entry, dict) and entry.get("baseindex"):
                        by_baseindex[entry["baseindex"]] = entry
                _dhatu_manjari_cache = by_baseindex
        except (OSError, ValueError):
            _dhatu_manjari_cache = {}
    return _dhatu_manjari_cache


def _load_dhatu_gana_names():
    """gana (str, "1".."10") -> Devanagari gana name, read from
    Dhatu-Lakara.json's own per-entry `gana_name` field (a real project
    file, not hand-typed prose) -- its 30 roots (3 per gana) cover all
    ten ganas at least once."""
    global _dhatu_gana_names_cache
    if _dhatu_gana_names_cache is None:
        names = {}
        try:
            with open(DHATU_LAKARA_PATH, encoding="utf-8") as f:
                for entry in json.load(f).get("data", []):
                    if isinstance(entry, dict) and entry.get("gana") and entry.get("gana_name"):
                        names.setdefault(entry["gana"], entry["gana_name"])
        except (OSError, ValueError):
            pass
        _dhatu_gana_names_cache = names
    return _dhatu_gana_names_cache


def dhatu_manjari_citation(root):
    """Returns a citation-style suffix string for `root` (e.g.
    " -- धातुमञ्जरी-सन्दर्भः: गण ६ तुदादिः, परस्मैपदी, LSK-सूत्र 662"), or
    "" if `root` isn't in the hand-verified map above, its baseindex
    isn't found in Dhatu-Manjari.json this run, or it has no lsk_sutra
    recorded -- degrades silently, never fabricates a citation number."""
    baseindex = DHATU_MANJARI_ROOT_BASEINDEX.get(root)
    if not baseindex:
        return ""
    entry = _load_dhatu_manjari().get(baseindex)
    if not entry:
        return ""
    gana = entry.get("gana", "")
    gana_name = _load_dhatu_gana_names().get(gana, "")
    pada = _PADA_DEVA.get(entry.get("pada", ""), "")
    lsk = entry.get("lsk_sutra") or ""
    sk = entry.get("sk_sutra") or ""
    bits = [f"गण {gana}{' ' + gana_name if gana_name else ''}".strip()]
    if pada:
        bits.append(pada)
    if lsk:
        bits.append(f"LSK-सूत्र {lsk}")
    elif sk:
        bits.append(f"सि.कौ.-सूत्र {sk}")
    if not bits:
        return ""
    return " -- धातुमञ्जरी-सन्दर्भः: " + ", ".join(bits)


HEADERS = [
    "#", "श्लोकः (Verse)", "पदच्छेदः\n(Padaccheda)", "अन्वयः\n(Anvaya)",
    "पदविग्रहः\n(Pada-vigraha)", "कारकम्\n(Karaka)", "शब्दरूपाणि\n(Sabdarupani)",
    "धातुरूपाणि\n(Dhaturupani)", "प्रत्ययः\n(Pratyaya)", "सन्धिः\n(Sandhi)",
    "समासः\n(Samasa)", "छन्दः\n(Chandas)", "Verdict (mark here)",
    "Correction / Notes", "Source (Internal/External)",
]
COL_WIDTHS = [5, 12, 20, 26, 24, 22, 20, 20, 22, 30, 30, 22, 14, 36, 16]

AMBER = PatternFill(start_color="FFE599", end_color="FFE599", fill_type="solid")
HEADER_FILL = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")


def _canon(word_deva):
    """Strip Component-1's hyphen compound-boundary markers and any
    trailing punctuation, for matching a padaccheda word against a
    fused surface form elsewhere (sandhi/samasa/pratyaya evidence
    lists use the fused form, e.g. "वाग्विदाम्" not "वाग्-विदाम्")."""
    return word_deva.replace("-", "").strip()


_DEVANAGARI_RUN = re.compile(r"[ऀ-ॿ][ऀ-ॿ\s\-+०-९]*")
_NO_DEVANAGARI_PLACEHOLDER = "(मूलस्रोतसि आङ्ग्लभाषायाम् एव उपलब्धम्)"


def devanagari_only(text):
    """
    Keep ONLY the Devanagari-script portions of `text`, dropping any
    English/IAST commentary -- per explicit user instruction, every
    grammar-concept cell in this report must be Devanagari-only, never
    the bilingual free text several Library evidence fields actually
    contain (e.g. "tatpuruṣa-type compound", "root choice remains
    ambiguous"). Returns (cleaned_text, was_english_only) so the caller
    can amber-flag the cell rather than silently showing "-" as if no
    evidence existed at all when the SOURCE data itself was English-only.
    """
    if not text:
        return "-", False
    runs = [r.strip(" -+") for r in _DEVANAGARI_RUN.findall(str(text))]
    joined = " ".join(r for r in runs if r)
    if joined:
        return joined, False
    return _NO_DEVANAGARI_PLACEHOLDER, True


class ReportRow:
    def __init__(self, verse_ref, word):
        self.verse_ref = verse_ref
        self.word = word
        self.anvaya = "-"
        self.pada_vigraha = "-"
        self.karaka = "-"
        self.shabdarupani = "-"
        self.dhaturupani = "-"
        self.pratyaya = "-"
        self.sandhi = "-"
        self.samasa = "-"
        self.chandas = "-"
        self.amber_cols = set()  # column keys needing amber fill
        self.provenance = "Internal"
        self.shabdarupani_link = None  # 'Vibhakti Reference'!A<n> cell anchor, if classified


# --------------------------------------------------------------------------- #
# Verses 1-5: extract from sanskrit_grammar_engine.py's own Library data
# --------------------------------------------------------------------------- #
def build_rows_from_engine(engine, verse_num, samasa_cs):
    verse_id = f"1.1.{verse_num}"
    record = engine.generate_treatise_record(verse_id)
    comps = record["components"]
    ref = record["source_ref"]

    words = comps["COMPONENT_1_padaccheda"]["padaccheda"]
    rows = [ReportRow(ref, w) for w in words]
    canon_index = {_canon(w): i for i, w in enumerate(words)}

    # Component 2 (Anvaya) -- verse-level, shown on first row only.
    anvaya = comps.get("COMPONENT_2_anvaya", {})
    anvaya_text = anvaya.get("anvaya_sa") or (anvaya.get("saralartha") or {}).get("sa")
    if anvaya_text and rows:
        rows[0].anvaya, was_en = devanagari_only(anvaya_text)
        if was_en:
            rows[0].amber_cols.add("anvaya")

    # Component 3 (Pada-vigraha) -- real key is "matched_words" (an
    # "unmatched_words" sibling list also exists and is deliberately
    # left as "-" here, per the engine's own "not guessed" policy).
    c3 = comps.get("COMPONENT_3_padavigraha", {})
    for entry in c3.get("matched_words", []):
        if not isinstance(entry, dict):
            continue
        idx = canon_index.get(_canon(entry.get("word", "")))
        if idx is None:
            continue
        bits = []
        if entry.get("pos"):
            bits.append(entry["pos"])
        if entry.get("gender"):
            bits.append(entry["gender"])
        if entry.get("case"):
            bits.append(entry["case"])
        if entry.get("meaning"):
            bits.append(f"({entry['meaning']})")
        cell_raw = " ".join(b for b in bits if b) or entry.get("etymology", "")
        cell, was_en = devanagari_only(cell_raw)
        rows[idx].pada_vigraha = cell
        if was_en or entry.get("status") != "SOURCE_ASSERTION":
            rows[idx].amber_cols.add("pada_vigraha")

    # Component 4 (Karaka) -- built in two passes:
    #  Pass A: सुप्/तिङ्/अव्यय classification from Component 3's own pos/
    #  case fields (per explicit user direction: Padaccheda -- via
    #  Component 3's morphology -- is "a good starting point to identify
    #  if a word is sup-pratyaya or tiṅ-pratyaya"), then the vibhakti ->
    #  kāraka DEFAULT mapping (citation_lookup.classify_suptin /
    #  karaka_from_vibhakti) for every सुबन्त word -- not just the couple
    #  Component 4 itself asserts. तिङन्त (finite verb) and अव्यय
    #  (indeclinable) words are labelled as such and correctly excluded
    #  from having a kāraka at all.
    #  Pass B: Component 4's own real key is "roles" (not "karaka") --
    #  where the Library ITSELF names a SPECIFIC word as THE sentence's
    #  कर्ता/कर्म, that is genuine per-verse evidence and OVERRIDES pass
    #  A's generic default (and is not amber-flagged, unlike the default
    #  mapping, which is a traditional generalization applied uniformly).
    c3_by_canon = {_canon(entry.get("word", "")): entry for entry in c3.get("matched_words", [])
                   if isinstance(entry, dict)}
    word_case = {}  # row idx -> Library-given vibhakti name, for the Pass-B cross-check below
    for canon_word, idx in canon_index.items():
        entry = c3_by_canon.get(canon_word)
        if entry is None:
            continue
        case = entry.get("case")
        word_case[idx] = case
        suptin = cite.classify_suptin(entry.get("pos"), case)
        if suptin == "तिङन्तम्":
            rows[idx].karaka = "- (तिङन्तं क्रियापदम्, न कारकम्)"
        elif suptin == "अव्ययम्":
            rows[idx].karaka = "- (अव्ययम्, न कारकम्)"
        elif suptin == "सुबन्तम्":
            _, karaka_cell, definitive = cite.karaka_from_vibhakti(case)
            rows[idx].karaka = f"[सुबन्तम्] {karaka_cell}"
            if not definitive:
                rows[idx].amber_cols.add("karaka")

    # Vibhakti values that are flatly INCOMPATIBLE with a given Component-4
    # role -- e.g. कर्म requires द्वितीया (2.3.2 कर्मणि द्वितीया); a word
    # Component 3 itself marks प्रथमा cannot simultaneously be कर्म. Used
    # only to catch a genuine Library-internal inconsistency (see अहम्/
    # 1.1.5 below), not to second-guess every legitimate reading.
    INCOMPATIBLE_CASE_FOR_ROLE = {
        "karma": {"प्रथमा", "तृतीया", "चतुर्थी", "पञ्चमी", "षष्ठी", "सप्तमी", "सम्बोधन-प्रथमा"},
        "karta": {"द्वितीया", "चतुर्थी", "पञ्चमी", "षष्ठी", "सम्बोधन-प्रथमा"},
    }

    c4 = comps.get("COMPONENT_4_karaka", {})
    for role_key, info in c4.get("roles", {}).items():
        if not isinstance(info, dict) or info.get("status") != "present":
            continue
        deva_role, citation, known = cite.lookup_karaka_citation(role_key)
        for wid in info.get("word_ids", []):
            m = re.search(r"w0*(\d+)$", wid)
            if not m:
                continue
            idx = int(m.group(1)) - 1
            if not (0 <= idx < len(rows)):
                continue
            case_here = word_case.get(idx)
            bad_cases = INCOMPATIBLE_CASE_FOR_ROLE.get(role_key, set())
            if case_here in bad_cases:
                # Genuine Library-internal contradiction found (e.g.
                # 1.1.5's अहम् is Component-3-asserted प्रथमा but
                # Component-4-asserted कर्म -- कर्म REQUIRES द्वितीया per
                # 2.3.2; प्रथमा cannot be कर्म). Report BOTH readings and
                # flag amber rather than silently trusting either one.
                rows[idx].karaka = (
                    f"⚠ विरोधः: Library-रूपेण \"{deva_role}\" इति उक्तम्, "
                    f"किन्तु शब्दस्य विभक्तिः \"{case_here}\" इति Component-3-द्वारा एव कथितम् "
                    f"({case_here} \"{deva_role}\"-रूपेण असङ्गतम्, 2.3.2/2.3.46 प्रमाणेन) -- "
                    f"पुनः परीक्षणीयम्"
                )
                rows[idx].amber_cols.add("karaka")
                continue
            rows[idx].karaka = deva_role + (f" ({citation})" if citation else "") + " -- सन्दर्भानुसारेण Library-निश्चितम्"
            rows[idx].amber_cols.discard("karaka")  # Library-asserted, not a default guess
            if not known:
                rows[idx].amber_cols.add("karaka")

    # Component 5 (Sabdarupani) -- real key is "stems" (a dict keyed by
    # SLP1-ish stem id, NOT "shabdarupani" as first assumed), each with
    # {lemma, gender, declension_table: {headers, rows}} -- pure
    # Devanagari, no garbling found. Per-word cell: find which stem's
    # declension table contains a cell EXACTLY equal to this word (or a
    # hyphen-stripped compound-final match), and report the specific
    # vibhakti/vacana that occurrence realizes -- far more useful than
    # a verse-level "N stems tabulated" note (the previous version).
    c5 = comps.get("COMPONENT_5_shabdarupani", {})
    for stem_key, stem in (c5.get("stems") or {}).items():
        if not isinstance(stem, dict):
            continue
        table = stem.get("declension_table") or {}
        lemma = stem.get("lemma") or stem_key
        gender = stem.get("gender") or ""
        gender_suffix = f" ({gender})" if gender else ""
        for row in table.get("rows", []):
            if not row:
                continue
            vibhakti_name = row[0]
            for col_i, form in enumerate(row[1:], start=1):
                header = (table.get("headers") or [None] * 4)[col_i] if col_i < len(table.get("headers", [])) else ""
                idx = canon_index.get(_canon(form))
                if idx is None:
                    continue
                cell = f"{lemma}{gender_suffix} -- {vibhakti_name} {header}: {form}"
                # Per explicit user request: classify this stem's ending
                # (akara/ikara/aakara/ukara/nakara/vat-mat/in-anta/
                # pronoun) against vibhakti_table.json and append the
                # traditional model word (e.g. "रामशब्दवत्"), hyperlinked
                # to that paradigm's own section in this workbook's
                # "Vibhakti Reference" sheet (see write_report).
                model, class_key = vibref.get_model_and_key(lemma, gender, stem.get("pos"))
                if model:
                    is_sarvanama = class_key.startswith("sarvanama")
                    suffix_word = "-सर्वनाम" if is_sarvanama else "शब्दवत्"
                    cell += f" -- {model}{suffix_word}"
                    rows[idx].shabdarupani_link = class_key
                rows[idx].shabdarupani = cell

    # Pada-vigraha fallback from Sabdarupani (this pass's new work,
    # per explicit user request on row 15/1.1.2's कः): Component 3's own
    # Library `matched_words` queue (above) does not cover every
    # occurrence of a repeated word -- e.g. कः recurs 8 times across
    # 1.1.2-1.1.4, but the Library pada_vigraha evidence only carries
    # ONE queued entry for it, so most occurrences were left as a bare
    # "-" even though Component 5 (Sabdarupani) already independently
    # identified that SAME occurrence's lemma/gender/vibhakti via an
    # exact declension-table cell match (a real, already-computed
    # result, just sitting one column over, unused by Pada-vigraha).
    # Rather than leave those rows blank, cross-reference Component 5's
    # own match into Pada-vigraha -- clearly labelled as a cross-
    # reference (not fresh Library pada_vigraha evidence) and amber-
    # flagged, the same "computed, not Library-asserted" treatment
    # already used for the Samasa "(सम्पूरितम्, न Library-दत्तम्)"
    # supplementation above. Only fires where Component 3 left "-" AND
    # Component 5 has real content for that exact row.
    for row in rows:
        if row.pada_vigraha == "-" and row.shabdarupani != "-":
            row.pada_vigraha = (
                f"{row.shabdarupani} -- (शब्दरूपाणि-आधारेण सम्पूरितम्, "
                f"न प्रत्यक्षं Library-Pada-vigraha-दत्तम्)"
            )
            row.amber_cols.add("pada_vigraha")

    # Component 6 (Dhaturupani) -- real per-word evidence lives in
    # `lexical_evidence` (surface/analysis pairs), which is ALREADY
    # clean Devanagari (unlike `conjugation_tables`' own gana/lakara/
    # form fields, which carry the SAME English-garbled-into-Devanagari
    # defect found and fixed in Chandas/alankara this session -- e.g.
    # "३ (जुहोत्यादि/रेदुप्लिचतिन्ग् च्लस्स्)" = "3 (juhotyādi/reduplicating
    # class)" spelled out letter-by-letter; NOT used here for that
    # reason). `analysis` already gives root + lakāra + puruṣa/vacana,
    # and for upasarga-prefixed verbs already shows the उपसर्ग+धातु split
    # (e.g. परिपप्रच्छ -> "प्रच्छ्, लिट्/परोक्षभूत, प्रथमपुरुष, एकवचन, "
    # "परस्मैपद; परि + पप्रच्छ") -- exactly the decomposition requested.
    c6 = comps.get("COMPONENT_6_dhaturupani", {})
    for ev in c6.get("lexical_evidence", []):
        idx = canon_index.get(_canon(ev.get("surface", "")))
        if idx is None:
            continue
        raw_analysis = ev.get("analysis", "")
        cell, was_en = devanagari_only(raw_analysis)
        # Dhatu-Manjari.json citation (this session's new work): the
        # root name is always the first comma-separated field of
        # `analysis` (see the block comment above); looked up against
        # the hand-verified DHATU_MANJARI_ROOT_BASEINDEX map, then
        # against the actual Dhatu-Manjari.json/Dhatu-Lakara.json files
        # at runtime -- never fabricated, and silently omitted (not
        # amber-flagged) if the root isn't in the map or the citation
        # data isn't reachable this run.
        root = raw_analysis.split(",", 1)[0].strip()
        cell += dhatu_manjari_citation(root)
        rows[idx].dhaturupani = cell
        if was_en or ev.get("status") != "MATCH":
            rows[idx].amber_cols.add("dhaturupani")

    # Deeper Samasa (this session's addition): the Library's own
    # Component 9 has real GAPS (verses 1.1.3 and 1.1.5 have ZERO
    # resolved_items at all, despite containing genuine compounds --
    # एकप्रियदर्शनः, एवंविधम्). For any hyphenated Component-1 word (a
    # compound, per the engine's own convention) that Component 9 did
    # NOT resolve, supplement with this project's OWN, hardened
    # combined_splitter.py samasa pipeline (see earlier this session --
    # false-positive-guarded, cross-checked against apte_dictionary.sqlite)
    # -- always amber-flagged, since it's computed, not Library-asserted.
    for i, word in enumerate(words):
        if "-" not in word or rows[i].samasa != "-":
            continue  # not a compound, or Component 9 already covered it
        deva_piece = _canon(word)
        best = samasa_cs._best_samasa_decomposition(deva_piece)
        if best is None:
            continue
        deva_label, citation, known = cite.lookup_samasa_citation(best["type_guess"])
        cell = f"{deva_label} : {' + '.join(best['members'])}"
        if citation:
            cell += f" [{citation}]"
        cell += " (सम्पूरितम्, न Library-दत्तम्)"
        rows[i].samasa = cell
        rows[i].amber_cols.add("samasa")

    # Component 7 (Pratyaya) -- per word by fused-surface match.
    c7 = comps.get("COMPONENT_7_pratyaya", {})
    for ev in c7.get("evidence", []):
        surface = _canon(ev.get("surface", ""))
        idx = canon_index.get(surface)
        if idx is None:
            continue
        cell, was_en = devanagari_only(ev.get("analysis", ""))
        rows[idx].pratyaya = cell
        if was_en or ev.get("status") != "MATCH":
            rows[idx].amber_cols.add("pratyaya")

    # Component 8 (Sandhi) -- per word/junction by fused-surface match.
    c8 = comps.get("COMPONENT_8_sandhi", {})
    for ev in c8.get("evidence", []):
        surface = _canon(ev.get("surface", ""))
        idx = canon_index.get(surface)
        if idx is None:
            continue
        cell, was_en = devanagari_only(ev.get("analysis", ""))
        rows[idx].sandhi = cell
        if was_en or ev.get("status") != "MATCH":
            rows[idx].amber_cols.add("sandhi")

    # Component 9 (Samasa) -- resolved_items: [word, X, Y, citation?].
    # IMPORTANT, found by direct inspection of MULTIPLE verses: the
    # (vigraha, type_description) ORDER of X/Y is NOT fixed across
    # entries -- e.g. 1.1.1's धर्मज्ञः has X="धर्मस्य ज्ञाता" (vigraha),
    # Y="tatpuruṣa-type compound" (type), but the SAME verse's
    # मुनिपुङ्गवम् has X="षष्ठीतत्पुरुषः" (type), Y="मुनीनां मध्ये पुङ्गवः
    # इव" (vigraha) -- exactly reversed. A fixed positional assumption
    # (tried first, found wrong) silently mislabels roughly half of all
    # entries. Disambiguated instead by CONTENT: when a citation exists,
    # whichever of X/Y matches its `rule_name_sa` is the type label and
    # the OTHER is the vigraha (unambiguous); when no citation exists,
    # the string ending in a recognized compound-class suffix
    # (तत्पुरुषः/बहुव्रीहिः/द्वन्द्वः/अव्ययीभावः/द्विगुः, optionally
    # hedged with ";") is the type, the other the vigraha.
    _SAMASA_CLASS_SUFFIXES = ("तत्पुरुषः", "बहुव्रीहिः", "द्वन्द्वः", "अव्ययीभावः", "द्विगुः")

    def _split_type_and_vigraha(x, y, rule_name_sa=None):
        if rule_name_sa:
            if x.strip() == rule_name_sa.strip():
                return x, y
            if y.strip() == rule_name_sa.strip():
                return y, x
        x_is_type = any(s in x for s in _SAMASA_CLASS_SUFFIXES)
        y_is_type = any(s in y for s in _SAMASA_CLASS_SUFFIXES)
        if x_is_type and not y_is_type:
            return x, y
        if y_is_type and not x_is_type:
            return y, x
        if rule_name_sa:
            # A citation exists but names neither x nor y verbatim (the
            # rulebook's own phrasing can differ slightly from the
            # Library's free-text type description) -- fall back to
            # script: whichever of x/y is PREDOMINANTLY Latin script is
            # the (often English) type description Library evidence
            # sometimes uses instead of a proper Sanskrit label (see
            # this module's own docstring on this exact defect class);
            # the Devanagari one is the vigraha. The citation's own
            # rule_name_sa is used as the displayed type label regardless.
            x_deva_chars = len(_DEVANAGARI_RUN.findall(x))
            y_deva_chars = len(_DEVANAGARI_RUN.findall(y))
            if x_deva_chars and not y_deva_chars:
                return rule_name_sa, x
            if y_deva_chars and not x_deva_chars:
                return rule_name_sa, y
        return None, None  # genuinely ambiguous -- caller must fall back safely

    c9 = comps.get("COMPONENT_9_samasa", {})
    for item in c9.get("resolved_items", []):
        if not item:
            continue
        word = item[0]
        idx = canon_index.get(_canon(word))
        if idx is None:
            continue
        x = item[1] if len(item) > 1 else ""
        y = item[2] if len(item) > 2 else ""
        citation_obj = item[3] if len(item) > 3 and isinstance(item[3], dict) else None
        rc = citation_obj.get("rulebook_citation") if citation_obj else None
        type_str, vigraha = _split_type_and_vigraha(x, y, rc.get("rule_name_sa") if rc else None)
        amber = False
        if rc and type_str is not None:
            label = rc.get("rule_name_sa", "")
            ref = rc.get("ashtadhyayi_ref", "")
            cell = f"{label} : {vigraha}" if vigraha else label
            if ref:
                cell += f" [अष्टाध्यायी {ref}]"
        elif type_str is not None:
            label, was_en = devanagari_only(type_str)
            cell = f"{label} : {vigraha}" if vigraha else (vigraha or label)
            amber = True  # no verified citation for this classification
        else:
            # Genuinely couldn't tell which of x/y is which -- show both
            # labelled explicitly rather than silently guessing an order.
            cell_x, _ = devanagari_only(x)
            cell_y, _ = devanagari_only(y)
            cell = f"(अनिश्चितक्रमेण) {cell_x} / {cell_y}"
            amber = True
        rows[idx].samasa = cell
        if amber or ";" in x or ";" in y:
            rows[idx].amber_cols.add("samasa")  # hedged/ambiguous or uncited classification

    # Component 10 (Chandas) -- verse-level, shown once. The Library's
    # own alankara "name" field sometimes appends a parenthetical
    # English aside that a prior data-preparation pass garbled into
    # phonetic-but-meaningless Devanagari (e.g. "रूपक (मिनोर्, एम्बेद्देद्)"
    # is literally "rupaka (minor, embedded)" transliterated letter-by-
    # letter, and "प्रश्न (...)" cases spell out entire English sentences
    # the same way) -- these pass devanagari_only()'s script-only filter
    # untouched since they ARE valid Devanagari Unicode, just semantically
    # empty. Every real example checked has its genuine Sanskrit term
    # BEFORE the first "(" (स्वभावोक्ति, रूपक, प्रश्न, अतिशयोक्तिः), so the
    # parenthetical is dropped entirely rather than displayed.
    c10 = comps.get("COMPONENT_10_chandas", {})
    if c10.get("chandas_name") and rows:
        rows[0].chandas = c10["chandas_name"]
        alankaras = c10.get("alankara") or []
        if alankaras:
            clean_names = [a.get("name", "").split("(")[0].strip() for a in alankaras]
            rows[0].chandas += f" | अलङ्काराः: {', '.join(n for n in clean_names if n)}"

    for r in rows:
        r.provenance = "Internal"
    return rows


# --------------------------------------------------------------------------- #
# Verses 6-10: compute via this project's own sandhi/samasa tools
# --------------------------------------------------------------------------- #
def build_rows_computed(cs, verse_key, pada_lines):
    kanda, sarga, verse_num = verse_key
    ref = f"R_{kanda},{sarga:03d}.{verse_num:03d}"
    rows = []
    for pada_line in pada_lines:
        tokens = pada_line.split()
        if not tokens:
            continue
        analyzed = cs.analyze_pada_line(tokens)
        restored = restore_tokens(cs.sp, tokens, scheme="iast")
        karaka_entries = analyze_karaka(cs.sp, restored, scheme="iast")

        for i, a in enumerate(analyzed):
            word_deva = parasavarna_normalize(tl(a["citation_form"], sanscript.IAST, sanscript.DEVANAGARI))
            row = ReportRow(ref, word_deva)
            row.provenance = "Internal"

            # Sandhi
            if a["sandhi_rule"] is not None:
                deva_label, citation, known = cite.lookup_sandhi_citation(a["sandhi_rule"])
                left = parasavarna_normalize(tl(a["sandhi_vigraha"][0], sanscript.IAST, sanscript.DEVANAGARI))
                right = parasavarna_normalize(tl(a["sandhi_vigraha"][1], sanscript.IAST, sanscript.DEVANAGARI))
                cell = f"{deva_label} : {left} + {right}"
                if citation:
                    cell += f" [{citation}]"
                row.sandhi = cell
                row.amber_cols.add("sandhi")  # computed, not Library-verified
                if not known:
                    row.amber_cols.add("sandhi")

            # Samasa
            if a["samasa"] is not None:
                deva_label, citation, known = cite.lookup_samasa_citation(a["samasa"]["type_guess"])
                members = " + ".join(a["samasa"]["members"])
                cell = f"{deva_label} : {members}"
                if citation:
                    cell += f" [{citation}]"
                row.samasa = cell
                row.amber_cols.add("samasa")  # computed heuristic, always flagged

            rows.append(row)

        # Karaka -- map analyze_karaka's per-token roles onto this
        # pāda-line's rows by token index (restore_tokens/analyze_karaka
        # walk the same token list in the same order as analyzed above).
        # analyze_karaka's own `role` field is a hand-written ENGLISH
        # sentence in several shapes (see its source, samasa_splitter.py
        # ~line 1689): "karta (nominative subject)", "karma (accusative
        # object)", "qualifies karta (TOKEN)", "qualifies karma (TOKEN)",
        # or "{case} ({number}) -- not karta/karma". citation_lookup.py's
        # generic best-effort transliteration fallback is for grammar-
        # concept LABELS, not free English sentences -- blindly
        # transliterating "qualifies" phonetically produced Devanagari
        # gibberish (क़ुअलिफ़िएस्) when first tried; each shape is now
        # parsed explicitly instead.
        offset = len(rows) - len(analyzed)
        for i, entry in enumerate(karaka_entries):
            role_raw = entry.get("role")
            if not role_raw or offset + i >= len(rows):
                continue
            target_row = rows[offset + i]
            if role_raw.startswith("karta"):
                deva_role, citation, _ = cite.lookup_karaka_citation("karta")
                target_row.karaka = deva_role + (f" ({citation})" if citation else "")
            elif role_raw.startswith("karma"):
                deva_role, citation, _ = cite.lookup_karaka_citation("karma")
                target_row.karaka = deva_role + (f" ({citation})" if citation else "")
            elif role_raw.startswith("qualifies karta"):
                target_row.karaka = "विशेषणम् (कर्तुः)"
            elif role_raw.startswith("qualifies karma"):
                target_row.karaka = "विशेषणम् (कर्मणः)"
            else:
                # "{case} ({number}) -- not karta/karma" -- neither karta
                # nor karma; not a kāraka role worth asserting here, so
                # leave "-" rather than transliterate a throwaway note.
                continue
            target_row.amber_cols.add("karaka")

        # Pratyaya -- check each token for a resolvable krt/matup pratyaya.
        for i, tok in enumerate(tokens):
            if offset + i >= len(rows):
                continue
            resolved = cs.sp.resolve_pratyaya(tok, scheme="iast") or cs.sp.resolve_matup(tok, scheme="iast")
            if resolved is None:
                continue
            name = resolved.get("pratyaya")
            deva_name, citation, known = cite.lookup_pratyaya_citation(name)
            root_or_stem = resolved.get("root") or resolved.get("stem")
            cell = f"{deva_name}"
            if root_or_stem:
                # resolve_pratyaya/resolve_matup return root/stem in
                # whatever scheme was passed in (iast, here) -- must be
                # transliterated to Devanagari, never shown as raw IAST.
                stems = root_or_stem if isinstance(root_or_stem, list) else [root_or_stem]
                stem_deva = "/".join(tl(s, sanscript.IAST, sanscript.DEVANAGARI) for s in stems)
                cell += f" ({stem_deva})"
            if citation:
                cell += f" [{citation}]"
            rows[offset + i].pratyaya = cell
            rows[offset + i].amber_cols.add("pratyaya")
            if not resolved.get("resolved", True) or not known:
                rows[offset + i].amber_cols.add("pratyaya")

    return rows


# --------------------------------------------------------------------------- #
def build_all_rows(verse_start, verse_end, source_text=None):
    """
    source_text: path to the GRETIL-format source text used ONLY for
    verses beyond LIBRARY_VERSE_MAX (the computed path -- see module
    docstring). Verses at or below LIBRARY_VERSE_MAX always come from
    sanskrit_grammar_engine.py's own Library data regardless of this
    argument, since that data is keyed to the verse number, not to any
    text file. Defaults to the module-level SOURCE_TEXT constant (this
    project's own sa_rAmAyaNa.txt) when not given, so existing callers
    that don't pass it keep their prior behaviour unchanged.
    """
    if source_text is None:
        source_text = SOURCE_TEXT
    engine = sge.load_engine()
    cs = CombinedSplitter()
    all_rows = []

    for v in range(verse_start, verse_end + 1):
        if v <= LIBRARY_VERSE_MAX:
            all_rows.extend(build_rows_from_engine(engine, v, cs))
        else:
            verses = parse_gretil_verses(source_text, kanda=1, sarga=1, verse_start=v, verse_end=v)
            for key, pada_lines in sorted(verses.items()):
                all_rows.extend(build_rows_computed(cs, key, pada_lines))
    return all_rows


def _write_vibhakti_reference_sheet(wb):
    """
    Renders vibhakti_table.json's own paradigm classes as a real sheet
    in this workbook, grouped into families (e.g. akara_pum: नारद +
    राम side by side) so a reader sees both the project's own Library-
    verified anchor AND the traditional textbook name in one place.
    Returns {class_key: excel_row_of_that_class's_own_heading} for
    write_report to hyperlink each Sabdarupani cell to.
    """
    table = vibref.load_vibhakti_table()
    classes = table["classes"]
    ws = wb.create_sheet("Vibhakti Reference")
    ws["A1"] = table.get("title", "Vibhakti Reference")
    ws["A2"] = table.get("methodology_note", "")
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions["A"].width = 16
    for col in "BCDE":
        ws.column_dimensions[col].width = 20

    anchor_row = {}
    r = 4
    for class_key, cls in classes.items():
        ws.cell(row=r, column=1, value=cls["class_name_sa"]).font = Font(bold=True, size=12)
        ws.cell(row=r, column=1).fill = HEADER_FILL
        anchor_row[class_key] = r
        r += 1
        ws.cell(row=r, column=1, value=f"आदर्शशब्दः: {cls['model_word']}  |  "
                                        f"स्रोतः (Provenance): {cls['provenance']}")
        ws.cell(row=r, column=1).font = Font(italic=True)
        r += 1
        ws.cell(row=r, column=1, value=cls.get("source_note", ""))
        ws.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
        r += 1
        dtable = cls["declension_table"]
        for col_i, header in enumerate(dtable["headers"], start=1):
            c = ws.cell(row=r, column=col_i, value=header)
            c.font = Font(bold=True)
            c.fill = HEADER_FILL
        r += 1
        for row_vals in dtable["rows"]:
            for col_i, val in enumerate(row_vals, start=1):
                ws.cell(row=r, column=col_i, value=val)
            r += 1
        r += 1  # blank row between classes
    return anchor_row


def write_report(rows, output_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "10-Component Report"
    ws.append(HEADERS)
    for col, w in enumerate(COL_WIDTHS, start=1):
        ws.column_dimensions[get_column_letter(col)].width = w
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"

    col_key_to_index = {
        "padaccheda": 3, "anvaya": 4, "pada_vigraha": 5, "karaka": 6,
        "shabdarupani": 7, "dhaturupani": 8, "pratyaya": 9, "sandhi": 10,
        "samasa": 11, "chandas": 12,
    }

    vibhakti_anchor_row = _write_vibhakti_reference_sheet(wb)

    for i, r in enumerate(rows, 1):
        ws.append([
            i, r.verse_ref, r.word, r.anvaya, r.pada_vigraha, r.karaka,
            r.shabdarupani, r.dhaturupani, r.pratyaya, r.sandhi, r.samasa,
            r.chandas, "", "", r.provenance,
        ])
        excel_row = i + 1
        if r.shabdarupani_link and r.shabdarupani_link in vibhakti_anchor_row:
            # An internal same-workbook link needs a real Hyperlink
            # object with `location` set -- assigning a plain "#..."
            # string to `cell.hyperlink` sets `target` (an external
            # URL/file reference) instead and silently produces a dead
            # link (found by direct testing: cell.hyperlink.location
            # read back as None after the plain-string assignment).
            target_row = vibhakti_anchor_row[r.shabdarupani_link]
            sabda_cell = ws.cell(row=excel_row, column=7)
            sabda_cell.hyperlink = Hyperlink(
                ref=sabda_cell.coordinate, location=f"'Vibhakti Reference'!A{target_row}",
                display=sabda_cell.value)
            sabda_cell.font = Font(color="0563C1", underline="single")
        for key in r.amber_cols:
            col = col_key_to_index.get(key)
            if col:
                ws.cell(row=excel_row, column=col).fill = AMBER

    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=(cell.column > 2))

    ws2 = wb.create_sheet("Notes")
    ws2["A1"] = "Valmiki Ramayana -- Balakanda, Sarga 1 -- 10-Component Grammar Quality Report"
    ws2["A2"] = (
        "Scope, per explicit user direction: verses 1.1.1-1.1.5 ONLY (the first 5 slokas, all "
        "Library-verified). Verses 6-10's separate, less-certain COMPUTED path still exists in "
        "this script (--verse-end > 5) but is no longer the default -- out of scope for now."
    )
    ws2["A3"] = (
        "KARAKA (this session's main new work): every सुबन्त (nominal) word now gets a real "
        "kāraka determination, not just the couple words Component 4 itself names. Method: "
        "Component 3's own pos/case fields classify each word तिङन्तम् (finite verb, no kāraka) / "
        "अव्ययम् (indeclinable, no kāraka) / सुबन्तम् (nominal); a सुबन्त word's Library-given "
        "vibhakti is then mapped to its DEFAULT kāraka via vibhakti_prakarana_rulebook.json's own "
        "vibhakti_assignment_rules (2.3.x) + kāraka_definitions (1.4.24-1.4.55), both cited. "
        "षष्ठी and the vocative are correctly shown as NOT kārakas (2.3.50 षष्ठी शेषे, 2.3.47 "
        "सम्बोधने च) rather than mislabeled. प्रथमा/तृतीया are amber-flagged (default reading only "
        "-- 2.3.46 and 2.3.18 each cover more than one possible kāraka depending on voice, which a "
        "vibhakti table alone can't resolve); द्वितीया/चतुर्थी/पञ्चमी/सप्तमी map to exactly one "
        "kāraka and are not amber. Where Component 4 ITSELF names a specific word as THE verse's "
        "कर्ता/कर्म, that overrides the default (marked 'Library-निश्चितम्', not amber) -- UNLESS "
        "it contradicts that same word's own Component-3 vibhakti (a real example found this "
        "session: 1.1.5's अहम्, Component-3-asserted प्रथमा, was Component-4-asserted कर्म, which "
        "is impossible per 2.3.2 कर्मणि द्वितीया -- flagged with ⚠ instead of silently trusted)."
    )
    ws2["A4"] = (
        "CHANDAS fix: the Library's own alankara names sometimes carry a parenthetical English "
        "aside that an earlier data-preparation pass garbled into phonetic-but-meaningless "
        "Devanagari (e.g. 'रूपक (मिनोर्, एम्बेद्देद्)' = 'rupaka (minor, embedded)' spelled out "
        "letter-by-letter). Fixed by keeping only the text before the first '(' -- every checked "
        "example has its genuine Sanskrit term there."
    )
    ws2["A5"] = (
        "SABDARUPANI (this session's new work): rebuilt from a verse-level 'N stems tabulated' "
        "note into a REAL per-word cell. Component 5's actual key is `stems` (a dict, not "
        "`shabdarupani` as first assumed) -- pure Devanagari, no garbling. For every word, this "
        "report now finds which stem's declension table contains a cell EXACTLY matching that "
        "word, and reports the specific lemma/gender/vibhakti/vacana it realizes (e.g. तपस्वी -> "
        "'तपस्विन् (पुंलिङ्गम्) -- प्रथमा एकवचनम्: तपस्वी'). "
        "NEW (per explicit user request): a standalone reference file, "
        "04_Laghu_Siddhanta_Kaumudi/vibhakti_table.json, holds the standard declension paradigms "
        "(akara/ikara/aakara/ukara/nakara/vat-mat-anta/in-anta/pronoun classes -- 16 total). Every "
        "Sabdarupani cell now ends with '-- <model>शब्दवत्' (e.g. 'रामशब्दवत्'), a live hyperlink "
        "into this workbook's new 'Vibhakti Reference' sheet. Classification is Devanagari-"
        "orthography-aware (अकारान्त words end in a BARE consonant letter since Devanagari never "
        "writes the inherent अ; इकारान्त/आकारान्त/उकारान्त are matched by the dependent vowel "
        "MATRA, not the independent vowel letter -- an early version compared against the wrong "
        "Unicode codepoint and silently matched nothing, caught by direct testing). PROVENANCE "
        "per class is NOT uniform -- see vibhakti_table.json's own methodology_note: classes "
        "anchored in this project's own Library data (नारद, संयुग, वाल्मीकि, तपस्विन्, गुणवत्, "
        "किम्, इदम्, एतद्, अस्मद्, युष्मद्) are 'Internal'; the explicitly-requested traditional "
        "names not present in the 5-verse benchmark (राम, फल, मुनि, रमा, गुरु, राजन्) are 'External' "
        "(general Sanskrit-grammar knowledge, not from this project's files or a web search) and "
        "flagged for a future print-grammar cross-check, particularly राम's own णत्व-affected "
        "cells (रामेण, रामाणाम्), which are NOT a blind copy of नारद's table. "
        "UPDATE (this pass): 04_Laghu_Siddhanta_Kaumudi/sabdamanjari_vibhakti_tables.json (a "
        "page-cited extraction of the Śabdamañjarī textbook, added to the project folder this "
        "pass) was checked against all six previously-'External' classes by exact model-word "
        "lookup. Five matched (राम पृ.6, मुनि पृ.8, गुरु पृ.9, रमा पृ.12, राजन् पृ.53) and now carry "
        "'Internal' provenance with a real page citation -- their seven previously-held rows were "
        "byte-identical to Śabdamañjarī's own (confirming they were already correct), but "
        "Śabdamañjarī additionally supplies the संबोधनम् row every External class was missing, "
        "and राजन्'s table gains four genuine typo corrections (राज्णः/राज्ना/राज्ने/राज्नोः, ण् "
        "where ञ् belongs, corrected to राज्ञः/राज्ञा/राज्ञे/राज्ञोः). फल is NOT in the pages this "
        "extraction currently covers (Śabdamañjarī's own अजन्त-नपुंसक साधारण example is वन "
        "'forest', not फल) and stays 'External', honestly unchanged rather than substituted."
    )
    ws2["A6"] = (
        "DHATURUPANI (this session's new work): built from Component 6's `lexical_evidence` field "
        "(surface/analysis pairs) -- already clean Devanagari, UNLIKE that same component's "
        "`conjugation_tables.gana/lakara/form` fields, which carry the identical English-garbled-"
        "into-Devanagari defect found in Chandas (e.g. 'जुहोत्यादि/रेदुप्लिचतिन्ग् च्लस्स्' = "
        "'juhotyādi/reduplicating class' spelled out letter-by-letter) -- those fields are "
        "deliberately NOT used. `lexical_evidence.analysis` already gives root + lakāra + puruṣa/"
        "vacana AND, for upasarga-prefixed verbs, the उपसर्ग+धातु split requested: परिपप्रच्छ -> "
        "'प्रच्छ्, लिट्/परोक्षभूत, प्रथमपुरुष, एकवचन, परस्मैपद; परि + पप्रच्छ'. "
        "UPDATE (this pass): 04_Laghu_Siddhanta_Kaumudi/Dhatu-Manjari.json (2,259-root Dhatupatha "
        "reference, added this pass) now appends a citation suffix to each Dhaturupani cell -- "
        "gana (with its Devanagari name, itself read from Dhatu-Lakara.json's own per-entry field, "
        "not hand-typed), pada, and an LSK/Siddhanta-Kaumudi sutra number, e.g. परिपप्रच्छ -> "
        "'... -- धातुमञ्जरी-सन्दर्भः: गण ६ तुदादिः, परस्मैपदी, LSK-सूत्र 662'. Each of this "
        "benchmark's 4 roots (प्रच्छ्, भी, इष्, अस्) was hand-matched to its correct Dhatu-Manjari "
        "baseindex by MEANING, since Dhatu-Manjari lists 3 homonymous अस् roots (ganas 1/2/4) and "
        "3 homonymous इष् roots (ganas 4/6/9) -- इष्/इच्छामि was matched to gana 6 'इच्छायाम्', "
        "अस्/असि to gana 2 'भुवि' (existential), NOT the first same-spelled root found, and both "
        "selections were cross-checked against the gana this project's own engine already asserts "
        "for that cell (Stage 35's deva.json values) before being recorded, not assumed. "
        "Dhatu-Lakara.json (a 30-root, 3-per-gana full-paradigm demonstration file, also added "
        "this pass) was NOT used for conjugation forms here -- this benchmark's actual tables "
        "still come from deva.json's lexical_evidence (Stage 35, unchanged) -- only for its "
        "gana-name field; प्रच्छ् itself is not among Dhatu-Lakara's 30 demo roots."
    )
    ws2["A7"] = (
        "SAMASA -- two fixes this session: (1) a real data-inconsistency bug -- resolved_items' "
        "(vigraha, type) tuple order is NOT fixed across entries (e.g. 1.1.1's धर्मज्ञः has "
        "(vigraha, type) order but मुनिपुङ्गवम् has (type, vigraha), reversed) -- now disambiguated "
        "by CONTENT (matching the citation's own rule_name_sa, or a known compound-class suffix, "
        "or script) instead of a fixed position, which had silently swapped roughly half the "
        "verse's entries. (2) DEEPER COVERAGE: verses 1.1.3 and 1.1.5 have ZERO Component-9 "
        "resolved_items despite containing real compounds (एकप्रियदर्शनः, एवंविधम्) -- any hyphenated "
        "Component-1 word (the engine's own compound-marking convention) Component 9 leaves "
        "uncovered is now supplemented by this project's own hardened combined_splitter.py samasa "
        "pipeline (from the sandhi/samasa report work earlier this session), marked "
        "'(सम्पूरितम्, न Library-दत्तम्)' and amber-flagged as computed, not Library-asserted."
    )
    ws2["A8"] = (
        "All grammar-concept labels (sandhi/samasa type, karaka role, pratyaya name) are rendered in "
        "Devanagari via citation_lookup.py, hand-verified against sandhi_rulebook.json / "
        "samasah_rulebook.json / vibhakti_prakarana_rulebook.json by rule CONTENT, not name-string "
        "matching. Ashtadhyayi rule numbers are cited in brackets where a verified match exists."
    )
    ws2["A9"] = "Source column: every row in this report is 'Internal' (project's own Library files, rulebooks, and tools) -- no external web lookup was used for this pass."
    ws2["A10"] = (
        "THIS PASS (new files): four new JSONs were added to 04_Laghu_Siddhanta_Kaumudi -- "
        "sabdamanjari_vibhakti_tables.json (185 pratipadikas, page-cited to the Śabdamañjarī "
        "textbook already in the project as Sabdamanjari.pdf) and sabdamanjari_numerals.json for "
        "शब्दरूप referenceability (see A5); Dhatu-Manjari.json (2,259-root Dhatupatha) and "
        "Dhatu-Lakara.json (30-root full-paradigm demo set) for धातुरूप referenceability (see A6). "
        "sabdamanjari_numerals.json and Dhatu-Lakara.json's own conjugation tables are not yet "
        "consumed by this generator beyond gana-naming -- neither is needed for this 5-verse "
        "benchmark's own words (no numeral occurs in verses 1.1.1-1.1.5; this benchmark's 4 verbal "
        "roots are already fully tabulated from deva.json) -- and are recorded here as reachable, "
        "verified-present Library files for a future verse range where they would apply, not "
        "wired in speculatively."
    )
    ws2["A11"] = (
        "PADA-VIGRAHA fallback (this pass, per explicit user request on row 15/1.1.2's कः): "
        "Component 3's Library `matched_words` queue does not carry a separate entry for every "
        "occurrence of a repeated surface form -- कः recurs 8 times across 1.1.2-1.1.4, but the "
        "Library pada_vigraha evidence queue only covers a subset of those occurrences, so most "
        "were left as a bare '-' even where Component 5 (Sabdarupani) had already independently "
        "identified that SAME row's lemma/gender/vibhakti via an exact declension-table match. "
        "Rather than leave those cells blank, any row still '-' after Component 3's own pass is "
        "now backfilled from that row's own Sabdarupani result, labelled "
        "'(शब्दरूपाणि-आधारेण सम्पूरितम्, न प्रत्यक्षं Library-Pada-vigraha-दत्तम्)' so it reads as a "
        "cross-reference from Component 5, not fresh Library pada_vigraha evidence, and "
        "amber-flagged accordingly -- the same computed-not-asserted treatment already used for "
        "the Samasa supplementation in A7. This only fires where Component 3 left '-' AND "
        "Component 5 has real content for that exact row; rows where neither component resolved "
        "the word (e.g. यत्र in 1.1.3, which has no Sabdarupani match either) remain honestly blank."
    )
    for cell in ("A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11"):
        ws2[cell].alignment = Alignment(wrap_text=True, vertical="top")
    ws2.column_dimensions["A"].width = 120

    wb.save(output_path)


# Output formats this generator knows how to write. Only "xlsx" is
# implemented -- the report's multi-sheet layout (Notes, Vibhakti
# Reference), hyperlinks, and amber quality-flagging are all native to
# openpyxl/xlsx and don't have an honest equivalent in a flat format
# like csv/json without silently dropping most of that structure. Kept
# as an explicit registry (not a hardcoded ".xlsx" string) so a future
# format can be added -- e.g. {"xlsx": write_report, "json": write_json}
# -- without changing the CLI contract below.
OUTPUT_WRITERS = {
    "xlsx": write_report,
}


def main():
    parser = argparse.ArgumentParser(
        description="10-component Sanskrit grammar quality-report generator for "
                     "Valmiki Ramayana, Balakanda Sarga 1. Verses 1-%d are always "
                     "read from this project's own Library-verified data "
                     "(sanskrit_grammar_engine.py); verses beyond that are computed "
                     "on the fly from --input-file via this project's sandhi/samasa "
                     "tools and are amber-flagged as less certain -- see this file's "
                     "own module docstring for the full DATA SOURCES breakdown."
                     % LIBRARY_VERSE_MAX,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--input-file", type=str, default=SOURCE_TEXT,
        help="Path to the GRETIL-format Sanskrit source text (IAST, one verse's "
             "padas per line, 'R_kanda,sarga.verse' references) used ONLY for "
             "verses beyond --verse-end %d; verses at or below that always come "
             "from the project's own Library data regardless of this flag." % LIBRARY_VERSE_MAX)
    parser.add_argument(
        "--verse-start", type=int, default=1,
        help="First verse number within Balakanda Sarga 1 to include.")
    parser.add_argument(
        "--verse-end", type=int, default=LIBRARY_VERSE_MAX,
        help="Last verse number within Balakanda Sarga 1 to include. Per explicit "
             "user direction the default stays at the Library-verified ceiling "
             "(%d); pass a higher value explicitly to also include the "
             "less-certain computed range." % LIBRARY_VERSE_MAX)
    parser.add_argument(
        "--output-file", type=str, default=None,
        help="Output file name or path. A bare filename (no directory component) "
             "is written into %s; a path that includes a directory is used "
             "exactly as given (the directory is created if missing). If "
             "omitted, defaults to '10component_report_1.1.<start>-<end>.<format>' "
             "in that same folder. Whatever extension is given is normalized to "
             "match --format." % QUALITY_REPORTS_DIR)
    parser.add_argument(
        "--format", type=str, default="xlsx", choices=sorted(OUTPUT_WRITERS),
        help="Output file format.")
    args = parser.parse_args()

    if not os.path.isfile(args.input_file) and args.verse_end > LIBRARY_VERSE_MAX:
        parser.error(
            f"--input-file not found: {args.input_file} "
            f"(required because --verse-end {args.verse_end} > {LIBRARY_VERSE_MAX})")

    os.makedirs(QUALITY_REPORTS_DIR, exist_ok=True)

    if args.output_file:
        output_path = args.output_file
        out_dir = os.path.dirname(output_path)
        if not out_dir:
            output_path = os.path.join(QUALITY_REPORTS_DIR, output_path)
        else:
            os.makedirs(out_dir, exist_ok=True)
        root, ext = os.path.splitext(output_path)
        wanted_ext = "." + args.format
        if ext.lower() != wanted_ext:
            output_path = root + wanted_ext
    else:
        output_path = os.path.join(
            QUALITY_REPORTS_DIR,
            f"10component_report_1.1.{args.verse_start}-{args.verse_end}.{args.format}")

    rows = build_all_rows(args.verse_start, args.verse_end, source_text=args.input_file)
    OUTPUT_WRITERS[args.format](rows, output_path)
    print(f"Wrote {output_path} ({len(rows)} words, verses 1.1.{args.verse_start}-1.1.{args.verse_end}, "
          f"input-file={args.input_file})", file=sys.stderr)


if __name__ == "__main__":
    main()
