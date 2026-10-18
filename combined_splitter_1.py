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


class CombinedSplitter:
    def __init__(self, sqlite_dict_path=DEFAULT_SQLITE_DICT):
        self.sqlite_dict_path = sqlite_dict_path
        self.sp = SamasaSplitter()
        if sqlite_dict_path and os.path.exists(sqlite_dict_path):
            self.sp.load_sqlite_dictionary(sqlite_dict_path)
        self._db_path = sqlite_dict_path

    # ------------------------------------------------------------- utils --
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
            return None
        return {"type_guess": best["type_guess"], "members": best["members"]}

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
        citation = [c.lstrip("'") for c in citation]

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
            deva_citation = parasavarna_normalize(
                tl(citation[i], sanscript.IAST, sanscript.DEVANAGARI))
            samasa = self._best_samasa_decomposition(deva_citation)

            rows.append({
                "word": word, "citation_form": citation[i],
                "sandhi_rule": sandhi_rule, "sandhi_sutra": sandhi_sutra,
                "sandhi_vigraha": sandhi_vigraha, "samasa": samasa,
            })
        return rows

    def split_word(self, deva_word):
        """
        Run the two-tool pipeline on a single continuous Devanagari word
        (may itself be sandhi-fused with a following particle, e.g. a
        whole pāda). Returns:
            {
              "input": deva_word,
              "sandhi_pieces": [...],   # sandhi_splitter.py's own output
              "sandhi_rules": [         # one entry per sandhi_splitter.py step actually used
                  {"rule_id": str, "note": str, "left": str, "right": str}, ...
              ],
              "samasa_decompositions": [   # one entry per piece samasa_splitter.py decomposed
                  {"piece": str, "type_guess": str, "members": [str, ...]}, ...
              ],
              "atoms": [
                  {"text": str, "source": "sandhi-piece"|"samasa-member",
                   "confidence": "dictionary-verified"|"phonology-only"|"unverified"},
                  ...
              ],
            }
        `sandhi_rules`/`samasa_decompositions` are the "sandhi name" /
        "samasa name" + pada-vigraha a report needs; empty lists mean
        "no sandhi happened here" / "not a recognized compound" --
        reported as such, never silently omitted or guessed.
        """
        sandhi_result = sandhi_splitter.split_word_recursive(deva_word)
        pieces = sandhi_result["pieces"]
        sandhi_rules = [
            {"rule_id": step["rule_id"], "note": step["note"],
             "left": step["left"], "right": step["right"]}
            for step in sandhi_result["steps"]
        ]
        samasa_decompositions = []

        # If ANY step sandhi_splitter used to reach these pieces was itself
        # UNCONFIRMED on both sides (`left_confirmed`/`right_confirmed`
        # both False -- i.e. it survived only as the best of an otherwise
        # all-unconfirmed candidate set, not because either side actually
        # validated against the dictionary), don't hand any piece of this
        # word to the samasa layer for further decomposition. Compounding
        # a shaky guess with a SECOND layer of guessing only manufactures
        # more confident-looking noise on top of an already-uncertain
        # split (observed directly: "जितक्रोधो" sandhi-peels, unconfirmed
        # both sides, to "जितक्रः"+"धो"; feeding "जितक्रः" onward then
        # produced an equally-unfounded "जित्"+"अक्रः"). Pieces still get
        # returned, just never decomposed further.
        sandhi_is_shaky = any(
            not step["left_confirmed"] and not step["right_confirmed"]
            for step in sandhi_result["steps"]
        )

        atoms = []
        for piece in pieces:
            if sandhi_is_shaky:
                atoms.append({"text": piece, "source": "sandhi-piece",
                               "confidence": "dictionary-verified" if self._is_dictionary_word(piece)
                               else "unverified (unconfirmed sandhi split)"})
                continue
            if self._is_non_compound_form(piece):
                atoms.append({"text": piece, "source": "sandhi-piece",
                               "confidence": "dictionary-verified" if self._is_dictionary_word(piece)
                               else "unverified (recognized verb/pronoun form)"})
                continue

            # See _best_samasa_decomposition's own docstring for the
            # acceptance rule (dictionary-verified, 2+ members, every
            # member >=3 WX chars) and why it exists -- shared with
            # analyze_pada_line() so both entry points apply it
            # identically.
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

    def split_pada(self, deva_pada):
        """
        Run the pipeline over a whole whitespace-tokenized pāda (or plain
        running text), word by word -- see split_word for the per-word
        pipeline. Returns a list of that function's per-word result dicts,
        one per whitespace-delimited token in `deva_pada`.
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
