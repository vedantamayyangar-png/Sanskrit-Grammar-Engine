#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
padakosha_builder.py — turns sarga_analyser's per-verse rows into the *Padakosha* JSON layout used in
Ramayana_Padakosha.json:

    {"corpus_meta": {...}, "words": [ {word, iast, verses, word_type, pratipadika, dhatu, dhatu_gana,
                                       meaning_en, gender, number, case, paradigm, samasa_type,
                                       samasa_split, samasa_component_meanings, pratyaya,
                                       ashtadhyayi_ref, ashtadhyayi_url, notes}, ... ]}

* one entry per distinct printed word (Devanagari), in order of first occurrence; "verses" lists every
  occurrence (repeats kept, as in the reference file);
* all grammatical fields are in Devanagari Sanskrit; only meaning_en (and the component meanings) are English;
* meaning_en is NOT generated (no local translation engine). Supply --glossary FILE.json
  ({"word or pratipadika": "meaning", ...}) to fill it; otherwise it is "".
* sūtra numbers come from small, conservative lookup tables below (samāsa type, lakāra, kāraka-vibhakti,
  common kṛt/taddhita pratyayas, sarvanāma/saṅkhyā/avyaya). Where the table has no entry the ref/url are
  left "" and the note says so — nothing is invented.
"""
import re
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate as tl

try:                                    # hand-verified samāsa citations, used when my own table has no entry
    import citation_lookup as _cite
except Exception:
    _cite = None

URL = "https://ashtadhyayi.com/sutraani/{}/{}/{}"

KANDA = {1: "बालकाण्डः / Bala Kanda", 2: "अयोध्याकाण्डः / Ayodhya Kanda", 3: "अरण्यकाण्डः / Aranya Kanda",
         4: "किष्किन्धाकाण्डः / Kishkindha Kanda", 5: "सुन्दरकाण्डः / Sundara Kanda",
         6: "युद्धकाण्डः / Yuddha Kanda", 7: "उत्तरकाण्डः / Uttara Kanda"}
GANA = {1: "भ्वादिः", 2: "अदादिः", 3: "जुहोत्यादिः", 4: "दिवादिः", 5: "स्वादिः", 6: "तुदादिः", 7: "रुधादिः",
        8: "तनादिः", 9: "क्र्यादिः", 10: "चुरादिः"}
CASES = {1: "प्रथमा", 2: "द्वितीया", 3: "तृतीया", 4: "चतुर्थी", 5: "पञ्चमी", 6: "षष्ठी", 7: "सप्तमी", 8: "सम्बोधनम्"}
NUMS = {"e": "एकवचनम्", "d": "द्विवचनम्", "b": "बहुवचनम्"}
CASE_SUTRA = {1: "2.3.46 (प्रातिपदिकार्थलिङ्गपरिमाणवचनमात्रे प्रथमा)", 2: "2.3.2 (कर्मणि द्वितीया)",
              3: "2.3.18 (कर्तृकरणयोस्तृतीया)", 4: "2.3.13 (चतुर्थी सम्प्रदाने)", 5: "2.3.28 (अपादाने पञ्चमी)",
              6: "2.3.50 (षष्ठी शेषे)", 7: "2.3.36 (सप्तम्यधिकरणे च)", 8: "2.3.47 (सम्बोधने च)"}
LAKARA_SUTRA = {"लट्": "3.2.123 (वर्तमाने लट्)", "लिट्": "3.2.115 (परोक्षे लिट्)", "लुङ्": "3.2.110 (लुङ्)",
                "लङ्": "3.2.111 (अनद्यतने लङ्)", "लुट्": "3.3.15 (अनद्यतने लुट्)", "लृट्": "3.3.13 (लृट् शेषे च)",
                "लोट्": "3.3.162 (लोट् च)", "विधिलिङ्": "3.3.161 (विधिनिमन्त्रणामन्त्रणाधीष्टसंप्रश्नप्रार्थनेषु लिङ्)",
                "आशीर्लिङ्": "3.3.173 (आशिषि लिङ्लोटौ)", "लृङ्": "3.3.139 (लिङ्निमित्ते लृङ् क्रियातिपत्तौ)"}
SAMASA_SUTRA = {"कर्मधारय": "2.1.57 (विशेषणं विशेष्येण बहुलम्)", "षष्ठीतत्पुरुष": "2.2.8 (षष्ठी)",
                "द्वितीयातत्पुरुष": "2.1.24 (द्वितीया श्रितातीतपतितगतात्यस्तप्राप्तापन्नैः)",
                "तृतीयातत्पुरुष": "2.1.30 (तृतीया तत्कृतार्थेन गुणवचनेन)", "चतुर्थीतत्पुरुष": "2.1.36 (चतुर्थी तदर्थार्थबलिहितसुखरक्षितैः)",
                "पञ्चमीतत्पुरुष": "2.1.37 (पञ्चमी भयेन)", "सप्तमीतत्पुरुष": "2.1.40 (सप्तमी शौण्डैः)",
                "बहुव्रीहि": "2.2.23 (शेषो बहुव्रीहिः)", "द्वन्द्व": "2.2.29 (चार्थे द्वन्द्वः)",
                "द्विगु": "2.1.52 (संख्यापूर्वो द्विगुः)", "नञ्तत्पुरुष": "2.2.6 (नञ्)",
                "नञ्": "2.2.6 (नञ्)", "नञ्बहुव्रीहि": "2.2.24 (अनेकमन्यपदार्थे) सह वार्त्तिकम् (नञोऽस्त्यर्थानां…)", "उपपदतत्पुरुष": "2.2.19 (उपपदमतिङ्)", "अव्ययीभाव": "2.1.5 (अव्ययं विभक्तिसमीप…)",
                "प्रादि": "2.2.18 (कुगतिप्रादयः)", "तत्पुरुष": "2.1.22 (तत्पुरुषः)"}
KRT_SUTRA = {"क्त": "1.1.26 (क्तक्तवतू निष्ठा) व 3.2.102 (निष्ठा)", "क्तवतु": "1.1.26 (क्तक्तवतू निष्ठा)",
             "क्त्वा": "3.4.21 (समानकर्तृकयोः पूर्वकाले)", "ल्यप्": "7.1.37 (समासेऽनञ्पूर्वे क्त्वो ल्यप्)",
             "शतृ": "3.2.124 (लटः शतृशानचावप्रथमासमानाधिकरणे)", "शानच्": "3.2.124 (लटः शतृशानचौ)",
             "ल्युट्": "3.3.115 (ल्युट् च)", "तव्यत्": "3.1.96 (तव्यत्तव्यानीयरः)", "अनीयर्": "3.1.96 (तव्यत्तव्यानीयरः)", "तुमुन्": "3.3.10 (तुमुन्ण्वुलौ क्रियायां क्रियार्थायाम्)",
             "ण्वुल्": "3.1.133 (ण्वुल्तृचौ)", "तृच्": "3.1.133 (ण्वुल्तृचौ)", "घञ्": "3.3.18 (भावे)",
             "अच्": "3.1.134 (नन्दिग्रहिपचादिभ्यो ल्युणिन्यचः)", "ण्यत्": "3.1.124 (ऋहलोर्ण्यत्)"}
KRT_NAME = {"क्त": "क्तान्तम्", "क्तवतु": "क्तवतुप्रत्ययान्तम्", "क्त्वा": "क्त्वान्तम्", "ल्यप्": "ल्यबन्तम्",
            "शतृ": "शतृप्रत्ययान्तम्", "शानच्": "शानच्प्रत्ययान्तम्", "ल्युट्": "ल्युडन्तम्", "तव्यत्": "तव्यदन्तम्",
            "अनीयर्": "अनीयरन्तम्", "तुमुन्": "तुमुन्नन्तम्", "घञ्": "घञन्तम्", "ण्वुल्": "ण्वुलन्तम्", "तृच्": "तृजन्तम्", "अच्": "अजन्तम्"}
TADDHITA_SUTRA = {"त्व": "5.1.119 (तस्य भावस्त्वतलौ)", "मतुप्": "5.2.94 (तदस्यास्त्यस्मिन्निति मतुप्)", "विनि": "5.2.121 (अस्मायामेधास्रजो विनिः)",
                  "इनि": "5.2.115 (अत इनिठनौ)"}
PRONOUNS = {"तद्", "एतद्", "इदम्", "अदस्", "यद्", "किम्", "अस्मद्", "युष्मद्", "सर्व", "विश्व", "अन्य", "अपर",
            "पर", "एक", "भवत्", "स्व", "उभ", "इतर", "कतर", "कतम"}
NUMERALS = {"द्वि", "त्रि", "चतुर्", "पञ्चन्", "षष्", "सप्तन्", "अष्टन्", "नवन्", "दशन्", "शत", "सहस्र", "विंशति", "त्रिंशत्"}
NO_NUMERAL_ONE = {"एक"}          # 'एक' is listed as sarvanāma; kept out of NUMERALS on purpose
SUTRA_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def deva(iast):
    return tl(iast, sanscript.IAST, sanscript.DEVANAGARI)


def _final_m(s):
    """Reference file spells a final anusvāra as म् (…तम्, not …तं)."""
    return s[:-1] + "म्" if s.endswith("ं") else s


def _final_m_iast(s):
    return s[:-1] + "m" if s.endswith(("ṃ", "ṁ")) else s


def _head(s):
    """'क्त (निष्ठा)' / 'क्त्वा — x' -> 'क्त' / 'क्त्वा'."""
    return re.split(r"[\s(—,;/]", (s or "").strip(), maxsplit=1)[0]


def norm_gender(g):
    out = []
    for part in re.split(r"[/,]", str(g or "")):
        p = part.strip().lower()
        if not p:
            continue
        if "नपुं" in p or p in ("n", "neut", "neuter", "napumsaka"):
            out.append("नपुंसकलिङ्गम्")
        elif "स्त्री" in p or p in ("f", "fem", "feminine"):
            out.append("स्त्रीलिङ्गम्")
        elif "पुं" in p or p in ("m", "masc", "masculine"):
            out.append("पुंल्लिङ्गम्")
        else:
            out.append(part.strip())
    return "/".join(dict.fromkeys(out))


def norm_number(n):
    n = str(n or "")
    if n in NUMS:
        return NUMS[n]
    for key, val in (("एक", "एकवचनम्"), ("द्वि", "द्विवचनम्"), ("बहु", "बहुवचनम्")):
        if key in n:
            return val
    return n


def norm_purusha(p):
    p = str(p or "")
    for key in ("प्रथम", "मध्यम", "उत्तम"):
        if key in p:
            return key + "पुरुषः"
    return p


def norm_pada(p):
    p = str(p or "")
    if "कर्मणि" in p:
        return "आत्मनेपदम्, कर्मणि"
    for key, val in (("परस्मै", "परस्मैपदम्"), ("आत्मने", "आत्मनेपदम्"), ("उभय", "उभयपदम्")):
        if key in p:
            return val
    return p


def norm_lakara(l):
    l = str(l or "").replace("लकारः", "").replace("लकार", "").strip()
    return l


def ending_class(stem, gender):
    last = (stem or "")[-1:]
    cls = {"अ": "अकारान्त", "आ": "आकारान्त", "इ": "इकारान्त", "ी": "ईकारान्त", "ि": "इकारान्त", "ु": "उकारान्त",
           "ू": "ऊकारान्त", "ृ": "ऋकारान्त", "ा": "आकारान्त"}.get(last)
    if cls is None and last and "\u0915" <= last <= "\u0939":     # consonant letter, inherent अ
        cls = "अकारान्त"
    elif cls is None and last == "्":
        cls = "हलन्त"
    return f"{cls} {gender.replace('म्', '')}".strip() if cls else ""


def sutra_url(ref):
    m = SUTRA_RE.search(ref or "")
    return URL.format(*m.groups()) if m else ""


def _sam_type_name(t):
    """'षष्ठीतत्पुरुषः' -> 'षष्ठीतत्पुरुष' (table key)."""
    t = re.split(r"[\s(—]", (t or "").strip(), maxsplit=1)[0]
    return t.rstrip("ः")


class PadakoshaBuilder:
    def __init__(self, glossary=None, analyser=None):
        """analyser: the PadaAnalyser (optional) — used to look up gaṇa/artha of a kṛt root and to check
        that a taddhita base is a real lexicon word."""
        self.glossary = glossary or {}
        self.pa = analyser
        self.entries = {}          # word -> entry   (insertion-ordered)
        self._sig = {}             # word -> signature of the reading that built the entry
        self.verse_nums = set()

    # ---------------------------------------------------------------- public
    def add_row(self, verse_num, row):
        """row: one dict from sarga_analyser.analyse_verse (needs _reading, _sam, _iast, pada, confidence)."""
        self.verse_nums.add(verse_num)
        word = _final_m(row["pada"])
        entry, sig = self._entry(word, row)
        if word not in self.entries:
            entry["verses"] = [verse_num]
            self.entries[word] = entry
            self._sig[word] = sig
            return
        old = self.entries[word]
        old["verses"].append(verse_num)
        if sig != self._sig[word]:
            alt = f"श्लोक {verse_num}: अन्यः पाठः — {entry['word_type']}, {entry['pratipadika'] or entry['dhatu']}"
            if entry["case"] or entry["number"]:
                alt += f", {entry['case']} {entry['number']}".rstrip()
            if alt not in old["notes"]:
                old["notes"] = (old["notes"] + " | " if old["notes"] else "") + alt

    def build(self, kanda, sarga, source_file, verses_total=None):
        lo, hi = (min(self.verse_nums), max(self.verse_nums)) if self.verse_nums else (0, 0)
        meta = {
            "source_file": source_file,
            "kanda": KANDA.get(kanda, str(kanda)),
            "sarga": sarga,
            "verses_covered": f"{lo}-{hi}" if lo != hi else str(lo),
            "language_policy": "meaning_en in English; all grammatical fields in Sanskrit (Devanagari)",
            "ashtadhyayi_url_pattern": "https://ashtadhyayi.com/sutraani/{adhyaya}/{pada}/{sutra}",
            "important_disclaimer": (
                "Automatically generated by sarga_analyser.py from local tools only (no LLM, no internet). "
                "Rows whose notes say 'confidence: guess/default/pattern-only/none' must be checked by hand. "
                "ashtadhyayi_ref/url come from a fixed table of governing rules (samasa type, lakara, vibhakti, "
                "common krt/taddhita pratyayas); where the table has no entry they are left empty. "
                "meaning_en is empty unless a --glossary file was supplied."),
        }
        return {"corpus_meta": meta, "words": list(self.entries.values())}

    # --------------------------------------------------------------- internals
    def _gloss(self, *keys):
        for k in keys:
            if k and k in self.glossary:
                return self.glossary[k]
        return ""

    def _entry(self, word, row):
        r, sam = row.get("_reading"), row.get("_sam")
        e = {"word": word, "iast": _final_m_iast(row.get("_iast") or tl(word, sanscript.DEVANAGARI, sanscript.IAST)),
             "verses": [], "word_type": "", "pratipadika": "", "dhatu": "", "dhatu_gana": "", "meaning_en": "",
             "gender": "", "number": "", "case": "", "paradigm": "", "samasa_type": "", "samasa_split": "",
             "samasa_component_meanings": {}, "pratyaya": "", "ashtadhyayi_ref": "", "ashtadhyayi_url": "",
             "notes": ""}
        refs = []                                   # candidate ashtadhyayi_ref strings, best first
        if r is None:
            e["word_type"] = "अनिर्णीतम्"
        elif r["type"] == "noun":
            self._noun(e, r, refs)
        elif r["type"] == "verb":
            self._verb(e, r, refs)
        else:
            self._avyaya(e, r, refs)
        if sam and sam.get("members"):
            self._samasa(e, sam, refs)
        e["meaning_en"] = self._gloss(word, e["pratipadika"], e["dhatu"].split(" (")[0])
        if refs:
            e["ashtadhyayi_ref"] = refs[0]
            e["ashtadhyayi_url"] = sutra_url(refs[0])
        extra = e.pop("notes_extra", "")
        e["notes"] = self._notes(e, row, refs) + (f"; {extra}" if extra else "")
        sig = (e["word_type"], e["pratipadika"], e["dhatu"], e["case"], e["number"], e["gender"])
        return e, sig

    def _noun(self, e, r, refs):
        stem = r["stem"]
        gender = norm_gender(r.get("gender"))
        e.update(pratipadika=stem, gender=gender, number=NUMS.get(r["num"], norm_number(r["num"])),
                 case=CASES.get(r["case"], str(r.get("case_name", ""))))
        model = r.get("model") or ""
        ec = ending_class(stem, gender)
        e["paradigm"] = f"{model}शब्दवत्" + (f" ({ec})" if ec else "")
        e["word_type"] = "नाम"
        k = r.get("krt")
        if k:
            p = _head(k["pratyaya"])
            ups = ", ".join(k.get("upasarga") or [])
            e["dhatu"] = k["dhatu"] + (f" (उपसर्गः {ups})" if ups else "")
            e["dhatu_gana"] = self._root_info(k["dhatu"])
            e["pratyaya"] = k["pratyaya"]
            e["word_type"] = f"कृदन्तम् ({KRT_NAME.get(p, p + '-प्रत्ययान्तम्')})"
            if p in KRT_SUTRA:
                refs.append(KRT_SUTRA[p])
        elif stem in NUMERALS:
            e["word_type"] = "सङ्ख्यावाचकम्"
            refs.append("1.1.23 (बहुगणवतुडति सङ्ख्या)")
        elif stem in PRONOUNS:
            e["word_type"] = "सर्वनाम"
            refs.append("1.1.27 (सर्वादीनि सर्वनामानि)")
        elif self._taddhita_of(stem):
            t = self._taddhita_of(stem)
            e["word_type"] = "तद्धितान्त नाम"
            e["pratyaya"] = t + " (अनुमितम्)"
            refs.append(TADDHITA_SUTRA.get(t, ""))
        if r["case"] in CASE_SUTRA and not refs:
            refs.append(CASE_SUTRA[r["case"]])
        refs[:] = [x for x in refs if x]

    def _verb(self, e, r, refs):
        ups = ", ".join(r.get("upasarga") or [])
        e["dhatu"] = r["dhatu"] + (f" (उपसर्गः {ups})" if ups else "")
        e["dhatu_gana"] = self._gana(r.get("gana"), r.get("artha"), r.get("all_ganas"))
        lak = norm_lakara(r["lakara"])
        e["word_type"] = f"क्रियापदम् ({lak}लकारः)" if lak else "क्रियापदम्"
        e["number"] = norm_number(r.get("vacana"))
        e["case"] = f"{norm_purusha(r.get('purusha'))} ({norm_pada(r.get('pada'))})"
        e["paradigm"] = f"{lak}लकारः {norm_purusha(r.get('purusha'))} {norm_pada(r.get('pada'))}".strip()
        e["pratyaya"] = f"तिङ् ({lak})" + ("; णिच्" if r.get("nijanta") else "")
        if lak in LAKARA_SUTRA:
            refs.append(LAKARA_SUTRA[lak])

    def _avyaya(self, e, r, refs):
        e["pratipadika"] = r.get("stem", "")
        e["paradigm"] = "अव्ययम्"
        kind = r.get("kind")
        if kind == "krdanta":
            p = _head(r.get("pratyaya", ""))
            ups = ", ".join(r.get("upasarga") or [])
            e["word_type"] = f"कृदन्तम् ({KRT_NAME.get(p, p + '-प्रत्ययान्तम्')})"
            e["paradigm"] = f"अव्ययम् ({KRT_NAME.get(p, p)} गेरुण्डम्)"
            e["pratyaya"] = r.get("pratyaya", "")
            # PadaAnalyser puts the ROOT (Devanagari) in "stem" for kṛdanta avyayas, or the bare string
            # with "(root not identified)" in the evidence when it could not find one.
            root_known = "root not identified" not in (r.get("evidence") or "")
            e["pratipadika"] = ""
            if root_known and r.get("stem"):
                e["dhatu"] = r["stem"] + (f" (उपसर्गः {ups})" if ups else "")
                e["dhatu_gana"] = self._root_info(r["stem"])
            if r.get("nan"):
                e["notes_extra"] = "नञ्-पूर्वकम्"
            refs.append(KRT_SUTRA.get(p) or (r.get("sutra") or ""))
        elif kind == "taddhita":
            e["word_type"] = "तद्धितान्त नाम"
            e["pratyaya"] = r.get("pratyaya", "")
            refs.append(TADDHITA_SUTRA.get(_head(r.get("pratyaya", "")), ""))
        else:
            e["word_type"] = "अव्ययम्"
            refs.append("1.1.37 (स्वरादिनिपातमव्ययम्)")
        refs[:] = [x for x in refs if x]

    def _samasa(self, e, sam, refs):
        t = sam.get("type") or str(sam.get("type_guess", "")).split(" — ")[0]
        reason = str(sam.get("type_guess", "")).split(" — ", 1)[1] if " — " in str(sam.get("type_guess", "")) else ""
        members = sam["members"]
        e["word_type"] = f"समासः ({t})"
        e["samasa_type"] = f"{t} ({reason})" if reason else t
        e["samasa_split"] = " + ".join(members)
        e["samasa_component_meanings"] = {m: self._gloss(m, m.rstrip("ःम्")) for m in members}
        if sam.get("stem") and not e["pratipadika"]:
            e["pratipadika"] = sam["stem"]
        s = SAMASA_SUTRA.get(_sam_type_name(t))
        if not s and _cite is not None:
            try:
                _, citation, known = _cite.lookup_samasa_citation(str(sam.get("type_guess") or t))
                if known and citation:
                    s = citation.replace("अष्टाध्यायी ", "", 1)
            except Exception:
                s = None
        if s:
            refs.insert(0, s)           # for a compound the governing rule is the samāsa sūtra

    @staticmethod
    def _gana(g, artha, all_ganas=None):
        gs = [x for x in (all_ganas or []) if x] or ([g] if g not in (None, "") else [])
        if not gs:
            return ""
        names = []
        for x in gs:
            n = GANA.get(x) if isinstance(x, int) else (GANA.get(int(x)) if str(x).isdigit() else str(x))
            if n and n not in names:
                names.append(n)
        name = "/".join(names)
        return f"{name} ({artha})" if artha else name

    def _root_info(self, root_deva):
        """(gana-cell) for a Devanagari root, from PadaAnalyser.roots (Dhatu-Manjari), or ''."""
        if not self.pa or not root_deva:
            return ""
        key = tl(root_deva.strip(), sanscript.DEVANAGARI, sanscript.SLP1)
        recs = (getattr(self.pa, "roots", {}) or {}).get(key) or []
        if not recs:
            return ""
        return self._gana(recs[0].get("gana"), recs[0].get("artha"),
                          sorted({x.get("gana") for x in recs if x.get("gana")}))

    def _lex_has(self, deva_stem):
        if not self.pa:
            return False
        lex = getattr(self.pa, "lex", {}) or {}
        slp = tl(deva_stem, sanscript.DEVANAGARI, sanscript.SLP1)
        return slp in lex or slp + "a" in lex

    def _taddhita_of(self, stem):
        """PadaAnalyser never labels taddhita nouns, so infer the three unambiguous matvarthīya/bhāva
        shapes (-वत्/-मत्, -विन्, -त्व) and only when the base is itself a lexicon word."""
        for suf, name in (("वत्", "मतुप्"), ("मत्", "मतुप्"), ("विन्", "विनि"), ("त्व", "त्व")):
            if stem.endswith(suf) and len(stem) > len(suf) + 1:
                base = stem[:-len(suf)]
                if self._lex_has(base) or self._lex_has(base + "्"):
                    return name
        return ""

    @staticmethod
    def _notes(e, row, refs):
        bits = [f"confidence: {row.get('confidence', '')}"]
        if row.get("alternatives"):
            bits.append(f"वैकल्पिकपठनानि: {row['alternatives']}")
        if not refs:
            bits.append("सूत्रं सारण्यां नास्ति — हस्तेन योज्यम्")
        if not e["meaning_en"]:
            bits.append("meaning_en not generated")
        return "; ".join(bits)
