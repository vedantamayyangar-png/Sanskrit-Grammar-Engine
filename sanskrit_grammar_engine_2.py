#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sanskrit_grammar_engine.py — v0.15

Canonical, Library-only Sanskrit grammatical treatise engine.

v0.5 (Stage 33) added a Library file-loader: instead of relying only on a
static, hand-curated evidence list embedded in this module, the engine
reads the Library artifact `Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json`
directly from the project directory at runtime, and cross-validates /
derives Components 1, 2, 4, 8, 9, and 10 from it.

v0.6 (Stage 34) adds a SECOND, richer directory-resident Library file,
`combined_shlokas_1-5_v81_migrated_labels_sa.json`, and uses it to:

  1. populate Component 5 (Śabdarūpāṇi / full declension tables), which
     was previously hardcoded to GAP for every verse regardless of
     evidence — this file supplies near-complete 7-case x 3-number tables
     for almost every declinable stem across all five verses;
  2. populate Component 4 (Kāraka) for all five verses (previously only
     1.1.1, 1.1.4, 1.1.5 had non-pending Kāraka), using this file's
     explicit present/absent status per semantic role; and
  3. extend Component 9 (Samāsa) coverage, preserving ambiguity where the
     Library file itself hedges a compound's classification between two
     or three options rather than forcing one.

Both directory files are cross-validated against the engine's authoritative
(sa_rAmAyaNa.txt-sourced) Component 1 independently; the two files use
different but internally-consistent tokenization/orthography conventions,
so their cross-validation methods differ (see LIBRARY_V81_FILENAME).

If a Library file cannot be found or parsed, the engine falls back to the
smaller embedded KNOWN_FORM_EVIDENCE list (and to the other directory file,
if only one is present) so it remains runnable, but flags degraded mode
explicitly in the gap report — it never silently fabricates missing
directory evidence.

v0.14 (Stage 42) adds a SIXTH directory-resident Library file,
`skd_entries.json` — the Śabdakalpadruma (SKD) dictionary, 42,531 entries,
derived from `Sanskrit_Relational_Corpus_Stage7_v0.9.zip`'s own
skd_entries.json, which was already present in the project directory. All
42,531 entries and their full `source_fields` (the k1/k2 SLP1 headwords
this engine actually looks up) are carried over unchanged; each entry's
`source_text` field is truncated to ~220 characters purely to keep the
file transferable (the untruncated verbatim text remains available in the
Stage 7 zip itself, unaltered) -- this engine only ever uses source_text
for an illustrative sample snippet, never as evidence content itself. It
is used for exactly one new, narrowly-scoped
purpose: independent dictionary-attestation of Component 9 (Samāsa)
compound-member breakdowns. For each compound the v8.1 file already
decomposes into constituent words (e.g. मुनिपुंगवम् → मुनि + पुंगवम्), the
engine now deterministically transliterates each constituent to SLP1 (the
same representation SKD's own headwords use) and performs an EXACT lookup
against the SKD headword index, with one documented, symmetric fallback
(stripping a trailing visarga, since SKD conventionally cites many entries
in a nominative-singular citation form that a compound's non-final,
bare-stem members do not carry). This never changes a compound's existing
status or classification — it only adds a separate, honestly-reported
`skd_attestation` field per constituent (attested / not attested), exactly
following the citation-only, non-promoting pattern already established for
rulebook citations (RULEBOOK_CITATION_MAP, SAMASA_CANDIDATE_MAP). Some
known, systematic SKD orthographic conventions (guttural/anusvāra
alternation, Bengali-typesetting consonant gemination) are NOT normalized
in this cycle and are recorded as an explicit follow-up gap rather than
chased with additional heuristics — see PROJECT_STATE.md.

v0.15 (Stage 43) adds a SEVENTH directory-resident Library file,
`apte_entries.json` -- Apte's 1890 Sanskrit-English Dictionary, 34,882
entries, parsed fresh (a from-scratch parser, not a reused prior artifact)
from `ap90.txt`, the same CSDL-format source text sitting alongside
`skd.txt` in the project's `D:\python` directory. Stage 42's
`_skd_attest_word` is generalized into `_dictionary_attest_word`, which now
checks EVERY configured dictionary Library file (currently SKD and Apte)
and reports a per-dictionary `sources` list rather than collapsing to one
boolean -- preserving exactly which dictionary(ies) actually attested a
word, per this project's source-provenance principle. Component 9's
per-constituent field is renamed `skd_attestation` -> `dictionary_attestation`
to reflect this (a deliberate, documented rename, not a silent shape
change -- see the Stage 43 CHANGELOG entry). The same mechanism is also
wired into Component 8 (Sandhi) for the first time: each already-asserted
Sandhi evidence item's pre-sandhi constituent words (parsed deterministically
from its own `analysis` string, e.g. "कः + नु -> को नु" => ["कः", "नु"]) are
now independently dictionary-attested the same way Samāsa's constituents
already are -- citation-only, never changing an item's existing status.

Canonical benchmark:
Vālmīki Rāmāyaṇa, Bālakāṇḍa, Sarga 1, ślokas 1.1.1–1.1.5.

No external web content is grammatical evidence for this engine.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import argparse
import json
import re

ENGINE_VERSION = "0.17"
BENCHMARK_ID = "valmiki-ramayana-balakanda-1.1.1-1.1.5"
TEMPLATE_COMPONENTS = [
    "COMPONENT_1_padaccheda",
    "COMPONENT_2_anvaya",
    "COMPONENT_3_padavigraha",
    "COMPONENT_4_karaka",
    "COMPONENT_5_shabdarupani",
    "COMPONENT_6_dhaturupani",
    "COMPONENT_7_pratyaya",
    "COMPONENT_8_sandhi",
    "COMPONENT_9_samasa",
    "COMPONENT_10_chandas",
    "COMPONENT_11_quiz",
]

STATUS_MATCH = "MATCH"
STATUS_AMBIGUOUS = "AMBIGUOUS"
STATUS_GAP = "GAP"
STATUS_NOT_ASSERTED = "NOT_ASSERTED"
STATUS_SOURCE_ASSERTION = "SOURCE_ASSERTION"
STATUS_COMPUTED = "COMPUTED_EVIDENCE"
# Stage 44: an item's own grammatical classification supplied by the
# engine's human author, NOT by any directory Library file and NOT
# runtime-verified against a rulebook (contrast SAMASA_CANDIDATE_MAP,
# whose citations ARE checked against the actual rulebook file). Used
# only where every available Library source leaves an item permanently
# pending/hedged with zero resolving evidence anywhere (see PROJECT_STATE.md
# Stage 38/44). Explicitly authorized as a one-time, clearly-labeled
# exception to this project's no-fabrication policy -- never conflated
# with SOURCE_ASSERTION, never counted toward evidence coverage, and never
# changes the item's own resolved/pending/ambiguous status.
STATUS_ENGINE_INFERRED = "ENGINE_INFERRED"

# Strings the Library template itself uses to mark an entry as not yet
# promotable. If any of these appear in a component's own "status" (or
# similarly-named) field, the engine must NOT promote that component to
# SOURCE_ASSERTION, regardless of how much text is present.
LIBRARY_PENDING_MARKERS = (
    "pending",
    "not_applicable",
    "needs_deterministic_morphology_pass",
    "needs review",
    "needs_review",
    "not asserted",
    "not_asserted",
)

# The single directory-resident Library file this engine reads at runtime.
# This is the file the project's KNOWN_FORM_EVIDENCE citations refer to as
# "Library comprehensive-10-component-template.json" / "Library
# Ramayana_BalaKanda_1.1.2-1.1.5_template_test_v0.2_library_only.json" in
# earlier stages; the artifact actually present in the project directory is:
LIBRARY_TEMPLATE_FILENAME = "Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json"

# Second, richer directory-resident Library artifact (Stage 34). This is a
# v8.1-schema, per-occurrence file that carries near-complete Component 5
# (declension tables), structured Component 4 (Kāraka, present/absent per
# role), and Component 9 (Samāsa breakdowns) for all five benchmark verses.
# Its own orthography is anusvāra-normalized (e.g. "नारदं" rather than
# "नारदम्"), which differs systematically — not erroneously — from the
# consonant+virāma forms used in sa_rAmAyaNa.txt and the engine's embedded
# Component 1. Because that difference is a whole-file convention rather
# than a per-word discrepancy, Component-1 cross-validation against this
# file compares word COUNTS only, not exact string equality (an exact
# string compare would falsely flag nearly every word).
LIBRARY_V81_FILENAME = "combined_shlokas_1-5_v81_migrated_labels_sa.json"

# Third directory-resident Library artifact (Stage 35). This is the
# PRE-migration source of the v8.1 file above — hand-authored Components
# 2/3/5/6/10 plus mechanically-derived Components 1/4/7/8/9 (per its own
# "note" field) — and unlike the v8.1 migration it carries genuine
# Component 6 (full verb conjugation tables) and Component 7 (suffix
# derivations, each tagged with a "confidence" of "resolved" or
# "heuristic (ending-match only...)"). Only "resolved"/non-heuristic
# entries are promoted, per the project's standing rule that ending-match
# heuristics must never be treated as authoritative morphology.
LIBRARY_DEVA_FILENAME = "combined_shlokas_1-5_deva.json"

# Stage 38: fourth directory-resident Library artifact, single-verse
# (1.1.1 only — confirmed by its own shloka_metadata.id). This is the
# original source the Stage-16 archive's Subanta registry drew from; its
# own Component-5 "note" field self-describes as COMPLETE for all 7
# declinable stems in 1.1.1, including वाग्विद् (a द्-stem/क्विप्-कृदन्त
# noun with an irregular चर्त्व nominative) — the one stem the v8.1 file
# (Stage 34) deliberately excluded as needing hand-checking. Used ONLY to
# fill Component-5 stem gaps the v8.1 file leaves open for 1.1.1, never to
# override or duplicate a stem the v8.1 file already supplies.
LIBRARY_COMPREHENSIVE_FILENAME = "comprehensive-10-component-template.json"

# Stage 36: reference rulebook artifacts. These are systematic, sutra-cited
# grammar rule compilations (NOT verse-specific evidence). Per the
# project's standing no-generalized-generation policy, they are used
# ONLY in two ways, both non-generative:
#   1. CITATION — attaching a real sutra/rule reference to a component
#      value that ALREADY has per-verse SOURCE_ASSERTION status from a
#      directory Library file. This never changes the value or its status;
#      it only adds provenance, and only after the engine has looked the
#      cited rule up in the actual rulebook file on disk and confirmed the
#      rule text matches the phenomenon (see RULEBOOK_CITATION_MAP below).
#   2. CANDIDATE ANNOTATION — for an item the Library itself still marks
#      pending/ambiguous, attaching a *non-binding* candidate rule match
#      (e.g. "this has the same structure as an already-resolved sibling
#      item") without promoting its status. The item stays GAP/AMBIGUOUS.
# The rulebooks are never used to classify an item that has zero per-verse
# Library evidence, and never used to synthesize new Sandhi/Samāsa
# operations beyond what a Library file already asserts for that verse.
LIBRARY_RULEBOOK_FILENAMES = {
    "sandhi": "sandhi_rulebook.json",
    "samasa": "samasah_rulebook.json",
    "taddhita": "taddhita_rulebook.json",
    "krt": "krt_pratyaya_rulebook.json",
    "chandas": "chandas_rulebook.json",
    "alankara": "alankara_rulebook.json",
}

# Stage 42: sixth directory-resident Library artifact — the Śabdakalpadruma
# (SKD) dictionary, 42,531 entries, extracted verbatim from
# Sanskrit_Relational_Corpus_Stage7_v0.9.zip's own skd_entries.json (that
# zip was already present in the project directory; nothing here is new
# content, only a re-surfacing of existing folder material in the flat-file
# form this engine's Library loaders expect). Used ONLY for dictionary
# ATTESTATION of Component-9 (Samāsa) compound-member breakdowns already
# supplied by the v8.1 file — never to derive a new compound analysis or to
# supply Sandhi/Pratyaya evidence (that remains out of scope for this
# cycle; see the Stage 42 CHANGELOG entry for why).
LIBRARY_SKD_FILENAME = "skd_entries.json"

# Stage 43: eighth directory-resident Library artifact -- Apte's 1890
# Sanskrit-English Dictionary, 34,882 entries, parsed fresh from ap90.txt
# (same CSDL format as skd.txt, same D:\python source tree). Used for the
# SAME purpose as skd_entries.json -- dictionary ATTESTATION of already-
# asserted Component-9 (Samāsa) and Component-8 (Sandhi) constituent
# words -- never to derive a new compound or sandhi analysis. See
# _dictionary_attest_word, which checks this and LIBRARY_SKD_FILENAME
# together and reports which dictionary(ies) actually attested each word.
LIBRARY_APTE_FILENAME = "apte_entries.json"

# Stage 40: hand-verified, per-verse mapping from a v8.1-asserted Alaṅkāra
# item's Sanskrit name (matched by prefix, since the v8.1 file's own name
# strings carry garbled parenthetical commentary, e.g. "रूपक (मिनोर्,
# एम्बेद्देद्)") to a specific alankara_rulebook.json rule id. Populated ONLY
# where the rulebook's own structural definition was read and genuinely
# matches how the v8.1 file describes that verse's actual figure -- not by
# name-string coincidence alone. Every entry here is still re-verified at
# runtime against the loaded rulebook file (_find_rule_in_rulebook) before
# a citation is ever attached; nothing here is fabricated or assumed to
# still be present in the file.
ALANKARA_RULEBOOK_CITATION_MAP: Dict[str, tuple] = {
    # 1.1.1's रूपक item: मुनिपुङ्गवम् (muni-puṅgava, "sage-bull") asserts
    # identity via a bare compound, no comparison particle -- structurally
    # the same अभेद-आरोपण (identity-assertion-without-comparison-word)
    # pattern as alankara-6's own worked examples (मुखचन्द्रं, वदनसरोजं).
    "1.1.1|रूपक": ("alankara-6", None,
                    "मुनिपुङ्गवम् asserts मुनिः एव पुङ्गवः (identity, no comparison particle) -- "
                    "the same अभेद-आरोपण structure as the rulebook's own मुखचन्द्रं/वदनसरोजं examples."),
    # NOTE: 1.1.4's v8.1-asserted "अतिशयोक्तिः" item is deliberately NOT
    # mapped here. alankara_rulebook.json's alankara-7 defines अतिशयोक्तिः
    # as a specific structural figure (उपमानं मात्रम् उच्यते, उपमेयं विना --
    # the comparison-OBJECT stated alone, with the actual subject omitted
    # entirely). The verse (kasya bibhyati devāś ca jātaroṣasya saṃyuge)
    # has no upamāna/upameya structure at all -- it is a rhetorical
    # question asserting an extraordinary claim, i.e. "hyperbole" only in
    # the loose English sense the v8.1 file's own gloss uses ("ativāda/
    # atiśayokti -- hyperbolic praise"), not the rulebook's technical
    # figure. Attaching alankara-7 here would be exactly the kind of
    # name-string-only overreach the project's citation policy prohibits
    # (cf. Stage 37's तपःस्वाध्यायनिरतम् precedent) -- reported as an
    # uncited Library assertion instead, with this reasoning attached.
}

# Stage 35: the engine's own directory does not contain every Library
# artifact — some live in a separate, user-specified directory. Rather than
# duplicating files across locations, the engine searches each of these
# directories in order (first match wins) for every named Library file.
# This list is machine-specific; on another machine, only the engine's own
# directory will exist, and the engine degrades gracefully (see
# _find_library_file / load_library_*).
# Stage 44: added the two new locations a September folder
# reorganization moved Library files into (corpus_data now holds the
# v0.1/v81/deva/comprehensive JSONs; 05_Sanskrit_Dictionaries now holds
# skd_entries.json/apte_entries.json), alongside the original D:\python
# (unchanged -- the six rulebook JSONs and the raw dictionary .txt
# sources still live there and were never moved).
LIBRARY_SEARCH_DIRS_EXTRA = [
    r"D:\python",
    r"E:\Sanskrit & Tamil Scholarship\01_Ramayana_Project\corpus_data",
    r"E:\Sanskrit & Tamil Scholarship\05_Sanskrit_Dictionaries",
]


def _find_library_file(filename: str, library_dir: Optional[Path]) -> Optional[Path]:
    """Locate `filename` by exact name only (no fuzzy search) across the
    engine's own directory and any configured extra search directories.
    If `library_dir` is explicitly given (e.g. via --library-dir), it is
    the ONLY directory searched, matching the pre-Stage-35 override
    semantics exactly."""
    if library_dir is not None:
        candidate = Path(library_dir) / filename
        return candidate if candidate.exists() else None
    search_dirs = [Path(__file__).resolve().parent] + [Path(d) for d in LIBRARY_SEARCH_DIRS_EXTRA]
    for d in search_dirs:
        try:
            candidate = d / filename
            if candidate.exists():
                return candidate
        except OSError:
            continue
    return None


def _is_pending(value: Any) -> bool:
    """True if a Library-supplied status/note string marks content as not
    yet promotable to SOURCE_ASSERTION."""
    if value is None:
        return False
    text = str(value).lower()
    return any(marker in text for marker in LIBRARY_PENDING_MARKERS)


