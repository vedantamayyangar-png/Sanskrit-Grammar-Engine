#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
samasa_classifier.py — decide whether a (sandhi-restored) pada is a samāsa, name its members, and
guess its type with a stated reason.

Added in the Sarga-1 gold-standard pass (2026-09-23). Scoring samasa_splitter.py's output against
the hand analysis of all 79 verses showed two separate problems:

  * detection — only 54% of real compounds were found, and 41% of the words it flagged were not
    compounds at all (संयुगे → सं+युगे, वीर्ये → वि+इर्ये, ददर्श → दद+ऋश …): an inflected word was
    being split before its ending was removed;
  * type — 90% of the compounds it did find were labelled "uncertain".

This module works on the prātipadika that pada_analyser.py recovers (ending already stripped,
validated against MW + Apte + SKD), splits it with the analyser's lexicon-checked compound
splitter, and applies explicit guards and typing rules, each with its Pāṇinian basis:

  guards   (a) a first member that is an upasarga (प्र, परि, सम् …) makes a prādi/gati form
               that the treatise convention lists under उपसर्गः, not समासः;
           (b) a whole stem that is itself a lexicon headword is kept whole when its first
               "member" is only a short prefix (स-मुद्र, स-दृश, स-हस्र are not compounds);
           (c) a "last member" that is really a suffix (-वत्, -मत्, -इत, -अन …) is rejected;
           (d) kṛdanta participle stems (अनुपालयत्, वसत्) are never split.
  typing   नञ्-पूर्वपदः → नञ्तत्पुरुषः / नञ्बहुव्रीहिः (2.2.6 नञ्)
           स(ह)-पूर्वपदः → बहुव्रीहिः (2.2.28 तेन सहेति तुल्ययोगे)
           सङ्ख्या-पूर्वपदः → द्विगुः (2.1.52 सङ्ख्यापूर्वो द्विगुः)
           कृत्-उत्तरपदम् (-ज, -ज्ञ, -ग, -द, -चर, -घ्न, -स्थ …) → उपपदतत्पुरुषः (2.2.19 उपपदमतिङ्)
           लिङ्गव्यत्ययः: last member n./f. but the compound declines masculine → बहुव्रीहिः
               (2.2.24 अनेकमन्यपदार्थे — an exocentric compound takes its referent's gender)
           महा/सु/दुर्-पूर्वपदः in a masculine nominative epithet → बहुव्रीहिः (guess, flagged)
           adjective + noun → कर्मधारयः (2.1.57 विशेषणं विशेष्येण बहुलम्)
           otherwise → तत्पुरुषः (षष्ठी — 2.2.8 षष्ठी), flagged as default
Every result carries `reason`, and `confidence` = "rule" or "default".
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MORPH = os.path.normpath(os.path.join(HERE, "..", "morphology"))
if MORPH not in sys.path:
    sys.path.insert(0, MORPH)

UPASARGA_FIRST = {"pra", "parA", "apa", "sam", "saM", "anu", "ava", "nis", "nir", "dus", "vi", "A",
                  "ni", "aDi", "api", "ati", "ud", "ut", "uc", "aBi", "prati", "pari", "upa"}
PREFIX_LIKE = {"sa", "su", "a", "an", "ku", "vi", "dur", "dus", "nir", "nis", "sam", "saM", "A"}
SUFFIX_LIKE_LAST = {"vat", "avat", "mat", "at", "ita", "ta", "ana", "aka", "ika", "in", "tva", "tA",
                    "maya", "vin", "ya", "ad", "ar", "ak", "an", "ant", "ati", "anta", "aRa", "ara",
                    "ira", "ura", "ina", "Ana", "mAna", "Ayana"}
UPAPADA_FINALS = {"vit", "vAdin", "ja", "jYa", "ga", "da", "cara", "Gna", "sTa", "pa", "kara", "hara", "BU", "ha",
                  "jit", "kft", "vid", "dfS", "sad", "dA", "Da", "Ra", "nuga", "anuga"}
NUMERALS = {"eka", "dvi", "tri", "catur", "paYca", "zaz", "sapta", "azwa", "nava", "daSa", "Sata",
            "sahasra", "trayas", "ekAdaSa", "dvAdaSa"}
EPITHET_FIRST = {"mahA", "su", "dur", "dus"}
MANNER_FIRST = {"evaM", "evam", "kiM", "kim", "itTaM", "tAvat", "yAvat"}   # indeclinable first member: evaṃ-vidha, kiṃ-rūpa
# closed list of common adjectives that open compounds (visheshana-purvapada)
COMMON_ADJECTIVES = set("""mahA mahat maha sarva parama satya dfQa SuBa viSAla vipula pIna snigDa sama SrezWa
ugra Gora citra eka uttama nIla rakta Sveta kfzRa dIrGa hrasva bahu alpa nava purARa puRya pApa priya
SIGra aSeza nitya divya pUrRa SuDa Suci vIra DIra ramya sundara kamala amita aneka su dur""".split())
# nouns denoting a person/being: a compound ending in one of these names that being itself
# (karmadhāraya: mahā-kapi "great monkey"), not a possessor (bahuvrīhi)
PERSON_NOUNS = set("""kapi rAkzasa fzi rAjan rAja vIra muni nara jana deva puruza vAnara hari sura asura
brAhmaRa kzatriya dvija nfpa BUpa pati putra sUnu kanyA strI nArI kavi guru Sizya BrAtf pitf mAtf""".split())
# possessable attributes / body parts: an epithet ending in one of these describes a possessor
ATTRIBUTE_NOUNS = set("""aNga akza aMsa bAhu grIva grIvA Atman vIrya bala tejas Ayus saNgraha vikrama parAkrama darSana
vrata varRa lakzaRa kroDa roza izvAsa uras Siras lalAwa hanu jatru netra mukha kara pAda vakzas guRa
prabhava praBava pramuKa mati buddhi Buddhi yaSas kIrti rUpa vezA veza kAnti dyuti sattva mana manas
citta hfdaya vAkya vacana saMDA ASaya""".split())
# second members meaning "equal to / like / joined with": the compound is a tatpuruṣa of the
# instrumental of comparison or accompaniment (tulyārthair atulopamābhyāṁ tṛtīyā 2.3.72)
TULYA_LAST = {"sama", "sadfSa", "saMnIBa", "saMniBa", "saMkASa", "tulya", "sahita", "yukta", "anvita",
              "upeta", "saMpanna", "sampanna", "Adya"}


class SamasaClassifier:
    def __init__(self, analyser=None):
        if analyser is None:
            from pada_analyser import PadaAnalyser
            analyser = PadaAnalyser()
        self.pa = analyser
        self.lex = analyser.lex

    def _nominal(self, s):
        t = self.lex.get(s, "")
        return any(c in t for c in "mfna")

    def members_of(self, stem):
        """Guarded compound split of a prātipadika (SLP1). Returns member list or None."""
        pa = self.pa
        if len(stem) < 5 or pa._participle(stem):
            return None
        m = pa.compound_split(stem)
        if not m or len(m) < 2:
            return None
        first, last = m[0], m[-1]
        if first in UPASARGA_FIRST:
            return None
        if last in SUFFIX_LIKE_LAST or any(x in SUFFIX_LIKE_LAST for x in m[1:]):
            return None
        in_lex = stem in self.lex
        if in_lex and (first in PREFIX_LIKE or len(first) <= 2):
            if not (first in ("a", "an", "su", "dur", "dus") and len(last) >= 4 and self._nominal(last)):
                return None             # lexicalised prefix word: समुद्र, सदृश, सहस्र (नञ् kept)
        epithet_person = first in COMMON_ADJECTIVES and last in PERSON_NOUNS      # mahā-ṛṣi, parama-ṛṣi
        if in_lex and not epithet_person and any(len(x) < 4 and x not in UPAPADA_FINALS and x not in PREFIX_LIKE and
                                                 x not in NUMERALS and x not in PERSON_NOUNS for x in m):
            return None                 # a lexicalised word cut into short scraps: नार+अद
        if any(len(x) < 3 and x not in PREFIX_LIKE for x in m):    # (fzi has 3 letters, so unaffected)
            return None
        # A short non-lexicon first member is a junction artefact, not a word: DarmaraTa → Das + marata
        # (r/s undone at the cut). Real first members are attested in the lexicon.
        if any(x not in self.lex and len(x) <= 4 and x not in PREFIX_LIKE and x not in NUMERALS for x in m[:-1]):
            return None
        return m

    def _is_adjective_member(self, m):
        return m in COMMON_ADJECTIVES or bool(self.pa._participle(m) and self.pa._participle(m)[1] == "क्त")

    def classify(self, members, gender=None, case=None, number=None):
        """Type guess for member list (SLP1). gender/case/number: the compound's own reading."""
        first, last = members[0], members[-1]
        lt = self.lex.get(last, "")
        masc_or_fem = bool(gender) and (gender.startswith("पुं") or gender.startswith("स्त्री"))
        attribute_last = last not in PERSON_NOUNS
        if first in ("a", "an"):
            if masc_or_fem and attribute_last and ("n" in lt or "f" in lt) and not self._nominal_agent(last):
                return "नञ्बहुव्रीहिः", "नञ्-पूर्वपदः; अन्यपदार्थे विशेषणम् (नञोऽस्त्यर्थानां वाच्यो वा चोत्तरपदलोपः)", "rule"
            return "नञ्तत्पुरुषः", "नञ्-पूर्वपदः (नञ् 2.2.6)", "rule"
        if first in MANNER_FIRST:
            return "बहुव्रीहिः", "अव्यय-पूर्वपदम् (एवम्/किम्…) + उत्तरपदम्, अन्यपदार्थे (अनेकमन्यपदार्थे 2.2.24)", "rule"
        if first in ("sa", "saha"):
            return "बहुव्रीहिः", "स(ह)-पूर्वपदः (तेन सहेति तुल्ययोगे 2.2.28)", "rule"
        if last in UPAPADA_FINALS or (last.endswith(("jYa", "cara", "Gna", "ja")) and len(last) <= 6):
            return "उपपदतत्पुरुषः", "कृदन्त-उत्तरपदम् (उपपदमतिङ् 2.2.19)", "rule"
        if first in NUMERALS:
            if last in NUMERALS:
                return "द्वन्द्वः", "सङ्ख्या + सङ्ख्या (चार्थे द्वन्द्वः 2.2.29)", "rule"
            if masc_or_fem:
                return "बहुव्रीहिः", "सङ्ख्यापूर्वपदः अन्यपदार्थे (अनेकमन्यपदार्थे 2.2.24)", "rule"
            return "द्विगुः", "सङ्ख्या-पूर्वपदः समाहारे (सङ्ख्यापूर्वो द्विगुः 2.1.52)", "rule"
        last_kta = bool(self.pa._participle(last) and self.pa._participle(last)[1] == "क्त")
        if last in TULYA_LAST or (last_kta and (len(members) > 2 or not self._is_adjective_member(first))):
            return "तत्पुरुषः", "उत्तरपदं कृदन्तम्/तुल्यार्थकम् — तृतीयातत्पुरुषः (कर्तृकरणे कृता बहुलम् 2.1.32)", "rule"
        if last.endswith("ana") and gender and gender.startswith("पुं") and not self._is_adjective_member(first):
            return "तत्पुरुषः", "कर्तृ-अर्थे ल्युडन्त-उत्तरपदम् — षष्ठीतत्पुरुषः (कर्तृकर्मणोः कृति 2.3.65)", "rule"
        if self._is_adjective_member(first) or first in EPITHET_FIRST:
            if (masc_or_fem or last in ATTRIBUTE_NOUNS) and (last in ATTRIBUTE_NOUNS or (attribute_last and not self._nominal_agent(last)
                                                            and "m" not in lt)):
                return "बहुव्रीहिः", "विशेषण-पूर्वपदम् + गुण/अवयव-उत्तरपदम्, अन्यपदार्थे (अनेकमन्यपदार्थे 2.2.24)", "guess"
            return "कर्मधारयः", "विशेषण-पूर्वपदम् (विशेषणं विशेष्येण बहुलम् 2.1.57)", "rule"
        g = "m" if (gender or "").startswith("पुं") else "f" if (gender or "").startswith("स्त्री") else None
        if masc_or_fem and (last in ATTRIBUTE_NOUNS or (g and any(x in lt for x in "mfn") and g not in lt)):
            return "बहुव्रीहिः", "गुण/अवयव-उत्तरपदम्, समासः अन्यपदार्थस्य विशेषणम् (अनेकमन्यपदार्थे 2.2.24)", "guess"
        return "तत्पुरुषः", "पूर्वपदं विशेष्यम् — षष्ठीतत्पुरुषः अनुमितः (षष्ठी 2.2.8)", "default"

    def _nominal_agent(self, m):
        return m.endswith(("aka", "tf", "in", "ana"))

    def analyse(self, iast_or_deva, scheme="iast"):
        """Full decision for one pada: {'members': [...deva], 'type', 'reason', 'confidence'} or None."""
        from pada_analyser import slp1_to_deva
        from transliterate import deva_to_slp1
        rd = self.pa.analyse(iast_or_deva, scheme=scheme, max_readings=1)
        if not rd or rd[0]["type"] != "noun":
            return None
        r = rd[0]
        stem = deva_to_slp1(r["stem"])
        m = self.members_of(stem)
        if not m and stem.endswith("A") and r.get("case") == 1 and len(stem) > 4:
            # pada_analyser reads the visarga nominative mahātejāḥ as a feminine ā-stem; the
            # masculine/neuter stem is -as (mahātejas), which is what the compound is built on.
            m = self.members_of(stem[:-1] + "as")
        if not m:
            return None
        from indic_transliteration import sanscript as _s
        surface = _s.transliterate(iast_or_deva, _s.IAST, _s.DEVANAGARI) if scheme == "iast" else iast_or_deva
        # (1) Finite passive/middle verb, not a compound: विद्यते, महीयते, दृश्यते are
        #     विद् / मही / दृश् + the -यते ending; the noun-stem reading "…यत" must not be a member.
        if m[-1] in ("yata", "yatin") and surface.endswith(("ते", "ति")):     # m is SLP1
            return None
        # (2) nañ-tatpuruṣa: अ + consonant-initial member yields a surface beginning with अ, never आ.
        #     So आत्मा / आहवे are not अ + त्मन् / अ + हव (they are the lexical words आत्मन् / आहव).
        if m[0] in ("a", "an") and surface.startswith("आ") and m[1][:1] not in "aAiIuUfFxXeEoO":
            return None
        typ, reason, conf = self.classify(m, r.get("gender"), r.get("case"), r.get("num"))
        return {"members": [slp1_to_deva(x) for x in m], "type": typ, "reason": reason,
                "confidence": conf, "stem": r["stem"]}


if __name__ == "__main__":
    sc = SamasaClassifier()
    for w in sys.argv[1:]:
        print(w, sc.analyse(w, scheme="deva"))
