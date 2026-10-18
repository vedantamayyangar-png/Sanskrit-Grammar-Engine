#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sandhi Rulebook Compiler / Engine
---------------------------------
Compiles the supplied sandhi_rulebook.json into executable Python rule objects.

Design principle:
- The JSON rulebook remains the source of truth.
- Python supplies the computational interpretation of each rule.
- A rule may be:
    EXECUTABLE   -> deterministic/mostly deterministic implementation
    CONDITIONAL  -> executable only when the required grammatical context is supplied
    MANUAL       -> retained as a rule record, but not guessed automatically
- No English grammar terminology is emitted by the engine's Sanskrit analysis output.
  English is used only in programmer-facing diagnostics/docstrings.

This is intentionally a first-pass engine. It does NOT pretend that every prose rule
in a traditional grammar book can be reduced to a safe two-word transformation without
additional grammatical context.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Iterable, Any
import json
import argparse
import re


# ---------------------------------------------------------------------------
# Sanskrit phonological classes
# ---------------------------------------------------------------------------

VOWELS = set("अआइईउऊऋॠऌएऐओऔ")
SHORT_VOWELS = set("अइउऋऌ")
LONG_VOWELS = set("आईऊॠएऐओऔ")

IK = set("इईउऊऋॠऌ")
EC = set("एओऐऔ")
AC = VOWELS

GUTTURAL = set("कखगघङ")
PALATAL = set("चछजझञ")
CEREBRAL = set("टठडढण")
DENTAL = set("तथदधन")
LABIAL = set("पफबभम")
SEMIVOWELS = set("यरलव")
SIBILANTS = set("शषस")
NASALS = set("ङञणनम")
ANUSVARA = "ं"
VISARGA = "ः"
AVAGRAHA = "ऽ"

# जश् = third member of each वर्ग + ब? The standard जश् set used here is:
JASH = {"ग", "ज", "ड", "द", "ब"}

# झल् = all non-vowels/non-semivowels/non-nasals in the traditional pratyahara.
JHAL = set("कखगघचछजझटठडढतथदधपफबभशषसह")


def is_vowel(ch: str) -> bool:
    return ch in VOWELS


def is_soft_consonant(ch: str) -> bool:
    return ch in (set("गघजझडढदधबभ") | NASALS | SEMIVOWELS)


def is_hard_consonant(ch: str) -> bool:
    return ch in set("कखचछटठतथपफशषस")


def normalize_word(s: str) -> str:
    """Normalize whitespace only; do not alter Sanskrit orthography."""
    return re.sub(r"\s+", "", s or "")


def last_orthographic_char(s: str) -> Optional[str]:
    s = normalize_word(s)
    return s[-1] if s else None


def first_orthographic_char(s: str) -> Optional[str]:
    s = normalize_word(s)
    return s[0] if s else None


# ---------------------------------------------------------------------------
# Rule representation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SandhiResult:
    rule_id: str
    rule_name: str
    category: str
    left: str
    right: str
    result: str
    status: str = "निश्चितम्"
    note: str = ""


@dataclass
class RuleRecord:
    id: str
    name: str
    category: str
    source: dict[str, Any]
    implementation: str
    apply_fn: Optional[Callable[[str, str, dict[str, Any]], Optional[str]]] = None

    def apply(self, left: str, right: str, context: Optional[dict[str, Any]] = None) -> Optional[SandhiResult]:
        if self.apply_fn is None:
            return None
        context = context or {}
        result = self.apply_fn(normalize_word(left), normalize_word(right), context)
        if result is None:
            return None
        return SandhiResult(
            rule_id=self.id,
            rule_name=self.name,
            category=self.category,
            left=left,
            right=right,
            result=result,
        )



VOWEL_MATRAS = {
    "अ": "", "आ": "ा", "इ": "ि", "ई": "ी", "उ": "ु", "ऊ": "ू",
    "ऋ": "ृ", "ॠ": "ॄ", "ऌ": "ॢ", "ए": "े", "ऐ": "ै", "ओ": "ो", "औ": "ौ"
}
MATRA_TO_VOWEL = {v:k for k,v in VOWEL_MATRAS.items() if v}

def _strip_terminal_markers(word: str) -> tuple[str, str]:
    """Return word without terminal visarga/anusvāra and the marker."""
    if word.endswith(("ः", "ं")):
        return word[:-1], word[-1]
    return word, ""