def _c3_join_key(word: str) -> str:
    """Stage 41: canonicalize a word for joining Component 1's authoritative
    padaccheda inventory against the v8.1 file's own per-word
    COMPONENT_3_padavigraha.pada_vigraha list, undoing two KNOWN, DOCUMENTED
    formatting artifacts -- never an approximate/fuzzy match between
    different words:

    1. Component 1 displays compound/matup words hyphenated at member
       boundaries (e.g. "तपः-स्वाध्याय-निरतम्"); pada_vigraha's own 'word'
       field does not carry the hyphen consistently (see Stage 38's
       identical fix for the Component-5 cell-lookup join).
    2. The v8.1 file's orthography uses a word-final anusvāra (ं) in
       several 'word' entries where Component 1's authoritative inventory
       (sourced from sa_rAmAyaNa.txt) has the corresponding word-final
       consonant-म् spelling (e.g. "वरम्" vs a hypothetical "वरं") -- the
       same whole-file anusvāra-normalization convention already
       documented for this file in LIBRARY_V81_FILENAME's docstring and
       relied on by the count-only Component-1 cross-validation since
       Stage 34. Only the word-FINAL ं is touched; medial anusvāra is left
       alone since it is phonemically load-bearing there, not a spelling
       convention.

    This intentionally does NOT bridge genuine lexical differences (e.g.
    वाग्- vs वाक्- reflecting a real जश्त्व-sandhi spelling the pada_vigraha
    entry itself has not applied, or a real textual variant such as 1.1.4's
    द्युतिमान्/मतिमान् discrepancy) -- those are left to fail the join
    deliberately, so the caller reports them as unmatched rather than
    silently equating two different words."""
    key = word.replace("-", "")
    if key.endswith("ं"):
        key = key[:-1] + "म्"
    return key


