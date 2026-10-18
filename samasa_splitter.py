#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
samasa_splitter.py
===================
Rule-based Sanskrit compound (samasa) splitter.

Built on top of the `sandhi` package (Hrishikesh Terdalkar's Python port of
the Samsaadhanii Ashtadhyayi Sandhi engine -- the same sandhi.py you
uploaded, plus its niyama.py rule table and apavaada.py exception table).

HOW IT WORKS
------------
A Sanskrit compound (samasta-pada) is really just two or more independent
words (pratipadikas) that have been fused together, usually with ordinary
sandhi happening at the seam(s) -- e.g.

    kambu + grIvaH        -> kambugrIvaH      (no phonetic change needed)
    ikSvAku + vaMSa + prabhavaH -> ikSvAkuvaMSaprabhavaH

`sandhi.py` only runs *forward* (word1 + word2 -> combined form). This
script builds the *reverse* direction on top of it:

  1. It loads niyama.py's 2,548-row rule table and inverts it into a
     lookup: "if you see this junction pattern, then the pre-sandhi
     ending of word 1 could have been X and the pre-sandhi start of
     word 2 could have been Y".
  2. For every possible cut-point in the input word, it looks up which
     rules could explain the letters straddling that cut, reconstructs
     the two candidate pieces, and then RE-RUNS the original forward
     sandhi.py engine on them. If the forward result matches the input
     word again, the split is certified as phonologically valid.
  3. Optionally, if you supply a wordlist (one stem per line, any
     transliteration scheme -- see --dict), each candidate piece is
     checked against it, and only dictionary-backed splits are kept.
     This step is what actually tells you *which* candidate split is
     the real one, and it also lets the script recurse into 3+ member
     compounds.
  4. A very rough, heuristic-only samasa-TYPE guess (tatpurusha /
     karmadharaya / dvigu / bahuvrihi / avyayibhava / dvandva) is
     attached to each result, based on simple structural cues from the
     Samasah literature (numeral first member -> dvigu, common avyaya
     first member -> avyayibhava, etc). This is NOT authoritative --
     real classification needs meaning, which needs a dictionary with
     glosses, not just a wordlist. Treat it as a starting guess only.

REQUIRES
--------
    pip install sandhi indic_transliteration

USAGE
-----
    python samasa_splitter.py rAjapuruSaH
    python samasa_splitter.py ikSvAkuvaMSaprabhavaH --scheme wx
    python samasa_splitter.py kambugrIvaH --dict my_wordlist.txt
    python samasa_splitter.py            # runs the built-in demo

    As a library:
        from samasa_splitter import SamasaSplitter
        sp = SamasaSplitter(dictionary_path="apte_stems.txt")
        sp.split("ikṣvākuvaṃśaprabhavaḥ", scheme="iast")