def final_vowel(word: str) -> Optional[str]:
    """Return the final pronounced vowel of a simple Devanagari word."""
    w, _ = _strip_terminal_markers(normalize_word(word))
    if not w:
        return None
    if w[-1] in VOWELS:
        return w[-1]
    if w[-1] in MATRA_TO_VOWEL:
        return MATRA_TO_VOWEL[w[-1]]
    # Final consonant without halant carries inherent अ.
    if w[-1] in JHAL or w[-1] in SEMIVOWELS or w[-1] in NASALS or w[-1] in {"ह"}:
        return "अ"
    # Search the last vowel-bearing sign.
    for ch in reversed(w):
        if ch in VOWELS:
            return ch
        if ch in MATRA_TO_VOWEL:
            return MATRA_TO_VOWEL[ch]
    return None

def _final_consonant_and_vowel(word: str):
    """Return (base-without-vowel-marker, final-vowel, terminal-marker)."""
    w, marker = _strip_terminal_markers(normalize_word(word))
    if not w:
        return w, None, marker
    if w[-1] in VOWELS:
        return w[:-1], w[-1], marker
    if w[-1] in MATRA_TO_VOWEL:
        return w[:-1], MATRA_TO_VOWEL[w[-1]], marker
    if w[-1] in JHAL or w[-1] in SEMIVOWELS or w[-1] in NASALS or w[-1] in {"ह"}:
        return w, "अ", marker
    return w, final_vowel(w), marker

def replace_final_vowel(word: str, vowel: str) -> str:
    """Replace the final pronounced vowel while preserving Devanagari orthography."""
    base, old, marker = _final_consonant_and_vowel(word)
    if old is None:
        return word
    if vowel in VOWEL_MATRAS:
        return base + VOWEL_MATRAS[vowel] + marker
    # A target such as य् means a consonantal replacement of the vowel.
    # The preceding consonant must be made virāma-final before the new consonant.
    if len(vowel) == 2 and vowel[1] == "्":
        return base + "्" + vowel[0] + marker
    return base + vowel + marker

def remove_final_vowel(word: str) -> str:
    base, old, marker = _final_consonant_and_vowel(word)
    if old is None:
        return word
    return base + marker

# ---------------------------------------------------------------------------
# Executable rule functions
# ---------------------------------------------------------------------------

def r_svara_1(left, right, ctx):
    a, b = final_vowel(left), first_orthographic_char(right)
    pairs = {
        frozenset(("अ", "अ")): "आ", frozenset(("अ", "आ")): "आ", frozenset(("आ", "अ")): "आ",
        frozenset(("आ", "आ")): "आ",
        frozenset(("इ", "इ")): "ई", frozenset(("इ", "ई")): "ई", frozenset(("ई", "इ")): "ई",
        frozenset(("ई", "ई")): "ई",
        frozenset(("उ", "उ")): "ऊ", frozenset(("उ", "ऊ")): "ऊ", frozenset(("ऊ", "उ")): "ऊ",
        frozenset(("ऊ", "ऊ")): "ऊ",
        frozenset(("ऋ", "ऋ")): "ॠ", frozenset(("ऋ", "ॠ")): "ॠ", frozenset(("ॠ", "ऋ")): "ॠ",
    }
    if a in VOWELS and b in VOWELS:
        repl = pairs.get(frozenset((a, b)))
        if repl:
            return replace_final_vowel(left, repl) + right[1:]
    return None


def r_svara_2(left, right, ctx):
    a, b = final_vowel(left), first_orthographic_char(right)
    if a not in {"अ", "आ"}:
        return None
    repl = {"इ": "ए", "ई": "ए", "उ": "ओ", "ऊ": "ओ", "ऋ": "अर्", "ॠ": "अर्"}.get(b)
    return replace_final_vowel(left, repl) + right[1:] if repl else None


def r_svara_3(left, right, ctx):
    a, b = final_vowel(left), first_orthographic_char(right)
    if a not in {"अ", "आ"}:
        return None
    repl = {"ए": "ऐ", "ऐ": "ऐ", "ओ": "औ", "औ": "औ"}.get(b)
    return replace_final_vowel(left, repl) + right[1:] if repl else None


def r_svara_4(left, right, ctx):
    a, b = final_vowel(left), first_orthographic_char(right)
    if a not in IK or b not in AC or a == b:
        return None
    repl = {"इ": "य्", "ई": "य्", "उ": "व्", "ऊ": "व्", "ऋ": "र्", "ॠ": "र्", "ऌ": "ल्"}.get(a)
    return replace_final_vowel(left, repl) + (right[1:] if right.startswith("अ") else right) if repl else None


def r_svara_5(left, right, ctx):
    a, b = final_vowel(left), first_orthographic_char(right)
    if a not in EC or b not in AC:
        return None
    repl = {"ए": "अय्", "ओ": "अव्", "ऐ": "आय्", "औ": "आव्"}[a]
    return left[:-1] + repl + right


