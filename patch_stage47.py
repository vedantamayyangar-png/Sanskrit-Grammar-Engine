# -*- coding: utf-8 -*-
path = "engine_stage47_work.py"
with open(path, encoding="utf-8") as f:
    src = f.read()

# 1. Bump engine version
needle = 'ENGINE_VERSION = "0.17"'
assert src.count(needle) == 1
src = src.replace(needle, 'ENGINE_VERSION = "0.18"')

# 2. Add Tuple to the typing import (needed for the new candidate-list type hint).
needle = "from typing import Any, Dict, Iterable, List, Optional"
assert src.count(needle) == 1
src = src.replace(needle, "from typing import Any, Dict, Iterable, List, Optional, Tuple")

# 3. Insert the three new Stage-47 module-level normalization helpers
# right after devanagari_to_slp1's definition.
anchor = '''        if ch in _DEVA_IGNORABLE:
            i += 1; continue
        return None
    return "".join(out)


# Exact Library text snapshot used only as the fixed benchmark. Source:'''
assert src.count(anchor) == 1, "devanagari_to_slp1 end anchor not found"
insertion = '''        if ch in _DEVA_IGNORABLE:
            i += 1; continue
        return None
    return "".join(out)


# ----------------------------------------------------------------------
# Stage 47: three additional, deterministic, symmetric SLP1-level
# normalizations for dictionary lookup, closing known gap #15. Each is a
# single, well-defined, script-level transformation -- never a guess at
# a word's gender, stem class, or declension -- and each was verified
# empirically against the real SKD/Apte data before being wired in (see
# CHANGELOG Stage 47), per this project's no-fuzzy-matching policy.

_HOMORGANIC_NASAL: Dict[str, str] = {}
for _stops, _nasal in (("kKgG", "N"), ("cCjJ", "Y"), ("wWqQ", "R"), ("tTdD", "n"), ("pPbB", "m")):
    for _s in _stops:
        _HOMORGANIC_NASAL[_s] = _nasal
del _stops, _nasal, _s

_SLP1_CONSONANTS = set(_DEVA_CONSONANTS.values())


def _slp1_citation_ending_stripped(slp1: str) -> Optional[str]:
    """Strip a single trailing citation-ending marker: visarga 'H'
    (nom.sg. masc./fem. -- the original Stage 42 normalization), or the
    neuter/masc.-acc. singular '-am' ending, itself conventionally
    spelled EITHER as a bare consonant 'm' (e.g. the v8.1 breakdown's
    "puMgavam") OR as an anusvara 'M' (e.g. Apte's own headword
    "vIryaM") in these Library sources -- both are the same ending, just
    two standard, interchangeable final-nasal spellings; stripping
    either is the same category of normalization as the original
    visarga strip, not stem-class-specific guessing (nothing here picks
    which ending to expect based on a guessed gender/declension -- it
    only ever removes a single trailing H/m/M actually present). Returns
    None if the string does not end in one of these three markers."""
    if slp1 and slp1[-1] in ("H", "m", "M"):
        return slp1[:-1]
    return None


def _slp1_guttural_normalized(slp1: str) -> Optional[str]:
    """Realize an anusvara ('M') immediately preceding a class stop as
    that stop's own homorganic (savarna) nasal, per the standard
    Paninian convention (8.4.58, anusvarasya yayi parasavarnah) that
    these dictionaries' headwords follow (e.g. SKD's own "aNga",
    "puNgavaH" spell the guttural nasal explicitly rather than with an
    anusvara). A single, symmetric, deterministic substitution -- not a
    guess, since the following stop's class fixes the correct nasal
    uniquely. Returns None if no anusvara-before-stop occurs."""
    out: List[str] = []
    changed = False
    i, n = 0, len(slp1)
    while i < n:
        ch = slp1[i]
        if ch == "M" and i + 1 < n and slp1[i + 1] in _HOMORGANIC_NASAL:
            out.append(_HOMORGANIC_NASAL[slp1[i + 1]])
            changed = True
        else:
            out.append(ch)
        i += 1
    return "".join(out) if changed else None


def _slp1_gemination_normalized(slp1: str) -> Optional[str]:
    """Double the non-'r' member of any 'r'+consonant or consonant+'r'
    conjunct (two consonant letters directly adjacent in the SLP1
    string, with no vowel between them -- which devanagari_to_slp1 only
    ever produces for an original Devanagari virama-joined conjunct),
    modeling the Bengali-typesetting gemination convention documented
    for SKD since Stage 42/43 (e.g. "DarmaH" -> "DarmmaH", "putraH" ->
    "puttraH") -- confirmed in Stage 47 to also explain SKD's own
    "vIryyaH"-family spellings of vIrya. A single documented transform,
    tried as one extra deterministic candidate -- never assumed to be
    the dictionary's actual spelling, and never chained into repeated/
    recursive doubling. Returns None if no r-adjacent conjunct occurs."""
    chars = list(slp1)
    n = len(chars)
    out: List[str] = []
    i = 0
    changed = False
    while i < n:
        c = chars[i]
        nxt = chars[i + 1] if i + 1 < n else None
        if c == "r" and nxt in _SLP1_CONSONANTS and nxt != "r":
            out.append(c); out.append(nxt); out.append(nxt)
            changed = True
            i += 2
            continue
        if c in _SLP1_CONSONANTS and c != "r" and nxt == "r":
            out.append(c); out.append(c); out.append(nxt)
            changed = True
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out) if changed else None


# Exact Library text snapshot used only as the fixed benchmark. Source:'''
src = src.replace(anchor, insertion)