"""

import argparse
import re
import sys
from functools import lru_cache

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate as tl
    import sandhi as sandhi_pkg
    from sandhi.niyama import RULES
except ImportError as e:
    sys.exit(
        "Missing dependency: {}\n"
        "Install with:  pip install sandhi indic_transliteration".format(e)
    )

# --------------------------------------------------------------------------- #
# The 22 traditional upasargas (verbal/nominal prefixes) of Sanskrit
# grammar, with their core senses for reference. These are real,
# closed-class morphemes -- unlike an arbitrary short dictionary match,
# a word starting with one of these is reliably a genuine compound-
# forming prefix even at 1-2 characters (e.g. "su-", "vi-", "ā-"), so
# they're treated as always-valid short members rather than filtered
# out by the general min_member_len noise guard (except single-letter
# "ā", excluded below -- see UPASARGA_LEN_EXEMPT). WX forms were
# generated via indic_transliteration, not typed by hand.
#
#   pra   (pra)     forward, forth, most
#   parA  (parā)    away, backward, reversal
#   apa   (apa)     away, off, opposite
#   sam   (sam)     together, with, completely
#   anu   (anu)     after, following, behind
#   ava   (ava)     down, off, away
#   nis   (nis)     out, away, without
#   nir   (nir)     out, forth
#   xus   (dus)     bad, difficult, hard
#   xur   (dur)     hard, faulty, bad
#   vi    (vi)      apart, asunder, distinct
#   A     (ā/āṅ)    near, towards, back
#   ni    (ni)      down, in, into
#   aXi   (adhi)    above, over, on
#   api   (api)     also, proximate, covert
#   awi   (ati)     beyond, across, excess
#   su    (su)      good, well, excellent
#   uw/ux (ut/ud)   up, upwards, high (ud- before voiced sounds)
#   aBi   (abhi)    towards, to, against
#   prawi (prati)   against, back, towards
#   pari  (pari)    around, about, round
#   upa   (upa)     near, towards, secondary
# --------------------------------------------------------------------------- #
UPASARGA_WX = {
    "pra", "parA", "apa", "sam", "anu", "ava", "nis", "nir", "xus", "xur",
    "vi", "A", "ni", "aXi", "api", "awi", "su", "uw", "ux", "aBi", "prawi",
    "pari", "upa",
}
# The nañ (negative) prefix -- "a-" before a consonant-initial word,
# "an-" before a vowel-initial one (e.g. "an" + "asUyakaH" -> "anasUyakaH",
# "not envious"). This is NOT one of the 22 upasargas (those attach only
# to verb roots to form derived stems; nañ attaches to nominal stems to
# form a NAÑ-TATPURUSA, a distinct compound type) but it is exactly as
# closed-class and unambiguous as an upasarga -- there are only these two
# allomorphs, in strict complementary distribution by the following
# sound -- so it gets the same min-length exemption treatment (see
# CLOSED_CLASS_LEN_EXEMPT below), restricted the same way to the true
# start of the word (depth 0 / idx 0), never mid-recursion.
NAN_PREFIX_WX = {"a", "an"}
# A few more avyayas (indeclinables) commonly seen as compound first
# members, beyond the 22 upasargas proper -- kept separate since they
# aren't upasargas in the technical sense (e.g. negation, comparison
# particles). Used only for the best-effort samasa-type heuristic in
# guess_samasa_type(), not for the min-length exemption above.
COMMON_AVYAYA_PREFIXES = UPASARGA_WX | NAN_PREFIX_WX | {
    "sa", "yaWA", "yAvaw", "xuH",
}
NUMERAL_PREFIXES = {
    "eka", "xvi", "wri", "cawur", "paYca", "SaS", "sapwa", "aSta", "nava",
    "xaSa",  # WX forms of eka/dvi/tri/catur/pancha/shash/sapta/ashta/nava/dasha
}


# --------------------------------------------------------------------------- #
# Common Sanskrit indeclinable PARTICLES (avyaya) -- ca "and", vā "or",
# tu "but", hi "indeed/for", eva "only/indeed", api "even/also",
# ha/sma (emphatic), nu "now/indeed", cit/svit (indefinite markers).
#
# These are NOT upasargas (they don't attach to verb roots to form
# derived stems) and NOT samasa members (a particle doesn't semantically
# combine with the next word into a compound) -- they are ordinary
# separate WORDS that simply, very commonly, get sandhi-joined onto the
# following word with no printed space between them in running verse
# (e.g. "ca" + "etat" -> "caitat", "ca" + "eva" -> "caiva"). Splitting
# these apart is genuinely a SANDHI restoration, not a samasa split, even
# though the mechanics (reverse-index + dictionary check) are identical.
# Kept separate from UPASARGA_WX so guess_samasa_type() and the corpus
# pipeline can correctly label a "ca-" split as sandhi, not tatpurusa.
# --------------------------------------------------------------------------- #
SANDHI_PARTICLE_WX = {
    "ca", "vA", "wu", "hi", "ha", "sma", "nu", "ciw", "sviw", "cana",
}

# --------------------------------------------------------------------------- #
# Core personal/demonstrative pronoun paradigm (asmad "I", yuṣmad "you",
# tad "he/she/it/that") in WX. Pronouns are a small, closed, extremely
# high-frequency word class in Sanskrit narrative, but their case forms
# are largely SUPPLETIVE (tvayā doesn't derive from any stem+ending rule
# the way a regular noun does), so no general stem-restoration heuristic
# can find them the way _stem_candidates() finds "buddhimat" from
# "buddhimān". Dictionary coverage of these forms is also inconsistent
# (MW happens to list "mayā"/"tena" but not "tvayā"/"tayā"). Listed here
# so the whole-word gate in analyze_verse_corpus() can recognize them
# directly and correctly refuse a spurious particle-led split (e.g.
# "tvayā" is NOT "tu" + "ayā").
# --------------------------------------------------------------------------- #
PRONOUN_FORMS_WX = {
    "AvAByAm", "AvAm", "aham", "asmABiH", "asmAkam", "asmAn", "asmAsu",
    "asmAw", "mAm", "mahyam", "mama", "maw", "mayA", "me", "nO", "sA",
    "saH", "vAm", "vayam", "wAByAm", "wAH", "wAM", "wAn", "wAni", "wAsAm",
    "wAsu", "wEH", "wO", "waM", "wasmAw", "wasmE", "wasyAH", "wasyE",
    "wasya", "wava", "waw", "wayA", "we", "weRAm", "weRu", "wena",
    "wuByam", "wvAm", "wvam", "wvaw", "wvayA", "yUyam", "yuRmABiH",
    "yuRmAkam", "yuRmAn", "yuRmAsu", "yuRmAw", "yuvAByAm", "yuvAm",
}


# --------------------------------------------------------------------------- #
# Declension-suffix restoration table: (printed_suffix, lemma_suffix,
# needs_ext_sandhi_flag, gloss). CDSL dictionaries list citation-form
# STEMS (pratipadikas), e.g. "rAma", not inflected forms like "rAmaH",
# so before giving up on a dictionary lookup, _stem_candidates() strips
# each printed_suffix it finds and reattaches the corresponding
# lemma_suffix, i.e. lemma = word[:-len(printed_suffix)] + lemma_suffix.
# This is a heuristic table, not a real declension engine -- it covers
# the common patterns seen in this corpus, not every Sanskrit ending.
#
# needs_ext_sandhi_flag marks restorations that are ONLY valid for a
# compound's FINAL member (checked with allow_ext_visarga_o=True) --
# "-o"/"-r" only ever arise from EXTERNAL visarga sandhi with whatever
# followed in the original running text, so allowing them when judging
# whether a token is already, as printed, a complete citation form would
# let something like "ko" falsely "validate" via a restoration that
# itself proves sandhi already happened (see is_len_exempt_particle()).
# --------------------------------------------------------------------------- #
DECLENSION_SUFFIXES = [
    # (printed_suffix, lemma_suffix, needs_ext_sandhi_flag, gloss)
    ("o",  "aH", True,  "ext. visarga sandhi before voiced sound: ko -> kaH"),
    ("r",  "H",  True,  "ext. visarga sandhi before vowel: jatrur -> jatruH"),
    ("H",  "",   False, "visarga stem: rAmaH -> rAma, maweH -> mawi"),
    ("M",  "",   False, "anusvara-shifted ending"),
    ("m",  "",   False, "neuter -am -> -a: vanam -> vana"),
    ("a",  "an", False, "neuter n-stem: nAma -> nAman"),
    ("A",  "an", False, "masc n-stem: rAjA -> rAjan, AwmA -> Awman"),
    ("A",  "a",  False, "feminine adjective agreement (long -A replacing "
                        "the masc/neut short -a of the base stem): "
                        "saMpannA -> saMpanna"),
    ("I",  "in", False, "masc -in stem: vAgmI -> vAgmin, balI -> balin"),
    ("An", "aw", False, "-mat/-vat stem nom.sg: buxXimAn -> buxXimaw"),
    ("An", "a", False, "accusative plural, a-stem masc (the other, much "
                       "more common, source of a final -An -- distinct "
                       "from the -mat/-vat row above): "
                       "naran -> nara, saMBArAn -> saMBAra"),
    ("AH", "as", False, "masc/fem -as stem nom.sg, agreement-lengthened "
                         "(e.g. bahuvrIhi): pInavakzAH -> pInavakzas"),
    ("aH", "as", False, "neut -as stem nom/acc.sg (unlengthened): "
                        "manaH -> manas, wapaH -> wapas"),
    ("e", "a", False, "locative singular, a-stem masc/neut (direct case "
                      "ending, NOT visarga-derived like the o/e->aH row "
                      "above): vane -> vana, gAmBIrye -> gAmBIrya"),
    ("eNa", "a", False, "instrumental singular, a-stem, retroflex Na "
                        "(natva after r/z earlier in the word): "
                        "XEryeNa -> XErya"),
    ("ena", "a", False, "instrumental singular, a-stem, plain dental: "
                        "xevena -> xeva"),
    ("yAH", "I", False, "genitive/ablative singular of an I-stem fem "
                        "noun (glide -y- + AH): nadyAH -> nadI, "
                        "kEkeyyAH -> kEkeyI"),
    ("NAm", "", False, "genitive plural of an I/U-stem fem noun, "
                       "retroflexed after r/z earlier in the word "
                       "(the I is already present before this suffix): "
                       "nArINAm -> nArI"),
    ("nAm", "", False, "genitive plural of an I/U-stem fem noun, "
                       "plain dental (the I is already present before "
                       "this suffix): nadInAm -> nadI"),
    ("AnAm", "a", False, "genitive plural, a-stem masc/neut (the most "
                         "common noun class): xevAnAm -> xeva"),
    ("xBiH", "w", False, "instrumental plural of an -ant/-at (present "
                         "participle) stem, t+bhiH assimilated to "
                         "dbhiH: saxBiH -> saw (sat)"),
    ("EH", "a", False, "instrumental plural, a-stem masc/neut: "
                       "xevEH -> xeva, guNEH -> guNa"),
    ("Aw", "a", False, "ablative singular, a-stem masc/neut: "
                       "xevAw -> xeva, vacanAw -> vacana"),
    ("x", "w", False, "final consonant d, voiced by external sandhi "
                      "before a following voiced sound, restored to "
                      "citation -t (this fires broadly across whatever "
                      "case ending the word actually has, e.g. ablative "
                      "-At -> -Ax before a voiced initial): "
                      "vacanAx -> vacanAw"),
    ("BiH", "", False, "instrumental plural, generic -- attaches "
                       "directly after a stem-final vowel with no "
                       "further change (u/i-stem etc.): "
                       "sinXuBiH -> sinXu"),
    ("unA", "u", False, "instrumental singular, u-stem masc/neut: "
                        "viRNunA -> viRNu, gurunA -> guru"),
]

# --------------------------------------------------------------------------- #
# Verb-conjugation ending recognition. Unlike DECLENSION_SUFFIXES, this
# table does NOT try to reconstruct a dictionary lemma -- Sanskrit verb
# roots undergo reduplication (paripapraccha), internal ablaut/vowel
# change (bhI -> biBy-), and augment prefixing (a-bravIt) that a simple
# suffix-strip can't reverse the way stripping a case ending reliably
# yields a real nominal stem. MW/Apte mostly index only the bare root
# anyway (root "prach" for the whole perfect-tense family built on it),
# so resolving all the way to a dictionary hit isn't the goal here.
#
# What this table IS for: recognizing that a token ends in a
# distinctive, low-ambiguity finite-verb/gerund/infinitive pattern, so
# the whole-word gate can trust "this is an inflected verb form" and
# skip attempting a particle/samasa decomposition on it at all -- e.g.
# "buddhvā" (root budh + gerund -tvā, sandhi-assimilated to "-dhvā")
# was previously mis-accepted as the "samasa" budh + dhvā; recognizing
# the "-dhvā" gerund ending directly stops that. Endings are kept
# reasonably long/distinctive on purpose (no bare "-ta"/"-at"/"-an" --
# those collide constantly with ordinary nominal endings, same
# promiscuity problem as the single-letter upasarga/particle cases).
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# WX aspirate -> unaspirated-counterpart map, needed for reduplicated
# perfect-tense detection (see looks_like_upasarga_verb): Sanskrit's
# reduplication rule deaspirates the copied consonant, so root "prach"
# (WX "praC") surfaces in its own reduplicated perfect as "pa-prac-cha"
# (WX "paprac Ca") -- the "C" of the root shows up as plain "c" in the
# duplicated copy. Searching for the root's DEASPIRATED form is what
# actually finds it in the surface text.
# --------------------------------------------------------------------------- #
ASPIRATE_TO_PLAIN_WX = {
    "K": "k", "G": "g", "C": "c", "J": "j", "T": "t",
    "D": "d", "W": "w", "X": "x", "P": "p", "B": "b",
}

VERB_ENDING_SUFFIXES_WX = {
    # present indicative (thematic + a few athematic), active & middle
    "awi", "anwi", "Ami", "Amy", "asi", "asy", "awe", "anwe",
    # future
    "iRyawi", "syawi", "iRyAmi", "syAmi",
    # imperfect / aorist 3rd singular
    "Iw",
    # gerund (ktvA), including common sandhi-assimilated spellings
    "wvA", "kwvA", "iwvA", "XvA", "wwvA",
    # infinitive
    "wum", "iwum",
    # passive present / passive imperative
    "yawe", "yawAm",
    # optative
    "eyam",
}

# --------------------------------------------------------------------------- #
# kRt-pratyaya (primary derivational suffix) table for the two endings
# seen most often in this corpus: tumun (infinitive) and ktvA (gerund).
# Unlike VERB_ENDING_SUFFIXES_WX above (which only recognizes a pattern
# to avoid mis-splitting it), this table is for ACTUALLY resolving
# root + pratyaya -- see resolve_pratyaya(). Each entry is
# (suffix, pratyaya_name, gloss); the root is whatever's left after
# stripping the suffix, verified against verb_roots (built from MW's
# cl.N. markers -- see build_verb_roots_from_cdsl), not the general
# dictionary, so a hit here means "this really is a known verbal root
# forming this pratyaya", not a coincidental short match.
# --------------------------------------------------------------------------- #
PRATYAYA_SUFFIXES = [
    ("wum", "tumun", "infinitive: 'to (do/be) ...'"),
    ("Xum", "tumun", "infinitive, root-final aspirate assimilated the -t- (buX -> boXXum)"),
    ("wvA", "ktvA", "gerund: 'having (done/been) ...'"),
    ("XvA", "ktvA", "gerund, root-final aspirate assimilated the -t- (buX -> buXXvA)"),
]

# matup pratyaya (मतुप्): a NOMINAL possessive suffix -- noun + vat/mat ->
# "possessing/having <noun>" -- e.g. pratApa ("splendor") + vat ->
# pratApavat, nom. sg. masc. pratApavAn ("possessing splendor"). This is
# NOT a compound (samasa) at all, even though the samasa engine can
# occasionally force a phonologically-valid two-piece split of one of
# these words that happens to pass dictionary validation on both halves
# by coincidence (e.g. "pratApavAn" wrongly torn into "prata"+"apavAn",
# both rare-but-real independent MW headwords) -- see looks_like_matup_
# form()/resolve_matup(), which stop this the same way looks_like_verb_
# form() stops an inflected verb from being wrongly compound-split.
# Only the nominative singular masculine forms are covered here (the
# two allomorphs -vAn/-mAn); other case/gender/number forms of the same
# suffix (vati, vatI, vantam, ...) are not yet recognized.
MATUP_SUFFIXES_WX = [
    ("vAn", "vat", "matup pratyaya (possessive): 'possessing/having ~'"),
    ("mAn", "mat", "matup pratyaya (possessive): 'possessing/having ~'"),
    # "-vAF"/"-mAF" (WX "F" = ñ): the same nom.sg.masc. ending, but with
    # its final n assimilated to the homorganic nasal ñ before a
    # following palatal-initial word (e.g. "lakSmIvAn" + "SuBa..." ->
    # "lakSmIvAY SuBa..."). Recognizing this spelling directly here is
    # simpler than requiring the sandhi-restoration engine to reverse it
    # first, since that engine's forward oracle only ever reproduces the
    # fully-fused internal-sandhi form (with an inserted tuk-augment
    # consonant) and never this plain nasal-assimilation-only spelling
    # that GRETIL's pada-by-pada printing convention actually uses.
    ("vAF", "vat", "matup pratyaya (possessive): 'possessing/having ~'"),
    ("mAF", "mat", "matup pratyaya (possessive): 'possessing/having ~'"),
]


class SamasaSplitter:
    def __init__(self, dictionary_path=None, dict_scheme=sanscript.IAST,
                 max_depth=3, min_member_len=3):
        self.S = sandhi_pkg.Sandhi()
        self.reverse_index = self._build_reverse_index()
        self.max_depth = max_depth
        self.min_member_len = min_member_len
        self._split_cache = {}
        self._recursive_cache = {}
        self.dictionary = None
        self.verb_roots = None
        self.proper_nouns = None
        self.glosses = None
        self.compound_headwords = None
        if dictionary_path:
            self.dictionary = self._load_dictionary(dictionary_path, dict_scheme)

    # ---------------------------------------------------------- setup ----
    @staticmethod
    def _build_reverse_index():
        """Invert niyama.RULES: junction-result-string -> [(lf, sf, type, sutra)]"""
        idx = {}
        for row in RULES:
            parts = row.replace('"', "").split(",")
            if len(parts) < 5:
                continue
            lf, sf, result, styp, sutra = parts[0], parts[1], parts[2], parts[3], parts[4]
            for variant in result.split("/"):
                variant = variant.strip()
                if variant:
                    idx.setdefault(variant, []).append((lf, sf, styp, sutra))
        return idx

    def _load_dictionary(self, path, scheme):
        """Load a plain wordlist (one stem per line) and store WX-normalised forms."""
        words = set()
        with open(path, encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if not w or w.startswith("#"):
                    continue
                words.add(tl(w, scheme, sanscript.WX))
        return words

    @staticmethod
    def build_dictionary_from_cdsl(paths, key_tag="k1"):
        """
        Parse one or more raw CDSL source files (e.g. Monier-Williams' mw.txt,
        Apte's ap90.txt from sanskrit-lexicon/csl-orig) and return a set of
        WX-encoded headword stems.

        CDSL source files mark each entry as:
            <L>123<pc>1,1<k1>HEADWORD<k2>...<e>...
            ... gloss text ...
            <LEND>
        The <k1> field is the clean lookup key. Crucially, CDSL headwords are
        encoded in SLP1, not WX -- this function does that conversion.
        """
        pat = re.compile(r"<{0}>([^<]+)<k2>".format(key_tag))
        stems_slp1 = set()
        for path in paths:
            with open(path, encoding="utf-8") as f:
                data = f.read()
            stems_slp1.update(pat.findall(data))
        return {tl(w, sanscript.SLP1, sanscript.WX) for w in stems_slp1}

    @staticmethod
    def build_compound_headwords_from_cdsl(paths, key_tag="k1"):
        """
        Parse raw CDSL source files and return the subset of WX-encoded
        headwords that MW/Apte's OWN citation form marks as a genuine
        lexicalized COMPOUND -- as opposed to a monomorphemic word or one
        with unrelated internal (taddhita/root) etymology.

        The <k2> field (distinct from <k1>, the bare lookup key) is
        CDSL's etymologically-segmented citation spelling, and it uses
        TWO VISUALLY DIFFERENT DASH CHARACTERS with different meanings,
        confirmed by direct inspection of the source files:
          - em dash "\u2014" (2+ bytes, U+2014): marks a genuine SAMASA
            boundary between two independent word-members, e.g.
            "Darma\u2014jYa" (dharmajYa), "muni\u2014puMgava" (munipuMgava)
          - plain hyphen "-" (U+002D), or no dash at all: marks ordinary
            etymology that ISN'T a compound reading -- a taddhita/kRt
            suffix boundary (e.g. "ut-tama", ut + the superlative suffix
            -tama, NOT the upasarga "ut" + a separate word "tama"), or a
            ROOT+PREFIX boundary that dictionaries segment for etymology
            but tradition doesn't treat as samasa (e.g. "ny-Asa", ni +
            \u221a as, NOT the word "ni" + a separate word "Asa"); or
            simply a bare monomorphemic headword like "vIra" or "suKa"
            with no internal segmentation shown at all.

        This is the key signal that separates a WORD THE DICTIONARY
        ITSELF DOCUMENTS AS COMPOUND (where showing the samasa-vigraha
        is genuinely correct, e.g. dharmajYa, munipuMgava) from a WORD
        THAT MERELY HAS A COINCIDENTAL PHONOLOGICAL CUT POINT surviving
        the samasa engine's own dictionary validation on both pieces in
        total isolation from each other (e.g. "vIraH" wrongly torn into
        "vi"+"IraH" -- "vi" and "IraH" are each independently real
        headwords, but MW's own entry for "vIra" shows no compound
        structure at all: it's simply a monomorphemic word). See its use
        in analyze_verse_corpus, where a token whose whole-word reading
        is dictionary-backed but NOT in this set suppresses every
        multi-member samasa candidate outright, rather than needing a
        much narrower per-case exemption (as the is_sandhi_particle-only
        check previously did).
        """
        entry_pat = re.compile(r"^<L>\d+<pc>[^<]*<{0}>([^<]+)<k2>([^<]*)".format(key_tag))
        compound_slp1 = set()
        for path in paths:
            with open(path, encoding="utf-8") as f:
                data = f.read()
            for entry in re.split(r"(?=<L>)", data):
                m = entry_pat.match(entry)
                if not m:
                    continue
                headword, k2 = m.group(1), m.group(2)
                if "\u2014" in k2:
                    compound_slp1.add(headword)
        return {tl(w, sanscript.SLP1, sanscript.WX) for w in compound_slp1}

    def load_compound_headwords(self, paths):
        """Convenience: point this at mw.txt / ap90.txt to populate
        self.compound_headwords."""
        self.compound_headwords = self.build_compound_headwords_from_cdsl(paths)
        return len(self.compound_headwords)

    @staticmethod
    def build_verb_roots_from_cdsl(paths, key_tag="k1"):
        """
        Parse raw CDSL source files and return a set of WX-encoded verb
        ROOTS specifically (not the whole headword list). MW marks a
        root entry with a conjugation-class tag right after the headword
        -- e.g. "jYA ... <ab>cl.</ab> 9. <ab>P.</ab> <ab>Ā.</ab> jAnA/ti"
        -- which only ever appears on a dhatu (verbal root) entry, never
        an ordinary noun/adjective. Scanning for that tag in a short
        window after each headword gives a real root list, not just
        "any short dictionary match", which is what makes proper
        pratyaya resolution (see PRATYAYA_SUFFIXES/resolve_pratyaya)
        trustworthy rather than another source of coincidental noise.
        """
        entry_pat = re.compile(r"^<L>\d+<pc>[^<]*<{0}>([^<]+)<k2>".format(key_tag))
        roots_slp1 = set()
        for path in paths:
            with open(path, encoding="utf-8") as f:
                data = f.read()
            for entry in re.split(r"(?=<L>)", data):
                m = entry_pat.match(entry)
                if not m:
                    continue
                window = entry[:300]
                if "<ab>cl.</ab>" in window:
                    roots_slp1.add(m.group(1))
        return {tl(w, sanscript.SLP1, sanscript.WX) for w in roots_slp1}

    def load_verb_roots(self, paths):
        """Convenience: point this at mw.txt (Apte's ap90.txt doesn't use
        the same cl.N. markup) to populate self.verb_roots."""
        self.verb_roots = self.build_verb_roots_from_cdsl(paths)
        return len(self.verb_roots)

    @staticmethod
    def build_proper_nouns_from_cdsl(paths, key_tag="k1"):
        """
        Parse raw CDSL source files and return a set of WX-encoded
        PROPER-NOUN-ONLY headwords -- entries whose primary/only sense is
        "N. of a river/person/place/..." (MW's standard "Name of" tag).
        Used to DEPRIORITIZE, not exclude, a samasa candidate: a rare
        proper noun coincidentally matching part of a word (e.g. "vAgu",
        the name of a river mentioned once in one text) is a much less
        likely explanation than an ordinary word, when both are
        otherwise tied -- but genuine compounds DO sometimes legitimately
        contain proper nouns (place names, deity names), so this is
        never used to reject a candidate outright, only to rank it
        behind an equally-valid non-proper-noun alternative.

        A headword can have several <L> entries (homonyms/sub-senses,
        e.g. common words like "jIva" or "loka" run to a dozen-plus
        entries covering ordinary senses PLUS one incidental "N. of a
        place" sub-sense) -- checking any single entry in isolation
        would wrongly tag the whole (extremely common, ordinary) word
        as proper-noun-only. This requires EVERY entry sharing a
        headword to carry the "N. of" tag before the word counts --
        i.e. a word is only flagged when a proper noun is its ONLY
        attested sense, not merely one of several.

        MW also has a common ELLIPTICAL-CONTINUATION convention this
        must account for: when a headword has multiple "N. of ..."
        senses (a common person/place name shared by several distinct
        referents), only the FIRST repeats the headword and the literal
        "N." tag -- subsequent entries just continue with a bare
        "¦ of ..."/"¦ also ..." with no restated headword span and no
        repeated "N." tag at all, e.g. vAlmIki's second sense is simply
        "¦ of a son of Garuḍa", inheriting "N." from its first sense
        ("N. of the celebrated author..."). Checking each entry in
        strict isolation misses this and wrongly excludes such
        headwords entirely. Since same-headword <L> entries always
        appear consecutively in the source, an entry whose body (after
        its <L> header line) starts directly with "¦" -- i.e. skips the
        usual "<s>headword</s> ¦ ..." restatement -- inherits its
        name-status from the immediately preceding entry for the SAME
        headword, whatever that status was (so a non-name headword's
        elliptical continuations correctly stay non-name too).
        """
        entry_pat = re.compile(r"^<L>\d+<pc>[^<]*<{0}>([^<]+)<k2>".format(key_tag))
        total_entries = {}   # headword -> count of <L> entries seen
        name_entries = {}    # headword -> count of those tagged "N. of"
        last_was_name = {}   # headword -> name-status of its most recent entry
        for path in paths:
            with open(path, encoding="utf-8") as f:
                data = f.read()
            for entry in re.split(r"(?=<L>)", data):
                m = entry_pat.match(entry)
                if not m:
                    continue
                headword = m.group(1)
                total_entries[headword] = total_entries.get(headword, 0) + 1
                is_name = "<ab>N.</ab> of" in entry[:250]
                if not is_name:
                    body = entry.split("\n", 1)[1] if "\n" in entry else ""
                    if body.lstrip().startswith("\u00a6") and last_was_name.get(headword):
                        is_name = True
                if is_name:
                    name_entries[headword] = name_entries.get(headword, 0) + 1
                last_was_name[headword] = is_name
        names_slp1 = {w for w, total in total_entries.items()
                      if name_entries.get(w, 0) == total}
        return {tl(w, sanscript.SLP1, sanscript.WX) for w in names_slp1}

    @staticmethod
    def build_glosses_from_cdsl(paths, key_tag="k1", max_len=100):
        """
        Parse raw CDSL source files and return {WX_headword: short English
        gloss} -- one short definition snippet per headword, taken from
        its FIRST <L> entry only (a word's first-listed sense is usually
        its most common one; later homonym senses are skipped here since
        this is meant for a quick "what does this word mean" column, not
        a full dictionary lookup). Only the first file's first match for
        a headword is kept if the same headword appears in more than one
        source file.

        The raw entry text mixes real prose with a lot of CDSL markup
        (<lex>, <ab>, <s1>, <ls>, ...); this strips all of it, drops the
        leading "¦" separator MW/Apte use between headword and
        definition, and truncates to `max_len` characters at a word
        boundary so the result is short enough for a spreadsheet cell.
        """
        entry_pat = re.compile(r"^<L>\d+<pc>[^<]*<{0}>([^<]+)<k2>".format(key_tag))
        glosses = {}
        for path in paths:
            with open(path, encoding="utf-8") as f:
                data = f.read()
            for entry in re.split(r"(?=<L>)", data):
                m = entry_pat.match(entry)
                if not m:
                    continue
                headword = m.group(1)
                if headword in glosses:
                    continue
                body = entry.split("\n", 1)[1] if "\n" in entry else ""
                text = re.sub(r"<[^>]+>", "", body)
                text = text.lstrip("\u00a6").strip()
                text = re.sub(r"\s+", " ", text)
                if len(text) > max_len:
                    text = text[:max_len].rsplit(" ", 1)[0] + "..."
                if text:
                    glosses[headword] = text
        return {tl(w, sanscript.SLP1, sanscript.WX): g for w, g in glosses.items()}

    def load_glosses(self, paths):
        """Convenience: point this at mw.txt / ap90.txt to populate self.glosses."""
        self.glosses = self.build_glosses_from_cdsl(paths)
        return len(self.glosses)


    def load_proper_nouns(self, paths):
        """Convenience: point this at mw.txt to populate self.proper_nouns."""
        self.proper_nouns = self.build_proper_nouns_from_cdsl(paths)
        return len(self.proper_nouns)

    def load_cdsl_dictionaries(self, paths):
        """Convenience: point this at mw.txt / ap90.txt (or both) directly."""
        self.dictionary = self.build_dictionary_from_cdsl(paths)
        return len(self.dictionary)

    @staticmethod
    def build_dictionary_from_sqlite(db_path):
        """
        Load the ``stems`` table of the sibling `sandhi/` tool's own
        verified dictionary (`apte_dictionary.sqlite`, SKD+Apte combined,
        107,190 stem rows) and return a set of WX-encoded stems.

        This is the SAME database `sandhi_splitter.py`'s `dictionary_lookup`
        queries -- reusing it (rather than requiring a separate plain
        wordlist or raw CDSL parse) is what lets this tool and
        `sandhi_splitter.py` agree on what counts as a real word, instead
        of validating candidates against two different, independently-
        assembled dictionaries. `stems.stem` is already SLP1-encoded (see
        `sandhi/sandhi_splitter.py`'s `dictionary_lookup` docstring/query);
        this only does the SLP1->WX conversion this class's internal
        `_in_dictionary` check needs.
        """
        import sqlite3
        conn = sqlite3.connect(db_path)
        try:
            rows = conn.execute("SELECT DISTINCT stem FROM stems").fetchall()
        finally:
            conn.close()
        return {tl(stem, sanscript.SLP1, sanscript.WX) for (stem,) in rows if stem}

    def load_sqlite_dictionary(self, db_path):
        """Convenience: point this at `apte_dictionary.sqlite` to populate
        self.dictionary from the shared sandhi/samasa dictionary."""
        self.dictionary = self.build_dictionary_from_sqlite(db_path)
        return len(self.dictionary)

    # -------------------------------------------------------- helpers ----
    def _to_wx(self, word, scheme):
        return tl(word, scheme, sanscript.WX)

    def _from_wx(self, wx, scheme):
        return tl(wx, sanscript.WX, scheme)

    def _stem_candidates(self, wx_word, allow_ext_visarga_o=True):
        """
        Try each entry in DECLENSION_SUFFIXES against wx_word and return
        every lemma reconstruction that results -- see that table for the
        actual restoration rules and why allow_ext_visarga_o gates some
        of them. This is a heuristic, not a real declension engine -- it
        will miss some consonant-stem and irregular forms.
        """
        variants = {wx_word}
        for _ in range(2):
            new = set()
            for v in variants:
                for (printed_suf, lemma_suf, needs_ext, _gloss) in DECLENSION_SUFFIXES:
                    if needs_ext and not allow_ext_visarga_o:
                        continue
                    if v.endswith(printed_suf) and len(v) > len(printed_suf):
                        new.add(v[:-len(printed_suf)] + lemma_suf)
            variants |= new
        return variants

    def _in_dictionary(self, stem_wx, allow_ext_visarga_o=True):
        if stem_wx in PRONOUN_FORMS_WX:
            return True
        if self.dictionary is None:
            return None  # unknown -- no dictionary loaded
        for cand in self._stem_candidates(stem_wx, allow_ext_visarga_o=allow_ext_visarga_o):
            if cand in self.dictionary:
                return True
        return False

    # Process-wide cache for the third-party `sandhi` package's forward
    # oracle (self.S._wx_sandhi), keyed by (left, right) -- NOT per-word
    # like _split_cache below, because the same short (left, right) pair
    # (a common particle boundary like "ca"+something, or a repeated
    # word-final/initial fragment) recurs constantly across a real verse
    # corpus. Found necessary by direct profiling while scaling this
    # pipeline from one sarga (880 words) to the full Ramayana (~18,761
    # verses, ~200K+ words): cProfile showed _wx_sandhi's OWN regex
    # compilation (re._compile, not this project's code) dominating
    # runtime -- 4.3 million re.search calls for just 15 words, ~85% of
    # total wall time -- because sandhi.py itself never caches a compiled
    # pattern across calls. _wx_sandhi is a pure function of its two
    # string arguments (no side effects, verified by reading sandhi.py),
    # so memoizing it here is safe and doesn't touch third-party code.
    _WX_SANDHI_CACHE = {}

    def _cached_wx_sandhi(self, left, right):
        key = (left, right)
        cached = self._WX_SANDHI_CACHE.get(key)
        if cached is not None:
            return cached
        try:
            result = self.S._wx_sandhi(left, right)
        except Exception:
            result = ("__EXCEPTION__",)
        self._WX_SANDHI_CACHE[key] = result
        return result

    # -------------------------------------------------- candidate gen -----
    def _candidate_two_way_splits(self, wx_word):
        """
        Return every phonologically-valid 2-way split of a WX-encoded word,
        as (left_wx, right_wx, sandhi_type, sutra, prior_sandhi_occurred).
        Verified by re-running forward sandhi and matching the input word.
        """
        cached = self._split_cache.get(wx_word)
        if cached is not None:
            return cached

        n = len(wx_word)
        # Cheap first pass: only consider junction patterns that actually
        # occur as a substring somewhere in this word at all -- this prunes
        # the ~1400-entry rule index down to a handful before we do any of
        # the expensive position-alignment / forward-sandhi verification.
        relevant_keys = [k for k in self.reverse_index if k and k in wx_word]
        relevant_keys.sort(key=len, reverse=True)

        found = []
        seen = set()

        for key in relevant_keys:
            klen = len(key)
            start = wx_word.find(key)
            while start != -1:
                for (lf, sf, styp, sutra) in self.reverse_index[key]:
                    left = wx_word[:start] + lf
                    right = sf + wx_word[start + klen:]
                    if not left or not right:
                        continue
                    sig = (left, right, styp, sutra)
                    if sig in seen:
                        continue
                    seen.add(sig)
                    out = self._cached_wx_sandhi(left, right)
                    if out == ("__EXCEPTION__",):
                        continue
                    # Some valid forward outputs keep the pieces as two
                    # separate words (embedded spaces) rather than a
                    # single fused string -- e.g. an OPTIONAL-retention
                    # apavaada rule like "vā śari" can output
                    # "wapaH  svAXyAyanirawaM" (note the double space)
                    # as one legitimate answer alongside a fused one.
                    # Comparing against wx_word (which has no spaces at
                    # all) needs the same space-stripping here as
                    # everywhere else this comparison is made.
                    forms = [f.replace(" ", "") for f in
                             (out[0].split(":") if out and out[0] else [])]
                    if wx_word in forms:
                        found.append((left, right, styp, sutra,
                                      styp != "varNamelana"))
                start = wx_word.find(key, start + 1)

        # Supplementary pass: compound-internal linking nasal. Some
        # compounds insert an anusvara/homorganic nasal between members
        # purely as a junction convention (e.g. "ari"+"damaH" ->
        # "ariMxamaH") that isn't a phonological SANDHI rule at all --
        # niyama.py's rule table has no entry for it, so it's handled
        # separately: at every 'M' immediately before a voiced stop,
        # propose a split that treats the 'M' as the inserted linking
        # sound belonging to neither member.
        STOPS = set("kKgGcCjJwWqQwWxXtTdDpPB")
        for i, ch in enumerate(wx_word):
            if ch == "M" and 0 < i < len(wx_word) - 1 and wx_word[i + 1] in STOPS:
                left = wx_word[:i]
                right = wx_word[i + 1:]
                sig = (left, right, "sandhi-augment", "")
                if sig not in seen and left and right:
                    seen.add(sig)
                    found.append((left, right, "sandhi-augment (linking nasal)", "", False))

        # Supplementary pass: "no visible change happened here" junctions
        # that are grammatically valid ONLY via an APAVAADA (exception)
        # rule, not the general niyama.py table -- e.g. visarga retained
        # unchanged before a sibilant ("tapaḥ svādhyāya" staying as-is is
        # the "vā śari" OPTIONAL retention rule) lives entirely inside
        # apavaada.py's exception logic. The reverse-index above is built
        # only from niyama.RULES, so it can never even propose this
        # split as a candidate to verify.
        #
        # Deliberately narrow: this checks EVERY position, but the
        # forward engine's fallback ALWAYS trivially reproduces a plain
        # concatenation when no rule applies at all (see sandhi.py's
        # `else: result = [f"{first}{second}", ...]`), so a blanket
        # "does the forward call reproduce wx_word" check would accept
        # a no-sandhi-justification candidate at literally every
        # position in every word -- tried and confirmed this flooded
        # the dictionary-guided ranking with coincidental noise
        # (jīva+lokasya losing to jīvalā+ukasya, etc.). Restricting to
        # the specific H+sibilant pattern targets only the real
        # apavaada-only phenomenon this was meant to catch.
        for i in range(self.min_member_len, n - self.min_member_len + 1):
            if not (wx_word[i - 1] == "H" and wx_word[i] in "sSz"):
                continue
            left = wx_word[:i]
            right = wx_word[i:]
            sig = (left, right, "as-printed", "")
            if sig in seen:
                continue
            seen.add(sig)
            out = self._cached_wx_sandhi(left, right)
            if out == ("__EXCEPTION__",):
                continue
            forms = [f.replace(" ", "") for f in
                     (out[0].split(":") if out and out[0] else [])]
            if wx_word in forms:
                found.append((left, right, "as-printed (no change needed)", "", False))

        # Supplementary pass: the nañ (negative) prefix "a-"/"an-" at the
        # very start of the word. Unlike most compound junctions, this one
        # is very often phonologically TRIVIAL -- "an" ends in a consonant
        # and the second member can begin with any vowel with no euphonic
        # change at all (e.g. "an"+"asUyakaH" -> "anasUyakaH", n+a simply
        # concatenate; contrast a real upasarga+root junction, which is
        # what actually triggers niyama.py's rules). Because the rule
        # table above only encodes junctions where a phonological RULE
        # fires, this trivial juxtaposition is otherwise invisible to the
        # cut-point scanner. Restricted to position 0 (nañ is always the
        # first member) and to exactly the two closed-class allomorphs,
        # so -- unlike a general "try every position" pass, which the
        # comment above the H+sibilant pass notes was tried and rejected
        # for flooding the ranking with noise -- this can't do the same,
        # since only ONE cut point is ever proposed per allomorph and the
        # dictionary-validation step downstream still has to confirm the
        # remainder is a real word before either candidate survives.
        for prefix in ("an", "a"):
            if len(wx_word) <= len(prefix):
                continue
            if not wx_word.startswith(prefix):
                continue
            left = prefix
            right = wx_word[len(prefix):]
            # Unlike the other supplementary passes above, this candidate
            # is never round-tripped through forward sandhi (there's no
            # sandhi to verify -- see the comment above). That means it
            # has no independent legitimacy check of its own, so require
            # the remainder to actually be a real dictionary word here,
            # at generation time, rather than letting it through as an
            # unverified "phonology-only" guess for the generic ranking
            # to sort out later. Without this, EVERY "a"-initial word in
            # the language -- including extremely common pronoun/
            # demonstrative forms like "asmin" (locative of idam/ayam,
            # nothing to do with negation) -- would spuriously propose
            # "a" + <remainder>, which is exactly the kind of noise the
            # H+sibilant pass above was deliberately kept narrow to avoid.
            if self.dictionary is not None and not self._in_dictionary(right):
                continue
            sig = (left, right, "nan-samAsa", "")
            if sig in seen:
                continue
            seen.add(sig)
            found.append((left, right,
                           "na\u00f1-samāsa (negative prefix, no sandhi)", "", False))

        # General "trivial junction" pass: many genuine compounds need NO
        # sandhi transformation at all at their member boundary -- e.g.
        # "SreRTa"+"guNEH" ("shreshtha"+"gunaih"), where the first member
        # ends in a vowel and the second begins with a consonant, so the
        # two simply concatenate unchanged. Every OTHER pass above finds
        # its candidates by searching for the SIGNATURE of an applied
        # sandhi rule (matched against niyama.py's table), so a genuinely
        # sandhi-free junction like this is otherwise invisible to the
        # cut-point scanner entirely -- not mis-ranked, not found at all.
        # (An earlier attempt at a blanket "try every position" version
        # of this, with no dictionary gate, was reverted for flooding the
        # ranking with coincidental noise -- see the H+sibilant pass
        # comment above. What makes this safe now is requiring AT LEAST
        # ONE side to independently validate via the full stem-candidate
        # machinery before proposing the cut at all -- i.e. this benefits
        # from every declension-ending pattern in DECLENSION_SUFFIXES,
        # not a raw substring match -- so a random cut surviving on pure
        # coincidence is rare enough to be an acceptable trade-off,
        # unlike allowing a single unfiltered short first-member the way
        # that earlier attempt did. Only one side is required, not both,
        # so a genuine 3+-member compound can still be found: e.g.
        # "sarva"+"lakzaRasaMpannA" -- the right piece isn't a dictionary
        # word ON ITS OWN (it's itself a further compound, "lakzaRa"+
        # "saMpannA") -- proposing the cut here just makes it a candidate;
        # _recursive_split (the caller) is what actually decides whether
        # to accept it outright (both sides validate) or recurse into
        # whichever side didn't, with its own further length/quality
        # gating on that recursion.
        if self.dictionary is not None:
            for i in range(self.min_member_len, n - self.min_member_len + 1):
                left, right = wx_word[:i], wx_word[i:]
                sig = (left, right, "sax-samAsa", "")
                if sig in seen:
                    continue
                if not (self._in_dictionary(left) or self._in_dictionary(right)):
                    continue
                seen.add(sig)
                found.append((left, right,
                               "sandhi-free junction (members concatenate "
                               "unchanged)", "", False))

        self._split_cache[wx_word] = found
        return found

    # ------------------------------------------------------- classify -----
    def guess_samasa_type(self, member_wx_list):
        """Very rough structural heuristic. NOT a substitute for real
        (dictionary + meaning based) samasa classification."""
        if len(member_wx_list) < 2:
            return "not a compound (single member)"
        first = member_wx_list[0]
        if first in SANDHI_PARTICLE_WX:
            return (f"NOT a samasa -- '{first}' is a particle; this is "
                     "ordinary external sandhi fused without a written space")
        if first in NUMERAL_PREFIXES:
            return "dvigu (heuristic: numeral first member)"
        if first in UPASARGA_WX:
            return (f"tatpuruSa (upasarga-compound: '{first}-' is one of "
                     "the 22 traditional upasargas)")
        if first in NAN_PREFIX_WX:
            return (f"na\u00f1-tatpuruSa (negative compound: '{first}-' is "
                     "the negative prefix a-/an-)")
        if first in COMMON_AVYAYA_PREFIXES:
            return "avyayibhava? (heuristic: indeclinable-looking first member)"
        return ("tatpuruSa / karmaXAraya / bahuvrIhi -- uncertain "
                "(needs meaning/dictionary glosses to disambiguate)")

    def is_upasarga(self, word, scheme="iast"):
        """Is `word` one of the 22 traditional Sanskrit upasargas?"""
        scheme_obj = getattr(sanscript, scheme.upper(), sanscript.IAST)
        wx = self._to_wx(word, scheme_obj)
        # Normalize a trailing anusvara (WX "M") to plain "m" before
        # checking -- "sam" (the upasarga) surfaces as "saM" whenever it
        # occurs word-finally (e.g. as a compound member on its own, see
        # the "saM"+"BArAn" split of "saMBArAn"), since final "m" before
        # any following consonant becomes anusvara. UPASARGA_WX stores
        # the citation spelling ("sam"), so without this the two never
        # matched at all.
        if wx.endswith("M"):
            wx = wx[:-1] + "m"
        return wx in UPASARGA_WX

    def is_nan_prefix(self, word, scheme="iast"):
        """Is `word` the nañ (negative) prefix -- "a-" or "an-"?"""
        scheme_obj = getattr(sanscript, scheme.upper(), sanscript.IAST)
        return self._to_wx(word, scheme_obj) in NAN_PREFIX_WX

    def is_sandhi_particle(self, word, scheme="iast"):
        """Is `word` one of the common indeclinable particles (ca, vā, tu,
        hi, eva, api, ...) that frequently get sandhi-fused onto the next
        word with no printed space, rather than forming a real compound?"""
        scheme_obj = getattr(sanscript, scheme.upper(), sanscript.IAST)
        return self._to_wx(word, scheme_obj) in SANDHI_PARTICLE_WX

    def is_len_exempt_particle(self, word, scheme="iast"):
        """Is `word` a particle trusted enough to justify a short-match
        split by length alone (currently just "ca" -- see
        CLOSED_CLASS_LEN_EXEMPT for why the others aren't)?"""
        scheme_obj = getattr(sanscript, scheme.upper(), sanscript.IAST)
        wx = self._to_wx(word, scheme_obj)
        return wx in self.CLOSED_CLASS_LEN_EXEMPT and wx not in UPASARGA_WX

    def looks_like_verb_form(self, word, scheme="iast", min_stem_len=2):
        """
        Does `word` end in a distinctive finite-verb/gerund/infinitive
        pattern (see VERB_ENDING_SUFFIXES_WX)? This does NOT resolve to a
        dictionary root -- see that table's docstring for why not -- it's
        a structural recognizer, used to stop an inflected verb form from
        being mistaken for a particle/samasa split. `min_stem_len`
        guards against matching the ending alone with nothing in front
        of it.
        """
        scheme_obj = getattr(sanscript, scheme.upper(), sanscript.IAST)
        wx = self._to_wx(word, scheme_obj)
        for suf in VERB_ENDING_SUFFIXES_WX:
            if wx.endswith(suf) and len(wx) - len(suf) >= min_stem_len:
                return True
        return False

    def resolve_pratyaya(self, word, scheme="iast"):
        """
        Try to properly resolve `word` as ROOT + kRt-PRATYAYA (see
        PRATYAYA_SUFFIXES), verified against real verb roots (see
        load_verb_roots) rather than just recognized-and-skipped the way
        looks_like_verb_form() treats other verb forms.

        Two strategies, tried in order:
          1. Direct suffix strip -- works for roots that don't change
             before the suffix (jYA + wum -> jYAwum, unchanged).
          2. The existing sandhi-reversal engine (the same one samasa
             splitting and word-boundary restoration use), restricted to
             splits whose right-hand piece is exactly the pratyaya --
             this catches regular EXTERNAL-sandhi-style changes at the
             root/suffix boundary (e.g. gam + wum -> ganwum via nasal
             assimilation).

        What this can NOT catch: guNa/vRddhi ablaut internal to
        kRt-pratyaya formation (kR -> kar+wum, buX -> boX+Xum) -- that's
        a root-formation rule, not a sandhi rule, and isn't in niyama.py
        at all. Returns a dict either way so the caller can tell resolved
        apart from merely recognized:
            {"pratyaya": name, "gloss": ..., "root": str_or_None,
             "resolved": bool}
        or None if the word doesn't end in any known pratyaya at all. If
        more than one root equally explains the surface form (rare, but
        real -- see "buddhvā" in the source comments), "root" is a list
        instead of a string and an "ambiguous": True key is added, rather
        than silently guessing one.
        """
        scheme_obj = getattr(sanscript, scheme.upper(), sanscript.IAST)
        wx = self._to_wx(word, scheme_obj)

        for (suf, name, gloss) in PRATYAYA_SUFFIXES:
            if not (wx.endswith(suf) and len(wx) > len(suf)):
                continue
            if not self.verb_roots:
                return {"pratyaya": name, "gloss": gloss, "root": None, "resolved": False}

            # Collect every root candidate that actually explains the
            # surface form, from both strategies -- more than one can
            # validate (e.g. "buddhvā" is explained equally well by
            # budh+tvā and the rare root bud+tvā, since jaṣtva collapses
            # both to the same "-ddhvā" surface spelling). Rather than
            # arbitrarily picking whichever came first, surface the
            # ambiguity honestly instead of guessing.
            found = set()
            direct = wx[: -len(suf)]
            if direct in self.verb_roots:
                found.add(direct)
            for (left, right, styp, sutra, _real) in self._candidate_two_way_splits(wx):
                if right == suf and left in self.verb_roots:
                    found.add(left)

            if len(found) == 1:
                root_wx = next(iter(found))
                return {"pratyaya": name, "gloss": gloss,
                        "root": self._from_wx(root_wx, scheme_obj), "resolved": True}
            if len(found) > 1:
                roots = sorted(self._from_wx(r, scheme_obj) for r in found)
                return {"pratyaya": name, "gloss": gloss,
                        "root": roots, "resolved": True, "ambiguous": True}
            # recognized the pratyaya, but couldn't verify a root (likely
            # needs guNa/vRddhi ablaut reversal -- out of scope here)
            return {"pratyaya": name, "gloss": gloss, "root": None, "resolved": False}
        return None

    def looks_like_matup_form(self, word, scheme="iast"):
        """
        Does `word` end in a matup pratyaya allomorph (see
        MATUP_SUFFIXES_WX) with a plausible stem in front of it? Purely
        structural (like looks_like_verb_form) -- use resolve_matup() to
        also validate the stem against the dictionary.
        """
        scheme_obj = getattr(sanscript, scheme.upper(), sanscript.IAST)
        wx = self._to_wx(word, scheme_obj)
        for suf, _citation, _gloss in MATUP_SUFFIXES_WX:
            if wx.endswith(suf) and len(wx) - len(suf) >= 2:
                return True
        return False

    def resolve_matup(self, word, scheme="iast"):
        """
        Try to resolve `word` as NOUN-STEM + matup (possessive) pratyaya
        -- see MATUP_SUFFIXES_WX. Verified against the dictionary when
        one is loaded, the same way resolve_pratyaya verifies a kRt-
        pratyaya root against self.verb_roots.

        Returns a dict either way so the caller can tell resolved apart
        from merely recognized:
            {"pratyaya": "vat"/"mat", "gloss": ..., "stem": str_or_None,
             "resolved": bool}
        or None if the word doesn't end in either matup allomorph at all.
        """
        scheme_obj = getattr(sanscript, scheme.upper(), sanscript.IAST)
        wx = self._to_wx(word, scheme_obj)
        for suf, citation, gloss in MATUP_SUFFIXES_WX:
            if not (wx.endswith(suf) and len(wx) - len(suf) >= 2):
                continue
            stem_wx = wx[:-len(suf)]
            if self.dictionary is None:
                return {"pratyaya": citation, "gloss": gloss, "stem": None, "resolved": False}
            if self._in_dictionary(stem_wx):
                return {"pratyaya": citation, "gloss": gloss,
                        "stem": self._from_wx(stem_wx, scheme_obj), "resolved": True}
            return {"pratyaya": citation, "gloss": gloss, "stem": None, "resolved": False}
        return None

    @staticmethod
    def _deaspirate(wx_str):
        return "".join(ASPIRATE_TO_PLAIN_WX.get(ch, ch) for ch in wx_str)

    def looks_like_upasarga_verb(self, word, scheme="iast"):
        """
        Does `word` consist of a recognized upasarga prefixed directly
        onto a verb form -- e.g. pari+papraccha ("he asked"),
        anu+gacchati ("he follows")? Upasargas attach to verbs at least
        as often as they open nominal compounds, but so far only
        nominal-compound recognition has used them. Left unchecked, a
        token like "paripapraccha" gets handed to the samasa splitter,
        which has no notion of verb morphology and confidently proposes
        a wrong nominal split instead (the "samasa" paripapr + accha).

        Three checks, tried in order, after stripping a recognized 2+
        char upasarga:
          1. the remainder is itself a verified root (bare upasarga+root)
          2. the remainder ends in a recognized verb-conjugation pattern
             (looks_like_verb_form) -- ordinary tense forms, e.g.
             anu+gacchati
          3. a DEASPIRATED verb root appears near the start of the
             remainder -- catches reduplicated perfect-tense forms,
             where Sanskrit's reduplication rule deaspirates the copied
             consonant (root "prach" -> "pa-prac-cha": the root's
             aspirated "ch" surfaces as plain "c" in the duplicated
             copy, so searching for the LITERAL root text would miss it)

        This does NOT extract the exact root -- reduplication drops and
        alters too much to reverse with a simple table, the same
        boundary resolve_pratyaya() draws for guNa/vRddhi ablaut. The
        value here, like that "recognized but unresolved" case, is
        correctly recognizing "this is a verb, not a compound" even
        when the precise root can't be pinned down.
        """
        scheme_obj = getattr(sanscript, scheme.upper(), sanscript.IAST)
        wx = self._to_wx(word, scheme_obj)
        wx_scheme = sanscript.WX

        for up in sorted(self.CLOSED_CLASS_LEN_EXEMPT, key=len, reverse=True):
            if up not in UPASARGA_WX or len(up) < 2 or not wx.startswith(up):
                continue
            remainder = wx[len(up):]
            if len(remainder) < 3:
                continue
            if self.verb_roots and remainder in self.verb_roots:
                return True
            if self.looks_like_verb_form(remainder, scheme="wx"):
                return True
            if self._has_reduplication_signature(remainder):
                return True
        return False

    @staticmethod
    def _has_reduplication_signature(remainder):
        """
        A narrow, precise test for Sanskrit's reduplicated-perfect
        pattern: consonant + vowel, then the SAME consonant (possibly
        deaspirated) again -- e.g. "pa-prac-cha" (p...p), "ca-kAr"
        (k...k, for kR). This is much stricter than searching for any
        known root as a loose substring (which was tried and caused
        real false positives -- "vipulAMso"'s remainder "pulAMso" has
        no repeated consonant, but some coincidental root text still
        matched somewhere in a wide window). Requiring the exact
        two-syllable repeat at a fixed offset is far more specific to
        actual reduplication and much less likely to fire by accident.
        """
        if len(remainder) < 4:
            return False
        c0 = ASPIRATE_TO_PLAIN_WX.get(remainder[0], remainder[0])
        c2 = ASPIRATE_TO_PLAIN_WX.get(remainder[2], remainder[2])
        return c0.isalpha() and c0 == c2

    # ---------------------------------------------------------- public ----
    # Common inflectional case-suffixes that occasionally coincide with an
    # unrelated short dictionary headword (e.g. "sya" -- the a-stem
    # genitive singular ending -- happens to itself be a rare entry).
    # When one of these turns up as the LAST "member" of a split, it's
    # really the case ending on the member before it, not a compound
    # member in its own right -- merge it back in.
    _CASE_SUFFIXES_WX = {"sya", "asya", "ya", "Aya", "e", "ay"}

    def _merge_stray_case_suffix(self, members_wx):
        if len(members_wx) >= 2 and members_wx[-1] in self._CASE_SUFFIXES_WX:
            merged = members_wx[:-2] + (members_wx[-2] + members_wx[-1],)
            return merged
        return members_wx

    def split(self, word, scheme="iast", verbose=True):
        """
        Top-level entry point. Returns a list of result dicts:
            {"members": [...], "confidence": "dictionary-verified"/"phonology-only",
             "type_guess": str}
        `scheme` is any indic_transliteration scheme name (iast, devanagari, ...).
        """
        scheme_obj = getattr(sanscript, scheme.upper(), sanscript.IAST)
        wx_word = self._to_wx(word, scheme_obj)

        results = self._recursive_split(wx_word, depth=0)
        # Fold a stray trailing case-suffix "member" back into the
        # preceding one, then re-dedupe (this can make two candidates
        # collapse into the same result).
        merged_results = []
        seen = set()
        for members_wx, dict_backed in results:
            merged = self._merge_stray_case_suffix(members_wx)
            if merged not in seen:
                seen.add(merged)
                merged_results.append((merged, dict_backed))
        results = merged_results

        # Prefer: dictionary-backed, then fewest members, then (new)
        # among equally-sized candidates, the one whose FIRST member is
        # LONGEST -- i.e. prefer a cut as far right as possible before
        # falling back to an earlier, shorter one. A short first-member
        # match (e.g. "bhara"+"dvAjasya", "vacananis"+"xeSAw") is much
        # more likely to be phonological coincidence than the same word
        # explained by a longer, more specific first member ("BaraxvAja"
        # +"sya", "vacana"+"nirxeSAw") -- this directly implements
        # "start from the full word and strip letters from the right
        # one at a time until something matches" rather than accepting
        # whichever short coincidental cut the search happens to reach
        # first. Then (as a further tie-break) candidates where no
        # member is a proper-noun-ONLY entry -- a rare name coincidentally
        # matching part of a word (see build_proper_nouns_from_cdsl) is a
        # much less likely explanation than an ordinary word when the two
        # are otherwise tied, though a genuine compound CAN legitimately
        # contain a proper noun, so this only breaks ties, never excludes.
        def _has_proper_noun(members_wx):
            return bool(self.proper_nouns) and any(m in self.proper_nouns for m in members_wx)

        results.sort(key=lambda r: (not r[1], len(r[0]), _has_proper_noun(r[0])))
        results = results[:8]

        formatted = []
        for members_wx, dict_backed in results:
            members = [self._from_wx(m, scheme_obj) for m in members_wx]
            formatted.append({
                "members": members,
                "confidence": "dictionary-verified" if dict_backed else "phonology-only",
                "type_guess": self.guess_samasa_type(members_wx),
            })

        if verbose:
            self._print_report(word, formatted)
        return formatted

    # Single-character upasargas (just "A" / ā) are excluded from the
    # length exemption below: a 1-character match is too promiscuous --
    # "ā" collides constantly with the ordinary feminine -ā ending and
    # would "exempt" almost any word-final fragment. 2+ character
    # upasargas (su, vi, ni, dur, ...) are distinctive enough to trust.
    # Sandhi particles (ca, vā, tu, hi, ...) get the same treatment for
    # the same reason.
    UPASARGA_LEN_EXEMPT = {u for u in UPASARGA_WX if len(u) >= 2}
    # Length-exemption now covers the full particle set. "vA"/"wu" (vā,
    # tu) had been excluded because "vāgmī"->"vā"+"agmī" and
    # "tvayā"->"tu"+"ayā" both slipped past the whole-word gate -- but
    # that was really a dictionary-coverage gap (an -in stem adjective
    # and a suppletive pronoun form), now fixed directly in
    # _stem_candidates() and PRONOUN_FORMS_WX rather than worked around
    # here.
    # NAN_PREFIX_WX ("a"/"an") is added here too -- see its module-level
    # comment for why a 1-2 char nañ-tatpuruSa prefix earns the same
    # closed-class exemption as a 2+ char upasarga.
    CLOSED_CLASS_LEN_EXEMPT = UPASARGA_LEN_EXEMPT | SANDHI_PARTICLE_WX | NAN_PREFIX_WX

    def _member_len_ok(self, piece, factor=1, allow_upasarga=False):
        """
        Is this piece long enough to plausibly be a real compound member?
        A recognized (2+ char) upasarga OR sandhi particle is exempt from
        the length floor, but ONLY when `allow_upasarga` is set -- callers
        should only pass this for the left-hand piece of a TOP-LEVEL split
        (the true start of the original word), never for pieces produced
        deeper in recursion, where a coincidental match is far more likely
        than a real prefix/particle.
        """
        if allow_upasarga and piece in self.CLOSED_CLASS_LEN_EXEMPT:
            return True
        return len(piece) >= self.min_member_len * factor

    def _recursive_split(self, wx_word, depth):
        """
        Returns a list of (members_wx_tuple, dict_backed_bool).
        If a dictionary is loaded: prefer splits where every final member is
        a dictionary word, recursing into pieces that aren't.
        If no dictionary: just return the raw two-way candidates (no
        recursion, since without validation we can't tell which piece is
        "real" enough to keep splitting).
        """
        cache_key = (wx_word, depth)
        cached = self._recursive_cache.get(cache_key)
        if cached is not None:
            return cached

        two_way = self._candidate_two_way_splits(wx_word)
        # Drop candidates with a too-short piece -- real samasa members are
        # essentially never single/double-letter fragments, and the
        # dictionary contains many spurious short entries that would
        # otherwise blow up the recursion combinatorially. A recognized
        # upasarga (su-, vi-, ni-, dur-, ...) is exempt when it's the
        # left-hand piece of THIS top-level call (depth 0) -- i.e. the
        # true start of the word -- since that's a genuine morphological
        # signal, not dictionary noise.
        allow_left = (depth == 0)
        two_way = [t for t in two_way
                   if self._member_len_ok(t[0], allow_upasarga=allow_left)
                   and self._member_len_ok(t[1])]

        if self.dictionary is None:
            two_way.sort(key=lambda t: (not t[4], len(t[0])))
            result = [((l, r), False) for (l, r, *_rest) in two_way[:25]]
            self._recursive_cache[cache_key] = result
            return result

        # Dictionary-guided recursive segmentation
        results = []
        if self._in_dictionary(wx_word):
            results.append(((wx_word,), True))

        if depth < self.max_depth:
            for (left, right, styp, sutra, real_change) in two_way:
                left_ok = self._in_dictionary(left)
                right_ok = self._in_dictionary(right)
                if left_ok and right_ok:
                    results.append(((left, right), True))
                elif left_ok and not right_ok and self._member_len_ok(right, factor=2):
                    for sub in self._recursive_split(right, depth + 1):
                        if sub[1]:
                            results.append(((left,) + sub[0], True))
                elif right_ok and not left_ok and self._member_len_ok(left, factor=2):
                    for sub in self._recursive_split(left, depth + 1):
                        if sub[1]:
                            results.append((sub[0] + (right,), True))
        # de-dup, prefer fewest members
        seen = set()
        uniq = []
        for r in sorted(results, key=lambda r: len(r[0])):
            if r[0] not in seen:
                seen.add(r[0])
                uniq.append(r)
        if not uniq:
            two_way.sort(key=lambda t: (not t[4], len(t[0])))
            uniq = [((l, r), False) for (l, r, *_rest) in two_way[:10]]
        uniq = uniq[:12]
        self._recursive_cache[cache_key] = uniq
        return uniq

    def _print_report(self, original, formatted):
        print(f"\n=== {original} ===")
        if not formatted:
            print("  (no valid splits found)")
            return
        if self.dictionary is None:
            print("  [no dictionary loaded -- showing all phonologically valid "
                  "candidates, unranked by meaning]")
        for r in formatted:
            tag = "✓ dict" if r["confidence"] == "dictionary-verified" else "  phon"
            print(f"  [{tag}]  " + " + ".join(r["members"]) +
                  f"   -- type guess: {r['type_guess']}")

    # ---------------------------------------------------- inter-word ------
    # Plausible pre-sandhi endings to try for a word-final syllable, keyed
    # by what the OBSERVED final WX character is. Sourced from the common
    # patterns of visarga sandhi (H -> o/r/s/etc), yaN sandhi (i/u -> y/v),
    # and vowel-length alternations -- not exhaustive, but covers the
    # overwhelming majority of junctions in narrative verse.
    _ENDING_GUESSES = {
        "o": ["aH"], "e": ["aH", "e"], "H": ["H", "s", "r"],
        "S": ["H"], "z": ["H"], "s": ["H", "s"], "r": ["H", "r"],
        "y": ["i", "I"], "v": ["u", "U"],
        "a": ["a"], "A": ["A", "a", "AH"], "i": ["i"], "I": ["I", "i"],
        "u": ["u"], "U": ["U", "u"],
    }

    def restore_word_boundary(self, token1, token2, scheme="iast"):
        """
        Given two ADJACENT printed padas, propose the pre-sandhi citation
        forms of BOTH tokens at their shared junction, using the real
        forward Sandhi.sandhi() engine as the oracle -- this automatically
        includes apavaada.py's exception rules (e.g. visarga + voiced
        consonant -> o), which a rule-table-only reverse index would miss.

        Handles the common avagraha case too: a token printed as "'xyz"
        (leading apostrophe) marks an elided initial "a" -- e.g.
        "ko 'nasūyakaḥ" is really "kaḥ" + "anasūyakaḥ". Both the left
        token's ending AND the right token's elided start are proposed
        as candidates and verified together.

        Returns a list of dicts (best first): left, right (restored
        forms of both tokens), sandhi_type, sutra, dict_backed.
        """
        scheme_obj = getattr(sanscript, scheme.upper(), sanscript.IAST)
        t1_wx = self._to_wx(token1, scheme_obj)
        t2_wx = self._to_wx(token2, scheme_obj)
        printed_wx = t1_wx + t2_wx  # what a fully fused form would look like

        last = t1_wx[-1] if t1_wx else ""
        # NOTE: these must be an ORDER-PRESERVING, deduplicated sequence,
        # not a set -- Python's string-hash randomization makes set
        # iteration order vary between process runs, which previously
        # caused this method to non-deterministically rank tied
        # candidates differently on different runs (e.g. "nu" vs "nū"
        # for the same input). dict.fromkeys() dedupes while keeping
        # first-seen order, which keeps the baseline first and ties
        # broken the same way every time.
        left_guesses = dict.fromkeys(
            [t1_wx] + [t1_wx[:-1] + ending for ending in self._ENDING_GUESSES.get(last, [])])

        # right-side candidates: as-printed, plus the avagraha-restored
        # form when the token starts with an elision apostrophe
        right_guesses = [token2]
        if token2.startswith("'"):
            right_guesses.append("a" + token2[1:])

        scored = []
        for cand_left_wx in left_guesses:
            cand_left_native = self._from_wx(cand_left_wx, scheme_obj)
            for cand_right_native in right_guesses:
                try:
                    out = self.S.sandhi(cand_left_native, cand_right_native,
                                         input_scheme=scheme_obj)
                except Exception:
                    continue
                cand_right_wx = self._to_wx(cand_right_native, scheme_obj)
                is_baseline = (cand_left_wx == t1_wx and cand_right_native == token2)
                for (ans, sutra, styp) in out:
                    ans_wx = self._to_wx(ans, scheme_obj).replace(" ", "")
                    if ans_wx == printed_wx:
                        # a candidate identical to the as-printed token
                        # must validate WITHOUT the -o->-aH restoration,
                        # since needing that restoration is itself proof
                        # sandhi already happened (see _stem_candidates)
                        strict_left = (cand_left_wx == t1_wx)
                        l_ok = bool(self._in_dictionary(
                            cand_left_wx, allow_ext_visarga_o=not strict_left)) if self.dictionary else None
                        if cand_right_native == token2:
                            dict_backed = l_ok
                        else:
                            r_ok = bool(self._in_dictionary(cand_right_wx)) if self.dictionary else None
                            dict_backed = bool(l_ok) and bool(r_ok)
                        scored.append((cand_left_wx, cand_right_native, styp, sutra,
                                       is_baseline, dict_backed))

        # also always keep the as-printed baseline even if unverified
        if not any(c[0] == t1_wx and c[1] == token2 for c in scored):
            l_ok = bool(self._in_dictionary(t1_wx, allow_ext_visarga_o=False)) if self.dictionary else None
            scored.append((t1_wx, token2, "as-printed", "", True, l_ok))

        # prefer dictionary-backed candidates. Among those, a token ending
        # in short "o" is virtually NEVER a genuine citation form (that
        # ending only ever arises from visarga sandhi before a voiced
        # sound), so a validated correction should win there even if the
        # as-printed baseline happens to coincidentally match some
        # unrelated dictionary entry. The same logic applies to a token
        # ending in "ś" or "ṣ" (WX: S/R) -- these arise ONLY from visarga
        # sandhi before a palatal (c/ch) or retroflex (ṭ/ṭh) initial (e.g.
        # "kaḥ"+"ca" -> "kaś ca"); a genuine citation form essentially
        # never ends in these consonants at a word boundary, so a
        # baseline "as-printed" dictionary hit here (e.g. some unrelated
        # headword "kaś") is coincidental, not the real reading, and must
        # not outrank a validated visarga-restoration candidate. For any
        # other ending, prefer the as-printed baseline among ties -- it's
        # the simplest explanation unless a correction is the ONLY thing
        # that validates.
        visarga_derived_ending = t1_wx.endswith(("o", "S", "R"))
        scored.sort(key=lambda c: (not bool(c[5]), visarga_derived_ending and (c[0] == t1_wx), not c[4]))

        out = []
        seen = set()
        for (cand_left_wx, cand_right_native, styp, sutra, is_baseline, dict_backed) in scored:
            key = (cand_left_wx, cand_right_native)
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "left": self._from_wx(cand_left_wx, scheme_obj),
                "right": cand_right_native,
                "sandhi_type": "as-printed" if is_baseline else styp,
                "sutra": sutra,
                "dict_backed": dict_backed,
            })
            if len(out) >= 5:
                break
        return out



# --------------------------------------------------------------------------- #
# Karaka (case-role) analysis: identify the finite verb (kriya), then the
# karta (nominative subject) and karma (accusative object) by MATCHING CASE
# ENDINGS, then group any other same-case word in the verse as a qualifier
# of whichever of the two it agrees with -- this mirrors the traditional
# pedagogical method: find the verb, ask "who [verb]?" for karta, ask
# "whom/what did [karta] [verb]?" for karma, then repeatedly ask "what type
# of [karta/karma]?" until no more same-case words remain.
#
# CRITICAL CAVEAT: this is a case-ENDING matcher, not a declension parser.
# Sanskrit endings are genuinely ambiguous across gender/stem-class without
# knowing the stem's actual class from a declension-aware dictionary --
# e.g. "-An" is BOTH a masc./fem. consonant-stem (-mat/-vat) NOMINATIVE
# SINGULAR ("bhagavAn") and a masc. a-stem ACCUSATIVE PLURAL ("narAn"); "-A"
# is both a fem. A-stem nominative singular AND (with a different stem
# class) an instrumental singular. Every tag this produces is therefore a
# CANDIDATE reading, exactly like the tool's existing "phonology-only"
# (unconfirmed) findings elsewhere -- worth a manual check, not a verdict.
# Table entries are ordered LONGEST SUFFIX FIRST so e.g. "-mAn"/"-vAn"
# (3 chars) are tried before the shorter, differently-cased "-An" (2
# chars) they'd otherwise be swallowed by.
# --------------------------------------------------------------------------- #
CASE_ENDING_TABLE_WX = [
    # (suffix_wx, case, number, note)
    ("mAn", "nominative", "singular", "-mat stem (e.g. buddhimAn)"),
    ("vAn", "nominative", "singular", "-vat stem (e.g. balavAn, bhagavAn)"),
    ("Iyam", "nominative", "singular", "fem I-stem/pronoun (iyam)"),
    ("asya", "genitive", "singular", "a-stem masc/neut gen sg (e.g. rAmasya)"),
    # FIXED (Sarga-1 gold-standard pass): was "Anam" -- the a-stem genitive plural is -ānām
    # (WX "AnAm"), so the old entry never matched a real genitive plural (prajānām, rakṣasām...).
    ("AnAm", "genitive", "plural", "a-stem gen pl (e.g. narANAm -- approximate)"),
    ("ANAm", "genitive", "plural", "a-stem gen pl after r/ṣ (ṇatva), e.g. rAmANAm"),
    ("eRu", "locative", "plural", "a-stem loc pl (e.g. narezu)"),
    ("AByAm", "instrumental", "dual", ""),
    ("Aw", "ablative", "singular", "a-stem abl sg (e.g. grAmAw)"),
    ("AH", "nominative", "plural", "a-stem masc nom pl (ambiguous w/ A-stem fem gen/abl sg)"),
    ("An", "accusative", "plural", "a-stem masc acc pl (ambiguous w/ -mat/-vat nom sg, see above)"),
    ("aH", "nominative", "singular", "a-stem masc nom sg (e.g. rAmaH)"),
    ("am", "accusative", "singular", "a-stem masc acc sg / neut nom-acc sg"),
    ("ena", "instrumental", "singular", "a-stem masc/neut inst sg (e.g. vanena)"),
    # ADDED (Sarga-1 pass): the ṇatva form -eṇa (WX "eNa": rāmeṇa, cāritreṇa) was missing, so every
    # instrumental after r/ṛ/ṣ went unrecognised.
    ("eNa", "instrumental", "singular", "a-stem inst sg after r/ṣ (ṇatva), e.g. rAmeNa"),
    ("EH", "instrumental", "plural", "a-stem inst pl (e.g. janaiH)"),
    ("eByaH", "dative", "plural", "a-stem dat/abl pl -- ambiguous with ablative"),
    ("ayoH", "genitive", "dual", "a-stem gen/loc dual -- ambiguous with locative"),
    ("Aya", "dative", "singular", "a-stem masc/neut dat sg"),
    ("iH", "nominative", "singular", "i-stem masc/fem nom sg (e.g. vAlmIkiH)"),
    ("uH", "nominative", "singular", "u-stem masc/fem nom sg (e.g. guruH)"),
    ("im", "accusative", "singular", "i-stem acc sg"),
    ("um", "accusative", "singular", "u-stem acc sg"),
    ("Am", "genitive", "plural", "-Am gen pl across several stem classes (e.g. vAgvidAm)"),
    ("I", "nominative", "singular", "-in stem masc / fem I-stem (e.g. wapasvI)"),
    ("A", "nominative", "singular", "fem A-stem nom sg (highly ambiguous -- also inst sg elsewhere)"),
]


def restore_tokens(sp, tokens, scheme="iast"):
    """
    Given a list of RAW (as-printed, sandhi-affected) tokens from a line
    of running verse text, return best-effort CITATION-FORM tokens,
    junction by junction (via restore_word_boundary -- the same
    restoration analyze_verse_corpus applies before samasa-splitting,
    see restored_left/restored_right there). This is a prerequisite for
    the karaka case-ending matcher: a word's case ending is very often
    itself masked by the FOLLOWING word's sandhi (e.g. the visarga in
    "vAlmIkiH" surfaces as plain "r" before the voiced "munipuMgavam"),
    so running the matcher on raw running-text tokens misses real
    nominative/accusative endings and can misidentify an adjective as
    the head noun purely because it happened to already be in citation
    form. Processes junctions left-to-right so an avagraha-restored
    token's real ENDING (fixed by the NEXT junction) still gets applied
    on top of its already avagraha-restored BEGINNING.
    """
    restored = list(tokens)
    for i in range(len(tokens) - 1):
        t1, t2 = restored[i], tokens[i + 1]
        try:
            cands = sp.restore_word_boundary(t1, t2, scheme=scheme)
        except Exception:
            cands = []
        if not cands:
            continue
        best = cands[0]
        if best["left"] != t1:
            restored[i] = best["left"]
        if best["right"] != t2:
            restored[i + 1] = best["right"]
    return [r.strip("'") for r in restored]


def guess_case(sp, word_wx):
    """
    Return (case, number, note) for the best-matching entry in
    CASE_ENDING_TABLE_WX, or None if nothing matches. See the module
    caveat above -- this is a candidate reading, not a certainty.

    Normalizes a trailing anusvara ("M" in this WX scheme) to plain "m"
    before matching: word-final "m" becomes anusvara before almost any
    following consonant in connected verse (a near-universal sandhi
    rule, not specific to any one case), so e.g. accusative-singular
    "nAraxam" almost always actually surfaces as "nAraxaM" -- matching
    literal "am" alone would silently miss the overwhelming majority of
    real accusative/neuter endings in running text.
    """
    if word_wx.endswith("M"):
        word_wx = word_wx[:-1] + "m"
    for suffix, case, number, note in CASE_ENDING_TABLE_WX:
        if word_wx.endswith(suffix):
            return (case, number, note)
    return None


def _is_likely_proper_noun(sp, word_wx):
    """Is any plausible stem of this inflected word a known proper noun
    (see build_proper_nouns_from_cdsl)? Used to prefer a real referential
    head (e.g. "vAlmIkiH") over a merely case-agreeing adjective (e.g.
    "wapasvI") when picking karta/karma among several same-case
    candidates -- Sanskrit verse word order is free for meter, so "first
    in the line" is a weak signal on its own."""
    if not sp.proper_nouns:
        return False
    for cand in sp._stem_candidates(word_wx):
        if cand in sp.proper_nouns:
            return True
    return False


def analyze_karaka(sp, tokens, scheme="iast"):
    """
    Heuristic karaka breakdown of one verse's worth of tokens (ideally
    already sandhi-restored -- see restored_left/restored_right in
    analyze_verse_corpus). Returns a list of dicts:
      {"token": str, "case": (case, number, note) | None, "role": str}
    The FIRST recognized finite verb becomes kriyA. The first nominative-
    tagged token after that becomes karta; the first accusative-tagged
    token becomes karma. Every other tagged token is filed as a qualifier
    of whichever head shares its case (nominative -> karta, accusative ->
    karma); untagged tokens (particles, unresolved forms, the verb
    itself) are passed through with role=None.
    """
    scheme_obj = getattr(sanscript, scheme.upper(), sanscript.IAST)
    entries = []
    verb_seen = False
    for tok in tokens:
        tok_clean = tok.strip("'")
        wx = sp._to_wx(tok_clean, scheme_obj)

        is_verb = False
        if not verb_seen:
            pratyaya = sp.resolve_pratyaya(tok_clean, scheme=scheme)
            is_verb = (bool(pratyaya)
                       or sp.looks_like_verb_form(tok_clean, scheme=scheme)
                       or sp.looks_like_upasarga_verb(tok_clean, scheme=scheme))
        if is_verb:
            verb_seen = True
            entries.append({"token": tok, "case": None, "role": "kriyā (verb)"})
            continue

        case_info = guess_case(sp, wx)
        entries.append({"token": tok, "case": case_info, "role": None})

    karta_idx = karma_idx = None
    nom_indices = [i for i, e in enumerate(entries) if e["case"] and e["case"][0] == "nominative"]
    acc_indices = [i for i, e in enumerate(entries) if e["case"] and e["case"][0] == "accusative"]

    def _pick_head(indices):
        if not indices:
            return None
        proper = [i for i in indices
                  if _is_likely_proper_noun(sp, sp._to_wx(entries[i]["token"].strip("'"), scheme_obj))]
        return proper[0] if proper else indices[0]

    karta_idx = _pick_head(nom_indices)
    karma_idx = _pick_head(acc_indices)

    for i, e in enumerate(entries):
        if i == karta_idx:
            e["role"] = "karta (nominative subject)"
        elif i == karma_idx:
            e["role"] = "karma (accusative object)"
        elif e["case"] and e["case"][0] == "nominative" and karta_idx is not None:
            e["role"] = f"qualifies karta ({entries[karta_idx]['token']})"
        elif e["case"] and e["case"][0] == "accusative" and karma_idx is not None:
            e["role"] = f"qualifies karma ({entries[karma_idx]['token']})"
        elif e["case"] and e["role"] is None:
            e["role"] = f"{e['case'][0]} ({e['case'][1]}) -- not karta/karma"

    return entries


def get_gloss(sp, word, scheme="iast"):
    """
    Look up a short English gloss for `word` (in the given input scheme)
    using sp.glosses (see build_glosses_from_cdsl / load_glosses). Tries
    each candidate stem from _stem_candidates() -- the same ending-guess
    machinery used for dictionary validation elsewhere -- so an inflected
    surface form (e.g. "munipuMgavam") can still resolve via its bare
    stem ("munipuMgava"), not just an exact headword match. Returns None
    if nothing is found or no glosses are loaded.
    """
    if not sp.glosses:
        return None
    scheme_obj = getattr(sanscript, scheme.upper(), sanscript.IAST)
    wx = sp._to_wx(word.strip("'"), scheme_obj)
    if wx in sp.glosses:
        return sp.glosses[wx]
    for cand in sp._stem_candidates(wx):
        if cand in sp.glosses:
            return sp.glosses[cand]
    return None


# --------------------------------------------------------------------------- #
# Corpus mode: run sandhi-split / samasa-split over a range of verses from
# a GRETIL-style Sanskrit text file (the "# Text" marker convention, with
# each pada-line tagged  ...text... R_KANDA,SARGA.VERSE  at the end).
# --------------------------------------------------------------------------- #

def parse_gretil_verses(text_path, kanda=None, sarga=None,
                         verse_start=None, verse_end=None, limit_lines=None):
    """
    Parse a GRETIL-style text file into {(kanda, sarga, verse): [pada_line, ...]}.
    A verse may span multiple physical lines; only the LAST line of a verse
    carries the "R_K,S.V" tag, so lines are buffered until that tag appears.

    Filters (all optional): kanda, sarga restrict to those numbers;
    verse_start/verse_end restrict the verse number within that sarga;
    limit_lines caps the number of pada-lines returned in total (applied
    last, after filtering, so it truncates the selection predictably).
    """
    line_pat = re.compile(r'^(.*\S)\s+R_(\d+),(\d+)\.(\d+)\s*$')
    with open(text_path, encoding="utf-8") as f:
        text = f.read()
    if "# Text" not in text:
        raise ValueError('Expected a "# Text" marker in the source file')
    body = text.split("# Text", 1)[1]

    verses = {}
    order = []
    buffer = []
    for raw in body.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        m = line_pat.match(raw)
        if m:
            padatext, k, s, v = m.groups()
            buffer.append(padatext)
            key = (int(k), int(s), int(v))
            verses[key] = buffer
            order.append(key)
            buffer = []
        else:
            buffer.append(raw)

    def keep(key):
        k, s, v = key
        if kanda is not None and k != kanda:
            return False
        if sarga is not None and s != sarga:
            return False
        if verse_start is not None and v < verse_start:
            return False
        if verse_end is not None and v > verse_end:
            return False
        return True

    selected = {k: verses[k] for k in order if keep(k)}

    if limit_lines is not None:
        capped = {}
        n = 0
        for k in sorted(selected.keys()):
            lines_ = selected[k]
            if n >= limit_lines:
                break
            take = lines_[: max(0, limit_lines - n)]
            if take:
                capped[k] = take
                n += len(take)
        selected = capped

    return selected


def analyze_verse_corpus(sp, verses, mode="both"):
    """
    Run sandhi-split and/or samasa-split over parsed verses (as returned
    by parse_gretil_verses). Returns (report, stats):
      report: list of {"verse": "K.S.V", "lines": [...]} -- full detail,
              suitable for a human-readable report.
      stats:  running totals for the separate summary report (see
              write_summary_report).
    """
    do_sandhi = mode in ("sandhi", "both")
    do_samasa = mode in ("samasa", "both")

    stats = {
        "verses": 0, "lines": 0,
        "sandhi_total": 0, "sandhi_confirmed": 0,
        "sandhi_phonology_only": 0, "sandhi_unchanged": 0,
        "samasa_attempted": 0, "samasa_dict_verified": 0,
        "samasa_phonology_only": 0, "samasa_none_found": 0,
        "pratyaya_attempted": 0, "pratyaya_resolved": 0,
        "pratyaya_ambiguous": 0, "pratyaya_unresolved": 0,
        "matup_attempted": 0, "matup_resolved": 0, "matup_unresolved": 0,
        "per_verse": [],  # (verse_label, sandhi_confirmed, sandhi_total, samasa_found, samasa_attempted)
    }

    report = []
    for key in sorted(verses.keys()):
        kanda, sarga, shloka = key
        verse_label = f"{kanda}.{sarga}.{shloka}"
        stats["verses"] += 1
        v_sandhi_conf = v_sandhi_total = v_samasa_found = v_samasa_attempted = 0

        verse_entry = {"verse": verse_label, "lines": []}
        for line in verses[key]:
            stats["lines"] += 1
            tokens = [w for w in re.split(r"\s+", line.strip()) if w]
            line_entry = {"text": line, "tokens": tokens}

            # restored_left[i] holds the sandhi-restored CITATION form of
            # tokens[i], when the junction with tokens[i+1] changed it (e.g.
            # "dharmajñaś" + "ca" -> restored_left[i] = "dharmajñaḥ").
            # restored_right[i+1] is the same idea for the OTHER side of the
            # same junction -- most often an avagraha restoration, e.g.
            # "ko" + "'nasūyakaḥ" -> restored_right[i+1] = "anasūyakaḥ" (the
            # elided initial "a" put back). The samasa pass below must
            # split these restored forms, not the raw surface tokens --
            # otherwise it tries to explain the neighboring word's sandhi
            # mutation (or, for the right side, the elided vowel) as part
            # of the compound boundary itself, which produces nonsense
            # (e.g. "dharmajñaś" torn into "dhas+maj+naś" instead of
            # "dharma+jña", or "'nasūyakaḥ" -- with the apostrophe merely
            # stripped rather than resolved -- torn into "nasu+uyakaḥ"
            # instead of the real "an+asūyakaḥ" nañ-tatpuruṣa).
            restored_left = {}
            restored_right = {}
            if do_sandhi:
                junctions = []
                for i in range(len(tokens) - 1):
                    t1, t2 = tokens[i], tokens[i + 1]
                    try:
                        cands = sp.restore_word_boundary(t1, t2, scheme="iast")
                    except Exception:
                        cands = []
                    junctions.append({"pair": (t1, t2), "candidates": cands})
                    best = cands[0] if cands else None
                    stats["sandhi_total"] += 1
                    v_sandhi_total += 1
                    if best is None:
                        pass
                    elif best["left"] == t1:
                        stats["sandhi_unchanged"] += 1
                        if best["right"] != t2:
                            restored_right[i + 1] = best["right"]
                    elif best["dict_backed"]:
                        stats["sandhi_confirmed"] += 1
                        v_sandhi_conf += 1
                        restored_left[i] = best["left"]
                        if best["right"] != t2:
                            restored_right[i + 1] = best["right"]
                    else:
                        stats["sandhi_phonology_only"] += 1
                        restored_left[i] = best["left"]
                        if best["right"] != t2:
                            restored_right[i + 1] = best["right"]
                line_entry["junctions"] = junctions

            # Single-token fused sandhi: some pairs of words (very often a
            # short particle like "ca"/"vā"/"hi" + the next word) get
            # sandhi-joined with NO printed space at all -- e.g. "ca" +
            # "etat" -> "caitat". restore_word_boundary() above can't see
            # these (there's no space to anchor on), so each token is also
            # run through the samasa engine and, if the result splits off
            # a recognized particle, it's reclassified as a sandhi finding
            # (not a samasa) and folded into the sandhi stats/output.
            fused_sandhi = {}
            samasa_results = {}
            pratyaya_results = {}
            matup_results = {}
            if do_sandhi or do_samasa:
                for idx, tok in enumerate(tokens):
                    # Analyze the sandhi-restored citation form when the
                    # junction pass found one (see restored_left/restored_
                    # right above); this is what resolve_pratyaya/looks_
                    # like_verb_form/split() should all see. An avagraha
                    # restoration (restored_right) takes priority when both
                    # are present, since it fixes the token's actual first
                    # letter, which every downstream check depends on. The
                    # raw `tok` is kept as the dict key so displayed output
                    # still shows the form actually printed in the verse.
                    tok_clean = restored_right.get(idx, restored_left.get(idx, tok.strip("'")))
                    tok_clean = tok_clean.strip("'")
                    if len(tok_clean) < 4:
                        continue
                    # A recognized verb-conjugation ending (see
                    # VERB_ENDING_SUFFIXES_WX) means this token is almost
                    # certainly an inflected verb form, not a compound or
                    # a particle-fusion. Before just skipping it, try to
                    # properly resolve it as root + pratyaya (see
                    # resolve_pratyaya) -- when that works, it's a much
                    # more useful report entry than silent avoidance.
                    pratyaya = sp.resolve_pratyaya(tok_clean, scheme="iast")
                    if pratyaya:
                        pratyaya_results[tok] = pratyaya
                        stats["pratyaya_attempted"] += 1
                        if pratyaya.get("ambiguous"):
                            stats["pratyaya_ambiguous"] += 1
                        elif pratyaya["resolved"]:
                            stats["pratyaya_resolved"] += 1
                        else:
                            stats["pratyaya_unresolved"] += 1
                        if do_samasa and len(tok_clean) >= 5:
                            stats["samasa_attempted"] += 1
                            v_samasa_attempted += 1
                            stats["samasa_none_found"] += 1
                        continue
                    matup = sp.resolve_matup(tok_clean, scheme="iast")
                    if matup:
                        matup_results[tok] = matup
                        stats["matup_attempted"] += 1
                        if matup["resolved"]:
                            stats["matup_resolved"] += 1
                        else:
                            stats["matup_unresolved"] += 1
                        if do_samasa and len(tok_clean) >= 5:
                            stats["samasa_attempted"] += 1
                            v_samasa_attempted += 1
                            stats["samasa_none_found"] += 1
                        continue
                    if sp.looks_like_verb_form(tok_clean, scheme="iast"):
                        if do_samasa and len(tok_clean) >= 5:
                            stats["samasa_attempted"] += 1
                            v_samasa_attempted += 1
                            stats["samasa_none_found"] += 1
                        continue
                    if sp.looks_like_upasarga_verb(tok_clean, scheme="iast"):
                        if do_samasa and len(tok_clean) >= 5:
                            stats["samasa_attempted"] += 1
                            v_samasa_attempted += 1
                            stats["samasa_none_found"] += 1
                        continue
                    tok_wx = sp._to_wx(tok_clean, sanscript.IAST)
                    # Only used to gate PARTICLE-led splits (see below) --
                    # a genuine samasa (ariṃdamaḥ -> ari+damaḥ, himālayaḥ
                    # -> hima+ālayaḥ) is worth showing even when the whole
                    # word ALSO happens to be independently dictionary-
                    # listed, since compounding it is still the real,
                    # traditionally-recognized structure. A particle
                    # "split" (hi + taḥ) is different: a particle doesn't
                    # semantically merge into anything, so if the whole
                    # word already stands on its own ("hitaḥ" is simply
                    # the word "beneficial"), a same-letters particle
                    # match is just coincidence, not morphology, and
                    # should be suppressed.
                    whole_word_ok = sp._in_dictionary(tok_wx, allow_ext_visarga_o=False)
                    try:
                        res = sp.split(tok_clean, scheme="iast", verbose=False)
                    except Exception:
                        res = []

                    # sp.split() already applies its own internal quality
                    # control (dictionary validation at every depth,
                    # upasarga/particle-aware length exemption, and
                    # proper-noun deprioritization -- see build_proper_
                    # nouns_from_cdsl), so its own ranking is trusted
                    # directly here. An earlier version of this pipeline
                    # additionally required each member to be >=4 chars
                    # (with a narrow upasarga/particle exemption) -- that
                    # was a workaround from before the library had its
                    # own safeguards, and it actively backfired: it threw
                    # out perfectly good short members ("vāk"/"vāg", 3
                    # chars) while letting a WORSE candidate survive
                    # ("vāgu", 4 chars, a rare proper noun) purely because
                    # it happened to be one character longer -- undoing
                    # the library's own correct (proper-noun-deprioritized)
                    # ranking. Only the structural member-count constraint
                    # is still enforced here.
                    def _member_ok(m, idx, members, dict_verified):
                        if len(m) >= 4:
                            return True
                        if sp.is_upasarga(m, scheme="iast"):
                            return True
                        if idx == 0 and (sp.is_nan_prefix(m, scheme="iast")
                                          or sp.is_len_exempt_particle(m, scheme="iast")):
                            return True
                        # a short (3-char) SECOND member is allowed only
                        # right after a recognized particle first member
                        # (e.g. "ca" + "eva") -- not as a general floor.
                        # (A broader version of this exemption -- letting
                        # ANY dict-verified 2-member candidate through --
                        # was tried and reverted: it fixed "sarvaBUwa"+
                        # "iSu" but reopened "wapa"+"svI" for "wapasvin",
                        # since MW's em-dash convention -- see build_
                        # compound_headwords_from_cdsl -- turns out to
                        # ALSO mark -in taddhita-suffix formations, not
                        # just genuine samasa, undermining the whole-word
                        # gate's ability to catch it independently. Needs
                        # its own -in-suffix recognition pass, analogous
                        # to matup, before this can be safely widened.)
                        if (idx == 1 and len(members) == 2 and len(m) >= 3
                                and sp.is_len_exempt_particle(members[0], scheme="iast")):
                            return True
                        return False

                    multi = [r for r in res
                             if 2 <= len(r["members"]) <= 4
                             and all(_member_ok(m, i, r["members"],
                                                 r["confidence"] == "dictionary-verified")
                                     for i, m in enumerate(r["members"]))]
                    # The nañ (a-/an-) exemption inside _member_ok lets a
                    # 1-2 char first member through purely by matching a
                    # closed-class prefix string -- unlike the upasarga/
                    # particle exemptions (built on candidates that came
                    # from an actually-verified sandhi/dictionary pathway),
                    # a nañ-shaped candidate can also come from an entirely
                    # unverified generic vowel-fusion match, e.g. "asmin"
                    # -> "a"+"smin" (a locative pronoun form that happens
                    # to start with "a", nothing to do with negation).
                    # Require dictionary confirmation specifically for
                    # this exemption, so it only surfaces genuine nañ-
                    # tatpuruṣa compounds (e.g. "an"+"asūyakaḥ", where
                    # "asūyakaḥ" is independently dictionary-verified)
                    # rather than every ordinary "a"-initial word.
                    multi = [r for r in multi
                             if not (sp.is_nan_prefix(r["members"][0], scheme="iast")
                                     and r["confidence"] != "dictionary-verified")]
                    # Drop particle-led candidates when the whole word
                    # already stands on its own (see whole_word_ok above).
                    multi = [r for r in multi
                             if not (whole_word_ok and sp.is_sandhi_particle(r["members"][0], scheme="iast"))]

                    # BROADER whole-word gate: the check above only ever
                    # caught a particle-led false split (a coincidence,
                    # since particles don't semantically merge into
                    # anything). But the same failure happens just as
                    # often with an upasarga-led first member instead --
                    # "vIraH" wrongly torn into "vi"+"IraH", "sukham" into
                    # "su"+"kham", "nyAsaM" into "ni"+"AsaM", "uttamA" into
                    # "ut"+"tamA", "pratijYAm" into "prati"+"jYAm" -- each
                    # piece independently real, dictionary-verified, and
                    # structurally a legal upasarga-compound shape, yet
                    # every one of these whole words is actually a simple,
                    # monomorphemic (or non-compound-derived) word with no
                    # real internal compound structure at all. The
                    # decisive signal MW/Apte itself gives: does that
                    # dictionary's OWN citation form for the whole word
                    # mark it as a documented compound via an em dash (see
                    # build_compound_headwords_from_cdsl) -- "Darma\u2014
                    # jYa", "muni\u2014puMgava" (yes) vs "vIra", "ut-tama",
                    # "ny-Asa" (no -- bare, or only a plain hyphen for
                    # unrelated etymology). When the whole word IS
                    # independently dictionary-backed but is NOT a
                    # documented compound, every generic multi-member
                    # candidate is dropped -- with one narrow exception:
                    # a nan-tatpuruSa candidate (the a-/an- negative
                    # prefix) already carries its own independent
                    # dictionary confirmation of the remainder (see the
                    # nan-samAsa supplementary pass and its confidence
                    # gate above), so it's trusted here regardless of
                    # whether MW happens to mark that specific headword's
                    # citation form with a dash.
                    if whole_word_ok and sp.compound_headwords is not None:
                        stems = list(sp._stem_candidates(tok_wx))
                        is_documented_compound = any(c in sp.compound_headwords for c in stems)
                        # A proper noun overrides the compound marking even
                        # when MW's own citation form happens to use the
                        # em dash (e.g. "SqfgaveraPra", a place name whose
                        # etymology IS genuinely composed of sqfga+vera+
                        # pura) -- for a name used referentially in a verse,
                        # showing its component parts is pedantic rather
                        # than useful, unlike an ordinary transparent
                        # compound like dharmajYa. See build_proper_nouns_
                        # from_cdsl for how membership here is decided.
                        is_proper_noun = bool(sp.proper_nouns) and any(
                            c in sp.proper_nouns for c in stems)
                        if is_proper_noun or not is_documented_compound:
                            multi = [r for r in multi
                                     if sp.is_nan_prefix(r["members"][0], scheme="iast")
                                     and r["confidence"] == "dictionary-verified"]

                    # Targeted override: the >=4-char floor above exists to
                    # block short coincidental matches (without it,
                    # "vidvān"/"tapasvī"/etc. flood back in as wrongly
                    # "split" participles/suffixed adjectives -- verified
                    # by testing). But it has one real failure mode: it
                    # can let a WORSE candidate survive purely for being
                    # one character longer than a BETTER one it excludes
                    # -- e.g. "vāgvidāṃ" filtered down to the rare-proper-
                    # noun "vāgu"+"idāṃ" (4 chars) while sp.split()'s own
                    # proper-noun-aware ranking correctly prefers
                    # "vāk"+"vidāṃ" (3 chars) but that got floor-filtered
                    # out. So: if the filtered top choice contains a
                    # proper noun and sp.split()'s own UNFILTERED top
                    # choice doesn't, trust sp.split()'s ranking instead.
                    if multi and sp.proper_nouns:
                        def _has_pn(r):
                            return any(sp._to_wx(m, sanscript.IAST) in sp.proper_nouns
                                       for m in r["members"])
                        unfiltered_top = res[0] if res and 2 <= len(res[0]["members"]) <= 3 else None
                        if (unfiltered_top and _has_pn(multi[0])
                                and not _has_pn(unfiltered_top)):
                            multi = [unfiltered_top] + [r for r in multi if r != unfiltered_top]
                    if not multi:
                        if do_samasa and len(tok_clean) >= 5:
                            stats["samasa_attempted"] += 1
                            v_samasa_attempted += 1
                            stats["samasa_none_found"] += 1
                        continue
                    best = multi[0]
                    if sp.is_sandhi_particle(best["members"][0], scheme="iast"):
                        if do_sandhi:
                            fused_sandhi[tok] = best
                            stats["sandhi_total"] += 1
                            v_sandhi_total += 1
                            if best["confidence"] == "dictionary-verified":
                                stats["sandhi_confirmed"] += 1
                                v_sandhi_conf += 1
                            else:
                                stats["sandhi_phonology_only"] += 1
                    elif do_samasa and len(tok_clean) >= 5:
                        stats["samasa_attempted"] += 1
                        v_samasa_attempted += 1
                        samasa_results[tok] = best
                        v_samasa_found += 1
                        if best["confidence"] == "dictionary-verified":
                            stats["samasa_dict_verified"] += 1
                        else:
                            stats["samasa_phonology_only"] += 1
            if do_sandhi:
                line_entry["fused_sandhi"] = fused_sandhi
            if do_samasa:
                line_entry["samasa"] = samasa_results
            line_entry["pratyaya"] = pratyaya_results
            line_entry["matup"] = matup_results

            verse_entry["lines"].append(line_entry)
        report.append(verse_entry)
        stats["per_verse"].append(
            (verse_label, v_sandhi_conf, v_sandhi_total, v_samasa_found, v_samasa_attempted))

    return report, stats


def write_verse_report(report, mode, out_path):
    do_sandhi = mode in ("sandhi", "both")
    do_samasa = mode in ("samasa", "both")
    lines_out = [f"# Sandhi/Samasa Analysis ({mode})", ""]
    for v in report:
        lines_out.append(f"## Verse {v['verse']}")
        lines_out.append("")
        for line in v["lines"]:
            lines_out.append(f"**{line['text']}**")
            lines_out.append("")
            if do_sandhi:
                fused = line.get("fused_sandhi", {})
                restored, last_right = [], None
                for j in line["junctions"]:
                    t1, t2 = j["pair"]
                    if t1 in fused:
                        r = fused[t1]
                        tag = "\u2713" if r["confidence"] == "dictionary-verified" else "\u25e6"
                        restored.append(f"{tag}[" + " + ".join(r["members"]) + "]")
                    else:
                        best = j["candidates"][0] if j["candidates"] else None
                        if best and best["left"] != t1:
                            tag = "\u2713" if best["dict_backed"] else "\u25e6"
                            restored.append(f"{tag}{best['left']}")
                        else:
                            restored.append(t1)
                    last_right = j["candidates"][0]["right"] if j["candidates"] else t2
                final_tok = line["tokens"][-1] if line["tokens"] else ""
                if final_tok in fused:
                    r = fused[final_tok]
                    tag = "\u2713" if r["confidence"] == "dictionary-verified" else "\u25e6"
                    restored.append(f"{tag}[" + " + ".join(r["members"]) + "]")
                elif last_right is not None and last_right != final_tok:
                    restored.append(f"\u25e6{last_right}")
                else:
                    restored.append(final_tok)
                lines_out.append("*Sandhi split:*")
                lines_out.append("  " + " ".join(restored))
                lines_out.append("")
            if do_samasa and line.get("samasa"):
                lines_out.append("*Samasa split:*")
                for tok, r in line["samasa"].items():
                    tag = "\u2713" if r["confidence"] == "dictionary-verified" else "\u25e6"
                    lines_out.append(f"  - {tag} `{tok}` \u2192 " + " + ".join(r["members"]))
                lines_out.append("")
            if line.get("pratyaya"):
                lines_out.append("*Pratyaya (verb-suffix) resolution:*")
                for tok, p in line["pratyaya"].items():
                    if p.get("ambiguous"):
                        tag = "\u25e6"
                        desc = f"root: {' / '.join(p['root'])} (ambiguous) + {p['pratyaya']}"
                    elif p["resolved"]:
                        tag = "\u2713"
                        desc = f"{p['root']} + {p['pratyaya']}"
                    else:
                        tag = "\u25e6"
                        desc = f"{p['pratyaya']} recognized, root not resolved"
                    lines_out.append(f"  - {tag} `{tok}` \u2192 {desc}  ({p['gloss']})")
                lines_out.append("")
            if line.get("matup"):
                lines_out.append("*Matup (possessive-suffix) resolution:*")
                for tok, mt in line["matup"].items():
                    if mt["resolved"]:
                        tag = "\u2713"
                        desc = f"{mt['stem']} + {mt['pratyaya']}"
                    else:
                        tag = "\u25e6"
                        desc = f"{mt['pratyaya']} recognized, stem not resolved"
                    lines_out.append(f"  - {tag} `{tok}` \u2192 {desc}  ({mt['gloss']})")
                lines_out.append("")
        lines_out.append("")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines_out))


def write_summary_report(stats, mode, out_path):
    do_sandhi = mode in ("sandhi", "both")
    do_samasa = mode in ("samasa", "both")

    def pct(n, d):
        return f"{100 * n / d:.1f}%" if d else "n/a"

    lines_out = ["# Summary Report", ""]
    lines_out.append(f"Verses processed: {stats['verses']} "
                      f"({stats['lines']} pada-lines)")
    lines_out.append("")

    if do_sandhi:
        t = stats["sandhi_total"]
        lines_out.append("## Sandhi split")
        lines_out.append(f"Junctions analyzed: {t}")
        lines_out.append(f"- \u2713 Restored, dictionary-confirmed: "
                          f"{stats['sandhi_confirmed']} ({pct(stats['sandhi_confirmed'], t)})")
        lines_out.append(f"- \u25e6 Restored, phonology-only (unconfirmed): "
                          f"{stats['sandhi_phonology_only']} ({pct(stats['sandhi_phonology_only'], t)})")
        lines_out.append(f"- No change needed (already citation form): "
                          f"{stats['sandhi_unchanged']} ({pct(stats['sandhi_unchanged'], t)})")
        lines_out.append("")

    if do_samasa:
        a = stats["samasa_attempted"]
        lines_out.append("## Samasa split")
        lines_out.append(f"Tokens attempted (length >= 5 chars): {a}")
        lines_out.append(f"- \u2713 Decomposed, dictionary-verified: "
                          f"{stats['samasa_dict_verified']} ({pct(stats['samasa_dict_verified'], a)})")
        lines_out.append(f"- \u25e6 Decomposed, phonology-only: "
                          f"{stats['samasa_phonology_only']} ({pct(stats['samasa_phonology_only'], a)})")
        lines_out.append(f"- No compound decomposition found: "
                          f"{stats['samasa_none_found']} ({pct(stats['samasa_none_found'], a)})")
        lines_out.append("")

    p = stats["pratyaya_attempted"]
    if p:
        lines_out.append("## Pratyaya (verb-suffix) resolution")
        lines_out.append(f"Verb-ending tokens recognized: {p}")
        lines_out.append(f"- \u2713 Resolved to a verified root: "
                          f"{stats['pratyaya_resolved']} ({pct(stats['pratyaya_resolved'], p)})")
        lines_out.append(f"- \u25e6 Ambiguous (2+ roots equally explain it): "
                          f"{stats['pratyaya_ambiguous']} ({pct(stats['pratyaya_ambiguous'], p)})")
        lines_out.append(f"- \u25e6 Recognized but unresolved (likely needs guNa/vRddhi "
                          f"ablaut reversal): "
                          f"{stats['pratyaya_unresolved']} ({pct(stats['pratyaya_unresolved'], p)})")
        lines_out.append("")

    mt = stats["matup_attempted"]
    if mt:
        lines_out.append("## Matup (possessive-suffix) resolution")
        lines_out.append(f"'-vAn'/'-mAn'-ending tokens recognized: {mt}")
        lines_out.append(f"- \u2713 Resolved to a verified stem: "
                          f"{stats['matup_resolved']} ({pct(stats['matup_resolved'], mt)})")
        lines_out.append(f"- \u25e6 Recognized but stem not resolved: "
                          f"{stats['matup_unresolved']} ({pct(stats['matup_unresolved'], mt)})")
        lines_out.append("")

    lines_out.append("## Per-verse breakdown")
    lines_out.append("")
    header = "| Verse |"
    sep = "|---|"
    if do_sandhi:
        header += " Sandhi confirmed/total |"
        sep += "---|"
    if do_samasa:
        header += " Samasa found/attempted |"
        sep += "---|"
    lines_out.append(header)
    lines_out.append(sep)
    for (label, s_conf, s_tot, sm_found, sm_att) in stats["per_verse"]:
        row = f"| {label} |"
        if do_sandhi:
            row += f" {s_conf}/{s_tot} |"
        if do_samasa:
            row += f" {sm_found}/{sm_att} |"
        lines_out.append(row)

    lines_out.append("")
    lines_out.append(
        "**Legend:** \u2713 = dictionary-confirmed (high confidence). "
        "\u25e6 = phonologically valid but not independently confirmed "
        "(typically a finite verb form, or an inflection pattern the "
        "dictionary doesn't index) -- treat as lower confidence, worth "
        "a manual check."
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines_out))