def r_svara_6(left, right, ctx):
    if not ctx.get("pada_boundary", True):
        return None
    a, b = final_vowel(left), first_orthographic_char(right)
    if a in {"ए", "ओ"} and b == "अ":
        return left + AVAGRAHA + right[1:]
    return None


def r_svara_7(left, right, ctx):
    # The rulebook describes this as a specialised/contextual rule.
    # Do not guess prefix/augment context.
    if not ctx.get("pararupa_allowed"):
        return None
    a, b = last_orthographic_char(left), first_orthographic_char(right)
    if a in {"ए", "ओ"} and b == "ए":
        return left[:-1] + b + right[1:]
    return None


def r_svara_8(left, right, ctx):
    # Retain as conditional because the source itself places this under
    # aṅgakārya / declensional stem modification.
    if not ctx.get("avang_context"):
        return None
    a, b = last_orthographic_char(left), first_orthographic_char(right)
    if a == "ओ" and b in AC:
        return left[:-1] + "अव" + right
    return None


def r_svara_9(left, right, ctx):
    # Prakṛtibhāva is primarily a blocking condition, not a transformation.
    if ctx.get("prakritibhava"):
        return left + right
    return None


def _class_of(ch):
    if ch in GUTTURAL: return GUTTURAL
    if ch in PALATAL: return PALATAL
    if ch in CEREBRAL: return CEREBRAL
    if ch in DENTAL: return DENTAL
    if ch in LABIAL: return LABIAL
    return None


def _third_of(ch):
    cls = _class_of(ch)
    if not cls: return None
    ordered = [
        "कखगघङ", "चछजझञ", "टठडढण", "तथदधन", "पफबभम"
    ]
    for chars in ordered:
        if ch in chars:
            return chars[2]
    return None


def _fourth_of(ch):
    cls = _class_of(ch)
    if not cls: return None
    for chars in ["कखगघङ","चछजझञ","टठडढण","तथदधन","पफबभम"]:
        if ch in chars:
            return chars[3]
    return None


def _first_of(ch):
    for chars in ["कखगघङ","चछजझञ","टठडढण","तथदधन","पफबभम"]:
        if ch in chars:
            return chars[0]
    return None


def r_vyan_1(left, right, ctx):
    a, b = last_orthographic_char(left), first_orthographic_char(right)
    if a == "स्" and b in PALATAL:
        return left[:-1] + "श्" + right
    if a == "स" and b in PALATAL:
        return left[:-1] + "श" + right
    if a in DENTAL and b in PALATAL:
        # Dental -> corresponding palatal member by place.
        mapping = {"त":"च", "थ":"छ", "द":"ज", "ध":"झ", "न":"ञ"}
        return left[:-1] + mapping[a] + right
    return None


def r_vyan_2(left, right, ctx):
    a, b = last_orthographic_char(left), first_orthographic_char(right)
    mapping = {"त":"ट", "थ":"ठ", "द":"ड", "ध":"ढ", "न":"ण", "स":"ष"}
    if a in mapping and b in CEREBRAL:
        return left[:-1] + mapping[a] + right
    return None


def r_vyan_3(left, right, ctx):
    a, b = last_orthographic_char(left), first_orthographic_char(right)
    if a in JHAL and (is_soft_consonant(b) or is_vowel(b)):
        j = _third_of(a)
        if j:
            return left[:-1] + j + right
    return None


def r_vyan_4(left, right, ctx):
    a, b = last_orthographic_char(left), first_orthographic_char(right)
    # chártva: final voiced/soft consonant becomes corresponding voiceless member
    # before a voiceless consonant.
    if a in JASH and is_hard_consonant(b):
        mapping = {"ग":"क","ज":"च","ड":"ट","द":"त","ब":"प"}
        return left[:-1] + mapping[a] + right
    return None


def r_vyan_5(left, right, ctx):
    a, b = last_orthographic_char(left), first_orthographic_char(right)
    if b not in NASALS:
        return None
    if a in JHAL:
        cls = _class_of(b)
        if cls:
            return left[:-1] + b + right
    return None


def r_vyan_6(left, right, ctx):
    a, b = last_orthographic_char(left), first_orthographic_char(right)
    if a in {"म्", "म"} and b in {"क","ख","ग","घ","च","छ","ज","झ","ट","ठ","ड","ढ","त","थ","द","ध","प","फ","ब","भ","श","ष","स"}:
        return left[:-1] + ANUSVARA + right
    if a == "ं":
        return left + right
    return None


