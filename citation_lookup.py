#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
citation_lookup.py
====================
Hand-verified Devanagari labels + Ashtadhyayi/Laghusiddhantakaumudi rule
citations for the grammar-concept strings produced by this project's own
tools (`sandhi/sandhi_splitter.py`'s `sandhi` package output via
`samasa_splitter.py`'s `restore_word_boundary`, `samasa_splitter.py`'s
`guess_samasa_type`, and the six kāraka roles).

WHY HAND-VERIFIED, NOT AUTOMATED FUZZY MATCHING
-------------------------------------------------
This project's own established policy (see PROJECT_STATE.md principle 12
and `sanskrit_grammar_engine.py`'s `RULEBOOK_CITATION_MAP`) is that a
rulebook citation must be attached only after checking the rulebook's
OWN actual rule content matches what's being cited -- never a
name-string-only guess. Every mapping below was built by directly
grepping `sandhi_rulebook.json` / `samasah_rulebook.json` /
`vibhakti_prakarana_rulebook.json` for the specific rule types this
project's tools actually produce for Bālakāṇḍa Sarga 1 ślokas 1-10, then
hand-matching by rule CONTENT (not just name) to each entry's own
`ashtadhyayi_ref`. If this pipeline is later extended to more verses and
encounters a sandhi/samasa type not in these tables, the correct
response is to look it up the same way (see `lookup_sandhi_citation`'s
fallback) -- never to fabricate a plausible-looking rule number.