def write_verse_excel(report, sp, out_path):
    """
    Write the same per-verse sandhi/samasa findings as write_verse_report,
    but as an .xlsx workbook with one row-block per verse:
      Col A: Shloka (moola text, one merged cell spanning the block)
      Col B: Sandhi Split (one row per restored junction/fused-particle
              split found in that verse)
      Col C: Word Meaning (gloss of the restored word(s) in that row)
      Col D: Samasa (one row per compound split found in that verse)
      Col E: Samasa Word Meanings (glosses of that row's compound
              members, joined into one cell)
    Sandhi and samasa counts differ per verse, so a block's row count is
    whichever list is longer; the shorter column is left blank for the
    remaining rows. Requires openpyxl (pip install openpyxl).
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Sandhi-Samasa"

    headers = ["Shloka", "Sandhi Split", "Word Meaning", "Samasa", "Samasa Word Meanings"]
    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = Font(name="Arial", bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical="top")

    body_font = Font(name="Arial")
    wrap_top = Alignment(wrap_text=True, vertical="top", horizontal="left")

    row_cursor = 2
    for v in report:
        moola_text = "\n".join(line["text"] for line in v["lines"])

        sandhi_rows = []
        for line in v["lines"]:
            fused = line.get("fused_sandhi", {})
            for j in line.get("junctions", []):
                t1, t2 = j["pair"]
                if t1 in fused:
                    r = fused[t1]
                    tag = "\u2713" if r["confidence"] == "dictionary-verified" else "\u25e6"
                    display = f"{tag} {t1} \u2192 " + " + ".join(r["members"])
                    meaning = "; ".join(
                        f"{m}: {get_gloss(sp, m) or '?'}" for m in r["members"])
                    sandhi_rows.append((display, meaning))
                    continue
                best = j["candidates"][0] if j["candidates"] else None
                if best and best["left"] != t1:
                    tag = "\u2713" if best["dict_backed"] else "\u25e6"
                    display = f"{tag} {t1} \u2192 {best['left']}"
                    meaning = get_gloss(sp, best["left"]) or ""
                    sandhi_rows.append((display, meaning))

        samasa_rows = []
        for line in v["lines"]:
            for tok, r in line.get("samasa", {}).items():
                tag = "\u2713" if r["confidence"] == "dictionary-verified" else "\u25e6"
                display = f"{tag} {tok} \u2192 " + " + ".join(r["members"])
                meaning = "; ".join(
                    f"{m}: {get_gloss(sp, m) or '?'}" for m in r["members"])
                samasa_rows.append((display, meaning))
            for tok, mt in line.get("matup", {}).items():
                tag = "\u2713" if mt["resolved"] else "\u25e6"
                stem = mt["stem"] or "?"
                display = f"{tag} {tok} \u2192 {stem} + {mt['pratyaya']}  (matup, not a samasa)"
                meaning = f"{stem}: {get_gloss(sp, stem) or '?'}" if mt["stem"] else ""
                samasa_rows.append((display, meaning))

        block_len = max(len(sandhi_rows), len(samasa_rows), 1)
        start_row = row_cursor
        end_row = row_cursor + block_len - 1

        ws.cell(row=start_row, column=1, value=moola_text)
        if block_len > 1:
            ws.merge_cells(start_row=start_row, start_column=1,
                            end_row=end_row, end_column=1)

        for i in range(block_len):
            r = start_row + i
            if i < len(sandhi_rows):
                ws.cell(row=r, column=2, value=sandhi_rows[i][0])
                ws.cell(row=r, column=3, value=sandhi_rows[i][1])
            if i < len(samasa_rows):
                ws.cell(row=r, column=4, value=samasa_rows[i][0])
                ws.cell(row=r, column=5, value=samasa_rows[i][1])
            for col in range(1, 6):
                cell = ws.cell(row=r, column=col)
                cell.font = body_font
                cell.alignment = wrap_top

        row_cursor = end_row + 1

    legend_row = row_cursor + 1
    legend = ("Legend: \u2713 = dictionary-confirmed (high confidence). "
              "\u25e6 = phonologically valid but not independently confirmed -- "
              "treat as lower confidence, worth a manual check.")
    ws.cell(row=legend_row, column=1, value=legend).font = Font(name="Arial", italic=True)
    ws.merge_cells(start_row=legend_row, start_column=1, end_row=legend_row, end_column=5)

    widths = {1: 30, 2: 28, 3: 40, 4: 28, 5: 45}
    for col, w in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = w

    wb.save(out_path)


def _build_splitter_from_args(args, verbose_stream=sys.stderr):
    """
    Shared dictionary-loading logic for all three CLI entry points
    (single-word, --karaka-line, --corpus). Priority: --sqlite-dict >
    --cdsl > --dict, so a single flag lets every mode validate against
    the same real dictionary sandhi_splitter.py already uses (see
    `build_dictionary_from_sqlite`) instead of each mode repeating its
    own copy of this loading logic (previously duplicated three times,
    independently, in this file).
    """
    if getattr(args, "sqlite_dict", None):
        sp = SamasaSplitter()
        n = sp.load_sqlite_dictionary(args.sqlite_dict)
        print(f"[loaded {n} unique stems from {args.sqlite_dict}]", file=verbose_stream)
        return sp
    if args.cdsl:
        sp = SamasaSplitter()
        n = sp.load_cdsl_dictionaries(args.cdsl)
        print(f"[loaded {n} unique stems from {', '.join(args.cdsl)}]", file=verbose_stream)
        nr = sp.load_verb_roots(args.cdsl)
        print(f"[loaded {nr} verified verb roots]", file=verbose_stream)
        nn = sp.load_proper_nouns(args.cdsl)
        print(f"[loaded {nn} proper-noun entries (deprioritized, not excluded)]", file=verbose_stream)
        nc = sp.load_compound_headwords(args.cdsl)
        print(f"[loaded {nc} documented-compound headwords]", file=verbose_stream)
        if getattr(args, "out_xlsx", None):
            ng = sp.load_glosses(args.cdsl)
            print(f"[loaded {ng} glosses]", file=verbose_stream)
        return sp
    dict_scheme = getattr(sanscript, args.dict_scheme.upper(), sanscript.IAST)
    return SamasaSplitter(dictionary_path=args.dictionary, dict_scheme=dict_scheme)


def _run_corpus_mode(args):
    verses = parse_gretil_verses(
        args.corpus, kanda=args.kanda, sarga=args.sarga,
        verse_start=args.verse_start, verse_end=args.verse_end,
        limit_lines=args.limit_lines,
    )
    if not verses:
        sys.exit("No verses matched the given kanda/sarga/verse-range filters.")

    sp = _build_splitter_from_args(args)

    report, stats = analyze_verse_corpus(sp, verses, mode=args.mode)

    out_path = args.out or "report.md"
    summary_path = args.summary or "summary.md"
    write_verse_report(report, args.mode, out_path)
    write_summary_report(stats, args.mode, summary_path)
    print(f"[wrote {out_path}]", file=sys.stderr)
    print(f"[wrote {summary_path}]", file=sys.stderr)

    if args.out_xlsx:
        write_verse_excel(report, sp, args.out_xlsx)
        print(f"[wrote {args.out_xlsx}]", file=sys.stderr)


# --------------------------------------------------------------------------- #
def _demo():
    """Runs against a handful of real compounds from Ramayana Balakanda Sarga 1."""
    demo_words = [
        "kambugrīvo",
        "ikṣvākuvaṃśaprabhavo",
        "śatrunibarhaṇaḥ",
        "mahābāhuḥ",
        "rāmāyaṇam",
    ]
    print("No --dict supplied: running phonology-only demo on real Sarga-1 "
          "compounds. Every result is a grammatically LEGAL split point; "
          "only some are the semantically correct one (marked candidates, "
          "not verdicts).")
    sp = SamasaSplitter()
    for w in demo_words:
        sp.split(w, scheme="iast")


def main():
    parser = argparse.ArgumentParser(description="Rule-based Sanskrit samasa (compound) splitter.")
    parser.add_argument("word", nargs="?", help="Compound word to split (single-word mode)")
    parser.add_argument("--scheme", default="iast",
                         help="Transliteration scheme of the input word (iast, devanagari, wx, ...). Default: iast")
    parser.add_argument("--dict", dest="dictionary", default=None,
                         help="Optional plain wordlist file (one stem per line) to validate/rank splits and enable recursion")
    parser.add_argument("--dict-scheme", default="iast",
                         help="Transliteration scheme used inside the plain wordlist file. Default: iast")
    parser.add_argument("--cdsl", nargs="+", default=None,
                         help="One or more raw CDSL source files (mw.txt, ap90.txt) to use as the dictionary directly (SLP1 headwords, auto-converted)")
    parser.add_argument("--sqlite-dict", dest="sqlite_dict", default=None,
                         help="Path to apte_dictionary.sqlite (the sibling sandhi/ tool's own "
                              "verified SKD+Apte dictionary) to use as the dictionary directly. "
                              "Takes priority over --cdsl/--dict when given -- this is what lets "
                              "this tool and sandhi_splitter.py validate against the same words.")
    parser.add_argument("--karaka-line", default=None,
                         help="Run the karaka (case-role) heuristic on one line/verse of "
                              "space-separated Sanskrit text and print the breakdown, "
                              "then exit. Bypasses single-word/demo/corpus modes.")

    # --- Corpus mode: analyze a range of verses from a GRETIL-style text file ---
    corpus = parser.add_argument_group(
        "corpus mode",
        "Pass --corpus to switch from single-word mode to analyzing a range "
        "of verses from a GRETIL-style Ramayana-formatted text file.")
    corpus.add_argument("--corpus", default=None,
                         help="Path to a GRETIL-style text file (has a '# Text' marker, "
                              "each pada-line tagged '...text... R_KANDA,SARGA.VERSE')")
    corpus.add_argument("--kanda", type=int, default=None, help="Restrict to this kanda number")
    corpus.add_argument("--sarga", type=int, default=None, help="Restrict to this sarga number")
    corpus.add_argument("--verse-start", type=int, default=None,
                         help="First verse number to include (within the selected sarga)")
    corpus.add_argument("--verse-end", type=int, default=None,
                         help="Last verse number to include (within the selected sarga)")
    corpus.add_argument("--limit-lines", type=int, default=None,
                         help="Cap the total number of pada-lines processed, applied after "
                              "the kanda/sarga/verse filters")
    corpus.add_argument("--mode", choices=["sandhi", "samasa", "both"], default="both",
                         help="Which analysis to run. Default: both")
    corpus.add_argument("--out", default=None,
                         help="Path for the detailed verse-by-verse report. Default: report.md")
    corpus.add_argument("--summary", default=None,
                         help="Path for the separate success/failure summary report. "
                              "Default: summary.md")
    corpus.add_argument("--out-xlsx", default=None,
                         help="Also write an .xlsx workbook (Shloka | Sandhi Split | "
                              "Word Meaning | Samasa | Samasa Word Meanings, one merged "
                              "row-block per verse). Requires openpyxl (pip install openpyxl).")

    args = parser.parse_args()

    if args.karaka_line:
        sp = _build_splitter_from_args(args, verbose_stream=sys.stdout)
        tokens = [w for w in re.split(r"\s+", args.karaka_line.strip()) if w]
        restored = restore_tokens(sp, tokens, scheme=args.scheme)
        if restored != tokens:
            print("[sandhi-restored: " + " ".join(restored) + "]")
        entries = analyze_karaka(sp, restored, scheme=args.scheme)
        print(f"\n=== karaka analysis: {args.karaka_line} ===")
        for e in entries:
            case_str = ""
            if e["case"]:
                case, number, note = e["case"]
                case_str = f"  [{case}, {number}]"
                if note:
                    case_str += f"  ({note})"
            print(f"  {e['token']:<20} {e['role'] or '-':<40}{case_str}")
        return

    if args.corpus:
        _run_corpus_mode(args)
        return

    if not args.word:
        _demo()
        return

    sp = _build_splitter_from_args(args, verbose_stream=sys.stdout)
    sp.split(args.word, scheme=args.scheme)


if __name__ == "__main__":
    main()