def r_vyan_7(left, right, ctx):
    a, b = last_orthographic_char(left), first_orthographic_char(right)
    if a in {"ङ","ञ","ण","न","म"} and b in JASH:
        # A nasal assimilates to the following वर्ग nasal.
        target = {
            "क":"ङ","ख":"ङ","ग":"ङ","घ":"ङ",
            "च":"ञ","छ":"ञ","ज":"ञ","झ":"ञ",
            "ट":"ण","ठ":"ण","ड":"ण","ढ":"ण",
            "त":"न","थ":"न","द":"न","ध":"न",
            "प":"म","फ":"म","ब":"म","भ":"म",
        }.get(b)
        if target:
            return left[:-1] + target + right
    return None


def r_vyan_8(left, right, ctx):
    if not ctx.get("purvasavarna"):
        return None
    return r_vyan_7(left, right, ctx)


def r_vyan_9(left, right, ctx):
    # chē / छत्व with tuk augmentation is context-sensitive.
    if not ctx.get("tuk_before_chha"):
        return None
    if first_orthographic_char(right) == "छ":
        return left + "त्" + right
    return None


def r_vyan_10(left, right, ctx):
    a, b = last_orthographic_char(left), first_orthographic_char(right)
    if a == "ः" and b in SIBILANTS:
        return left[:-1] + {"श":"श","ष":"ष","स":"स"}[b] + right
    return None


def r_vyan_11(left, right, ctx):
    # ṇatva requires a preceding trigger and intervening segments.
    # The engine accepts explicit context supplied by a higher morphology layer.
    if not ctx.get("natva_allowed"):
        return None
    a, b = last_orthographic_char(left), first_orthographic_char(right)
    if b == "न":
        return left + "ण" + right[1:]
    return None


def r_vyan_12(left, right, ctx):
    if ctx.get("tuk_before_chha") and first_orthographic_char(right) == "छ":
        return left + "त्" + right
    return None


def r_vyan_13(left, right, ctx):
    if not ctx.get("ngamud_context"):
        return None
    # The exact trigger is grammatical; do not invent it from surface text.
    return None


def r_vyan_14(left, right, ctx):
    a, b = last_orthographic_char(left), first_orthographic_char(right)
    if b == "ल" and a in DENTAL:
        mapping = {"त":"ल","थ":"ल","द":"ल","ध":"ल","न":"ल्"}
        return left[:-1] + mapping[a] + right
    return None


def r_visarga_0(left, right, ctx):
    a, b = last_orthographic_char(left), first_orthographic_char(right)
    if a in {"स्","र"} and (not b or is_hard_consonant(b) or ctx.get("pause")):
        return left[:-1] + "ः" + right
    if a == "ः":
        return left + right
    return None


def r_visarga_1(left, right, ctx):
    if last_orthographic_char(left) == "ः" and is_hard_consonant(first_orthographic_char(right) or ""):
        return left + right
    return None


def r_visarga_2(left, right, ctx):
    a, b = last_orthographic_char(left), first_orthographic_char(right)
    if a == "ः" and b in SIBILANTS and ctx.get("optional", True):
        return left[:-1] + b + right
    return None


def r_visarga_3(left, right, ctx):
    a, b = last_orthographic_char(left), first_orthographic_char(right)
    if a != "ः":
        return None
    repl = {"च":"श","छ":"श","ट":"ष","ठ":"ष","त":"स","थ":"स"}.get(b)
    return left[:-1] + repl + right if repl else None


def r_visarga_4(left, right, ctx):
    if last_orthographic_char(left) != "ः":
        return None
    if final_vowel(left) != "अ":
        return None
    b = first_orthographic_char(right)
    if b and is_soft_consonant(b):
        return left[:-1] + "ो" + right
    return None


def r_visarga_4b(left, right, ctx):
    if last_orthographic_char(left) != "ः":
        return None
    if final_vowel(left) != "अ":
        return None
    b = first_orthographic_char(right)
    if b in VOWELS and b != "अ":
        return left[:-1] + right
    return None


def r_visarga_5(left, right, ctx):
    if last_orthographic_char(left) != "ः":
        return None
    if final_vowel(left) in {"अ", "आ"}:
        return None
    b = first_orthographic_char(right)
    if b and (is_soft_consonant(b) or is_vowel(b)):
        return left[:-1] + "र्" + right
    return None


def r_visarga_6(left, right, ctx):
    if last_orthographic_char(left) != "ः":
        return None
    if final_vowel(left) == "आ":
        return left[:-1] + right
    return None


def r_visarga_7(left, right, ctx):
    if last_orthographic_char(left) != "ः":
        return None
    b = first_orthographic_char(right)
    if b == "क" or b == "ख":
        return left + right  # phonetic allophone, orthography unchanged
    if b == "प" or b == "फ":
        return left + right
    return None


