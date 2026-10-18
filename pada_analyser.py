#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pada_analyser.py — rule-based morphological analysis of ONE Sanskrit pada (word form).

Given a citation-form pada (i.e. AFTER external sandhi has been undone — what
combined_splitter.analyze_pada_line() returns as `citation_form`), return its readings, best
first:

    noun / pronoun / numeral : prātipadika, vibhakti (1-8), vacana, liṅga, model word (शब्दवत्)
    finite verb              : dhātu (with gaṇa, pada, artha from Dhatu-Manjari), upasarga(s),
                               lakāra, puruṣa, vacana, pada
    indeclinable             : avyaya (closed list), or kṛdanta-avyaya (क्त्वा / ल्यप् / तुमुन्),
                               or taddhita-avyaya (-वत्, -तः, -त्र, -दा, -शः)

Every reading is built ONLY from project files — nothing is looked up online:

    04_Laghu_Siddhanta_Kaumudi/sabdamanjari_vibhakti_tables.json  185 declension paradigms (page-cited)
    04_Laghu_Siddhanta_Kaumudi/Dhatu-Lakara.json                  30 full verb paradigms (10 lakāras)
    04_Laghu_Siddhanta_Kaumudi/Dhatu-Manjari.json                 2,259 roots (gaṇa, pada, artha)
    05_Sanskrit_Dictionaries/lexicon_index.json                   241k headwords (MW + Apte + SKD),
                                                                  built by build_lexicon_index.py

How it works
------------
NOUNS  Each Śabdamañjarī table is inverted into ending rules: model राम / form रामेण gives
       "…eRa → stem …a, तृतीया एकवचनम्, पुंलिङ्गम्". A word is matched against every rule, the
       candidate stem is validated against the lexicon (whole stem, or its last compound member),
       and candidates are ranked by: validated > compound-validated > unvalidated; lexicon gender
       agrees with the paradigm's gender; longer (more specific) ending; then a case/number prior.
VERBS  Dhatu-Lakara's 30 paradigms teach which "rest" strings follow a root-stem in each cell
       (bhav|ati → लट् प्र ए, a|bhav|at → लङ्, ba-bhūv|a → लिट्). A word is peeled of upasargas and
       the augment, then every Dhatu-Manjari root is tried in its guṇa/vṛddhi/samprasāraṇa/
       reduplicated/causative shapes as a prefix; the remainder must be a learned rest.
AVYAYA closed list + kṛt/taddhita suffix patterns.

This is a candidate generator with honest ranking, not a full Pāṇinian derivation: every reading
carries `evidence` saying which rule and which dictionary hit produced it, and `confidence`
('validated' / 'compound-validated' / 'pattern-only').

Usage:
    python pada_analyser.py रामेण गच्छति इति
    python pada_analyser.py --iast rāmeṇa gacchati
    from pada_analyser import PadaAnalyser; PadaAnalyser().analyse("रामेण")