DEVANAGARI-ONLY LABELS
-----------------------
Per explicit user instruction, every grammar-concept label shown in a
report must be Devanagari, never the IAST/WX strings this project's
tools return internally (e.g. "rutva-> utva-> guṇa-sandhiḥ" must render
as "रुत्वम् → उत्वम् → गुणसन्धिः"). Each table below pairs the tool's own
internal string with its Devanagari rendering, taken directly from the
matching rulebook entry's own `sanskrit_name` field wherever one exists
(never independently retranslated) -- this guarantees the Devanagari
label matches the exact term the rulebook itself uses for that rule.
"""

import re
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate as tl


def _best_effort_devanagari(iast_or_wx_text):
    """
    Last-resort transliteration for a grammar-concept string this module
    has NOT hand-verified a citation for -- used only so an UNKNOWN
    label is still rendered in Devanagari rather than left as raw IAST,
    per the Devanagari-only requirement. The caller must still treat
    this as is_known=False (amber-flag the cell) since the underlying
    rule citation itself is unverified -- this only fixes the SCRIPT,
    not the missing citation. Handles the "a -> b -> c" chain notation
    these tools sometimes use by transliterating each segment
    separately and rejoining with "→".
    """
    segments = [s.strip() for s in re.split(r"->|→", str(iast_or_wx_text))]
    out = []
    for seg in segments:
        try:
            out.append(tl(seg, sanscript.IAST, sanscript.DEVANAGARI))
        except Exception:
            out.append(seg)
    return " → ".join(out)


# --------------------------------------------------------------------------- #
# SANDHI: sandhi_type string (from the `sandhi` package's niyama.py table,
# as returned by samasa_splitter.py's restore_word_boundary) -> Devanagari
# label(s) + citation(s). Verified against sandhi_rulebook.json's own
# entries by content (not name-string alone) -- see this module's
# docstring. A compound sandhi_type string like "rutva-> utva->
# guṇa-sandhiḥ" reflects MULTIPLE successive rule applications, so its
# value here is a list of (id, devanagari_name, ashtadhyayi_ref) tuples,
# in the order the rules actually apply.
# --------------------------------------------------------------------------- #
SANDHI_TYPE_CITATIONS = {
    # ko + nu -> kaḥ+nu: visarga -> रु (8.2.66-family) -> उ (6.1.113/114) -> गुण (6.1.87)
    "rutva-> utva-> guṇa-sandhiḥ": [
        ("visarga-4", "विसर्गस्य उकारादेशः", "6.1.113 सह 6.1.114"),
        ("svara-2", "गुण सन्धिः", "6.1.87"),
    ],
    # yaḥ+asti-type chain ending in पूर्वरूप retention (e.g. nu+asmin -> nvasmin
    # is yaṇ, but a distinct qualifying chain toward a+a-derived पूर्वरूप
    # was also observed in this project's own output)
    "rutva -> utva-> guṇa-> pūrvarupa": [
        ("visarga-4", "विसर्गस्य उकारादेशः", "6.1.113 सह 6.1.114"),
        ("svara-2", "गुण सन्धिः", "6.1.87"),
        ("svara-6", "पूर्वरूप सन्धिः", "6.1.109"),
    ],
    # nu + asmin -> nvasmin: u -> v before a vowel (semivowel substitution)
    "yaṇ": [
        ("svara-4", "यण् सन्धिः", "6.1.77"),
    ],
    # vālmīkiḥ + munipuṅgavam -> vālmīkir munipuṅgavam: visarga -> र् before
    # a voiced sound, when preceded by a vowel other than a/ā
    "repha-sandhiḥ": [
        ("visarga-5", "विसर्गस्य रेफादेशः", "8.2.66 (ससजुषो रुः) → 6.1.113/114"),
    ],
    # dharmajñaḥ + ca -> dharmajñaś ca: visarga -> स् (8.3.34) then स् -> श्
    # before a च-varga sound (श्चुत्व, 8.4.40)
    "satva-> ścutva-sandhiḥ": [
        ("visarga-3", "विसर्गस्य श्/ष्/स् त्वम् (च-ट-त वर्गे)", "8.3.34"),
        ("vyan-1", "श्चुत्व सन्धिः", "8.4.40"),
    ],
    # ग reversed to क् (jashtva undone) -- vyan-3 in sandhi_splitter.py's own
    # rule table, seen for dharmajñaḥ-type words at the vyañjana layer
    "jashtva": [
        ("vyan-3", "जश्त्व सन्धिः", "8.2.39"),
    ],
    # ---- added in the Sarga-1 gold-standard pass: the oracle already emitted "satva-sandhiḥ"
    # (samas tyāge) but it had no entry here, so it fell through to a transliterated label; the
    # rest are produced by combined_splitter.deterministic_junction / split_fused_token.
    "satva-sandhiḥ": [("visarga-3", "विसर्गस्य सकारः (विसर्जनीयस्य सः)", "8.3.34")],
    "satva-> ṣṭutva-sandhiḥ": [("visarga-3", "विसर्जनीयस्य सः", "8.3.34"), ("vyan-2", "ष्टुत्व सन्धिः", "8.4.41")],
    "anusvāra-sandhiḥ": [("vyan-6", "अनुस्वार सन्धिः (मोऽनुस्वारः)", "8.3.23")],
    "sulopa-sandhiḥ": [("sandhi_rulebook.json-बहिः", "सुलोपः (एतत्तदोः सुलोपोऽकोरनञ्समासे हलि)", "6.1.132")],
    "jaśtva-sandhiḥ": [("vyan-3", "जश्त्व सन्धिः (झलां जशोऽन्ते)", "8.2.39")],
    "jaśtva-> pūrvasavarṇa-sandhiḥ": [("vyan-3", "जश्त्व सन्धिः", "8.2.39"),
                                      ("vyan-14 (सन्दर्भः)", "पूर्वसवर्ण सन्धिः (झयो होऽन्यतरस्याम्)", "8.4.62")],
    "jaśtva-> ścutva-sandhiḥ": [("vyan-3", "जश्त्व सन्धिः", "8.2.39"), ("vyan-1", "श्चुत्व सन्धिः", "8.4.40")],
    "ścutva-sandhiḥ": [("vyan-1", "श्चुत्व सन्धिः (स्तोः श्चुना श्चुः)", "8.4.40")],
    "anunāsika-sandhiḥ": [("vyan-5", "अनुनासिक सन्धिः (यरोऽनुनासिकेऽनुनासिको वा)", "8.4.45")],
    "pūrvarūpa-sandhiḥ": [("svara-6", "पूर्वरूप सन्धिः (एङः पदान्तादति)", "6.1.109")],
    "ayādi-sandhiḥ": [("svara-5", "अयादि सन्धिः (एचोऽयवायावः)", "6.1.78")],
    "visarga-lopa (aḥ)": [("visarga-4b", "विसर्गलोपः (भोभगोअघोअपूर्वस्य योऽशि; लोपः शाकल्यस्य)", "8.3.17 → 8.3.19")],
    "visarga-lopa (āḥ)": [("visarga-4b", "विसर्गलोपः (भोभगोअघोअपूर्वस्य योऽशि; लोपः शाकल्यस्य)", "8.3.17 → 8.3.19")],
    "visarga-lopa (khar-para śar)": [("visarga-2", "विसर्गलोपः (खर्परे शरि वा विसर्गलोपो वक्तव्यः)", "8.3.36 वार्त्तिकम्")],
    "ṅamuṭ-sandhiḥ": [("vyan-13", "ङमुडागमः (ङमो ह्रस्वादचि ङमुण्नित्यम्)", "8.3.32")],
    "rutva-> satva (naś chavy apraśān)": [("sandhi_rulebook.json-बहिः", "नश्छव्यप्रशान् (रुत्वम्)", "8.3.7"),
                                          ("visarga-3", "विसर्जनीयस्य सः", "8.3.34")],
    "dīrgha-sandhiḥ": [("svara-1", "सवर्णदीर्घ सन्धिः (अकः सवर्णे दीर्घः)", "6.1.101")],
    "guṇa-sandhiḥ": [("svara-2", "गुण सन्धिः (आद्गुणः)", "6.1.87")],
    "vṛddhi-sandhiḥ": [("svara-3", "वृद्धि सन्धिः (वृद्धिरेचि)", "6.1.88")],
}

# Sandhi_type values that mean "checked, no real rule fired" -- must be
# rendered as "-" (no sandhi), never Devanagari-transliterated as if they
# were a rule name.
SANDHI_TYPE_NO_OP = {
    "as-printed", "as-printed (no change needed)",
    "sandhi-augment (linking nasal)", "sandhi-augment",
}


def lookup_sandhi_citation(sandhi_type):
    """
    Returns (devanagari_label, citation_str, is_known) for a sandhi_type
    string as produced by samasa_splitter.py's restore_word_boundary.
    is_known=False means this sandhi_type has NOT been hand-verified
    against sandhi_rulebook.json yet -- the caller should flag the cell
    amber and show the raw IAST string rather than fabricate a citation.
    """
    if sandhi_type in SANDHI_TYPE_NO_OP:
        return "-", "", True
    entries = SANDHI_TYPE_CITATIONS.get(sandhi_type)
    if entries is None:
        return _best_effort_devanagari(sandhi_type), "", False
    label = " → ".join(name for (_id, name, _ref) in entries)
    citation = "; ".join(f"अष्टाध्यायी {ref} ({sid})" for (sid, _name, ref) in entries)
    return label, citation, True


# --------------------------------------------------------------------------- #
# SAMASA: guess_samasa_type() output string (samasa_splitter.py) ->
# Devanagari label + citation. Verified against samasah_rulebook.json's
# tatpurusha/bahuvrihi/dvandva/avyayibhava arrays (dvigu and गति/प्रादि
# nested under tatpurusha in that file) by content.
# --------------------------------------------------------------------------- #
DEVANAGARI_SAMASA_CITATIONS = [
    ("नञ्तत्पुरुषः", "अष्टाध्यायी 2.2.6 (नञ्)"),
    ("नञ्बहुव्रीहिः", "अष्टाध्यायी 2.2.24 (अनेकमन्यपदार्थे) सह वार्त्तिकम् (नञोऽस्त्यर्थानां…)"),
    ("उपपदतत्पुरुषः", "अष्टाध्यायी 2.2.19 (उपपदमतिङ्)"),
    ("कर्मधारयः", "अष्टाध्यायी 1.2.42 (तत्पुरुषः समानाधिकरणः कर्मधारयः); 2.1.57 (विशेषणं विशेष्येण बहुलम्)"),
    ("बहुव्रीहिः", "अष्टाध्यायी 2.2.24 (अनेकमन्यपदार्थे)"),
    ("द्वन्द्वः", "अष्टाध्यायी 2.2.29 (चार्थे द्वन्द्वः)"),
    ("द्विगुः", "अष्टाध्यायी 2.1.52 (सङ्ख्यापूर्वो द्विगुः)"),
    ("अव्ययीभावः", "अष्टाध्यायी 2.1.5 (अव्ययीभावः); 2.1.6"),
    ("तत्पुरुषः", "अष्टाध्यायी 2.1.22 (तत्पुरुषः); 2.2.8 (षष्ठी)"),
]


def lookup_samasa_citation(type_guess):
    """
    Returns (devanagari_label, citation_str, is_known) for a
    guess_samasa_type() output string. The generic, explicitly
    "uncertain" reading (samasa_splitter.py itself hedges between
    tatpuruṣa/karmadhāraya/bahuvrīhi) is rendered honestly as uncertain,
    WITHOUT a specific rule citation -- citing one specific sutra for a
    reading the tool itself can't disambiguate would misrepresent
    certainty that doesn't exist.
    """
    if type_guess.startswith("not a compound"):
        return "-", "", True
    # Devanagari type names produced by samasa_classifier.py (Sarga-1 pass): "<type> — <reason>"
    for dev_type, cite in DEVANAGARI_SAMASA_CITATIONS:
        if type_guess.startswith(dev_type):
            return type_guess, cite, True
    if type_guess.startswith("dvigu"):
        # FIXED (Sarga-1 pass): was "2.1.51 (दvigu-1, तद्धितार्थद्विगुः)" -- a mixed-script typo, and
        # 2.1.51 (तद्धितार्थोत्तरपदसमाहारे च) is the licensing rule, not the dvigu definition.
        return ("द्विगुः (सङ्ख्यापूर्वपदः)",
                "अष्टाध्यायी 2.1.52 (सङ्ख्यापूर्वो द्विगुः); 2.1.51 (तद्धितार्थोत्तरपदसमाहारे च)", True)
    if type_guess.startswith("tatpuruSa (upasarga-compound"):
        return ("प्रादितत्पुरुषः (उपसर्गपूर्वपदः)",
                "अष्टाध्यायी 2.2.18 (nan-4, प्रादिसमासः)", True)
    if type_guess.startswith("nañ-tatpuruSa"):
        # FIXED (Sarga-1 pass): was "2.2.61" -- the nañ-samāsa sūtra is 2.2.6 (नञ्).
        return ("नञ्तत्पुरुषः",
                "अष्टाध्यायी 2.2.6 (नञ्)", True)
    if type_guess.startswith("avyayibhava"):
        return ("अव्ययीभावः (सम्भाव्यः)",
                "अष्टाध्यायी 2.1.6 (avyayibhava-1) -- अनिश्चितम्", True)
    if type_guess.startswith("tatpuruSa / karmaXAraya / bahuvrIhi"):
        return ("तत्पुरुषः/कर्मधारयः/बहुव्रीहिः (अनिश्चितम्)", "", True)
    return _best_effort_devanagari(type_guess), "", False


# --------------------------------------------------------------------------- #
# KARAKA: the six kārakas, verified directly against
# vibhakti_prakarana_rulebook.json's own karaka_definitions array
# (vibhakti-1..6). All six sutras are Pāṇini's own foundational
# kāraka-definitions (Aṣṭādhyāyī 1.4.24-1.4.55).
# --------------------------------------------------------------------------- #
KARAKA_CITATIONS = {
    "karta": ("कर्ता", "अष्टाध्यायी 1.4.54 (स्वतन्त्रः कर्ता)"),
    "karma": ("कर्म", "अष्टाध्यायी 1.4.49 (कर्तुरीप्सिततमं कर्म)"),
    "karana": ("करणम्", "अष्टाध्यायी 1.4.42 (साधकतमं करणम्)"),
    "sampradana": ("सम्प्रदानम्", "अष्टाध्यायी 1.4.32 (कर्मणा यमभिप्रैति स सम्प्रदानम्)"),
    "apadana": ("अपादानम्", "अष्टाध्यायी 1.4.24 (ध्रुवमपायेऽपादानम्)"),
    "adhikarana": ("अधिकरणम्", "अष्टाध्यायी 1.4.45 (आधारोऽधिकरणम्)"),
    "kriya": ("क्रिया", ""),
}


def lookup_karaka_citation(role_key):
    """role_key: one of the KARAKA_CITATIONS keys, or a raw role string
    from analyze_karaka() -- e.g. "karta (nominative subject)". Matches
    on whichever known key is a PREFIX of the given string."""
    if not role_key:
        return "-", "", True
    for key, (deva, citation) in KARAKA_CITATIONS.items():
        if role_key.startswith(key):
            return deva, citation, True
    return _best_effort_devanagari(role_key), "", False


# --------------------------------------------------------------------------- #
# VIBHAKTI (सुप् case-ending) -> KARAKA: the traditional default
# correspondence, each cell citing BOTH the vibhakti_assignment_rules
# entry that names the affix (vibhakti-7..15, Ashtadhyayi 2.3.x) AND the
# karaka_definitions entry it conventionally realizes (vibhakti-1..6,
# Ashtadhyayi 1.4.24-1.4.55) -- both verified directly against
# vibhakti_prakarana_rulebook.json (see search results this session).
#
# IMPORTANT CAVEAT, deliberately preserved in the `definitive` flag:
# a vibhakti ending alone does NOT deterministically fix the kāraka --
# प्रथमा marks the कर्ता only in kartari (active-voice) construction, but
# marks कर्म in karmani (passive) construction; तृतीया's OWN governing
# sutra (2.3.18, कर्तृकरणयोस्तृतीया) explicitly covers BOTH कर्ता and
# करण. Genuinely resolving this needs the verb's voice (kartari/karmani/
# bhāve), which a per-word vibhakti table alone cannot supply -- so
# `definitive=False` for प्रथमा/तृतीया (default reading only, must be
# amber-flagged), while द्वितीया/चतुर्थी/पञ्चमी/सप्तमी each map to
# exactly one kāraka in the ordinary case (definitive=True). षष्ठी and
# the vocative are EXPLICITLY EXCLUDED from the six kārakas by Pāṇini
# himself (2.3.50 षष्ठी शेषे, "the genitive marks the REMAINDER [not a
# kāraka]") -- never mislabeled as a kāraka here.
# --------------------------------------------------------------------------- #
VIBHAKTI_TO_KARAKA = {
    "प्रथमा": {
        "assignment": ("vibhakti-7", "प्रातिपदिकार्थलिङ्गपरिमाणवचनमात्रे प्रथमा", "2.3.46"),
        "karaka": "karta", "definitive": False,
        "note": "उक्तकर्तरि प्रायः कर्ता (कर्तरि प्रयोगे); कर्मणि प्रयोगे तु कर्म भवितुम् अर्हति",
    },
    "द्वितीया": {
        "assignment": ("vibhakti-9", "कर्मणि द्वितीया", "2.3.2"),
        "karaka": "karma", "definitive": True, "note": "",
    },
    "तृतीया": {
        "assignment": ("vibhakti-10", "कर्तृकरणयोस्तृतीया", "2.3.18"),
        "karaka": "karana", "definitive": False,
        "note": "करणम् अथवा कर्तरि (कर्मणि/भावे प्रयोगे) -- सूत्रम् उभयम् अपि कथयति",
    },
    "चतुर्थी": {
        "assignment": ("vibhakti-11", "चतुर्थी सम्प्रदाने", "2.3.13"),
        "karaka": "sampradana", "definitive": True, "note": "",
    },
    "पञ्चमी": {
        "assignment": ("vibhakti-13", "अपादाने पञ्चमी", "2.3.28"),
        "karaka": "apadana", "definitive": True, "note": "",
    },
    "षष्ठी": {
        "assignment": ("vibhakti-14", "षष्ठी शेषे", "2.3.50"),
        "karaka": None, "definitive": True,
        "note": "षष्ठी न कारकसंज्ञां लभते (\"शेषे\") -- सम्बन्धमात्रम्",
    },
    "सप्तमी": {
        "assignment": ("vibhakti-15", "सप्तम्यधिकरणे च", "2.3.36"),
        "karaka": "adhikarana", "definitive": True, "note": "",
    },
    "सम्बोधन-प्रथमा": {
        "assignment": ("vibhakti-8", "सम्बोधने च", "2.3.47"),
        "karaka": None, "definitive": True,
        "note": "सम्बोधनम् न कारकसंज्ञा",
    },
}


def classify_suptin(pos, case):
    """
    Classify a Component-1/3 word as तिङन्तम् (finite verb), अव्ययम्
    (indeclinable -- neither सुप् nor तिङ्), सुबन्तम् (nominal, सुप्-
    प्रत्ययान्त), or unknown, from the Library's own `pos`/`case` fields
    (sanskrit_grammar_engine.py Component 3). Returns one of
    "तिङन्तम्", "अव्ययम्", "सुबन्तम्", or None (insufficient data).
    """
    if pos == "क्रियापदम्":
        return "तिङन्तम्"
    if case in (None, "", "—", "-"):
        if pos and "अव्यय" in pos:
            return "अव्ययम्"
        return None
    return "सुबन्तम्"


def karaka_from_vibhakti(case):
    """
    Returns (suptin_label, karaka_cell, definitive) for a Library-given
    vibhakti name (e.g. "प्रथमा"). karaka_cell already includes both
    citations (vibhakti-assignment + kāraka-definition, or the
    "not a kāraka" note for षष्ठी/vocative). Returns (None, "-", True)
    if `case` isn't a recognized vibhakti name.
    """
    entry = VIBHAKTI_TO_KARAKA.get(case)
    if entry is None:
        return None, "-", True
    aid, aname, aref = entry["assignment"]
    if entry["karaka"] is None:
        cell = f"{entry['note']} [अष्टाध्यायी {aref} ({aid}, {aname})]"
        return case, cell, entry["definitive"]
    karaka_deva, karaka_cite = KARAKA_CITATIONS[entry["karaka"]]
    cell = f"{karaka_deva} ({case})"
    if entry["note"]:
        cell += f" -- {entry['note']}"
    cell += f" [अष्टाध्यायी {aref} ({aid}, {aname}); {karaka_cite}]"
    return case, cell, entry["definitive"]


# --------------------------------------------------------------------------- #
# PRATYAYA: resolve_pratyaya()/resolve_matup() name strings (WX) ->
# Devanagari + citation. Verified against krt_pratyaya_rulebook.json /
# taddhita_rulebook.json by content.
# --------------------------------------------------------------------------- #
PRATYAYA_CITATIONS = {
    "tumun": ("तुमुन्", "अष्टाध्यायी 3.3.10 (तुमुन्ण्वुलौ क्रियायां क्रियार्थायाम्)"),
    "ktvA": ("क्त्वा", "अष्टाध्यायी 3.4.21 (समानकर्तृकयोः पूर्वकाले)"),
    "vat": ("मतुप् (वत् आदेशः)", "अष्टाध्यायी 5.2.94 (तदस्यास्त्यस्मिन्निति मतुप्), 8.2.9 (मत्वर्थे भुवश्च)"),
    "mat": ("मतुप्", "अष्टाध्यायी 5.2.94 (तदस्यास्त्यस्मिन्निति मतुप्)"),
}


def lookup_pratyaya_citation(pratyaya_name):
    if not pratyaya_name:
        return "-", "", True
    entry = PRATYAYA_CITATIONS.get(pratyaya_name)
    if entry is None:
        return _best_effort_devanagari(pratyaya_name), "", False
    return entry[0], entry[1], True