IMPLEMENTATIONS = {
    "svara-1": ("EXECUTABLE", r_svara_1),
    "svara-2": ("EXECUTABLE", r_svara_2),
    "svara-3": ("EXECUTABLE", r_svara_3),
    "svara-4": ("EXECUTABLE", r_svara_4),
    "svara-5": ("EXECUTABLE", r_svara_5),
    "svara-6": ("CONDITIONAL", r_svara_6),
    "svara-7": ("CONDITIONAL", r_svara_7),
    "svara-8": ("CONDITIONAL", r_svara_8),
    "svara-9": ("CONDITIONAL", r_svara_9),
    "vyan-1": ("EXECUTABLE", r_vyan_1),
    "vyan-2": ("EXECUTABLE", r_vyan_2),
    "vyan-3": ("EXECUTABLE", r_vyan_3),
    "vyan-4": ("EXECUTABLE", r_vyan_4),
    "vyan-5": ("EXECUTABLE", r_vyan_5),
    "vyan-6": ("EXECUTABLE", r_vyan_6),
    "vyan-7": ("EXECUTABLE", r_vyan_7),
    "vyan-8": ("CONDITIONAL", r_vyan_8),
    "vyan-9": ("CONDITIONAL", r_vyan_9),
    "vyan-10": ("EXECUTABLE", r_vyan_10),
    "vyan-11": ("CONDITIONAL", r_vyan_11),
    "vyan-12": ("CONDITIONAL", r_vyan_12),
    "vyan-13": ("CONDITIONAL", r_vyan_13),
    "vyan-14": ("EXECUTABLE", r_vyan_14),
    "visarga-0": ("EXECUTABLE", r_visarga_0),
    "visarga-1": ("EXECUTABLE", r_visarga_1),
    "visarga-2": ("CONDITIONAL", r_visarga_2),
    "visarga-3": ("EXECUTABLE", r_visarga_3),
    "visarga-4": ("EXECUTABLE", r_visarga_4),
    "visarga-4b": ("EXECUTABLE", r_visarga_4b),
    "visarga-5": ("EXECUTABLE", r_visarga_5),
    "visarga-6": ("EXECUTABLE", r_visarga_6),
    "visarga-7": ("EXECUTABLE", r_visarga_7),
}