# 4. Generalize both dictionary loaders' stripped index (visarga-only ->
# citation-ending: H, m, or M). Both loaders share identical bodies for
# this block, so a single (multi-occurrence) replace covers both.
loader_needle = '''    by_headword: Dict[str, List[Dict[str, Any]]] = {}
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
    }'''
assert src.count(loader_needle) == 2, f"expected 2 loader occurrences, found {src.count(loader_needle)}"
loader_replacement = '''    by_headword: Dict[str, List[Dict[str, Any]]] = {}
    by_headword_citation_ending_normalized: Dict[str, List[Dict[str, Any]]] = {}
    for entry in data:
        if not isinstance(entry, dict):
            continue
        sf = entry.get("source_fields", {}) or {}
        headwords = {sf.get("k1"), sf.get("k2")}
        for hw in headwords:
            if not hw or not isinstance(hw, str):
                continue
            by_headword.setdefault(hw, []).append(entry)
            # Stage 47: generalizes the Stage 42 single-trailing-visarga
            # strip to the full set of single-character citation endings
            # (see _slp1_citation_ending_stripped's docstring for why H,
            # m, and M are the same category of ending).
            stripped = hw[:-1] if hw and hw[-1] in ("H", "m", "M") else hw
            by_headword_citation_ending_normalized.setdefault(stripped, []).append(entry)
    return {
        "raw_count": len(data),
        "by_headword": by_headword,
        "by_headword_citation_ending_normalized": by_headword_citation_ending_normalized,
        "path": str(path),
    }'''
src = src.replace(loader_needle, loader_replacement)

# 5. Rewrite _dictionary_attest_word to use the new six-way candidate
# priority chain (see its own docstring for the exact order).
old_method = '''    def _dictionary_attest_word(self, word_deva: str) -> Dict[str, Any]:
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
        return result'''
