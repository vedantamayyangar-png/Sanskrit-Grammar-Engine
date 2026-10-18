#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
combined_splitter.py
=====================
Runs `sandhi_splitter.py` (the `sandhi/` tool) and `samasa_splitter.py`
(this folder) IN TANDEM on a single running Devanagari word or pada, so
each tool does the part it is actually good at:

  - `sandhi_splitter.py` (Stages 48-50, PROJECT_STATE.md gap #14/#18):
    peels off EXTERNAL sandhi junctions -- particles fused onto the next
    word (ca/vā/hi/...), avagraha elision, visarga/svara/vyañjana
    boundary changes -- using its own tested tiered ranking and
    already-complete-word guards (`_stem_after_common_inflection`, the
    single-character-piece guards, the paribhāṣā-12 rule-priority
    tiebreak). This is the layer verified against real running verse
    text (the 64-word corpus) and known to correctly recognize ordinary
    inflected words instead of over-splitting them -- exactly the
    failure mode `samasa_splitter.py` has no defense against on its own
    (its own candidate generator has no equivalent of
    `_stem_after_common_inflection`).

  - `samasa_splitter.py` (this folder): decomposes a genuine multi-member
    COMPOUND (samasa) into its constituent members, with upasarga/nañ/
    particle closed-class recognition, matup/kṛt-pratyaya resolution,
    and (new, this session -- see `build_dictionary_from_sqlite`) the
    SAME dictionary sandhi_splitter.py validates against
    (`apte_dictionary.sqlite`), rather than two tools silently
    disagreeing about what counts as a real word.

WHY NEITHER TOOL ALONE IS ENOUGH
---------------------------------
`sandhi_splitter.py`'s own SKILL.md documents its central open gap
(#14): compound words whose FUSED stem isn't independently
dictionary-headworded (सर्वभूतेषु, जातरोषस्य, दृढव्रतः, ...) get wrongly
split or left unsplit, because its candidate generators only look for
PHONOLOGICAL sandhi signatures at a junction -- they have no notion of
"this is a compound, decompose it into named members." That is exactly
what `samasa_splitter.py` is built to do. Conversely, `samasa_splitter.py`
alone has no defense against over-splitting an ordinary inflected word
(the false-positive class `sandhi_splitter.py`'s Tier-4/Tier-5 fixes
were built to catch) -- feeding it a whole raw pada word-by-word without
first stripping genuine external sandhi produces noise.

PIPELINE
--------
For each whitespace-delimited word in the input:
  1. Run `sandhi_splitter.split_word_recursive(word)` to peel EXTERNAL
     sandhi (particles, avagraha, boundary sandhi) into a list of
     `pieces`. This is the already-tested, real-corpus-verified layer;
     it is never bypassed.
  2. For each resulting piece, ask `samasa_splitter`'s `SamasaSplitter`
     (backed by the SAME `apte_dictionary.sqlite`) whether it further
     decomposes into a dictionary-verified multi-member compound. Only
     accept that decomposition if:
       a. `samasa_splitter` actually returns a dictionary-verified
          (not phonology-only) result with 2+ members, AND
       b. the piece is NOT already a complete word on its own (checked
          via `sandhi_splitter`'s own `dictionary_lookup` /
          `_stem_after_common_inflection`, reusing its guard rather
          than re-implementing it) -- this stops `samasa_splitter` from
          "discovering" a coincidental internal cut in an ordinary
          monomorphemic word that `sandhi_splitter` already correctly
          left alone (this is precisely gap #18's failure mode, applied
          one layer up).
     If accepted, replace the piece with its samasa members; otherwise
     keep the piece as-is (an atomic unit, whether or not it's fully
     dictionary-confirmed).
  3. Flatten and return, tagging each atomic unit with which layer
     produced it (`sandhi` vs `samasa`) and its confidence, so a caller
     can see exactly which tool is responsible for which piece of the
     final answer -- never silently blending unverified guesses from
     either side.

USAGE
-----
    D:\\python\\python.exe combined_splitter.py <word_or_pada> [--scheme iast|devanagari]
    D:\\python\\python.exe combined_splitter.py <wordlist.txt>   # one word/pada per line
    D:\\python\\python.exe combined_splitter.py --test           # runs against the bundled
                                                                  # fused-pada regression corpus

As a library:
    from combined_splitter import CombinedSplitter
    cs = CombinedSplitter()
    cs.split_pada("तपःस्वाध्यायनिरतं")   # devanagari, continuous (fused) input
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SANDHI_DIR = os.path.normpath(os.path.join(HERE, "..", "sandhi"))
if not os.path.isdir(SANDHI_DIR) and os.path.isfile(os.path.join(HERE, "sandhi_splitter.py")):
    SANDHI_DIR = HERE               # flat folder: sandhi_splitter.py, the rulebook and the sqlite dictionary sit next to this script
DEFAULT_SQLITE_DICT = os.path.join(SANDHI_DIR, "apte_dictionary.sqlite")

if SANDHI_DIR not in sys.path:
    sys.path.insert(0, SANDHI_DIR)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sandhi_splitter  # noqa: E402  (sandhi/sandhi_splitter.py, path-inserted above)
from samasa_splitter import SamasaSplitter  # noqa: E402
from indic_transliteration import sanscript  # noqa: E402
from indic_transliteration.sanscript import transliterate as tl  # noqa: E402
from build_ramayana_input import parasavarna_normalize  # noqa: E402  (sandhi/build_ramayana_input.py)


# --------------------------------------------------------------------------- #
# DETERMINISTIC JUNCTION LAYER (added 2026-09-23, Sarga-1 gold-standard pass)
#
# restore_word_boundary() asks the forward sandhi engine "which pre-sandhi
# pair reproduces the printed pair?" and then ranks candidates by
# dictionary validation. Scoring all 708 printed-token junctions of Sarga 1
# against the hand-written analysis showed it names only 88 of ~300 real
# junction sandhis. The misses are almost all cases where the PRINTED
# ending by itself proves that a sandhi rule applied -- a pada-final
# anusvāra before a consonant (मोऽनुस्वारः), a pada-final द्/ग्/ड्/ब्
# (जश्त्व -- a citation pada can never end in a voiced stop), च्/ज्/ञ् before a
# palatal (श्चुत्व), स/एष before a consonant (सुलोप), a hiatus after अ/आ
# (visarga lopa), a word ending in य्/व् (यण्) or आव्/आय् (अयादि) -- but the
# oracle's dictionary tie-break lets the as-printed form win whenever the
# restored citation form is not itself a headword (inflected words, verb
# forms, pronouns). These rules are unambiguous from spelling alone, so
# they are applied here as a FALLBACK whenever the oracle returns nothing
# better than "as-printed". Each rule is a Pāṇinian sūtra, cited in the
# same "name (a|p|s)" style the oracle already uses.
# --------------------------------------------------------------------------- #
_VOWEL_START = ("a", "ā", "i", "ī", "u", "ū", "ṛ", "ṝ", "ḷ", "e", "o", "'")
_HARD_START = ("k", "c", "ṭ", "t", "p", "ś", "ṣ", "s")  # includes aspirates (kh, ch, ...)
_VOICED_CONS = ("g", "j", "ḍ", "d", "b", "ṅ", "ñ", "ṇ", "n", "m", "y", "r", "l", "v", "h")
_JUNCTION_PARTICLES_A = {"ca", "na", "iva", "eva", "ha", "sma", "atha", "tathā", "yathā",
                         "hā", "vā", "mā", "sadā", "tadā", "yadā", "kadā", "sarvadā"}
_TRUE_R_FINALS = {"punar", "antar", "prātar", "svar", "ahar", "dvār", "gir", "pur"}


def _starts_consonant(tok):
    return bool(tok) and not tok.startswith(_VOWEL_START)


def _starts_soft(tok):
    return bool(tok) and (tok.startswith(_VOWEL_START) or tok.startswith(_VOICED_CONS))


def deterministic_junction(t1, t2, score=None):
    """Return (sandhi_type, sutra, left_citation, right_citation) for a printed IAST junction
    whose ending alone proves a sandhi rule applied, else None. Never guesses between two
    genuinely possible readings -- ambiguous patterns (e.g. -ā before a voiced consonant,
    which may be a real feminine -ā or a lost -āḥ) are deliberately left out."""
    if not t1 or not t2:
        return None
    last2 = t1[-2:]
    # 1. anusvāra before a consonant: final m -> ṃ
    if t1.endswith("ṃ") and _starts_consonant(t2):
        return ("anusvāra-sandhiḥ", "mo'nusvāraḥ (8|3|23)", t1[:-1] + "m", t2)
    # 2. saḥ / eṣaḥ lose visarga before any consonant
    if t1 in ("sa", "eṣa") and _starts_consonant(t2):
        return ("sulopa-sandhiḥ", "etattadoḥ sulopo'koranañsamāse hali (6|1|132)", t1 + "ḥ", t2)
    # 3. -d + dh- : t + h -> d + dh (jhayo ho'nyatarasyām) -- only when a lexicon scorer says
    #    the h- reading is the better word (real "tad dhanam"-type junctions stay plain jaśtva)
    if t1.endswith("d") and t2.startswith("dh") and score is not None:
        if score("h" + t2[2:]) > score(t2):
            return ("jaśtva-> pūrvasavarṇa-sandhiḥ",
                    "jhalāṃ jaśo'nte (8|2|39)-> jhayo ho'nyatarasyām (8|4|62)",
                    t1[:-1] + "t", "h" + t2[2:])
    # 4. jaśtva: a pada can never end in a voiced stop
    jash = {"d": "t", "g": "k", "ḍ": "ṭ", "b": "p"}
    if t1[-1] in jash and len(t1) > 1 and _starts_soft(t2):
        return ("jaśtva-sandhiḥ", "jhalāṃ jaśo'nte (8|2|39)", t1[:-1] + jash[t1[-1]], t2)
    # 5. ścutva: t + c/ch -> c, t + j/jh -> j, n + ś/c/j -> ñ
    if t1.endswith("c") and t2.startswith("c"):
        return ("ścutva-sandhiḥ", "stoḥ ścunā ścuḥ (8|4|40)", t1[:-1] + "t", t2)
    if t1.endswith("j") and t2.startswith("j"):
        return ("jaśtva-> ścutva-sandhiḥ", "jhalāṃ jaśo'nte (8|2|39)-> stoḥ ścunā ścuḥ (8|4|40)",
                t1[:-1] + "t", t2)
    if t1.endswith("ñ") and t2.startswith(("ś", "c", "j")):
        return ("ścutva-sandhiḥ", "stoḥ ścunā ścuḥ (8|4|40)", t1[:-1] + "n", t2)
    # 6. anunāsika: t + nasal -> n, only for closed forms whose t-reading is certain
    if t2.startswith(("n", "m")) and (t1.endswith("īn") or t1 in ("cin", "tan", "etan", "yan", "kiṃcin")):
        return ("anunāsika-sandhiḥ", "yaro'nunāsike'nunāsiko vā (8|4|45)", t1[:-1] + "t", t2)
    # 7. visarga -> r after a vowel other than a/ā, before a voiced sound
    if t1.endswith("r") and len(t1) > 2 and t1[-2] not in ("a", "ā") and _starts_soft(t2):
        left = t1 if t1 in _TRUE_R_FINALS else t1[:-1] + "ḥ"
        return ("repha-sandhiḥ", "sasajuṣo ruḥ (8|2|66)", left, t2)
    if t1 in _TRUE_R_FINALS and _starts_soft(t2):
        return ("repha-sandhiḥ", "sasajuṣo ruḥ (8|2|66)", t1, t2)
    # 8. -o before a voiced consonant / avagraha: aḥ -> o
    if t1.endswith("o") and len(t1) > 1:
        if t2.startswith("'"):
            return ("rutva -> utva-> guṇa-> pūrvarupa",
                    "sasajuṣo ruḥ (8|2|66)-> ato roraplutādaplute (6|1|113)-> ād guṇaḥ (6|1|87)-> eṅaḥ padāntādati (6|1|109)",
                    t1[:-1] + "aḥ", "a" + t2[1:])
        if t2.startswith(_VOICED_CONS):
            return ("rutva-> utva-> guṇa-sandhiḥ",
                    "sasajuṣo ruḥ (8|2|66)-> haśi ca (6|1|114)-> ād guṇaḥ (6|1|87)", t1[:-1] + "aḥ", t2)
    # 8b. n + t/c -> ṃs/ṃś (naś chavy apraśān 8.3.7): bhagavāṃs tatra, paśyaṃs tat
    if t1.endswith(("ṃs", "ṃś", "ṃṣ")) and t2.startswith(("t", "c", "ṭ")):
        return ("rutva-> satva (naś chavy apraśān)", "naś chavy apraśān (8|3|7)-> visarjanīyasya saḥ (8|3|34)",
                t1[:-2] + "n", t2)
    # 9. visarga -> s/ś/ṣ before a hard dental/palatal/retroflex
    if t1.endswith("ś") and t2.startswith(("c", "ś")):
        return ("satva-> ścutva-sandhiḥ", "visarjanīyasya saḥ (8|3|34)-> stoḥ ścunā ścuḥ (8|4|40)", t1[:-1] + "ḥ", t2)
    if t1.endswith("s") and t2.startswith("t"):
        return ("satva-sandhiḥ", "visarjanīyasya saḥ (8|3|34)", t1[:-1] + "ḥ", t2)
    if t1.endswith("ṣ") and t2.startswith("ṭ"):
        return ("satva-> ṣṭutva-sandhiḥ", "visarjanīyasya saḥ (8|3|34)-> ṣṭunā ṣṭuḥ (8|4|41)", t1[:-1] + "ḥ", t2)
    # 10. -e + avagraha: pūrvarūpa
    if t1.endswith(("e", "o")) and t2.startswith("'") and not t1.endswith("o"):
        return ("pūrvarūpa-sandhiḥ", "eṅaḥ padāntādati (6|1|109)", t1, "a" + t2[1:])
    # 11. ayādi: āv / āy before a vowel
    if last2 in ("āv", "āy") and t2.startswith(_VOWEL_START):
        return ("ayādi-sandhiḥ", "eco'yavāyāvaḥ (6|1|78)", t1[:-2] + ("au" if last2 == "āv" else "ai"), t2)
    # 11b. ṅamuṭ: a short vowel + ṅ/ṇ/n doubles before a vowel (ṅamo hrasvād aci ṅamuṇ nityam 8.3.32)
    if t1.endswith(("nn", "ṅṅ", "ṇṇ")) and t2.startswith(_VOWEL_START[:-1]) and len(t1) > 3:
        return ("ṅamuṭ-sandhiḥ", "ṅamo hrasvādaci ṅamuṇnityam (8|3|32)", t1[:-1], t2)
    # 12. yaṇ: a word ending in a semivowel after a consonant
    if len(t1) > 1 and t1[-1] in ("y", "v") and t1[-2] not in "aāiīuūṛeo" and t2.startswith(_VOWEL_START):
        return ("yaṇ", "iko yaṇaci (6|1|77)", t1[:-1] + ("i" if t1[-1] == "y" else "u"), t2)
    # 13. hiatus after a/ā: a visarga was dropped (bho-bhago-agho-apūrvasya yo'śi, lopaḥ śākalyasya)
    if t2.startswith(_VOWEL_START[:-1]) and t1 not in _JUNCTION_PARTICLES_A:
        if t1.endswith("ā") and len(t1) > 1:
            return ("visarga-lopa (āḥ)", "bhobhagoaghoapūrvasya yo'śi (8|3|17)-> lopaḥ śākalyasya (8|3|19)", t1 + "ḥ", t2)
        if t1.endswith("a") and not t1.endswith(("ai", "au")) and len(t1) > 1:
            return ("visarga-lopa (aḥ)", "bhobhagoaghoapūrvasya yo'śi (8|3|17)-> lopaḥ śākalyasya (8|3|19)", t1 + "ḥ", t2)
    # 14. visarga dropped before a sibilant + hard consonant (vārttika khar-pare śari vā visargalopo vaktavyaḥ)
    if t1.endswith("a") and t1 not in _JUNCTION_PARTICLES_A and len(t1) > 3 \
            and t2[:1] in ("s", "ś", "ṣ") and t2[1:2] in ("k", "c", "ṭ", "t", "p", "m", "n"):
        return ("visarga-lopa (khar-para śar)", "kharpare śari vā visargalopo vaktavyaḥ (vārttika on 8|3|36)", t1 + "ḥ", t2)
    return None


class CombinedSplitter:
    def __init__(self, sqlite_dict_path=DEFAULT_SQLITE_DICT):
        self.sqlite_dict_path = sqlite_dict_path
        self.sp = SamasaSplitter()
        if sqlite_dict_path and os.path.exists(sqlite_dict_path):
            self.sp.load_sqlite_dictionary(sqlite_dict_path)
        self._db_path = sqlite_dict_path

    # ------------------------------------------------------------- utils --
    def _iast_word_score(self, iast_word):
        """Rough lexical plausibility of an IAST word, used only to break the one genuinely
        ambiguous deterministic-junction case (d + dh-: is the second word dh- or h-?).
        2 = the word (or its stem after a common ending, or a kṛt-resolved form) is attested;
        1 = its first 3+ letters are an attested stem (first member of a compound);
        0 = nothing found."""
        deva = parasavarna_normalize(tl(iast_word, sanscript.IAST, sanscript.DEVANAGARI))
        try:
            if self._is_dictionary_word(deva) or self.sp.resolve_pratyaya(iast_word, scheme="iast"):
                return 2
        except Exception:
            pass
        wx = self.sp._to_wx(iast_word, sanscript.IAST)
        for n in range(len(wx) - 1, 2, -1):
            if self.sp.dictionary and wx[:n] in self.sp.dictionary:
                return 1
        return 0

    def _is_dictionary_word(self, deva_piece):
        """
        Does `deva_piece` resolve to a real dictionary headword, either
        directly or via sandhi_splitter.py's own citation-form guard
        (`_stem_after_common_inflection`, the mātup/vatup/common-ending
        table from Stage 48/50)? Used only for CONFIDENCE labeling on an
        atomic (non-decomposed) piece -- NOT to gate whether samasa
        decomposition is attempted (see split_word: a word being its own
        lexicalized headword does not mean it isn't ALSO a real compound
        worth showing the members of -- e.g. मुनिपुङ्गवः is independently
        headworded in Apte AND is the genuine tatpuruṣa मुनि + पुङ्गवः;
        this project's own grammar engine keeps whole-word lexical status
        (Component 1) and samasa-vigraha (Component 9) as separate,
        coexisting evidence, not mutually exclusive -- see Stage-42
        PROJECT_STATE.md result for the same मुनिपुंगवम् example).
        """
        hit = sandhi_splitter.dictionary_lookup(deva_piece, db_path=self._db_path)
        if hit.get("found"):
            return True
        stemmed = sandhi_splitter._stem_after_common_inflection(deva_piece, db_path=self._db_path)
        return stemmed is not None

    def _is_non_compound_form(self, deva_piece):
        """
        Is `deva_piece` a recognized VERB form (looks_like_verb_form), a
        core PRONOUN form (PRONOUN_FORMS_WX), a मतुप्/वतुप् possessive-
        pratyaya form (looks_like_matup_form), OR already a DIRECT
        dictionary headword in its own right (dictionary_lookup, exact/
        H/M-strip match)? All four are genuinely non-compound whole-word
        categories that must never be forced through samasa decomposition,
        no matter what a coincidental phonological cut might otherwise
        suggest.

        The direct-headword check is the one that matters most in
        practice, found empirically while testing this pipeline against
        real verse text: नारदं (a proper noun), साम्प्रतं (an adverb),
        युक्तः, विद्वान् (participles) are ALL direct dictionary hits on
        the whole word, and were ALL being wrongly torn into two
        "dictionary-verified" pieces by samasa_splitter's own
        stem-candidate machinery (नार+दं, साम्+प्रतं, युक्+तः, विथ्+वान्)
        -- the same "coincidental phonological cut, not a genuine split"
        failure mode sandhi_splitter.py's SKILL.md warns confirmation
        status alone cannot catch. मुनिपुङ्गवम् (a genuine compound that
        ALSO happens to be independently headworded) is NOT a direct hit
        via this exact/stripped-suffix check (dictionary_lookup only
        strips H/M, not the -अम् this word actually ends in), so it
        correctly stays eligible for decomposition -- see this class's
        module docstring for why whole-word lexical status and
        samasa-vigraha are treated as compatible, not exclusive, but only
        when the whole word ISN'T already a plain direct dictionary
        match on its own citation-ish form.
        looks_like_matup_form (गुणवान्, वीर्यवान्, आत्मवान्, विद्वान् --
        possessive/participial -वान्/-मान् formations, not tatpuruṣa/
        karmadhāraya compounds at all) is checked regardless of the
        direct-hit status, since these words are often NOT direct hits
        (the dictionary indexes the bare stem, not the -वान्/-मान् form)
        but are still definitionally not samasa members.
        """
        if self.sp.looks_like_verb_form(deva_piece, scheme="devanagari"):
            return True
        if self.sp.looks_like_matup_form(deva_piece, scheme="devanagari"):
            return True
        wx = self.sp._to_wx(deva_piece, sanscript.DEVANAGARI)
        from samasa_splitter import PRONOUN_FORMS_WX
        if wx in PRONOUN_FORMS_WX:
            return True
        return sandhi_splitter.dictionary_lookup(deva_piece, db_path=self._db_path).get("found", False)

    def _best_samasa_decomposition(self, deva_piece):
        """
        Try to decompose `deva_piece` (a Devanagari word assumed ALREADY
        complete/correctly-segmented -- i.e. the caller is responsible
        for handing this a genuine word, not an arbitrary fragment) into
        samasa members. Returns {"type_guess": str, "members": [...]} or
        None if no dictionary-verified 2+-member decomposition survives
        this pipeline's false-positive guards.

        Shared by split_word() and analyze_pada_line() so both entry
        points apply the IDENTICAL acceptance rule -- see split_word's
        own comments (still present there) for why each guard exists;
        this is a straight extraction, not a behavior change.
        """
        if self._is_non_compound_form(deva_piece):
            return None
        samasa_results = self.sp.split(deva_piece, scheme="devanagari", verbose=False)

        def _all_members_long_enough(members):
            for m in members:
                wx = self.sp._to_wx(m, sanscript.DEVANAGARI)
                # Normalize a trailing anusvara ("M") to plain "m" before
                # the closed-class check -- "sam" (सम्, the upasarga)
                # surfaces as "saM" whenever it's word-final (see
                # SamasaSplitter.is_upasarga's own docstring for the same
                # normalization, needed for the same reason here).
                wx_normalized = wx[:-1] + "m" if wx.endswith("M") else wx
                if wx_normalized in self.sp.CLOSED_CLASS_LEN_EXEMPT:
                    # A genuine upasarga/particle/nañ-prefix (सं, वि, अ/अन्,
                    # ...) is SUPPOSED to be this short as a compound's
                    # first member -- samasa_splitter.py already exempts
                    # these elsewhere (UPASARGA_LEN_EXEMPT); reusing the
                    # same closed-class set here so this guard doesn't
                    # wrongly exclude the same words that class already
                    # deliberately allows (e.g. सं in संयुगे, सम्+युगे).
                    continue
                # A member's STEM (after stripping one trailing
                # visarga/anusvara/final-nasal case marker) must be at
                # least 3 WX chars, on top of the existing >=3-char floor
                # on the raw form -- found necessary by direct testing:
                # "satyavākyo" (सत्यवाक्यः, a genuine सत्य+वाक्यः
                # karmadhāraya) was wrongly split as सत्यवाक्+यः instead,
                # because यः ("yaH", 3 WX chars) is a real dictionary
                # word (the relative pronoun "who") that cleared the
                # plain >=3 floor on the raw form. Stripping the trailing
                # "H"/"M"/"m" first drops यः to a 2-char stem ("ya"),
                # correctly excluding it (यः isn't in CLOSED_CLASS_LEN_
                # EXEMPT -- relative pronouns aren't upasargas/particles),
                # while genuine content-word members (व्रतः->"vrawa" 5
                # chars, मुनि->"muni" 4 chars, दृढ->"dfQ" 3 chars/no
                # strippable ending) are unaffected.
                stem = wx[:-1] if wx and wx[-1] in "HMm" else wx
                if len(wx) < 3 or len(stem) < 3:
                    return False
            return True

        def _all_members_independently_validated(members):
            """
            Require every non-exempt member to independently pass a
            STRICTER dictionary check than samasa_splitter's own
            `_in_dictionary` -- which was found, by direct audit of a
            full 79-verse run, to accept far too much: its
            `_stem_candidates` strips any of 26 declension-suffix
            patterns, TWO rounds deep (up to ~676 chained combinations),
            so two coincidentally-matching fragments of an ordinary
            single word constantly get accepted as "dictionary-verified"
            (e.g. विष्णुना, a proper noun, wrongly validated as
            वि + ष्णुना; धैर्येण, instrumental of धैर्य, as धैर् + येण;
            नियतात्मा as नियता + त्मा -- त्मा isn't even a word).

            Each member must instead pass ONE of: a genuine upasarga/
            particle exemption (same CLOSED_CLASS_LEN_EXEMPT set used
            above), sandhi_splitter.dictionary_lookup's STRICT exact/H/M-
            strip-only match (no declension guessing at all), or
            sandhi_splitter._stem_after_common_inflection -- the small,
            hand-curated ending table built and hardened specifically
            against false positives during that tool's own Stage 48-50
            real-corpus debugging (मतुप्/वतुप् + a dozen common endings),
            a much narrower and more trustworthy source of "yes, this
            ending is legitimately strippable" than samasa_splitter's
            own generic 26-entry table.

            Verified directly (not assumed) against 12 known-bad and 7
            known-good decompositions before being enabled here: rejects
            9 of the 12 bad cases while preserving all 7 good ones
            (मुनिपुङ्गवम्, धर्मज्ञः, दृढव्रतः, सर्वभूतेषु, संयुगे,
            तपःस्वाध्यायनिरतं, वाग्विदां). Two DIFFERENT, harder failure
            modes remain open, NOT fixable by tightening this guard
            further:
              1. Both fragments happen to be independently genuine
                 dictionary words even though the whole word is not a
                 compound at all (क्षमया -> क्ष+मया, अयाचत -> अया+चत,
                 प्रजानां -> प्रजा+नां -- all coincidental).
              2. A genuine DICTIONARY-COVERAGE GAP on the correct
                 reading's own member, while a wrong reading's members
                 both happen to be covered: सुललाटः is really सु+ललाटः
                 (सु+ललाट, "good-browed"), but ललाट/ललाटः isn't in
                 apte_dictionary.sqlite at all (checked directly --
                 dictionary_lookup fails on both the visarga and bare
                 forms), while the wrong सु+लल+अटः reading's fragments
                 (लल "playful", अट "wandering") are each independently
                 real, rare headwords. No amount of stricter fragment-
                 validation logic fixes a genuine missing headword --
                 this needs a richer dictionary, not better guard logic.
            """
            for m in members:
                wx = self.sp._to_wx(m, sanscript.DEVANAGARI)
                wx_normalized = wx[:-1] + "m" if wx.endswith("M") else wx
                if wx_normalized in self.sp.CLOSED_CLASS_LEN_EXEMPT:
                    continue
                if sandhi_splitter.dictionary_lookup(m, db_path=self._db_path).get("found", False):
                    continue
                if sandhi_splitter._stem_after_common_inflection(m, db_path=self._db_path) is not None:
                    continue
                return False
            return True

        best = next((r for r in samasa_results
                     if r["confidence"] == "dictionary-verified" and len(r["members"]) >= 2
                     and _all_members_long_enough(r["members"])
                     and _all_members_independently_validated(r["members"])
                     # guess_samasa_type() itself already flags a first
                     # member matching SANDHI_PARTICLE_WX as "NOT a
                     # samasa" (see its own docstring) -- a candidate
                     # carrying that label must be REJECTED here, not
                     # merely relabeled and shown as if it were an
                     # answer. Found necessary by direct testing:
                     # "cāritreṇa" (चारित्रेण, a single word, instrumental
                     # of चारित्र) was being wrongly presented as
                     # "च" (the particle "and") + "अरित्रेण" -- a
                     # phonologically valid but semantically bogus cut
                     # of a word that has no preceding/following "ca" to
                     # combine with at all; this pipeline had been
                     # accepting samasa_splitter's own self-flagged
                     # non-samasa candidates instead of treating that
                     # flag as a rejection.
                     and not r["type_guess"].startswith("NOT a samasa")),
                    None)
        if best is None:
            return self._recursive_samasa_fallback(deva_piece)
        return {"type_guess": best["type_guess"], "members": best["members"]}

    # ---------------------------------------------------------------------- #
    # FALLBACK (added 2026-09-30): multi-member compounds whose members are
    # only dictionary-verifiable after (a) taking the headword form actually
    # stored in apte_dictionary.sqlite (neuter a-stems are stored with -M,
    # masculine with -H: dhAnya is stored as dhAnyaM) and (b) stripping the
    # neuter plural -Ani (upapannAni -> upapanna). Without this, a correct cut
    # such as dhanadhAnya + upapannAni stays "phonology-only" and is discarded,
    # and 3-member compounds are never reached because the left member
    # (dhanadhAnya) is itself a compound and not a headword.
    # Conservative: only runs when the strict path found nothing, and EVERY
    # final atom must be a dictionary member of >= 3 WX chars.
    # ---------------------------------------------------------------------- #
    def _member_lexical_forms(self, m):
        stems = [m]
        if m.endswith("\u093e\u0928\u093f"):        # -Ani (neuter nom/acc pl of a-stems)
            stems.append(m[:-3])
        forms = []
        for st in stems:
            forms += [st, st + "\u0902", st + "\u0903"]  # bare, +M (neuter), +H (masculine)
        return forms

    def _member_in_dictionary(self, m):
        wx = self.sp._to_wx(m, sanscript.DEVANAGARI)
        if len(wx) < 4 or m.endswith("\u094d"):     # >=4 sounds, and never a bare consonant-final scrap
            return False
        for f in self._member_lexical_forms(m):
            if sandhi_splitter.dictionary_lookup(f, db_path=self._db_path).get("found", False):
                return True
        return False

    def _recursive_members(self, piece, depth=0):
        """Return a list of dictionary-verified atoms whose concatenation-with-sandhi is `piece`,
        or None. A piece that is itself a (lexical-form) dictionary word is an atom."""
        if depth > 0 and self._member_in_dictionary(piece):
            return [piece]
        if depth >= 3:
            return None
        best = None
        binary = []
        # (1) plain concatenative cuts at akshara boundaries (no sandhi at the joint)
        _dep = "\u093e\u093f\u0940\u0941\u0942\u0943\u0944\u0947\u0948\u094b\u094c\u094d\u0902\u0903\u0901"
        for i in range(2, len(piece) - 1):
            if piece[i] in _dep or piece[i - 1] == "\u094d":
                continue
            binary.append([piece[:i], piece[i:]])
        # (2) sandhi-aware binary candidates from samasa_splitter
        for r in self.sp.split(piece, scheme="devanagari", verbose=False):
            if len(r["members"]) == 2 and not r["type_guess"].startswith("NOT a samasa"):
                binary.append(r["members"])
        for ms in binary:
            left = self._recursive_members(ms[0], depth + 1)
            if not left:
                continue
            right = self._recursive_members(ms[1], depth + 1)
            if not right:
                continue
            cand = left + right
            # prefer the fewest atoms, then the longest shortest-atom (avoids over-splitting)
            key = (len(cand), -min(len(x) for x in cand), sum(len(x) for x in cand))  # last: prefer a- over long-A restoration (a+u and A+u both give o)
            if best is None or key < best[0]:
                best = (key, cand)
        return best[1] if best else None

    def _recursive_samasa_fallback(self, deva_piece):
        atoms = self._recursive_members(deva_piece)
        if not atoms or len(atoms) < 2:
            return None
        return {"type_guess": "samāsa (members dictionary-verified; type not determined)",
                "members": atoms}

    def analyze_pada_line(self, iast_tokens):
        """
        Correct sandhi+samasa analysis of a REAL printed pada-line -- a
        list of GRETIL-tokenized IAST words EXACTLY as segmented in the
        source text (e.g. sa_rAmAyaNa.txt), one physical line at a time.

        This is deliberately NOT built on split_word()/
        sandhi_splitter.split_word_recursive(): that function assumes its
        input is a single fused string with an internal boundary to find
        -- correct when given a genuinely fused pāda, but WRONG when
        given an already-isolated, already-complete GRETIL token (it
        will manufacture a fake internal cut rather than report "no
        sandhi here"). Confirmed directly: feeding isolated tokens this
        way produced ~90%+ false positives across the first 80 words of
        a real Sarga-1 run (e.g. "parIpapraccha" alone wrongly torn into
        "paH"+"ipapraccha"), while the SAME underlying engine, asked the
        right question -- "is there real sandhi AT THE JUNCTION between
        this word and the next, as GRETIL already segmented them?" --
        gets it right (parIpapraccha + vAlmIkir -> correctly recognizes
        no restoration is needed at all).

        Uses samasa_splitter.py's own `restore_word_boundary` (the real
        forward Sandhi.sandhi() engine as oracle, with dictionary
        validation) junction-by-junction, exactly as `restore_tokens`
        already does elsewhere in this file -- reimplemented inline here
        (not calling restore_tokens directly) only because this method
        also needs the PER-JUNCTION rule name/sūtra for reporting, which
        restore_tokens discards.

        Returns a list of per-word dicts, one per input token, in order:
            {
              "word": str,              # as printed (IAST)
              "citation_form": str,     # restored citation form (IAST)
              "sandhi_rule": str|None,  # e.g. "repha-sandhiḥ", or None
              "sandhi_sutra": str,
              "sandhi_vigraha": (left, right)|None,   # IAST
              "samasa": {"type_guess": str, "members": [str, ...]}|None,  # Devanagari
            }
        A None sandhi_rule / samasa means exactly that: checked, nothing
        found -- never a guess presented as a result.
        """
        n = len(iast_tokens)
        junctions = [None] * max(n - 1, 0)
        for i in range(n - 1):
            try:
                cands = self.sp.restore_word_boundary(iast_tokens[i], iast_tokens[i + 1], scheme="iast")
            except Exception:
                cands = []
            junctions[i] = cands[0] if cands else None
            # Deterministic fallback (see deterministic_junction above): only when the oracle
            # found nothing better than the printed form itself.
            if junctions[i] is None or junctions[i].get("sandhi_type") == "as-printed":
                det = deterministic_junction(iast_tokens[i], iast_tokens[i + 1], score=self._iast_word_score)
                if det is not None:
                    styp, sutra, left, right = det
                    junctions[i] = {"left": left, "right": right, "sandhi_type": styp,
                                    "sutra": sutra, "dict_backed": None, "source": "deterministic"}

        # Citation forms, left-to-right -- mirrors restore_tokens()'s own
        # logic exactly (an avagraha-restored token's real ENDING, fixed
        # by the NEXT junction, still gets applied on top of its already
        # avagraha-restored BEGINNING).
        citation = list(iast_tokens)
        for i in range(n - 1):
            best = junctions[i]
            if best is None:
                continue
            if best["left"] != citation[i]:
                citation[i] = best["left"]
            if best["right"] != iast_tokens[i + 1]:
                citation[i + 1] = best["right"]
        # An avagraha stands for an elided initial अ (एङः पदान्तादति): restore it rather than
        # dropping the apostrophe -- "samartho 'si" is samarthaḥ + asi, not + si (Sarga-1 pass fix).
        citation = [("a" + c[1:]) if c.startswith("'") else c for c in citation]

        rows = []
        for i, word in enumerate(iast_tokens):
            best = junctions[i] if i < len(junctions) else None
            if best is not None and best["sandhi_type"] != "as-printed":
                sandhi_rule = best["sandhi_type"]
                sandhi_sutra = best.get("sutra", "")
                sandhi_vigraha = (best["left"], best["right"])
            else:
                sandhi_rule = None
                sandhi_sutra = ""
                sandhi_vigraha = None

            # parasavarna_normalize: an anusvara directly before a
            # class-stop consonant must be spelled as that class's own
            # nasal letter (e.g. "muniMgavam" -> मुनिङ्गवम्... correctly
            # मुनिपुङ्गवम्, not मुनिपुंगवम्) to match how this project's
            # dictionary indexes citation forms (gap #15, PROJECT_STATE.md)
            # -- omitting this here (found by direct testing) caused a
            # real false samasa split (मुनिपुंगवम् -> मुनि+पुंग+वम् instead
            # of मुनि+पुङ्गवम्) purely from the un-normalized spelling not
            # matching the dictionary's own headword form.
            token_split = self.split_fused_token(citation[i])
            deva_citation = parasavarna_normalize(
                tl(token_split["pieces"][-1] if token_split else citation[i], sanscript.IAST, sanscript.DEVANAGARI))
            legacy = self._best_samasa_decomposition(deva_citation)
            samasa = self._classified_samasa(token_split["pieces"][-1] if token_split else citation[i])
            if samasa is None and self._classifier() is False:
                samasa = legacy         # morphology data unavailable: old behaviour

            rows.append({
                "word": word, "citation_form": citation[i],
                "sandhi_rule": sandhi_rule, "sandhi_sutra": sandhi_sutra,
                "sandhi_vigraha": sandhi_vigraha, "samasa": samasa,
                "samasa_legacy": legacy,
                "token_split": token_split["pieces"] if token_split else None,
                "token_split_sandhi": token_split["sandhi"] if token_split else None,
            })
        return rows

    # ------------------------------------------------ fused printed tokens --
    # GRETIL prints some genuine two-word sandhi fusions as ONE token (caiva = ca + eva,
    # sītāpy = sītā + api, tasyābhiṣeka… = tasya + abhiṣeka…). analyze_pada_line only looks at
    # junctions BETWEEN printed tokens, so these were invisible (PROJECT_STATE.md open item 8:
    # caitat). Running the recursive splitter on every token is the change already proven to
    # cause ~90% false positives, so this is deliberately narrow: a token is split only if
    #   (1) the whole token is NOT already a validated simple word (pada_analyser score >= 3, not
    #       a compound guess), and
    #   (2) the left piece is a closed-class word (particle / pronoun / adverb) OR carries an
    #       overt inflection (verb, gerund, case ending) -- a compound's first member never does,
    #       which is what separates tasya+abhiṣeka (two words) from kausalyā+ānanda (compound);
    #   (3) the right piece is itself a plausible word (score >= 2).
    _CLOSED_LEFT = {"ca", "na", "sa", "tu", "hi", "iva", "eva", "iti", "api", "atha", "tatra", "yatra",
                    "sadā", "sarvadā", "tadā", "yadā", "tena", "tasya", "asya", "tathā", "yathā",
                    "evam", "punar", "saha", "ha", "vā", "mā", "tataḥ", "yena", "yasya", "kim"}
    _CLOSED_RIGHT = {"api", "iti", "eva", "atha", "iva", "asya", "etat", "etad", "ātmānam", "asmin",
                     "idam", "ayam", "enam", "eṣaḥ", "api"}

    def _pa(self):
        if getattr(self, "_pada_analyser", None) is None:
            morph = os.path.normpath(os.path.join(HERE, "..", "morphology"))
            if morph not in sys.path:
                sys.path.insert(0, morph)
            try:
                from pada_analyser import PadaAnalyser
                self._pada_analyser = PadaAnalyser()
            except Exception:           # morphology data missing: feature silently off
                self._pada_analyser = False
        return self._pada_analyser

    def _classifier(self):
        """samasa_classifier.SamasaClassifier sharing this splitter's PadaAnalyser (lazy), or
        False if the morphology data is not available."""
        if getattr(self, "_samasa_classifier", None) is None:
            pa = self._pa()
            if not pa:
                self._samasa_classifier = False
            else:
                from samasa_classifier import SamasaClassifier
                self._samasa_classifier = SamasaClassifier(pa)
        return self._samasa_classifier

    def _classified_samasa(self, iast_word):
        """Samāsa decision from samasa_classifier (ending stripped first, lexicon-validated members,
        explicit type rule). Returns the analyze_pada_line samasa shape, or None."""
        sc = self._classifier()
        if not sc:
            return None
        try:
            res = sc.analyse(iast_word, scheme="iast")
        except Exception:
            return None
        if not res:
            return None
        return {"type_guess": f"{res['type']} — {res['reason']}", "type": res["type"],
                "members": res["members"], "confidence": res["confidence"],
                "stem": res["stem"], "source": "samasa_classifier"}

    def _word_score(self, iast):
        pa = self._pa()
        if not pa:
            return 0, None
        rd = pa.analyse(iast, scheme="iast", max_readings=1)
        if not rd:
            return 0, None
        return rd[0]["_score"], rd[0]

    def split_fused_token(self, iast_token):
        """Return {"pieces": [left, right], "sandhi": (type, sutra)} or None."""
        t = iast_token
        if len(t) < 4 or not self._pa():
            return None
        whole, wr = self._word_score(t)
        whole_is_word = whole >= 2.5 and not (wr and wr.get("members"))
        whole_is_compound = bool(wr and wr.get("members")) and whole >= 2
        cands = []
        for k in range(1, len(t) - 1):
            c = t[k]
            left, right = t[:k], t[k + 1:]
            opts = []
            if c == "ā":
                opts += [(left + "a", "a" + right, "dīrgha-sandhiḥ", "akaḥ savarṇe dīrghaḥ (6|1|101)"),
                         (left + "a", "ā" + right, "dīrgha-sandhiḥ", "akaḥ savarṇe dīrghaḥ (6|1|101)"),
                         (left + "ā", "a" + right, "dīrgha-sandhiḥ", "akaḥ savarṇe dīrghaḥ (6|1|101)"),
                         (left + "ā", "ā" + right, "dīrgha-sandhiḥ", "akaḥ savarṇe dīrghaḥ (6|1|101)")]
            elif c == "e" and not t[k - 1:k] in ("a", "ā"):
                opts += [(left + "a", "i" + right, "guṇa-sandhiḥ", "ād guṇaḥ (6|1|87)"),
                         (left + "ā", "i" + right, "guṇa-sandhiḥ", "ād guṇaḥ (6|1|87)")]
            elif c == "o":
                opts += [(left + "a", "u" + right, "guṇa-sandhiḥ", "ād guṇaḥ (6|1|87)"),
                         (left + "ā", "u" + right, "guṇa-sandhiḥ", "ād guṇaḥ (6|1|87)")]
            elif t[k:k + 2] == "ai":
                right = t[k + 2:]
                opts += [(left + "a", "e" + right, "vṛddhi-sandhiḥ", "vṛddhireci (6|1|88)"),
                         (left + "ā", "e" + right, "vṛddhi-sandhiḥ", "vṛddhireci (6|1|88)"),
                         (left + "a", "ai" + right, "vṛddhi-sandhiḥ", "vṛddhireci (6|1|88)")]
            elif (k >= 2 and t[k - 1] == "ā" and c in "dbgjvmyrl" and len(t) - k >= 3
                  and not t[k + 1:k + 2] in ("a", "ā", "i", "ī", "u", "ū", "e", "o")):
                # visarga-lopa (8.3.19, optional): tuṣṭāḥ + dhanaiḥ printed as tuṣṭādhanaiḥ.
                # Only the restored nominative ḥ-form on the left and an attested right piece qualify.
                lh, rh = left + "ḥ", t[k:]
                lr_ = self._word_score(lh)[1]
                rr_ = self._word_score(rh)[1]
                if (lr_ and lr_.get("type") == "noun" and lr_.get("case") in (1, 2, 8) and not lr_.get("members")
                        and rr_ and rr_.get("type") == "noun" and rr_.get("case") in (3, 4, 5)
                        and self._is_dictionary_word(tl(rr_["stem"], sanscript.DEVANAGARI, sanscript.DEVANAGARI))):
                    opts += [(lh, rh, "visarga-lopa", "lopaḥ śākalyasya (8|3|19), vikalpena")]
            elif c in ("y", "v") and t[k + 1:k + 2] in ("a", "ā", "u", "e", "o") and t[k - 1:k] not in "aāiīuūeo":
                opts += [(left + ("i" if c == "y" else "u"), right, "yaṇ", "iko yaṇaci (6|1|77)")]
            for l, r, styp, sutra in opts:
                if len(l) < 2 or len(r) < 2:
                    continue
                closed_l, closed_r = l in self._CLOSED_LEFT, r in self._CLOSED_RIGHT
                ls, lr = self._word_score(l)
                overt_l = bool(lr and (lr.get("type") == "verb"
                                       or (lr.get("type") == "avyaya" and lr.get("kind") in ("krdanta", "taddhita"))))
                if not closed_l:
                    if lr is None or lr.get("members") or ls < (2 if closed_r else 3):
                        continue
                    if styp == "yaṇ" and lr["type"] != "verb":
                        continue        # i/u-final nouns are too often compound first members
                    overt = (lr["type"] == "verb"
                             or (lr["type"] == "avyaya" and lr.get("kind") in ("krdanta", "taddhita"))
                             or (lr["type"] == "noun" and lr.get("case") != 8
                                 and lr["stem"] != tl(l, sanscript.IAST, sanscript.DEVANAGARI)))
                    if not (overt or closed_r):
                        continue
                rs, rr = self._word_score(r)
                if rs < 2 and not closed_r:
                    continue
                # Guard (added): a right-hand piece that is only a *verb reading* with no
                # dictionary headword (ākyaḥ → √अश् laṅ, from satyavākyaḥ) is not evidence of a
                # real word boundary. Require lexical support for non-closed right pieces.
                if (not closed_r and rr is not None and not rr.get("members")
                        and (rr.get("type") == "verb" or (rr.get("type") == "noun" and len(r) <= 4))
                        and not self._is_dictionary_word(tl(r, sanscript.IAST, sanscript.DEVANAGARI))):
                    continue
                if whole_is_word and not (closed_l and closed_r) and not (closed_l and rs > whole + 0.3):
                    continue            # the unsplit token is already a good word: keep it
                if whole_is_compound and not closed_r and (rr is None or rr.get("members") or rs <= whole):
                    continue            # cāru+nisvana is a better compound than ca + āru-nisvana
                # Added: a token that is itself a validated compound (nihatāmitraḥ, tuṣṭādhanaiḥ,
                # dharmātmanā) is never cut into two non-closed-class nominal pieces. Only a
                # closed-class word (ca, tasya, sarvadā…) or an overt verb may be split off.
                # Added: a split of two non-closed pieces needs at least one dictionary-backed piece.
                # bāhlīkaiḥ → bā + ahlīkaiḥ had neither piece attested and was accepted on score alone.
                if not closed_l and not closed_r and styp != "visarga-lopa":
                    dl = self._is_dictionary_word(tl(l, sanscript.IAST, sanscript.DEVANAGARI))
                    dr = self._is_dictionary_word(tl(r, sanscript.IAST, sanscript.DEVANAGARI)) or (
                        r.startswith("a") and len(r) > 4 and self._is_dictionary_word(tl(r[1:], sanscript.IAST, sanscript.DEVANAGARI)))
                    if not (dl or dr):
                        continue
                if (whole_is_compound and len(wr.get("members") or []) == 2 and styp != "visarga-lopa"
                        and not closed_l and not closed_r and not overt_l):
                    continue
                bonus = 0.5 if (styp == "vṛddhi-sandhiḥ" and r.startswith("e")) else 0   # a+e -> ai is the regular vṛddhi (ca+eka), not ca+aika
                # Ranking only: pieces that are dictionary headwords beat pieces that are merely
                # analysable (nāvidvān: avidvān over the phantom āvidvān).
                dict_bonus = 0.75 if (not closed_r and (self._is_dictionary_word(tl(r, sanscript.IAST, sanscript.DEVANAGARI))
                                                        or (r.startswith("a") and len(r) > 4 and   # nañ: a-vidvān ← vidvān
                                                            self._is_dictionary_word(tl(r[1:], sanscript.IAST, sanscript.DEVANAGARI))))) else 0
                cands.append((ls + rs + (1 if closed_l else 0) + (1 if closed_r else 0) + bonus + dict_bonus, l, r, styp, sutra))
        if not cands:
            return None
        cands.sort(key=lambda c: (-round(c[0], 6), c[1], c[2]))
        _, l, r, styp, sutra = cands[0]
        return {"pieces": [l, r], "sandhi": (styp, sutra)}

# --------------------------------------------------------------------------- #
    def split_word(self, deva_word):
        """
        Run the two-tool pipeline on a single continuous Devanagari word
        (may itself be sandhi-fused with a following particle, e.g. a
        whole pāda).
        """
        sandhi_result = sandhi_splitter.split_word_recursive(deva_word)
        pieces = sandhi_result["pieces"]
        sandhi_rules = [
            {"rule_id": step["rule_id"], "note": step["note"],
             "left": step["left"], "right": step["right"]}
            for step in sandhi_result["steps"]
        ]
        samasa_decompositions = []

        # If ANY step was unconfirmed on BOTH sides, discard the spurious phonological
        # split and keep the intact word so compound analysis can process it.
        sandhi_is_shaky = any(
            not step["left_confirmed"] and not step["right_confirmed"]
            for step in sandhi_result["steps"]
        )

        if sandhi_is_shaky:
            pieces = [deva_word]
            sandhi_rules = []

        atoms = []
        for piece in pieces:
            # 1. Classifier-based analysis (IAST-based, strips inflections like -āni)
            iast_piece = tl(piece, sanscript.DEVANAGARI, sanscript.IAST)
            classified = self._classified_samasa(iast_piece)
            if classified and len(classified.get("members", [])) >= 2:
                deva_members = [tl(m, sanscript.IAST, sanscript.DEVANAGARI) for m in classified["members"]]
                samasa_decompositions.append({
                    "piece": piece,
                    "type_guess": classified.get("type_guess", "samāsa"),
                    "members": deva_members,
                })
                for member in deva_members:
                    atoms.append({"text": member, "source": "samasa-member",
                                  "confidence": "dictionary-verified"})
                continue

            if self._is_non_compound_form(piece):
                atoms.append({"text": piece, "source": "sandhi-piece",
                              "confidence": "dictionary-verified" if self._is_dictionary_word(piece)
                              else "unverified (recognized verb/pronoun form)"})
                continue

            # 2. Legacy samāsa decomposition fallback
            best = self._best_samasa_decomposition(piece)
            if best:
                samasa_decompositions.append({
                    "piece": piece, "type_guess": best["type_guess"], "members": best["members"],
                })
                for member in best["members"]:
                    atoms.append({"text": member, "source": "samasa-member",
                                  "confidence": "dictionary-verified"})
            else:
                atoms.append({
                    "text": piece, "source": "sandhi-piece",
                    "confidence": "dictionary-verified" if self._is_dictionary_word(piece) else "unverified",
                })

        return {"input": deva_word, "sandhi_pieces": pieces, "sandhi_rules": sandhi_rules,
                "samasa_decompositions": samasa_decompositions, "atoms": atoms}

    def samasa_of_piece(self, iast_piece):
        """Samāsa analysis of ONE already-isolated IAST word, in the same shape analyze_pada_line puts
        under row["samasa"]: {"type_guess", "type", "members" (Devanagari), "confidence", "stem"} or None.
        (sarga_analyser used to call split_word() for fused tokens and then read ["members"] /
        ["type_guess"], keys split_word() does not return; this is the method it should have been calling.
        Its "type"/"stem"/"members" are also what padakosha_builder turns into the samasa_* JSON fields.)"""
        res = self._classified_samasa(iast_piece)
        if res is None and self._classifier() is False:      # morphology data unavailable: legacy path
            deva_piece = parasavarna_normalize(tl(iast_piece, sanscript.IAST, sanscript.DEVANAGARI))
            return self._best_samasa_decomposition(deva_piece)
        return res

    def split_pada(self, deva_pada):
        """
        Run the pipeline over a whole whitespace-tokenized pāda (or plain
        running text), word by word.
        """
        tokens = [t for t in deva_pada.split() if t]
        return [self.split_word(t) for t in tokens]
# --------------------------------------------------------------------------- #
def _print_result(result):
    print(f"=== {result['input']} ===")
    print(f"  sandhi pieces: {' + '.join(result['sandhi_pieces'])}")
    conf_tags = {"dictionary-verified": "\u2713 dict", "phonology-only": "  phon",
                 "unverified": "  ???"}
    for atom in result["atoms"]:
        tag = "sandhi" if atom["source"] == "sandhi-piece" else "samasa"
        conf = conf_tags.get(atom["confidence"], atom["confidence"])
        print(f"    [{tag:6}] [{conf}]  {atom['text']}")
    print()


def _run_wordlist(cs, path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            word = line.strip().split("||")[0].strip()
            if not word or word.startswith("#"):
                continue
            _print_result(cs.split_word(word))


BUNDLED_CORPUS = os.path.join(HERE, "corpus_64word_ramayana_1.1.1-5.txt")


def _run_test():
    """
    Smoke-test: run the bundled 64-word real-verse corpus through the
    combined pipeline and report counts. This is deliberately NOT a
    graded PASS/FAIL suite against hand-picked "expected" compound
    decompositions -- this project's own source policy (PROJECT_STATE.md:
    "silent inference: not permitted") argues against fabricating
    expected-answer labels for samasa splits that haven't actually been
    checked against a real grammatical authority. What this DOES verify,
    directly by execution: the pipeline runs to completion on every word
    with no exceptions, and reports exactly how many samasa decompositions
    survive the false-positive guards -- so a future change that starts
    silently over- or under-decomposing again is visible by a count
    swing, even without per-word grading.
    """
    cs = CombinedSplitter()
    n_words = 0
    n_samasa_decomposed = 0
    n_dict_verified_atoms = 0
    n_unverified_atoms = 0
    decomposed_words = []

    with open(BUNDLED_CORPUS, encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if not word or word.startswith("#"):
                continue
            n_words += 1
            result = cs.split_word(word)
            samasa_atoms = [a for a in result["atoms"] if a["source"] == "samasa-member"]
            if samasa_atoms:
                n_samasa_decomposed += 1
                decomposed_words.append((word, [a["text"] for a in result["atoms"]]))
            for atom in result["atoms"]:
                if atom["confidence"] == "dictionary-verified":
                    n_dict_verified_atoms += 1
                else:
                    n_unverified_atoms += 1

    print(f"Ran combined pipeline on {n_words} words from {BUNDLED_CORPUS}, no exceptions.")
    print(f"Samasa decomposition fired on {n_samasa_decomposed} word(s):")
    for word, atoms in decomposed_words:
        print(f"    {word}  ->  {' + '.join(atoms)}")
    print(f"Final atom confidence: {n_dict_verified_atoms} dictionary-verified, "
          f"{n_unverified_atoms} unverified.")


def _self_check(quiet=False):
    """
    Internal consistency check, distinct from _run_test's corpus smoke
    test: verifies the specific false-positive guards this pipeline
    relies on are actually firing, on cases found (and fixed) while
    building this pipeline. Returns True/False; prints a report unless
    quiet=True. Not a substitute for _run_test -- this checks the GUARDS
    specifically, by name, so a future refactor that silently disables
    one is caught even if the corpus-level counts happen to look similar.
    """
    cs = CombinedSplitter()
    cases = [
        # (word, must NOT appear as a samasa-member atom text -- i.e. this
        # word must stay atomic, not be wrongly torn apart)
        ("नारदं", "direct dictionary headword (proper noun) must not be torn apart"),
        ("साम्प्रतं", "direct dictionary headword (adverb) must not be torn apart"),
        ("युक्तः", "direct dictionary headword (participle) must not be torn apart"),
        ("विद्वान्", "direct dictionary headword / मतुप्-like form must not be torn apart"),
        ("गुणवान्", "मतुप् possessive form must not be torn apart (looks_like_matup_form guard)"),
        ("वीर्यवान्", "मतुप् possessive form must not be torn apart (looks_like_matup_form guard)"),
        ("आत्मवान्", "मतुप् possessive form must not be torn apart (looks_like_matup_form guard)"),
        ("जितक्रोधो", "product of an UNCONFIRMED sandhi split must not be further decomposed"),
        ("सत्यवाक्यः", "यः (relative pronoun, bare 2-char stem) must not count as a valid compound member"),
        ("चारित्रेण", "guess_samasa_type's own 'NOT a samasa' (particle) label must be a rejection, not a result"),
        ("विष्णुना", "ष्णुना is not a word -- fragments must independently validate, not just via samasa_splitter's loose stem-matcher"),
        ("धैर्येण", "धैर्+येण -- neither fragment is a real word"),
        ("नियतात्मा", "त्मा is not a word"),
        ("अदीनात्मा", "त्मा is not a word"),
        ("इवापरः", "इवा is not a word"),
        ("प्रीत्या", "इत्या is not a word"),
    ]
    # (word, expected members) -- must correctly decompose
    positive_cases = [
        ("मुनिपुङ्गवम्", ["मुनि", "पुङ्गवम्"]),
        ("संयुगे", ["सं", "युगे"]),
    ]

    ok = True
    for word, reason in cases:
        result = cs.split_word(word)
        samasa_texts = [a["text"] for a in result["atoms"] if a["source"] == "samasa-member"]
        if samasa_texts:
            ok = False
            if not quiet:
                print(f"FAIL  {word}: wrongly decomposed into {samasa_texts} -- {reason}")
        elif not quiet:
            print(f"PASS  {word}: stayed atomic -- {reason}")

    for word, expected_members in positive_cases:
        result = cs.split_word(word)
        atoms = [a["text"] for a in result["atoms"]]
        if atoms != expected_members:
            ok = False
            if not quiet:
                print(f"FAIL  {word}: expected {expected_members}, got {atoms}")
        elif not quiet:
            print(f"PASS  {word}: correctly decomposed into {atoms}")

    if not quiet:
        print("RESULT:", "all guard checks passed" if ok else "SOME GUARD CHECKS FAILED")
    return ok


def main():
    parser = argparse.ArgumentParser(
        description="Run sandhi_splitter.py and samasa_splitter.py in tandem "
                     "on a Devanagari word, pada, or wordlist file.")
    parser.add_argument("input", nargs="?", help="A Devanagari word/pada, or a path to a wordlist file")
    parser.add_argument("--scheme", default="devanagari",
                         help="Transliteration scheme of `input` if not Devanagari (iast, wx, ...)")
    parser.add_argument("--sqlite-dict", default=DEFAULT_SQLITE_DICT,
                         help="Path to apte_dictionary.sqlite. Default: the sandhi/ tool's own copy.")
    parser.add_argument("--test", action="store_true",
                         help="Run the bundled 64-word corpus smoke test and the false-positive "
                              "guard self-check, then exit.")
    args = parser.parse_args()

    if args.test:
        _run_test()
        print()
        ok = _self_check()
        sys.exit(0 if ok else 1)

    if not args.input:
        sys.exit("Usage: combined_splitter.py <word_or_pada|wordlist.txt> [--scheme iast]")

    cs = CombinedSplitter(sqlite_dict_path=args.sqlite_dict)

    if os.path.isfile(args.input):
        _run_wordlist(cs, args.input)
        return

    deva_input = args.input
    if args.scheme != "devanagari":
        scheme_obj = getattr(sanscript, args.scheme.upper(), sanscript.IAST)
        deva_input = tl(args.input, scheme_obj, sanscript.DEVANAGARI)

    for result in cs.split_pada(deva_input):
        _print_result(result)


if __name__ == "__main__":
    main()