class SandhiEngine:
    def __init__(self, rulebook_path: str | Path):
        self.rulebook_path = Path(rulebook_path)
        self.data = json.loads(self.rulebook_path.read_text(encoding="utf-8"))
        self.rules: list[RuleRecord] = []
        self._compile()

    def _compile(self):
        for category in ("svara_sandhi", "vyanjana_sandhi", "visarga_sandhi"):
            for item in self.data.get(category, []):
                rid = item["id"]
                impl, fn = IMPLEMENTATIONS.get(rid, ("MANUAL", None))
                self.rules.append(RuleRecord(
                    id=rid,
                    name=item["sanskrit_name"],
                    category=category,
                    source=item,
                    implementation=impl,
                    apply_fn=fn,
                ))

    def rule(self, rule_id: str) -> RuleRecord:
        for r in self.rules:
            if r.id == rule_id:
                return r
        raise KeyError(rule_id)

    def candidates(self, left: str, right: str, context: Optional[dict[str, Any]] = None) -> list[SandhiResult]:
        results = []
        for rule in self.rules:
            result = rule.apply(left, right, context)
            if result is not None:
                results.append(result)
        return results

    def explain(self, left: str, right: str, context: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        return [
            {
                "नियम_क्रमाङ्कः": r.rule_id,
                "सन्धिप्रकारः": r.category,
                "सन्धिनाम": r.rule_name,
                "पूर्वपदम्": r.left,
                "उत्तरपदम्": r.right,
                "परिणामः": r.result,
                "स्थितिः": r.status,
                "टिप्पणी": r.note,
            }
            for r in self.candidates(left, right, context)
        ]

    def compile_report(self) -> dict[str, Any]:
        counts = {}
        for r in self.rules:
            counts[r.implementation] = counts.get(r.implementation, 0) + 1
        return {
            "नियमाः": len(self.rules),
            "वर्गीकरणम्": counts,
            "नियमसूची": [
                {
                    "id": r.id,
                    "नाम": r.name,
                    "वर्गः": r.category,
                    "implementation": r.implementation,
                    "अष्टाध्यायी": r.source.get("ashtadhyayi_ref", ""),
                }
                for r in self.rules
            ],
        }

    def test_examples(self) -> list[dict[str, Any]]:
        """
        Tests only examples that can be parsed safely as 'left + right = result'.
        This is a diagnostic, not a claim that every source example is linguistically correct.
        """
        report = []
        for rule in self.rules:
            for ex in rule.source.get("examples", []):
                raw = ex.get("sandhi", "")
                m = re.match(r"^\s*(.+?)\s*\+\s*(.+?)\s*=\s*(.+?)\s*$", raw)
                if not m:
                    continue
                left, right, expected = map(str.strip, m.groups())
                # Remove explanatory parentheticals from expected only for display;
                # never silently alter source data.
                candidates = rule.apply(left, right, {})
                report.append({
                    "नियमः": rule.id,
                    "पूर्वम्": left,
                    "उत्तरम्": right,
                    "अपेक्षितम्": expected,
                    "निर्मितम्": candidates.result if candidates else None,
                    "मिलनम्": bool(candidates and candidates.result == expected),
                    "implementation": rule.implementation,
                })
        return report


# ---------------------------------------------------------------------------
# Batch / terminal interface
# ---------------------------------------------------------------------------

# IAST -> Devanagari conversion used only as an input adapter.  The Sandhi rule
# implementations themselves continue to operate on Devanagari.
IAST_TO_DEV = {
    "a":"अ","ā":"आ","i":"इ","ī":"ई","u":"उ","ū":"ऊ",
    "ṛ":"ऋ","ṝ":"ॠ","ḷ":"ऌ","e":"ए","ai":"ऐ","o":"ओ","au":"औ",
    "ṃ":"ं","ṁ":"ं","ḥ":"ः","'":"ऽ",
    "kh":"ख","gh":"घ","ch":"च","jh":"झ","ṭh":"ठ","ḍh":"ढ",
    "th":"थ","dh":"ध","ph":"फ","bh":"भ",
    "k":"क","g":"ग","ṅ":"ङ","c":"च","j":"ज","ñ":"ञ",
    "ṭ":"ट","ḍ":"ड","ṇ":"ण","t":"त","d":"द","n":"न",
    "p":"प","b":"ब","m":"म","y":"य","r":"र","l":"ल",
    "v":"व","ś":"श","ṣ":"ष","s":"स","h":"ह",
}

DEV_INDEPENDENT = {"a":"अ","ā":"आ","i":"इ","ī":"ई","u":"उ","ū":"ऊ",
                   "ṛ":"ऋ","ṝ":"ॠ","ḷ":"ऌ","e":"ए","ai":"ऐ","o":"ओ","au":"औ"}
DEV_MATRA = {"a":"","ā":"ा","i":"ि","ī":"ी","u":"ु","ū":"ू",
             "ṛ":"ृ","ṝ":"ॄ","ḷ":"ॢ","e":"े","ai":"ै","o":"ो","au":"ौ"}
IAST_VOWELS = ("ai","au","ā","ī","ū","ṛ","ṝ","ḷ","a","i","u","e","o")
IAST_CONSONANTS = ("kh","gh","ch","jh","ṭh","ḍh","th","dh","ph","bh",
                   "k","g","ṅ","c","j","ñ","ṭ","ḍ","ṇ","t","d","n",
                   "p","b","m","y","r","l","v","ś","ṣ","s","h")


def iast_to_devanagari(text: str) -> str:
    """Convert ordinary IAST Sanskrit text to Devanagari.

    This adapter intentionally preserves whitespace and punctuation. It is designed
    for Sanskrit source text rather than arbitrary multilingual IAST.
    """
    out = []
    i = 0
    prev_consonant = False
    while i < len(text):
        ch = text[i]
        if ch.isspace() or ch in "।॥,;:!?()[]{}\"“”‘’-–—0123456789":
            # A consonant at a word/punctuation boundary is consonant-final in
            # IAST and therefore must be written with virāma in Devanāgarī.
            # Without this, final d/t/m/n/s etc. incorrectly acquire inherent अ
            # (e.g. tvād -> त्वाद instead of त्वाद्).
            if prev_consonant:
                out.append("्")
            out.append(ch)
            prev_consonant = False
            i += 1
            continue
        if text.startswith("\\n", i):
            if prev_consonant:
                out.append("्")
            out.append("\n")
            prev_consonant = False
            i += 2
            continue
        if ch in "ṃṁḥऽ'":
            # If a marker follows a bare consonant, close that consonant first.
            if prev_consonant:
                out.append("्")
            out.append({"ṃ":"ं","ṁ":"ं","ḥ":"ः","ऽ":"ऽ","'":"ऽ"}[ch])
            prev_consonant = False
            i += 1
            continue
        tok = None
        for t in IAST_VOWELS + IAST_CONSONANTS:
            if text.startswith(t, i):
                tok = t
                break
        if tok is None:
            out.append(ch)
            prev_consonant = False
            i += 1
            continue
        if tok in DEV_INDEPENDENT:
            if prev_consonant:
                out.append(DEV_MATRA[tok])
            else:
                out.append(DEV_INDEPENDENT[tok])
            prev_consonant = False
        else:
            if prev_consonant:
                out.append("्")
            out.append(IAST_TO_DEV[tok])
            prev_consonant = True
        i += len(tok)
    # Preserve a word-final consonant at end-of-string as a half consonant.
    if prev_consonant:
        out.append("्")
    return "".join(out)

DEV_TO_IAST = {
    "अ":"a","आ":"ā","इ":"i","ई":"ī","उ":"u","ऊ":"ū","ऋ":"ṛ","ॠ":"ṝ","ऌ":"ḷ",
    "ए":"e","ऐ":"ai","ओ":"o","औ":"au","ं":"ṃ","ः":"ḥ","ऽ":"'",
    "क":"k","ख":"kh","ग":"g","घ":"gh","ङ":"ṅ","च":"c","छ":"ch","ज":"j","झ":"jh","ञ":"ñ",
    "ट":"ṭ","ठ":"ṭh","ड":"ḍ","ढ":"ḍh","ण":"ṇ","त":"t","थ":"th","द":"d","ध":"dh","न":"n",
    "प":"p","फ":"ph","ब":"b","भ":"bh","म":"m","य":"y","र":"r","ल":"l","व":"v",
    "श":"ś","ष":"ṣ","स":"s","ह":"h","्":"",
}
MATRA_TO_IAST = {"ा":"ā","ि":"i","ी":"ī","ु":"u","ू":"ū","ृ":"ṛ","ॄ":"ṝ","ॢ":"ḷ","े":"e","ै":"ai","ो":"o","ौ":"au"}
VOWEL_SIGNS = set("ािऀीुूृॄॢेैोौ")

def devanagari_to_iast(text: str) -> str:
    """Convert common Devanagari Sanskrit text to IAST, including inherent a."""
    out = []
    chars = list(text)
    i = 0
    while i < len(chars):
        ch = chars[i]
        if ch in MATRA_TO_IAST:
            out.append(MATRA_TO_IAST[ch])
            i += 1
            continue
        if ch == "्":
            i += 1
            continue
        if ch in DEV_TO_IAST and ch not in VOWELS and ch not in {"ं","ः","ऽ"}:
            out.append(DEV_TO_IAST[ch])
            # Consonant followed by a vowel sign gets that vowel; followed by
            # virama gets no inherent vowel; otherwise it carries inherent a.
            if i + 1 < len(chars) and chars[i + 1] == "्":
                i += 2
                continue
            if i + 1 < len(chars) and chars[i + 1] in MATRA_TO_IAST:
                i += 1
                continue
            out.append("a")
            i += 1
            continue
        if ch in DEV_TO_IAST:
            out.append(DEV_TO_IAST[ch])
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def _parse_verses(path: str | Path) -> list[dict[str, Any]]:
    """Parse common numbered-verse text layouts.

    Supported forms include lines beginning with `1`, `1.`, `1)`, `[1]`, etc.
    If no verse numbers are found, blank-line-separated blocks are numbered from 1.
    """
    text = Path(path).read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    verses = []
    current_no = None
    current = []
    num_re = re.compile(r"^\s*(?:verse\s*)?[\[(]?([0-9]+)[\].):]?\s*(.*)$", re.I)
    for line in lines:
        m = num_re.match(line)
        if m:
            if current and current_no is not None:
                verses.append({"verse": current_no, "text": " ".join(x.strip() for x in current).strip()})
            current_no = int(m.group(1))
            current = [m.group(2)] if m.group(2).strip() else []
        elif line.strip() == "":
            if current and current_no is None:
                verses.append({"verse": len(verses) + 1, "text": " ".join(x.strip() for x in current).strip()})
                current = []
            elif current_no is not None:
                current.append("")
        else:
            current.append(line)
    if current and (current_no is not None or any(x.strip() for x in current)):
        verses.append({"verse": current_no if current_no is not None else len(verses) + 1,
                       "text": " ".join(x.strip() for x in current).strip()})
    return [v for v in verses if v["text"]]


def process_verse(engine: SandhiEngine, verse: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    original = verse["text"]
    dev = iast_to_devanagari(original)
    # SandhiEngine operates on adjacent whitespace-delimited units. We report every
    # pair independently so the validation output remains auditable and does not
    # pretend that a whole verse can be safely rejoined automatically.
    tokens = re.findall(r"[^\s]+", dev)
    pairs = []
    for idx in range(len(tokens) - 1):
        left, right = tokens[idx], tokens[idx + 1]
        candidates = engine.explain(left, right, context)
        pairs.append({
            "क्रमः": idx + 1,
            "पूर्वपदम्_IAST": devanagari_to_iast(left),
            "उत्तरपदम्_IAST": devanagari_to_iast(right),
            "पूर्वपदम्": left,
            "उत्तरपदम्": right,
            "प्रस्ताविताः": [dict(c, **{"परिणामः_IAST": devanagari_to_iast(c["परिणामः"])}) for c in candidates],
        })
    return {
        "verse": verse["verse"],
        "original_IAST": original,
        "devanagari_internal": dev,
        "token_count": len(tokens),
        "sandhi_pairs": pairs,
    }


def process_file(engine: SandhiEngine, input_path: str | Path, start_verse: int,
                 end_verse: int, context: dict[str, Any]) -> dict[str, Any]:
    verses = _parse_verses(input_path)
    selected = [v for v in verses if start_verse <= v["verse"] <= end_verse]
    return {
        "engine": "sandhi_engine",
        "source": str(input_path),
        "encoding": "UTF-8",
        "input_script": "IAST",
        "start_verse": start_verse,
        "end_verse": end_verse,
        "verses_found": len(verses),
        "verses_processed": len(selected),
        "note": "Sandhi candidates are reported for adjacent whitespace-delimited units; no unresolved transformation is guessed.",
        "results": [process_verse(engine, v, context) for v in selected],
    }


def write_batch_output(data: dict[str, Any], output_path: str | Path, fmt: str) -> None:
    p = Path(output_path)
    if fmt == "json":
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return
    lines = [
        f"Sandhi Engine validation output",
        f"Source: {data['source']}",
        f"Verses: {data['start_verse']} - {data['end_verse']}",
        "",
    ]
    for v in data["results"]:
        lines.append(f"Verse {v['verse']}: {v['original_IAST']}")
        for pair in v["sandhi_pairs"]:
            lines.append(f"  {pair['पूर्वपदम्_IAST']} + {pair['उत्तरपदम्_IAST']}")
            if pair["प्रस्ताविताः"]:
                for c in pair["प्रस्ताविताः"]:
                    lines.append(f"    -> {c['परिणामः_IAST']} [{c['सन्धिनाम']}; {c['नियम_क्रमाङ्कः']}; {c['स्थितिः']}]")
            else:
                lines.append("    -> no applicable implemented rule")
        lines.append("")
    p.write_text("\n".join(lines), encoding="utf-8")


def cli():
    parser = argparse.ArgumentParser(description="Sandhi rulebook compiler and first-pass engine")
    parser.add_argument("--rulebook", default="sandhi_rulebook.json")
    parser.add_argument("--compile-report", action="store_true")
    parser.add_argument("--test-examples", action="store_true")
    parser.add_argument("--left")
    parser.add_argument("--right")
    parser.add_argument("--context", default="{}")
    parser.add_argument("--input", help="UTF-8 IAST Sanskrit source text")
    parser.add_argument("--start-verse", type=int, help="First verse number to process")
    parser.add_argument("--end-verse", type=int, help="Last verse number to process")
    parser.add_argument("--output", help="Output .json or .txt validation file")
    parser.add_argument("--format", choices=("json", "txt"), help="Output format; inferred from --output when omitted")
    args = parser.parse_args()

    try:
        context = json.loads(args.context)
    except json.JSONDecodeError as exc:
        parser.error(f"--context must be valid JSON: {exc}")

    engine = SandhiEngine(args.rulebook)

    if args.compile_report:
        print(json.dumps(engine.compile_report(), ensure_ascii=False, indent=2))

    if args.test_examples:
        print(json.dumps(engine.test_examples(), ensure_ascii=False, indent=2))

    if args.left is not None and args.right is not None:
        print(json.dumps(engine.explain(args.left, args.right, context), ensure_ascii=False, indent=2))

    if args.input:
        if args.start_verse is None or args.end_verse is None:
            parser.error("--input requires both --start-verse and --end-verse")
        if args.start_verse < 1 or args.end_verse < args.start_verse:
            parser.error("verse range must satisfy 1 <= start-verse <= end-verse")
        if not args.output:
            parser.error("--input requires --output")
        fmt = args.format or ("json" if Path(args.output).suffix.lower() == ".json" else "txt")
        data = process_file(engine, args.input, args.start_verse, args.end_verse, context)
        write_batch_output(data, args.output, fmt)
        print(f"Wrote {args.output} ({data['verses_processed']} verses)")


if __name__ == "__main__":
    cli()