assert src.count(old_method) == 1, "_dictionary_attest_word original body not found verbatim"
new_method = '''    def _dictionary_attest_word(self, word_deva: str) -> Dict[str, Any]:
        """Stage 43 (generalizes Stage 42's SKD-only _skd_attest_word);
        Stage 47 widens the normalization set (closing known gap #15).
        Independently attest one Devanagari word/constituent against
        EVERY configured dictionary Library file (currently SKD and
        Apte), reporting a per-dictionary `sources` list rather than
        collapsing to a single boolean -- so which dictionary(ies)
        actually attested a word, and by which method, is never lost,
        per this project's source-provenance principle.

        For each dictionary, up to six deterministic lookup candidates
        are tried, in this fixed priority order (first hit wins; the
        specific method that hit is always recorded verbatim, never
        collapsed to a generic "matched"), against BOTH that
        dictionary's raw headword index and its citation-ending-
        normalized index (so a match is found whichever side -- the
        query or the dictionary's own headword -- happens to carry the
        citation ending):

          1. exact -- the word's own SLP1 transliteration, verbatim.
          2. citation_ending_normalized (Stage 42, generalized Stage 47)
             -- one trailing visarga/case-ending marker (H, m, or M; see
             _slp1_citation_ending_stripped) stripped, since both
             dictionaries conventionally cite many headwords in an
             inflected nom./acc. singular citation form while a
             compound's non-final members or a pratyaya breakdown's
             stem are frequently bare.
          3. guttural_normalized (Stage 47) -- an anusvara before a class
             stop realized as that stop's homorganic nasal (see
             _slp1_guttural_normalized), matching e.g. SKD's own
             "puNgavaH" rather than "puMgavaH".
          4. guttural_normalized + citation_ending_normalized -- both
             together (needed for e.g. the v8.1 breakdown's accusative
             "puMgavam").
          5. gemination_normalized (Stage 47) -- the non-'r' member of an
             'r'-adjacent conjunct doubled, modeling SKD's Bengali-
             typesetting gemination (see _slp1_gemination_normalized).
          6. gemination_normalized + citation_ending_normalized -- both
             together.

        All six are single, symmetric, documented script-level
        substitutions, empirically verified against the real SKD/Apte
        data before being wired in (CHANGELOG Stage 47) -- none of them
        guesses at a word's gender, stem class, or declension to
        manufacture a different ending. A word that still doesn't match
        after all six is reported attested=False, not silently dropped
        or promoted: e.g. आत्मन्'s own citation form ("AtmA", a stem-
        class-specific nominative lengthening) and any multi-character
        declensional suffix (e.g. genitive "-sya") remain open,
        explicitly out of this scope -- see PROJECT_STATE.md gap #15."""
        slp1 = devanagari_to_slp1(word_deva)
        result: Dict[str, Any] = {"constituent": word_deva, "slp1": slp1, "attested": False, "sources": []}
        if slp1 is None:
            result["note"] = "Word contains a character outside the engine's deterministic Devanagari→SLP1 table; dictionary lookup not attempted."
            return result

        candidates: List[Tuple[str, str]] = [("exact", slp1)]
        ces = _slp1_citation_ending_stripped(slp1)
        if ces:
            candidates.append(("citation_ending_normalized", ces))
        gu = _slp1_guttural_normalized(slp1)
        if gu:
            candidates.append(("guttural_normalized", gu))
            gu_ces = _slp1_citation_ending_stripped(gu)
            if gu_ces:
                candidates.append(("guttural_normalized+citation_ending_normalized", gu_ces))
        ge = _slp1_gemination_normalized(slp1)
        if ge:
            candidates.append(("gemination_normalized", ge))
            ge_ces = _slp1_citation_ending_stripped(ge)
            if ge_ces:
                candidates.append(("gemination_normalized+citation_ending_normalized", ge_ces))

        any_dict_loaded = False
        for dict_key, lib in (("skd", self.library_skd), ("apte", self.library_apte)):
            if lib is None:
                continue
            any_dict_loaded = True
            for method, cand in candidates:
                hits = lib["by_headword"].get(cand) or lib["by_headword_citation_ending_normalized"].get(cand)
                if hits:
                    sample = hits[0].get("source_text", "")
                    result["sources"].append({
                        "dictionary": dict_key,
                        "match_method": method,
                        "matched_form_slp1": cand,
                        "entry_ids": [h.get("id") for h in hits[:5]],
                        "entry_count": len(hits),
                        "sample_text_slp1": (sample[:200] + "…") if len(sample) > 200 else sample,
                    })
                    break  # first-hit priority order, as documented above
        result["attested"] = bool(result["sources"])
        if not any_dict_loaded:
            result["note"] = "No dictionary Library file found on disk; attestation not attempted."
        elif not result["attested"]:
            result["note"] = "No match under any of the six deterministic lookup methods in any loaded dictionary; reported as a gap, not guessed."
        return result'''
src = src.replace(old_method, new_method)

with open(path, "w", encoding="utf-8") as f:
    f.write(src)
print("Stage 47 patch applied OK, bytes:", len(src.encode("utf-8")))