"""
import json
import os
import re
import sys
from functools import lru_cache

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.normpath(os.path.join(HERE, "..", ".."))
LSK = os.path.join(PROJ, "04_Laghu_Siddhanta_Kaumudi")
DICT_DIR = os.path.join(PROJ, "05_Sanskrit_Dictionaries")
if not os.path.isdir(LSK) and os.path.isfile(os.path.join(HERE, "Dhatu-Manjari.json")):
    LSK = HERE                      # flat folder: all data files sit next to the scripts
if not os.path.isdir(DICT_DIR) and os.path.isfile(os.path.join(HERE, "apte_dictionary.sqlite")):
    DICT_DIR = HERE
SANDHI_DIR = os.path.join(HERE, "..", "sandhi")
if not os.path.isdir(SANDHI_DIR):
    SANDHI_DIR = HERE
if SANDHI_DIR not in sys.path:
    sys.path.insert(0, SANDHI_DIR)
from transliterate import deva_to_slp1  # noqa: E402

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate as _tl

    def slp1_to_deva(s):
        return _tl(s, sanscript.SLP1, sanscript.DEVANAGARI)

    def iast_to_slp1(s):
        return _tl(s, sanscript.IAST, sanscript.SLP1)
except ImportError:  # the analyser still works in Devanagari without it
    def slp1_to_deva(s):
        return s

    def iast_to_slp1(s):
        raise RuntimeError("pip install indic_transliteration for IAST input")

VOWELS = set("aAiIuUfFxXeEoO")
CASE_NAMES = {1: "प्रथमा", 2: "द्वितीया", 3: "तृतीया", 4: "चतुर्थी", 5: "पञ्चमी", 6: "षष्ठी",
              7: "सप्तमी", 8: "सम्बोधनम्"}
CASE_OF = {v: k for k, v in CASE_NAMES.items()}
CASE_OF["संबोधनम्"] = 8
NUM_NAMES = {"e": "एकवचनम्", "d": "द्विवचनम्", "b": "बहुवचनम्"}
GENDER_NAMES = {"m": "पुंलिङ्गम्", "f": "स्त्रीलिङ्गम्", "n": "नपुंसकलिङ्गम्", "x": "त्रिलिङ्गम्"}
LAKARA_DEV = {"lat": "लट्", "lit": "लिट्", "lut": "लुट्", "lrt": "लृट्", "lot": "लोट्", "lan": "लङ्",
              "vidhi_lin": "विधिलिङ्", "ashir_lin": "आशीर्लिङ्", "lun": "लुङ्", "lrn": "लृङ्"}
PURUSHA_DEV = {"prathama": "प्रथमपुरुषः", "madhyama": "मध्यमपुरुषः", "uttama": "उत्तमपुरुषः"}
VACANA_KEY = {"eka": "e", "dvi": "d", "bahu": "b"}
PADA_DEV = {"parasmaipada": "परस्मैपदम्", "atmanepada": "आत्मनेपदम्", "karmani": "आत्मनेपदम् (कर्मणि)"}
# rough corpus frequency of each vibhakti+vacana in narrative verse (used only to break ties
# between readings the paradigms and the lexicon cannot separate)
FREQ_PRIOR = {(1, "e"): 0.30, (2, "e"): 0.25, (3, "e"): 0.15, (6, "e"): 0.15, (7, "e"): 0.15,
              (1, "b"): 0.15, (2, "b"): 0.10, (3, "b"): 0.10, (6, "b"): 0.10, (4, "e"): 0.08,
              (5, "e"): 0.06, (7, "b"): 0.06, (8, "e"): -0.10}
CASE_PRIOR = {1: 0, 2: 1, 3: 2, 6: 3, 7: 4, 4: 5, 5: 6, 8: 7}
NUM_PRIOR = {"e": 0, "b": 1, "d": 2}

# 22 upasargas (SLP1), with the shapes they take before a vowel (yaṇ) or after ṣatva
UPASARGAS = ["pra", "parA", "apa", "sam", "anu", "ava", "nis", "nir", "dus", "dur", "vi", "AN",
             "ni", "aDi", "api", "ati", "su", "ud", "aBi", "prati", "pari", "upa"]
UPASARGA_SHAPES = {}
for _u in UPASARGAS:
    base = {"AN": "A"}.get(_u, _u)
    shapes = {base}
    if base.endswith("i"):
        shapes.add(base[:-1] + "y")          # prati -> praty (+vowel)
    if base.endswith("u"):
        shapes.add(base[:-1] + "v")          # anu -> anv
    if base == "sam":
        shapes |= {"saM", "saN", "saY", "saR", "san"}
    if base == "ud":
        shapes |= {"ut", "un", "uc", "uj", "ul"}
    if base in ("nis", "dus"):
        shapes |= {base[:-1] + "z", base[:-1] + "H", base[:-1] + "S"}
    for s in shapes:
        UPASARGA_SHAPES[s] = {"AN": "आ"}.get(_u, slp1_to_deva(base if base != "A" else "A"))
UPASARGA_SHAPES_SORTED = sorted(UPASARGA_SHAPES, key=len, reverse=True)

# closed list of indeclinables (SLP1) — particles, adverbs of time/place/manner
AVYAYAS = set("""ca na eva iti api hi tu ha iva atha taTA yaTA tadA sadA sarvadA kadA yadA punar
punaH tatra yatra kutra kva cit cana nAma saha prati fte samyak sAmpratam nu sma vA mA alam iha
adya idAnIm tataH yataH ataH kutaH evam tataH yadi cet Kalu kila nanu muhuH sahasA uccEH SanEH
purA puraH bahiH antaH antar prAk paScAt agre vinA svayam aho hanta Bos kim Iti tUzRIm vfTA
mfzA sAkam sArDam samam yAvat tAvat""".split())
AVYAYA_GLOSS = {"ca": "समुच्चये", "na": "निषेधे", "eva": "अवधारणे", "iti": "वाक्यसमाप्तौ",
                "api": "समुच्चये", "hi": "हेतौ", "tu": "विशेषे", "ha": "पादपूरणे", "iva": "उपमायाम्"}


def _norm_slp1(s):
    """anusvāra -> class nasal before a stop, final anusvāra -> m (citation spelling)."""
    s = s.replace("‌", "").replace("‍", "")
    if s.endswith("M"):
        s = s[:-1] + "m"
    nasal = {"k": "N", "K": "N", "g": "N", "G": "N", "c": "Y", "C": "Y", "j": "Y", "J": "Y",
             "w": "R", "W": "R", "q": "R", "Q": "R", "t": "n", "T": "n", "d": "n", "D": "n",
             "p": "m", "P": "m", "b": "m", "B": "m"}
    return re.sub(r"M(?=[kKgGcCjJwWqQtTdDpPbB])", lambda m: nasal[s[m.end()]] if m.end() < len(s) else "m", s)


def peel_upasarga(b, min_rest=1):
    """Yield (upasarga_devanagari, remainder) for every upasarga that can start `b`, undoing the
    vowel sandhi between upasarga and root: pra+āp -> prāp, upa+i -> upe, upa+agamat -> upāgamat."""
    for shape in UPASARGA_SHAPES_SORTED:
        up = UPASARGA_SHAPES[shape]
        if b.startswith(shape) and len(b) - len(shape) >= min_rest:
            rest = b[len(shape):]
            if shape.endswith(("y", "v")) and rest[:1] not in VOWELS:
                continue
            yield up, rest
        if shape.endswith(("a", "A")) and len(b) > len(shape) + min_rest - 1:
            stem, nxt = shape[:-1], b[len(shape) - 1:len(shape)]
            if not b.startswith(stem):
                continue
            rest = b[len(shape):]
            if nxt == "A":
                yield up, "a" + rest
                yield up, "A" + rest
            elif nxt == "e" and shape.endswith("a"):
                yield up, "i" + rest
            elif nxt == "o" and shape.endswith("a"):
                yield up, "u" + rest
            elif nxt == "E" and shape.endswith("a"):
                yield up, "e" + rest
        if shape.endswith(("i", "u")) and len(b) > len(shape) + min_rest - 1:
            long_v = "I" if shape.endswith("i") else "U"      # vi+īkṣ -> vīkṣ (अकः सवर्णे दीर्घः)
            if b.startswith(shape[:-1]) and b[len(shape) - 1:len(shape)] == long_v:
                rest = b[len(shape):]
                yield up, shape[-1] + rest
                yield up, long_v + rest


class PadaAnalyser:
    def __init__(self, lsk_dir=LSK, dict_dir=DICT_DIR):
        self.lex = {}
        lex_path = os.path.join(dict_dir, "lexicon_index.json")
        if os.path.isfile(lex_path):
            with open(lex_path, encoding="utf-8") as fh:
                self.lex = json.load(fh)
        self.noun_rules = []          # (ending, tail, case, num, gender, model, page)
        self.exact_forms = {}         # form -> list of readings (pronouns, numerals, models)
        self._load_sabdamanjari(os.path.join(lsk_dir, "sabdamanjari_vibhakti_tables.json"))
        self.roots = {}               # SLP1 root -> list of Dhatu-Manjari records
        self._load_roots(os.path.join(lsk_dir, "Dhatu-Manjari.json"))
        self.verb_exact = {}          # full form -> cells (from the 30 paradigms)
        self.rest_table = {}          # (flag, rest) -> {cell: count}
        self.root_rest = {}           # (root, flag, rest) -> {cell: count}, for the 30 paradigm roots
        self._variant_index = None
        self._load_paradigms(os.path.join(lsk_dir, "Dhatu-Lakara.json"))
        # ब्रुवः पञ्चानामादित आहो ब्रुवः (3.4.84): brū's optional laṭ forms āha/āhatuḥ/āhuḥ
        for f, cell in (("Aha", ("lat", "prathama", "e", "parasmaipada")),
                        ("AhatuH", ("lat", "prathama", "d", "parasmaipada")),
                        ("AhuH", ("lat", "prathama", "b", "parasmaipada"))):
            self.verb_exact.setdefault(f, set()).add(("brU",) + cell)

    # ------------------------------------------------------------------ loading
    def _load_sabdamanjari(self, path):
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        rules = set()
        for sec in d["sections"].values():
            for w in sec["words"]:
                model = deva_to_slp1(w["model_word"])
                g_raw = w.get("gender", "")
                gender = "m" if "पुं" in g_raw else "f" if "स्त्री" in g_raw else "n" if "नपुं" in g_raw else "x"
                if "नपुं" in g_raw:
                    gender = "n"
                closed = sec.get("section_num") in (14, 15, 16) or w["model_word"] in (
                    "अस्मद्", "युष्मद्", "तद्", "यद्", "एतद्", "इदम्", "अदस्", "किम्")
                cols = self._columns(w["declension_table"]["headers"], gender, w["model_word"])
                for row in w["declension_table"]["rows"]:
                    case = CASE_OF.get(row[0])
                    if case is None:
                        continue
                    for (gender, num), cell in zip(cols, row[1:]):
                        first_tail = None
                        for fi, form in enumerate(re.split(r"\s*[/,]\s*|\s+-\s+|(?<=[ऀ-ॿ])-(?=[ऀ-ॿ]{2})", cell or "")):
                            form = form.strip(" ()")
                            if not form or form in ("-", "—"):
                                continue
                            f = _norm_slp1(deva_to_slp1(form))
                            if not f:
                                continue
                            reading = {"type": "noun", "stem": model, "case": case, "num": num,
                                       "gender": gender, "model": model, "page": w.get("source_pdf_page"),
                                       "closed": closed}
                            self.exact_forms.setdefault(f, []).append(reading)
                            if closed:
                                continue
                            cp = 0
                            while cp < min(len(f), len(model)) and f[cp] == model[cp]:
                                cp += 1
                            if fi == 0:
                                first_tail = model[cp:]
                            elif first_tail and model[cp:] == "" and f.endswith(("H", "m")):
                                continue        # optional word-specific alternate (मासः, मांसः, उद्नः): exact match only, never a general ending rule
                            if cp < 1:
                                continue
                            rules.add((f[cp:], model[cp:], case, num, gender, model, w.get("source_pdf_page"),
                                       sec.get("section_num") in (1, 2, 3, 7, 8, 9)))
        # ṇatva variants: a rule learned from राम (…eRa) also covers देव-type (…ena) and vice versa
        extra = set()
        for r in rules:
            if "R" in r[0]:
                extra.add((r[0].replace("R", "n"),) + r[1:])
            elif "n" in r[0] and r[0] not in ("n",):
                extra.add((r[0].replace("n", "R"),) + r[1:])
        # fully deterministic order (Python's string hashing is randomised per process, so a
        # plain set order made tie-breaks differ between runs): longest ending, common models,
        # then the book's own page order
        self.noun_rules = sorted(rules | extra, key=lambda r: (-len(r[0]), not r[7], r[6] or 0, r[5],
                                                               r[2], r[3], r[4], r[1]))

    @staticmethod
    def _columns(headers, gender, model_word):
        """(gender, number) for each data column of a Śabdamañjarī table."""
        num_of = {"एकवचनम्": "e", "द्विवचनम्": "d", "बहुवचनम्": "b"}
        g_of = {"पुं": "m", "स्त्री": "f", "नपुं": "n"}
        fixed_num = "e" if model_word == "एक" else "d" if model_word in ("द्वि", "उभ") else "b"
        cols = []
        for h in headers[1:]:
            if h in num_of:
                cols.append((gender, num_of[h]))
            elif "-" in h and h.split("-")[0] in g_of:
                g, n = h.split("-", 1)
                cols.append((g_of[g], num_of.get(n, "b")))
            elif h.startswith("नपुं"):
                cols.append(("n", fixed_num))
            elif h.startswith("पुं"):
                cols.append(("m", fixed_num))
            elif h.startswith("स्त्री"):
                cols.append(("f", fixed_num))
            else:                                   # "रूपम् (त्रिषु लिङ्गेषु समानम्)"
                cols.append(("x", fixed_num))
        return cols

    def _load_roots(self, path):
        with open(path, encoding="utf-8") as fh:
            for rec in json.load(fh)["data"]:
                r = deva_to_slp1(rec["dhatu"])
                if r:
                    self.roots.setdefault(r, []).append(rec)

    def _load_paradigms(self, path):
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        for rec in d["data"]:
            root = deva_to_slp1(rec["dhatu"])
            for pada, lakaras in rec["padas"].items():
                for lak, persons in lakaras.items():
                    for per, nums in persons.items():
                        for num, cell in nums.items():
                            for form in cell.get("dev", []):
                                f = _norm_slp1(deva_to_slp1(form))
                                key = (lak, per, VACANA_KEY[num], pada)
                                self.verb_exact.setdefault(f, set()).add((root,) + key)
                                for flag, stem_len, _root, _kind in self._match_root(f, only_root=root):
                                    if lak in ("lan", "lun", "lrn") and not flag.startswith("aug"):
                                        continue
                                    rest = f[stem_len:]
                                    self.rest_table.setdefault((flag, rest), {})
                                    self.rest_table[(flag, rest)][key] = \
                                        self.rest_table[(flag, rest)].get(key, 0) + 1
                                    rr = self.root_rest.setdefault((root, f[:stem_len], rest), {})
                                    rr[key] = rr.get(key, 0) + 1

    # ------------------------------------------------------------------ lexicon
    def lex_tags(self, stem):
        t = self.lex.get(stem)
        if t is None and stem.endswith(("n", "t")) is False:
            t = self.lex.get(stem + "H")
        return t

    @staticmethod
    def _nominal(tags):
        return any(c in tags for c in "mfna")

    def in_lex(self, stem):
        return stem in self.lex

    def compound_split(self, stem, depth=0):
        """Best member list if `stem` = [plausible member(s)] + [lexicon word], else None.
        All cut points are tried and scored (longer, fewer members win; a last member that is
        just a- + another headword, e.g. a-krodha in jita|krodha, is penalised)."""
        if len(stem) < 4 or depth > 3:
            return None
        best, best_score = None, None
        for i in range(1, len(stem) - 1):
            for first, last in self._junction_splits(stem, i):
                res = self._try_members(first, last, depth)
                if not res:
                    continue
                sc = sum(len(m) ** 2 for m in res) - 6 * (len(res) - 2)
                for m in res[1:]:
                    if m.startswith("a") and len(m) > 3 and m[1:] in self.lex and self._nominal(self.lex[m[1:]]):
                        sc -= 25
                if best_score is None or sc > best_score:
                    best, best_score = res, sc
        return best

    @staticmethod
    def _junction_splits(stem, i):
        """Possible (first, last) pairs for a cut before position i, undoing vowel sandhi."""
        a, b = stem[:i], stem[i:]
        yield a, b
        v = b[0]
        if v == "A":
            yield a + "a", "a" + b[1:]
            yield a + "A", "a" + b[1:]
            yield a + "a", b
            yield a + "A", b
        elif v in ("e", "o", "E", "O"):
            base = {"e": "i", "o": "u", "E": "e", "O": "o"}[v]
            yield a + "a", base + b[1:]
            yield a + "A", base + b[1:]
            if v in ("e", "o"):
                yield a + "a", {"e": "I", "o": "U"}[v] + b[1:]
        elif v in ("I", "U"):
            yield a + v.lower(), v.lower() + b[1:]
            yield a + v.lower(), b
        if b.startswith("ar"):
            yield a + "a", "f" + b[2:]

    SHORT_FIRST_MEMBERS = {"su", "dur", "dus", "a", "an", "sa", "mahA", "nis", "nir", "vi", "pra",
                           "sam", "saM", "ku", "sad", "sat"}

    def _try_members(self, first, last, depth):
        """Members if `last` is a nominal headword and `first` is one too (or decomposes)."""
        if len(last) < 3 or last not in self.lex or not self._nominal(self.lex[last]) or len(first) < 1:
            return None
        cands = [first]
        if first.endswith("M"):
            cands.append(first[:-1] + "m")
        if first[-1] not in VOWELS:
            cands += [first + "H"]
        if first.endswith("A"):
            cands.append(first[:-1] + "a")   # mahā- < mahat; long ā in the first member
        if first.endswith("o"):
            cands.append(first[:-1] + "as")  # mano- < manas
        if first.endswith("r"):
            cands += [first[:-1] + "s", first[:-1] + "H"]  # dhanur- < dhanus
        if first.endswith("H"):
            cands += [first[:-1] + "s", first[:-1]]        # tapaḥ- < tapas
        if first[-1] in "gqdb":
            cands.append(first[:-1] + {"g": "k", "q": "w", "d": "t", "b": "p"}[first[-1]])  # vāg- < vāc/vāk
            if first.endswith("g"):
                cands.append(first[:-1] + "c")
        for c in cands:
            if (c in self.lex and len(c) >= 3 and self._nominal(self.lex[c])) or c in self.SHORT_FIRST_MEMBERS:
                return [c, last]
        sub = self.compound_split(first, depth + 1)
        if sub:
            return sub + [last]
        return None

    # ------------------------------------------------------------------ verbs
    def _root_variants(self, root):
        """Yield (shape, kind) pairs a root takes in finite forms."""
        out = {(root, "plain")}
        v_idx = [i for i, ch in enumerate(root) if ch in VOWELS]
        if not v_idx:
            return out
        i = v_idx[-1]
        v = root[i]
        guna = {"i": "e", "I": "e", "u": "o", "U": "o", "f": "ar", "F": "ar", "x": "al"}
        vrddhi = {"a": "A", "i": "E", "I": "E", "u": "O", "U": "O", "f": "Ar", "F": "Ar", "e": "E", "o": "O"}
        dirgha = {"i": "I", "u": "U", "f": "F"}
        pre, post = root[:i], root[i + 1:]
        forms = [root]
        if v in guna:
            forms.append(pre + guna[v] + post)
        if v in vrddhi:
            forms.append(pre + vrddhi[v] + post)
        if v in dirgha:
            forms.append(pre + dirgha[v] + post)
        final = []
        for f in forms:
            final.append(f)
            if f[-1] in ("e", "o", "E", "O"):
                final.append(f[:-1] + {"e": "ay", "o": "av", "E": "Ay", "O": "Av"}[f[-1]])
            if f[-1] in ("i", "I"):
                final.append(f[:-1] + "iy")
            if f[-1] in ("u", "U"):
                final.append(f[:-1] + "uv")
            if f[-1] in ("c", "j", "S", "z", "h"):
                final.append(f[:-1] + "k")   # before -s(y)a: vac -> vak|zyati
        for f in final:
            out.add((f, "plain"))
        # causative / curādi stems: guṇa-or-vṛddhi + ay, ā-roots + pay
        caus = set()
        for f in forms:
            caus.add(f + "ay")
        if root.endswith("A"):
            caus.add(root + "pay")
        if v == "a" and len(post) == 1:
            caus.add(pre + "A" + post + "ay")
        for c in caus:
            out.add((c, "caus"))
        # samprasāraṇa and irregular present stems
        irregular = {"gam": ["gacC"], "iz": ["icC"], "yam": ["yacC"], "sTA": ["tizW"], "pA": ["pib"],
                     "dfS": ["paSy", "drak"], "sad": ["sId"], "vac": ["uc", "vak"], "yaj": ["ij", "yak"],
                     "vas": ["uz", "vat"], "vah": ["uh", "voQ"], "grah": ["gfh", "gfhR", "gfhN"],
                     "pracC": ["pfcC", "pfC"], "svap": ["sup"], "BU": ["BUv"], "jan": ["jA", "jaj"],
                     "sic": ["ziYc", "siYc", "zic"], "muc": ["muYc"], "han": ["Gn", "jahi"],
                     "brU": ["bruv", "brav", "vac", "vak"], "as": ["s"], "i": ["y", "I"],
                     "SAs": ["Siz"], "kf": ["kur", "karo", "kar", "cakr"], "dA": ["dad", "dat", "de", "dI"],
                     "sTA": ["tizW", "sTI"], "pA": ["pib", "pI"], "hA": ["hI"],
                     "mfj": ["mArj"], "Sru": ["SfR", "SfRo", "SfRu", "SrU"], "sfj": ["sraz", "sarj"]}
        for s in irregular.get(root, []):
            out.add((s, "plain"))
        # ṣatva after an upasarga: sic -> zic, sTA -> zWA
        if root.startswith("s"):
            for s, k in list(out):
                if s.startswith("s"):
                    out.add(("z" + s[1:], k))
        # reduplication (liṭ): abhyāsa consonant de-aspirated, guttural/h -> palatal
        cons = root[:i]
        first = cons[:1] if cons else ""
        if first:
            deasp = {"K": "k", "G": "g", "C": "c", "J": "j", "W": "w", "Q": "q", "T": "t", "D": "d",
                     "P": "p", "B": "b"}.get(first, first)
            deasp = {"k": "c", "g": "j", "h": "j"}.get(deasp, deasp)
            if len(cons) > 1 and cons[0] in "sS" and cons[1] not in "yrlv":
                deasp = {"K": "k", "T": "t", "W": "w", "P": "p"}.get(cons[1], cons[1])
                deasp = {"k": "c"}.get(deasp, deasp)
            av = {"a": "a", "A": "a", "f": "a", "F": "a", "x": "a", "i": "i", "I": "i", "e": "i",
                  "u": "u", "U": "u", "o": "u", "E": "i", "O": "u"}[v]
            abh = deasp + av
            red = set()
            for f in final + [pre + "A" + post] + [pre + post]:
                red.add(abh + f)
            if root.endswith("A"):
                red.add(abh + root[:-1])        # dA -> dad|O, yA -> yay|O
            if root == "han":
                red |= {"jaGAn", "jaGn", "jaGan"}
            if root == "grah":
                red |= {"jagrAh", "jagfh"}
            if root == "vac":
                red |= {"uvAc", "Uc"}
            if root == "vas":
                red |= {"uvAs", "Uz"}
            for r in red:
                out.add((r, "redup"))
        elif v in ("a", "A", "i", "u"):
            out.add(("A" + root[1:], "redup"))   # as -> Asa (āsa), aṭ -> āṭa
        return out

    def _build_variant_index(self):
        idx = {}
        for root in self.roots:
            for shape, kind in self._root_variants(root):
                if len(shape) >= 1:
                    idx.setdefault(shape, set()).add((root, kind))
        self._variant_index = idx

    def _match_root(self, word, only_root=None):
        """Yield (flag, stem_len, root, kind) for every way a root shape is a prefix of `word`
        (after the laṅ/luṅ augment, which is recorded in `flag`)."""
        starts = [("", word)]
        if word.startswith("a") and len(word) > 3:
            starts.append(("aug", word[1:]))
        if word[:1] in ("A", "E", "O"):
            starts.append(("aug", {"A": "a", "E": "i", "O": "u"}[word[0]] + word[1:]))
            if word[0] == "E":
                starts.append(("aug", "e" + word[1:]))
        found = []
        if only_root is not None:
            shapes = self._root_variants(only_root)
            for flag, w in starts:
                off = len(word) - len(w)
                for shape, kind in sorted(shapes):
                    if w.startswith(shape) and len(w) > len(shape):
                        found.append(((flag + "+" + kind) if flag else kind, off + len(shape), only_root, kind))
            return found
        if self._variant_index is None:
            self._build_variant_index()
        for flag, w in starts:
            off = len(word) - len(w)
            for L in range(min(len(w) - 1, 9), 0, -1):
                for root, kind in sorted(self._variant_index.get(w[:L], ())):
                    found.append(((flag + "+" + kind) if flag else kind, off + L, root, kind))
        return found

    def analyse_verb(self, w):
        """Readings for a finite verb form (SLP1)."""
        readings = []
        # periphrastic perfect: X-Am-Asa / X-AM-cakAra / X-AM-baBUva
        m = re.match(r"(.+?)(Am|AM)(Asa|Asatu[Hs]|AsuH|cakAra|cakre|baBUva)$", w)
        body_candidates = [("", w)]
        # peel upasargas (up to three)
        for _ in range(3):
            new = []
            for ups, b in body_candidates:
                for up, rest in peel_upasarga(b, min_rest=2):
                    new.append((ups + "|" + up, rest))
            if not new:
                break
            body_candidates += [n for n in new if n not in body_candidates]
        for ups, body in body_candidates:
            upasargas = [u for u in ups.split("|") if u]
            if m and body.endswith(m.group(2) + m.group(3)):
                stem = body[: -len(m.group(2) + m.group(3))]
                for root in self.roots:
                    for shape, kind in self._root_variants(root):
                        if kind == "caus" and shape == stem or (kind == "plain" and stem == shape + "ay"):
                            readings.append(self._verb_reading(root, ("lit", "prathama", "e", "parasmaipada"),
                                                               upasargas, "periphrastic", 3, "कास्प्रत्ययादाममन्त्रे लिटि (आम्) + अस्-अनुप्रयोगः"))
                continue
            if body in self.verb_exact and not upasargas:
                for (root, lak, per, num, pada) in self.verb_exact[body]:
                    readings.append(self._verb_reading(root, (lak, per, num, pada), upasargas, "paradigm", 4,
                                                       "Dhatu-Lakara.json exact form"))
            for flag, L, root, kind in self._match_root(body):
                rest = body[L:]
                keys = [(flag, rest)]
                if rest.startswith("z") and body[L - 1:L] == "k":
                    keys.append((flag, "s" + rest[1:]))
                    keys.append((flag, "iz" + rest[1:]))
                cells = {}
                for k in keys:                      # the root's own paradigm first, if we have it
                    for cell, c in self.root_rest.get((root, body[:L], k[1]), {}).items():
                        cells[cell] = cells.get(cell, 0) + c
                if not cells:
                    for k in keys:
                        for cell, c in self.rest_table.get(k, {}).items():
                            cells[cell] = cells.get(cell, 0) + c
                note = ""
                if not cells and flag.startswith("aug") is False:
                    # ārṣa: laṅ without augment (e.g. शंसत्)
                    for cell, c in self.rest_table.get(("aug+" + flag if flag else "aug+plain", rest), {}).items():
                        cells[cell] = cells.get(cell, 0) + c
                        note = "आर्षप्रयोगः — अडागमाभावः"
                if not cells and rest in ("yate", "yante", "yatAm", "yantAm", "yeta", "yata", "yanta"):
                    cells = {({"yate": "lat", "yante": "lat", "yatAm": "lot", "yantAm": "lot",
                               "yeta": "vidhi_lin", "yata": "lan", "yanta": "lan"}[rest],
                              "prathama", "b" if "nt" in rest else "e", "karmani"): 1}
                    note = "सार्वधातुके यक् (कर्मणि)"
                if not cells:
                    continue
                lak_p = {"lat": 0, "lan": 1, "lit": 2, "lot": 3, "vidhi_lin": 4, "lrt": 5, "lun": 6,
                         "ashir_lin": 7, "lut": 8, "lrn": 9}
                per_p = {"prathama": 0, "uttama": 1, "madhyama": 2}
                best_cell = max(cells.items(), key=lambda kv: (-lak_p.get(kv[0][0], 9),
                                                               -per_p.get(kv[0][1], 9), kv[1]))[0]
                # -ya- after a non-divādi root is the passive yak, not the divādi vikaraṇa
                gan = {r.get("gana") for r in self.roots.get(root, [])}
                pas = {"yate": ("lat", "e"), "yante": ("lat", "b"), "yatAm": ("lot", "e"),
                       "yantAm": ("lot", "b"), "yeta": ("vidhi_lin", "e"), "yata": ("lan", "e")}
                if rest in pas and "4" not in gan:
                    best_cell = (pas[rest][0], "prathama", pas[rest][1], "karmani")
                    note = "सार्वधातुके यक् (कर्मणि)"
                score = {"redup": 3.4, "caus": 2.4}.get(kind, 2.2) + (0.6 if flag.startswith("aug") else 0) \
                    - (0.6 if note.startswith("आर्ष") else 0)
                readings.append(self._verb_reading(root, best_cell, upasargas, kind, score,
                                                   f"root-shape «{slp1_to_deva(body[:L])}» + «{slp1_to_deva(rest)}»"
                                                   + (f"; {note}" if note else "")))
        # prefer: exact paradigm > longer root shape/fewer upasargas; dedupe
        seen, out = set(), []
        pp = {"प्रथमपुरुषः": 0, "मध्यमपुरुषः": 2, "उत्तमपुरुषः": 1}
        for r in readings:
            recs = self.roots.get(deva_to_slp1(r["dhatu"]), [])
            if any("common" in (x.get("tags") or "") for x in recs):
                r["_score"] += 0.1
        for r in sorted(readings, key=lambda r: (-round(r["_score"], 6), len(r["upasarga"]), pp.get(r["purusha"], 3),
                                                 -len(r["dhatu"]), r["dhatu"], r["lakara"], r["vacana"])):
            key = (r["dhatu"], r["lakara"], r["purusha"], r["vacana"], tuple(r["upasarga"]))
            if key not in seen:
                seen.add(key)
                out.append(r)
        return out

    def _verb_reading(self, root, cell, upasargas, kind, score, evidence):
        lak, per, num, pada = cell
        recs = self.roots.get(root, [{}])
        rec = recs[0]
        return {"type": "verb", "dhatu": slp1_to_deva(root), "gana": rec.get("gana"),
                "dhatu_pada": rec.get("pada"), "artha": rec.get("artha"),
                "all_ganas": sorted({r.get("gana") for r in recs if r.get("gana")}),
                "lakara": LAKARA_DEV.get(lak, lak), "purusha": PURUSHA_DEV.get(per, per),
                "vacana": NUM_NAMES.get(num, num), "pada": PADA_DEV.get(pada, pada),
                "nijanta": kind == "caus", "upasarga": upasargas, "evidence": evidence,
                "_score": score}

    # ------------------------------------------------------------------ nouns
    def _matup_base(self, stem):
        """-vat/-mat (मतुप्/वतुप्) nouns: return (base, allomorph_ok) when `stem` = lexicon base + mat/vat, else None.
        vat after bases ending in a/ā/m or with a/ā as upadhā (मादुपधायाश्च मतोर्वोऽयवादिभ्यः 8.2.9); mat elsewhere.
        Never fires for kta-vat participles (kṛtavat), nor where a vasu stem exists (vidvas-, not *vid-vat)."""
        suf = stem[-3:]
        base = stem[:-3]
        if suf not in ("vat", "mat") or len(base) < 2:
            return None
        if self._participle(stem) or (stem[:-1] + "s") in self.lex and self._nominal(self.lex[stem[:-1] + "s"]):
            return None
        if not any(self.lex.get(b2) is not None and self._nominal(self.lex[b2]) for b2 in (base, base + "n", base + "s")) \
                and not self.compound_split(base):          # ātma-vat < ātman, tejas-vat
            return None
        want_vat = base[-1] in "aAm" or (len(base) > 1 and base[-2] in "aA" and base[-1] not in VOWELS)
        return base, (suf == "vat") == want_vat

    def analyse_noun(self, w):
        out = []
        for r in self.exact_forms.get(w, []):
            if r["closed"]:
                out.append(self._noun_reading(r["stem"], r["case"], r["num"], r["gender"], r["model"],
                                              r["page"], 4.6, "सर्वनाम/सङ्ख्या — Śabdamañjarī exact form", None))
        for end, tail, case, num, gender, model, page, common in self.noun_rules:
            if not w.endswith(end) or len(w) - len(end) < 1:
                continue
            stem = w[:len(w) - len(end)] + tail
            if len(stem) < 2 or stem[-1] != model[-1]:
                continue            # a word declines like a model only if it ends in the same sound
            members = None
            tags = self.lex.get(stem)
            # Neuter a-stems are indexed under their nominative headword (vAkyaM, not vAkya).
            # Without this, vākyam fell to an unattested stem (score 0.3) and lost to a phantom
            # laṅ verb reading (√वच् + ārṣa augment-less), see Sarga-1 audit.
            if tags is None and gender == "n" and model.endswith("a") and self.lex.get(stem + "M") is not None \
                    and "n" in self.lex.get(stem + "M"):          # SLP1: anusvāra = M
                tags = self.lex.get(stem + "M")
            if tags is not None and self._nominal(tags):
                score = 3.0
            elif self._participle(stem) or (w.endswith("ataH") and self._satr_stem(stem)):
                score, tags = 2.6, "a"
            else:
                members = self.compound_split(stem)
                if members:
                    score, tags = 2.0, self.lex.get(members[-1], "")
                elif tags is not None:
                    score = 1.5          # headword exists but is only a root / indeclinable
                else:
                    score, tags = 0.3, ""
            matup = self._matup_base(stem) if (end and stem.endswith(("vat", "mat"))) else None
            if matup:
                base, ok_allomorph = matup
                members, score, tags = None, (3.0 if ok_allomorph else 2.55), "a"   # तदस्यास्त्यस्मिन्निति मतुप् (5.2.94)
            if members:
                score += -0.1 * (len(members) - 2) + 0.02 * len(members[-1])
            if stem not in self.lex and not matup:
                if stem.endswith("n") and not w.endswith("n") and not stem.endswith(("man", "van", "in")) \
                        and not (members and members[-1].endswith(("man", "van", "in"))):
                    score -= 0.8        # *cāritreṇan, *anasūyakan: an -n stem invented from an a-final word, no lexicon backing
                elif re.search("[eoEO][^aAiIuUfFxXeEoO]+$", stem):
                    score -= 0.8        # a stem does not end in e/o/ai/au + consonant
            if members and end and model[-1] not in VOWELS and members[-1] in self.roots \
                    and not any(g in (self.lex.get(members[-1]) or "") for g in "mfn"):
                score += 0.7            # kvip/upapada compound ending in a root (vāg-vid-): consonant-stem model, overt case ending
            genders = {g for g in "mfn" if g in tags}
            if gender in genders:
                score += 0.6
            elif "a" in tags:
                score += 0.35           # adjective: agrees with any gender
            elif gender == "x" or not genders:
                score += 0.2
            else:
                score -= 1.0
            if not end and case == 8:
                score -= 0.6            # zero-ending vocative
            score += 0.01 * len(end) + (0 if common else -0.4) + FREQ_PRIOR.get((case, num), 0)
            if case == 2 and num == "e" and w.endswith("am"):
                score += 0.1            # -am in narrative verse is far more often accusative than neuter nominative
            if stem.endswith("at") and case in (1, 8) and "n" not in end and \
                    ((self._participle(stem) or ("", ""))[1] == "शतृ" or (w.endswith("ataH") and self._satr_stem(stem))):
                score -= 0.5            # śatṛ strong cases take num (उगिदचां सर्वनामस्थानेऽधातोः 7.1.70): *bruvataḥ nom.pl.
            r = self._noun_reading(stem, case, num, gender, model, page, score,
                                   f"{slp1_to_deva(model)}-शब्दवत् (Śabdamañjarī पृ.{page}); ending «{slp1_to_deva(end) if end else '∅'}»",
                                   members)
            if matup:
                r["taddhita"] = {"pratyaya": "मतुप्", "sutra": "5.2.94", "base": slp1_to_deva(matup[0])}
            if score >= 2.5 and not members and not matup:
                k = self._participle(stem) or (w.endswith("ataH") and self._satr_stem(stem))
                if k:
                    r["krt"] = {"dhatu": k[0], "pratyaya": k[1], "upasarga": list(k[2])}
            out.append(r)
        out.sort(key=lambda r: (-round(r["_score"], 6), CASE_PRIOR.get(r["case"], 9), NUM_PRIOR.get(r["num"], 9),
                                r["page"] or 0, r["stem"], r["gender"]))
        seen, res = set(), []
        for r in out:
            key = (r["stem"], r["case"], r["num"])
            if key not in seen:
                seen.add(key)
                res.append(r)
        return res

    def _noun_reading(self, stem, case, num, gender, model, page, score, evidence, members):
        return {"type": "noun", "stem": slp1_to_deva(stem), "case": case, "case_name": CASE_NAMES[case],
                "num": num, "vacana": NUM_NAMES[num], "gender": GENDER_NAMES.get(gender, gender),
                "model": slp1_to_deva(model), "page": page, "members": [slp1_to_deva(m) for m in members] if members else None,
                "confidence": "validated" if score >= 3 else "compound-validated" if score >= 1.9 else "pattern-only",
                "evidence": evidence, "_score": score}

    @lru_cache(maxsize=20000)
    def _satr_stem(self, stem):
        """Irregular śatṛ stems (bruvat-, vīkṣat-) that _participle's root-shape guess misses: accept
        «X-at» when «X-anti» parses as a present 3pl, taking the root from that parse. Used ONLY for
        the -ataḥ (gen./abl. sg.) competition with -tas avyayas — elsewhere the finite-verb reading
        of the same evidence must win (श्रूयताम्, न्यवसन्, मज्जन्ति are verbs, not participles)."""
        if not stem.endswith("at") or len(stem) < 4:
            return None
        base = stem[:-2]
        if base[-1] in VOWELS or base + "a" in self.SARVADI_TASIL:
            return None
        for up, rest in [("", base)] + list(peel_upasarga(base, min_rest=2)):
            for r in self.analyse_verb(rest + "anti"):
                if r.get("lakara") == "लट्" and r.get("dhatu"):
                    return (r["dhatu"], "शतृ", tuple([up] if up else []) + tuple(r.get("upasarga") or []))
        return None

    PARTICIPLE_SUFFIXES = [("itavat", "क्तवतु"), ("tavat", "क्तवतु"), ("mAna", "शानच्"), ("Ana", "शानच्"),
                           ("ita", "क्त"), ("ta", "क्त"), ("na", "क्त"), ("at", "शतृ"), ("tavya", "तव्यत्"),
                           ("anIya", "अनीयर्")]

    PRESENT_ONLY_STEMS = {"gam": ["gacC"], "iz": ["icC"], "yam": ["yacC"], "sTA": ["tizW"], "pA": ["pib"],
                          "dfS": ["paSy"], "sad": ["sId"]}

    @lru_cache(maxsize=50000)
    def _participle(self, stem):
        """(root, pratyaya, upasargas) if `stem` is a kṛdanta participle stem of a known root."""
        for suf, name in self.PARTICIPLE_SUFFIXES:
            if not stem.endswith(suf) or len(stem) - len(suf) < 1:
                continue
            base = stem[: -len(suf)]
            if name in ("क्त", "क्तवतु") and base.endswith(("w", "q", "d", "D", "g")):
                base = base  # dṛṣ-ṭa, bud-dha … handled by _guess_root's reversals
            present = name in ("शतृ", "शानच्")
            if name == "शानच्" and not base.endswith(("a", "ya", "aya", "nA", "RA", "nu", "Ru", "u")):
                continue                                # vikaraṇa must be visible before -māna/-āna
            root, ups = self._guess_root_with_upasarga(base, present=present)
            if root and present and deva_to_slp1(root) in self.PRESENT_ONLY_STEMS and \
                    not any(p in base for p in self.PRESENT_ONLY_STEMS[deva_to_slp1(root)]):
                continue          # gam+śatṛ must be gacchat, not *gamat
            if root:
                return (root, name, tuple(ups))
        return None

    def _guess_root_with_upasarga(self, s, present=False):
        """Peel upasargas, then find a root for the remaining verbal base."""
        options = [([], s)]
        for _ in range(3):
            new = []
            for ups, b in options:
                for up, rest in peel_upasarga(b):
                    new.append((ups + [up], rest))
            options += [n for n in new if n not in options]
        best = None
        for ups, b in options:
            r = self._guess_root(b[:-1] if present and b.endswith("a") else b, present)
            if not r:
                continue
            common = any("common" in (x.get("tags") or "") for x in self.roots.get(deva_to_slp1(r), []))
            key = (len(ups), 0 if common else 1, -len(r))
            if best is None or key < best[2]:
                best = (r, ups, key)
        return (best[0], best[1]) if best else (None, [])

    # ------------------------------------------------------------------ avyaya
    def analyse_avyaya(self, w):
        if w in AVYAYAS:
            return [{"type": "avyaya", "stem": slp1_to_deva(w), "kind": "avyaya",
                     "gloss": AVYAYA_GLOSS.get(w, ""), "evidence": "closed avyaya list", "_score": 5}]
        out = []
        t = self.lex.get(w, "")
        if "i" in t and not any(g in t for g in "mfn"):
            out.append({"type": "avyaya", "stem": slp1_to_deva(w), "kind": "avyaya",
                        "evidence": "lexicon: indeclinable (ind.)", "_score": 3.6})
        if w.startswith(("an", "a")) and not w.startswith(("anu", "aBi", "ava", "aDi", "api", "ati", "apa")):
            base = w[2:] if w.startswith("an") else w[1:]
            for r in self.analyse_avyaya(base) if len(base) > 3 else []:
                if r.get("kind") == "krdanta" and r.get("upasarga"):
                    r = dict(r)
                    r["evidence"] += "; नञ्-पूर्वकम् (न + …)"
                    r["nan"] = True
                    out.append(r)
        body, ups = w, []
        for up, rest in peel_upasarga(w, min_rest=3):   # also ava+āp -> avāp (a literal-prefix test missed it)
            body, ups = rest, [up]
            break
        pats = [("tvA", "क्त्वा", "समानकर्तृकयोः पूर्वकाले"), ("itvA", "क्त्वा", "समानकर्तृकयोः पूर्वकाले"),
                ("DvA", "क्त्वा", "समानकर्तृकयोः पूर्वकाले; झषस्तथोर्धोऽधः"),
                ("wvA", "क्त्वा", "समानकर्तृकयोः पूर्वकाले; ष्टुना ष्टुः"),
                ("tum", "तुमुन्", "तुमुन्ण्वुलौ क्रियायां क्रियार्थायाम्"), ("itum", "तुमुन्", "तुमुन्ण्वुलौ क्रियायां क्रियार्थायाम्")]
        for suf, name, sutra in pats:
            if w.endswith(suf) and len(w) > len(suf) + 1:
                root, rups = self._guess_root_with_upasarga(w[: -len(suf)])
                out.append({"type": "avyaya", "kind": "krdanta", "pratyaya": name, "sutra": sutra,
                            "stem": root or slp1_to_deva(w[: -len(suf)]), "upasarga": rups,
                            "evidence": f"kṛt suffix «{slp1_to_deva(suf)}»" + ("" if root else " (root not identified)"),
                            "_score": 4.2 if root else 1.5})
        if ups and (body.endswith("ya") or body.endswith("tya")) and not w.endswith("aya"):
            root, rups = self._guess_root_with_upasarga(w[:-3] if w.endswith("tya") else w[:-2])
            if root and rups:
                ups = rups
                out.append({"type": "avyaya", "kind": "krdanta", "pratyaya": "ल्यप्",
                            "sutra": "समासेऽनञ्पूर्वे क्त्वो ल्यप्", "stem": root, "upasarga": ups,
                            "evidence": "upasarga + root + «य»", "_score": 4.2})
        for suf, name in (("vat", "वति"), ("taH", "तसिल्"), ("tra", "त्रल्"), ("dA", "दा"), ("SaH", "शस्")):
            base = w[: -len(suf)]
            nan_base = base[2:] if base.startswith("an") else base[1:] if base.startswith("a") else None
            ok = base in self.lex or (nan_base is not None and nan_base in self.lex and self._nominal(self.lex[nan_base]))
            if suf == "taH" and w.endswith(suf) and self._satr_genitive(base):
                ok = False              # bruvataḥ / paśyataḥ: genitive of a śatṛ participle, not -tas
            if w.endswith(suf) and len(w) > len(suf) + 1 and ok:
                nominal = (base in self.lex and self._nominal(self.lex[base])) or nan_base in self.lex
                strong = nominal and suf == "taH"
                if strong and base not in self.SARVADI_TASIL and w[:-1] not in self.SARVADI_TASIL and w.endswith("aH") and self._nominal(self.lex.get(w[:-1], "")):
                    strong = False          # hitaḥ = hita- (a lexicon adjective) + ḥ, not hi + tasil
                out.append({"type": "avyaya", "kind": "taddhita", "pratyaya": name,
                            "stem": slp1_to_deva(base), "evidence": f"taddhita «{slp1_to_deva(suf)}»",
                            "_score": 3.7 if strong else 2.5})
        return out

    SARVADI_TASIL = frozenset("sarva viSva anya itara ubhaya eka pUrva para avara dakziRa uttara apara "
                              "aDara sva antara ta ya eta ka ita ata sarvata".split())

    def _satr_genitive(self, base):
        """True when «base+taḥ» is better read as the genitive/ablative singular of a śatṛ stem
        (bruvat-, paśyat-, vīkṣat-): the thematic base must make a present 3pl «base+nti», and it
        must not be a sarvādi pronominal (sarva-, anya-, which take -tas); pṛṣṭha- etc. fail the verb test."""
        if not base.endswith("a") or base in self.SARVADI_TASIL:
            return False
        forms = [base + "nti"] + [rest + "nti" for _, rest in peel_upasarga(base, min_rest=2)]
        return any(any(r.get("lakara") == "लट्" for r in self.analyse_verb(f)) for f in forms)

    SPECIAL_KRT_BASES = {"hi": "hA", "is": "yaj", "iz": "yaj", "uk": "vac", "uz": "vas", "uD": "vah",
                         "gfhI": "grah", "dat": "dA", "ha": "han", "ga": "gam", "ma": "man", "ta": "tan",
                         "ra": "ram", "ya": "yam", "nata": "nam", "hf": "hf", "pf": "praC", "sTi": "sTA",
                         "zWi": "sTA", "gI": "gE", "pI": "pA", "pfz": "pracC", "pfC": "pracC", "BU": "BU", "kf": "kf", "mf": "mf", "Df": "Df",
                         "Sru": "Sru", "Sro": "Sru", "yok": "yuj", "yuk": "yuj", "muk": "muc"}

    @lru_cache(maxsize=50000)
    def _guess_root(self, s, present=False):
        """Root (Devanagari) for a kṛt/verbal base such as Sru (Srutvā), dfz (dfzwvA), gam|ga (gatvA)."""
        if not s:
            return None
        cands = [s]
        if s in self.SPECIAL_KRT_BASES:
            cands.insert(0, self.SPECIAL_KRT_BASES[s])
        if s.endswith("i") and len(s) > 2:          # iṭ augment: upAs-i-tvA, nivedaya-i-tvA
            cands.append(s[:-1])
            if s.endswith("ayi"):
                cands.append(s[:-3])                 # causative ay + iṭ
        if s.endswith("ay"):
            cands.append(s[:-2])                     # causative stem
        more = []
        for c in cands:
            more.append(c)
            if c.endswith("a") and len(c) >= 2:
                more += [c + "m", c + "n"]           # anunāsika dropped: ga(m)-tvā, ha(n)-tvā
            if c.endswith(("dD", "gD", "bD")):
                more += [c[:-2] + "D", c[:-2] + "h", c[:-2] + "B"]   # bud-dhvā, dag-dhvā
            if c.endswith(("z", "w")):
                more += [c[:-1] + "S", c[:-1] + "z", c[:-1] + "j", c[:-1] + "c"]
            if c.endswith("k"):
                more += [c[:-1] + "c", c[:-1] + "j"]
            if c.endswith("g"):
                more += [c[:-1] + "j", c[:-1] + "h"]
            if c.endswith("d"):
                more += [c[:-1] + "D", c[:-1] + "h"]
            if c.endswith("Ir") or c.endswith("Ur"):
                more.append(c[:-2] + "F")            # tīr-tvā < tṝ
            if c.endswith(("tt",)):
                more.append(c[:-2] + "A")            # dat-tvā < dā
        # guṇa / vṛddhi reversal on the last vowel
        rev = []
        for c in more:
            rev.append(c)
            for a_, b_ in (("e", "i"), ("o", "u"), ("ar", "f"), ("E", "i"), ("O", "u"), ("Ar", "f"),
                           ("A", "a"), ("av", "u"), ("ay", "i"), ("Av", "u"), ("I", "i"), ("U", "u")):
                j = c.rfind(a_)
                if j >= 0:
                    rev.append(c[:j] + b_ + c[j + len(a_):])
        for c in rev:
            if c in self.roots:
                return slp1_to_deva(c)
        return None

    # ------------------------------------------------------------------ main entry
    def analyse(self, word, scheme="deva", max_readings=5):
        w = word if scheme == "slp1" else iast_to_slp1(word) if scheme == "iast" else deva_to_slp1(word)
        w = _norm_slp1(w.strip("'").strip())
        if not w:
            return []
        readings = []
        readings += self.analyse_avyaya(w)
        nouns = self.analyse_noun(w)
        verbs = self.analyse_verb(w)
        readings += nouns[:max_readings]
        readings += verbs[:max_readings]
        # a validated noun outranks a pattern-only verb and vice versa
        def rank(r):
            s = r["_score"]
            if r["type"] == "verb" and w.endswith(("ti", "nti", "si", "mi", "at", "an", "a", "uH", "e", "O", "tu", "et", "It", "At")):
                s += 0.3
            # -yate/-yante is a passive/middle finite form; its "…yata" noun reading is a participle-like artefact
            if r["type"] == "noun" and w.endswith(("yate", "yante")) and str(r.get("stem", "")).endswith(("यत", "यतिन्", "यत्")):
                s -= 1.0
            return -s
        readings.sort(key=lambda r: (rank(r), r["type"], str(r.get("stem") or r.get("dhatu"))))
        return readings[:max_readings]


def _format(r):
    if r["type"] == "noun":
        s = f"{r['stem']} — {r['case_name']}, {r['vacana']}, {r['gender']}"
        if r.get("members"):
            s += f" [समास? {' + '.join(r['members'])}]"
    elif r["type"] == "verb":
        s = (f"√{r['dhatu']} (गण {r['gana']}, {r['artha']}) — {r['lakara']}, {r['purusha']}, "
             f"{r['vacana']}, {r['pada']}")
        if r["upasarga"]:
            s = "+".join(r["upasarga"]) + " " + s
    else:
        s = f"{r['stem']} — अव्ययम् ({r.get('pratyaya') or r.get('kind')})"
    return f"{s}   [{r['evidence']}; score {r['_score']:.2f}]"


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Rule-based analysis of Sanskrit word forms (Devanagari or IAST).")
    ap.add_argument("words", nargs="+")
    ap.add_argument("--iast", action="store_true")
    ap.add_argument("-n", type=int, default=3)
    a = ap.parse_args()
    pa = PadaAnalyser()
    for w in a.words:
        print(w)
        for r in pa.analyse(w, scheme="iast" if a.iast else "deva", max_readings=a.n):
            print("   ", _format(r))