def load_library_template(library_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Load the Library template JSON from the project directory.

    Returns a dict with keys 'raw' (full parsed JSON), 'by_verse' (verse_id
    -> verse record), and 'path' (resolved file path); or None if the file
    is missing / unreadable / malformed. This function performs no web
    access and no fuzzy path search — it looks only for the exact filename
    in the given (or engine-adjacent) directory, consistent with the
    Library-only, exact-matching project policy.
    """
    path = _find_library_file(LIBRARY_TEMPLATE_FILENAME, Path(library_dir) if library_dir is not None else None)
    if not path:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    by_verse: Dict[str, Dict[str, Any]] = {}
    for v in data.get("verses", []):
        vid = v.get("id")
        if vid:
            by_verse[vid] = v
    return {"raw": data, "by_verse": by_verse, "path": str(path)}


def load_library_v81(library_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Load the second, richer v8.1-schema Library artifact from the
    project directory (see LIBRARY_V81_FILENAME). Same exact-filename,
    no-fuzzy-search policy as load_library_template()."""
    path = _find_library_file(LIBRARY_V81_FILENAME, Path(library_dir) if library_dir is not None else None)
    if not path:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    by_verse: Dict[str, Dict[str, Any]] = {}
    for v in data.get("shlokas", []):
        vid = v.get("shloka_metadata", {}).get("id")
        if vid:
            by_verse[vid] = v
    return {"raw": data, "by_verse": by_verse, "path": str(path)}


def load_library_deva(library_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Load the third, pre-migration Library artifact (see
    LIBRARY_DEVA_FILENAME). Same exact-filename policy; searched across
    the engine's directory and LIBRARY_SEARCH_DIRS_EXTRA."""
    path = _find_library_file(LIBRARY_DEVA_FILENAME, Path(library_dir) if library_dir is not None else None)
    if not path:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    by_verse: Dict[str, Dict[str, Any]] = {}
    for v in data.get("shlokas", []):
        vid = v.get("shloka_metadata", {}).get("id")
        if vid:
            by_verse[vid] = v
    return {"raw": data, "by_verse": by_verse, "path": str(path)}


def load_library_comprehensive(library_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Load the fourth, single-verse (1.1.1-only) directory Library
    artifact (see LIBRARY_COMPREHENSIVE_FILENAME). Same exact-filename,
    no-fuzzy-search policy as the other Library loaders. Unlike the other
    three, this file's top level IS a single verse record (no
    'verses'/'shlokas' wrapper list), so 'by_verse' is built from its own
    shloka_metadata.id rather than iterated from a list."""
    path = _find_library_file(LIBRARY_COMPREHENSIVE_FILENAME, Path(library_dir) if library_dir is not None else None)
    if not path:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    vid = data.get("shloka_metadata", {}).get("id")
    by_verse = {vid: data} if vid else {}
    return {"raw": data, "by_verse": by_verse, "path": str(path)}


def load_rulebook(key: str, library_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Load a named reference rulebook (see LIBRARY_RULEBOOK_FILENAMES).
    Same exact-filename, multi-directory-search policy as the other
    Library loaders."""
    filename = LIBRARY_RULEBOOK_FILENAMES.get(key)
    if not filename:
        return None
    path = _find_library_file(filename, Path(library_dir) if library_dir is not None else None)
    if not path:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return {"raw": data, "path": str(path), "filename": filename}


def _find_rule_in_rulebook(rulebook_data: Dict[str, Any], rule_id: str, section: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Find a rule entry by its 'id' field within a loaded rulebook,
    optionally restricted to one top-level list section. Returns the raw
    rule dict (with its real sutra/example fields) or None if the id isn't
    actually present -- this is the runtime verification step that keeps
    citations honest: the engine never emits a citation it hasn't just
    confirmed exists, verbatim, in the file on disk."""
    raw = rulebook_data.get("raw", {})
    sections = [section] if section else [k for k, v in raw.items() if isinstance(v, list)]
    for sec in sections:
        for entry in raw.get(sec, []):
            if isinstance(entry, dict) and entry.get("id") == rule_id:
                return entry
    return None


def _citation_from_rule(rulebook_filename: str, rule: Dict[str, Any], note: str) -> Dict[str, Any]:
    example = (rule.get("examples") or [{}])[0]
    return {
        "rulebook": rulebook_filename,
        "rule_id": rule.get("id"),
        "rule_name_sa": rule.get("sanskrit_name"),
        "ashtadhyayi_ref": rule.get("ashtadhyayi_ref"),
        "sutra": rule.get("sutra_devanagari"),
        "parallel_example": example.get("sandhi"),
        "note": note,
    }


def load_library_skd(library_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Load the Śabdakalpadruma (SKD) dictionary Library artifact (see
    LIBRARY_SKD_FILENAME). The on-disk copy carries all 42,531 entries'
    full source_fields (k1/k2), with only source_text truncated (to keep
    the file transferable -- the untruncated verbatim text remains in
    Sanskrit_Relational_Corpus_Stage7_v0.9.zip, unaltered); this loader
    performs no further filtering. Same exact-filename, multi-directory-search
    policy as the other Library loaders. Unlike the other loaders, this
    also builds two headword indexes (never used to alter the raw records
    themselves): an EXACT-match SLP1-headword index (from each entry's own
    source_fields.k1/k2, which the Stage 7 corpus's own manifest states are
    preserved in SLP1 verbatim from the source text), and a second index
    keyed on that same headword with a single trailing visarga ('H')
    stripped, to support the one documented, symmetric normalization used
    by _skd_attest_word (see its docstring for why). If the file cannot be
    found or parsed, returns None and the engine degrades exactly like
    every other Library-gated mechanism -- no fabricated substitute."""
    path = _find_library_file(LIBRARY_SKD_FILENAME, Path(library_dir) if library_dir is not None else None)
    if not path:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, list):
        return None
    by_headword: Dict[str, List[Dict[str, Any]]] = {}
    by_headword_visarga_stripped: Dict[str, List[Dict[str, Any]]] = {}
    for entry in data:
        if not isinstance(entry, dict):
            continue
        sf = entry.get("source_fields", {}) or {}
        headwords = {sf.get("k1"), sf.get("k2")}
        for hw in headwords:
            if not hw or not isinstance(hw, str):
                continue
            by_headword.setdefault(hw, []).append(entry)
            stripped = hw[:-1] if hw.endswith("H") else hw
            by_headword_visarga_stripped.setdefault(stripped, []).append(entry)
    return {
        "raw_count": len(data),
        "by_headword": by_headword,
        "by_headword_visarga_stripped": by_headword_visarga_stripped,
        "path": str(path),
    }


def load_library_apte(library_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Load Apte's 1890 Sanskrit-English Dictionary Library artifact (see
    LIBRARY_APTE_FILENAME). Structurally identical to load_library_skd
    (same reduced entry shape: id/source_id/source_fields/source_text/
    parse_status, same k1/k2-based headword indexes, same visarga-stripped
    fallback index) -- a second dictionary of the same kind, not a
    different mechanism. Returns None if the file is missing/unreadable,
    exactly like every other Library loader."""
    path = _find_library_file(LIBRARY_APTE_FILENAME, Path(library_dir) if library_dir is not None else None)
    if not path:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, list):
        return None
    by_headword: Dict[str, List[Dict[str, Any]]] = {}
    by_headword_visarga_stripped: Dict[str, List[Dict[str, Any]]] = {}
    for entry in data:
        if not isinstance(entry, dict):
            continue
        sf = entry.get("source_fields", {}) or {}
        headwords = {sf.get("k1"), sf.get("k2")}
        for hw in headwords:
            if not hw or not isinstance(hw, str):
                continue
            by_headword.setdefault(hw, []).append(entry)
            stripped = hw[:-1] if hw.endswith("H") else hw
            by_headword_visarga_stripped.setdefault(stripped, []).append(entry)
    return {
        "raw_count": len(data),
        "by_headword": by_headword,
        "by_headword_visarga_stripped": by_headword_visarga_stripped,
        "path": str(path),
    }


# ----------------------------------------------------------------------
# Stage 42: deterministic Devanagari -> SLP1 transliteration.
#
# Like IAST_VOWELS_SORTED/iast_syllabify (Stage 39), this is a MECHANICAL
# orthographic conversion table, not grammatical evidence in itself -- it
# exists only so a Component-9 compound-member word (given in Devanagari by
# the v8.1 Library file's own 'breakdown' field) can be looked up against
# skd_entries.json's own SLP1 headwords (see LIBRARY_SKD_FILENAME; the
# Stage 7 corpus manifest states SLP1 is that file's source representation,
# so this is the representation the lookup must convert INTO, not a
# substantive grammatical claim about the word itself). Any character
# outside this table causes the conversion to return None rather than
# guess -- the caller then reports "not attempted", never a false match.
_DEVA_CONSONANTS: Dict[str, str] = {
    "क": "k", "ख": "K", "ग": "g", "घ": "G", "ङ": "N",
    "च": "c", "छ": "C", "ज": "j", "झ": "J", "ञ": "Y",
    "ट": "w", "ठ": "W", "ड": "q", "ढ": "Q", "ण": "R",
    "त": "t", "थ": "T", "द": "d", "ध": "D", "न": "n",
    "प": "p", "फ": "P", "ब": "b", "भ": "B", "म": "m",
    "य": "y", "र": "r", "ल": "l", "व": "v",
    "श": "S", "ष": "z", "स": "s", "ह": "h", "ळ": "L",
}
_DEVA_VOWEL_SIGNS: Dict[str, str] = {
    "ा": "A", "ि": "i", "ी": "I", "ु": "u", "ू": "U",
    "ृ": "f", "ॄ": "F", "ॢ": "x", "ॣ": "X",
    "े": "e", "ै": "E", "ो": "o", "ौ": "O",
}
_DEVA_INDEP_VOWELS: Dict[str, str] = {
    "अ": "a", "आ": "A", "इ": "i", "ई": "I", "उ": "u", "ऊ": "U",
    "ऋ": "f", "ॠ": "F", "ऌ": "x", "ॡ": "X",
    "ए": "e", "ऐ": "E", "ओ": "o", "औ": "O",
}
_DEVA_VIRAMA = "्"
_DEVA_ANUSVARA = "ं"
_DEVA_VISARGA = "ः"
_DEVA_CANDRABINDU = "ँ"
_DEVA_AVAGRAHA = "ऽ"
_DEVA_IGNORABLE = (" ", "-", "‌", "‍")


def devanagari_to_slp1(word: str) -> Optional[str]:
    """Convert a Devanagari word to SLP1. Returns None (never a guess) if
    any character in `word` is outside the table above."""
    s = (word or "").strip()
    out: List[str] = []
    i, n = 0, len(s)
    while i < n:
        ch = s[i]
        if ch in _DEVA_CONSONANTS:
            out.append(_DEVA_CONSONANTS[ch])
            nxt = s[i + 1] if i + 1 < n else None
            if nxt == _DEVA_VIRAMA:
                i += 2
                continue
            if nxt in _DEVA_VOWEL_SIGNS:
                out.append(_DEVA_VOWEL_SIGNS[nxt])
                i += 2
                continue
            out.append("a")
            i += 1
            continue
        if ch in _DEVA_INDEP_VOWELS:
            out.append(_DEVA_INDEP_VOWELS[ch]); i += 1; continue
        if ch == _DEVA_ANUSVARA:
            out.append("M"); i += 1; continue
        if ch == _DEVA_VISARGA:
            out.append("H"); i += 1; continue
        if ch == _DEVA_CANDRABINDU:
            out.append("~"); i += 1; continue
        if ch == _DEVA_AVAGRAHA:
            out.append("'"); i += 1; continue
        if ch in _DEVA_IGNORABLE:
            i += 1; continue
        return None
    return "".join(out)


# Exact Library text snapshot used only as the fixed benchmark. Source:
# Library sa_rAmAyaNa.txt, refs R_1,001.001–R_1,001.005.
BENCHMARK_VERSES: Dict[str, Dict[str, Any]] = {
    "1.1.1": {
        "source_ref": "R_1,001.001",
        "iast": "tapaḥsvādhyāyanirataṃ tapasvī vāgvidāṃ varam / nāradaṃ paripapraccha vālmīkir munipuṃgavam",
        "padaccheda": [
            "तपः-स्वाध्याय-निरतम्", "तपस्वी", "वाग्-विदाम्", "वरम्",
            "नारदम्", "परिपप्रच्छ", "वाल्मीकिः", "मुनि-पुङ्गवम्"
        ],
        "status": "benchmark_source_assertion",
    },
    "1.1.2": {
        "source_ref": "R_1,001.002",
        "iast": "ko nv asmin sāmprataṃ loke guṇavān kaś ca vīryavān / dharmajñaś ca kṛtajñaś ca satyavākyo dṛḍhavrataḥ",
        "padaccheda": [
            "कः", "नु", "अस्मिन्", "साम्प्रतम्", "लोके", "गुणवान्", "कः", "च",
            "वीर्यवान्", "धर्मज्ञः", "च", "कृतज्ञः", "च", "सत्यवाक्यः", "दृढव्रतः"
        ],
        "status": "benchmark_source_assertion",
    },
    "1.1.3": {
        "source_ref": "R_1,001.003",
        "iast": "cāritreṇa ca ko yuktaḥ sarvabhūteṣu ko hitaḥ / vidvān kaḥ kaḥ samarthaś ca kaś caikapriyadarśanaḥ",
        "padaccheda": [
            "चारित्रेण", "च", "कः", "युक्तः", "सर्वभूतेषु", "कः", "हितः", "विद्वान्",
            "कः", "कः", "समर्थः", "च", "कः", "च", "एकप्रियदर्शनः"
        ],
        "status": "benchmark_source_assertion",
    },
    "1.1.4": {
        "source_ref": "R_1,001.004",
        "iast": "ātmavān ko jitakrodho dyutimān ko 'nasūyakaḥ / kasya bibhyati devāś ca jātaroṣasya saṃyuge",
        "padaccheda": [
            "आत्मवान्", "कः", "जितक्रोधः", "द्युतिमान्", "कः", "अनसूयकः", "कस्य",
            "बिभ्यति", "देवाः", "च", "जातरोषस्य", "संयुगे"
        ],
        "status": "benchmark_source_assertion",
    },
    "1.1.5": {
        "source_ref": "R_1,001.005",
        "iast": "etad icchāmy ahaṃ śrotuṃ paraṃ kautūhalaṃ hi me / maharṣe tvaṃ samartho 'si jñātum evaṃvidhaṃ naram",
        "padaccheda": [
            "एतत्", "इच्छामि", "अहम्", "श्रोतुम्", "परम्", "कौतूहलम्", "हि", "मे",
            "महर्षे", "त्वम्", "समर्थः", "असि", "ज्ञातुम्", "एवंविधम्", "नरम्"
        ],
        "status": "benchmark_source_assertion",
    },
}

# Evidence already established from Library-backed project work. These are
# intentionally small and explicit; they are not generalized paradigms.
# This list remains the FALLBACK evidence source (used verbatim if the
# directory-resident Library file above cannot be found), and it also still
# supplies Subanta/Tiṅanta/Kṛt/Pratyaya lexical evidence that the Library
# template file does not itself carry in machine-readable per-word form.
KNOWN_FORM_EVIDENCE = [
    # Stage 32: explicit verse-level Sandhi evidence from the Library regression artifact.
    {"surface": "को नु", "domain": "sandhi", "status": STATUS_MATCH, "analysis": "कः + नु → को नु", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json", "verse_id": "1.1.2"},
    {"surface": "न्वस्मिन्", "domain": "sandhi", "status": STATUS_MATCH, "analysis": "नु + अस्मिन् → न्वस्मिन्", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json", "verse_id": "1.1.2"},
    {"surface": "कश्च", "domain": "sandhi", "status": STATUS_MATCH, "analysis": "कः + च → कश्च", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json", "verse_id": "1.1.2"},
    {"surface": "धर्मज्ञश्च", "domain": "sandhi", "status": STATUS_MATCH, "analysis": "धर्मज्ञः + च → धर्मज्ञश्च", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json", "verse_id": "1.1.2"},
    {"surface": "कृतज्ञश्च", "domain": "sandhi", "status": STATUS_MATCH, "analysis": "कृतज्ञः + च → कृतज्ञश्च", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json", "verse_id": "1.1.3"},
    {"surface": "समर्थश्च", "domain": "sandhi", "status": STATUS_MATCH, "analysis": "समर्थः + च → समर्थश्च", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json", "verse_id": "1.1.3"},
    {"surface": "कश्चैकप्रियदर्शनः", "domain": "sandhi", "status": STATUS_MATCH, "analysis": "कः + च + एकप्रियदर्शनः → कश्चैकप्रियदर्शनः", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json", "verse_id": "1.1.3"},
    {"surface": "को जितक्रोधो", "domain": "sandhi", "status": STATUS_MATCH, "analysis": "कः + जितक्रोधः → को जितक्रोधो", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json", "verse_id": "1.1.4"},
    {"surface": "कोऽनसूयकः", "domain": "sandhi", "status": STATUS_MATCH, "analysis": "कः + अनसूयकः → कोऽनसूयकः", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json", "verse_id": "1.1.4"},
    {"surface": "देवाश्च", "domain": "sandhi", "status": STATUS_MATCH, "analysis": "देवाः + च → देवाश्च", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json", "verse_id": "1.1.4"},
    {"surface": "एतदिच्छामि", "domain": "sandhi", "status": STATUS_MATCH, "analysis": "एतत् + इच्छामि → एतदिच्छामि", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json", "verse_id": "1.1.5"},
    {"surface": "अहं श्रोतुम्", "domain": "sandhi", "status": STATUS_MATCH, "analysis": "अहम् + श्रोतुम् → अहं श्रोतुम्", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json", "verse_id": "1.1.5"},
    {"surface": "समर्थोऽसि", "domain": "sandhi", "status": STATUS_MATCH, "analysis": "समर्थः + असि → समर्थोऽसि", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json", "verse_id": "1.1.5"},
    {"surface": "ज्ञातुमेवंविधम्", "domain": "sandhi", "status": STATUS_MATCH, "analysis": "ज्ञातुम् + एवंविधम् → ज्ञातुमेवंविधम्", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json", "verse_id": "1.1.5"},
    {"surface": "युक्तः", "domain": "krtanta", "status": STATUS_AMBIGUOUS,
     "analysis": "क्त-derived form; root choice remains ambiguous", "source": "Library project evidence"},
    {"surface": "श्रोतुम्", "domain": "nonfinite", "status": STATUS_MATCH,
     "analysis": "श्रु + तुमुन्", "source": "Library-backed project evidence"},
    {"surface": "ज्ञातुम्", "domain": "nonfinite", "status": STATUS_MATCH,
     "analysis": "ज्ञा + तुमुन्", "source": "Library-backed project evidence"},
    {"surface": "परिपप्रच्छ", "domain": "tinganta", "status": STATUS_MATCH,
     "analysis": "प्रच्छ्, लिट्/परोक्षभूत, प्रथमपुरुष, एकवचन, परस्मैपद; परि + पप्रच्छ",
     "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json"},
    {"surface": "इच्छामि", "domain": "tinganta", "status": STATUS_MATCH,
     "analysis": "इष्, लट्, उत्तमपुरुष, एकवचन", "source": "Library-backed project evidence"},
    {"surface": "असि", "domain": "tinganta", "status": STATUS_MATCH,
     "analysis": "अस्, लट्, मध्यमपुरुष, एकवचन", "source": "Library-backed project evidence"},
    {"surface": "बिभ्यति", "domain": "tinganta", "status": STATUS_MATCH,
     "analysis": "भी, लट्, प्रथमपुरुष, बहुवचन", "source": "Library-backed project evidence"},
    {"surface": "वाग्-विदाम्", "domain": "krtanta", "status": STATUS_MATCH,
     "analysis": "वाच् + विद् (क्विप्) + आम्", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json"},
    {"surface": "वरम्", "domain": "pratyaya", "status": STATUS_MATCH,
     "analysis": "वृ + अप् + अम्", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json"},
    {"surface": "तपस्वी", "domain": "pratyaya", "status": STATUS_MATCH,
     "analysis": "तपस् + विन् + सुँ (ई-आदेश)", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json"},
    {"surface": "निरतम्", "domain": "krtanta", "status": STATUS_MATCH,
     "analysis": "नि + रम् + क्त", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json"},
    {"surface": "वाल्मीकिः", "domain": "pratyaya", "status": STATUS_MATCH,
     "analysis": "वाल्मीकि + सुँ; इकारान्त पुंलिङ्ग, प्रथमा एकवचन", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json"},
    {"surface": "नारदम्", "domain": "pratyaya", "status": STATUS_MATCH,
     "analysis": "नारद + अम्; द्वितीया एकवचन", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json"},
    {"surface": "मुनि-पुङ्गवम्", "domain": "samasa", "status": STATUS_MATCH,
     "analysis": "षष्ठीतत्पुरुषसमासः (template assertion)", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json"},
    {"surface": "वाल्मीकिर्मुनिपुङ्गवम्", "domain": "sandhi", "status": STATUS_MATCH,
     "analysis": "विसर्गसन्धिः: वाल्मीकिः + मुनिपुङ्गवम्", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json"},
    {"surface": "वाग्विद्", "domain": "sandhi", "status": STATUS_MATCH,
     "analysis": "जश्त्वसन्धिः: वाच् + विद्", "source": "Library Ramayana_BalaKanda_1.1.1-1.1.5_template_test_v0.1.json"},
]

# Stage 36 (verse-by-verse rulebook validation pass, starting with 1.1.2):
# each entry maps an already-SOURCE_ASSERTION-status surface/compound to a
# specific rule this project's rulebooks were independently found to
# contain, hand-verified by the engine's author to describe the identical
# phenomenon (matching example pattern, matching sutra). The engine looks
# each rule_id up in the actual rulebook file at runtime (_find_rule_in_rulebook)
# before ever attaching a citation, so a citation only ever appears if the
# rule genuinely exists in the file on disk with that content.
RULEBOOK_CITATION_MAP = {
    # Component 7 (Pratyaya) — मतुप्/वतुप् possessive taddhita suffix.
    "गुणवान्": ("taddhita", None, "taddhita-5",
                "मतुप्/वतुप् possessive suffix; rulebook's own example गुणः अस्य अन्ति = गुणवान् is this exact word."),
    "वीर्यवान्": ("taddhita", None, "taddhita-5",
                  "Same मतुप्/वतुप् possessive-suffix rule family as गुणवान्."),
    # Component 8 (Sandhi).
    "को नु": ("sandhi", "visarga_sandhi", "visarga-4",
              "विसर्ग(अः) + soft consonant → ओ; rulebook example रामः+गच्छति=रामो गच्छति is the identical transformation."),
    "न्वस्मिन्": ("sandhi", "svara_sandhi", "svara-4",
                  "उ + dissimilar vowel → व्; rulebook example सु+आगतम्=स्वागतम् is the identical उ→व् substitution."),
    "कश्च": ("sandhi", "visarga_sandhi", "visarga-3",
             "विसर्ग + च → श्; rulebook example रामः+चलति=रामश्चलति is the identical transformation."),
    "धर्मज्ञश्च": ("sandhi", "visarga_sandhi", "visarga-3", "Same विसर्ग→श् rule as कश्च."),
    "कृतज्ञश्च": ("sandhi", "visarga_sandhi", "visarga-3", "Same विसर्ग→श् rule as कश्च."),
    # Stage 37 (verses 1.1.3-1.1.5).
    "समर्थश्च": ("sandhi", "visarga_sandhi", "visarga-3", "Same विसर्ग→श् rule as कश्च (1.1.2/1.1.3)."),
    "कश्चैकप्रियदर्शनः": ("sandhi", "svara_sandhi", "svara-3",
                          "अ+ए→ऐ (वृद्धिसन्धिः, the कः+च→कश्च visarga step is separately covered by visarga-3); "
                          "rulebook example तव+एव=तवैव is the identical अ+ए→ऐ substitution."),
    "को जितक्रोधो": ("sandhi", "visarga_sandhi", "visarga-4", "Same विसर्ग(अः)→ओ rule as को नु (1.1.2)."),
    "देवाश्च": ("sandhi", "visarga_sandhi", "visarga-3", "Same विसर्ग→श् rule as कश्च."),
    # Stage 38 fix: these two keys previously read "कोओनसूयकः"/"समर्थोओसि" (a
    # literal letter ओ typed in place of the avagraha ऽ), so they never
    # matched either verse's actual Component-8 surface string
    # ("कोऽनसूयकः"/"समर्थोऽसि") and silently attached no citation. Corrected
    # to the real surfaces; the rule/analysis these entries already carried
    # was correct and unchanged.
    "कोऽनसूयकः": ("sandhi", "svara_sandhi", "svara-6",
                  "विसर्ग(अः)→ओ first (visarga-4, same step as को नु), then ओ+अ→ओ with avagraha (पूर्वरूपसन्धिः); "
                  "rulebook example हरे+अत्र=हरेऽत्र is the identical ओ+अ→ओ(ऽ) elision."),
    "समर्थोऽसि": ("sandhi", "svara_sandhi", "svara-6", "Same two-step विसर्ग-4 + पूर्वरूप combination as कोऽनसूयकः."),
    "एतदिच्छामि": ("sandhi", "vyanjana_sandhi", "vyan-3",
                   "त्→द् (जश्त्वसन्धिः) before a vowel; rulebook example वाक्+ईशः=वागीशः is the same "
                   "hard-to-soft class substitution pattern (क्→ग् there, त्→द् here)."),
    "अहं श्रोतुम्": ("sandhi", "vyanjana_sandhi", "vyan-6",
                    "म्→अनुस्वार before a following consonant; rulebook example रामम्+वन्दे=रामं वन्दे is the "
                    "identical transformation."),
    # Stage 38: 1.1.1's sole Component-8 item had no citation at all yet.
    # वाल्मीकिः ends in ई+विसर्ग (not अ+विसर्ग), so this is NOT the same
    # rule as को नु/को जितक्रोधो (visarga-4, which is specifically the
    # अतः रोः rule) -- after a non-अ vowel, visarga before a voiced sound
    # becomes र्, which is visarga-5, not visarga-4.
    "वाल्मीकिर्मुनिपुङ्गवम्": ("sandhi", "visarga_sandhi", "visarga-5",
                              "विसर्गस्य रेफादेशः: इ/उ/... + विसर्ग + घोष व्यञ्जन → र्; rulebook example "
                              "हरिः+वदति=हरिर्वदति is the identical इः+voiced-consonant→र् substitution "
                              "(distinct from visarga-4's अः→ओ, which only applies after अ)."),
    # Stage 38: three more Component-7 items the Library (deva.json) itself
    # labels मत्वर्थीयः वत्/मत्-प्रत्ययः (confidence: resolved) -- the same
    # taddhita-5 rule family already cited for गुणवान्/वीर्यवान् (1.1.2).
    "विद्वान्": ("taddhita", None, "taddhita-5",
                "deva.json's own breakdown labels this word मत्वर्थीयः वत्/मत्-प्रत्ययः (विद्+वत्), confidence "
                "'resolved' -- same rule family as गुणवान्/वीर्यवान्. Note: this citation reflects the Library's "
                "own stated classification only; it does not adjudicate the separate scholarly question of "
                "whether विद्वान् is better analysed as a क्वसु-प्रत्यय (कृत्) participle -- that review is out "
                "of scope for citation-only enrichment and is flagged here for a future correctness pass."),
    "आत्मवान्": ("taddhita", None, "taddhita-5",
                 "Same मत्वर्थीयः वत्/मत्-प्रत्ययः family as गुणवान्/वीर्यवान् (deva.json, confidence 'resolved')."),
    "मतिमान्": ("taddhita", None, "taddhita-5",
                "Same मत्वर्थीयः वत्/मत्-प्रत्ययः family, -मत् allomorph (deva.json, confidence 'resolved'); "
                "rulebook's own बुद्धिः अस्य अन्ति = बुद्धिमान् example is the identical -मत्-after-इ-stem case."),
}

# Component 9 (Samāsa) citations for items that ALREADY carry a resolved,
# non-hedged classification from a directory Library file (v0.1 template).
SAMASA_RULEBOOK_CITATION_MAP = {
    "धर्मज्ञः": ("samasa", "tatpurusha", "nan-5",
                 "उपपद-तत्पुरुष: object + ज्ञ (from ज्ञा) agent-noun; rulebook example कुम्भं करोति इति = कुम्भकारः is the same object+verbal-agent-noun structure."),
    "दृढव्रतः": ("samasa", "bahuvrihi", "bahuvrihi-1",
                 "सामान्यबहुव्रीहिः; rulebook's own example दृढा भक्तिः यस्य सः = दृढाभक्तिः is a structurally identical adjective+noun possessive compound."),
    # Stage 38: 1.1.1 and 1.1.4's resolved compounds had not yet had a
    # rulebook pass.
    "मुनिपुङ्गवम्": ("samasa", "tatpurusha", "tatpurusha-6",
                    "षष्ठीतत्पुरुषः: मुनीनां पुङ्गवः (इव) -- genitive-plural noun + noun; rulebook example "
                    "मद्राणां राजा = मद्राजः / देवस्य पूजकः = देवपूजकः is the same genitive-tatpurusha structure."),
    "वाग्विदाम्": ("samasa", "tatpurusha", "nan-5",
                   "उपपद-तत्पुरुष: वाच् (upapada) + विद्-क्विप् agent-noun ('one who knows speech') -- same "
                   "object-plus-क्विप्-agent-noun structure already used for धर्मज्ञः/कृतज्ञः (ज्ञा-root); here "
                   "the root is विद् rather than ज्ञा, but the compound formation is identical."),
    "जितक्रोधः": ("samasa", "bahuvrihi", "bahuvrihi-1",
                  "सामान्यबहुव्रीहिः: जितः क्रोधः येन सः -- rulebook's own first example ऊढः रथः येन सः = "
                  "ऊढरथः is the identical past-participle + noun, 'येन सः' possessive-compound structure."),
    "जातरोषस्य": ("samasa", "bahuvrihi", "bahuvrihi-1",
                  "सामान्यबहुव्रीहिः: जातः रोषः यस्य सः -- same participle+noun 'येन सः' structure as जितक्रोधः, "
                  "matching the rulebook's ऊढः रथः येन सः = ऊढरथः example."),
}

# Component 9 CANDIDATE annotations for items a directory Library file
# still marks pending/ambiguous. These NEVER change the item's status —
# they only note that an already-resolved sibling item in the SAME verse
# has the identical morphological structure, for a human reviewer's
# benefit. Promoting these automatically would be exactly the kind of
# unsupported generalization this project has prohibited at every stage.
SAMASA_CANDIDATE_MAP = {
    "कृतज्ञः": ("samasa", "tatpurusha", "nan-5",
                "Same उपपद-तत्पुरुष structure (object + ज्ञ from ज्ञा) as धर्मज्ञः, already resolved above via this same rule. Offered as a candidate only — Library evidence still marks this item's classification as pending, so its status is not promoted."),
    "सत्यवाक्यः": ("samasa", "bahuvrihi", "bahuvrihi-1",
                   "Same adjective+noun possessive structure ('सत्यं वाक्यं यस्य सः') as दृढव्रतः, already resolved above via this same rule. Offered as a candidate only — Library evidence still marks this item's classification as pending, so its status is not promoted."),
}

# Stage 44 (STATUS_ENGINE_INFERRED, see its docstring above): grammatical
# classifications for the three Component-9 items that, after an
# exhaustive re-check of every directory Library file (v0.1 template,
# v8.1 migrated file, pre-migration deva.json, comprehensive template,
# samasah_rulebook.json -- none of which resolves them; see PROJECT_STATE.md
# Stage 38/44), have NO resolving Library evidence anywhere. Authorized by
# the project owner as a deliberate, one-time exception (2026 audit) --
# these are the engine-author's own grammatical judgment, not Library
# evidence, and a domain-expert human review of each is expected. Keyed
# by verse_id, then by the item's own surface form (matching either the
# v0.1 template's spelling or the v8.1/deva files' spelling, since the
# same word appears differently spelled -- विसर्ग/अनुस्वार -- across sources).
ENGINE_INFERRED_SAMASA_MAP = {
    ("1.1.3", "सर्वभूतेषु"): {
        "compound_type": "कर्मधारयः (सामानाधिकरणतत्पुरुषस्य भेदः)",
        "breakdown": "सर्व + भूतेषु",
        "rationale": "सर्व (विशेषणम्) and भूत (नाम) stand in the same case (सामानाधिकरणम्), together meaning 'all beings' -- the same adjective+noun same-case compound pattern as नीलोत्पलम् or सर्वजनः. This is the standard textbook classification for सर्व-prefixed compounds of this shape; confidence is high, but it is still the engine author's own judgment, not a Library citation.",
        "confidence": "engine-author judgment, high confidence -- domain-expert review invited",
    },
    ("1.1.3", "एकप्रियदर्शनः"): {
        "compound_type": "बहुव्रीहिः (प्राथमिक पठन; तत्पुरुष-पठनमपी व्याकरणसम्मतम्)",
        "breakdown": "एक + प्रिय + दर्शनः",
        "rationale": "Library's own vigraha offers two readings: 'एकं प्रियं दर्शनं यस्य' (bahuvrīhi -- 'one whose sight is uniquely dear') vs 'सर्वेषां प्रियदर्शनः' (षष्ठीतत्पुरुष -- 'dear-sighted of/to all'). Preferred here as bahuvrīhi because it matches this verse's other epithets (विद्वान, समर्थः), which are adjectival descriptions of a person rather than genitive-tatpuruṣa constructions. This reading is NOT fully settled even by this inference -- the tatpuruṣa reading remains grammatically plausible and is not ruled out.",
        "confidence": "engine-author judgment, moderate confidence -- genuine residual ambiguity; domain-expert review invited",
    },
    ("1.1.5", "एवंविधम्"): {
        "compound_type": "तत्पुरुषः (अव्ययपूर्वपदः)",
        "breakdown": "एवम् + विधम्",
        "rationale": "एवम् is an indeclinable used adjectivally with the bound noun विध ('kind, manner'); the resulting compound एवंविधम् declines (agrees with नरम् in gender/case) rather than becoming indeclinable itself, so it cannot be an avyayībhāva (Paṇini's own defining test for that category) and is best analyzed as a tatpuruṣa whose pūrvapada happens to be an avyaya, the same pattern as तादृश/कीदृश-type words.",
        "confidence": "engine-author judgment, moderate-high confidence -- domain-expert review invited",
    },
    ("1.1.5", "एवंविधं"): None,  # filled below (same entry, v8.1/deva spelling)
}
ENGINE_INFERRED_SAMASA_MAP[("1.1.5", "एवंविधं")] = ENGINE_INFERRED_SAMASA_MAP[("1.1.5", "एवंविधम्")]


@dataclass
class LookupResult:
    status: str
    domain: str
    query: str
    matches: List[Dict[str, Any]]
    reason: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        d = {"status": self.status, "domain": self.domain, "query": self.query}
        if self.matches:
            d["matches"] = self.matches
        if self.reason:
            d["reason"] = self.reason
        return d


def normalize_surface(value: str) -> str:
    return " ".join(str(value).strip().split())


def exact_key(value: str) -> str:
    return normalize_surface(value)


# ----------------------------------------------------------------------
# Stage 39: deterministic IAST syllabification and guru/laghu scansion.
#
# This is COMPUTED_EVIDENCE, not a Library source assertion — but unlike
# a rulebook *citation* (which only ever decorates an already-Library-
# asserted value), this genuinely COMPUTES a new value from the verse's
# own immutable IAST text, the same way Component 3's declension-table
# lookup computes pada-vigraha from Component 5. To stay inside the
# project's Library-only policy, the classification rules themselves are
# not taken from general Sanskrit-prosody knowledge -- they are grounded
# in, and verified at runtime against, chandas_rulebook.json's own stated
# rules:
#   - chandas-2 defines a वर्ण (syllable, for metrical purposes) as a
#     vowel optionally preceded by consonants; a bare trailing consonant
#     is not its own syllable (its own example: अवाक् = अ + वाक्, 2
#     syllables).
#   - chandas-3 gives the five-fold गुरु test: a syllable is गुरु if it
#     carries अनुस्वार, is दीर्घ (long vowel), carries विसर्ग, is followed
#     by a consonant-cluster (संयोग, i.e. 2+ consonants before the next
#     vowel), or stands at a पादान्त (kept as a SEPARATE flag here, never
#     silently folded into the phonetic pattern -- see below).
#   - chandas-6 gives अनुष्टुप्'s structural constraint: four 8-syllable
#     पादs; 5th syllable always लघु; 6th always गुरु; 7th गुरु in पादs 1/3,
#     लघु in पादs 2/4.
# If chandas_rulebook.json is unreachable, or any of these three rule ids
# is not actually present in the file, scansion is not computed at all
# (GAP-like degradation, same policy as every other Library-gated
# component) -- the rules are never hardcoded independently of the file.
IAST_VOWELS_SHORT = ["a", "i", "u", "ṛ", "ḷ"]
IAST_VOWELS_LONG = ["ā", "ī", "ū", "ṝ", "e", "ai", "o", "au"]
IAST_VOWELS_SORTED = sorted(IAST_VOWELS_LONG + IAST_VOWELS_SHORT, key=len, reverse=True)

# IAST represents each aspirated stop as a two-character digraph, but it
# is ONE consonant phoneme (e.g. "ḍh" = ढ्, not ड्+ह्). Counting raw
# characters for the संयोग (cluster) test would misclassify every
# syllable immediately before an aspirate as heavier than it actually is
# -- this was caught empirically (Stage 39 development) as a false
# positive on दृढव्रतः/जिज्ञातुम्-type words before this list was added.
IAST_ASPIRATE_DIGRAPHS = sorted(
    ["kh", "gh", "ch", "jh", "ṭh", "ḍh", "th", "dh", "ph", "bh"], key=len, reverse=True
)


def _iast_vowel_at(s: str, i: int) -> Optional[str]:
    for v in IAST_VOWELS_SORTED:
        if s[i:i + len(v)] == v:
            return v
    return None


def _iast_consonant_count(segment: str) -> int:
    """Count consonant PHONEMES (not characters) in a pure-consonant
    IAST segment, treating each aspirate digraph as one consonant."""
    i, n, count = 0, len(segment), 0
    while i < n:
        matched = False
        for asp in IAST_ASPIRATE_DIGRAPHS:
            if segment[i:i + len(asp)] == asp:
                count += 1
                i += len(asp)
                matched = True
                break
        if not matched:
            count += 1
            i += 1
    return count


def iast_syllabify(text: str) -> List[Dict[str, Any]]:
    """Split IAST text (word spaces and avagraha apostrophes are
    prosodically silent and stripped, per chandas-2's own definition of
    वर्ण as vowel-anchored) into syllables. Each syllable's onset
    consonants attach to ITS OWN vowel, per chandas-2's अवाक्=अ+वाक्
    example (a bare trailing consonant with no following vowel joins the
    PRECEDING syllable instead, since it starts no वर्ण of its own)."""
    s = text.replace(" ", "").replace("'", "").replace("-", "")
    n = len(s)
    vowel_positions = []
    j = 0
    while j < n:
        v = _iast_vowel_at(s, j)
        if v:
            vowel_positions.append((j, len(v), v))
            j += len(v)
        else:
            j += 1
    syllables: List[Dict[str, Any]] = []
    prev_end = 0
    for (vpos, vlen, vtext) in vowel_positions:
        start = prev_end
        vowel_end = vpos + vlen
        end = vowel_end
        while end < n and s[end] in ("ṃ", "ḥ", "ṁ"):
            end += 1
        syllables.append({"text": s[start:end], "vowel": vtext, "vowel_start": vpos,
                          "vowel_end_raw": vowel_end, "start": start, "end": end})
        prev_end = end
    if syllables and prev_end < n:
        syllables[-1]["text"] += s[prev_end:n]
        syllables[-1]["end"] = n
    return syllables


def iast_classify_guru_laghu(syllables: List[Dict[str, Any]], s: str) -> List[Dict[str, Any]]:
    """Classify each syllable per chandas-3's first four (phonetic)
    criteria only -- अनुस्वार, दीर्घ, विसर्ग, संयोग. The fifth criterion
    (पादान्त) is a verse-position fact, not a phonetic one, and is applied
    separately by the caller so the two are never silently conflated."""
    marks = []
    for idx, syl in enumerate(syllables):
        reasons = []
        if syl["text"].endswith("ṃ") or syl["text"].endswith("ṁ"):
            reasons.append("anusvara")
        if syl["text"].endswith("ḥ"):
            reasons.append("visarga")
        if syl["vowel"] in IAST_VOWELS_LONG:
            reasons.append("dirgha")
        if idx + 1 < len(syllables):
            gap = s[syl["end"]:syllables[idx + 1]["vowel_start"]]
            if _iast_consonant_count(gap) >= 2:
                reasons.append("samyoga")
        marks.append({"text": syl["text"], "guru": bool(reasons), "reasons": reasons})
    return marks


class SanskritGrammarEngine:
    """Single evolving evidence engine for the five-śloka benchmark."""

    def __init__(self, *, library_only: bool = True, library_dir: Optional[str] = None):
        self.version = ENGINE_VERSION
        self.library_only = library_only
        self.external_web_content_used_for_grammar = False
        self.fuzzy_matching = False
        self.generalized_generation = False
        self.registries: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
            d: {} for d in ("subanta", "tinganta", "nonfinite", "krtanta", "pratyaya", "sandhi", "samasa")
        }
        self.sandhi_reverse: Dict[str, List[Dict[str, Any]]] = {}
        self.sandhi_rules: Dict[str, Dict[str, Any]] = {}
        self.source_assertions: List[Dict[str, Any]] = []
        self.audit_log: List[Dict[str, Any]] = []
        self.benchmark = BENCHMARK_VERSES

        # Directory-resident Library file. This is the concrete mechanism
        # requested for Stage 33: validate/reference grammar components
        # against the actual file sitting next to the engine, not only
        # against data embedded in this module.
        self.library = load_library_template(Path(library_dir) if library_dir else None)
        self.library_available = self.library is not None
        self.audit_log.append({
            "operation": "load_library_template",
            "filename": LIBRARY_TEMPLATE_FILENAME,
            "found": self.library_available,
            "path": self.library["path"] if self.library else None,
            "semantics": "Directory-resident Library file loaded at runtime for cross-validation and component evidence." if self.library_available
                         else "Library file not found next to the engine; falling back to embedded KNOWN_FORM_EVIDENCE only.",
        })

        # Stage 34: second, richer directory-resident Library file.
        self.library_v81 = load_library_v81(Path(library_dir) if library_dir else None)
        self.library_v81_available = self.library_v81 is not None
        self.audit_log.append({
            "operation": "load_library_v81",
            "filename": LIBRARY_V81_FILENAME,
            "found": self.library_v81_available,
            "path": self.library_v81["path"] if self.library_v81 else None,
            "semantics": "Directory-resident v8.1 Library file loaded at runtime for Component 5/4/9 evidence." if self.library_v81_available
                         else "v8.1 Library file not found next to the engine; Component 5/4/9 fall back to the v0.1 template file or embedded evidence.",
        })

        # Stage 35: third directory-resident Library file, possibly found
        # in a different directory than the engine (see LIBRARY_SEARCH_DIRS_EXTRA).
        self.library_deva = load_library_deva(Path(library_dir) if library_dir else None)
        self.library_deva_available = self.library_deva is not None
        self.audit_log.append({
            "operation": "load_library_deva",
            "filename": LIBRARY_DEVA_FILENAME,
            "found": self.library_deva_available,
            "path": self.library_deva["path"] if self.library_deva else None,
            "semantics": "Directory-resident (possibly external-directory) Library file loaded at runtime for Component 6/7 evidence." if self.library_deva_available
                         else "deva.json Library file not found in the engine's directory or any configured extra search directory; Component 6/7 stay at their existing (lower) coverage.",
        })

        # Stage 38: fifth directory-resident Library file, 1.1.1-only,
        # used solely to fill Component-5 stem gaps the v8.1 file leaves
        # open for that verse (see LIBRARY_COMPREHENSIVE_FILENAME).
        self.library_comprehensive = load_library_comprehensive(Path(library_dir) if library_dir else None)
        self.library_comprehensive_available = self.library_comprehensive is not None
        self.audit_log.append({
            "operation": "load_library_comprehensive",
            "filename": LIBRARY_COMPREHENSIVE_FILENAME,
            "found": self.library_comprehensive_available,
            "path": self.library_comprehensive["path"] if self.library_comprehensive else None,
            "semantics": "1.1.1-only directory Library file loaded at runtime to fill Component-5 stem gaps the v8.1 file leaves open." if self.library_comprehensive_available
                         else "comprehensive-10-component-template.json not found; Component 5 stays at whatever the v8.1 file alone supplies.",
        })

        # Stage 42: sixth directory-resident Library file -- the SKD
        # dictionary, used only for Component-9 constituent attestation.
        self.library_skd = load_library_skd(Path(library_dir) if library_dir else None)
        self.library_skd_available = self.library_skd is not None
        self.audit_log.append({
            "operation": "load_library_skd",
            "filename": LIBRARY_SKD_FILENAME,
            "found": self.library_skd_available,
            "path": self.library_skd["path"] if self.library_skd else None,
            "entry_count": self.library_skd["raw_count"] if self.library_skd else None,
            "semantics": "Śabdakalpadruma dictionary loaded at runtime for Component-9 compound-member dictionary attestation (citation-only; never used to derive a new compound analysis)." if self.library_skd_available
                         else "skd_entries.json not found; Component 9 items are reported without dictionary attestation (not a fabricated substitute).",
        })

        # Stage 43: eighth directory-resident Library file -- Apte's
        # dictionary, used the same way as SKD (see _dictionary_attest_word).
        self.library_apte = load_library_apte(Path(library_dir) if library_dir else None)
        self.library_apte_available = self.library_apte is not None
        self.audit_log.append({
            "operation": "load_library_apte",
            "filename": LIBRARY_APTE_FILENAME,
            "found": self.library_apte_available,
            "path": self.library_apte["path"] if self.library_apte else None,
            "entry_count": self.library_apte["raw_count"] if self.library_apte else None,
            "semantics": "Apte's dictionary loaded at runtime for Component-8/9 constituent dictionary attestation, alongside SKD (citation-only)." if self.library_apte_available
                         else "apte_entries.json not found; attestation falls back to whichever other dictionary Library file(s) are available.",
        })

        self._seed_known_evidence()
        if self.library_available:
            self._seed_library_sandhi_evidence()

        # Stage 36: reference rulebooks (citation-only; see LIBRARY_RULEBOOK_FILENAMES docstring).
        self.rulebooks: Dict[str, Optional[Dict[str, Any]]] = {}
        for key in LIBRARY_RULEBOOK_FILENAMES:
            rb = load_rulebook(key, Path(library_dir) if library_dir else None)
            self.rulebooks[key] = rb
            self.audit_log.append({
                "operation": f"load_rulebook_{key}",
                "filename": LIBRARY_RULEBOOK_FILENAMES[key],
                "found": rb is not None,
                "path": rb["path"] if rb else None,
                "semantics": "Reference rulebook loaded for citation-only enrichment of already-asserted evidence." if rb
                             else f"{LIBRARY_RULEBOOK_FILENAMES[key]} not found; citations from this rulebook are omitted, not fabricated.",
            })

    # ------------------------------------------------------------------
    # Evidence seeding
    # ------------------------------------------------------------------

    def _seed_known_evidence(self) -> None:
        for rec in KNOWN_FORM_EVIDENCE:
            self.register(rec["domain"], rec)
        self.audit_log.append({
            "operation": "seed_known_evidence",
            "count": len(KNOWN_FORM_EVIDENCE),
            "semantics": "explicit evidence only; no generalized derivation",
        })

    def _library_verse(self, verse_id: str) -> Optional[Dict[str, Any]]:
        if not self.library_available:
            return None
        return self.library["by_verse"].get(verse_id)

    def _library_v81_verse(self, verse_id: str) -> Optional[Dict[str, Any]]:
        if not self.library_v81_available:
            return None
        return self.library_v81["by_verse"].get(verse_id)

    def _library_deva_verse(self, verse_id: str) -> Optional[Dict[str, Any]]:
        if not self.library_deva_available:
            return None
        return self.library_deva["by_verse"].get(verse_id)

    def _comprehensive_verse(self, verse_id: str) -> Optional[Dict[str, Any]]:
        if not self.library_comprehensive_available:
            return None
        return self.library_comprehensive["by_verse"].get(verse_id)

    def _comprehensive_extra_c5_stems(self, verse_id: str, existing_stems: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 38: fill Component-5 (Śabdarūpāṇi) stem gaps the v8.1
        file leaves open, using the comprehensive-10-component-template.json
        Library file -- ONLY for stems not already supplied by v8.1
        (never overrides/duplicates an existing stem), and ONLY for verses
        that file actually covers (in practice, 1.1.1 only)."""
        cv = self._comprehensive_verse(verse_id)
        if not cv:
            return {}
        c5 = cv.get("COMPONENT_5_shabdarupani", {}).get("shabdarupani", {})
        extra = {}
        for key, obj in c5.items():
            if key in ("note", "coverage_note", "stem_count") or key in existing_stems:
                continue
            if not isinstance(obj, dict):
                continue
            table = obj.get("declension_table")
            if not table:
                continue
            extra[key] = {"lemma": obj.get("lemma"), "gender": obj.get("gender"), "declension_table": table,
                          "source": LIBRARY_COMPREHENSIVE_FILENAME}
        return extra

    def _rulebook_citation(self, citation_map: Dict[str, Any], surface: str) -> Optional[Dict[str, Any]]:
        """Look up `surface` in a citation map, resolve its rulebook
        key/section/rule_id against the *actually loaded* rulebook file,
        and return a verified citation dict -- or None if the map has no
        entry, the rulebook isn't reachable, or the rule_id isn't actually
        present in the file (the last case should not happen for entries
        the author hand-verified, but is checked anyway rather than
        trusted blindly)."""
        entry = citation_map.get(surface)
        if not entry:
            return None
        rb_key, section, rule_id, note = entry
        rb = self.rulebooks.get(rb_key)
        if not rb:
            return None
        rule = _find_rule_in_rulebook(rb, rule_id, section)
        if not rule:
            return None
        return _citation_from_rule(rb["filename"], rule, note)

    def _c3_padavigraha(self, verse_id: str, words: List[str], c5_stems: Dict[str, Any],
                         v81_padavigraha: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> Dict[str, Any]:
        """Component 3 (Pada-vigraha).

        Stage 41 makes the v8.1 Library file's own per-word pada_vigraha
        entry (see _v81_padavigraha) the PRIMARY source for each
        Component-1 word: a real Library SOURCE_ASSERTION carrying
        meaning, etymology, morphology and grammatical role -- not just
        confirmation that an inflected form exists somewhere in a
        declension table. It covers indeclinables and verbs too (Component
        5 cannot, since neither has a case table), e.g. परिपप्रच्छ (1.1.1,
        a verb) now gets real evidence for the first time.

        Words the v8.1 file has no non-pending entry for fall back to the
        Stage-36 mechanism: an EXACT cell match inside Component 5's own
        declension tables for this verse (COMPUTED_EVIDENCE, not a Library
        assertion -- the same mechanism Stage 16's
        build_subanta_registry/lookup_subanta used). Words matched neither
        way are listed as unmatched, never guessed at. The join between
        Component 1's word and either source's own word field uses
        _c3_join_key (see its docstring) -- exact matching on a known,
        documented formatting/orthography convention only, never fuzzy
        matching between different words; a genuine textual-variant
        mismatch (e.g. 1.1.4's द्युतिमान् vs the v8.1 file's मतिमान् at the
        same position -- the Library source text itself reads द्युतिमान्,
        confirmed against sa_rAmAyaNa.txt) is deliberately left unmatched
        rather than bridged."""
        # Consumed as a queue (not re-read) so a repeated surface form
        # (e.g. कः occurring four times in 1.1.3) draws on each available
        # v8.1 entry at most once, in the same left-to-right order both
        # lists enumerate the verse -- never lets one occurrence's real
        # entry stand in for another occurrence the Library file itself
        # left needs_review. See _v81_padavigraha's docstring.
        v81_queues: Dict[str, List[Dict[str, Any]]] = {k: list(v) for k, v in (v81_padavigraha or {}).items()}
        matched: List[Dict[str, Any]] = []
        unmatched: List[str] = []
        for word in words:
            key = _c3_join_key(word)
            queue = v81_queues.get(key)
            v81_item = queue.pop(0) if queue else None
            if v81_item:
                matched.append({
                    "word": word,
                    "status": STATUS_SOURCE_ASSERTION,
                    "pos": v81_item.get("pos"),
                    "gender": v81_item.get("gender"),
                    "number": v81_item.get("number"),
                    "case": v81_item.get("case"),
                    "meaning": v81_item.get("meaning"),
                    "etymology": v81_item.get("etymology"),
                    "morphology": v81_item.get("morphology"),
                    "role": v81_item.get("role"),
                    "method": "v81_library_pada_vigraha",
                    "source": LIBRARY_V81_FILENAME,
                })
                continue
            word_key = word.replace("-", "")
            hits = []
            for stem_key, stem in c5_stems.items():
                table = stem.get("declension_table", {})
                headers = table.get("headers") or []
                for row in table.get("rows", []):
                    if not row or len(row) != len(headers):
                        continue
                    case = row[0]
                    for idx, number in enumerate(headers[1:], start=1):
                        if row[idx] == word_key:
                            hits.append({"lemma": stem.get("lemma", stem_key), "case": case, "number": number})
            if len(hits) == 1:
                matched.append({"word": word, "status": STATUS_COMPUTED, "match": hits[0],
                                 "method": "exact_declension_table_lookup"})
            elif len(hits) > 1:
                matched.append({"word": word, "status": STATUS_AMBIGUOUS, "matches": hits,
                                 "method": "exact_declension_table_lookup"})
            else:
                unmatched.append(word)
        if not matched:
            return self._component_stub("COMPONENT_3_padavigraha", verse_id, STATUS_GAP,
                                        "Component 3 must reconcile to Component 1; only explicit evidence is promoted.")
        any_source_assertion = any(m["status"] == STATUS_SOURCE_ASSERTION for m in matched)
        any_computed = any(m["status"] == STATUS_COMPUTED for m in matched)
        if any_source_assertion:
            status = STATUS_SOURCE_ASSERTION
        elif any_computed:
            status = STATUS_COMPUTED
        else:
            status = STATUS_AMBIGUOUS
        return {
            "status": status,
            "verse": verse_id,
            "note": "Primary source: the v8.1 Library file's own per-word pada_vigraha entry (meaning, etymology, "
                    "morphology, role), where present and not marked needs_review. Words it does not cover fall "
                    "back to a deterministic exact-cell lookup against Component 5's declension tables for this "
                    "verse (COMPUTED_EVIDENCE). Unmatched words are listed separately, not guessed.",
            "matched_words": matched,
            "unmatched_words": unmatched,
            "method": "v81_library_primary_component5_computed_fallback",
        }

    def _seed_library_sandhi_evidence(self) -> None:
        """Register Component-8 Sandhi items straight from the directory
        Library file into the same sandhi registry used by lookup_sandhi(),
        so directory-sourced records are queryable exactly like the
        embedded fallback list. Duplicate surfaces (already present via
        KNOWN_FORM_EVIDENCE) are not re-registered."""
        added = 0
        for verse_id, verse in self.library["by_verse"].items():
            c8 = verse.get("components", {}).get("COMPONENT_8_sandhi", {})
            for item in c8.get("items", []):
                result = item.get("result")
                original = item.get("original")
                if not result or not original:
                    continue
                key = exact_key(result)
                if key in self.registries["sandhi"]:
                    continue  # already present from KNOWN_FORM_EVIDENCE; don't duplicate
                rec = {
                    "surface": result,
                    "domain": "sandhi",
                    "status": STATUS_MATCH,
                    "analysis": f"{original} → {result}" + (f" ({item['type']})" if item.get("type") else ""),
                    "source": LIBRARY_TEMPLATE_FILENAME,
                    "verse_id": verse_id,
                }
                self.register("sandhi", rec)
                added += 1
        self.audit_log.append({
            "operation": "seed_library_sandhi_evidence",
            "newly_registered_from_directory_file": added,
            "semantics": "Component-8 sandhi items read directly from the Library JSON on disk.",
        })

    def register(self, domain: str, record: Dict[str, Any]) -> None:
        if domain not in self.registries:
            raise ValueError(f"Unsupported domain: {domain}")
        surface = record.get("surface")
        if not surface:
            return
        self.registries[domain].setdefault(exact_key(surface), []).append(dict(record))

    def register_sandhi(self, record: Dict[str, Any]) -> None:
        self.register("sandhi", record)
        original = record.get("original")
        result = record.get("result")
        if original:
            self.registries["sandhi"].setdefault(exact_key(original), []).append(dict(record))
        if result:
            self.sandhi_reverse.setdefault(exact_key(result), []).append(dict(record))

    def register_sandhi_rule(self, record: Dict[str, Any]) -> None:
        if record.get("id"):
            self.sandhi_rules[record["id"]] = dict(record)

    def _lookup(self, domain: str, value: str) -> LookupResult:
        matches = self.registries[domain].get(exact_key(value), [])
        if len(matches) == 1:
            return LookupResult(STATUS_MATCH, domain, value, matches)
        if len(matches) > 1:
            return LookupResult(STATUS_AMBIGUOUS, domain, value, matches)
        return LookupResult(STATUS_GAP, domain, value, [], "No exact Library-supported record is registered.")

    def lookup(self, domain: str, surface: str) -> Dict[str, Any]:
        return self._lookup(domain, surface).as_dict()

    def lookup_subanta(self, surface: str) -> Dict[str, Any]: return self.lookup("subanta", surface)
    def lookup_tinganta(self, surface: str) -> Dict[str, Any]: return self.lookup("tinganta", surface)
    def lookup_nonfinite(self, surface: str) -> Dict[str, Any]: return self.lookup("nonfinite", surface)
    def lookup_krtanta(self, surface: str) -> Dict[str, Any]: return self.lookup("krtanta", surface)
    def lookup_pratyaya(self, surface: str) -> Dict[str, Any]: return self.lookup("pratyaya", surface)
    def lookup_sandhi(self, surface: str) -> Dict[str, Any]: return self.lookup("sandhi", surface)

    def reverse_sandhi(self, result: str) -> Dict[str, Any]:
        matches = self.sandhi_reverse.get(exact_key(result), [])
        if len(matches) == 1:
            return {"status": STATUS_MATCH, "domain": "sandhi_reverse", "query": result, "matches": matches}
        if len(matches) > 1:
            return {"status": STATUS_AMBIGUOUS, "domain": "sandhi_reverse", "query": result, "matches": matches}
        return {"status": STATUS_GAP, "domain": "sandhi_reverse", "query": result,
                "reason": "No exact Library-supported reverse Sandhi record is registered."}

    def benchmark_manifest(self) -> Dict[str, Any]:
        return {
            "benchmark_id": BENCHMARK_ID,
            "scope": "Vālmīki Rāmāyaṇa, Bālakāṇḍa, Sarga 1, ślokas 1.1.1–1.1.5",
            "source_file": "Library: sa_rAmAyaNa.txt",
            "source_refs": [v["source_ref"] for v in self.benchmark.values()],
            "verse_count": len(self.benchmark),
            "fixed": True,
            "expansion_before_stage30_review": False,
            "library_template_file": LIBRARY_TEMPLATE_FILENAME,
            "library_template_found_on_disk": self.library_available,
            "library_v81_file": LIBRARY_V81_FILENAME,
            "library_v81_found_on_disk": self.library_v81_available,
            "library_deva_file": LIBRARY_DEVA_FILENAME,
            "library_deva_found_on_disk": self.library_deva_available,
            "library_skd_file": LIBRARY_SKD_FILENAME,
            "library_skd_found_on_disk": self.library_skd_available,
            "library_skd_entry_count": self.library_skd["raw_count"] if self.library_skd_available else None,
            "library_apte_file": LIBRARY_APTE_FILENAME,
            "library_apte_found_on_disk": self.library_apte_available,
            "library_apte_entry_count": self.library_apte["raw_count"] if self.library_apte_available else None,
            "rulebooks_found_on_disk": {k: (v is not None) for k, v in self.rulebooks.items()},
        }

    # ------------------------------------------------------------------
    # Component 1 + directory cross-validation
    # ------------------------------------------------------------------

    def _component1(self, verse: Dict[str, Any]) -> Dict[str, Any]:
        words = verse["padaccheda"]
        return {
            "status": STATUS_SOURCE_ASSERTION,
            "source_ref": verse["source_ref"],
            "padaccheda": words,
            "word_count": len(words),
            "authoritative": True,
        }

    def _cross_validate_component1(self, verse_id: str, embedded_words: List[str]) -> Dict[str, Any]:
        """Compare the engine's embedded Component-1 word inventory against
        the same verse's Component-1 word inventory in the directory
        Library file. This is the concrete "validate using the directory
        entries" check: it does not just borrow content from the file, it
        confirms the two sources agree before anything downstream relies
        on Component 1 being authoritative."""
        if not self.library_available:
            return {"status": "SKIPPED", "reason": "Library file not found on disk."}
        lib_verse = self._library_verse(verse_id)
        if not lib_verse:
            return {"status": "SKIPPED", "reason": f"Verse {verse_id} not present in Library file."}
        lib_c1 = lib_verse.get("components", {}).get("COMPONENT_1_padaccheda", {})
        lib_rows = lib_c1.get("padaccheda", [])
        lib_words = [row[0] if isinstance(row, list) and row else row for row in lib_rows]
        if lib_words == embedded_words:
            return {"status": "MATCH", "word_count": len(lib_words)}
        return {
            "status": "MISMATCH",
            "embedded_word_count": len(embedded_words),
            "library_word_count": len(lib_words),
            "embedded_words": embedded_words,
            "library_words": lib_words,
        }

    def _cross_validate_component1_v81(self, verse_id: str, embedded_words: List[str]) -> Dict[str, Any]:
        """Word-COUNT-only cross-validation against the second (v8.1)
        Library file. That file's orthography is anusvāra-normalized
        throughout (a whole-file convention, e.g. "नारदं" vs the embedded
        "नारदम्"), so an exact per-word string comparison would falsely flag
        nearly every word; comparing counts still catches genuine
        segmentation differences (e.g. a verse where a token is fused into
        its neighbour) without that noise."""
        if not self.library_v81_available:
            return {"status": "SKIPPED", "reason": "v8.1 Library file not found on disk."}
        lv = self._library_v81_verse(verse_id)
        if not lv:
            return {"status": "SKIPPED", "reason": f"Verse {verse_id} not present in v8.1 Library file."}
        rows = lv.get("COMPONENT_1_padaccheda", {}).get("padaccheda", [])
        v81_count = len(rows)
        embedded_count = len(embedded_words)
        return {
            "status": "MATCH_COUNT" if v81_count == embedded_count else "MISMATCH_COUNT",
            "embedded_word_count": embedded_count,
            "v81_word_count": v81_count,
            "note": "Count-only comparison (see LIBRARY_V81_FILENAME docstring for why exact string comparison is not used here).",
        }

    def _component_stub(self, component: str, verse_id: str, status: str, note: str,
                        evidence: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        return {
            "status": status,
            "verse": verse_id,
            "note": note,
            "evidence": evidence or [],
        }

    def _known_for_verse(self, words: Iterable[str], domains: Iterable[str]) -> List[Dict[str, Any]]:
        wanted = set(words)
        doms = set(domains)
        out = []
        for rec in KNOWN_FORM_EVIDENCE:
            if rec.get("surface") in wanted and rec.get("domain") in doms:
                out.append(rec)
        return out

    def _known_sandhi_for_verse(self, verse_id: str) -> List[Dict[str, Any]]:
        """Sandhi evidence for a verse, preferring directory-sourced
        records (registered in self.registries["sandhi"] with this verse's
        id) and falling back to the embedded KNOWN_FORM_EVIDENCE list only
        where directory evidence is unavailable."""
        out = [rec for surfaces in self.registries["sandhi"].values() for rec in surfaces
               if rec.get("verse_id") == verse_id]
        if out:
            # de-duplicate by surface, preserving first occurrence
            seen = set()
            deduped = []
            for rec in out:
                key = rec.get("surface")
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(rec)
            return deduped
        return [r for r in KNOWN_FORM_EVIDENCE
                if r.get("domain") == "sandhi" and (r.get("verse_id") == verse_id
                or (verse_id == "1.1.1" and r.get("surface") in {"वाल्मीकिर्मुनिपुङ्गवम्", "वाग्-विदाम्"}))]

    # ------------------------------------------------------------------
    # Directory-driven component derivation (Stage 33)
    # ------------------------------------------------------------------

    def _library_anvaya(self, verse_id: str) -> Dict[str, Any]:
        lv = self._library_verse(verse_id)
        if not lv:
            return self._component_stub("COMPONENT_2_anvaya", verse_id, STATUS_GAP,
                                        "Full verse-specific Anvaya requires explicit Library-supported analysis before promotion.")
        c2 = lv.get("components", {}).get("COMPONENT_2_anvaya", {})
        anvaya_sa = c2.get("anvaya_sa")
        if not anvaya_sa or _is_pending(c2.get("status")):
            return self._component_stub("COMPONENT_2_anvaya", verse_id, STATUS_GAP,
                                        "Library file does not carry a non-pending Anvaya for this verse.")
        return {
            "status": STATUS_SOURCE_ASSERTION,
            "verse": verse_id,
            "anvaya_sa": anvaya_sa,
            "translation_en": c2.get("translation_en"),
            "source": LIBRARY_TEMPLATE_FILENAME,
        }

    def _library_karaka(self, verse_id: str) -> Dict[str, Any]:
        # Stage 34: prefer the richer v8.1 file, which has structured
        # present/absent Kāraka for all five verses.
        v81 = self._v81_karaka(verse_id)
        if v81:
            return v81
        lv = self._library_verse(verse_id)
        if not lv:
            if verse_id == "1.1.1":
                # Embedded last-resort fallback for degraded (no-directory-file) mode only.
                return {"status": STATUS_SOURCE_ASSERTION, "verse": verse_id,
                        "roles": {"karta": "वाल्मीकिः", "karma": "नारदम्"},
                        "note": "Template assertion; other roles are retained as stated there.",
                        "source": "embedded_fallback (directory Library file unavailable)"}
            return self._component_stub("COMPONENT_4_karaka", verse_id, STATUS_NOT_ASSERTED,
                                        "Verse-specific complete semantic role analysis not fully Library-retrieved.")
        c4 = lv.get("components", {}).get("COMPONENT_4_karaka", {})
        if not c4 or _is_pending(c4.get("status")):
            note = c4.get("note") if isinstance(c4, dict) else None
            return self._component_stub("COMPONENT_4_karaka", verse_id, STATUS_NOT_ASSERTED,
                                        note or "Library file marks Kāraka analysis for this verse as pending/not overt.")
        roles = {k: v for k, v in c4.items() if k != "status"}
        return {
            "status": STATUS_SOURCE_ASSERTION,
            "verse": verse_id,
            "roles": roles,
            "source": LIBRARY_TEMPLATE_FILENAME,
        }

    def _library_samasa(self, verse_id: str) -> Dict[str, Any]:
        v81_items = self._v81_samasa(verse_id)
        lv = self._library_verse(verse_id)
        if not lv and not v81_items:
            if verse_id == "1.1.1":
                # Embedded last-resort fallback for degraded (no-directory-file) mode only.
                return {"status": STATUS_SOURCE_ASSERTION, "verse": verse_id,
                        "resolved_items": [
                            ["तपः-स्वाध्याय-निरतम्", "compound/derivational analysis in Library template"],
                            ["मुनि-पुङ्गवम्", "षष्ठीतत्पुरुषसमासः in Library template"],
                        ],
                        "pending_items": [],
                        "source": "embedded_fallback (directory Library file unavailable)"}
            return self._component_stub("COMPONENT_9_samasa", verse_id, STATUS_GAP,
                                        "Complete verse-specific Samāsa evidence is not yet fully retrieved from Library.")
        template_resolved, template_pending = [], []
        if lv:
            c9 = lv.get("components", {}).get("COMPONENT_9_samasa", {})
            for row in c9.get("items", []):
                text = " ".join(str(x) for x in row)
                (template_pending if _is_pending(text) else template_resolved).append(row)
        v81_resolved = [it for it in v81_items if it["status"] == STATUS_SOURCE_ASSERTION]
        v81_ambiguous = [it for it in v81_items if it["status"] == STATUS_AMBIGUOUS]
        if not (template_resolved or template_pending or v81_items):
            return self._component_stub("COMPONENT_9_samasa", verse_id, STATUS_GAP,
                                        "No Samāsa evidence found in either directory Library file for this verse.")
        status = STATUS_SOURCE_ASSERTION if (template_resolved or v81_resolved) else STATUS_AMBIGUOUS
        return {
            "status": status,
            "verse": verse_id,
            "resolved_items": template_resolved + v81_resolved,
            "ambiguous_items": v81_ambiguous,
            "pending_items": template_pending,
            "note": "Items whose Library classification is marked pending are kept separate and not promoted; "
                    "v8.1-sourced items whose compound_type is hedged between multiple options are kept as AMBIGUOUS. "
                    + ("Stage 42/43: each v8.1 item's compound-member breakdown also carries independent "
                       "dictionary attestation (see each item's dictionary_attestation field, checked against "
                       + ("SKD and Apte" if (self.library_skd_available and self.library_apte_available)
                          else "SKD" if self.library_skd_available else "Apte")
                       + ") -- citation-only, never promoting an item's own status."
                       if (self.library_skd_available or self.library_apte_available) else
                       "Stage 42/43 dictionary attestation was not available this run (neither skd_entries.json "
                       "nor apte_entries.json was found on disk)."),
            "sources": [s for s in (LIBRARY_TEMPLATE_FILENAME if lv else None, LIBRARY_V81_FILENAME if v81_items else None,
                                     LIBRARY_SKD_FILENAME if self.library_skd_available else None,
                                     LIBRARY_APTE_FILENAME if self.library_apte_available else None) if s],
            "skd_library_available": self.library_skd_available,
            "apte_library_available": self.library_apte_available,
        }

    def _library_sandhi_component(self, verse_id: str) -> Dict[str, Any]:
        known_sandhi = self._known_sandhi_for_verse(verse_id)
        # Stage 43: attach independent dictionary attestation of each
        # evidence item's own pre-sandhi constituent words, parsed
        # deterministically from that item's existing `analysis` string.
        # Citation-only -- never changes an item's own status. `known_sandhi`
        # can hold direct references into the module-level KNOWN_FORM_EVIDENCE
        # list (its fallback branch), so items are shallow-copied before any
        # new key is attached, never mutated in place.
        annotated = []
        for item in known_sandhi:
            item2 = dict(item)
            if self.library_skd_available or self.library_apte_available:
                constituents = self._sandhi_constituents_from_analysis(item2.get("analysis", ""))
                if constituents:
                    item2["dictionary_attestation"] = [self._dictionary_attest_word(w) for w in constituents]
            annotated.append(item2)
        return self._component_stub(
            "COMPONENT_8_sandhi", verse_id,
            STATUS_MATCH if known_sandhi else STATUS_GAP,
            "Only explicitly attested Sandhi operations are promoted; no generalized Sandhi generation."
            + (" Sourced from the directory Library file." if self.library_available else " Directory Library file unavailable; embedded fallback evidence used.")
            + (" Stage 43: each item's pre-sandhi constituent words also carry independent dictionary "
               "attestation (see each item's dictionary_attestation field) -- citation-only." if (self.library_skd_available or self.library_apte_available) else ""),
            annotated,
        )

    def _library_chandas(self, verse_id: str) -> Dict[str, Any]:
        lv = self._library_verse(verse_id)
        if not lv:
            return self._component_stub("COMPONENT_10_chandas", verse_id, STATUS_GAP,
                                        "Chandas remains source/template assertion unless independently validated in Library.")
        c10 = lv.get("components", {}).get("COMPONENT_10_chandas", {})
        chandas_name = c10.get("chandas_name")
        if not chandas_name:
            return self._component_stub("COMPONENT_10_chandas", verse_id, STATUS_GAP,
                                        "Library file carries no chandas_name for this verse.")
        scansion_pending = _is_pending(c10.get("status")) or "scansion" not in c10
        template_alankara_pending = _is_pending(c10.get("alankara_status")) or c10.get("alankara_status") is None

        # Stage 40: the v0.1 template file's own 'alankara_status' is only
        # ever a bare completion flag (no named figures, not even for
        # 1.1.1) -- the v8.1 file carries the actual, non-pending,
        # per-verse named-figure content for all five verses. Prefer it
        # whenever available; fall back to the thin template-only status
        # (NOT_ASSERTED for 4 of 5 verses) only if v8.1 has nothing usable.
        v81_alankara = self._v81_alankara(verse_id)
        result = {
            "status": STATUS_SOURCE_ASSERTION,
            "verse": verse_id,
            "scope": "meter_identification_only",
            "chandas_name": chandas_name,
            "scansion": c10.get("scansion"),
            "scansion_status": STATUS_GAP if scansion_pending else STATUS_SOURCE_ASSERTION,
            "note": "Meter name is a Library source assertion; full syllabic scansion is computed separately "
                    "(see syllabic_scansion_computed); alaṅkāra is sourced from the v8.1 file where available.",
            "source": LIBRARY_TEMPLATE_FILENAME,
        }
        if v81_alankara:
            result["alankara_status"] = STATUS_SOURCE_ASSERTION
            result["alankara"] = v81_alankara["items"]
            result["alankara_source"] = LIBRARY_V81_FILENAME
            result["alankara_quality_status_sa"] = v81_alankara.get("quality_status_sa")
        else:
            result["alankara_status"] = STATUS_NOT_ASSERTED if template_alankara_pending else STATUS_SOURCE_ASSERTION
            result["alankara"] = None
        return result

    def _syllabic_scansion(self, verse_id: str) -> Optional[Dict[str, Any]]:
        """Stage 39: COMPUTED_EVIDENCE full syllabic guru/laghu scansion,
        derived from the verse's own immutable IAST text and grounded in
        chandas_rulebook.json's chandas-2 (syllable definition), chandas-3
        (guru/laghu test) and chandas-6 (अनुष्टुप् 8-syllable/पाद structure
        and its 5th/6th/7th-syllable constraint). All three rules are
        looked up and verified against the actual rulebook file before any
        scansion is computed -- if the file is unreachable or any of the
        three ids is missing, this returns None and Component 10 falls
        back to its pre-Stage-39 meter-name-only behaviour, exactly like
        every other Library-gated mechanism in this engine.

        Pāda boundaries are NOT guessed: अनुष्टुप् is asserted (chandas-6)
        to have exactly 4 pādas of 8 syllables each, so a half-verse
        (split at the source text's own '/' pause mark) is only divided
        into two 8-syllable pādas when it is independently confirmed to
        contain exactly 16 syllables; a half that doesn't is left
        unsplit and flagged, never forced."""
        rb = self.rulebooks.get("chandas")
        if not rb:
            return None
        rule2 = _find_rule_in_rulebook(rb, "chandas-2", "general_rules")
        rule3 = _find_rule_in_rulebook(rb, "chandas-3", "general_rules")
        rule6 = _find_rule_in_rulebook(rb, "chandas-6", "named_metres")
        if not (rule2 and rule3 and rule6):
            return None

        v = self.benchmark.get(verse_id)
        if not v or not v.get("iast"):
            return None
        halves = [h.strip() for h in v["iast"].split("/")]
        if len(halves) != 2:
            return {"status": STATUS_GAP, "note": f"Expected 2 half-verses separated by '/', found {len(halves)}; scansion not computed."}

        padas: List[Dict[str, Any]] = []
        half_notes = []
        for half_idx, half in enumerate(halves):
            sylls = iast_syllabify(half)
            if len(sylls) != 16:
                half_notes.append(f"Half {half_idx + 1} has {len(sylls)} syllables, not the 16 chandas-6 "
                                   f"requires for two 8-syllable pādas; that half's pāda split was not computed.")
                continue
            marks = iast_classify_guru_laghu(sylls, half.replace(" ", "").replace("'", "").replace("-", ""))
            for p in range(2):
                pada_num = half_idx * 2 + p + 1
                pm = marks[p * 8:(p + 1) * 8]
                pattern = "".join("G" if m["guru"] else "L" for m in pm)
                expected7 = "G" if pada_num in (1, 3) else "L"
                mismatches = []
                if pattern[4] != "L":
                    mismatches.append(f"5th syllable expected लघु (chandas-6), computed {'गुरु' if pattern[4]=='G' else 'लघु'}")
                if pattern[5] != "G":
                    mismatches.append(f"6th syllable expected गुरु (chandas-6), computed {'गुरु' if pattern[5]=='G' else 'लघु'}")
                if pattern[6] != expected7:
                    mismatches.append(f"7th syllable expected {'गुरु' if expected7=='G' else 'लघु'} "
                                       f"(chandas-6, pāda {pada_num}), computed {'गुरु' if pattern[6]=='G' else 'लघु'}")
                padas.append({
                    "pada": pada_num,
                    "syllables": [m["text"] for m in pm],
                    "pattern": pattern,
                    "pattern_note": "G=गुरु, L=लघु; positions 1-8. Position 8 (पादान्तः) is conventionally counted "
                                    "गुरु regardless of its own phonetic weight (chandas-3, criterion 5) -- shown "
                                    "here as computed (criteria 1-4 only) so the two are never conflated.",
                    "chandas6_constraint_check": "MATCH" if not mismatches else "MISMATCH",
                    "chandas6_constraint_notes": mismatches,
                })
        if not padas:
            return {"status": STATUS_GAP, "note": "; ".join(half_notes) or "No pāda could be scanned."}

        # Self-check: 1.1.1's Library-asserted 4-line scansion (from the
        # v0.1 template file) gives an independent pāda split to compare
        # against, with zero risk of the comparison being circular.
        # NOTE: the Library's own "scansion" field (1.1.1 only) is written
        # in Devanagari, while this computation works from the IAST source
        # text -- an early version of this check compared the two as
        # plain strings and reported a false MISMATCH purely from the
        # script difference (the underlying words matched exactly on
        # manual inspection). Rather than build and risk an unverified
        # transliteration layer just to make that comparison possible,
        # this checks only what can be compared without one: the number
        # of Library-asserted lines against the number of computed pādas.
        cross_check = None
        lv = self._library_verse(verse_id)
        if lv:
            lib_scansion = lv.get("components", {}).get("COMPONENT_10_chandas", {}).get("scansion")
            if lib_scansion:
                cross_check = {
                    "compared": "pāda COUNT only (Library's scansion field is Devanagari; this computation is "
                                "IAST-based, and no transliteration layer exists yet to compare the text itself)",
                    "library_pada_count": len(lib_scansion),
                    "computed_pada_count": len(padas),
                    "status": "MATCH" if len(lib_scansion) == len(padas) else "MISMATCH",
                }

        return {
            "status": STATUS_COMPUTED,
            "verse": verse_id,
            "padas": padas,
            "half_notes": half_notes,
            "library_pada_cross_validation": cross_check,
            "note": "Guru/laghu computed deterministically from the immutable IAST source text per chandas-3's "
                    "four phonetic criteria (पादान्त, criterion 5, kept separate -- see each pāda's pattern_note); "
                    "pāda boundaries computed only where a half-verse independently has exactly 16 syllables, "
                    "per chandas-6. This is COMPUTED_EVIDENCE, not a Library source assertion.",
            "grounding_citations": [
                _citation_from_rule(rb["filename"], rule2, "Syllable (वर्ण) definition."),
                _citation_from_rule(rb["filename"], rule3, "Five-fold गुरु/लघु test (पादान्त criterion applied separately, see above)."),
                _citation_from_rule(rb["filename"], rule6, "अनुष्टुप् structure and 5th/6th/7th-syllable constraint."),
            ],
        }

    # ------------------------------------------------------------------
    # v8.1 Library-file derivation (Stage 34)
    # ------------------------------------------------------------------

    def _v81_shabdarupani(self, verse_id: str) -> Dict[str, Any]:
        """Component 5 (Śabdarūpāṇi / declension tables), sourced from the
        v8.1 Library file. Previously this component was hardcoded GAP for
        every verse regardless of evidence; the v8.1 file supplies
        essentially complete 7-case x 3-number tables for nearly every
        declinable stem in all five verses."""
        lv = self._library_v81_verse(verse_id)
        if not lv:
            return self._component_stub("COMPONENT_5_shabdarupani", verse_id, STATUS_GAP,
                                        "Complete paradigms are not yet available for all declinables in these five verses.")
        c5 = lv.get("COMPONENT_5_shabdarupani", {}).get("shabdarupani", {})
        stems = {}
        skipped_note = None
        for key, obj in c5.items():
            if key == "note":
                skipped_note = obj
                continue
            if not isinstance(obj, dict) or _is_pending(obj.get("status")):
                continue
            table = obj.get("declension_table")
            if not table:
                continue
            stems[key] = {"lemma": obj.get("lemma"), "gender": obj.get("gender"), "declension_table": table}
        if not stems:
            return self._component_stub("COMPONENT_5_shabdarupani", verse_id, STATUS_GAP,
                                        "v8.1 Library file carries no non-pending declension tables for this verse.")
        return {
            "status": STATUS_SOURCE_ASSERTION,
            "verse": verse_id,
            "stems": stems,
            "stem_count": len(stems),
            "note": skipped_note,
            "source": LIBRARY_V81_FILENAME,
        }

    def _v81_padavigraha(self, verse_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Stage 41: Component 3 (Pada-vigraha), primary source.

        The v8.1 Library file carries its OWN per-word pada_vigraha record
        under COMPONENT_3_padavigraha -- meaning, etymology, morphology,
        grammatical role in the sentence, POS, gender/number/case -- for
        every word in all five verses, not just the declinables a
        declension-table cell-match can cover. This was never read by the
        engine before Stage 41; Component 3 was instead derived purely by
        COMPUTED_EVIDENCE cell-lookup against Component 5 (see
        _c3_padavigraha below), which can only ever confirm a word's
        inflected form, not its actual meaning or syntactic role, and
        cannot cover indeclinables or verbs at all (Component 5 has no
        table for those).

        Roughly a quarter of the file's per-word entries are themselves
        explicitly marked '_quality_status': 'needs_review' with an honest
        '_quality_note' (typically "No matching Component 3 scholarly
        entry exists in the source JSON; intentionally not fabricated.")
        and are all-empty-fields placeholders -- those are filtered out
        here exactly like any other pending Library marker, never
        promoted.

        Returns a dict keyed by _c3_join_key(item['word']) -> an in-order
        LIST of the raw (non-pending) items sharing that key, for the
        caller to join against Component 1's authoritative word list. A
        list, not a single item, because some words repeat within a verse
        (क, kaḥ, appearing four times in 1.1.3, three च occurrences in
        1.1.2) -- a plain single-item dict would let one occurrence's real
        entry silently stand in for every other occurrence of the same
        surface form, including ones the Library file itself explicitly
        marks needs_review (meaning it deliberately did NOT vouch for that
        specific occurrence). The caller consumes this list front-to-back,
        one item per matching Component-1 occurrence in reading order, so
        each pv item is used for at most the one C1 occurrence it
        legitimately corresponds to; a repeat beyond what the queue has
        correctly falls through to the computed fallback or stays
        unmatched, rather than reusing a stale entry. Returns {} if the
        v8.1 file is unreachable or has no usable data for this verse, so
        the caller falls back entirely to the existing computed
        cell-match."""
        lv = self._library_v81_verse(verse_id)
        if not lv:
            return {}
        items = lv.get("COMPONENT_3_padavigraha", {}).get("pada_vigraha", [])
        by_key: Dict[str, List[Dict[str, Any]]] = {}
        for it in items:
            if not isinstance(it, dict) or not it.get("word"):
                continue
            if it.get("_quality_status") is not None:
                continue
            by_key.setdefault(_c3_join_key(it["word"]), []).append(it)
        return by_key

    def _v81_karaka(self, verse_id: str) -> Optional[Dict[str, Any]]:
        """Component 4 (Kāraka), sourced from the v8.1 Library file, which
        carries an explicit present/absent status per role for all five
        verses (unlike the v0.1 template file, which only has non-pending
        Kāraka for 1.1.1, 1.1.4, 1.1.5). Returns None if the v8.1 file has
        no usable data for this verse, so the caller can fall back."""
        lv = self._library_v81_verse(verse_id)
        if not lv:
            return None
        c4 = lv.get("COMPONENT_4_karaka", {}).get("karaka", {})
        roles = {}
        for role, obj in c4.items():
            if role.startswith("_") or not isinstance(obj, dict):
                continue
            status = obj.get("status")
            if status not in ("present", "absent") or _is_pending(obj.get("_quality_status")):
                continue
            roles[role] = {"status": status, "word_ids": obj.get("word_ids", []), "display_sa": obj.get("display_sa")}
        if not roles:
            return None
        return {
            "status": STATUS_SOURCE_ASSERTION,
            "verse": verse_id,
            "roles": roles,
            "source": LIBRARY_V81_FILENAME,
        }

    def _dictionary_attest_word(self, word_deva: str) -> Dict[str, Any]:
        """Stage 43 (generalizes Stage 42's SKD-only _skd_attest_word):
        independently attest one Devanagari word/constituent against
        EVERY configured dictionary Library file (currently SKD and
        Apte), reporting a per-dictionary `sources` list rather than
        collapsing to a single boolean -- so which dictionary(ies)
        actually attested a word is never lost, per this project's
        source-provenance principle.

        For each dictionary, two, and only two, deterministic lookup
        attempts are made, in this order:

          1. EXACT -- the word's own SLP1 transliteration matched verbatim
             against that dictionary's headword (k1/k2).
          2. VISARGA-NORMALIZED -- if (1) fails, the same comparison with a
             single trailing visarga ('H') stripped from BOTH sides
             (already done to each index at load time; done here to the
             query). This exists because both dictionaries conventionally
             cite many headwords in a nominative-singular citation form
             (e.g. मुनि is headworded "muniH"), while a compound's
             non-final members or a sandhi'd phrase's pre-sandhi
             constituents are frequently bare stems (e.g. "muni"). This is
             a single, symmetric, documented normalization -- not
             fuzzy/approximate matching (cf. the identical justification
             already used for the count-only Component-1/v8.1
             cross-validation and for _c3_join_key's anusvāra fix).

        Neither attempt guesses at gender/stem-class to add other
        endings; a word that doesn't match in any configured dictionary is
        reported attested=False, not silently dropped or promoted. Known
        systematic spelling conventions NOT normalized here (guttural/
        anusvāra alternation, Bengali-typesetting consonant gemination)
        are left as an explicit, documented gap rather than chased with
        further heuristics -- see the Stage 42/43 CHANGELOG entries."""
        slp1 = devanagari_to_slp1(word_deva)
        result: Dict[str, Any] = {"constituent": word_deva, "slp1": slp1, "attested": False, "sources": []}
        if slp1 is None:
            result["note"] = "Word contains a character outside the engine's deterministic Devanagari→SLP1 table; dictionary lookup not attempted."
            return result
        stripped = slp1[:-1] if slp1.endswith("H") else slp1
        any_dict_loaded = False
        for dict_key, lib in (("skd", self.library_skd), ("apte", self.library_apte)):
            if lib is None:
                continue
            any_dict_loaded = True
            hits = lib["by_headword"].get(slp1)
            method = "exact"
            if not hits:
                hits = lib["by_headword_visarga_stripped"].get(stripped)
                method = "visarga_normalized"
            if hits:
                sample = hits[0].get("source_text", "")
                result["sources"].append({
                    "dictionary": dict_key,
                    "match_method": method,
                    "entry_ids": [h.get("id") for h in hits[:5]],
                    "entry_count": len(hits),
                    "sample_text_slp1": (sample[:200] + "…") if len(sample) > 200 else sample,
                })
        result["attested"] = bool(result["sources"])
        if not any_dict_loaded:
            result["note"] = "No dictionary Library file found on disk; attestation not attempted."
        elif not result["attested"]:
            result["note"] = "No exact (or visarga-normalized) headword match in any loaded dictionary; reported as a gap, not guessed."
        return result

    def _dictionary_attest_breakdown(self, breakdown: str) -> List[Dict[str, Any]]:
        """Stage 42/43: split a v8.1-supplied Component-9 'breakdown'
        string (e.g. "मुनि + पुंगवम्") on its own literal '+' separator --
        the exact delimiter that file itself uses, not a heuristic guess --
        and attest each resulting constituent against every configured
        dictionary."""
        if not breakdown:
            return []
        parts = [p.strip() for p in str(breakdown).split("+")]
        return [self._dictionary_attest_word(p) for p in parts if p]

    def _sandhi_constituents_from_analysis(self, analysis: str) -> List[str]:
        """Stage 43: extract the pre-sandhi constituent word(s) from a
        Component-8 evidence item's own 'analysis' string, deterministically,
        by undoing the exact, known formatting conventions that string
        already uses (never guessing at word boundaries the analysis
        itself doesn't state):

          1. Everything from the first '→' onward is the POST-sandhi
             result (plus, occasionally, a parenthetical note) -- discard it.
          2. Some hand-authored entries prefix the constituents with a
             rule-name label before a ':' (e.g. "विसर्गसन्धिः: वाल्मीकिः +
             मुनिपुङ्गवम्") -- if present, keep only the text after the
             last ':'.
          3. The remainder is one or more words joined by literal '+'
             (occasionally three, e.g. "कः + च + एकप्रियदर्शनः") -- split on
             it.

        Verified against every Component-8 analysis string in the current
        benchmark before use (16 items across 5 verses, both the
        single-':'-prefixed 1.1.1 item and every arrow-suffixed item)."""
        if not analysis:
            return []
        left = str(analysis).split("→", 1)[0]
        if ":" in left:
            left = left.rsplit(":", 1)[-1]
        parts = [p.strip() for p in left.split("+")]
        return [p for p in parts if p]

    def _v81_samasa(self, verse_id: str) -> List[Dict[str, Any]]:
        """Component 9 (Samāsa) items from the v8.1 Library file. Most
        entries there explicitly hedge their compound_type between two or
        three possibilities ("cannot be determined without further
        context"); those are surfaced as AMBIGUOUS, not SOURCE_ASSERTION,
        so the engine does not force a classification the Library itself
        declines to commit to."""
        lv = self._library_v81_verse(verse_id)
        if not lv:
            return []
        items = lv.get("COMPONENT_9_samasa", {}).get("samasa", [])
        out = []
        for it in items:
            if not isinstance(it, dict) or it.get("status") != "present":
                continue
            compound_type = it.get("compound_type") or ""
            hedged = _is_pending(compound_type) or "अशक्यम्" in compound_type or "/" in compound_type
            record = {
                "surface": it.get("word"),
                "domain": "samasa",
                "status": STATUS_AMBIGUOUS if hedged else STATUS_SOURCE_ASSERTION,
                "compound_type": it.get("compound_type"),
                "breakdown": it.get("breakdown"),
                "confidence": it.get("confidence"),
                "source": LIBRARY_V81_FILENAME,
                "verse_id": verse_id,
            }
            # Stage 42/43: independent dictionary attestation (SKD, and now
            # Apte too) of the compound's own constituent breakdown. Purely
            # additive -- never changes `status`/`compound_type` above,
            # whether the constituents attest or not.
            if (self.library_skd_available or self.library_apte_available) and it.get("breakdown"):
                record["dictionary_attestation"] = self._dictionary_attest_breakdown(it.get("breakdown"))
            out.append(record)
        return out

    def _v81_alankara(self, verse_id: str) -> Optional[Dict[str, Any]]:
        """Stage 40: Alaṅkāra evidence for Component 10, sourced from the
        v8.1 Library file, which carries an explicit, non-pending
        ('quality_status': 'present'/'उपलब्धम्') named-figure list for all
        five verses -- unlike the v0.1 template file, whose 'alankara_status'
        field is a bare completion flag with no actual figure content (only
        1.1.1 is even flagged complete, and even there it names nothing).
        Each returned item is enriched with a verified rulebook citation
        ONLY where ALANKARA_RULEBOOK_CITATION_MAP records that the citation
        was checked and genuinely matches the rulebook's own structural
        definition (see that map's docstring for the one deliberately
        withheld case). Returns None if the v8.1 file has no usable,
        non-pending alankara data for this verse, so the caller can fall
        back to the thinner v0.1-template-only status."""
        lv = self._library_v81_verse(verse_id)
        if not lv:
            return None
        c10 = lv.get("COMPONENT_10_chandas", {})
        quality = c10.get("quality_status") or c10.get("quality_status_sa")
        items_raw = c10.get("alankara")
        if _is_pending(quality) or not items_raw:
            return None
        rb = self.rulebooks.get("alankara")
        items = []
        for it in items_raw:
            if not isinstance(it, dict) or not it.get("name"):
                continue
            name = it["name"]
            entry = {"name": name, "definition": it.get("definition")}
            for map_key, (rule_id, section, note) in ALANKARA_RULEBOOK_CITATION_MAP.items():
                map_verse, name_prefix = map_key.split("|", 1)
                if map_verse == verse_id and name.startswith(name_prefix) and rb:
                    rule = _find_rule_in_rulebook(rb, rule_id, section)
                    if rule:
                        entry["rulebook_citation"] = _citation_from_rule(rb["filename"], rule, note)
                    break
            items.append(entry)
        return {
            "status": STATUS_SOURCE_ASSERTION,
            "verse": verse_id,
            "items": items,
            "quality_status_sa": c10.get("quality_status_sa"),
            "source": LIBRARY_V81_FILENAME,
            "note": "Named alaṅkāra figures and definitions are the v8.1 Library file's own literary-critical "
                    "assertion (quality_status: present); a rulebook_citation is attached only where "
                    "alankara_rulebook.json's own structural definition was checked and genuinely matches, "
                    "never by name-string coincidence alone.",
        }

    # ------------------------------------------------------------------
    # deva.json Library-file derivation (Stage 35)
    # ------------------------------------------------------------------

    def _deva_dhaturupani(self, verse_id: str) -> Optional[Dict[str, Any]]:
        """Component 6 (Dhātūrūpāṇi), sourced from the deva.json Library
        file, which carries full person x number conjugation tables for
        several verbal roots (unlike the other two directory files, which
        have almost no Component 6 content). Returns None if unavailable,
        so the caller can fall back to the existing lexical evidence."""
        lv = self._library_deva_verse(verse_id)
        if not lv:
            return None
        c6 = lv.get("COMPONENT_6_dhaturupani", {}).get("dhaturupani", {})
        note = c6.get("note")
        roots_field = c6.get("roots") if isinstance(c6.get("roots"), list) else ([c6] if c6.get("root") else [])
        tables = []
        for r in roots_field:
            if not r.get("conjugation") or _is_pending(r.get("status")):
                continue
            tables.append({
                "root": r.get("root"), "gana": r.get("gana"), "lakara": r.get("lakara"),
                "form": r.get("form"), "conjugation": r.get("conjugation"),
            })
        if not tables and not note:
            return None
        return {
            "status": STATUS_SOURCE_ASSERTION,
            "verse": verse_id,
            "conjugation_tables": tables,
            "note": note,
            "source": LIBRARY_DEVA_FILENAME,
        }

    def _deva_pratyaya(self, verse_id: str) -> List[Dict[str, Any]]:
        """Component 7 (Pratyāya) items from deva.json, filtered to exclude
        anything the Library itself tags as a heuristic ending-match rather
        than a resolved/verified derivation."""
        lv = self._library_deva_verse(verse_id)
        if not lv:
            return []
        items = lv.get("COMPONENT_7_pratyaya", {}).get("pratyaya", [])
        out = []
        for it in items:
            if not isinstance(it, dict):
                continue
            confidence = it.get("confidence") or ""
            if _is_pending(confidence) or "heuristic" in confidence.lower():
                continue
            record = {
                "surface": it.get("word"),
                "domain": "pratyaya",
                "status": STATUS_SOURCE_ASSERTION,
                "analysis": f"{it.get('breakdown', '')} ({it.get('pratyaya_name', '')})".strip(),
                "confidence": confidence,
                "source": LIBRARY_DEVA_FILENAME,
                "verse_id": verse_id,
            }
            # Stage 45: independent dictionary attestation of this already-
            # resolved item's own stem, reusing Stage 42/43's
            # _dictionary_attest_breakdown unchanged -- deva.json's
            # pratyaya `breakdown` field already uses the identical
            # "stem + suffix" plus-delimited convention Samasa's breakdown
            # field uses (e.g. "गुण + वत्"), so no new parsing is needed.
            # The bound suffix itself (वत्/मत्/तुमुन् etc.) is expected to
            # often come back unattested -- these are grammatical
            # morphemes, not headwords most dictionaries index the same
            # way content stems are -- and that is reported honestly as a
            # gap, not treated as a defect or suppressed. Citation-only:
            # never changes this item's own status, set above from the
            # Library file's own confidence field.
            if (self.library_skd_available or self.library_apte_available) and it.get("breakdown"):
                record["dictionary_attestation"] = self._dictionary_attest_breakdown(it.get("breakdown"))
            out.append(record)
        return out

    def _library_dhaturupani_extra(self, verse_id: str, existing: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add any Library-file verbal-root evidence not already covered by
        the embedded tinganta evidence (e.g. partial root lists supplied
        for a verse even when full paradigm/gana metadata is pending)."""
        lv = self._library_verse(verse_id)
        if not lv:
            return existing
        c6 = lv.get("components", {}).get("COMPONENT_6_dhaturupani", {})
        have_surfaces = {e.get("surface") for e in existing}
        extra = []
        roots_field = c6.get("roots") if isinstance(c6.get("roots"), list) else ([c6] if c6.get("root") else [])
        for r in roots_field:
            form = r.get("form")
            if not form or form in have_surfaces or _is_pending(r.get("status")):
                continue
            extra.append({
                "surface": form,
                "domain": "tinganta_or_nonfinite",
                "status": STATUS_SOURCE_ASSERTION,
                "analysis": f"root {r.get('root', '?')}"
                            + (f", {r.get('lakara')}" if r.get("lakara") else "")
                            + (f", {r.get('type')}" if r.get("type") else "")
                            + (f", person {r.get('person')}" if r.get("person") else "")
                            + (f", {r.get('number')}" if r.get("number") else ""),
                "source": LIBRARY_TEMPLATE_FILENAME,
                "verse_id": verse_id,
            })
        return existing + extra

    # ------------------------------------------------------------------
    # Treatise generation
    # ------------------------------------------------------------------

    def generate_treatise_record(self, verse_id: str) -> Dict[str, Any]:
        if verse_id not in self.benchmark:
            raise KeyError(f"Unknown benchmark verse: {verse_id}")
        v = self.benchmark[verse_id]
        words = v["padaccheda"]
        c1 = self._component1(v)
        library_cross_validation = self._cross_validate_component1(verse_id, words)
        library_v81_cross_validation = self._cross_validate_component1_v81(verse_id, words)

        known_morph = self._known_for_verse(words, ["subanta", "tinganta", "nonfinite"])
        known_morph = self._library_dhaturupani_extra(verse_id, known_morph)
        known_krt = self._known_for_verse(words, ["krtanta", "pratyaya"])

        c5 = self._v81_shabdarupani(verse_id)

        # Stage 38: fill any Component-5 stem the v8.1 file leaves open
        # (in practice, only 1.1.1's वाग्विद्) from the comprehensive
        # 1.1.1-only Library file, without overriding anything v8.1 already
        # supplies.
        extra_c5_stems = self._comprehensive_extra_c5_stems(verse_id, c5.get("stems", {}) if c5.get("status") == STATUS_SOURCE_ASSERTION else {})
        if extra_c5_stems and c5.get("status") == STATUS_SOURCE_ASSERTION:
            c5 = dict(c5)
            c5["stems"] = {**c5["stems"], **extra_c5_stems}
            c5["stem_count"] = len(c5["stems"])
            existing_sources = c5.get("source")
            c5["sources"] = [s for s in ([existing_sources] if existing_sources else []) + [LIBRARY_COMPREHENSIVE_FILENAME] if s]
            c5.pop("source", None)

        # Component 3: primary evidence is the v8.1 Library file's own
        # per-word pada_vigraha entry (Stage 41); words it doesn't cover
        # fall back to the Stage-36 deterministic exact-cell lookup against
        # Component 5's declension tables. Falls back further to the
        # legacy lexical evidence list if neither source has anything for
        # this verse at all.
        c5_stems = c5.get("stems", {}) if c5.get("status") == STATUS_SOURCE_ASSERTION else {}
        v81_pv = self._v81_padavigraha(verse_id)
        if c5_stems or v81_pv:
            c3 = self._c3_padavigraha(verse_id, words, c5_stems, v81_pv)
            if known_morph or known_krt:
                c3.setdefault("lexical_evidence", known_morph + known_krt)
        else:
            c3 = self._component_stub(
                "COMPONENT_3_padavigraha", verse_id,
                STATUS_MATCH if known_morph or known_krt else STATUS_GAP,
                "Component 3 must reconcile to Component 1; only explicit evidence is promoted.",
                known_morph + known_krt,
            )

        karaka = self._library_karaka(verse_id)
        samasa = self._library_samasa(verse_id)
        c2 = self._library_anvaya(verse_id)
        c8 = self._library_sandhi_component(verse_id)
        c10 = self._library_chandas(verse_id)

        # Stage 39: layer computed full syllabic guru/laghu scansion on
        # top of the (unchanged) Library-asserted meter name. Never
        # overwrites the existing SOURCE_ASSERTION meter-name status; adds
        # a separate computed field and upgrades scansion_status only when
        # the scansion was actually computed (never fabricated).
        scansion = self._syllabic_scansion(verse_id)
        if scansion:
            c10["syllabic_scansion_computed"] = scansion
            if scansion.get("status") == STATUS_COMPUTED:
                c10["scansion_status"] = STATUS_COMPUTED

        # Stage 36: attach verified rulebook citations to Component 8
        # (Sandhi) evidence items that already carry MATCH status.
        for item in c8.get("evidence", []):
            cite = self._rulebook_citation(RULEBOOK_CITATION_MAP, item.get("surface"))
            if cite:
                item["rulebook_citation"] = cite

        # Stage 36: attach verified rulebook citations to Component 9
        # (Samāsa) resolved items, plus non-binding candidate annotations
        # on still-pending items (status is never changed by these).
        for row in samasa.get("resolved_items", []):
            surface = row[0] if isinstance(row, list) else row.get("surface")
            cite = self._rulebook_citation(SAMASA_RULEBOOK_CITATION_MAP, surface)
            if cite and isinstance(row, list):
                row.append({"rulebook_citation": cite})
        candidate_annotations = []
        for row in samasa.get("pending_items", []):
            surface = row[0] if isinstance(row, list) else row.get("surface")
            entry = SAMASA_CANDIDATE_MAP.get(surface)
            if not entry:
                continue
            rb_key, section, rule_id, note = entry
            rb = self.rulebooks.get(rb_key)
            rule = _find_rule_in_rulebook(rb, rule_id, section) if rb else None
            if rule:
                candidate_annotations.append({
                    "surface": surface,
                    "candidate_citation": _citation_from_rule(rb["filename"], rule, note),
                    "status_unchanged": "pending",
                })
        if candidate_annotations:
            samasa["candidate_annotations_non_binding"] = candidate_annotations

        # Stage 44: attach engine-inferred (non-Library) classifications to
        # items with zero resolving Library evidence anywhere, clearly
        # separated from the rulebook-verified candidate_annotations above.
        # Applies to still-pending template items and hedged v8.1/deva
        # ambiguous items alike (the same word can surface as either,
        # depending on which Library file supplied it). Never changes the
        # item's own resolved/pending/ambiguous status.
        engine_inferred = []
        for row in samasa.get("pending_items", []):
            surface = row[0] if isinstance(row, list) else row.get("surface")
            entry = ENGINE_INFERRED_SAMASA_MAP.get((verse_id, surface))
            if entry:
                engine_inferred.append({"surface": surface, "status_unchanged": "pending", **entry})
        for row in samasa.get("ambiguous_items", []):
            surface = row.get("surface") if isinstance(row, dict) else None
            entry = ENGINE_INFERRED_SAMASA_MAP.get((verse_id, surface))
            if entry:
                engine_inferred.append({"surface": surface, "status_unchanged": "ambiguous", **entry})
        if engine_inferred:
            samasa["engine_inferred_annotations_NOT_LIBRARY_EVIDENCE"] = engine_inferred

        # Component 6: prefer the deva.json full conjugation tables; keep
        # the existing one-line lexical tiṅanta evidence alongside them
        # (different granularity, both genuine) rather than discarding it.
        lexical_c6 = self._known_for_verse(words, ["tinganta"])
        deva_c6 = self._deva_dhaturupani(verse_id)
        if deva_c6:
            c6 = {
                "status": STATUS_SOURCE_ASSERTION,
                "verse": verse_id,
                "conjugation_tables": deva_c6["conjugation_tables"],
                "note": deva_c6["note"],
                "lexical_evidence": lexical_c6,
                "sources": [s for s in (LIBRARY_DEVA_FILENAME, "Library-backed project evidence" if lexical_c6 else None) if s],
            }
        else:
            c6 = self._component_stub("COMPONENT_6_dhaturupani", verse_id,
                                      STATUS_MATCH if lexical_c6 else STATUS_GAP,
                                      "Only explicitly Library-supported verbal paradigms/analyses are promoted.",
                                      lexical_c6)

        # Component 7: merge existing Kṛt/pratyaya lexical evidence with
        # deva.json's confidence-filtered (non-heuristic) suffix entries,
        # de-duplicated by surface. Stage 36 also attaches verified
        # rulebook citations by surface.
        deva_c7 = self._deva_pratyaya(verse_id)
        have_surfaces = {e.get("surface") for e in known_krt}
        merged_c7 = known_krt + [e for e in deva_c7 if e.get("surface") not in have_surfaces]
        for item in merged_c7:
            cite = self._rulebook_citation(RULEBOOK_CITATION_MAP, item.get("surface"))
            if cite:
                item["rulebook_citation"] = cite
        c7 = self._component_stub("COMPONENT_7_pratyaya", verse_id,
                                  STATUS_MATCH if merged_c7 else STATUS_GAP,
                                  "Explicit Kṛt/pratyaya evidence only; heuristic ending-match entries are excluded; "
                                  "case affixes are not conflated with Kṛt derivation.",
                                  merged_c7)
        c11 = {"status": STATUS_NOT_ASSERTED,
               "generation": "runtime_only",
               "note": "Quiz generation is permitted only from validated components; invented answers are never supplied."}

        record = {
            "engine_version": self.version,
            "benchmark_id": BENCHMARK_ID,
            "verse_id": verse_id,
            "source_ref": v["source_ref"],
            "source_text_iast": v["iast"],
            "source_text_immutable": True,
            "source_policy": {
                "library_only": True,
                "external_web_content_used_for_grammar": False,
                "fuzzy_matching": False,
                "generalized_generation": False,
            },
            "library_cross_validation": library_cross_validation,
            "library_v81_cross_validation": library_v81_cross_validation,
            "components": {
                "COMPONENT_1_padaccheda": c1,
                "COMPONENT_2_anvaya": c2,
                "COMPONENT_3_padavigraha": c3,
                "COMPONENT_4_karaka": karaka,
                "COMPONENT_5_shabdarupani": c5,
                "COMPONENT_6_dhaturupani": c6,
                "COMPONENT_7_pratyaya": c7,
                "COMPONENT_8_sandhi": c8,
                "COMPONENT_9_samasa": samasa,
                "COMPONENT_10_chandas": c10,
                "COMPONENT_11_quiz": c11,
            },
        }
        record["validation"] = self.validate_treatise_record(record)
        return record

    def generate_benchmark_treatise(self) -> Dict[str, Any]:
        records = [self.generate_treatise_record(k) for k in self.benchmark]
        audit = self.audit_benchmark(records)
        return {
            "artifact_type": "engine_generated_sanskrit_grammatical_treatise_benchmark",
            "engine_version": self.version,
            "benchmark": self.benchmark_manifest(),
            "records": records,
            "audit": audit,
        }

    def validate_treatise_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []
        c = record.get("components", {})
        c1 = c.get("COMPONENT_1_padaccheda", {})
        c3 = c.get("COMPONENT_3_padavigraha", {})
        words = c1.get("padaccheda", [])
        if c1.get("authoritative") is not True:
            errors.append("Component 1 is not marked authoritative.")
        if c3.get("word_count") is not None and c3.get("word_count") != len(words):
            errors.append("Component 1/3 word-count mismatch.")
        policy = record.get("source_policy", {})
        if policy.get("library_only") is not True:
            errors.append("library_only must be true.")
        if policy.get("external_web_content_used_for_grammar") is True:
            errors.append("External web grammar evidence is prohibited.")
        if policy.get("fuzzy_matching") is True:
            errors.append("Fuzzy matching is prohibited.")
        # Component 1 is authoritative from the embedded sa_rAmAyaNa.txt-sourced
        # benchmark (per README/PROJECT_STATE.md), not from the secondary
        # template artifact. A mismatch there means the *template file* is
        # incomplete/stale relative to the established Component-1 inventory
        # (a Library-artifact defect worth flagging), not that this engine's
        # authoritative Component 1 is wrong. It is therefore a warning, not
        # a structural-validation failure.
        xval = record.get("library_cross_validation", {})
        if xval.get("status") == "MISMATCH":
            warnings.append(
                "Directory Library template file's own Component 1 word list differs from the "
                "authoritative (sa_rAmAyaNa.txt-sourced) Component 1 for this verse — likely a "
                "stale/incomplete padaccheda in the template artifact itself, not an engine defect. "
                f"Template: {xval.get('library_word_count')} words vs authoritative {xval.get('embedded_word_count')} words."
            )
        return {"status": "PASS" if not errors else "FAIL", "errors": errors, "warnings": warnings,
                "word_count": len(words), "component_count": len(c)}

    def audit_benchmark(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        rows = []
        supported = ambiguous = gaps = not_asserted = 0
        samasa_constituents_checked = samasa_constituents_attested = 0
        sandhi_constituents_checked = sandhi_constituents_attested = 0
        pratyaya_constituents_checked = pratyaya_constituents_attested = 0
        for r in records:
            for name in TEMPLATE_COMPONENTS:
                status = r["components"][name].get("status", STATUS_NOT_ASSERTED)
                if status in (STATUS_MATCH, STATUS_SOURCE_ASSERTION, STATUS_COMPUTED):
                    supported += 1
                elif status == STATUS_AMBIGUOUS:
                    ambiguous += 1
                elif status == STATUS_GAP:
                    gaps += 1
                else:
                    not_asserted += 1
            # Stage 42/43: measure dictionary-attestation coverage (SKD and,
            # since Stage 43, Apte) separately from the component-slot metric
            # above -- this is a finer-grained, sub-component measurement
            # (individual compound members / sandhi constituents, not whole
            # components), so it is reported alongside, not folded into, the
            # existing coverage percentage. Component 9 (Samāsa) has carried
            # this since Stage 42; Component 8 (Sandhi) gets it new in Stage 43.
            samasa = r["components"].get("COMPONENT_9_samasa", {})
            for item in samasa.get("resolved_items", []) + samasa.get("ambiguous_items", []):
                if isinstance(item, dict):
                    for att in item.get("dictionary_attestation", []):
                        samasa_constituents_checked += 1
                        if att.get("attested"):
                            samasa_constituents_attested += 1
            sandhi = r["components"].get("COMPONENT_8_sandhi", {})
            for item in sandhi.get("evidence", []):
                if isinstance(item, dict):
                    for att in item.get("dictionary_attestation", []):
                        sandhi_constituents_checked += 1
                        if att.get("attested"):
                            sandhi_constituents_attested += 1
            # Stage 45: same measurement, extended to Component 7 (Pratyaya).
            pratyaya = r["components"].get("COMPONENT_7_pratyaya", {})
            for item in pratyaya.get("evidence", []):
                if isinstance(item, dict):
                    for att in item.get("dictionary_attestation", []):
                        pratyaya_constituents_checked += 1
                        if att.get("attested"):
                            pratyaya_constituents_attested += 1
            rows.append({
                "verse_id": r["verse_id"],
                "validation": r["validation"],
                "library_cross_validation_status": r.get("library_cross_validation", {}).get("status"),
            })
        total = len(records) * len(TEMPLATE_COMPONENTS)
        coverage = round((supported / total) * 100, 2) if total else 0.0
        return {
            "benchmark_id": BENCHMARK_ID,
            "total_component_slots": total,
            "supported_or_source_asserted": supported,
            "ambiguous": ambiguous,
            "gaps": gaps,
            "not_asserted": not_asserted,
            "current_supported_coverage_percent": coverage,
            "target_percent": 99.0,
            "target_reached": coverage >= 99.0 and ambiguous == 0 and gaps == 0,
            "interpretation": "This is an evidence-coverage metric, not a claim of scholarly correctness.",
            "library_template_found_on_disk": self.library_available,
            "library_skd_found_on_disk": self.library_skd_available,
            "library_apte_found_on_disk": self.library_apte_available,
            "dictionary_attestation_summary": {
                "libraries_available": {"skd": self.library_skd_available, "apte": self.library_apte_available},
                "samasa": {
                    "constituents_checked": samasa_constituents_checked,
                    "constituents_attested": samasa_constituents_attested,
                    "attestation_rate_percent": round((samasa_constituents_attested / samasa_constituents_checked) * 100, 2) if samasa_constituents_checked else None,
                    "interpretation": "Independent dictionary attestation (SKD, and since Stage 43 also Apte) of "
                                      "Component-9 compound-member breakdowns; a constituent not attested in "
                                      "either dictionary is a reported gap (or a known, documented un-normalized "
                                      "spelling convention -- see PROJECT_STATE.md), never silently dropped, and "
                                      "never changes the compound's own status.",
                },
                "sandhi": {
                    "constituents_checked": sandhi_constituents_checked,
                    "constituents_attested": sandhi_constituents_attested,
                    "attestation_rate_percent": round((sandhi_constituents_attested / sandhi_constituents_checked) * 100, 2) if sandhi_constituents_checked else None,
                    "interpretation": "New in Stage 43: independent dictionary attestation (SKD and Apte) of "
                                      "Component-8 Sandhi evidence items' own pre-sandhi constituent words, "
                                      "parsed deterministically from each item's existing analysis string; "
                                      "citation-only, never changes the item's own status.",
                },
                "pratyaya": {
                    "constituents_checked": pratyaya_constituents_checked,
                    "constituents_attested": pratyaya_constituents_attested,
                    "attestation_rate_percent": round((pratyaya_constituents_attested / pratyaya_constituents_checked) * 100, 2) if pratyaya_constituents_checked else None,
                    "interpretation": "New in Stage 45: independent dictionary attestation (SKD and Apte) of "
                                      "Component-7 Pratyaya evidence items' own stem (reusing the identical "
                                      "plus-delimited breakdown convention and attestation method already used "
                                      "for Component 9/Samasa); citation-only, never changes the item's own "
                                      "status. The bound suffix itself is often not separately indexed by these "
                                      "dictionaries, so a lower attestation rate here than Samasa/Sandhi is "
                                      "expected, not a defect.",
                },
            },
            "record_validation": rows,
        }

    def gap_report(self) -> Dict[str, Any]:
        return {
            "engine_version": self.version,
            "benchmark": self.benchmark_manifest(),
            "library_template_file": LIBRARY_TEMPLATE_FILENAME,
            "library_template_found_on_disk": self.library_available,
            "library_v81_file": LIBRARY_V81_FILENAME,
            "library_v81_found_on_disk": self.library_v81_available,
            "library_deva_file": LIBRARY_DEVA_FILENAME,
            "library_deva_found_on_disk": self.library_deva_available,
            "library_skd_file": LIBRARY_SKD_FILENAME,
            "library_skd_found_on_disk": self.library_skd_available,
            "library_skd_entry_count": self.library_skd["raw_count"] if self.library_skd_available else None,
            "library_apte_file": LIBRARY_APTE_FILENAME,
            "library_apte_found_on_disk": self.library_apte_available,
            "library_apte_entry_count": self.library_apte["raw_count"] if self.library_apte_available else None,
            "rulebooks_found_on_disk": {k: (v is not None) for k, v in self.rulebooks.items()},
            "domains": {
                "subanta": {"indexed_surfaces": len(self.registries["subanta"]), "status": "PARTIAL_LIBRARY_EVIDENCE"},
                "tinganta": {"indexed_surfaces": len(self.registries["tinganta"]), "status": "PARTIAL_LIBRARY_EVIDENCE"},
                "nonfinite": {"indexed_surfaces": len(self.registries["nonfinite"]), "status": "PARTIAL_LIBRARY_EVIDENCE"},
                "krtanta": {"indexed_surfaces": len(self.registries["krtanta"]), "status": "PARTIAL_LIBRARY_EVIDENCE"},
                "pratyaya": {"indexed_surfaces": len(self.registries["pratyaya"]), "status": "PARTIAL_LIBRARY_EVIDENCE",
                             "dictionary_attestation": "ADDED_STAGE_45" if (self.library_skd_available or self.library_apte_available) else "NO_DICTIONARY_FILE_FOUND"},
                "sandhi": {"indexed_records": len(self.registries["sandhi"]), "indexed_rules": len(self.sandhi_rules), "status": "EXPLICIT_EVIDENCE_ONLY",
                           "dictionary_attestation": "ADDED_STAGE_43" if (self.library_skd_available or self.library_apte_available) else "NO_DICTIONARY_FILE_FOUND"},
                "taddhita": {"status": "NOT_GENERALIZED"},
                "samasa": {"status": "PARTIAL_LIBRARY_EVIDENCE",
                           "dictionary_constituent_attestation": ("ADDED_STAGE_42_EXTENDED_STAGE_43" if (self.library_skd_available and self.library_apte_available)
                                                                   else "ADDED_STAGE_42" if self.library_skd_available
                                                                   else "APTE_ONLY_STAGE_43" if self.library_apte_available
                                                                   else "NO_DICTIONARY_FILE_FOUND")},
                "karaka": {"status": "PARTIAL_LIBRARY_EVIDENCE"},
                "chandas": {"status": "SOURCE_ASSERTION_ONLY_UNLESS_VALIDATED (meter name only; scansion/alaṅkāra separately flagged)"},
                "alankara": {"status": "PARTIAL_LIBRARY_EVIDENCE (named figures + definitions from v8.1 for all 5 verses; rulebook citation attached only where genuinely verified)"},
                "rule_trace": {"status": "REFERENCE_REGISTRY_ONLY_UNLESS_OPERATIONAL_EVIDENCE_EXISTS"},
            },
            "policy": {
                "no_silent_inference": True,
                "no_fuzzy_matching": True,
                "ambiguous_cases_preserved": True,
                "missing_library_data_flagged": True,
                "fixed_benchmark_until_stage30_review": True,
            },
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine": "sanskrit_grammar_engine",
            "version": self.version,
            "benchmark": self.benchmark_manifest(),
            "policy": {
                "library_only": self.library_only,
                "external_web_content_used_for_grammar": self.external_web_content_used_for_grammar,
                "fuzzy_matching": self.fuzzy_matching,
                "generalized_generation": self.generalized_generation,
            },
            "registries": self.registries,
            "sandhi_reverse": self.sandhi_reverse,
            "sandhi_rules": self.sandhi_rules,
            "gap_report": self.gap_report(),
            "audit_log": self.audit_log,
        }

    def save_registry(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def load_engine(path: Optional[str] = None) -> SanskritGrammarEngine:
    # v0.5 loads the directory-resident Library template file (next to this
    # module by default, or from `path` if given) in addition to the
    # embedded canonical benchmark and fallback known-evidence list.
    return SanskritGrammarEngine(library_only=True, library_dir=path)


def main() -> None:
    parser = argparse.ArgumentParser(description=f"Canonical Library-only Sanskrit Grammar Engine v{ENGINE_VERSION}")
    parser.add_argument("--gap-report", action="store_true")
    parser.add_argument("--benchmark", action="store_true", help="Generate the five-śloka Stage-30 benchmark treatise JSON to stdout.")
    parser.add_argument("--benchmark-out", help="Write the five-śloka Stage-30 benchmark treatise JSON to a file.")
    parser.add_argument("--verse", help="Generate one benchmark verse, e.g. 1.1.1.")
    parser.add_argument("--library-dir", help="Directory to look for the Library template file in (defaults to the engine's own directory).")
    args = parser.parse_args()
    engine = load_engine(args.library_dir)
    if args.gap_report:
        print(json.dumps(engine.gap_report(), ensure_ascii=False, indent=2))
        return
    if args.verse:
        print(json.dumps(engine.generate_treatise_record(args.verse), ensure_ascii=False, indent=2))
        return
    if args.benchmark or args.benchmark_out:
        result = engine.generate_benchmark_treatise()
        text = json.dumps(result, ensure_ascii=False, indent=2)
        if args.benchmark_out:
            Path(args.benchmark_out).write_text(text, encoding="utf-8")
        else:
            print(text)
        return
    print(json.dumps({
        "engine": "sanskrit_grammar_engine",
        "version": engine.version,
        "status": "READY",
        "benchmark": engine.benchmark_manifest(),
        "gap_report": engine.gap_report(),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
